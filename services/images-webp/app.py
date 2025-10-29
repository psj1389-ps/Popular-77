# Image to WEBP Converter Service - Updated for Render deployment
from flask import Flask, request, send_file, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, io, zipfile, uuid, time

from converters.image_to_webp import image_to_webp, get_image_info, _get_supported_formats
from utils.file_utils import ensure_dirs
from converters.batch_processor import BatchProcessor, JobStatus, get_batch_processor

BASE = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")

app = Flask(__name__)
CORS(app)  # CORS 설정 추가
ensure_dirs([UPLOAD_DIR, OUTPUT_DIR])

# 배치 프로세서 초기화
batch_processor = get_batch_processor()

@app.route("/", methods=["GET"])
def root():
    # Check if request accepts HTML (browser request)
    if request.headers.get('Accept', '').find('text/html') != -1:
        return render_template('index.html')
    
    # Return JSON for API requests - Service status endpoint
    return jsonify({
        "service": "Image to WEBP Converter",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "convert": "/api/image-to-webp",
            "web_convert": "/convert",
            "batch_convert": "/api/batch-convert",
            "progress": "/api/progress",
            "download": "/api/download"
        },
        "usage": {
            "method": "POST",
            "endpoint": "/api/image-to-webp",
            "parameters": {
                "file": "Image file (required) - JPG, PNG, BMP, TIFF, GIF, SVG, PSD, HEIC, RAW",
                "quality": "WEBP Quality (75-100 or low/medium/high, default: medium)",
                "resize": "Resize factor (0.1-3.0, default: 1.0)"
            },
            "supported_formats": {
                "input": _get_supported_formats(),
                "output": "WEBP"
            }
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "Image to WEBP Converter"})

@app.route("/convert", methods=["POST"])
@app.route("/api/image-to-webp", methods=["POST"])
def convert_image():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 파일 저장
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "유효하지 않은 파일명입니다."}), 400
        
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(UPLOAD_DIR, unique_filename)
        file.save(input_path)
        
        # 변환 옵션 처리
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize', 1.0))
        transparent = request.form.get('transparent', 'false').lower() == 'true'
        
        # 변환 실행
        output_files = image_to_webp(
            input_path, 
            OUTPUT_DIR, 
            quality=quality, 
            resize_factor=resize_factor,
            preserve_transparency=transparent
        )
        
        if not output_files:
            return jsonify({"error": "변환에 실패했습니다."}), 500
        
        output_file = output_files[0]
        
        # 파일 전송
        response = send_file(
            output_file,
            as_attachment=True,
            download_name=os.path.basename(output_file),
            mimetype='image/webp'
        )
        
        # 임시 파일 정리 (응답 후)
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_file):
                    os.remove(output_file)
            except:
                pass
        
        return response
        
    except Exception as e:
        return jsonify({"error": f"변환 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)