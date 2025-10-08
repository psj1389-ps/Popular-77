import os
import io
import zipfile
from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
import fitz  # PyMuPDF
import base64

app = Flask(__name__)

def convert_to_ai(img):
    """
    PIL Image를 AI(PDF) 파일로 변환하는 함수
    """
    try:
        # 이미지 처리
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # 이미지를 PDF로 변환하여 메모리에 저장
        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, "PDF", resolution=100.0)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
        
    except Exception as e:
        raise Exception(f"AI(PDF) 변환 중 오류 발생: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

def parse_page_numbers(page_numbers_str, total_pages):
    """
    페이지 번호 문자열을 파싱하여 페이지 리스트 반환
    예: '1,3,5-7' -> [1, 3, 5, 6, 7]
    """
    pages = set()
    parts = page_numbers_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # 범위 처리 (예: 5-7)
            start, end = part.split('-')
            start, end = int(start.strip()), int(end.strip())
            for p in range(start, end + 1):
                if 1 <= p <= total_pages:
                    pages.add(p)
        else:
            # 단일 페이지
            p = int(part)
            if 1 <= p <= total_pages:
                pages.add(p)
    
    return sorted(list(pages))

@app.route('/convert_to_ai', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400
    
    try:
        # 업로드된 파일을 메모리에서 직접 처리
        pdf_data = file.read()
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
        
        # AI 변환 옵션 가져오기
        page_range = request.form.get('page_range', 'all')
        page_numbers_str = request.form.get('page_numbers', '')
        
        # 페이지 수 확인
        page_count = len(pdf_document)
        original_name = os.path.splitext(file.filename)[0]
        
        # 처리할 페이지 결정
        if page_range == 'specific' and page_numbers_str:
            try:
                pages_to_process = parse_page_numbers(page_numbers_str, page_count)
                if not pages_to_process:
                    return jsonify({'error': '유효한 페이지 번호가 없습니다.'}), 400
            except ValueError:
                return jsonify({'error': '페이지 번호 형식이 올바르지 않습니다. (예: 1,3,5-7)'}), 400
        else:
            # 모든 페이지 처리
            pages_to_process = list(range(1, page_count + 1))
        
        if len(pages_to_process) == 1:
            # 단일 페이지 처리
            page_num = pages_to_process[0] - 1  # 0-based index
            page = pdf_document[page_num]
            
            # 페이지를 이미지로 렌더링 (고해상도)
            matrix = fitz.Matrix(2.0, 2.0)  # 2배 확대
            pix = page.get_pixmap(matrix=matrix)
            
            # PIL Image로 변환
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # AI 변환
            ai_content_bytes = convert_to_ai(img)
            
            # 단일 AI 파일 반환
            ai_filename = f"{original_name}.ai"
            ai_buffer = io.BytesIO(ai_content_bytes)
            
            pdf_document.close()
            
            return send_file(
                ai_buffer,
                as_attachment=True,
                download_name=ai_filename,
                mimetype='application/octet-stream'
            )
        else:
            # 다중 페이지 처리 - ZIP 파일로 묶어서 반환
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for page_num_1based in pages_to_process:
                    page_num = page_num_1based - 1  # 0-based index
                    page = pdf_document[page_num]
                    
                    # 페이지를 이미지로 렌더링 (고해상도)
                    matrix = fitz.Matrix(2.0, 2.0)  # 2배 확대
                    pix = page.get_pixmap(matrix=matrix)
                    
                    # PIL Image로 변환
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # AI 변환
                    ai_content_bytes = convert_to_ai(img)
                    
                    # ZIP 파일에 AI 파일 추가
                    ai_filename = f"{original_name}_page_{page_num_1based}.ai"
                    zip_file.writestr(ai_filename, ai_content_bytes)
            
            zip_buffer.seek(0)
            pdf_document.close()
            
            # ZIP 파일 반환
            zip_filename = f"{original_name}_ai.zip"
            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
        
    except FileNotFoundError as e:
        return jsonify({'error': f'파일을 찾을 수 없습니다: {str(e)}'}), 404
    except ValueError as e:
        return jsonify({'error': f'잘못된 파라미터 값입니다: {str(e)}'}), 400
    except MemoryError as e:
        return jsonify({'error': '파일이 너무 커서 처리할 수 없습니다. 더 작은 파일을 사용해주세요.'}), 413
    except Exception as e:
        app.logger.error(f'PDF to AI 변환 오류: {str(e)}')
        return jsonify({'error': f'AI 변환 중 오류가 발생했습니다: {str(e)}'}), 500

# 기존 SVG 엔드포인트 호환성을 위한 리다이렉트
@app.route('/convert', methods=['POST'])
def convert_legacy():
    # 기존 /convert 엔드포인트를 새로운 AI 변환으로 리다이렉트
    return convert_file()

@app.route("/health")
def health():
    return "ok", 200

if __name__ == '__main__':
    app.run(debug=True)