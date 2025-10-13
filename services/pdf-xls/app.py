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

# 자격 증명 파일 확보 유틸 (ADOBE_CREDENTIALS_JSON/ADOBE_CREDENTIALS_FILE_PATH 기준)
import tempfile
import logging

def ensure_adobe_creds_file() -> str:
    creds_path = os.getenv("ADOBE_CREDENTIALS_FILE_PATH")
    creds_json = os.getenv("ADOBE_CREDENTIALS_JSON")
    logging.info("Adobe creds -> JSON:%s FILE:%s", 
                 bool(creds_json), bool(creds_path))
    if creds_path and os.path.exists(creds_path):
        return creds_path
    if creds_json:
        fd, path = tempfile.mkstemp(prefix="adobe_creds_", suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write(creds_json)
        return path
    raise RuntimeError("Missing ADOBE_CREDENTIALS_JSON or ADOBE_CREDENTIALS_FILE_PATH")

# Adobe 자격 증명 (개선된 디버그 출력)
CLIENT_ID = os.environ.get('PDF_SERVICES_CLIENT_ID')
CLIENT_SECRET = os.environ.get('PDF_SERVICES_CLIENT_SECRET')
ADOBE_CREDENTIALS_JSON = os.environ.get('ADOBE_CREDENTIALS_JSON')
ADOBE_CREDENTIALS_FILE_PATH = os.environ.get('ADOBE_CREDENTIALS_FILE_PATH')

print(f"Environment Variables Check:")
print(f"PDF_SERVICES_CLIENT_ID exists: {bool(CLIENT_ID)}")
print(f"PDF_SERVICES_CLIENT_SECRET exists: {bool(CLIENT_SECRET)}")
print(f"ADOBE_CREDENTIALS_JSON exists: {bool(ADOBE_CREDENTIALS_JSON)}")
print(f"ADOBE_CREDENTIALS_FILE_PATH exists: {bool(ADOBE_CREDENTIALS_FILE_PATH)}")
if CLIENT_ID:
    print(f"CLIENT_ID length: {len(CLIENT_ID)}")
if CLIENT_SECRET:
    print(f"CLIENT_SECRET length: {len(CLIENT_SECRET)}")

# Adobe SDK import 시도 (v4.2.0 snake_case 전용)
try:
    # v4.2.0 전용 import (snake_case 주의)
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf import ExportPDFParams, ExportPDFTargetFormat
    from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
    from adobe.pdfservices.operation.pdfjobs.io.file_ref import FileRef as JobFileRef
    from adobe.pdfservices.operation.pdfservices import PDFServices
    # 일부 배포판은 OAuthServiceAccountCredentials가 제공됩니다
    try:
        from adobe.pdfservices.operation.auth.oauth_service_account_credentials import OAuthServiceAccountCredentials as V4Creds
        V4_CREDS_KIND = "oauth_service_account"
    except Exception:
        V4Creds = None
        V4_CREDS_KIND = None
    ADOBE_SDK_VERSION = "4.x"
    ADOBE_AVAILABLE = True
except Exception as e_v4:
    import logging
    logging.warning("Adobe v4 import failed: %s", e_v4)
    # 선택지: v3로 폴백 임포트 (requirements를 3.4.2로 내릴 때만 유효)
    try:
        from adobe.pdfservices.operation.auth.credentials import Credentials as V3Creds
        from adobe.pdfservices.operation.io.file_ref import FileRef as V3FileRef
        from adobe.pdfservices.operation.pdfops.export_pdf_operation import ExportPDFOperation
        from adobe.pdfservices.operation.pdfops.options.export_pdf.export_pdf_target_format import ExportPDFTargetFormat as V3Target
        from adobe.pdfservices.operation.execution_context import ExecutionContext
        ADOBE_SDK_VERSION = "3.x"
        ADOBE_AVAILABLE = True
    except Exception as e_v3:
        ADOBE_SDK_VERSION = None
        ADOBE_AVAILABLE = False
        logging.warning("Adobe v3 import also failed: %s", e_v3)

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

# 디버그 정보 출력
print(f"=== Final Status ===")
print(f"Adobe SDK Available: {ADOBE_AVAILABLE}")
print(f"Adobe SDK Version: {ADOBE_SDK_VERSION if ADOBE_AVAILABLE else 'None'}")
print(f"Client ID configured: {bool(CLIENT_ID)}")
print(f"Client Secret configured: {bool(CLIENT_SECRET)}")

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

# 앱 시작 시 디버그 모듈 확인
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
    
    # 최신 SDK 방식: client_id와 client_secret만 사용
    creds = ServicePrincipalCredentials(
        client_id=client_id,
        client_secret=client_secret,
    )
    return ExecutionContext.create(creds)

def _export_via_adobe(in_pdf_path: str, target: str, out_path: str):
    ctx = adobe_context()
    op = ExportPDFOperation.create_new(ExportPDFTargetFormat[target])  # "XLSX"
    op.set_input(FileRef.create_from_local_file(in_pdf_path))
    result = op.execute(ctx)
    if os.path.exists(out_path):
        os.remove(out_path)
    result.save_as(out_path)

def perform_xlsx_conversion_adobe(input_pdf_path: str, output_xlsx_path: str):
    if not ADOBE_AVAILABLE or ADOBE_SDK_VERSION != "4.x":
        raise RuntimeError("Adobe v4 SDK not available")

    creds_file = ensure_adobe_creds_file()

    # 자격 증명 생성: SDK 배포판에 따라 이름이 다를 수 있어 분기 처리
    if V4Creds:
        credentials = V4Creds.create_from_file(creds_file)
    else:
        # 일부 환경에서는 기존 Credentials 빌더가 그대로 동작
        from adobe.pdfservices.operation.auth.credentials import Credentials
        credentials = Credentials.service_account_credentials_builder() \
            .from_file(creds_file).build()

    pdf_services = PDFServices(credentials)

    # 입력/파라미터/잡 생성
    input_ref = JobFileRef.create_from_local_file(input_pdf_path)
    params = ExportPDFParams(ExportPDFTargetFormat.XLSX)
    job = ExportPDFJob(input_ref, params)

    # 잡 제출 및 결과 수신
    location = pdf_services.submit(job)          # 제출
    result = pdf_services.get_job_result(location)  # 완료까지 내부적으로 폴링
    result.save_as(output_xlsx_path)

def perform_xlsx_conversion_fallback(in_path: str, base_name: str, scale: float = 1.0):
    """
    PDF → XLSX (시트당 이미지 1장, A1에 배치)
    """
    with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
        doc = fitz.open(in_path)
        mat = fitz.Matrix(scale, scale)
        wb = Workbook()
        # openpyxl 기본 시트를 첫 페이지로 사용, 나머지는 추가
        first_sheet = True

        for i in range(doc.page_count):
            set_progress(current_job_id, 10 + int(80 * (i + 1) / doc.page_count), f"페이지 {i+1}/{doc.page_count} 처리 중")
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_path = os.path.join(tmp, f"{base_name}_{i+1:02d}.png")
            pix.save(img_path)

            if first_sheet:
                ws = wb.active
                ws.title = f"Page_{i+1:02d}"
                first_sheet = False
            else:
                ws = wb.create_sheet(title=f"Page_{i+1:02d}")

            xlimg = XLImage(img_path)
            ws.add_image(xlimg, "A1")

        final_name = f"{base_name}.xlsx"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        if os.path.exists(final_path): 
            os.remove(final_path)
        wb.save(final_path)
        return final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

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

@app.route('/health', methods=['GET'])
def health_check():
    health_info = {
        'status': 'OK',
        'adobe_sdk': ADOBE_AVAILABLE,
        'adobe_error': adobe_error_msg,
        'credentials_configured': bool(CLIENT_ID and CLIENT_SECRET)
    }
    return jsonify(health_info), 200

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
            try:
                set_progress(job_id, 30, "Adobe로 변환 중")
                # PDF 파일을 읽어서 버퍼로 변환
                with open(in_path, 'rb') as f:
                    pdf_buffer = f.read()
                xlsx_data = perform_xlsx_conversion_adobe(pdf_buffer)
                
                # 결과를 파일로 저장
                final_name = f"{base_name}.xlsx"
                final_path = os.path.join(OUTPUTS_DIR, final_name)
                with open(final_path, 'wb') as f:
                    f.write(xlsx_data)
                
                out_path, name, ctype = final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            except Exception as e:
                app.logger.exception("Adobe export failed; fallback to image-based.")
                set_progress(job_id, 50, "이미지 기반 폴백 변환 중")
                out_path, name, ctype = perform_xlsx_conversion_fallback(in_path, base_name, scale=scale)  # 기존 이미지 방식
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
    def convert_pdf_to_xlsx(input_pdf_path, output_xlsx_path):
        import logging
        if ADOBE_AVAILABLE and ADOBE_SDK_VERSION == "4.x":
            try:
                return perform_xlsx_conversion_adobe(input_pdf_path, output_xlsx_path)
            except Exception as e:
                logging.warning("Adobe v4 conversion failed; fallback. err=%s", e, exc_info=True)
        # v3 설치 시 (requirements를 3.4.2로 내렸다면) v3 경로 시도
        if ADOBE_AVAILABLE and ADOBE_SDK_VERSION == "3.x":
            try:
                return perform_xlsx_conversion_adobe_v3(input_pdf_path, output_xlsx_path) # 기존 v3 함수가 있다면
            except Exception as e:
                logging.warning("Adobe v3 conversion failed; fallback. err=%s", e, exc_info=True)
        # 최종 폴백
        return perform_xlsx_conversion_fallback(input_pdf_path, base_name, scale=scale)

    try:
        # 1. Adobe API를 먼저 시도합니다.
        app.logger.info("Attempting conversion with Adobe API...")
        final_name = f"{base_name}.xlsx"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        
        convert_pdf_to_xlsx(in_path, final_path)
        
        out_path, name, ctype = final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except Exception as e:
        # 2. 어떤 이유로든 실패하면 (자격증명 오류, Adobe 서버 문제 등)
        app.logger.exception("Adobe export failed; falling back to image-based conversion.")
        # 3. 기존의 이미지 방식으로 변환을 시도합니다.
        out_path, name, ctype = perform_xlsx_conversion_fallback(in_path, base_name, scale=scale)
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