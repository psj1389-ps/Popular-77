from flask import Flask, request, send_file, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os, io, zipfile

from converters.pdf_to_images import pdf_to_images
from utils.file_utils import ensure_dirs

BASE = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE, "uploads")
OUTPUT_DIR = os.path.join(BASE, "outputs")

app = Flask(__name__)
ensure_dirs([UPLOAD_DIR, OUTPUT_DIR])

@app.route("/", methods=["GET"])
def root():
    # Check if request accepts HTML (browser request)
    if request.headers.get('Accept', '').find('text/html') != -1:
        return render_template('index.html')
    
    # Return JSON for API requests
    return jsonify({
        "service": "PDF-Image Converter",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "convert": "/api/pdf-to-images",
            "web_convert": "/convert",
            "convert_compat": [
                "/api/pdf-image/convert_to_images",
                "/convert_to_images"
            ]
        },
        "usage": {
            "method": "POST",
            "endpoint": "/api/pdf-to-images",
            "parameters": {
                "file": "PDF file (required)",
                "format": "Output format (png|jpg|webp|tiff|bmp|gif, default: png)",
                "dpi": "Resolution (default: 144)",
                "quality": "Quality (75-100 or low/medium/high)",
                "pages": "Page range (e.g., '1-3,5')",
                "transparentBg": "Transparent background (true/false)",
                "transparentColor": "Color to make transparent (hex)",
                "tolerance": "Color tolerance (default: 8)",
                "webpLossless": "WebP lossless mode (true/false)",
                "whiteThreshold": "White threshold (default: 250)"
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

@app.route("/api/pdf-to-images", methods=["POST"])
def api_pdf_to_images():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "file is required"}), 400

    fmt = (request.form.get("format") or "png").lower()    # png|jpg|webp|tiff|bmp|gif
    dpi = int(request.form.get("dpi") or 144)
    quality = request.form.get("quality")                  # 75~100 또는 low/medium/high
    pages_spec = request.form.get("pages")                 # "1-3,5"

    # 투명 배경 처리 - 다양한 파라미터명 지원
    transparent_bg = _flag(request.form.get("transparentBg"), False) or _flag(request.form.get("transparent"), False)
    transparent_color = request.form.get("transparentColor")   # 예: ffffff, #fff
    tolerance = int(request.form.get("tolerance") or 8)
    webp_lossless = _flag(request.form.get("webpLossless"), True)
    white_threshold = int(request.form.get("whiteThreshold") or 250)  # PDF-PNG 방식 밝기 임계값

    name = secure_filename(f.filename)
    in_path = os.path.join(UPLOAD_DIR, name)
    f.save(in_path)

    out_dir = os.path.join(OUTPUT_DIR, os.path.splitext(name)[0])
    os.makedirs(out_dir, exist_ok=True)

    out_files = pdf_to_images(
        in_path, out_dir,
        fmt=fmt, dpi=dpi, quality=quality, pages_spec=pages_spec,
        transparent_bg=transparent_bg, transparent_color=transparent_color,
        tolerance=tolerance, webp_lossless=webp_lossless,
        white_threshold=white_threshold
    )

    if not out_files:
        return jsonify({"error": "no output files generated"}), 500

    # 1개면 단일 파일, 2개 이상이면 ZIP
    if len(out_files) == 1:
        fp = out_files[0]
        # 단일 페이지: 1장.확장자 형식으로 파일명 설정
        korean_filename = f"1장.{fmt}"
        resp = send_file(fp, as_attachment=True, download_name=korean_filename)
        resp.headers["Content-Length"] = str(os.path.getsize(fp))
        # UTF-8 인코딩을 위한 Content-Disposition 헤더 설정 (URL 인코딩)
        import urllib.parse
        encoded_filename = urllib.parse.quote(korean_filename)
        resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
        return resp

    buf = _zip_paths(out_files)
    buf.seek(0, os.SEEK_END)
    length = buf.tell()
    buf.seek(0)
    # 다중 페이지: 원본파일명_images.zip 형식으로 파일명 설정
    base_name = os.path.splitext(name)[0]
    korean_zip_filename = f"{base_name}_images.zip"
    resp = send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=korean_zip_filename)
    resp.headers["Content-Length"] = str(length)
    # UTF-8 인코딩을 위한 Content-Disposition 헤더 설정 (URL 인코딩)
    import urllib.parse
    encoded_zip_filename = urllib.parse.quote(korean_zip_filename)
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_zip_filename}"
    return resp

# 호환 라우트: 당신의 테스트 URL대로도 동작합니다.
@app.route("/api/pdf-image/convert_to_images", methods=["POST"])
def compat_convert_to_images():
    return api_pdf_to_images()

# 추가 호환 라우트: /convert_to_images 경로 지원
@app.route("/convert_to_images", methods=["POST"])
def convert_to_images():
    return api_pdf_to_images()

# 웹 인터페이스용 /convert 라우트 추가
@app.route("/convert", methods=["POST"])
def convert():
    return api_pdf_to_images()

# 404 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint was not found.",
        "available_endpoints": {
            "service_info": "GET /",
            "health_check": "GET /health",
            "pdf_conversion": "POST /api/pdf-to-images",
            "web_interface": "POST /convert",
            "compatibility_routes": [
                "POST /api/pdf-image/convert_to_images",
                "POST /convert_to_images"
            ]
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
    app.run(debug=True, host='0.0.0.0', port=5000)