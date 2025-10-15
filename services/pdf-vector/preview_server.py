from flask import Flask, render_template, send_from_directory, request, jsonify, send_file
import os
from pdf2image import convert_from_bytes
from PIL import Image
import io
import zipfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/convert', methods=['POST'])
def convert_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        quality = request.form.get('quality', 'medium')
        
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400
        
        # 품질 설정
        dpi_settings = {
            'low': 150,
            'medium': 200,
            'high': 300
        }
        dpi = dpi_settings.get(quality, 200)
        
        # PDF를 이미지로 변환
        pdf_bytes = file.read()
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
        
        # 디버깅: 이미지 개수 로그 출력
        print(f"DEBUG: 변환된 이미지 개수: {len(images)}")
        print(f"DEBUG: 파일명: {file.filename}")
        
        # 단일 이미지인 경우
        if len(images) == 1:
            print("DEBUG: 단일 페이지 처리 - JPG 다운로드")
            img_io = io.BytesIO()
            images[0].save(img_io, 'JPEG', quality=85)
            img_io.seek(0)
            
            filename = secure_filename(file.filename)
            output_filename = os.path.splitext(filename)[0] + '.jpg'
            
            return send_file(
                img_io,
                mimetype='image/jpeg',
                as_attachment=True,
                download_name=output_filename
            )
        
        # 다중 페이지인 경우 ZIP으로 압축
        else:
            print("DEBUG: 다중 페이지 처리 - ZIP 다운로드")
            zip_io = io.BytesIO()
            with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, image in enumerate(images):
                    img_io = io.BytesIO()
                    image.save(img_io, 'JPEG', quality=85)
                    img_io.seek(0)
                    
                    filename = secure_filename(file.filename)
                    base_name = os.path.splitext(filename)[0]
                    img_filename = f"{base_name}_page_{i+1}.jpg"
                    
                    zip_file.writestr(img_filename, img_io.getvalue())
            
            zip_io.seek(0)
            
            return send_file(
                zip_io,
                mimetype='application/zip',
                as_attachment=True,
                download_name='converted_images.zip'
            )
            
    except Exception as e:
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)