from flask import Flask, request, send_file, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os, io, zipfile, uuid, time

from converters.image_to_jpg import image_to_jpg, get_image_info, _get_supported_formats
from utils.file_utils import ensure_dirs
from converters.batch_processor import BatchProcessor, JobStatus, get_batch_processor

BASE = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")

app = Flask(__name__)
ensure_dirs([UPLOAD_DIR, OUTPUT_DIR])

# 배치 프로세서 초기화
batch_processor = get_batch_processor()

@app.route("/", methods=["GET"])
def root():
    # Check if request accepts HTML (browser request)
    if request.headers.get('Accept', '').find('text/html') != -1:
        return render_template('index.html')
    
    # Return JSON for API requests
    return jsonify({
        "service": "Image to JPG Converter",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "convert": "/api/image-to-jpg",
            "web_convert": "/convert",
            "batch_convert": "/api/batch-convert",
            "progress": "/api/progress",
            "download": "/api/download"
        },
        "usage": {
            "method": "POST",
            "endpoint": "/api/image-to-jpg",
            "parameters": {
                "file": "Image file (required) - PNG, WEBP, BMP, TIFF, GIF",
                "quality": "JPG Quality (75-100 or low/medium/high, default: medium)",
                "resize": "Resize factor (0.1-3.0, default: 1.0)"
            },
            "supported_formats": {
                "input": _get_supported_formats(),
                "output": "JPG"
            }
        }
    })

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return jsonify({"ok": True})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/@vite/client')
def vite_client():
    # Vite 개발 서버 관련 요청 무시
    return '', 404

def _zip_paths(paths):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, arcname=os.path.basename(p))
    buf.seek(0)
    return buf

def _flag(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in ("1","true","yes","y","on")

@app.route("/api/image-to-jpg", methods=["POST"])
def api_image_to_jpg():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "file is required"}), 400

    # 파일 확장자 확인
    from converters.image_to_jpg import _is_supported_image
    if not _is_supported_image(f):
        supported_formats = _get_supported_formats()
        return jsonify({"error": f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(supported_formats)}"}), 400

    quality = request.form.get("quality") or "medium"      # 75~100 또는 low/medium/high
    
    # resize 파라미터 안전하게 처리
    try:
        resize_factor = float(request.form.get("resize") or 1.0)  # 크기 조절 비율
    except (ValueError, TypeError):
        resize_factor = 1.0

    # 크기 조절 비율 검증
    if not (0.1 <= resize_factor <= 3.0):
        return jsonify({"error": "크기 조절 비율은 0.1에서 3.0 사이여야 합니다."}), 400
    
    # 브라우저에서 전송하는 추가 파라미터들 처리 (무시)
    format_param = request.form.get("format")  # 브라우저에서 전송하지만 JPG 고정이므로 무시
    transparent_bg = request.form.get("transparentBg")  # JPG는 투명도 지원 안하므로 무시

    # 파일명/확장자 안전 처리 및 고유 파일명 생성
    original_name = secure_filename(f.filename or "")
    base, ext = os.path.splitext(original_name)

    if not ext:
        import mimetypes
        guessed_ext = mimetypes.guess_extension(getattr(f, 'mimetype', '') or '')
        if guessed_ext in (".jpeg", ".jpe"):
            guessed_ext = ".jpg"
        ext = guessed_ext or ""

    # 확장자가 여전히 없거나 지원되지 않으면 내용 기반 감지 시도
    supported_exts = set(["." + s for s in _get_supported_formats()])
    if not ext or ext.lower() not in supported_exts:
        try:
            from PIL import Image
            f.stream.seek(0)
            with Image.open(f.stream) as img:
                fmt = (img.format or "").lower()
                fmt_map = {
                    "png": ".png", "webp": ".webp", "bmp": ".bmp",
                    "tiff": ".tiff", "gif": ".gif", "jpeg": ".jpg",
                    "svg": ".svg", "psd": ".psd", "heif": ".heif", "heic": ".heic"
                }
                ext = fmt_map.get(fmt, ext)
        except Exception:
            pass
        finally:
            try:
                f.stream.seek(0)
            except Exception:
                pass

    if not ext:
        return jsonify({"error": "업로드한 파일의 확장자를 확인할 수 없습니다."}), 400

    unique_name = (base or "upload") + "_" + uuid.uuid4().hex[:8] + ext
    in_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        f.save(in_path)
    except IsADirectoryError:
        return jsonify({"error": f"업로드 경로가 디렉토리로 잘못 지정되었습니다: {in_path}"}), 500

    # 파일 저장 성공 여부 확인 (파일이어야 함)
    if not os.path.isfile(in_path):
        return jsonify({"error": f"파일 저장에 실패했습니다(파일이 아님): {in_path}"}), 500

    out_dir = os.path.join(OUTPUT_DIR, os.path.splitext(unique_name)[0])
    os.makedirs(out_dir, exist_ok=True)

    try:
        out_files = image_to_jpg(
            in_path, out_dir,
            quality=quality,
            resize_factor=resize_factor
        )

        if not out_files:
            return jsonify({"error": "변환된 파일이 생성되지 않았습니다."}), 500

        # 단일 파일 반환
        fp = out_files[0]
        base_name = os.path.splitext(original_name or f.filename)[0] or os.path.splitext(unique_name)[0]
        korean_filename = f"{base_name}.jpg"
        resp = send_file(fp, as_attachment=True, download_name=korean_filename, mimetype="image/jpeg")
        resp.headers["Content-Length"] = str(os.path.getsize(fp))
        
        # UTF-8 및 일반 filename 모두 설정
        import urllib.parse
        encoded_filename = urllib.parse.quote(korean_filename)
        resp.headers["Content-Disposition"] = f"attachment; filename=\"{korean_filename}\"; filename*=UTF-8''{encoded_filename}"
        resp.headers["Content-Type"] = "image/jpeg"
        return resp

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"이미지 변환 중 오류가 발생했습니다: {str(e)}"}), 500

