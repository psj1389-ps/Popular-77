from flask import Flask, request, jsonify, send_file, make_response, render_template, redirect
from flask_cors import CORS
import os, io, sys, logging, subprocess, shlex, shutil
from uuid import uuid4
from urllib.parse import quote
import unicodedata

app = Flask(__name__, template_folder="templates", static_folder="static")
logging.basicConfig(level=logging.INFO)

# 최대 업로드 크기 설정 (60MB)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", "60")) * 1024 * 1024

CORS(app, resources={r"/*": {"origins": [
    "http://localhost:5173",
    "https://77-tools.xyz",
    "https://www.77-tools.xyz",
    "https://popular-77.vercel.app",
    "https://popular-77-xbqq.onrender.com"
], "expose_headers": ["Content-Disposition"], "methods": ["GET","POST","OPTIONS"], "allow_headers": ["Content-Type"], "supports_credentials": False}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

ALLOWED_EXTS = {".ppt", ".pptx"}

SERVICE_NAME = os.getenv("SERVICE_DIR", "pptx-pdf")

def _accept_from_allowed():
    # ALLOWED_EXTS = {".ppt",".pptx"} 같은 세트가 서비스별로 이미 있습니다.
    return ",".join(sorted(ALLOWED_EXTS))

_titles = {
    "docx-pdf": "DOCX to PDF Converter",
    "pptx-pdf": "PPTX to PDF Converter",
    "xls-pdf": "XLS/XLSX to PDF Converter",
}

def ascii_fallback(name: str) -> str:
    a = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode("ascii") or "converted.pdf"
    return "".join(c for c in a if c.isalnum() or c in ".- ") or "converted.pdf"

def _set_pdf_disposition(resp, pdf_name: str):
    # CR/LF/쌍따옴표 삭제(헤더 인젝션/파싱 오류 방지)
    safe = pdf_name.replace('"','').replace('\r','').replace('\n','')
    ascii_name = ascii_fallback(safe)
    utf8_name = quote(safe, safe="")  # RFC5987로 퍼센트 인코딩
    resp.headers["Content-Disposition"] = (
        f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_name}'
    )
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    # 커스텀 헤더 제거 (X-Download-Filename 등)
    resp.headers.pop("X-Download-Filename", None)
    return resp

def _is_pdf(path: str) -> bool:
    try:
        with open(path,"rb") as f: return f.read(4) == b"%PDF"
    except: return False

def _find_soffice():
    return shutil.which("soffice") or shutil.which("libreoffice") or "/usr/bin/soffice"

def perform_libreoffice(in_path: str, out_pdf_path: str):
    soffice = _find_soffice()
    if not soffice: raise RuntimeError("LibreOffice not found")
    outdir = os.path.dirname(out_pdf_path); os.makedirs(outdir, exist_ok=True)
    ext = os.path.splitext(in_path)[1].lower()
    
    # PPT/PPTX 파일에 대해 올바른 필터 사용
    if ext in ['.ppt', '.pptx']:
        conv = "pdf"  # 간단한 pdf 필터 사용
    else:
        conv = "pdf"
    
    # 옵션 강화(헤드리스/복구/락/디폴트 비활성)
    cmd = [
        soffice, "--headless", "--invisible",
        "--nologo", "--nofirststartwizard", "--norestore",
        "--nolockcheck", "--nodefault",
        "--convert-to", conv, "--outdir", outdir, in_path
    ]
    # 환경변수: HOME=/tmp (LO가 사용자 디렉터리 필요로 할 때 오류 예방)
    env = os.environ.copy()
    env.setdefault("HOME", "/tmp")
    env.setdefault("SAL_USE_VCL", "svp")
    env.setdefault("OOO_DISABLE_RECOVERY", "1")

    logging.info("[LO] cmd=%s", " ".join(shlex.quote(x) for x in cmd))
    p = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logging.info("[LO] rc=%s", p.returncode)
    if p.stdout: logging.info("[LO] stdout=%s", p.stdout[:4000])
    if p.stderr: logging.warning("[LO] stderr=%s", p.stderr[:4000])

    if p.returncode != 0:
        raise RuntimeError(f"soffice rc={p.returncode}, err={p.stderr[:800]}")

    produced = os.path.join(outdir, os.path.splitext(os.path.basename(in_path))[0] + ".pdf")
    if not os.path.exists(produced):
        raise RuntimeError(f"PDF not produced: {produced}")
    
    # out_pdf_path로 통일
    if produced != out_pdf_path:
        if os.path.exists(out_pdf_path): os.remove(out_pdf_path)
        os.replace(produced, out_pdf_path)
    




@app.get("/health")
def health():
    """헬스체크 엔드포인트"""
    try:
        soffice_path = _find_soffice()
        if not soffice_path:
            return jsonify({
                "status": "error",
                "message": "LibreOffice not found",
                "timestamp": os.getenv("RENDER_GIT_COMMIT", "unknown")
            }), 500
        
        return jsonify({
            "status": "healthy",
            "service": "pptx-pdf",
            "timestamp": os.getenv("RENDER_GIT_COMMIT", "unknown")
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e),
            "timestamp": os.getenv("RENDER_GIT_COMMIT", "unknown")
        }), 500

