import os
import io
import urllib.parse
import tempfile
import shutil
import errno
import zipfile
import logging
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file, send_from_directory, abort
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import fitz  # PyMuPDF
from PIL import Image

app = Flask(__name__, static_folder="web", static_url_path="")
logging.basicConfig(level=logging.INFO)

# CORS (프리뷰/프로덕션 허용)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://77-tools.xyz",
            "https://www.77-tools.xyz",
            "https://popular-77.vercel.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Disposition"]
    }
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}
current_job_id = None

def safe_base_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename or "output"))[0]
    return base.replace("/", "_").replace("\\", "_").strip() or "output"

def set_progress(job_id, p, msg=None):
    info = JOBS.setdefault(job_id, {})
    info["progress"] = int(p)
    if msg is not None:
        info["message"] = msg

def send_download_memory(path: str, download_name: str, ctype: str):
    if not path or not os.path.exists(path):
        return jsonify({"error": "output file missing"}), 500
    with open(path, "rb") as f:
        data = f.read()
    resp = send_file(
        io.BytesIO(data),
        mimetype=ctype,
        as_attachment=True,
        download_name=download_name,
        conditional=False
    )
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(len(data))
    resp.headers["Cache-Control"] = "no-store"
    quoted = urllib.parse.quote(download_name)
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quoted}"
    return resp

def pix_to_rgba(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    return img if mode == "RGBA" else img.convert("RGBA")

def remove_white_to_alpha(rgba: Image.Image, white_threshold: int = 250) -> Image.Image:
    # 밝은 영역(종이 배경)을 투명으로
    gray = rgba.convert("L")
    alpha_mask = gray.point(lambda p: 0 if p >= white_threshold else 255)
    out = rgba.copy()
    out.putalpha(alpha_mask)
    return out

def perform_png_conversion(in_path: str, base_name: str,
                          scale: float = 1.0,
                          transparent: int = 0,
                          white_threshold: int = 250):
    with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:  # 같은 디스크에 임시폴더
        doc = fitz.open(in_path)
        mat = fitz.Matrix(scale, scale)
        page_count = doc.page_count
        out_paths = []

        for i in range(page_count):
            set_progress(current_job_id, 10 + int(80 * (i + 1) / page_count), f"페이지 {i+1}/{page_count} 처리 중")
            page = doc.load_page(i)
            # 알파 포함 렌더(투명 처리 대비)
            pix = page.get_pixmap(matrix=mat, alpha=True)
            rgba = pix_to_rgba(pix)
            if transparent:
                rgba = remove_white_to_alpha(rgba, white_threshold=white_threshold)
            out_path = os.path.join(tmp, f"{base_name}_{i+1:02d}.png")
            rgba.save(out_path, format="PNG", optimize=True)
            out_paths.append(out_path)

        doc.close()

        if len(out_paths) == 1:
            final_name = f"{base_name}.png"
            final_path = os.path.join(OUTPUTS_DIR, final_name)
            if os.path.exists(final_path): 
                os.remove(final_path)
            shutil.move(out_paths[0], final_path)  # EXDEV 안전
            return final_path, final_name, "image/png"

        final_name = f"{base_name}.zip"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        if os.path.exists(final_path): 
            os.remove(final_path)
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in out_paths:
                zf.write(p, arcname=os.path.basename(p))
        return final_path, final_name, "application/zip"

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

@app.route("/convert-async", methods=["POST"])
def convert_async():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400

    base_name = safe_base_name(f.filename)
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)

    def clamp_num(v, lo, hi, default, T=float):
        try: 
            x = T(v)
        except: 
            return default
        return max(lo, min(hi, x))

    scale = clamp_num(request.form.get("scale", "1.0"), 0.2, 2.0, 1.0, float)
    transparent = clamp_num(request.form.get("transparent", "0"), 0, 1, 0, int)
    white_threshold = clamp_num(request.form.get("white_threshold", "250"), 0, 255, 250, int)

    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}, scale={scale}, transparent={transparent}, th={white_threshold}")

    def run_job():
        global current_job_id
        current_job_id = job_id
        try:
            set_progress(job_id, 5, "변환 시작")
            final_path, final_name, content_type = perform_png_conversion(
                in_path, base_name, scale, transparent, white_threshold
            )
            set_progress(job_id, 100, "완료")
            JOBS[job_id].update({
                "status": "completed",
                "output_path": final_path,
                "filename": final_name,
                "content_type": content_type
            })
        except Exception as e:
            app.logger.error(f"[{job_id}] conversion failed: {str(e)}")
            JOBS[job_id].update({
                "status": "failed",
                "error": str(e),
                "message": f"오류: {str(e)}"
            })
        finally:
            # 입력 파일 정리
            if os.path.exists(in_path):
                try:
                    os.remove(in_path)
                except:
                    pass
            current_job_id = None

    executor.submit(run_job)
    return jsonify({"job_id": job_id})

