import os, re, io, zipfile, tempfile, logging, urllib.parse, mimetypes
import shutil, errno
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file, redirect
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed
import fitz  # PyMuPDF

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Redirect URL
HOME_URL = "https://77-tools.xyz/tools/pdf-ai"

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

@app.before_request
def route_front_routes():
    if request.path.startswith("/tools/"):
        return redirect(HOME_URL, code=302)

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
JOBS = {}

def safe_move(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        # 같은 파일시스템이면 원자적 교체
        if os.path.exists(dst):
            os.remove(dst)
        os.replace(src, dst)
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
    if n.endswith(".svg"): return "image/svg+xml"
    if n.endswith(".zip"): return "application/zip"
    if n.endswith(".ai"): return "application/pdf"  # Illustrator 호환 PDF
    if n.endswith(".pptx"): return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if n.endswith(".xlsx"): return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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

def perform_ai_conversion(in_path, base_name: str):
    result_paths = []
    with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
        src = fitz.open(in_path)
        pages = src.page_count
        for i in range(pages):
            set_progress(current_job_id, 10 + int(80*(i+1)/pages), f"페이지 {i+1}/{pages} 저장 중")
            out_pdf = fitz.open()            # 빈 문서
            out_pdf.insert_pdf(src, from_page=i, to_page=i)
            raw_path = os.path.join(tmp, f"{base_name}_{i+1:0{max(2,len(str(pages)))}d}.pdf")
            out_pdf.save(raw_path)           # PDF로 저장
            out_pdf.close()
            # .ai로 이름 변경(실제 포맷은 PDF, 일러스트에서 열 수 있음)
            ai_path = raw_path[:-4] + ".ai"
            os.replace(raw_path, ai_path)
            result_paths.append(ai_path)

        if len(result_paths) == 1:
            final_name = f"{base_name}.ai"
            final_path = os.path.join(OUTPUTS_DIR, final_name)
            if os.path.exists(final_path): os.remove(final_path)
            safe_move(result_paths[0], final_path)
            return final_path, final_name, "application/pdf"

        final_name = f"{base_name}.zip"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        if os.path.exists(final_path): os.remove(final_path)
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in result_paths:
                zf.write(p, arcname=os.path.basename(p))
        return final_path, final_name, "application/zip"

@app.get("/")
def home():
    return redirect(HOME_URL, code=302)

@app.route("/tools", defaults={"path": ""})
@app.route("/tools/<path:path>")
def tools_redirect(path):
    return redirect(HOME_URL, code=302)

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

    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}")

    def run_job():
        global current_job_id
        current_job_id = job_id
        try:
            set_progress(job_id, 10, "변환 준비 중")
            out_path, name, ctype = perform_ai_conversion(in_path, base_name)
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
    if not info: return jsonify({"error":"job not found"}), 404
    info.setdefault("progress", 0); info.setdefault("message", "")
    return jsonify(info), 200

@app.get("/download/<job_id>")
def job_download(job_id):
    info = JOBS.get(job_id)
    if not info: return jsonify({"error":"job not found"}), 404
    if info.get("status") != "done": return jsonify({"error":"not ready"}), 409
    
    path, name = info.get("path"), info.get("name")
    if not path or not os.path.exists(path): return jsonify({"error":"output file missing"}), 500
    
    ctype = guess_mime_by_name(name)
    resp = send_file(path, mimetype=ctype, as_attachment=True, download_name=name)
    # 파일명 한글 안정화
    return attach_download_headers(resp, name)

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

@app.errorhandler(Exception)
def handle_any(e):
    app.logger.exception("Unhandled")
    return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)