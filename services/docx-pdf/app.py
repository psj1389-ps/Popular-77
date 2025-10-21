from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os, io, sys, logging, tempfile, shutil, subprocess, shlex
import shutil as _sh
from uuid import uuid4

# Adobe API 비활성화 (LibreOffice 전용)
ADOBE_SDK_AVAILABLE = False

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["*", "https://77-tools.xyz", "http://localhost:*", "http://127.0.0.1:*"]}}, expose_headers=["Content-Disposition"], supports_credentials=True)

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


def _find_soffice():
    """LibreOffice soffice 실행 파일 경로를 찾습니다."""
    # 환경 변수에서 먼저 확인
    if 'SOFFICE_BIN' in os.environ:
        soffice_path = os.environ['SOFFICE_BIN']
        if os.path.exists(soffice_path):
            app.logger.info(f"Found soffice from environment variable: {soffice_path}")
            return soffice_path
    
    possible_paths = [
        '/usr/bin/soffice',
        '/usr/lib/libreoffice/program/soffice',
        '/opt/libreoffice*/program/soffice',
        '/snap/libreoffice/current/lib/libreoffice/program/soffice'
    ]
    
    for path in possible_paths:
        # 와일드카드 경로 처리
        if '*' in path:
            import glob
            matches = glob.glob(path)
            for match in matches:
                if os.path.exists(match):
                    app.logger.info(f"Found soffice at: {match}")
                    return match
        elif os.path.exists(path):
            app.logger.info(f"Found soffice at: {path}")
            return path
    
    # 시스템 PATH에서 찾기
    import shutil
    soffice_in_path = shutil.which('soffice')
    if soffice_in_path:
        app.logger.info(f"Found soffice in PATH: {soffice_in_path}")
        return soffice_in_path
    
    app.logger.error("soffice not found in any known location")
    return None



def perform_createpdf_libreoffice(in_path: str, out_pdf_path: str):
    soffice = _find_soffice()
    if not soffice:
        app.logger.error("LibreOffice (soffice) not found in system PATH")
        app.logger.error("Checked paths: SOFFICE_BIN env var, PATH, /usr/bin/soffice, /usr/lib/libreoffice/program/soffice, /opt/libreoffice/program/soffice")
        raise RuntimeError("LibreOffice (soffice) not found in system PATH. Set SOFFICE_BIN or install apt packages.")
    
    app.logger.info(f"Using LibreOffice at: {soffice}")
    outdir = os.path.dirname(out_pdf_path)
    os.makedirs(outdir, exist_ok=True)
    
    # 더 안전한 명령어 구성
    cmd = [
        soffice,
        "--headless",
        "--nologo", 
        "--nofirststartwizard",
        "--convert-to", "pdf",
        "--outdir", outdir,
        in_path
    ]
    
    app.logger.info(f"Running LibreOffice command: {' '.join(shlex.quote(arg) for arg in cmd)}")
    
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        stdout = proc.stdout.decode('utf-8', 'ignore')
        stderr = proc.stderr.decode('utf-8', 'ignore')
        
        app.logger.info(f"LibreOffice stdout: {stdout}")
        if stderr:
            app.logger.warning(f"LibreOffice stderr: {stderr}")
            
        if proc.returncode != 0:
            app.logger.error(f"LibreOffice failed with return code {proc.returncode}")
            raise RuntimeError(f"LibreOffice failed (code {proc.returncode}): {stderr}")
            
    except subprocess.TimeoutExpired:
        app.logger.error("LibreOffice conversion timed out after 60 seconds")
        raise RuntimeError("LibreOffice conversion timed out")
    except Exception as e:
        app.logger.error(f"LibreOffice subprocess error: {str(e)}")
        raise RuntimeError(f"LibreOffice subprocess error: {str(e)}")
    
    base = os.path.splitext(os.path.basename(in_path))[0]
    produced = os.path.join(outdir, f"{base}.pdf")
    
    if not os.path.exists(produced):
        app.logger.error(f"Expected output file not found: {produced}")
        # List files in output directory for debugging
        try:
            files = os.listdir(outdir)
            app.logger.error(f"Files in output directory: {files}")
        except Exception as e:
            app.logger.error(f"Could not list output directory: {e}")
        raise RuntimeError(f"LibreOffice did not produce expected output file: {produced}")
    
    if produced != out_pdf_path:
        if os.path.exists(out_pdf_path):
            os.remove(out_pdf_path)
        os.replace(produced, out_pdf_path)
        app.logger.info(f"Moved output from {produced} to {out_pdf_path}")


@app.get("/")
def index():
    accept = request.headers.get("Accept", "") or ""
    if "text/html" in accept:
        return render_template("index.html")
    return jsonify({
        "service": "docx-pdf",
        "version": "libreoffice-only",
        "endpoints": ["/convert", "/health", "/index.html"],
        "conversion_methods": ["LibreOffice"]
    })


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
        "python": sys.version,
        "libreoffice": lo_ver,
        "allowed_exts": sorted(list(ALLOWED_EXTS))
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
    
    # 먼저 LibreOffice로 시도, 실패 시 Adobe API로 폴백
    conversion_success = False
    error_messages = []
    
    try:
        app.logger.info("Attempting conversion with LibreOffice...")
        perform_createpdf_libreoffice(in_path, out_path)
        conversion_success = True
        app.logger.info("LibreOffice conversion successful")
    except Exception as e:
        app.logger.error(f"LibreOffice conversion failed: {e}")
        error_messages.append(f"LibreOffice: {str(e)}")
    
    if not conversion_success:
        app.logger.error("All conversion methods failed")
        return jsonify({
            "error": "PDF conversion failed with all available methods",
            "details": error_messages
        }), 500
    
    try:
        if out_path != final_path:
            if os.path.exists(final_path):
                os.remove(final_path)
            os.replace(out_path, final_path)
    except Exception as e:
        app.logger.error(f"Failed to move output file: {e}")
        return jsonify({"error": f"File processing error: {str(e)}"}), 500
    finally:
        try:
            os.remove(in_path)
        except Exception:
            pass

    return _send_download(final_path, out_name)


@app.get("/index.html")
def index_html():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