@app.get("/diag/pip")
def diag_pip():
    import pkgutil
    try:
        import pkg_resources
        installed = sorted([str(d).split(' ')[0] for d in pkg_resources.working_set])
    except Exception:
        installed = []
    return {"installed": installed[:50]}

@app.post("/convert")
def convert_sync():
    in_path = None
    try:
        f = request.files.get("file") or request.files.get("document")
        if not f: return jsonify({"error":"file field is required"}), 400
        in_name = f.filename or "input.pptx"
        base, ext = os.path.splitext(os.path.basename(in_name)); ext = ext.lower()
        if ext not in ALLOWED_EXTS: return jsonify({"error": f"unsupported extension: {ext}"}), 415

        jid      = uuid4().hex
        in_path  = os.path.join(UPLOADS_DIR, f"{jid}{ext}")
        tmp_out  = os.path.join(OUTPUTS_DIR, f"{jid}.pdf")
        out_name = f"{base}.pdf"
        final_out= os.path.join(OUTPUTS_DIR, out_name)

        f.save(in_path)
        perform_libreoffice(in_path, tmp_out)
        if not _is_pdf(tmp_out): raise RuntimeError("Output is not a valid PDF")

        if tmp_out != final_out:
            if os.path.exists(final_out): os.remove(final_out)
            os.replace(tmp_out, final_out)

        size = os.path.getsize(final_out)
        resp = send_file(final_out, as_attachment=True, download_name=out_name,
                         mimetype="application/pdf", conditional=False)
        resp.headers["Content-Length"] = str(size)
        return _set_pdf_disposition(resp, out_name)

    except Exception as e:
        logging.exception("conversion failed")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            if in_path and os.path.exists(in_path): os.remove(in_path)
        except Exception:
            pass

@app.post("/test-name")
def test_name():
    """헤더/파일명만 테스트(LO 호출 없이)"""
    try:
        name = (request.form.get("name") or "한글 이름 테스트") + ".pdf"
        data = b"%PDF-1.4\n%test\n"  # 작은 가짜 PDF 헤더
        resp = send_file(io.BytesIO(data), as_attachment=True, download_name=name, mimetype="application/pdf")
        resp.headers["Content-Length"] = str(len(data))
        return _set_pdf_disposition(resp, name)
    except Exception as e:
        logging.exception("test-name failed")
        return jsonify({"error": str(e)}), 500

def _index_response():
    page = {
        "title": _titles.get(SERVICE_NAME, "File to PDF Converter"),
        "subtitle": "문서를 PDF로 안정적으로 변환",
        "accept": _accept_from_allowed(),
        "service": SERVICE_NAME,
        "max_mb": os.getenv("MAX_CONTENT_LENGTH_MB", "60"),
    }
    try:
        resp = make_response(render_template("index.html", page=page))
    except Exception:
        html = f"""
<!doctype html><meta charset="utf-8">
<h2>{page['title']}</h2>
<form action="/convert" method="post" enctype="multipart/form-data">
<input type="file" name="file" accept="{page['accept']}" required>
<button type="submit">Convert</button>
</form>
<p><a href="/health">/health</a> · Max {page['max_mb']}MB</p>
"""
        resp = make_response(html, 200)
    resp.headers["Cache-Control"] = "no-store"
    return resp

# 1) 루트는 index로
@app.route("/", methods=["GET", "HEAD"])
def _root_index():
    return _index_response()

# 2) 캐치올 리라이트: 등록되지 않은 GET/HEAD 경로는 index로 폴백
@app.route("/<path:path>", methods=["GET", "HEAD"])
def _catch_all(path):
    # API/정적 경로는 리라이트하지 않음
    protected = ("/health", "/convert", "/routes", "/static", "/favicon.ico")
    if any(("/" + path).startswith(p) for p in protected):
        from flask import abort
        abort(404)
    return _index_response()

# (선택) 라우트 목록으로 등록 여부 확인
@app.get("/routes")
def list_routes():
    return {"routes": [f"{r.rule} {','.join(sorted(r.methods))}" for r in app.url_map.iter_rules()]}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)