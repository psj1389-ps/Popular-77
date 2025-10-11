import os, io, urllib.parse, tempfile, shutil, errno, zipfile, logging
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import fitz  # PyMuPDF
from PIL import Image

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# CORS
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
        "expose_headers": ["Content-Disposition"],
    }
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}

def safe_base_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename or "output"))[0]
    return base.replace("/", "_").replace("\\", "_").strip() or "output"

def set_progress(job_id, p, msg=None):
    JOBS.setdefault(job_id, {})
    JOBS[job_id]["progress"] = int(p)
    if msg is not None:
        JOBS[job_id]["message"] = msg

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
    resp.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{urllib.parse.quote(download_name)}"
    )
    return resp

def safe_move(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        if os.path.exists(dst):
            os.remove(dst)
        os.replace(src, dst)  # 같은 FS면 rename
    except OSError as e:
        if getattr(e, "errno", None) == errno.EXDEV:
            shutil.copy2(src, dst)         # 다른 FS면 copy+unlink
            try: os.unlink(src)
            except FileNotFoundError: pass
        else:
            raise

def pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    if mode == "RGBA":
        img = img.convert("RGB")
    return img

def perform_gif_conversion(in_path: str, base_name: str, job_id: str,
                           scale: float = 1.0,
                           delay_ms: int = 400,
                           colors: int = 128,
                           dither: int = 1,
                           max_pages: int = 100):
    """
    PDF -> Animated GIF 1개 생성.
    반환: (final_path, final_name, content_type)
    """
    with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
        doc = fitz.open(in_path)
        page_count = doc.page_count
        mat = fitz.Matrix(scale, scale)

        frames = []
        use_pages = min(page_count, max(1, int(max_pages)))
        for i in range(use_pages):
            set_progress(job_id, 10 + int(80 * (i + 1) / use_pages), f"페이지 {i+1}/{use_pages} 처리 중")
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pil = pix_to_pil(pix)
            # 팔레트 축소(색상 수 설정) + 디더링
            pil = pil.convert("P", palette=Image.ADAPTIVE, colors=max(2, min(256, colors)))
            if not dither:
                pil.info["transparency"] = None
            frames.append(pil)

        final_name = f"{base_name}.gif"
        final_path = os.path.join(OUTPUTS_DIR, final_name)

        # 첫 프레임 저장 + 나머지 프레임 append
        if len(frames) == 1:
            if os.path.exists(final_path): os.remove(final_path)
            frames[0].save(final_path, save_all=False, loop=0, optimize=True)
        else:
            if os.path.exists(final_path): os.remove(final_path)
            frames[0].save(
                final_path,
                save_all=True,
                append_images=frames[1:],
                loop=0,
                optimize=True,
                duration=max(20, int(delay_ms)),  # 최소 20ms
                disposal=2,
            )
        return final_path, final_name, "image/gif"

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

    # 옵션 파라미터
    def clamp(v, lo, hi, default):
        try:
            return max(lo, min(hi, float(v)))
        except (ValueError, TypeError):
            return default

    scale = clamp(request.form.get("scale", 1.0), 0.2, 2.0, 1.0)
    delay_ms = clamp(request.form.get("delay_ms", 400), 50, 5000, 400)
    colors = int(clamp(request.form.get("colors", 128), 2, 256, 128))
    dither = int(clamp(request.form.get("dither", 1), 0, 1, 1))
    max_pages = int(clamp(request.form.get("max_pages", 100), 1, 500, 100))

    JOBS[job_id] = {"progress": 0, "message": "작업 시작"}

    def worker():
        try:
            set_progress(job_id, 5, "PDF 파일 분석 중")
            final_path, final_name, content_type = perform_gif_conversion(
                in_path, base_name, job_id, scale, delay_ms, colors, dither, max_pages
            )
            set_progress(job_id, 100, "변환 완료")
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["output_path"] = final_path
            JOBS[job_id]["output_name"] = final_name
            JOBS[job_id]["content_type"] = content_type
        except Exception as e:
            logging.error(f"Job {job_id} failed: {e}")
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(e)
        finally:
            try:
                if os.path.exists(in_path):
                    os.remove(in_path)
            except:
                pass

    executor.submit(worker)
    return jsonify({"job_id": job_id}), 202

@app.route("/job/<job_id>", methods=["GET"])
def get_job_status(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    
    job = JOBS[job_id]
    response = {
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
        "status": job.get("status", "running")
    }
    
    if job.get("status") == "failed":
        response["error"] = job.get("error", "Unknown error")
    
    return jsonify(response)

@app.route("/download/<job_id>", methods=["GET"])
def download_result(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    
    job = JOBS[job_id]
    if job.get("status") != "completed":
        return jsonify({"error": "Job not completed"}), 400
    
    output_path = job.get("output_path")
    output_name = job.get("output_name")
    content_type = job.get("content_type", "image/gif")
    
    if not output_path or not os.path.exists(output_path):
        return jsonify({"error": "Output file not found"}), 404
    
    try:
        response = send_download_memory(output_path, output_name, content_type)
        # 다운로드 후 정리
        try:
            os.remove(output_path)
            del JOBS[job_id]
        except:
            pass
        return response
    except Exception as e:
        logging.error(f"Download failed for job {job_id}: {e}")
        return jsonify({"error": "Download failed"}), 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify({"error": e.description}), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)