# 웹 인터페이스용 /convert 라우트
@app.route("/convert", methods=["POST"])
def convert():
    # 디버깅을 위한 요청 정보 로깅
    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Request content type: {request.content_type}")
    print(f"[DEBUG] Request files: {list(request.files.keys())}")
    print(f"[DEBUG] Request form: {dict(request.form)}")
    print(f"[DEBUG] Request headers: {dict(request.headers)}")
    
    try:
        return api_image_to_jpg()
    except Exception as e:
        print(f"[ERROR] Exception in convert(): {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"변환 중 오류가 발생했습니다: {str(e)}"}), 500

# 배치 변환 API 엔드포인트
@app.route("/api/batch-convert", methods=["POST"])
def api_batch_convert():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "파일이 필요합니다"}), 400
    if len(files) > 100:
        return jsonify({"error": "최대 100개 파일까지 업로드 가능합니다"}), 400

    # 총 파일 크기 제한 (500MB)
    total_size = 0
    for f in files:
        f.seek(0, 2)
        total_size += f.tell()
        f.seek(0)

    if total_size > 500 * 1024 * 1024:
        return jsonify({"error": "총 파일 크기가 500MB를 초과합니다"}), 400

    # 지원되는 파일 형식 확인
    from converters.image_to_jpg import _is_supported_image
    unsupported_files = [f.filename for f in files if not _is_supported_image(f)]
    if unsupported_files:
        supported_formats = _get_supported_formats()
        return jsonify({
            "error": f"지원되지 않는 파일 형식이 포함되어 있습니다: {', '.join(unsupported_files)}",
            "supported_formats": supported_formats
        }), 400

    # 변환 옵션
    quality = request.form.get("quality", "medium")
    try:
        resize_factor = float(request.form.get("resize", 1.0))
    except (ValueError, TypeError):
        resize_factor = 1.0
    if not (0.1 <= resize_factor <= 3.0):
        return jsonify({"error": "크기 조절 비율은 0.1에서 3.0 사이여야 합니다"}), 400

    # 업로드 파일 저장 및 경로/원본명 수집
    saved_paths = []
    original_names = []
    supported_exts = set("." + s for s in _get_supported_formats())

    for f in files:
        original_name = secure_filename(f.filename or "")
        base, ext = os.path.splitext(original_name)

        if not ext:
            import mimetypes
            guessed_ext = mimetypes.guess_extension(getattr(f, 'mimetype', '') or '')
            if guessed_ext in (".jpeg", ".jpe"):
                guessed_ext = ".jpg"
            ext = guessed_ext or ""

        if not ext or ext.lower() not in supported_exts:
            try:
                from PIL import Image
                f.stream.seek(0)
                with Image.open(f.stream) as img:
                    fmt = (img.format or "").lower()
                    fmt_map = {
                        "png": ".png", "webp": ".webp", "bmp": ".bmp",
                        "tiff": ".tiff", "gif": ".gif", "jpeg": ".jpg",
                        "svg": ".svg", "psd": ".psd", "heif": ".heif", "heic": ".heic"
                    }
                    ext = fmt_map.get(fmt, ext)
            except Exception:
                pass
            finally:
                try:
                    f.stream.seek(0)
                except Exception:
                    pass

        if not ext:
            return jsonify({"error": f"업로드한 파일의 확장자를 확인할 수 없습니다: {original_name}"}), 400

        unique_name = (base or "upload") + "_" + uuid.uuid4().hex[:8] + ext
        in_path = os.path.join(UPLOAD_DIR, unique_name)
        f.save(in_path)
        saved_paths.append(in_path)
        original_names.append(original_name)

    # 배치 작업 생성 (올바른 인자명 사용)
    job_id = batch_processor.create_batch_job(
        file_paths=saved_paths,
        original_names=original_names,
        output_dir=OUTPUT_DIR,
        quality=quality,
        resize_factor=resize_factor
    )

    return jsonify({
        "job_id": job_id,
        "message": "배치 변환 작업이 시작되었습니다",
        "files_count": len(saved_paths)
    })