@app.route("/job/<job_id>", methods=["GET"])
def get_job_status(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    
    job = JOBS[job_id].copy()
    # 내부 경로는 노출하지 않음
    if "output_path" in job:
        del job["output_path"]
    
    return jsonify(job)

@app.route("/download/<job_id>", methods=["GET"])
def download_result(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    
    job = JOBS[job_id]
    if job["status"] != "completed":
        return jsonify({"error": "Job not completed"}), 400
    
    output_path = job["output_path"]
    if not os.path.exists(output_path):
        return jsonify({"error": "Output file not found"}), 404
    
    try:
        return send_download_memory(
            output_path,
            job["filename"],
            job["content_type"]
        )
    finally:
        # 다운로드 후 정리
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        if job_id in JOBS:
            del JOBS[job_id]

@app.route("/convert", methods=["POST"])
def convert_sync():
    """동기 변환 (호환성용)"""
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    def clamp_num(v, lo, hi, default, T=float):
        try: 
            x = T(v)
        except: 
            return default
        return max(lo, min(hi, x))

    scale = clamp_num(request.form.get("scale", "1.0"), 0.2, 2.0, 1.0, float)
    transparent = clamp_num(request.form.get("transparent", "0"), 0, 1, 0, int)
    white_threshold = clamp_num(request.form.get("white_threshold", "250"), 0, 255, 250, int)
    
    base_name = safe_base_name(f.filename)
    
    # 입력 파일 저장
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    
    try:
        global current_job_id
        current_job_id = job_id
        final_path, final_name, content_type = perform_png_conversion(
            in_path, base_name, scale, transparent, white_threshold
        )
        
        return send_download_memory(final_path, final_name, content_type)
        
    except Exception as e:
        app.logger.error(f"Sync conversion failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # 정리
        if os.path.exists(in_path):
            try:
                os.remove(in_path)
            except:
                pass
        if 'final_path' in locals() and os.path.exists(final_path):
            try:
                os.remove(final_path)
            except:
                pass
        current_job_id = None

# SPA fallback route
@app.route("/<path:path>")
def spa(path):
    # API 경로는 제외
    if path in ("health", "convert", "convert-async") or path.startswith(("job/", "download/")) or path.startswith("api/"):
        abort(404)
    full = os.path.join(app.static_folder, path)
    if os.path.isfile(full):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# API alias routes for /api/pdf-png/* paths
@app.get("/api/pdf-png/health")
def _alias_health():
    return health()

@app.post("/api/pdf-png/convert-async")
def _alias_convert_async():
    return convert_async()

@app.post("/api/pdf-png/convert")
def _alias_convert_sync():
    return convert_sync()

@app.get("/api/pdf-png/job/<job_id>")
def _alias_job(job_id):
    return get_job_status(job_id)

@app.get("/api/pdf-png/download/<job_id>")
def _alias_download(job_id):
    return download_result(job_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)