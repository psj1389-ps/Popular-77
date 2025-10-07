import os
import io
import zipfile
from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
import fitz  # PyMuPDF
import base64

app = Flask(__name__)

def convert_to_svg(img, color_count, detail_level, noise_suppression):
    """
    PIL Image를 SVG로 변환하는 함수
    """
    try:
        # 이미지 크기 조정 (detail_level에 따라)
        width, height = img.size
        scale_factor = detail_level / 10.0  # 1-10을 0.1-1.0으로 변환
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        if new_width > 0 and new_height > 0:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 색상 수 줄이기 (color_count 파라미터 활용)
        if img.mode == 'RGBA':
            # RGBA 이미지의 경우 RGB로 변환
            img = img.convert('RGB')
        
        img_quantized = img.quantize(colors=color_count).convert('RGB')
        
        # 노이즈 억제 (간단한 블러 효과로 구현)
        if noise_suppression > 0:
            from PIL import ImageFilter
            blur_radius = noise_suppression / 100.0 * 2.0  # 0-2.0 범위
            img_quantized = img_quantized.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # 이미지를 base64로 인코딩
        buffer = io.BytesIO()
        img_quantized.save(buffer, format='JPEG', quality=85)
        img_format = 'jpeg'
        
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # SVG 생성
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
     width="{img_quantized.width}" height="{img_quantized.height}" viewBox="0 0 {img_quantized.width} {img_quantized.height}">
  <image x="0" y="0" width="{img_quantized.width}" height="{img_quantized.height}" 
         xlink:href="data:image/{img_format};base64,{img_base64}"/>
</svg>'''
        
        return svg_content
        
    except Exception as e:
        raise Exception(f"SVG 변환 중 오류 발생: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
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
        
        # SVG 변환 옵션 가져오기
        color_count = int(request.form.get('colorCount', 64))
        detail_level = int(request.form.get('detailLevel', 5))
        noise_suppression = int(request.form.get('noiseSuppression', 30))
        
        # 페이지 수 확인
        page_count = len(pdf_document)
        original_name = os.path.splitext(file.filename)[0]
        
        if page_count == 1:
            # 단일 페이지 처리 (기존 로직)
            page = pdf_document[0]
            
            # 페이지를 이미지로 렌더링 (고해상도)
            matrix = fitz.Matrix(2.0, 2.0)  # 2배 확대
            pix = page.get_pixmap(matrix=matrix)
            
            # PIL Image로 변환
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # SVG 변환
            svg_content = convert_to_svg(img, color_count, detail_level, noise_suppression)
            
            # 단일 SVG 파일 반환
            svg_filename = f"{original_name}.svg"
            svg_buffer = io.BytesIO()
            svg_buffer.write(svg_content.encode('utf-8'))
            svg_buffer.seek(0)
            
            pdf_document.close()
            
            return send_file(
                svg_buffer,
                as_attachment=True,
                download_name=svg_filename,
                mimetype='image/svg+xml'
            )
        else:
            # 다중 페이지 처리 - ZIP 파일로 묶어서 반환
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for page_num in range(page_count):
                    page = pdf_document[page_num]
                    
                    # 페이지를 이미지로 렌더링 (고해상도)
                    matrix = fitz.Matrix(2.0, 2.0)  # 2배 확대
                    pix = page.get_pixmap(matrix=matrix)
                    
                    # PIL Image로 변환
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # SVG 변환
                    svg_content = convert_to_svg(img, color_count, detail_level, noise_suppression)
                    
                    # ZIP 파일에 SVG 추가
                    svg_filename = f"{original_name}_page_{page_num + 1}.svg"
                    zip_file.writestr(svg_filename, svg_content.encode('utf-8'))
            
            zip_buffer.seek(0)
            pdf_document.close()
            
            # ZIP 파일 반환
            zip_filename = f"{original_name}_svg_pages.zip"
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
        app.logger.error(f'PDF to SVG 변환 오류: {str(e)}')
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/convert_to_svg', methods=['POST'])
def convert_to_svg_endpoint():
    # /convert_to_svg 엔드포인트를 /convert와 동일하게 처리
    return convert_file()



if __name__ == '__main__':
    app.run(debug=True)