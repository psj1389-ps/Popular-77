import os
import sys
import io
import json
import time
import requests
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import fitz  # PyMuPDF
from PIL import Image
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage

# 환경 변수 먼저 로드
load_dotenv()

# 전역 변수 초기화
ADOBE_AVAILABLE = False
ADOBE_SDK_VERSION = None
ADOBE_IMPORT_ERROR = None

import logging

try:
    # v4 imports - 정확한 모듈 경로 사용
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
    from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset

    ADOBE_AVAILABLE = True
    ADOBE_SDK_VERSION = "4.x"
except Exception as e:
    ADOBE_AVAILABLE = False
    ADOBE_IMPORT_ERROR = f"v4 import failed: {e}"
    logging.warning(ADOBE_IMPORT_ERROR)

# 자격증명(JSON 파일 확보)
import os, json, tempfile, base64

def ensure_adobe_creds_file() -> str:
    # 1) JSON/FILE 직접 제공
    path = os.getenv("ADOBE_CREDENTIALS_FILE_PATH") or os.getenv("PDF_SERVICES_CREDENTIALS_FILE_PATH")
    js = os.getenv("ADOBE_CREDENTIALS_JSON") or os.getenv("PDF_SERVICES_CREDENTIALS_JSON")
    if path and os.path.exists(path):
        return path
    if js:
        fd, tmp = tempfile.mkstemp(prefix="adobe_creds_", suffix=".json")
        with os.fdopen(fd, "w") as f: f.write(js)
        return tmp

    # 2) ADOBE_*로 JSON 생성 (파일/평문/B64 키 모두 지원)
    cid = os.getenv("ADOBE_CLIENT_ID")
    csec = os.getenv("ADOBE_CLIENT_SECRET")
    org = os.getenv("ADOBE_ORGANIZATION_ID")
    acct = os.getenv("ADOBE_ACCOUNT_ID") or os.getenv("ADOBE_TECHNICAL_ACCOUNT_EMAIL")
    key_path = os.getenv("ADOBE_PRIVATE_KEY_PATH")
    key_text = os.getenv("ADOBE_PRIVATE_KEY")
    key_b64 = os.getenv("ADOBE_PRIVATE_KEY_B64")

    if not (cid and csec and org and acct and (key_path or key_text or key_b64)):
        missing = [k for k, v in {
            "ADOBE_CLIENT_ID": cid,
            "ADOBE_CLIENT_SECRET": csec,
            "ADOBE_ORGANIZATION_ID": org,
            "ADOBE_ACCOUNT_ID/ADOBE_TECHNICAL_ACCOUNT_EMAIL": acct,
            "ADOBE_PRIVATE_KEY_(PATH|/|_B64)": key_path or key_text or key_b64,
        }.items() if not v]
        raise RuntimeError(f"Missing Adobe env(s): {', '.join(missing)}")

    if key_text:
        private_key = key_text
    elif key_b64:
        private_key = base64.b64decode(key_b64).decode("utf-8")
    else:
        if not os.path.exists(key_path):
            raise RuntimeError(f"Private key not found: {key_path}")
        with open(key_path, "r") as f:
            private_key = f.read()

    payload = {
        "client_credentials": {"client_id": cid, "client_secret": csec},
        "service_account_credentials": {
            "organization_id": org,
            "account_id": acct,
            "private_key": private_key
        }
    }
    fd, tmp = tempfile.mkstemp(prefix="adobe_creds_", suffix=".json")
    with os.fdopen(fd, "w") as f: json.dump(payload, f)
    logging.info("Built Adobe credentials JSON from ADOBE_* envs at %s", tmp)
    return tmp

# 추가 imports
from werkzeug.exceptions import HTTPException
import urllib.parse, tempfile, shutil, errno, logging
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from typing import Optional

app = Flask(__name__)
CORS(app)

# Adobe 자격 증명 (개선된 디버그 출력)
ENV_CLIENT_ID = os.getenv("ADOBE_CLIENT_ID") or os.getenv("PDF_SERVICES_CLIENT_ID") or ""
ENV_CLIENT_SECRET = os.getenv("ADOBE_CLIENT_SECRET") or os.getenv("PDF_SERVICES_CLIENT_SECRET") or ""
ENV_CREDS_JSON = os.getenv("ADOBE_CREDENTIALS_JSON") or os.getenv("PDF_SERVICES_CREDENTIALS_JSON") or ""
ENV_CREDS_FILE_PATH = os.getenv("ADOBE_CREDENTIALS_FILE_PATH") or os.getenv("PDF_SERVICES_CREDENTIALS_FILE_PATH") or ""

print("Environment Variables Check:")
print(f"ADOBE/PDF_SERVICES CLIENT_ID exists: {bool(ENV_CLIENT_ID)}")
print(f"ADOBE/PDF_SERVICES CLIENT_SECRET exists: {bool(ENV_CLIENT_SECRET)}")
print(f"ADOBE_CREDENTIALS_JSON exists: {bool(ENV_CREDS_JSON)}")
print(f"ADOBE_CREDENTIALS_FILE_PATH exists: {bool(ENV_CREDS_FILE_PATH)}")

print("=== Final Status ===")
print(f"Adobe SDK Available: {ADOBE_AVAILABLE}")
print(f"Adobe SDK Version: {ADOBE_SDK_VERSION if ADOBE_AVAILABLE else 'None'}")
print(f"Client ID configured: {bool(ENV_CLIENT_ID)}")
print(f"Client Secret configured: {bool(ENV_CLIENT_SECRET)}")

logging.basicConfig(level=logging.INFO)

# 디버그 함수: v4 모듈 네임스페이스 확인
def debug_adobe_modules():
    import importlib, pkgutil, logging
    for base in [
        "adobe.pdfservices.operation.pdfjobs.params",
        "adobe.pdfservices.operation.pdfjobs.jobs",
        "adobe.pdfservices.operation.pdfjobs.io",
    ]:
        try:
            m = importlib.import_module(base)
            subs = [name for _, name, _ in pkgutil.iter_modules(m.__path__)]
            logging.info("%s -> %s", base, subs)
        except Exception as e:
            logging.warning("Cannot import %s: %s", base, e)

if ADOBE_AVAILABLE and ADOBE_SDK_VERSION == "4.x":
    debug_adobe_modules()

# 요청 로깅 추가
@app.before_request
def _trace():
    app.logger.info(f">>> {request.method} {request.path}")
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:5173",
    "https://77-tools.xyz",
    "https://www.77-tools.xyz",
    "https://popular-77.vercel.app"
], "expose_headers": ["Content-Disposition"], "methods": ["GET","POST","OPTIONS"], "allow_headers": ["Content-Type"]}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}
current_job_id: Optional[str] = None

def safe_base_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename or "output"))[0]
    return base.replace("/", "").replace("\\", "").strip() or "output"

def set_progress(job_id, p, msg=None):
    info = JOBS.setdefault(job_id, {})
    info["progress"] = int(p)
    if msg is not None:
        info["message"] = msg

def send_download_memory(path: str, download_name: str, ctype: str):
    if not path or not os.path.exists(path):
        return jsonify({"error":"output file missing"}), 500
    with open(path, "rb") as f:
        data = f.read()
    resp = send_file(io.BytesIO(data), mimetype=ctype, as_attachment=True, download_name=download_name, conditional=False)
    resp.direct_passthrough = False
    resp.headers["Content-Length"] = str(len(data))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{urllib.parse.quote(download_name)}"
    return resp

def _env(key: str, alt: list[str] = []):
    import os
    for k in [key, *alt]:
        v = os.environ.get(k)
        if v: return v
    raise KeyError(f"Missing env: {key}")

def adobe_context():
    if not ADOBE_AVAILABLE:
        raise RuntimeError("Adobe SDK is not installed or configured.")
    
    # 환경변수에서 자격증명 읽기
    client_id = os.environ["ADOBE_CLIENT_ID"]
    client_secret = os.environ["ADOBE_CLIENT_SECRET"]
    
    # v4 SDK 방식: ServicePrincipalCredentials 사용
    creds = ServicePrincipalCredentials.builder() \
        .with_client_id(client_id) \
        .with_client_secret(client_secret) \
        .build()
    return PDFServices.builder().with_credentials(creds).build()

def _export_via_adobe(in_pdf_path: str, target: str, out_path: str):
    pdf_services = adobe_context()
    
    # v4 방식: JobFileRef 생성 및 ExportPDFJob 실행
    input_asset = pdf_services.upload(input_stream=open(in_pdf_path, 'rb'), mime_type="application/pdf")
    
    # ExportPDFParams 설정
    export_pdf_params = ExportPDFParams(target_format=ExportPDFTargetFormat[target])
    
    # ExportPDFJob 생성 및 실행
    export_pdf_job = ExportPDFJob(input_asset=input_asset, export_pdf_params=export_pdf_params)
    location = pdf_services.submit(export_pdf_job)
    pdf_services_response = pdf_services.get_job_result(location, ExportPDFJob)
    
    # 결과 저장
    result_asset = pdf_services_response.get_result().get_asset()
    stream_asset = pdf_services.get_content(result_asset)
    
    if os.path.exists(out_path):
        os.remove(out_path)
    
    with open(out_path, "wb") as file:
        file.write(stream_asset.get_input_stream().read())

