from flask import Flask, request, jsonify, send_file, render_template, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import os, io, sys, logging, tempfile, shutil, subprocess, shlex
import shutil as _sh
from uuid import uuid4
from urllib.parse import quote
import unicodedata
from threading import Semaphore

# Adobe API 비활성화 (LibreOffice 전용)
ADOBE_SDK_AVAILABLE = False

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__, template_folder="templates", static_folder="static")

# 프로덕션 설정
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", "60")) * 1024 * 1024

# 동시성 제어 세마포어
SEMA = Semaphore(int(os.getenv("MAX_CONCURRENCY", "1")))

CORS(app, resources={r"/*": {"origins": ["*", "https://77-tools.xyz", "http://localhost:*", "http://127.0.0.1:*"]}}, expose_headers=["Content-Disposition"], supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

ALLOWED_EXTS = {".doc", ".docx", ".pdf"}

def ascii_fallback(name: str) -> str:
    """유니코드 파일명을 ASCII로 변환하여 안전한 파일명 생성"""
    a = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii") or "converted.pdf"
    # 따옴표/세미콜론 등 위험 문자 제거
    return "".join(c for c in a if c.isalnum() or c in ".- ") or "converted.pdf"

def _set_pdf_disposition(resp, pdf_name: str):
    """RFC 5987 + ASCII fallback으로 Content-Disposition 헤더 설정"""
    ascii_name = ascii_fallback(pdf_name)
    resp.headers["Content-Disposition"] = (
        f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(pdf_name)}'
    )
    resp.headers["Cache-Control"] = "no-store"
    return resp

def _is_pdf(path: str) -> bool:
    """PDF 파일 시그니처 검증"""
    try:
        with open(path, 'rb') as f:
            return f.read(4) == b'%PDF'
    except:
        return False

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
    
    # RFC 5987 표준에 따른 한글/유니코드 파일명 인코딩
    try:
        # ASCII 파일명인지 확인
        download_name.encode('ascii')
        # ASCII인 경우 기본 형식 사용
        resp.headers["Content-Disposition"] = f'attachment; filename="{download_name}"'
    except UnicodeEncodeError:
        # 유니코드 파일명인 경우 RFC 5987 형식 사용
        encoded_filename = quote(download_name, safe='')
        resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
    
    return resp


