from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
import os
import tempfile
from werkzeug.utils import secure_filename
import io
from PIL import Image
import json
from dotenv import load_dotenv
import subprocess
import platform
# import cv2  # Removed to fix ModuleNotFoundError
# import numpy as np  # Removed to fix ModuleNotFoundError
import fitz  # PyMuPDF
import re
from typing import List, Tuple, Dict, Any
# Adobe PDF Services SDK 임포트 및 설정
try:
    # 올바른 Adobe PDF Services SDK import 구문
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
    from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult
    
    adobe_available = True
    ADOBE_SDK_AVAILABLE = True
    print("Adobe PDF Services SDK가 성공적으로 로드되었습니다.")
except ImportError as e:
    print(f"Adobe PDF Services SDK를 가져올 수 없습니다: {e}")
    print("Adobe SDK 없이 계속 진행합니다.")
    adobe_available = False
    ADOBE_SDK_AVAILABLE = False

# Adobe SDK 무조건 실행 모드 활성화
ADOBE_SDK_AVAILABLE = True
print(f"Adobe SDK 강제 실행 모드: {ADOBE_SDK_AVAILABLE}")

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return jsonify({
        "ok": True,
        "python": platform.python_version(),
        "service": "pdf-image"
    }), 200

# Adobe PDF Services API 구성 - 실제 인증 정보 사용
ADOBE_CONFIG = {
    "client_credentials": {
        "client_id": "243b50af2e834d90a9f4985c58dc74f4",
        "client_secret": "p8e-Zx1xRwlGWDut-fYK66EpUPJhfd-oi9_4"
    },
    "service_principal_credentials": {
        "organization_id": "3C67227E688C66000A495C72@AdobeOrg",
        "account_id": "461C220C68CBF68A0A495C65@techacct.adobe.com",
        "technical_account_email": "ab9c4481-e7f0-4361-9a0a-67eda3b9222b@techacct.adobe.com",
        "private_key_file": "private.key",
        "access_token": os.getenv("ADOBE_ACCESS_TOKEN", "")
    }
}

# Adobe SDK 무조건 실행 확인
print(f"Adobe SDK 강제 실행 상태: {ADOBE_SDK_AVAILABLE}")
print(f"Adobe 클라이언트 ID: {ADOBE_CONFIG['client_credentials']['client_id']}")
print("Adobe PDF Services API가 무조건 실행되도록 설정되었습니다.")



UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

# 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs('debug_output', exist_ok=True)  # 디버깅용 폴더

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 디버깅용 중간 결과물 저장 함수들
def save_debug_text(text, filename_prefix):
    """추출된 텍스트를 디버깅용 .txt 파일로 저장"""
    try:
        debug_file = os.path.join('debug_output', f'{filename_prefix}_extracted_text.txt')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"디버깅: 텍스트가 {debug_file}에 저장되었습니다. (길이: {len(text)}자)")
        return debug_file
    except Exception as e:
        print(f"디버깅 텍스트 저장 오류: {e}")
        return None

def save_debug_image(image, filename_prefix, page_num):
    """변환된 이미지를 디버깅용 .png 파일로 저장"""
    try:
        debug_file = os.path.join('debug_output', f'{filename_prefix}_page_{page_num}.png')
        image.save(debug_file, 'PNG')
        print(f"디버깅: 이미지가 {debug_file}에 저장되었습니다.")
        return debug_file
    except Exception as e:
        print(f"디버깅 이미지 저장 오류: {e}")
        return None

# pdf_to_docx_with_pymupdf function removed - docx dependency removed

# OCR 기능이 제거되었습니다 - pytesseract 의존성 제거로 인해
# def ocr_image_to_blocks(pil_image):
#     """이미지에서 단어 단위 텍스트와 위치(좌표)를 추출"""
#     OCR 기능이 제거되어 빈 리스트를 반환합니다.
def ocr_image_to_blocks(pil_image):
    """OCR 기능이 제거되었습니다 - pytesseract 의존성 제거"""
    print("OCR 기능이 제거되었습니다. PDF to image 변환만 지원됩니다.")
    return []

