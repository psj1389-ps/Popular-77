import os, re, io, zipfile, tempfile, logging, urllib.parse, mimetypes
import shutil, errno
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file, redirect, send_from_directory, abort
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed
import fitz  # PyMuPDF

app = Flask(__name__, static_folder="web", static_url_path="")
logging.basicConfig(level=logging.INFO)

# HOME_URL 변수 제거 - 자체 인터페이스 서빙

# CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://77-tools.xyz",
            "https://www.77-tools.xyz",
            "https://popular-77.vercel.app",
            "https://*.vercel.app"
        ],
        "expose_headers": ["Content-Disposition"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 기존 before_request 제거 - SPA fallback으로 대체됨

@app.errorhandler(HTTPException)
def handle_http_exc(e):
    # Flask 기본 404/405 등을 그대로 코드 유지 + JSON 바디
    return jsonify({"error": e.description or "error"}), e.code

@app.errorhandler(Exception)
def handle_any_exc(e):
    app.logger.exception("Unhandled")
    return jsonify({"error": str(e)}), 500

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}  # job_id -> dict

def safe_move(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        # 같은 파일시스템이면 원자적 교체
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
    except OSError as e:
        # 다른 파일시스템이면 복사 → 원본 삭제
        if getattr(e, "errno", None) == errno.EXDEV:
            shutil.copy2(src, dst)
            try: 
                os.unlink(src)
            except FileNotFoundError: 
                pass
        else:
            raise

def guess_mime_by_name(name: str) -> str:
    n = (name or "").lower()
    if n.endswith(".svg"):  return "image/svg+xml"
    if n.endswith(".zip"):  return "application/zip"
    return mimetypes.guess_type(n)[0] or "application/octet-stream"

def safe_base_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename or "output"))[0]
    base = base.replace("/", "_").replace("\\", "_")
    base = re.sub(r'[\r\n\t"]+', "_", base).strip()
    return base or "output"

def attach_download_headers(resp, download_name: str):
    quoted = urllib.parse.quote(download_name)
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quoted}"
    return resp

def set_progress(job_id, p, msg=None):
    info = JOBS.setdefault(job_id, {})
    info["progress"] = int(p)
    if msg is not None:
        info["message"] = msg

def send_download_memory(path: str):
    if not path or not os.path.exists(path):
        return jsonify({"error": "output file missing"}), 500

    name = os.path.basename(path).strip() or "output.svg"
    n = name.lower()
    if n.endswith(".svg"):
        ctype = "image/svg+xml"
    elif n.endswith(".zip"):
        ctype = "application/zip"
    else:
        ctype = "application/octet-stream"

    with open(path, "rb") as f:
        data = f.read()
    size = len(data)

    resp = send_file(
        io.BytesIO(data),
        mimetype=ctype,
        as_attachment=True,
        download_name=name,
        conditional=False
    )
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(size)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{urllib.parse.quote(name)}"
    )
    return resp

def perform_svg_conversion(in_path, scale: float, base_name: str):
    result_paths = []
    with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
        doc = fitz.open(in_path)
        page_count = doc.page_count
        mat = fitz.Matrix(scale, scale)

        for i in range(page_count):
            set_progress(current_job_id, 10 + int(80*(i+1)/page_count), f"페이지 {i+1}/{page_count} 벡터 추출 중")
            page = doc.load_page(i)
            svg = page.get_svg_image(matrix=mat)
            if not svg.lstrip().startswith("<"):
                svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg
            out_p = os.path.join(tmp, f"{base_name}_{i+1:0{max(2,len(str(page_count)))}d}.svg")
            with open(out_p, "w", encoding="utf-8") as f:
                f.write(svg)
            result_paths.append(out_p)

        if len(result_paths) == 1:
            final_name = f"{base_name}.svg"
            final_path = os.path.join(OUTPUTS_DIR, final_name)
            if os.path.exists(final_path): os.remove(final_path)
            safe_move(result_paths[0], final_path)
            return final_path, final_name, "image/svg+xml"

        final_name = f"{base_name}.zip"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        if os.path.exists(final_path): os.remove(final_path)
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in result_paths:
                zf.write(p, arcname=os.path.basename(p))
        return final_path, final_name, "application/zip"

