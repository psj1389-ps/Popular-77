from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os, io, sys, logging, tempfile, shutil, subprocess, shlex
from uuid import uuid4

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["Content-Disposition"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

ALLOWED_EXTS = {".doc", ".docx"}


def _send_download(path: str, download_name: str):
    if not os.path.exists(path):
        return jsonify({"error": "output not found"}), 500
    with open(path, "rb") as f:
        data = f.read()
    resp = send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
    )
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(len(data))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Disposition"] = f'attachment; filename="{download_name}"'
    return resp


def perform_createpdf_libreoffice(in_path: str, out_pdf_path: str):
    outdir = os.path.dirname(out_pdf_path)
    os.makedirs(outdir, exist_ok=True)
    cmd = f"soffice --headless --nologo --nofirststartwizard --convert-to pdf --outdir {shlex.quote(outdir)} {shlex.quote(in_path)}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"LibreOffice failed: {proc.stderr.decode('utf-8','ignore')}")
    base = os.path.splitext(os.path.basename(in_path))[0]
    produced = os.path.join(outdir, f"{base}.pdf")
    if produced != out_pdf_path:
        if os.path.exists(out_pdf_path):
            os.remove(out_pdf_path)
        os.replace(produced, out_pdf_path)


@app.get("/")
def index():
    return jsonify({
        "service": "docx-pdf",
        "status": "ok",
        "routes": {
            "GET /health": "service health",
            "POST /convert": "multipart file ('file' or 'document') -> PDF via LibreOffice",
        }
    })


@app.get("/health")
def health():
    try:
        v = subprocess.run(["soffice", "--version"], capture_output=True, text=True, check=False)
        soffice_ver = (v.stdout or v.stderr or "").strip()
    except Exception as e:
        soffice_ver = f"unavailable: {e}"
    return {
        "python": sys.version,
        "libreoffice": soffice_ver,
        "allowed_exts": sorted(list(ALLOWED_EXTS)),
    }


@app.post("/convert")
def convert_sync():
    f = request.files.get("file") or request.files.get("document")
    if not f:
        return jsonify({"error": "file field is required"}), 400

    name = f.filename or "input.docx"
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTS:
        return jsonify({"error": f"unsupported extension: {ext}"}), 415

    jid = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{jid}{ext}")
    out_name = os.path.splitext(os.path.basename(name))[0] + ".pdf"
    out_path = os.path.join(OUTPUTS_DIR, f"{jid}.pdf")
    final_path = os.path.join(OUTPUTS_DIR, out_name)

    f.save(in_path)
    try:
        perform_createpdf_libreoffice(in_path, out_path)
        if out_path != final_path:
            if os.path.exists(final_path):
                os.remove(final_path)
            os.replace(out_path, final_path)
    except Exception as e:
        app.logger.exception("LibreOffice conversion failed")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.remove(in_path)
        except Exception:
            pass

    return _send_download(final_path, out_name)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
