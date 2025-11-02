# Image Format Converter Service - Multi-format support
from flask import Flask, request, send_file, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, io, zipfile, uuid, time, tempfile, logging

from converters.multi_format_converter import MultiFormatConverter, get_supported_formats
from utils.file_utils import ensure_dirs
from converters.batch_processor import BatchProcessor, JobStatus, get_batch_processor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")

app = Flask(__name__)
CORS(app)  # CORS 설정 추가
ensure_dirs([UPLOAD_DIR, OUTPUT_DIR])

# 설정
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = get_supported_formats()['input']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext.lower() for ext in ALLOWED_EXTENSIONS]

# 배치 프로세서 초기화
batch_processor = get_batch_processor()

@app.route("/", methods=["GET"])
def root():
    # Check if request accepts HTML (browser request)
    if request.headers.get('Accept', '').find('text/html') != -1:
        return render_template('index.html')
    
    # Return JSON for API requests - Service status endpoint
    return jsonify({
        "service": "Image Format Converter",
        "version": "2.0.0",
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
            "endpoint": "/convert",
            "parameters": {
                "file": "Image file (required)",
                "format": "Output format (jpg, png, webp, bmp, tiff, default: webp)",
                "quality": "Quality (75-100 or low/medium/high, default: medium)",
                "resize": "Resize factor (0.1-3.0, default: 1.0)",
                "transparent": "Preserve transparency (true/false, default: false)"
            },
            "supported_formats": get_supported_formats()
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "Image Format Converter"})

@app.route("/convert", methods=["POST"])
@app.route("/api/image-to-webp", methods=["POST"])
def convert_image():
    try:
        # 파일 확인
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'지원되지 않는 파일 형식입니다. 지원 형식: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # 파일 크기 확인
        file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.tell()
        file.seek(0)  # 파일 시작으로 되돌리기
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 지원됩니다.'}), 400
        
        # 매개변수 추출
        output_format = request.form.get('format', 'webp').lower()
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize', '1.0'))
        transparent = request.form.get('transparent', 'false').lower() == 'true'
        
        # 지원되는 출력 형식 확인
        supported_output = get_supported_formats()['output']
        if output_format not in [fmt.lower() for fmt in supported_output]:
            return jsonify({'error': f'지원되지 않는 출력 형식입니다. 지원 형식: {", ".join(supported_output)}'}), 400
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file.filename.rsplit(".", 1)[1].lower()}') as temp_input:
            file.save(temp_input.name)
            temp_input_path = temp_input.name
        
        try:
            # 변환 수행
            converter = MultiFormatConverter()
            output_path = converter.convert_image(
                input_path=temp_input_path,
                output_dir=OUTPUT_DIR,
                output_format=output_format,
                quality=quality,
                resize_factor=resize_factor,
                preserve_transparency=transparent
            )
            
            # 파일명 생성
            base_name = os.path.splitext(secure_filename(file.filename))[0]
            output_filename = f"{base_name}.{output_format}"
            
            # 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype=f'image/{output_format}' if output_format != 'jpg' else 'image/jpeg'
            )
            
        finally:
            # 임시 파일 정리
            try:
                os.unlink(temp_input_path)
            except:
                pass
            
    except Exception as e:
        logger.error(f"변환 오류: {str(e)}")
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

# 배치 처리 관련 라우트들
@app.route('/api/batch-convert', methods=['POST'])
def batch_convert():
    try:
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 매개변수 추출
        output_format = request.form.get('format', 'webp').lower()
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize', '1.0'))
        transparent = request.form.get('transparent', 'false').lower() == 'true'
        
        # 지원되는 출력 형식 확인
        supported_output = get_supported_formats()['output']
        if output_format not in [fmt.lower() for fmt in supported_output]:
            return jsonify({'error': f'지원되지 않는 출력 형식입니다. 지원 형식: {", ".join(supported_output)}'}), 400
        
        # 배치 작업 시작
        job_id = batch_processor.start_batch_job(
            files=files,
            output_format=output_format,
            quality=quality,
            resize_factor=resize_factor,
            preserve_transparency=transparent
        )
        
        return jsonify({'job_id': job_id, 'message': '배치 변환이 시작되었습니다.'})
        
    except Exception as e:
        logger.error(f"배치 변환 오류: {str(e)}")
        return jsonify({'error': f'배치 변환 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    try:
        status = batch_processor.get_job_status(job_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"진행률 확인 오류: {str(e)}")
        return jsonify({'error': f'진행률 확인 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/download/<job_id>')
def download_batch_result(job_id):
    try:
        zip_path = batch_processor.get_result_zip(job_id)
        if not zip_path or not os.path.exists(zip_path):
            return jsonify({'error': '결과 파일을 찾을 수 없습니다.'}), 404
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'converted_images_{job_id[:8]}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"다운로드 오류: {str(e)}")
        return jsonify({'error': f'다운로드 중 오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)