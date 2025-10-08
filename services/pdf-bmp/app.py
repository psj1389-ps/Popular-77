from flask import Flask, render_template, request, send_file, jsonify
import os
import zipfile
from pdf2image import convert_from_bytes
from PIL import Image
import io
import tempfile

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/@vite/client')
def vite_client():
    # Vite 클라이언트 요청을 무시하고 빈 응답 반환
    return '', 204

@app.route('/convert', methods=['POST'])
def convert():
    try:
        file = request.files['file']
        quality = request.form.get('quality', 'medium')
        scale = float(request.form.get('scale', '1'))
        
        if not file or file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400
        
        # PDF를 이미지로 변환
        pdf_bytes = file.read()
        
        # 품질 설정
        dpi_map = {'low': 150, 'medium': 200, 'high': 300}
        dpi = dpi_map.get(quality, 200)
        
        # 크기 조절 적용
        dpi = int(dpi * scale)
        
        # PDF를 이미지로 변환
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
        
        # 단일 페이지인 경우 JPG로, 다중 페이지인 경우 ZIP으로
        if len(images) == 1:
            # 단일 이미지 처리
            img = images[0]
            
            # 크기 조정
            if scale != 1.0:
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 임시 파일로 저장
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bmp', dir='outputs')
            img.save(temp_file.name, 'BMP')
            temp_file.close()
            
            return send_file(temp_file.name, 
                           as_attachment=True, 
                           download_name=f"{os.path.splitext(file.filename)[0]}.bmp",
                           mimetype='image/bmp')
        else:
            # 다중 이미지를 ZIP으로 압축
            zip_filename = f"outputs/{os.path.splitext(file.filename)[0]}_bmp.zip"
            
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for i, img in enumerate(images):
                    # 크기 조정
                    if scale != 1.0:
                        new_width = int(img.width * scale)
                        new_height = int(img.height * scale)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 메모리에서 이미지 처리
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, 'BMP')
                    img_bytes.seek(0)
                    
                    # ZIP에 추가
                    zipf.writestr(f"page_{i+1:03d}.bmp", img_bytes.getvalue())
            
            return send_file(zip_filename, 
                           as_attachment=True, 
                           download_name=f"{os.path.splitext(file.filename)[0]}_bmp.zip",
                           mimetype='application/zip')
    
    except Exception as e:
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route("/health")
def health():
    return "ok", 200

if __name__ == '__main__':
    app.run(debug=True)