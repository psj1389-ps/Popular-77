# Image to GIF Converter Service - Updated for Render deployment
from flask import Flask, request, send_file, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, io, zipfile, uuid, time
import sys

from converters.image_to_gif import image_to_gif, images_to_gif, extract_gif_frames, get_image_info, _get_supported_formats
from utils.file_utils import ensure_dirs
from converters.batch_processor import BatchProcessor, JobStatus, get_batch_processor

BASE = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # UTF-8 지원

# UTF-8 인코딩 설정
if sys.platform.startswith('win'):
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Korean_Korea.65001')
        except locale.Error:
            pass

# Jinja2 환경 설정 - UTF-8 인코딩 강제
from jinja2 import FileSystemLoader, TemplateNotFound
import codecs

class UTF8FileSystemLoader(FileSystemLoader):
    def get_source(self, environment, template):
        # 부모 클래스의 메서드를 사용하여 경로 찾기
        for searchpath in self.searchpath:
            path = os.path.join(searchpath, template)
            if os.path.isfile(path):
                break
        else:
            raise TemplateNotFound(template)
        
        # UTF-8로 강제 읽기
        try:
            with codecs.open(path, 'r', encoding='utf-8') as f:
                source = f.read()
        except UnicodeDecodeError:
            # UTF-8 실패시 다른 인코딩 시도
            try:
                with codecs.open(path, 'r', encoding='cp949') as f:
                    source = f.read()
            except UnicodeDecodeError:
                with codecs.open(path, 'r', encoding='latin-1') as f:
                    source = f.read()
        
        mtime = os.path.getmtime(path)
        return source, path, lambda: mtime == os.path.getmtime(path)

# 커스텀 로더 적용
app.jinja_loader = UTF8FileSystemLoader(app.template_folder)
app.jinja_env.globals.update(zip=zip)

CORS(app)  # CORS 설정 추가
ensure_dirs([UPLOAD_DIR, OUTPUT_DIR])

# 배치 처리기 초기화
batch_processor = get_batch_processor()

@app.route("/", methods=["GET"])
def root():
    try:
        return render_template("index.html", 
                             supported_formats=_get_supported_formats(),
                             service_name="GIF 변환기",
                             service_description="이미지를 GIF로 변환하거나 여러 이미지로 애니메이션 GIF를 생성합니다.")
    except Exception as e:
        return jsonify({
            "error": f"템플릿 렌더링 오류: {str(e)}",
            "supported_formats": _get_supported_formats(),
            "service_info": {
                "name": "GIF 변환기",
                "description": "이미지를 GIF로 변환하거나 여러 이미지로 애니메이션 GIF를 생성합니다.",
                "endpoints": {
                    "/convert": "단일 이미지를 GIF로 변환",
                    "/api/images-gif": "이미지를 GIF로 변환 (API)",
                    "/api/batch-convert": "배치 변환",
                    "/api/create-animation": "애니메이션 GIF 생성",
                    "/api/extract-frames": "GIF 프레임 추출"
                }
            }
        })

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return jsonify({"status": "healthy", "service": "images-gif"})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'assets'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/@vite/client')
def vite_client():
    # Vite 개발 서버용 더미 응답
    return "", 404

def _zip_paths(paths):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for path in paths:
            if os.path.exists(path):
                zip_file.write(path, os.path.basename(path))
    zip_buffer.seek(0)
    return zip_buffer

def _flag(v, default=False):
    if v is None:
        return default
    return str(v).lower() in ('true', '1', 'yes', 'on')

@app.route("/convert", methods=["POST"])
def api_image_to_gif():
    """단일 이미지를 GIF로 변환"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 옵션 파라미터
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize_factor', 1.0))
        
        # 파일 저장
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
        file.save(input_path)
        
        try:
            # 출력 파일 경로
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.gif"
            output_path = os.path.join(OUTPUT_DIR, f"{file_id}_{output_filename}")
            
            # GIF 변환
            success, message = image_to_gif(
                input_path, 
                output_path,
                quality=quality,
                resize_factor=resize_factor
            )
            
            if success:
                # 파일 정보 가져오기
                file_info = get_image_info(output_path)
                
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=output_filename,
                    mimetype='image/gif'
                )
            else:
                return jsonify({"error": message}), 400
                
        finally:
            # 임시 파일 정리
            if os.path.exists(input_path):
                os.remove(input_path)
                
    except Exception as e:
        return jsonify({"error": f"변환 중 오류 발생: {str(e)}"}), 500

@app.route("/api/images-gif", methods=["POST"])
def api_images_gif():
    """이미지를 GIF로 변환 (API 엔드포인트)"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 옵션 파라미터
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize_factor', 1.0))
        
        # 파일 저장
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
        file.save(input_path)
        
        try:
            # 출력 파일 경로
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.gif"
            output_path = os.path.join(OUTPUT_DIR, f"{file_id}_{output_filename}")
            
            # GIF 변환
            success, message = image_to_gif(
                input_path, 
                output_path,
                quality=quality,
                resize_factor=resize_factor
            )
            
            if success:
                # 파일 정보 가져오기
                file_info = get_image_info(output_path)
                file_size = os.path.getsize(output_path)
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "file_info": file_info,
                    "file_size": file_size,
                    "download_url": f"/download/{file_id}_{output_filename}"
                })
            else:
                return jsonify({"success": False, "error": message}), 400
                
        finally:
            # 입력 파일 정리
            if os.path.exists(input_path):
                os.remove(input_path)
                
    except Exception as e:
        return jsonify({"success": False, "error": f"변환 중 오류 발생: {str(e)}"}), 500

