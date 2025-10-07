from flask import Flask, request, render_template, send_file, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from docx import Document
import fitz
import PyPDF2
import io
import subprocess
import tempfile
import os
import pandas as pd
import re
import platform
from pptx import Presentation
from pptx.util import Inches as PptxInches
from pptx.enum.text import PP_ALIGN

app = Flask(__name__)
CORS(app)

@app.route("/health")
def health():
    return "ok", 200

ADOBE_SDK_AVAILABLE = False
ADOBE_CONFIG = {
    "client_credentials": {
        "client_id": "",
        "client_secret": ""
    }
}

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

def allowed_file(filename, content_type):
    """허용된 파일 확인"""
    return content_type.lower().startswith('application/pdf')

def extract_text_blocks_with_ocr(image):
    """OCR로 텍스트 추출"""
    import pytesseract
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(image.tobytes()))
    ocr_text = pytesseract.image_to_string(image, lang='kor+eng')
    if ocr_text:
        return ocr_text
    else:
        return None

def extract_text_with_layout_from_pdf(pdf_path):
    """PDF 내용을 추출하는 함수"""
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        if page_text:
            return {
                'full_text': page_text,
                'text_blocks': [block for block in page.extract_text().split('\n') if block.strip()],
                'orientation_info': page.get_orientation_info()
            }
    return None

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
        print(f"전체 처리 중 오류 발생: {str(e)}")
        return {'success': False, 'error': f'서버 오류가 발생했습니다: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
        print(f"일반 오류: {str(e)}")
        return None

def pdf_to_xlsx(pdf_path, output_path, quality='medium'):
    """PDF를 XLSX로 변환하는 함수 (텍스트 추출 후 Excel 시트로 구조화)"""
    try:
        # 파일명에서 확장자 제거하여 디버깅용 prefix 생성
        filename_prefix = os.path.splitext(os.path.basename(pdf_path))[0]
        
        print("=== PDF → EXCEL 변환 시작 ===")
        print(f"입력 파일: {pdf_path}")
        print(f"출력 파일: {output_path}")
        # 1단계: PDF에서 텍스트 추출
        print("1단계: PDF에서 텍스트 추출 중...")
        extracted_text = ""
        
        # PyPDF2를 사용한 텍스트 추출 시도
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += f"페이지 {page_num + 1}:\n{page_text}\n\n"
                        
            if extracted_text:
                print(f"PyPDF2로 텍스트 추출 성공: {len(extracted_text)}자")
            else:
                print("PyPDF2로 텍스트 추출 실패, PyMuPDF 시도...")
                
        except Exception as e:
            print(f"PyPDF2 텍스트 추출 오류: {e}")
            
        # PyMuPDF를 사용한 텍스트 추출 (fallback)
        if not extracted_text:
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        extracted_text += f"페이지 {page_num + 1}:\n{page_text}\n\n"
                doc.close()
                
                if extracted_text:
                    print(f"PyMuPDF로 텍스트 추출 성공: {len(extracted_text)}자")
                else:
                    print("PyMuPDF로도 텍스트 추출 실패")
                    
            except Exception as e:
                print(f"PyMuPDF 텍스트 추출 오류: {e}")
        
        # 2단계: 텍스트가 없으면 OCR 시도
        if not extracted_text:
            print("2단계: OCR을 통한 텍스트 추출 시도...")
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # 페이지를 이미지로 변환
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # PIL Image로 변환
                    from PIL import Image
                    import io
                    image = Image.open(io.BytesIO(img_data))
                    
                    # OCR 수행
                    ocr_text = pytesseract.image_to_string(image, lang='kor+eng')
                    if ocr_text:
                        extracted_text += f"페이지 {page_num + 1}:\n{ocr_text}\n\n"
                        
                doc.close()
                
                if extracted_text:
                    print(f"OCR로 텍스트 추출 성공: {len(extracted_text)}자")
                else:
                    print("OCR로도 텍스트 추출 실패")
                    
            except Exception as e:
                print(f"OCR 텍스트 추출 오류: {e}")
        
        # 3단계: Excel 파일 생성
        print("3단계: Excel 파일 생성 중...")
        
        # pandas DataFrame 생성
        df_data = []
        
        if extracted_text:
            # 텍스트를 줄 단위로 분할
            lines = extracted_text.split('\n')
            
            # 빈 줄 제거 및 정리 (특수문자 필터링 추가)
            def clean_text(text):
                """텍스트에서 Excel에서 문제가 되는 특수문자 제거"""
                import re
                # Excel에서 문제가 되는 특수문자 패턴 제거
                # 제어 문자, 비표준 유니코드 문자 등 제거
                text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
                # 문제가 되는 특수 기호들 제거
                text = re.sub(r'[±Æ½®ÅìºÁ8Á]', '', text)
                # 연속된 공백을 하나로 변경
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
            
            cleaned_lines = [clean_text(line) for line in lines if line.strip() and clean_text(line)]
            
            # 페이지별로 데이터 구성
            current_page = 1
            for line in cleaned_lines:
                if line.startswith('페이지'):
                    # 페이지 번호 추출
                    try:
                        page_match = re.search(r'페이지 (\d+)', line)
                        if page_match:
                            current_page = int(page_match.group(1))
                    except:
                        pass
                    continue
                
                # 데이터 행 추가 (텍스트 정리 적용)
                cleaned_content = clean_text(line)
                if cleaned_content:  # 정리 후에도 내용이 있는 경우만 추가
                    df_data.append({
                        '페이지': current_page,
                        '내용': cleaned_content,
                        '길이': len(cleaned_content)
                    })
        
        # DataFrame이 비어있으면 기본 데이터 추가
        if not df_data:
            df_data.append({
                '페이지': 1,
                '내용': 'No text could be extracted',
                '길이': 0
            })
        
        # pandas DataFrame 생성
        df = pd.DataFrame(df_data)
        
        print(f"Excel 데이터 생성 완료: {len(df)}행")
        
        # 4단계: Excel 파일 저장
        print("4단계: Excel 파일 저장 중...")
        
        try:
            # ExcelWriter를 사용하여 Excel 파일 생성 (UTF-8 인코딩 보장)
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 메인 데이터 시트
                df.to_excel(writer, sheet_name='PDF_Content', index=False)
                
                # 요약 정보 시트 추가
                summary_data = {
                    '항목': ['총 페이지 수', '총 텍스트 행 수', '평균 텍스트 길이', '변환 일시'],
                    '값': [
                        df['페이지'].max() if not df.empty else 0,
                        len(df),
                        df['길이'].mean() if not df.empty else 0,
                        pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary_Info', index=False)
                
                # 워크시트 스타일링
                workbook = writer.book
                
                # 메인 시트 스타일링
                if 'PDF_Content' in writer.sheets:
                    worksheet = writer.sheets['PDF_Content']
                    
                    # 헤더 스타일 적용
                    from openpyxl.styles import Font, PatternFill, Alignment
                    header_font = Font(bold=True, color='FFFFFF')
                    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
                    
                    for cell in worksheet[1]:
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal='center')
                    
                    # 열 너비 자동 조정 및 셀 값 안전성 확보
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                # 셀 값이 문자열인 경우 특수문자 정리
                                if cell.value and isinstance(cell.value, str):
                                    cleaned_value = clean_text(str(cell.value))
                                    cell.value = cleaned_value
                                    cell_length = len(cleaned_value)
                                else:
                                    cell_length = len(str(cell.value)) if cell.value else 0
                                
                                if cell_length > max_length:
                                    max_length = cell_length
                            except Exception as cell_error:
                                print(f"셀 처리 중 오류: {cell_error}")
                                # 오류가 발생한 셀은 빈 값으로 설정
                                cell.value = ""
                        adjusted_width = min(max_length + 2, 50)  # 최대 50자로 제한
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # 요약 시트 스타일링
                if 'Summary_Info' in writer.sheets:
                    summary_worksheet = writer.sheets['Summary_Info']
                    
                    # 헤더 스타일 적용
                    for cell in summary_worksheet[1]:
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal='center')
                    
                    # 열 너비 조정
                    summary_worksheet.column_dimensions['A'].width = 20
                    summary_worksheet.column_dimensions['B'].width = 30
            
            print(f"Excel 파일 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            print(f"Excel 파일 저장 중 오류: {e}")
            print(f"오류 타입: {type(e).__name__}")
            print(f"오류 세부사항: {str(e)}")
            
            # 파일이 생성되었다면 삭제
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                    print(f"오류로 인해 불완전한 파일을 삭제했습니다: {output_path}")
            except:
                pass
            
            return False
        
        
        print(f"PDF → EXCEL 변환 완료: {output_path}")
        return True
        
    except Exception as e:
        print(f"PDF → EXCEL 변환 중 오류 발생: {str(e)}")
        return False

def pdf_to_pptx(pdf_path, output_path, quality='medium'):
    """PDF를 PPTX로 변환하는 함수 (Adobe API 통합 및 OCR 텍스트 추출, 방향 자동 감지)"""
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
        images = convert_from_path(pdf_path, dpi=settings['dpi'], fmt=settings['format'])
        
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
                                from docx.shared import Pt
                                if len(block['text']) < 50 and block['alignment'] == 'center':
                                    p.font.size = Pt(18)  # 제목용 크기
                                else:
                                    p.font.size = Pt(14)  # 본문용 크기
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
                    
                    # 슬라이드에 이미지 추가 (원본 비율 유지, 중앙 배치)
                    left = Inches((13.33 - target_width) / 2) if primary_orientation == 'landscape' else Inches((7.5 - target_width) / 2)
                    top = Inches((7.5 - target_height) / 2) if primary_orientation == 'landscape' else Inches((13.33 - target_height) / 2)
                    slide.shapes.add_picture(temp_img_path, left, top, width=Inches(target_width), height=Inches(target_height))
                    
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

# Health check endpoint for Render deployment
@app.route('/health')
def health_check():
    """Health check endpoint for Render deployment monitoring"""
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("파일 업로드 요청 시작")
        
        # 1단계: 파일 존재 여부 확인
        if 'file' not in request.files:
            print('오류: 파일이 선택되지 않았습니다.')
            return {'success': False, 'error': '파일이 선택되지 않았습니다.'}, 400
        
        file = request.files['file']
        
        # 2단계: 파일명 확인
        if not file or file.filename == '' or file.filename is None:
            print('오류: 파일이 선택되지 않았습니다.')
            return {'success': False, 'error': '파일이 선택되지 않았습니다.'}, 400
        
        # 3단계: 파일 내용 및 크기 확인 (강화된 검증)
        try:
            # 파일 포인터를 끝으로 이동하여 크기 확인
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)  # 파일 포인터를 다시 처음으로 이동
            
            # 파일 크기가 0인 경우 처리
            if file_size == 0:
                print('오류: 업로드된 파일이 비어있습니다.')
                return {'success': False, 'error': '업로드된 파일이 비어있습니다. 올바른 PDF 파일을 선택해주세요.'}, 400
            
            # 최소 파일 크기 확인 (PDF 헤더 최소 크기)
            if file_size < 100:  # 100바이트 미만은 유효한 PDF가 아님
                print('오류: 파일이 너무 작습니다.')
                return {'success': False, 'error': '파일이 너무 작습니다. 올바른 PDF 파일을 선택해주세요.'}, 400
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                print(f'오류: 파일 크기가 너무 큽니다. (현재: {file_size // (1024*1024)}MB, 최대: 100MB)')
                return {'success': False, 'error': f'파일 크기가 너무 큽니다. (현재: {file_size // (1024*1024)}MB, 최대: 100MB)'}, 400
            
            print(f"파일 크기: {file_size // (1024*1024) if file_size >= 1024*1024 else file_size // 1024}{'MB' if file_size >= 1024*1024 else 'KB'}")
            
            # 4단계: PDF 파일 헤더 검증
            file_content = file.read(10)  # 처음 10바이트 읽기
            file.seek(0)  # 다시 처음으로 이동
            
            if not file_content.startswith(b'%PDF-'):
                print('오류: 올바른 PDF 파일이 아닙니다.')
                return {'success': False, 'error': '올바른 PDF 파일이 아닙니다. PDF 파일을 선택해주세요.'}, 400
                
        except Exception as e:
            print(f"파일 검증 중 오류: {str(e)}")
            return {'success': False, 'error': '파일을 읽는 중 오류가 발생했습니다. 다른 파일을 시도해주세요.'}, 500
        
        # 5단계: 파일 형식 확인 및 처리 (강화된 검증)
        print(f"디버깅: 파일 MIME 타입 - '{file.content_type}'")
        if file and allowed_file(file.filename, file.content_type):
            filename = secure_filename(file.filename)
            
            # 파일 확장자 안전하게 추출 (list index out of range 오류 방지)
            file_ext = None
            if '.' in filename:
                try:
                    file_ext = filename.rsplit('.', 1)[1].lower()
                    print(f"디버깅: 최종 확장자 확인 - '{file_ext}'")
                except (IndexError, AttributeError) as e:
                    print(f'오류: 파일 확장자 추출 실패 - {e}')
                    return {'success': False, 'error': '파일 확장자를 확인할 수 없습니다. PDF 파일을 선택해주세요.'}, 400
            else:
                # 확장자가 없는 경우 MIME 타입으로 판단
                if file.content_type and 'pdf' in file.content_type.lower():
                    file_ext = 'pdf'
                    print(f"디버깅: MIME 타입으로 PDF 확인됨 - '{file.content_type}'")
                else:
                    print(f'오류: 파일 확장자가 없고 MIME 타입도 PDF가 아님 - MIME: {file.content_type}')
                    return {'success': False, 'error': '파일 확장자가 없습니다. PDF 파일을 선택해주세요.'}, 400
            
            if file_ext != 'pdf':
                print(f'오류: PDF 파일만 업로드 가능합니다. 현재: {file_ext}')
                return {'success': False, 'error': 'PDF 파일만 업로드 가능합니다.'}, 400
            
            # 안전한 파일명 생성 (원본 파일명 유지)
            import time
            timestamp = str(int(time.time()))
            # 중복 방지를 위해 타임스탬프를 내부적으로만 사용
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
                    print('오류: 파일 저장 중 오류가 발생했습니다.')
                    return {'success': False, 'error': '파일 저장 중 오류가 발생했습니다. 다시 시도해주세요.'}, 500
                
                print(f"파일 저장 완료 - 크기: {saved_file_size}바이트")
            except Exception as e:
                print(f"파일 저장 오류: {str(e)}")
                return {'success': False, 'error': f'파일 저장 중 오류가 발생했습니다: {str(e)}'}, 500
            
            # 변환 처리
            conversion_success = False
            output_path = None
            
            if file_ext == 'pdf':
                # PDF → EXCEL 변환
                # 원본 파일명에서 확장자 제거 (타임스탬프 없이)
                original_filename = file.filename  # 원본 파일명 사용
                # 한글 파일명 UTF-8 인코딩 보장
                try:
                    # 파일명이 올바른 UTF-8인지 확인하고 필요시 재인코딩
                    original_filename = original_filename.encode('utf-8').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # 인코딩 문제가 있는 경우 안전한 파일명으로 변경
                    original_filename = secure_filename(original_filename)
                
                base_filename = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
                output_filename = base_filename + '.xlsx'
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                quality = request.form.get('quality', 'medium')
                print(f"PDF → EXCEL 변환 시작 - {input_path} -> {output_path}")
                
                try:
                    conversion_success = pdf_to_xlsx(input_path, output_path, quality)
                except Exception as e:
                    print(f"변환 중 예외 발생: {str(e)}")
                    return {'success': False, 'error': f'변환 중 오류가 발생했습니다: {str(e)}'}, 500
                    
            elif file_ext == 'docx':
                # DOCX → PDF 변환
                # 원본 파일명에서 확장자 제거 (타임스탬프 없이)
                original_filename = file.filename  # 원본 파일명 사용
                # 한글 파일명 UTF-8 인코딩 보장
                try:
                    # 파일명이 올바른 UTF-8인지 확인하고 필요시 재인코딩
                    original_filename = original_filename.encode('utf-8').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # 인코딩 문제가 있는 경우 안전한 파일명으로 변경
                    original_filename = secure_filename(original_filename)
                
                base_filename = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
                output_filename = base_filename + '.pdf'
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                print(f"DOCX → PDF 변환 시작 - {input_path} -> {output_path}")
                
                try:
                    conversion_success = docx_to_pdf(input_path, output_path)
                except Exception as e:
                    print(f"변환 중 예외 발생: {str(e)}")
                    return {'success': False, 'error': f'변환 중 오류가 발생했습니다: {str(e)}'}, 500
            
            # 변환 결과 처리
            if conversion_success:
                print("변환 성공 - 다운로드 준비")
                
                # 업로드된 파일 정리
                try:
                    os.remove(input_path)
                    print("임시 파일 삭제 완료")
                except Exception as e:
                    print(f"임시 파일 삭제 실패 (무시됨): {e}")
                
                # JSON 응답으로 다운로드 URL 제공
                try:
                    download_url = f'/download/{output_filename}'
                    return {'success': True, 'download_url': download_url, 'filename': output_filename}, 200
                except Exception as e:
                    print(f"응답 생성 오류: {str(e)}")
                    return {'success': False, 'error': f'응답 생성 중 오류가 발생했습니다: {str(e)}'}, 500
            else:
                print("변환 실패 - 정리 작업")
                
                # 실패한 파일들 정리
                for cleanup_path in [input_path, output_path]:
                    try:
                        if cleanup_path and os.path.exists(cleanup_path):
                            os.remove(cleanup_path)
                    except Exception as e:
                        print(f"파일 정리 실패 (무시됨): {e}")
                
                return {'success': False, 'error': '파일 변환에 실패했습니다. 다시 시도해주세요.'}, 500
        else:
            return {'success': False, 'error': 'PDF 파일만 업로드 가능합니다.'}, 400
            
    except Exception as e: