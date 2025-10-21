from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os, io, sys, logging, tempfile, shutil, subprocess, shlex
import importlib

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "expose_headers": ["Content-Disposition"]}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

ALLOWED_EXTS = {".doc", ".docx"}

def _truthy(v: str | None) -> bool:
    return str(v).lower() in {"1", "true", "yes", "on"} if v is not None else False

# Adobe v4 imports (모든 경로 폴백 포함)
ADOBE_AVAILABLE, ADOBE_SDK_VERSION, ADOBE_IMPORT_ERROR = False, None, None
try:
    try:
        from adobe.pdfservices.operation.pdfservices import PDFServices
    except Exception:
        from adobe.pdfservices.operation.pdf_services import PDFServices

    try:
        from adobe.pdfservices.operation.auth.oauth_service_account_credentials import OAuthServiceAccountCredentials
    except Exception:
        # 일부 배포판에서는 이 경로가 다를 수 있으나, 보통 위가 표준
        raise

    try:
        from adobe.pdfservices.operation.pdfjobs.jobs.create_pdf_job import CreatePDFJob
    except Exception:
        from adobe.pdfservices.operation.pdfjobs.jobs.create_pdf.create_pdf_job import CreatePDFJob

    try:
        from adobe.pdfservices.operation.pdfjobs.params.create_pdf import CreatePDFParams
    except Exception:
        from adobe.pdfservices.operation.pdfjobs.params.create_pdf.create_pdf_params import CreatePDFParams

    try:
        from adobe.pdfservices.operation.pdfjobs.result.create_pdf_result import CreatePDFResult
    except Exception:
        from adobe.pdfservices.operation.pdfjobs.result.create_pdf.create_pdf_result import CreatePDFResult

    ADOBE_AVAILABLE, ADOBE_SDK_VERSION = True, "4.x"
except Exception as e:
    ADOBE_AVAILABLE, ADOBE_SDK_VERSION = False, None
    ADOBE_IMPORT_ERROR = f"v4 import failed: {e}"
    app.logger.warning(ADOBE_IMPORT_ERROR)

# FileRef 동적 로더
def _load_file_ref():
    errors = []
    for mod_path in [
        "adobe.pdfservices.operation.pdfjobs.io.file_ref",
        "adobe.pdfservices.operation.io.file_ref",
    ]:
        try:
            mod = importlib.import_module(mod_path)
            return getattr(mod, "FileRef")
        except Exception as e:
            errors.append(f"{mod_path}: {e}")
    raise ImportError("Cannot import FileRef. Tried -> " + " | ".join(errors))


def ensure_adobe_creds_file() -> str:
    path = os.getenv("ADOBE_CREDENTIALS_FILE_PATH") or os.getenv("PDF_SERVICES_CREDENTIALS_FILE_PATH")
    js = os.getenv("ADOBE_CREDENTIALS_JSON") or os.getenv("PDF_SERVICES_CREDENTIALS_JSON")
    if path and os.path.exists(path):
        return path
    if js:
        fd, tmp = tempfile.mkstemp(prefix="adobe_creds_", suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write(js)
        return tmp
    raise RuntimeError("Missing ADOBE_CREDENTIALS_JSON or ADOBE_CREDENTIALS_FILE_PATH")


def perform_createpdf_adobe(in_path: str, out_pdf_path: str):
    if not ADOBE_AVAILABLE or ADOBE_SDK_VERSION != "4.x":
        raise RuntimeError("Adobe v4 SDK not available")

    creds_file = ensure_adobe_creds_file()
    credentials = OAuthServiceAccountCredentials.create_from_file(creds_file)
    pdf_services = PDFServices(credentials)

    FileRef = _load_file_ref()
    input_ref = FileRef.create_from_local_file(in_path)

    params = CreatePDFParams()
    job = CreatePDFJob(input_ref, params)

    location = pdf_services.submit(job)
    result = pdf_services.get_job_result(location, CreatePDFResult)

    tmp_dir = tempfile.mkdtemp(prefix="createpdf_")
    try:
        tmp_out = os.path.join(tmp_dir, os.path.basename(out_pdf_path))
        result.save_as(tmp_out)
        os.makedirs(os.path.dirname(out_pdf_path), exist_ok=True)
        if os.path.exists(out_pdf_path):
            os.remove(out_pdf_path)
        shutil.move(tmp_out, out_pdf_path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


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


def _send_download(path: str, download_name: str):
    with open(path, "rb") as f:
        data = f.read()
    resp = send_file(io.BytesIO(data), as_attachment=True, download_name=download_name, mimetype="application/pdf")
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(len(data))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Disposition"] = f"attachment; filename={download_name}"
    return resp


@app.get("/health")
def health():
    from importlib.metadata import version, PackageNotFoundError
    try:
        sdk_ver = version("pdfservices-sdk")
    except PackageNotFoundError:
        sdk_ver = None
    return {
        "python": sys.version,
        "pdfservices_sdk": sdk_ver,
        "adobe_available": ADOBE_AVAILABLE,
        "adobe_sdk_version": ADOBE_SDK_VERSION,
        "adobe_error": ADOBE_IMPORT_ERROR,
        "creds": {
            "json": bool(os.getenv("ADOBE_CREDENTIALS_JSON") or os.getenv("PDF_SERVICES_CREDENTIALS_JSON")),
            "file": bool(os.getenv("ADOBE_CREDENTIALS_FILE_PATH") or os.getenv("PDF_SERVICES_CREDENTIALS_FILE_PATH")),
            "disabled": os.getenv("ADOBE_DISABLED"),
        },
        "allowed_exts": sorted(list(ALLOWED_EXTS)),
    }


@app.get("/")
def index():
    return jsonify({
        "service": "docx-pdf",
        "status": "ok",
        "routes": {
            "GET /health": "service health and SDK status",
            "POST /convert": "multipart file ('file' or 'document') -> PDF",
        },
        "adobe_available": ADOBE_AVAILABLE,
        "adobe_sdk_version": ADOBE_SDK_VERSION,
    })


@app.post("/convert")
def convert_sync():
    f = request.files.get("file") or request.files.get("document")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    name = f.filename or "input"
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTS:
        return jsonify({"error": f"unsupported extension: {ext}"}), 415
    in_path = os.path.join(UPLOADS_DIR, f"upload{ext}")
    out_name = os.path.splitext(os.path.basename(name))[0] + ".pdf"
    out_path = os.path.join(OUTPUTS_DIR, out_name)
    f.save(in_path)

    engine = (request.form.get("engine") or request.args.get("engine") or "").lower()
    use_libre = _truthy(os.getenv("ADOBE_DISABLED")) or engine == "libreoffice" or not ADOBE_AVAILABLE
    try:
        if use_libre:
            perform_createpdf_libreoffice(in_path, out_path)
        else:
            perform_createpdf_adobe(in_path, out_path)
    except Exception as e:
        app.logger.warning(f"Primary conversion failed: {e}; falling back to LibreOffice.")
        perform_createpdf_libreoffice(in_path, out_path)
    finally:
        try:
            os.remove(in_path)
        except Exception:
            pass

    return _send_download(out_path, out_name)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