@app.route("/api/create-animation", methods=["POST"])
def api_create_animation():
    """여러 이미지로 애니메이션 GIF 생성"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 옵션 파라미터
        duration = float(request.form.get('duration', 0.5))
        loop = int(request.form.get('loop', 0))
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize_factor', 1.0))
        
        file_id = str(uuid.uuid4())
        input_paths = []
        
        try:
            # 파일들 저장
            for i, file in enumerate(files):
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{i:03d}_{filename}")
                    file.save(input_path)
                    input_paths.append(input_path)
            
            if not input_paths:
                return jsonify({"error": "유효한 파일이 없습니다."}), 400
            
            # 출력 파일 경로
            output_filename = f"animation_{file_id}.gif"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            # 애니메이션 GIF 생성
            success, message = images_to_gif(
                input_paths,
                output_path,
                duration=duration,
                loop=loop,
                quality=quality,
                resize_factor=resize_factor
            )
            
            if success:
                file_info = get_image_info(output_path)
                file_size = os.path.getsize(output_path)
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "file_info": file_info,
                    "file_size": file_size,
                    "download_url": f"/download/{output_filename}"
                })
            else:
                return jsonify({"success": False, "error": message}), 400
                
        finally:
            # 임시 파일들 정리
            for path in input_paths:
                if os.path.exists(path):
                    os.remove(path)
                    
    except Exception as e:
        return jsonify({"success": False, "error": f"애니메이션 생성 중 오류 발생: {str(e)}"}), 500

@app.route("/api/extract-frames", methods=["POST"])
def api_extract_frames():
    """GIF에서 프레임 추출"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 옵션 파라미터
        output_format = request.form.get('format', 'PNG').upper()
        
        # 파일 저장
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
        file.save(input_path)
        
        try:
            # 출력 디렉토리
            output_dir = os.path.join(OUTPUT_DIR, f"frames_{file_id}")
            
            # 프레임 추출
            success, message, extracted_files = extract_gif_frames(
                input_path,
                output_dir,
                format=output_format
            )
            
            if success:
                # ZIP 파일 생성
                zip_filename = f"frames_{file_id}.zip"
                zip_path = os.path.join(OUTPUT_DIR, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for frame_path in extracted_files:
                        if os.path.exists(frame_path):
                            zipf.write(frame_path, os.path.basename(frame_path))
                
                return jsonify({
                    "success": True,
                    "message": message,
                    "frame_count": len(extracted_files),
                    "download_url": f"/download/{zip_filename}"
                })
            else:
                return jsonify({"success": False, "error": message}), 400
                
        finally:
            # 입력 파일 정리
            if os.path.exists(input_path):
                os.remove(input_path)
                
    except Exception as e:
        return jsonify({"success": False, "error": f"프레임 추출 중 오류 발생: {str(e)}"}), 500

@app.route("/api/batch-convert", methods=["POST"])
def api_batch_convert():
    """배치 GIF 변환"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
        
        # 옵션 파라미터
        quality = request.form.get('quality', 'medium')
        resize_factor = float(request.form.get('resize_factor', 1.0))
        
        # 파일들 저장
        file_paths = []
        original_names = []
        batch_id = str(uuid.uuid4())
        
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_DIR, f"{batch_id}_{filename}")
                file.save(file_path)
                file_paths.append(file_path)
                original_names.append(filename)
        
        if not file_paths:
            return jsonify({"error": "유효한 파일이 없습니다."}), 400
        
        try:
            # 배치 작업 생성
            job_id = batch_processor.create_batch_job(
                file_paths=file_paths,
                original_names=original_names,
                output_dir=OUTPUT_DIR,
                quality=quality,
                resize_factor=resize_factor
            )
            
            return jsonify({
                "success": True,
                "job_id": job_id,
                "message": f"{len(file_paths)}개 파일의 배치 변환이 시작되었습니다.",
                "total_files": len(file_paths)
            })
            
        except Exception as e:
            # 오류 발생시 업로드된 파일들 정리
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            raise e
            
    except Exception as e:
        return jsonify({"success": False, "error": f"배치 변환 시작 중 오류 발생: {str(e)}"}), 500

@app.route("/api/progress/<job_id>", methods=["GET"])
def api_progress(job_id):
    """배치 작업 진행 상황 조회"""
    try:
        job_status = batch_processor.get_job_status(job_id)
        
        if job_status is None:
            return jsonify({"error": "작업을 찾을 수 없습니다."}), 404
        
        return jsonify({
            "success": True,
            "job_status": job_status
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"상태 조회 중 오류 발생: {str(e)}"}), 500

@app.route("/api/download/<job_id>", methods=["GET"])
def api_download(job_id):
    """배치 작업 결과 다운로드"""
    try:
        zip_path = batch_processor.get_job_zip_path(job_id)
        
        if zip_path is None:
            return jsonify({"error": "다운로드할 파일이 없습니다."}), 404
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"gif_conversion_results_{job_id}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({"error": f"다운로드 중 오류 발생: {str(e)}"}), 500

@app.route("/api/cancel/<job_id>", methods=["POST"])
def api_cancel(job_id):
    """배치 작업 취소"""
    try:
        success = batch_processor.cancel_job(job_id)
        
        if success:
            return jsonify({"success": True, "message": "작업이 취소되었습니다."})
        else:
            return jsonify({"success": False, "error": "작업을 취소할 수 없습니다."}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": f"작업 취소 중 오류 발생: {str(e)}"}), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """파일 다운로드"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
    except Exception as e:
        return jsonify({"error": f"다운로드 중 오류 발생: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "페이지를 찾을 수 없습니다.",
        "service": "images-gif",
        "available_endpoints": [
            "/",
            "/convert",
            "/api/images-gif",
            "/api/create-animation",
            "/api/extract-frames",
            "/api/batch-convert",
            "/health"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "서버 내부 오류가 발생했습니다.",
        "service": "images-gif"
    }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV', '').lower() != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)