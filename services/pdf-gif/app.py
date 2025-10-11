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
            x = type(default)(v) 
        except: 
            return default 
        return max(lo, min(hi, x)) 

    scale = clamp(request.form.get("scale", "1.0"), 0.2, 2.0, 1.0) 
    delay_ms = clamp(request.form.get("delay_ms", "400"), 20, 2000, 400) 
    colors = clamp(request.form.get("colors", "128"), 2, 256, 128) 
    dither = clamp(request.form.get("dither", "1"), 0, 1, 1) 
    max_pages = clamp(request.form.get("max_pages", "100"), 1, 1000, 100) 

    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"} 
    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}, scale={scale}, delay={delay_ms}, colors={colors}, dither={dither}, max_pages={max_pages}") 

    def run_job(): 
        global current_job_id 
        current_job_id = job_id 
        try: 
            set_progress(job_id, 10, "변환 준비 중") 
            out_path, name, ctype = perform_gif_conversion( 
                in_path, base_name, 
                scale=scale, delay_ms=delay_ms, colors=colors, dither=dither, max_pages=max_pages 
            ) 
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
    if not info: return jsonify({"error":"job not found"}), 404 
    if info.get("status") != "done": return jsonify({"error":"not ready"}), 409 
    path, name, ctype = info.get("path"), info.get("name"), info.get("ctype") 
    return send_download_memory(path, name, ctype) 

@app.errorhandler(HTTPException) 
def handle_http_exc(e): 
    return jsonify({"error": e.description}), e.code 

@app.errorhandler(Exception) 
def handle_any(e): 
    app.logger.exception("Unhandled") 
    return jsonify({"error": str(e)}), 500

if __name__ == "__main__": 
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port)