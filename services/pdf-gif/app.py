import os, io, urllib.parse, tempfile, shutil, errno, zipfile, logging
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file, render_template
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

def pix_to_pil(pix: fitz.Pixmap, keep_alpha: bool) -> Image.Image:
    """Convert PyMuPDF Pixmap to PIL Image"""
    # keep_alpha가 True이고 pix.alpha가 있으면 RGBA 유지
    mode = "RGBA" if (keep_alpha and pix.alpha) else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    return img

def perform_gif_conversion(in_path: str, base_name: str, job_id: str,
                           scale: float = 1.0,
                           delay_ms: int = 400,
                           colors: int = 128,
                           dither: int = 1,
                           max_pages: int = 100,
                           transparent: int = 0):
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
            # 투명 배경: alpha=True로 렌더
            pix = page.get_pixmap(matrix=mat, alpha=bool(transparent))
            pil = pix_to_pil(pix, keep_alpha=bool(transparent))
            
            if transparent:
                # RGBA → 팔레트(P)로 양자화하면서 투명정보 유지 시도
                pal = pil.convert("RGBA").quantize(
                    colors=max(2, min(256, colors)),
                    method=Image.MEDIANCUT,
                    dither=Image.FLOYDSTEINBERG if dither else Image.NONE,
                )
                # Pillow가 RGBA 양자화 시 transparency 인덱스를 info에 넣는 경우가 많음
                # 첫 프레임의 transparency 값을 저장해 두었다가 저장 시 넘깁니다.
                frames.append(pal)
            else:
                # 불투명: 흰색 배경으로(알파 없음) + 팔레트 축소
                pal = pil.convert("RGB").convert(
                    "P", palette=Image.ADAPTIVE, colors=max(2, min(256, colors))
                )
                frames.append(pal)

        final_name = f"{base_name}.gif"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        if os.path.exists(final_path):
            os.remove(final_path)

        save_kwargs = dict(
            save_all=len(frames) > 1,
            loop=0,
            optimize=True,
            duration=max(20, int(delay_ms)),
            disposal=2,
        )

        # 투명 인덱스가 잡혀있으면 전달
        if transparent:
            trans_idx = frames[0].info.get("transparency")
            if trans_idx is not None:
                save_kwargs["transparency"] = trans_idx

        if len(frames) == 1:
            frames[0].save(final_path, **{k: v for k, v in save_kwargs.items() if k not in ("save_all", "append_images")})
        else:
            frames[0].save(final_path, append_images=frames[1:], **save_kwargs)
        return final_path, final_name, "image/gif"

@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

@app.route("/convert", methods=["POST"])
def convert():
    """Synchronous PDF to GIF conversion"""
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

    scale = clamp(request.form.get("scale", "1.0"), 0.1, 3.0, 1.0)
    delay_ms = clamp(request.form.get("delay_ms", "400"), 50, 5000, 400)
    colors = clamp(request.form.get("colors", "128"), 2, 256, 128)
    dither = clamp(request.form.get("dither", "1"), 0, 1, 1)
    max_pages = clamp(request.form.get("max_pages", "100"), 1, 500, 100)
    transparent = clamp(request.form.get("transparent", "0"), 0, 1, 0)  # 0=사용 안함, 1=사용 

    try:
        out_path, name, ctype = perform_gif_conversion( 
            in_path, base_name, job_id,
            scale=scale, delay_ms=delay_ms, colors=colors, dither=dither, max_pages=max_pages 
        ) 
        
        # 동기 변환이므로 바로 파일 반환
        response = send_download_memory(out_path, name, ctype)
        
        # 정리
        try:
            os.remove(in_path)
            os.remove(out_path)
        except:
            pass
            
        return response
        
    except Exception as e:
        app.logger.exception("Synchronous convert error")
        try:
            os.remove(in_path)
        except:
            pass
        return jsonify({"error": str(e)}), 500

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
                in_path, base_name, job_id,
                scale=scale, delay_ms=delay_ms, colors=colors, dither=dither, max_pages=max_pages, transparent=transparent 
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
    
    if not path or not os.path.exists(path):
        return jsonify({"error": "output file not found"}), 404
    
    try:
        response = send_download_memory(path, name, ctype)
        # 다운로드 후 정리
        try:
            os.remove(path)
            del JOBS[job_id]
        except:
            pass
        return response
    except Exception as e:
        app.logger.exception(f"Download failed for job {job_id}")
        return jsonify({"error": "download failed"}), 500 

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