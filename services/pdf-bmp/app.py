from flask import Flask, request, send_file, jsonify
import os
import fitz  # PyMuPDF
import zipfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- 기본 경로 및 헬스 체크 ---
@app.route("/")
def index():
    return "PDF to BMP Converter is running!"

@app.route("/health")
def health():
    return "ok", 200
# --------------------------

# --- 실제 변환 기능 ---
@app.route("/convert", methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다'}), 400

    # --- 임시 파일 저장을 위한 폴더 설정 ---
    # Render에서는 /tmp 폴더를 사용하는 것이 안전합니다.
    upload_folder = '/tmp/uploads'
    output_folder = '/tmp/outputs'
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    # ------------------------------------

    filename = secure_filename(file.filename)
    input_path = os.path.join(upload_folder, filename)
    file.save(input_path)

    image_paths = []
    try:
        doc = fitz.open(input_path)
        base_filename = os.path.splitext(filename)[0]

        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            # 파일 이름을 BMP로 지정
            output_image_filename = f"{base_filename}_page_{i+1}.bmp"
            image_path = os.path.join(output_folder, output_image_filename)
            pix.save(image_path)
            image_paths.append(image_path)
        page_count = len(doc)
        doc.close()

        if page_count == 1:
            return send_file(image_paths[0], as_attachment=True, download_name=os.path.basename(image_paths[0]))
        
        elif page_count > 1:
            zip_filename = f"{base_filename}_images.zip"
            zip_path = os.path.join(output_folder, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in image_paths:
                    zipf.write(file_path, os.path.basename(file_path))
            
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)

        else:
            return jsonify({'error': 'PDF에 페이지가 없습니다'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # --- 임시 파일 정리 ---
        try:
            if os.path.exists(input_path): os.remove(input_path)
            for path in image_paths:
                if os.path.exists(path): os.remove(path)
            if 'zip_path' in locals() and os.path.exists(zip_path): os.remove(zip_path)
        except Exception as e:
            print(f"임시 파일 정리 중 오류: {e}")
# ---------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)