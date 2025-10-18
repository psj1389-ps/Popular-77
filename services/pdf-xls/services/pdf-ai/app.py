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

CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://77-tools.xyz",
            "https://www.77-tools.xyz",
            "https://popular-77.vercel.app",
            "https://*.vercel.app",
            "https://popular-77.onrender.com"
        ],
        "expose_headers": ["Content-Disposition"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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

def send_download_memory(path: str, download_name: str, ctype: str):
    if not path or not os.path.exists(path):
        return jsonify({"error": "output file missing"}), 500

    with open(path, "rb") as f:
        data = f.read()
    size = len(data)

    resp = send_file(
        io.BytesIO(data),
        mimetype=ctype,
        as_attachment=True,
        download_name=download_name,
        conditional=False
    )
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(size)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{urllib.parse.quote(download_name)}"
    )
    return resp

def set_progress(job_id, p, msg=None):
    info = JOBS.setdefault(job_id, {})
    info["progress"] = int(p)
    if msg is not None:
        info["message"] = msg

def parse_page_range(expr: str, page_count: int) -> list[int]:
    """
    1,3,5-7 → [0,2,4,5,6] (0-based 반환)
    page_count를 벗어나는 값은 제거
    """
    if not expr:
        return []
    expr = expr.replace(" ", "")
    pages = set()
    for part in expr.split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            if a.isdigit() and b.isdigit():
                start = int(a)
                end = int(b)
                if start > end:
                    start, end = end, start
                for p in range(start, end + 1):
                    pages.add(p)
        else:
            if part.isdigit():
                pages.add(int(part))
    # 1-based → 0-based, 유효 범위만
    result = sorted({p - 1 for p in pages if 1 <= p <= page_count})
    return result

def perform_ai_conversion(in_path: str, base_name: str, pages: list[int] | None = None):
    """
    pages: 0-based 페이지 번호 리스트. None이면 전체.
    반환: (final_path, final_name, content_type)
    """
    with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
        src = fitz.open(in_path)
        all_pages = list(range(src.page_count))
        target_pages = all_pages if not pages else [p for p in pages if 0 <= p < src.page_count]
        if not target_pages:
            raise ValueError("no valid pages selected")

        out_paths = []
        pad = max(2, len(str(max(target_pages) + 1)))  # 원본 페이지 번호 기준 패딩

        for p in target_pages:
            # current_job_id가 정의되지 않은 경우를 위한 안전장치
            try:
                set_progress(current_job_id, 10 + int(80*(len(out_paths)+1)/len(target_pages)), f"페이지 {p+1} 저장 중")
            except NameError:
                pass  # current_job_id가 없는 경우 진행률 업데이트 생략
            out_pdf = fitz.open()
            out_pdf.insert_pdf(src, from_page=p, to_page=p)
            raw_path = os.path.join(tmp, f"{base_name}_{p+1:0{pad}d}.pdf")
            out_pdf.save(raw_path)
            out_pdf.close()
            ai_path = raw_path[:-4] + ".ai"  # PDF를 .ai로 rename (Illustrator에서 열림)
            os.replace(raw_path, ai_path)
            out_paths.append(ai_path)

        if len(out_paths) == 1:
            final_name = f"{base_name}.ai"
            final_path = os.path.join(OUTPUTS_DIR, final_name)
            if os.path.exists(final_path): os.remove(final_path)
            shutil.move(out_paths[0], final_path)
            return final_path, final_name, "application/pdf"

        final_name = f"{base_name}.zip"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        if os.path.exists(final_path): os.remove(final_path)
        with zipfile.ZipFile(final_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in out_paths:
                zf.write(p, arcname=os.path.basename(p))
        return final_path, final_name, "application/zip"

@app.get("/")
def home():
    from flask import render_template
    return render_template('index.html')

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

    page_mode = request.form.get("page_mode", "all")
    page_range_expr = request.form.get("page_range", "").strip()

    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}, page_mode={page_mode}, page_range='{page_range_expr}'")

    def run_job():
        global current_job_id
        current_job_id = job_id
        try:
            set_progress(job_id, 10, "변환 준비 중")
            # 선택 페이지는 perform_ai_conversion에서 문서 열고 파싱(유효성 재검증)
            pages = None
            if page_mode == "selected" and page_range_expr:
                # 문서 열어 유효 범위로 변환
                doc = fitz.open(in_path)
                pages = parse_page_range(page_range_expr, doc.page_count)
                doc.close()
                if not pages:
                    raise ValueError("선택된 페이지가 유효하지 않습니다.")
            out_path, name, ctype = perform_ai_conversion(in_path, base_name, pages)
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

@app.post("/convert_to_ai")
def convert_to_ai():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400

    base_name = safe_base_name(f.filename)
    in_path = os.path.join(UPLOADS_DIR, f"{uuid4().hex}.pdf")
    f.save(in_path)

    page_mode = request.form.get("page_mode", "all")
    page_range_expr = request.form.get("page_range", "").strip()

    try:
        pages = None
        if page_mode == "selected" and page_range_expr:
            doc = fitz.open(in_path)
            pages = parse_page_range(page_range_expr, doc.page_count)
            doc.close()
            if not pages:
                return jsonify({"error": "선택된 페이지 범위가 유효하지 않습니다."}), 400

        out_path, name, ctype = perform_ai_conversion(in_path, base_name, pages)
        return send_download_memory(out_path, name, ctype)
    except Exception as e:
        app.logger.exception("convert_to_ai error")
        return jsonify({"error": str(e)}), 500
    finally:
        try: os.remove(in_path)
        except: pass

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