# 루트: web/index.html 서빙
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# /tools 경로도 동일한 인터페이스 서빙
@app.get("/tools")
def tools():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/health")
def health():
    return "ok", 200

@app.post("/convert-async")
def convert_async():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400

    base_name = safe_base_name(f.filename)
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    quality = request.form.get("quality", "medium")
    try:
        scale = float(request.form.get("scale", "1.0"))
    except Exception:
        scale = 1.0
    scale = max(0.2, min(2.0, scale))

    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}, scale={scale}, quality={quality}")

    def run_job():
        global current_job_id
        current_job_id = job_id
        try:
            set_progress(job_id, 10, "변환 준비 중")
            out_path, name, ctype = perform_svg_conversion(in_path, scale, base_name)
            JOBS[job_id] = {"status": "done", "path": out_path, "name": name, "ctype": ctype,
                            "progress": 100, "message": "완료"}
            app.logger.info(f"[{job_id}] done: {out_path} exists={os.path.exists(out_path)}")
        except Exception as e:
            app.logger.exception("convert error")
            JOBS[job_id] = {"status": "error", "error": str(e), "progress": 0, "message": "오류"}
        finally:
            try: os.remove(in_path)
            except: pass

    executor.submit(run_job)
    return jsonify({"job_id": job_id}), 202

@app.get("/job/<job_id>")
def job_status(job_id):
    info = JOBS.get(job_id)
    if not info: return jsonify({"error": "job not found"}), 404
    info.setdefault("progress", 0); info.setdefault("message", "")
    return jsonify(info), 200

@app.get("/download/<job_id>")
def job_download(job_id):
    info = JOBS.get(job_id)
    if not info:  return jsonify({"error":"job not found"}), 404
    if info.get("status") != "done":  return jsonify({"error":"not ready"}), 409
    path = info.get("path")
    return send_download_memory(path)

@app.post("/convert")
def convert_compat():
    """
    구(舊) 클라이언트가 /convert로 올 때를 위한 하위호환 엔드포인트.
    내부적으로 /convert-async 로직을 그대로 실행해 job_id를 반환합니다.
    """
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    # 그대로 convert-async 실행
    return convert_async()

@app.post("/convert_to_svg")
def convert_to_svg():
    """
    템플릿 프론트엔드가 /convert_to_svg로 요청할 때를 위한 엔드포인트.
    내부적으로 /convert-async 로직을 실행하되, 직접 파일을 반환합니다.
    """
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400

    base_name = safe_base_name(f.filename)
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    quality = request.form.get("quality", "medium")
    try:
        scale = float(request.form.get("scale", "1.0"))
    except Exception:
        scale = 1.0
    scale = max(0.2, min(2.0, scale))

    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}, scale={scale}, quality={quality}")

    try:
        out_path, name, ctype = perform_svg_conversion(in_path, scale, base_name)
        app.logger.info(f"[{job_id}] done: {out_path} exists={os.path.exists(out_path)}")
        
        # 파일을 직접 반환
        response = send_file(out_path, as_attachment=True, download_name=name, mimetype=ctype)
        attach_download_headers(response, name)
        
        # 임시 파일들 정리
        try: os.remove(in_path)
        except: pass
        try: os.remove(out_path)
        except: pass
        
        return response
    except Exception as e:
        app.logger.exception("convert error")
        try: os.remove(in_path)
        except: pass
        return jsonify({"error": str(e)}), 500

# 정적 파일 or SPA fallback(가장 아래에 위치)
@app.route("/<path:path>")
def spa(path):
    # API 경로는 제외
    if path in ("health", "convert-async") or path.startswith(("job/", "download/")):
        abort(404)
    full = os.path.join(app.static_folder, path)
    if os.path.isfile(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(Exception)
def handle_any(e):
    app.logger.exception("Unhandled")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)