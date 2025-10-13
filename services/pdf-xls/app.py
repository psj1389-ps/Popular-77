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

# Adobe SDK import 시도 (더 세밀한 에러 처리)
ADOBE_AVAILABLE = False
adobe_error_msg = "Not attempted"

try:
    # 단계별 import 시도
    import adobe
    import adobe.pdfservices
    import adobe.pdfservices.operation
    
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_job import PDFServicesJob
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.pdfops.export_pdf_operation import ExportPDFOperation
    from adobe.pdfservices.operation.pdfops.options.exportpdf.export_pdf_target_format import ExportPDFTargetFormat
    from adobe.pdfservices.operation.pdfops.options.exportpdf.export_pdf_params import ExportPDFParams
    
    ADOBE_AVAILABLE = True
    adobe_error_msg = "Successfully loaded"
    print("SUCCESS: Adobe PDF Services SDK loaded successfully")
    
except ImportError as e:
    adobe_error_msg = str(e)
    print(f"WARNING: Adobe PDF Services SDK import failed: {e}")
    print("INFO: Using fallback conversion method")
except Exception as e:
    adobe_error_msg = f"Unexpected error: {str(e)}"
    print(f"ERROR: Unexpected error loading Adobe SDK: {e}")

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

# Adobe 자격 증명
CLIENT_ID = os.environ.get('PDF_SERVICES_CLIENT_ID')
CLIENT_SECRET = os.environ.get('PDF_SERVICES_CLIENT_SECRET')

# 디버그 정보 출력
print(f"Adobe SDK Available: {ADOBE_AVAILABLE}")
print(f"Adobe Error Message: {adobe_error_msg}")
print(f"Client ID configured: {bool(CLIENT_ID)}")
print(f"Client Secret configured: {bool(CLIENT_SECRET)}")

logging.basicConfig(level=logging.INFO)

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

def perform_xlsx_conversion_adobe(in_path: str, base_name: str):
    final_name = f"{base_name}.xlsx"
    final_path = os.path.join(OUTPUTS_DIR, final_name)
    _export_via_adobe(in_path, "XLSX", final_path)
    return final_path, final_name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

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

@app.route("/")
def index():
    return render_template("index.html")

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
                out_path, name, ctype = perform_xlsx_conversion_adobe(in_path, base_name)
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

    try:
        # 1. Adobe 변환을 먼저 시도합니다.
        app.logger.info("Attempting conversion with Adobe API...")
        out_path, name, ctype = perform_xlsx_conversion_adobe(in_path, base_name)
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