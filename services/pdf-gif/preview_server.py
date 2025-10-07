from flask import Flask, render_template, send_from_directory, request, jsonify, send_file, Response
import os
from pdf2image import convert_from_bytes
from PIL import Image
import io
import zipfile
from werkzeug.utils import secure_filename
from urllib.parse import quote

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
        
        # 고급 옵션 파라미터 추가
        scale_factor = float(request.form.get('scale_factor', 1.0))
        
        # 투명 배경 처리 - 라디오버튼 값 확인
        transparent_bg = request.form.get('transparent_bg') == 'on'
        
        print(f"DEBUG: 투명 배경: {transparent_bg}")
        print(f"DEBUG: 크기 배율: {scale_factor}")
        
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
        base_dpi = dpi_settings.get(quality, 200)
        # 크기 조절 배율 적용
        dpi = int(base_dpi * scale_factor)
        
        # PDF를 이미지로 변환
        pdf_bytes = file.read()
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='PNG')
        
        # 투명 배경 처리를 위한 함수
        def process_image(img):
            if transparent_bg:
                # 투명 배경으로 변환
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 흰색 배경을 투명하게 만들기 (개선된 알고리즘)
                data = img.getdata()
                new_data = []
                for item in data:
                    # 흰색에 가까운 픽셀을 투명하게 변환 (임계값 245로 조정)
                    # RGB 값이 모두 245 이상인 경우 투명하게 처리
                    if len(item) >= 3 and item[0] >= 245 and item[1] >= 245 and item[2] >= 245:
                        new_data.append((255, 255, 255, 0))  # 완전 투명
                    else:
                        # 기존 픽셀 유지 (알파 채널이 있으면 그대로, 없으면 불투명으로)
                        if len(item) == 4:
                            new_data.append(item)
                        else:
                            new_data.append(item + (255,))  # 알파 채널 추가 (불투명)
                img.putdata(new_data)
            else:
                # 투명배경을 사용하지 않는 경우 RGB로 변환
                if img.mode == 'RGBA':
                    # 흰색 배경으로 합성
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])  # 알파 채널을 마스크로 사용
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            return img
        
        # 디버깅: 이미지 개수 로그 출력
        print(f"DEBUG: 변환된 이미지 개수: {len(images)}")
        print(f"DEBUG: 파일명: {file.filename}")
        
        # 단일 이미지인 경우
        if len(images) == 1:
            print("DEBUG: 단일 페이지 처리 - PNG 다운로드")
            # 단일 페이지 처리
            # 원본 파일명을 직접 사용하도록 수정
            base_name = os.path.splitext(file.filename)[0]
            download_name = f"{base_name}.png"
            
            # 이미지 처리 (투명 배경 등)
            processed_image = process_image(images[0])
            
            # 이미지 데이터를 메모리 버퍼에 저장
            image_buffer = io.BytesIO()
            processed_image.save(image_buffer, format='PNG')
            

            
            image_buffer.seek(0)
            
            # 웹 표준(RFC 6266)에 따라 파일명을 URL 인코딩하여 헤더에 명시
            # 이 방식은 모든 최신 브라우저에서 한글 깨짐 없이 파일명을 처리합니다.
            return Response(
                image_buffer,
                mimetype='image/png',
                headers={
                    'Content-Disposition': f"attachment; filename*=UTF-8''{quote(download_name)}"
                }
            )
        
        # 다중 페이지인 경우 ZIP으로 압축
        else:
            print("DEBUG: 다중 페이지 처리 - ZIP 다운로드")
            zip_io = io.BytesIO()
            with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, image in enumerate(images):
                    # 이미지 처리 (투명 배경 등)
                    processed_image = process_image(image)
                    
                    img_io = io.BytesIO()
                    processed_image.save(img_io, 'PNG')
                    

                    
                    img_io.seek(0)
                    
                    # 원본 파일명을 직접 사용하도록 수정
                    base_name = os.path.splitext(file.filename)[0]
                    img_filename = f"{base_name}_page_{i+1}.png"
                    
                    zip_file.writestr(img_filename, img_io.getvalue())
            
            zip_io.seek(0)
            
            # 원본 파일명을 직접 사용하도록 수정
            base_name = os.path.splitext(file.filename)[0]
            zip_filename = f'{base_name}_png.zip'
            
            # 웹 표준(RFC 6266)에 따라 파일명을 URL 인코딩하여 헤더에 명시
            return Response(
                zip_io,
                mimetype='application/zip',
                headers={
                    'Content-Disposition': f"attachment; filename*=UTF-8''{quote(zip_filename)}"
                }
            )
            
    except Exception as e:
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)