def clean_special_characters(text: str) -> str:
    """특수 문자 처리 개선 - PDF에서 잘못 추출되는 문자들을 올바르게 복구"""
    if not text:
        return text
    
    # 일반적인 PDF 추출 오류 수정
    replacements = {
        '\uf0b7': '•',  # 불릿 포인트
        '\uf0a7': '§',  # 섹션 기호
        '\uf0e0': '→',  # 화살표
        '\u2022': '•',  # 불릿 포인트
        '\u201C': '"',  # 왼쪽 큰따옴표
        '\u201D': '"',  # 오른쪽 큰따옴표
        '\u2018': "'",  # 왼쪽 작은따옴표
        '\u2019': "'",  # 오른쪽 작은따옴표
        '\u2013': '–',  # en dash
        '\u2014': '—',  # em dash
        '\u00A0': ' ',  # 줄바꿈 없는 공백
        '\u200B': '',   # 폭이 0인 공백
        '\uFEFF': '',   # 바이트 순서 표시
    }
    
    # 특수 문자 변환
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 연속된 공백 정리
    text = re.sub(r'[\s\t\n\r]+', ' ', text)
    
    # 제로 폭 문자 제거
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    return text.strip()

def analyze_pdf_orientation(pdf_path: str) -> Dict[str, Any]:
    """PDF 페이지 크기를 분석하여 문서 방향 감지"""
    try:
        doc = fitz.open(pdf_path)
        page_orientations = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_rect = page.rect
            width = page_rect.width
            height = page_rect.height
            
            # 가로/세로 방향 판단
            if width > height:
                orientation = 'landscape'  # 가로형
            else:
                orientation = 'portrait'   # 세로형
            
            page_orientations.append({
                'page': page_num,
                'width': width,
                'height': height,
                'orientation': orientation,
                'aspect_ratio': width / height
            })
        
        doc.close()
        
        # 전체 문서의 주요 방향 결정
        landscape_count = sum(1 for p in page_orientations if p['orientation'] == 'landscape')
        portrait_count = len(page_orientations) - landscape_count
        
        primary_orientation = 'landscape' if landscape_count > portrait_count else 'portrait'
        
        return {
            'page_orientations': page_orientations,
            'primary_orientation': primary_orientation,
            'landscape_pages': landscape_count,
            'portrait_pages': portrait_count,
            'total_pages': len(page_orientations)
        }
        
    except Exception as e:
        print(f"PDF 방향 분석 중 오류: {e}")
        return {
            'page_orientations': [],
            'primary_orientation': 'portrait',
            'landscape_pages': 0,
            'portrait_pages': 0,
            'total_pages': 0
        }

def extract_text_with_layout_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """PDF에서 레이아웃 정보와 함께 텍스트 추출 (방향 감지 포함)"""
    try:
        doc = fitz.open(pdf_path)
        all_text_blocks = []
        
        # PDF 방향 분석
        orientation_info = analyze_pdf_orientation(pdf_path)
        print(f"PDF 방향 분석 결과: {orientation_info['primary_orientation']} (가로: {orientation_info['landscape_pages']}, 세로: {orientation_info['portrait_pages']})")
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_rect = page.rect
            
            # 텍스트 블록 추출
            text_blocks = page.get_text("dict")
            
            for block in text_blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        line_bbox = line["bbox"]
                        
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            if span_text.strip():
                                line_text += span_text
                        
                        if line_text.strip():
                            # 텍스트 정렬 감지
                            text_center = (line_bbox[0] + line_bbox[2]) / 2
                            page_center = page_rect.width / 2
                            
                            if abs(text_center - page_center) < 20:
                                alignment = 'center'
                            elif (page_rect.width - line_bbox[2]) < (line_bbox[0]):
                                alignment = 'right'
                            else:
                                alignment = 'left'
                            
                            all_text_blocks.append({
                                'text': clean_special_characters(line_text),
                                'bbox': line_bbox,
                                'page': page_num,
                                'alignment': alignment
                            })
        
        doc.close()
        
        # 텍스트 블록들을 위치 순서대로 정렬
        all_text_blocks.sort(key=lambda x: (x['page'], x['bbox'][1], x['bbox'][0]))
        
        return {
            'text_blocks': all_text_blocks,
            'full_text': '\n'.join([block['text'] for block in all_text_blocks]),
            'orientation_info': orientation_info
        }
        
    except Exception as e:
        print(f"PDF 레이아웃 추출 중 오류: {e}")
        return {'text_blocks': [], 'full_text': ''}