def _find_soffice():
    """Find LibreOffice soffice executable"""
    # Check environment variable first
    if 'SOFFICE_BIN' in os.environ:
        soffice_path = os.environ['SOFFICE_BIN']
        if os.path.isfile(soffice_path) and os.access(soffice_path, os.X_OK):
            app.logger.info(f"Found soffice from SOFFICE_BIN: {soffice_path}")
            return soffice_path
        else:
            app.logger.warning(f"SOFFICE_BIN path not executable: {soffice_path}")
    
    # Common LibreOffice installation paths (including Linux paths for Render)
    possible_paths = [
        # Linux paths (for Render deployment)
        '/usr/bin/soffice',
        '/usr/bin/libreoffice',
        '/opt/libreoffice/program/soffice',
        '/snap/bin/libreoffice',
        # Windows paths (for local development)
        'C:\\Program Files\\LibreOffice\\program\\soffice.exe',
        'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe',
        'C:\\Program Files\\LibreOffice\\program\\soffice.COM',
        'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.COM',
        # macOS paths
        '/Applications/LibreOffice.app/Contents/MacOS/soffice'
    ]
    
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            app.logger.info(f"Found soffice at predefined path: {path}")
            return path
    
    # Try to find in PATH
    try:
        # Try different command names
        for cmd in ['soffice', 'libreoffice', 'soffice.bin']:
            result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path and os.path.isfile(path) and os.access(path, os.X_OK):
                    app.logger.info(f"Found {cmd} in PATH: {path}")
                    return path
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
        app.logger.warning(f"Error searching PATH: {e}")
    
    # Windows-specific PATH search
    if os.name == 'nt':
        try:
            result = subprocess.run(['where', 'soffice'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]  # Take first result
                if path and os.path.isfile(path) and os.access(path, os.X_OK):
                    app.logger.info(f"Found soffice in PATH: {path}")
                    return path
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            app.logger.warning(f"Error using 'where' command: {e}")
    
    app.logger.error("LibreOffice soffice executable not found")
    raise RuntimeError("LibreOffice is not installed or not found in PATH. Please install LibreOffice.")

def perform_createpdf_libreoffice(input_path, output_dir, timeout=120):
    """Convert document to PDF using LibreOffice with enhanced error handling"""
    try:
        soffice_path = _find_soffice()
        app.logger.info(f"Using LibreOffice at: {soffice_path}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Build command with proper escaping
        cmd = [
            soffice_path,
            '--headless',
            '--nologo',
            '--nofirststartwizard',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_path
        ]
        
        app.logger.info(f"Running LibreOffice command: {' '.join(repr(arg) for arg in cmd)}")
        
        # Set environment variables for better compatibility
        env = os.environ.copy()
        env['HOME'] = '/tmp'  # Set HOME for headless operation
        env['TMPDIR'] = '/tmp'
        
        # Run LibreOffice conversion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=output_dir  # Set working directory to output directory
        )
        
        app.logger.info(f"LibreOffice stdout: {result.stdout}")
        if result.stderr:
            app.logger.warning(f"LibreOffice stderr: {result.stderr}")
        
        if result.returncode != 0:
            app.logger.error(f"LibreOffice failed with return code {result.returncode}")
            app.logger.error(f"Command: {' '.join(cmd)}")
            app.logger.error(f"Stdout: {result.stdout}")
            app.logger.error(f"Stderr: {result.stderr}")
            return False
        
        # Check if output file was created
        input_filename = os.path.basename(input_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        expected_output = os.path.join(output_dir, f"{name_without_ext}.pdf")
        
        if os.path.exists(expected_output):
            file_size = os.path.getsize(expected_output)
            app.logger.info(f"LibreOffice conversion successful - output file created: {expected_output} (size: {file_size} bytes)")
            return expected_output
        else:
            app.logger.error(f"Expected output file not found: {expected_output}")
            # List files in output directory for debugging
            try:
                files_in_output = os.listdir(output_dir)
                app.logger.info(f"Files in output directory: {files_in_output}")
            except Exception as e:
                app.logger.error(f"Could not list output directory: {e}")
            return False
            
    except subprocess.TimeoutExpired:
        app.logger.error(f"LibreOffice conversion timed out after {timeout} seconds")
        return False
    except Exception as e:
        app.logger.error(f"LibreOffice conversion failed with exception: {str(e)}")
        app.logger.exception("Full exception details:")
        return False


@app.get("/")
def index():
    # 이 서비스 전용 텍스트/수치(템플릿에서 사용)
    page = {
        "title": "DOCX to PDF Converter",
        "subtitle": "Word 문서를 PDF로 안정적으로 변환",
        "accept": ".doc,.docx",
        "max_mb": os.getenv("MAX_CONTENT_LENGTH_MB", "100"),
        "service": "docx-pdf"
    }
    resp = make_response(render_template("index.html", page=page))
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.get("/health")
def health():
    # LibreOffice 상태 확인
    try:
        import shutil as _sh, subprocess as sp
        bin_path = _find_soffice()
        if bin_path:
            v_out = sp.run([bin_path, "--version"], capture_output=True, text=True, check=False)
            lo_ver = (v_out.stdout or v_out.stderr or "").strip()
        else:
            lo_ver = "unavailable: soffice not found"
    except Exception as e:
        lo_ver = f"unavailable: {e}"
    
    return {
        "service": "docx-pdf",
        "engine": "libreoffice",
        "soffice_path": _find_soffice(),
        "pdfservices_sdk": None,  # Adobe 완전 제거 확인
        "python": sys.version,
        "libreoffice": lo_ver,
        "allowed_exts": sorted(list(ALLOWED_EXTS))
    }


@app.post("/upload")
@app.post("/convert")
def convert_sync():
    # 세마포어를 이용한 동시성 제어
    if not SEMA.acquire(timeout=float(os.getenv("QUEUE_TIMEOUT", "0"))):
        return jsonify({"error": "busy"}), 503
    
    try:
        f = request.files.get("file") or request.files.get("document")
        if not f:
            return jsonify({"error": "file field is required"}), 400

        in_name = f.filename or "input.docx"  # 서비스별 기본값
        base, ext = os.path.splitext(os.path.basename(in_name))
        ext = ext.lower()
        if ext not in ALLOWED_EXTS:
            return jsonify({"error": f"unsupported extension: {ext}"}), 415

        jid = uuid4().hex
        in_path = os.path.join(UPLOADS_DIR, f"{jid}{ext}")
        out_name = f"{base}.pdf"
        tmp_out = os.path.join(OUTPUTS_DIR, f"{jid}.pdf")
        final_out = os.path.join(OUTPUTS_DIR, out_name)

        f.save(in_path)
        try:
            # LibreOffice를 이용한 PDF 변환
            result = perform_createpdf_libreoffice(in_path, OUTPUTS_DIR)
            if not result:
                raise RuntimeError("LibreOffice conversion failed")
            
            # 결과 파일을 tmp_out으로 이동
            if result != tmp_out:
                if os.path.exists(tmp_out):
                    os.remove(tmp_out)
                os.replace(result, tmp_out)
            
            # PDF 유효성 검사
            if not _is_pdf(tmp_out):
                raise RuntimeError("Output is not a valid PDF")
            
            # 최종 파일명으로 이동
            if tmp_out != final_out:
                if os.path.exists(final_out):
                    os.remove(final_out)
                os.replace(tmp_out, final_out)

            size = os.path.getsize(final_out)
            # 스트리밍으로 직접 전송(메모리 절약)
            resp = send_file(
                final_out,
                as_attachment=True,
                download_name=out_name,         # 기본 파일명(추가로 아래에서 RFC5987 설정)
                mimetype="application/pdf",
                conditional=False
            )
            resp.headers["Content-Length"] = str(size)
            return _set_pdf_disposition(resp, out_name)
        except Exception as e:
            app.logger.exception("conversion failed")
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.remove(in_path)
            except:
                pass
    finally:
        SEMA.release()


@app.get("/index.html")
def index_html():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
