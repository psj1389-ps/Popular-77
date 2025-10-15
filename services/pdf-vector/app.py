from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
import os
import tempfile
import io
import zipfile
import logging
from werkzeug.utils import secure_filename
from converters.pdf_to_images import pdf_to_images
from converters.images_to_pdf import images_to_pdf
from utils.file_utils import ensure_dirs, zip_paths, parse_pages
from converters.pdf_to_svg import pdf_to_svgs
from converters.pdf_to_ai import split_pdf_to_ai_pages, save_pdf_as_ai
from PIL import Image
import json
from dotenv import load_dotenv
import subprocess
import platform
import fitz  # PyMuPDF
import re
from typing import List, Tuple, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

# 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_with_layout_from_pdf(pdf_path):
    """Extract text with layout information from PDF"""
    try:
        # Windows에서 LibreOffice 사용
        if platform.system() == "Windows":
            # LibreOffice 경로 찾기
            libreoffice_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                "soffice"  # PATH에 있는 경우
            ]
            
            libreoffice_path = None
            for path in libreoffice_paths:
                if os.path.exists(path) or path == "soffice":
                    libreoffice_path = path
                    break
            
            if libreoffice_path:
                # LibreOffice를 사용하여 변환
                output_dir = os.path.dirname(pdf_path)
                cmd = [
                    libreoffice_path,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", output_dir,
                    pdf_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # 생성된 PDF 파일명 확인 및 이동
                    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                    generated_pdf = os.path.join(output_dir, base_name + ".pdf")
                    
                    if os.path.exists(generated_pdf) and generated_pdf != pdf_path:
                        os.rename(generated_pdf, pdf_path)
                    
                    return os.path.exists(pdf_path)
                else:
                    print(f"LibreOffice 변환 실패: {result.stderr}")
                    return False
            else:
                print("LibreOffice를 찾을 수 없습니다.")
                return False
        else:
            print("현재 Linux/Mac에서의 DOCX → PDF 변환은 지원되지 않습니다.")
            return False
            
    except Exception as e:
        print(f"DOCX → PDF 변환 중 오류: {str(e)}")
        return False

def pdf_to_docx(pdf_path, output_path, quality='medium'):
    """PDF를 DOCX로 변환하는 함수 (Adobe API 통합 및 OCR 텍스트 추출, 방향 자동 감지)"""
    try:
        # 품질 설정에 따른 파라미터 설정 (최적화됨)
        quality_settings = {
            'medium': {
                'dpi': 120,  # DPI 최적화로 속도 향상
                'format': 'jpeg',
                'jpeg_quality': 80,  # 품질과 속도의 균형
                'max_size': (1600, 1200),  # 적절한 해상도
                'description': '균형 변환 (최적화된 속도와 품질)'
            },
            'high': {
                'dpi': 180,  # 고품질이지만 속도 고려
                'format': 'jpeg',  # PNG 대신 JPEG 사용으로 속도 향상
                'jpeg_quality': 90,
                'max_size': (2048, 1536),  # 해상도 최적화
                'description': '고품질 변환 (향상된 속도)'
            }
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        print(f"변환 설정: {settings['description']}")
        
        # 1단계: 레이아웃 인식을 통한 텍스트 추출 시도 (방향 정보 포함)
        print("레이아웃 인식을 통한 텍스트 추출을 시도합니다...")
        layout_data = extract_text_with_layout_from_pdf(pdf_path)
        extracted_text = layout_data.get('full_text', '')
        text_blocks = layout_data.get('text_blocks', [])
        orientation_info = layout_data.get('orientation_info', {})
        all_ocr_text = []
        
        if extracted_text:
            print(f"레이아웃 인식으로 텍스트 추출 성공: {len(extracted_text)}자")
        else:
            print("레이아웃 인식 실패, Adobe API를 시도합니다...")
            
            # 2단계: Adobe API를 사용한 PDF 내용 추출 시도
            if adobe_available:
                print("Adobe API를 사용하여 PDF 처리를 시작합니다...")
                extracted_content = extract_pdf_content_with_adobe(pdf_path)
                if extracted_content:
                    extracted_text = str(extracted_content)
                    print(f"Adobe API에서 텍스트 추출 성공: {len(extracted_text)}자")
                else:
                    print("Adobe API 추출 실패, OCR 방법으로 진행합니다.")
        
        # 기본 방법: PDF를 이미지로 변환 (품질별 최적화)
        print("PDF를 이미지로 변환 중...")
        temp_dir = tempfile.mkdtemp()
        ensure_dirs([temp_dir])
        image_paths = pdf_to_images(pdf_path, temp_dir, fmt=settings['format'], dpi=settings['dpi'])
        images = [Image.open(path) for path in image_paths]
        
        # 새 PowerPoint 프레젠테이션 생성 (방향에 따른 슬라이드 설정)
        prs = Presentation()
        
        # 슬라이드 크기 설정 (문서 방향에 따라 자동 조정)
        primary_orientation = orientation_info.get('primary_orientation', 'portrait')
        
        if primary_orientation == 'landscape':
            # 가로형 슬라이드 (16:9 비율)
            prs.slide_width = Inches(13.33)
            prs.slide_height = Inches(7.5)
            print("가로형 슬라이드로 설정됨 (16:9)")
        else:
            # 세로형 슬라이드 (9:16 비율)
            prs.slide_width = Inches(7.5)
            prs.slide_height = Inches(13.33)
            print("세로형 슬라이드로 설정됨 (9:16)")
        
        all_ocr_text = []
        
        print(f"총 {len(images)}페이지 처리 중...")
        def get_blank_slide_layout(prs):
            """안전한 빈 슬라이드 레이아웃 가져오기"""
            try:
                # 슬라이드 레이아웃이 있는지 먼저 확인
                if len(prs.slide_layouts) == 0:
                    raise IndexError("슬라이드 레이아웃이 없습니다")
                
                # 빈 슬라이드 레이아웃 우선 선택
                if len(prs.slide_layouts) > 6:
                    return prs.slide_layouts[6]  # 빈 슬라이드
                elif len(prs.slide_layouts) > 5:
                    return prs.slide_layouts[5]  # 제목만 있는 슬라이드
                else:
                    return prs.slide_layouts[0]  # 첫 번째 사용 가능한 레이아웃
            except (IndexError, AttributeError) as e:
                print(f"슬라이드 레이아웃 접근 오류: {e}")
                # 기본 프레젠테이션 생성 시 최소 하나의 레이아웃은 있어야 함
                if len(prs.slide_layouts) > 0:
                    return prs.slide_layouts[0]
                else:
                    raise Exception("사용 가능한 슬라이드 레이아웃이 없습니다")
        
        # 편집 가능한 텍스트 슬라이드 생성 (원본 이미지 제거)
        # OCR로 텍스트 추출 (Adobe API가 실패한 경우)
        if not extracted_text:
            for i, image in enumerate(images):
                print(f"페이지 {i+1}/{len(images)} OCR 처리 중...")
                ocr_text = extract_text_blocks_with_ocr(image)
                if ocr_text:
                    all_ocr_text.append(ocr_text)
        
        # 편집 가능한 텍스트 슬라이드 생성
        final_text = extracted_text if extracted_text else '\n'.join(all_ocr_text)
        
        if text_blocks:
            print(f"편집 가능한 텍스트 슬라이드 생성: {len(text_blocks)}개 블록")
            
            # 페이지별로 슬라이드 구성
            for page_num in range(len(images)):
                # 새 슬라이드 추가 (제목과 내용 레이아웃)
                try:
                    slide_layout = prs.slide_layouts[1]  # 제목과 내용 레이아웃
                except (IndexError, AttributeError):
                    slide_layout = get_blank_slide_layout(prs)
                
                slide = prs.slides.add_slide(slide_layout)
                
                # 슬라이드 제목 설정
                try:
                    title_shape = slide.shapes.title
                    title_shape.text = f"페이지 {page_num + 1}"
                except AttributeError:
                    # 제목이 없는 레이아웃인 경우 텍스트 박스 추가
                    left = Inches(0.5)
                    top = Inches(0.5)
                    width = Inches(9)
                    height = Inches(1)
                    title_box = slide.shapes.add_textbox(left, top, width, height)
                    title_frame = title_box.text_frame
                    title_frame.text = f"페이지 {page_num + 1}"
                
                # 해당 페이지의 텍스트 블록 추가
                page_text_blocks = [block for block in text_blocks if block['page'] == page_num]
                
                if page_text_blocks:
                    # 내용 텍스트박스 가져오기
                    try:
                        content_shape = slide.placeholders[1]
                        text_frame = content_shape.text_frame
                        text_frame.clear()
                        
                        for j, block in enumerate(page_text_blocks):
                            if j == 0:
                                # 첫 번째 단락
                                p = text_frame.paragraphs[0]
                            else:
                                # 추가 단락
                                p = text_frame.add_paragraph()
                            
                            p.text = block['text']
                            
                            # 텍스트 정렬 적용
                            if block['alignment'] == 'center':
                                p.alignment = 1  # 중앙 정렬
                                try:
                                    p.font.bold = True
                                except AttributeError:
                                    pass
                            elif block['alignment'] == 'right':
                                p.alignment = 2  # 오른쪽 정렬
                            else:
                                p.alignment = 0  # 왼쪽 정렬
                            
                            # 텍스트 크기 조정
                            try:
                                # from docx.shared import Pt
                                # if len(block['text']) < 50 and block['alignment'] == 'center':
                                #     p.font.size = Pt(18)  # 제목용 크기
                                # else:
                                #     p.font.size = Pt(14)  # 본문용 크기
                                pass
                            except (ImportError, AttributeError):
                                pass
                                
                    except (IndexError, AttributeError):
                        # 내용 플레이스홀더가 없는 경우 텍스트 박스 추가
                        left = Inches(0.5)
                        top = Inches(1.5)
                        width = Inches(9)
                        height = Inches(6)
                        content_box = slide.shapes.add_textbox(left, top, width, height)
                        content_frame = content_box.text_frame
                        content_text = '\n'.join([block['text'] for block in page_text_blocks])
                        content_frame.text = content_text
                else:
                    # 텍스트가 없는 페이지
                    try:
                        content_shape = slide.placeholders[1]
                        content_shape.text = "[이 페이지는 텍스트 추출이 어려운 이미지 페이지입니다]"
                    except (IndexError, AttributeError):
                        left = Inches(0.5)
                        top = Inches(1.5)
                        width = Inches(9)
                        height = Inches(6)
                        content_box = slide.shapes.add_textbox(left, top, width, height)
                        content_frame = content_box.text_frame
                        content_frame.text = "[이 페이지는 텍스트 추출이 어려운 이미지 페이지입니다]"
        
        elif final_text:
            print(f"일반 텍스트 슬라이드 생성: {len(final_text)}자")
            
            # 텍스트를 적절한 크기로 나누어 슬라이드 생성
            text_chunks = final_text.split('\n\n')
            chunk_size = 5  # 슬라이드당 단락 수
            
            for i in range(0, len(text_chunks), chunk_size):
                try:
                    slide_layout = prs.slide_layouts[1]  # 제목과 내용 레이아웃
                except (IndexError, AttributeError):
                    slide_layout = get_blank_slide_layout(prs)
                
                slide = prs.slides.add_slide(slide_layout)
                
                # 슬라이드 제목
                try:
                    title_shape = slide.shapes.title
                    title_shape.text = f"슬라이드 {(i // chunk_size) + 1}"
                except AttributeError:
                    left = Inches(0.5)
                    top = Inches(0.5)
                    width = Inches(9)
                    height = Inches(1)
                    title_box = slide.shapes.add_textbox(left, top, width, height)
                    title_frame = title_box.text_frame
                    title_frame.text = f"슬라이드 {(i // chunk_size) + 1}"
                
                # 내용 추가
                chunk_text = text_chunks[i:i+chunk_size]
                content_text = '\n\n'.join([para.strip() for para in chunk_text if para.strip()])
                
                try:
                    content_shape = slide.placeholders[1]
                    content_shape.text = content_text
                except (IndexError, AttributeError):
                    left = Inches(0.5)
                    top = Inches(1.5)
                    width = Inches(9)
                    height = Inches(6)
                    content_box = slide.shapes.add_textbox(left, top, width, height)
                    content_frame = content_box.text_frame
                    content_frame.text = content_text
        
        else:
            print("추출할 수 있는 텍스트가 없습니다. 이미지 기반 슬라이드를 생성합니다.")
            
            # 텍스트가 없는 경우에만 이미지 슬라이드 생성
            for i, image in enumerate(images):
                print(f"페이지 {i+1}/{len(images)} 처리 중...")
                
                # 슬라이드 추가 - 안전한 레이아웃 사용
                slide_layout = get_blank_slide_layout(prs)
                slide = prs.slides.add_slide(slide_layout)
                
                # 이미지 크기 최적화 (원본 문서와 동일한 크기 유지)
                original_width, original_height = image.size
                
                # 슬라이드 방향에 따른 이미지 크기 조정
                if primary_orientation == 'landscape':
                    # 가로형 슬라이드: 최대 높이 6.5인치
                    target_height = min(6.5, original_height / 72)  # 72 DPI 기준
                    aspect_ratio = original_width / original_height
                    target_width = target_height * aspect_ratio
                    # 슬라이드 너비를 초과하지 않도록 조정
                    max_slide_width = 12.5  # 가로형 슬라이드 최대 너비
                    if target_width > max_slide_width:
                        target_width = max_slide_width
                        target_height = target_width / aspect_ratio
                else:
                    # 세로형 슬라이드: 최대 너비 6.5인치
                    target_width = min(6.5, original_width / 72)  # 72 DPI 기준
                    aspect_ratio = original_height / original_width
                    target_height = target_width * aspect_ratio
                    # 슬라이드 높이를 초과하지 않도록 조정
                    max_slide_height = 12.5  # 세로형 슬라이드 최대 높이
                    if target_height > max_slide_height:
                        target_height = max_slide_height
                        target_width = target_height / aspect_ratio
                
                # 이미지를 임시 파일로 저장 (JPEG 최적화)
                temp_img_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img:
                        temp_img_path = temp_img.name
                        # JPEG로 저장 (품질별 압축, 빠른 처리)
                        image.save(temp_img_path, 'JPEG', quality=settings['jpeg_quality'], optimize=True)
                    
                    # 슬라이드에 이미지 추가 (원본 비율 유지)
                    slide.shapes.add_picture(temp_img_path, width=DocxInches(target_width))
                    
                    # 페이지 구분을 위한 페이지 브레이크 추가 (마지막 페이지 제외)
                    if i < len(images) - 1:
                        doc.add_page_break()
                    
                finally:
                    # 임시 파일 삭제 (빠른 처리)
                    if temp_img_path and os.path.exists(temp_img_path):
                        try:
                            os.unlink(temp_img_path)
                        except (OSError, PermissionError) as e:
                            print(f"임시 파일 삭제 실패 (무시됨): {e}")
                            # 임시 파일 삭제 실패는 무시하고 계속 진행
        
        # 하이브리드 변환: 추출된 텍스트를 편집 가능한 형태로 마지막 슬라이드에 추가
        final_text = extracted_text if extracted_text else '\n'.join(all_ocr_text)
        if final_text:
            print(f"하이브리드 변환: 추출된 텍스트를 편집 가능한 형태로 추가: {len(final_text)}자")
            
            # 텍스트 전용 슬라이드 추가 - 안전한 레이아웃 선택
            try:
                # 제목과 내용 레이아웃이 있는지 확인
                if len(prs.slide_layouts) > 1:
                    text_slide_layout = prs.slide_layouts[1]  # 제목과 내용 레이아웃
                else:
                    text_slide_layout = get_blank_slide_layout(prs)
            except (IndexError, AttributeError):
                text_slide_layout = get_blank_slide_layout(prs)
            
            text_slide = prs.slides.add_slide(text_slide_layout)
            
            # 제목 설정 (안전한 방법)
            try:
                title = text_slide.shapes.title
                title.text = "추출된 텍스트 (편집 가능)"
            except AttributeError:
                # 제목이 없는 레이아웃인 경우 텍스트 박스 추가
                left = Inches(0.5)
                top = Inches(0.5)
                width = Inches(9)
                height = Inches(1)
                title_box = text_slide.shapes.add_textbox(left, top, width, height)
                title_frame = title_box.text_frame
                title_frame.text = "추출된 텍스트 (편집 가능)"
            
            # 내용 설정 (안전한 방법) - 레이아웃 정보 활용
            if text_blocks:
                print("레이아웃 정보를 활용하여 텍스트 구조화...")
                try:
                    content = text_slide.placeholders[1]
                    content_frame = content.text_frame
                    content_frame.clear()
                    
                    current_page = -1
                    for block in text_blocks:
                        # 페이지가 바뀌면 구분선 추가
                        if block['page'] != current_page:
                            if current_page != -1:
                                p = content_frame.add_paragraph()
                                p.text = f"\n--- 페이지 {block['page'] + 1} ---"
                            current_page = block['page']
                        
                        # 텍스트 단락 추가
                        p = content_frame.add_paragraph()
                        p.text = block['text']
                        
                        # 정렬 설정 (기본값으로 처리)
                        if block['alignment'] == 'center':
                            p.alignment = 1  # 중앙 정렬
                        elif block['alignment'] == 'right':
                            p.alignment = 2  # 오른쪽 정렬
                        else:
                            p.alignment = 0  # 왼쪽 정렬
                            
                except (IndexError, AttributeError):
                    # 내용 플레이스홀더가 없는 경우 텍스트 박스 추가
                    left = Inches(0.5)
                    top = Inches(1.5)
                    width = Inches(9)
                    height = Inches(6)
                    content_box = text_slide.shapes.add_textbox(left, top, width, height)
                    content_frame = content_box.text_frame
                    content_frame.text = final_text
            else:
                # 레이아웃 정보가 없는 경우 일반 텍스트로 추가
                try:
                    content = text_slide.placeholders[1]
                    content.text = final_text
                except (IndexError, AttributeError):
                    # 내용 플레이스홀더가 없는 경우 텍스트 박스 추가
                    left = Inches(0.5)
                    top = Inches(1.5)
                    width = Inches(9)
                    height = Inches(6)
                    content_box = text_slide.shapes.add_textbox(left, top, width, height)
                    content_frame = content_box.text_frame
                    content_frame.text = final_text
            
            print("편집 가능한 텍스트가 레이아웃 정보와 함께 슬라이드에 추가되었습니다.")
        else:
            print("추출할 수 있는 텍스트가 없습니다.")
        
        # PPTX 파일 저장
        prs.save(output_path)
        return True
        
    except Exception as e:
        print(f"변환 중 오류 발생: {str(e)}")
        return False

def docx_to_pdf(docx_path, output_path):
    """DOCX를 PDF로 변환하는 함수"""
    try:
        # Windows에서 LibreOffice 사용
        if platform.system() == "Windows":
            # LibreOffice 경로 찾기
            libreoffice_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                "soffice"  # PATH에 있는 경우
            ]
            
            libreoffice_path = None
            for path in libreoffice_paths:
                if os.path.exists(path) or path == "soffice":
                    libreoffice_path = path
                    break
            
            if libreoffice_path:
                # LibreOffice를 사용하여 변환
                output_dir = os.path.dirname(output_path)
                cmd = [
                    libreoffice_path,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", output_dir,
                    docx_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # 생성된 PDF 파일명 확인 및 이동
                    base_name = os.path.splitext(os.path.basename(docx_path))[0]
                    generated_pdf = os.path.join(output_dir, base_name + ".pdf")
                    
                    if os.path.exists(generated_pdf) and generated_pdf != output_path:
                        os.rename(generated_pdf, output_path)
                    
                    return os.path.exists(output_path)
                else:
                    print(f"LibreOffice 변환 실패: {result.stderr}")
                    return False
            else:
                print("LibreOffice를 찾을 수 없습니다.")
                return False
        else:
            print("현재 Linux/Mac에서의 DOCX → PDF 변환은 지원되지 않습니다.")
            return False
            
    except Exception as e:
        print(f"DOCX → PDF 변환 중 오류: {str(e)}")
        return False

# 파일 크기 초과 오류 처리
@app.errorhandler(413)
def too_large(e):
    flash('파일 크기가 100MB를 초과합니다. 더 작은 파일을 선택해주세요.')
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "pdf-vector"}), 200