def extract_text_blocks_with_ocr(image):
    """OCR 기능이 제거되었습니다 - pytesseract 의존성 제거"""
    print("OCR 기능이 제거되었습니다. PDF to image 변환만 지원됩니다.")
    return ""

def extract_pdf_content_with_adobe(pdf_path):
    """Adobe PDF Services API를 사용하여 PDF 내용을 추출하는 함수"""
    if not ADOBE_SDK_AVAILABLE:
        print("Adobe PDF Services SDK를 사용할 수 없습니다.")
        return None
        
    try:
        # Adobe API 자격 증명 설정 (올바른 클래스 사용)
        credentials = ServicePrincipalCredentials(
            client_id=ADOBE_CONFIG["client_credentials"]["client_id"],
            client_secret=ADOBE_CONFIG["client_credentials"]["client_secret"]
        )
        
        # PDF Services 인스턴스 생성
        pdf_services = PDFServices(credentials=credentials)
        
        # PDF 파일을 스트림으로 읽기
        with open(pdf_path, 'rb') as file:
            input_stream = file.read()
        
        # StreamAsset 생성
        input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)
        
        print("Adobe API를 사용하여 PDF 내용을 처리했습니다.")
        return input_asset
            
    except (ServiceApiException, ServiceUsageException, SdkException) as e:
        print(f"Adobe API 오류: {str(e)}")
        return None
    except Exception as e:
        print(f"일반 오류: {str(e)}")
        return None

# pdf_to_docx function removed - docx dependency removed

# docx_to_pdf function removed - docx dependency removed

# 파일 크기 초과 오류 처리
@app.errorhandler(413)
def too_large(e):
    flash('파일 크기가 100MB를 초과합니다. 더 작은 파일을 선택해주세요.')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
@app.route('/upload', methods=['POST'])
@app.route('/convert_to_images', methods=['POST'])
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
                # PDF → 이미지 변환 (PyMuPDF 사용)
                try:
                    from converters.pdf_to_images import pdf_to_images
                    
                    # 출력 디렉토리 생성
                    output_dir = os.path.join(OUTPUT_FOLDER, f"{timestamp}_images")
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # PDF를 이미지로 변환
                    image_paths = pdf_to_images(input_path, output_dir, fmt="png", dpi=150)
                    
                    if image_paths:
                        # ZIP 파일로 압축
                        import zipfile
                        zip_filename = f"{timestamp}_pdf_images.zip"
                        zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
                        
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for img_path in image_paths:
                                zipf.write(img_path, os.path.basename(img_path))
                        
                        # 임시 이미지 파일들 정리
                        for img_path in image_paths:
                            try:
                                os.remove(img_path)
                            except:
                                pass
                        
                        # 임시 디렉토리 정리
                        try:
                            os.rmdir(output_dir)
                        except:
                            pass
                        
                        conversion_success = True
                        output_path = zip_path
                        output_filename = zip_filename
                        
                    else:
                        flash('PDF 변환에 실패했습니다.')
                        return redirect(url_for('index'))
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"PDF 변환 오류: {error_msg}")
                    
                    # 사용자 친화적인 오류 메시지 제공
                    if "암호로 보호" in error_msg or "encrypted" in error_msg.lower():
                        flash('PDF 파일이 암호로 보호되어 있습니다. 암호가 없는 PDF 파일을 사용해주세요.')
                    elif "손상" in error_msg or "지원되지 않는" in error_msg:
                        flash('PDF 파일을 열 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.')
                    elif "페이지가 없습니다" in error_msg:
                        flash('PDF 파일에 페이지가 없습니다. 올바른 PDF 파일을 업로드해주세요.')
                    else:
                        flash(f'PDF 변환 중 오류가 발생했습니다: {error_msg}')
                    
                    return redirect(url_for('index'))
                    
            elif file_ext == 'docx':
                # DOCX 기능 제거됨
                flash('DOCX 파일 처리는 현재 지원되지 않습니다.')
                return redirect(url_for('index'))
            
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
            flash('PDF 파일만 업로드 가능합니다.')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"업로드 처리 중 예외 발생: {str(e)}")
        flash('파일 처리 중 오류가 발생했습니다.')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)