# v3 변환(XLSX)
def _truthy(v: str | None) -> bool:
    return str(v).lower() in {"1", "true", "yes", "on"} if v is not None else False

def perform_xlsx_conversion_adobe(in_pdf_path: str, out_xlsx_path: str):
    if _truthy(os.getenv("ADOBE_DISABLED")):
        raise RuntimeError("Adobe is disabled via ADOBE_DISABLED")
    if not ADOBE_AVAILABLE or ADOBE_SDK_VERSION != "4.x":
        raise RuntimeError("Adobe v4 SDK not available")

    # v4 방식으로 변환 실행
    _export_via_adobe(in_pdf_path, "XLSX", out_xlsx_path)

# 폴백 함수(scale 인자 수용)
def perform_xlsx_conversion_fallback(in_pdf_path: str, out_xlsx_path: str, scale: float = 1.0):
    import fitz, openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Extracted"
    with fitz.open(in_pdf_path) as doc:
        row = 1
        for i, page in enumerate(doc, start=1):
            ws.cell(row=row, column=1, value=f"=== Page {i} ==="); row += 1
            for line in page.get_text("text").splitlines():
                ws.cell(row=row, column=1, value=line); row += 1
            row += 1
    wb.save(out_xlsx_path)

@app.route('/', methods=['GET'])
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF to XLSX Converter</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; border-radius: 10px; padding: 30px; text-align: center; }
            .upload-area.active { border-color: #4CAF50; background: #f0f8ff; }
            button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #45a049; }
            .message { margin-top: 20px; padding: 10px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .info { background: #d1ecf1; color: #0c5460; }
        </style>
    </head>
    <body>
        <h1>PDF to XLSX Converter</h1>
        <div class="upload-area" id="uploadArea">
            <p>Choose a PDF file or drag & drop here</p>
            <input type="file" id="fileInput" accept=".pdf" style="display: none;">
            <button onclick="document.getElementById('fileInput').click()">Select PDF</button>
        </div>
        <div id="message"></div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const messageDiv = document.getElementById('message');
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('active');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('active');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('active');
                const files = e.dataTransfer.files;
                if (files.length > 0) handleFile(files[0]);
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) handleFile(e.target.files[0]);
            });
            
            function showMessage(text, type) {
                messageDiv.className = 'message ' + type;
                messageDiv.textContent = text;
            }
            
            async function handleFile(file) {
                if (!file.name.toLowerCase().endsWith('.pdf')) {
                    showMessage('Please select a PDF file', 'error');
                    return;
                }
                
                showMessage('Converting... Please wait...', 'info');
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/convert', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = file.name.replace('.pdf', '.xlsx');
                        a.click();
                        window.URL.revokeObjectURL(url);
                        showMessage('Conversion successful! Download started.', 'success');
                    } else {
                        const error = await response.text();
                        showMessage('Conversion failed: ' + error, 'error');
                    }
                } catch (error) {
                    showMessage('Error: ' + error.message, 'error');
                }
            }
        </script>
    </body>
    </html>
    '''

# health 응답(무엇이 보이는지 명확히)
@app.get("/health")
def health():
    import sys
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
            "cid": bool(os.getenv("ADOBE_CLIENT_ID")),
            "csecret": bool(os.getenv("ADOBE_CLIENT_SECRET")),
            "org": bool(os.getenv("ADOBE_ORGANIZATION_ID")),
            "acct": bool(os.getenv("ADOBE_ACCOUNT_ID") or os.getenv("ADOBE_TECHNICAL_ACCOUNT_EMAIL")),
            "key_file_exists": os.path.exists(os.getenv("ADOBE_PRIVATE_KEY_PATH", "")),
            "key_text": bool(os.getenv("ADOBE_PRIVATE_KEY")),
            "key_b64": bool(os.getenv("ADOBE_PRIVATE_KEY_B64")),
            "disabled": os.getenv("ADOBE_DISABLED"),
        },
    }

@app.post("/convert-async")
def convert_async():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f: 
        return jsonify({"error":"file field is required"}), 400
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

    scale = clamp_num(request.form.get("scale","1.0"), 0.2, 2.0, 1.0, float)

    JOBS[job_id] = {"status":"pending","progress":1,"message":"대기 중"}

    def run_job():
        global current_job_id
        current_job_id = job_id
        try:
            set_progress(job_id, 10, "변환 준비 중")
            final_name = f"{base_name}.xlsx"
            final_path = os.path.join(OUTPUTS_DIR, final_name)
            try:
                perform_xlsx_conversion_adobe(in_path, final_path)
            except Exception as e:
                app.logger.exception("Adobe export failed; fallback to image-based.")
                perform_xlsx_conversion_fallback(in_path, final_path)
            out_path, name, ctype = final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            JOBS[job_id] = {"status":"done","path":out_path,"name":name,"ctype":ctype,
                           "progress":100,"message":"완료"}
        except Exception as e:
            app.logger.exception("convert error")
            JOBS[job_id] = {"status":"error","error":str(e),"progress":0,"message":"오류"}
        finally:
            current_job_id = None
            try: 
                os.remove(in_path)
            except: 
                pass

    executor.submit(run_job)
    return jsonify({"job_id": job_id}), 202

@app.get("/job/<job_id>")
def job_status(job_id):
    info = JOBS.get(job_id)
    if not info: 
        return jsonify({"error":"job not found"}), 404
    info.setdefault("progress", 0)
    info.setdefault("message","")
    return jsonify(info), 200

@app.get("/download/<job_id>")
def job_download(job_id):
    info = JOBS.get(job_id)
    if not info: 
        return jsonify({"error":"job not found"}), 404
    if info.get("status") != "done": 
        return jsonify({"error":"not ready"}), 409
    return send_download_memory(info["path"], info["name"], info["ctype"])

# API aliases: /api/pdf-xls/*
@app.post("/convert")
def convert_sync():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error":"file field is required"}), 400

    base_name = safe_base_name(f.filename)
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)

    quality = request.form.get("quality", "low")  # 수신만, 변환에는 사용하지 않음
    def clamp_num(v, lo, hi, default, T=float):
        try: 
            x = T(v)
        except: 
            return default
        return max(lo, min(hi, x))
    scale = clamp_num(request.form.get("scale","1.0"), 0.2, 2.0, 1.0, float)

    # 라우팅/실행 흐름은 기존처럼 Adobe → 실패시 폴백
    def convert_pdf_to_xlsx(input_pdf_path, output_xlsx_path, scale: float = 1.0):
        import logging
        if ADOBE_AVAILABLE and ADOBE_SDK_VERSION == "4.x":
            try:
                perform_xlsx_conversion_adobe(input_pdf_path, output_xlsx_path)
                return
            except Exception as e:
                logging.warning("Adobe v4 conversion failed; fallback. err=%s", e, exc_info=True)
        # 최종 폴백
        perform_xlsx_conversion_fallback(input_pdf_path, output_xlsx_path, scale=scale)

    try:
        # 1. Adobe API를 먼저 시도합니다.
        app.logger.info("Attempting conversion with Adobe API...")
        final_name = f"{base_name}.xlsx"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        
        convert_pdf_to_xlsx(in_path, final_path, scale=scale)
        
        out_path, name, ctype = final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception as e:
        # 2. 어떤 이유로든 실패하면 (자격증명 오류, Adobe 서버 문제 등)
        app.logger.exception("Adobe export failed; falling back to image-based conversion.")
        # 3. 기존의 이미지 방식으로 변환을 시도합니다.
        perform_xlsx_conversion_fallback(in_path, final_path, scale=scale)
        out_path, name, ctype = final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    finally:
        try: 
            os.remove(in_path)
        except: 
            pass
    
    return send_download_memory(out_path, name, ctype)

# /api aliases (frontend uses /api paths only)
@app.route("/api/pdf-xls/health", methods=["GET", "HEAD"])
def _xls_a_health(): return health()

@app.route("/api/pdf-xls/convert", methods=["POST", "OPTIONS"])
def _xls_a_convert_sync(): return convert_sync()

@app.route("/api/pdf-xls/convert-async", methods=["POST", "OPTIONS"])
def _xls_a_convert_async(): return convert_async()

@app.route("/api/pdf-xls/job/<job_id>", methods=["GET", "HEAD"])
def _xls_a_job(job_id): return job_status(job_id)

@app.route("/api/pdf-xls/download/<job_id>", methods=["GET", "HEAD"])
def _xls_a_download(job_id): return job_download(job_id)

# Protection for wrong methods
@app.route("/api/pdf-xls/convert-async", methods=["GET", "HEAD"])
def _xls_a_convert_async_wrong_method():
    return jsonify({"error": "use POST for /convert-async"}), 405

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