@app.route('/')
def index():
    return render_template('index.html')

def _zip_paths(paths):
    """Create a ZIP file in memory from a list of file paths"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=os.path.basename(p))
    buf.seek(0)
    return buf

@app.route('/convert_to_vector', methods=['POST'])
def convert_to_vector():
    try:
        # Input validation
        f = request.files.get("file")
        if not f:
            logging.warning("convert_to_vector: No file provided")
            return jsonify({"error": "file is required"}), 400

        if not f.filename:
            logging.warning("convert_to_vector: Empty filename")
            return jsonify({"error": "filename is required"}), 400

        # Parameter validation
        mode = (request.form.get("mode") or "svg").lower()
        if mode not in ["svg", "ai"]:
            logging.warning(f"convert_to_vector: Invalid mode '{mode}'")
            return jsonify({"error": "mode must be svg or ai"}), 400

        pages_spec = request.form.get("pages")
        text_as_path = (request.form.get("text_as_path") or "false").lower() in ("1","true","yes","y","on")
        
        try:
            zoom = float(request.form.get("zoom") or 1.0)
            if zoom <= 0:
                raise ValueError("zoom must be positive")
        except (ValueError, TypeError) as e:
            logging.warning(f"convert_to_vector: Invalid zoom value: {e}")
            return jsonify({"error": "zoom must be a positive number"}), 400

        split = (request.form.get("split") or "true").lower() in ("1","true","yes","y","on")

        # File handling with improved security
        name = secure_filename(f.filename)
        if not name:
            logging.warning("convert_to_vector: Invalid filename after sanitization")
            return jsonify({"error": "invalid filename"}), 400

        # Add timestamp to prevent file conflicts
        import time
        timestamp = str(int(time.time()))
        safe_name = f"{timestamp}_{name}"
        in_pdf = os.path.join(UPLOAD_FOLDER, safe_name)
        
        try:
            f.save(in_pdf)
            logging.info(f"convert_to_vector: Saved input file to {in_pdf}")
        except Exception as e:
            logging.error(f"convert_to_vector: Failed to save input file: {e}")
            return jsonify({"error": "failed to save input file"}), 500

        # Verify PDF file with enhanced checks
        if not os.path.exists(in_pdf):
            logging.error(f"convert_to_vector: Input file does not exist: {in_pdf}")
            return jsonify({"error": "input file was not saved properly"}), 500
            
        file_size = os.path.getsize(in_pdf)
        if file_size == 0:
            logging.error(f"convert_to_vector: Input file is empty: {in_pdf}")
            return jsonify({"error": "input file is empty"}), 500
            
        if file_size < 100:  # PDF files should be at least 100 bytes
            logging.error(f"convert_to_vector: Input file too small ({file_size} bytes): {in_pdf}")
            return jsonify({"error": "input file appears to be corrupted"}), 500

        logging.info(f"convert_to_vector: Input file validated ({file_size} bytes)")

        out_dir = os.path.join(OUTPUT_FOLDER, os.path.splitext(safe_name)[0] + f"_{mode}")
        try:
            os.makedirs(out_dir, exist_ok=True)
            logging.info(f"convert_to_vector: Created output directory {out_dir}")
        except Exception as e:
            logging.error(f"convert_to_vector: Failed to create output directory: {e}")
            return jsonify({"error": "failed to create output directory"}), 500

        # Conversion with better error handling
        files = []
        try:
            if mode == "svg":
                logging.info(f"convert_to_vector: Converting to SVG with zoom={zoom}, text_as_path={text_as_path}, pages={pages_spec}")
                files = pdf_to_svgs(in_pdf, out_dir, text_as_path=text_as_path, zoom=zoom, pages_spec=pages_spec)
            elif mode == "ai":
                logging.info(f"convert_to_vector: Converting to AI with split={split}, pages={pages_spec}")
                if split or pages_spec:
                    files = split_pdf_to_ai_pages(in_pdf, out_dir, pages_spec=pages_spec, prefix="page")
                else:
                    out_ai = os.path.join(out_dir, os.path.splitext(name)[0] + ".ai")
                    save_pdf_as_ai(in_pdf, out_ai)
                    files = [out_ai]
        except Exception as e:
            logging.error(f"convert_to_vector: Conversion failed for mode '{mode}': {e}")
            # Clean up input file on conversion failure
            try:
                if os.path.exists(in_pdf):
                    os.remove(in_pdf)
            except:
                pass
            return jsonify({"error": f"conversion failed: {str(e)}"}), 500

        # File validation with detailed logging
        valid_files = []
        for file_path in files:
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 0:
                    valid_files.append(file_path)
                    logging.info(f"convert_to_vector: Valid output file: {os.path.basename(file_path)} ({file_size} bytes)")
                else:
                    logging.warning(f"convert_to_vector: Empty output file: {file_path}")
            else:
                logging.warning(f"convert_to_vector: Missing output file: {file_path}")

        if not valid_files:
            logging.error("convert_to_vector: No valid output files generated")
            # Clean up input file
            try:
                if os.path.exists(in_pdf):
                    os.remove(in_pdf)
            except:
                pass
            return jsonify({"error": "no output files generated"}), 500

        logging.info(f"convert_to_vector: Successfully generated {len(valid_files)} files")

        # Clean up input file after successful conversion
        try:
            if os.path.exists(in_pdf):
                os.remove(in_pdf)
                logging.info(f"convert_to_vector: Cleaned up input file {in_pdf}")
        except Exception as e:
            logging.warning(f"convert_to_vector: Failed to clean up input file: {e}")

        # Return files directly (single file or ZIP) with proper headers
        if len(valid_files) == 1:
            # Single file - return directly
            fp = valid_files[0]
            file_size = os.path.getsize(fp)
            
            # Determine MIME type based on file extension
            if fp.endswith('.svg'):
                mimetype = 'image/svg+xml'
            elif fp.endswith('.ai'):
                mimetype = 'application/postscript'
            else:
                mimetype = 'application/octet-stream'
            
            resp = send_file(fp, as_attachment=True, download_name=os.path.basename(fp), mimetype=mimetype)
            resp.headers["Content-Length"] = str(file_size)
            resp.headers["Content-Disposition"] = f'attachment; filename="{os.path.basename(fp)}"'
            logging.info(f"convert_to_vector: Returning single file {os.path.basename(fp)} ({file_size} bytes)")
            return resp
        else:
            # Multiple files - return as ZIP
            buf = _zip_paths(valid_files)
            buf.seek(0, os.SEEK_END)
            length = buf.tell()
            buf.seek(0)
            zip_name = f"{os.path.splitext(name)[0]}_{mode}.zip"
            resp = send_file(buf, mimetype="application/zip", as_attachment=True, download_name=zip_name)
            resp.headers["Content-Length"] = str(length)
            resp.headers["Content-Disposition"] = f'attachment; filename="{zip_name}"'
            logging.info(f"convert_to_vector: Returning ZIP file {zip_name} with {len(valid_files)} files ({length} bytes)")
            return resp

    except Exception as e:
        logging.exception("convert_to_vector: Unexpected error occurred")
        return jsonify({"error": f"internal server error: {str(e)}"}), 500

# /download_vector endpoint removed - no longer needed as /convert_to_vector returns files directly

@app.route('/convert', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("파일 업로드 요청 시작")
        
        # 1단계: 파일 존재 여부 확인
        if 'file' not in request.files:
            flash('파일이 선택되지 않았습니다.')
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        # 2단계: 파일명 확인
        if not file or file.filename == '' or file.filename is None:
            flash('파일이 선택되지 않았습니다.')
            return redirect(url_for('index'))
        
        # 3단계: 파일 내용 및 크기 확인 (강화된 검증)
        try:
            # 파일 포인터를 끝으로 이동하여 크기 확인
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)  # 파일 포인터를 다시 처음으로 이동
            
            # 파일 크기가 0인 경우 처리
            if file_size == 0:
                flash('업로드된 파일이 비어있습니다. 올바른 PDF 파일을 선택해주세요.')
                return redirect(url_for('index'))
            
            # 최소 파일 크기 확인 (PDF 헤더 최소 크기)
            if file_size < 100:  # 100바이트 미만은 유효한 PDF가 아님
                flash('파일이 너무 작습니다. 올바른 PDF 파일을 선택해주세요.')
                return redirect(url_for('index'))
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                flash(f'파일 크기가 너무 큽니다. (현재: {file_size // (1024*1024)}MB, 최대: 100MB)')
                return redirect(url_for('index'))
            
            print(f"파일 크기: {file_size // (1024*1024) if file_size >= 1024*1024 else file_size // 1024}{'MB' if file_size >= 1024*1024 else 'KB'}")
            
            # 4단계: PDF 파일 헤더 검증
            file_content = file.read(10)  # 처음 10바이트 읽기
            file.seek(0)  # 다시 처음으로 이동
            
            if not file_content.startswith(b'%PDF-'):
                flash('올바른 PDF 파일이 아닙니다. PDF 파일을 선택해주세요.')
                return redirect(url_for('index'))
                
        except Exception as e:
            print(f"파일 검증 중 오류: {str(e)}")
            flash('파일을 읽는 중 오류가 발생했습니다. 다른 파일을 시도해주세요.')
            return redirect(url_for('index'))
        
        # 5단계: 파일 형식 확인 및 처리 (강화된 검증)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # 파일 확장자 안전하게 추출 (list index out of range 오류 방지)
            if '.' not in filename:
                flash('파일 확장자가 없습니다. PDF 파일을 선택해주세요.')
                return redirect(url_for('index'))
            
            file_ext = filename.rsplit('.', 1)[1].lower()
            if file_ext != 'pdf':
                flash('PDF 파일만 업로드 가능합니다.')
                return redirect(url_for('index'))
            
            # 안전한 파일명 생성 (타임스탬프 추가로 중복 방지)
            import time
            timestamp = str(int(time.time()))
            safe_filename = f"{timestamp}_{filename}"
            input_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            
            print(f"파일 저장 중 - {input_path}")
            try:
                # 파일 저장 전 디렉토리 존재 확인
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(input_path)
                
                # 저장된 파일 크기 재확인
                saved_file_size = os.path.getsize(input_path)
                if saved_file_size == 0:
                    os.remove(input_path)
                    flash('파일 저장 중 오류가 발생했습니다. 다시 시도해주세요.')
                    return redirect(url_for('index'))
                
                print(f"파일 저장 완료 - 크기: {saved_file_size}바이트")
            except Exception as e:
                print(f"파일 저장 오류: {str(e)}")
                flash(f'파일 저장 중 오류가 발생했습니다: {str(e)}')
                return redirect(url_for('index'))
            
            # 변환 처리
            conversion_success = False
            output_path = None
            
            if file_ext == 'pdf':
                # PDF → DOCX 변환
                # 파일명에서 확장자 제거 (안전하게)
                base_filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
                output_filename = base_filename + '.docx'
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                quality = request.form.get('quality', 'medium')
                print(f"PDF → DOCX 변환 시작 - {input_path} -> {output_path}")
                
                try:
                    conversion_success = pdf_to_docx(input_path, output_path, quality)
                except Exception as e:
                    print(f"변환 중 예외 발생: {str(e)}")
                    flash(f'변환 중 오류가 발생했습니다: {str(e)}')
                    
            elif file_ext == 'docx':
                # DOCX → PDF 변환
                # 파일명에서 확장자 제거 (안전하게)
                base_filename = filename.rsplit('.', 1)[0] if '.' in filename else filename
                output_filename = base_filename + '.pdf'
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                print(f"DOCX → PDF 변환 시작 - {input_path} -> {output_path}")
                
                try:
                    conversion_success = docx_to_pdf(input_path, output_path)
                except Exception as e:
                    print(f"변환 중 예외 발생: {str(e)}")
                    flash(f'변환 중 오류가 발생했습니다: {str(e)}')
            
            # 변환 결과 처리
            if conversion_success:
                print("변환 성공 - 다운로드 준비")
                
                # 업로드된 파일 정리
                try:
                    os.remove(input_path)
                    print("임시 파일 삭제 완료")
                except Exception as e:
                    print(f"임시 파일 삭제 실패 (무시됨): {e}")
                
                # 파일 다운로드 제공
                try:
                    print("파일 다운로드 시작")
                    return send_file(output_path, as_attachment=True, download_name=output_filename)
                except Exception as e:
                    print(f"파일 다운로드 오류: {str(e)}")
                    flash(f'파일 다운로드 중 오류가 발생했습니다: {str(e)}')
                    return redirect(url_for('index'))
            else:
                print("변환 실패 - 정리 작업")
                flash('파일 변환에 실패했습니다. 다시 시도해주세요.')
                
                # 실패한 파일들 정리
                for cleanup_path in [input_path, output_path]:
                    try:
                        if cleanup_path and os.path.exists(cleanup_path):
                            os.remove(cleanup_path)
                    except Exception as e:
                        print(f"파일 정리 실패 (무시됨): {e}")
                
                return redirect(url_for('index'))
        else:
            flash('PDF 또는 DOCX 파일만 업로드 가능합니다.')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"업로드 처리 중 예외 발생: {str(e)}")
        flash('파일 처리 중 오류가 발생했습니다.')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)