# 진행률 확인 API 엔드포인트
@app.route("/api/progress/<job_id>", methods=["GET"])
def api_progress(job_id):
    status = batch_processor.get_job_status(job_id)
    if not status:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404

    # status는 dict 형태
    total = int(status.get("total_files", 0) or 0)
    completed = int(status.get("completed_files", 0) or 0)
    failed = int(status.get("failed_files", 0) or 0)
    progress = ((completed + failed) / total * 100.0) if total > 0 else 0.0

    return jsonify({
        "job_id": job_id,
        "status": status.get("status"),
        "progress": progress,
        "total_files": total,
        "completed_files": completed,
        "failed_files": failed,
        "created_at": status.get("created_at"),
        "completed_at": status.get("completed_at"),
    })

# ZIP 다운로드 API 엔드포인트
@app.route("/api/download/<job_id>", methods=["GET"])
def api_download(job_id):
    status = batch_processor.get_job_status(job_id)
    if not status:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404

    if status.get("status") != "completed":
        return jsonify({"error": "작업이 완료되지 않았습니다"}), 400

    zip_path = status.get("zip_path")
    if not zip_path or not os.path.exists(zip_path):
        return jsonify({"error": "다운로드 파일을 찾을 수 없습니다"}), 404

    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"converted_images_{job_id[:8]}.zip"
    )

# 작업 취소 API 엔드포인트
@app.route("/api/cancel/<job_id>", methods=["POST"])
def api_cancel(job_id):
    success = batch_processor.cancel_job(job_id)
    if not success:
        return jsonify({"error": "작업을 찾을 수 없거나 취소할 수 없습니다"}), 404
    
    return jsonify({"message": "작업이 취소되었습니다"})

# 404 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint was not found.",
        "available_endpoints": {
            "service_info": "GET /",
            "health_check": "GET /health",
            "image_conversion": "POST /api/image-to-jpg",
            "web_interface": "POST /convert"
        },
        "documentation": "Visit GET / for detailed API documentation"
    }), 404

# 500 에러 핸들러
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred while processing your request.",
        "support": "Please check your request parameters and try again."
    }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', '').lower() != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)