from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os, io, sys, logging, tempfile, shutil, subprocess, shlex
import shutil as _sh
from uuid import uuid4
from urllib.parse import quote

# Adobe API 비활성화 (LibreOffice 전용)
ADOBE_SDK_AVAILABLE = False

load_dotenv()
logging.basicConfig(level=logging.INFO)
app = Flask(__name__, template_folder="templates", static_folder="static")
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
    return render_template("index.html", page=page)


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

    app.logger.info(f"Starting conversion: {name} -> {out_name}")
    app.logger.info(f"Input path: {in_path}")
    app.logger.info(f"Output path: {out_path}")
    app.logger.info(f"Final path: {final_path}")

    try:
        f.save(in_path)
        app.logger.info(f"File saved successfully: {in_path}")
    except Exception as e:
        app.logger.error(f"Failed to save input file: {e}")
        return jsonify({"error": f"Failed to save input file: {str(e)}"}), 500
    
    # LibreOffice 변환 시도
    conversion_success = False
    error_messages = []
    
    try:
        app.logger.info("Attempting conversion with LibreOffice...")
        result = perform_createpdf_libreoffice(in_path, OUTPUTS_DIR)
        
        if result:
            # result is the path to the created PDF file
            app.logger.info(f"LibreOffice conversion successful - output file: {result}")
            conversion_success = True
            
            # Move the file to the expected output path
            if result != out_path:
                if os.path.exists(out_path):
                    os.remove(out_path)
                os.replace(result, out_path)
                app.logger.info(f"Moved output from {result} to {out_path}")
        else:
            app.logger.error("LibreOffice conversion failed - no output file created")
            error_messages.append("LibreOffice: No output file created")
            
    except Exception as e:
        app.logger.error(f"LibreOffice conversion failed with exception: {e}")
        error_messages.append(f"LibreOffice: {str(e)}")
    
    # 변환 실패 시 오류 반환
    if not conversion_success:
        app.logger.error("All conversion methods failed")
        # 입력 파일 정리
        try:
            os.remove(in_path)
        except Exception:
            pass
        return jsonify({
            "error": "PDF conversion failed with all available methods",
            "details": error_messages
        }), 500
    
    # 파일 이동 및 최종 처리
    try:
        app.logger.info(f"Moving output file from {out_path} to {final_path}")
        
        if out_path != final_path:
            if os.path.exists(final_path):
                os.remove(final_path)
                app.logger.info(f"Removed existing final file: {final_path}")
            os.replace(out_path, final_path)
            app.logger.info(f"Successfully moved output file to: {final_path}")
        
        # 최종 파일 존재 및 크기 확인
        if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
            app.logger.error(f"Final output file is missing or empty: {final_path}")
            return jsonify({"error": "Final output file processing failed"}), 500
            
        app.logger.info(f"Conversion completed successfully - final file: {final_path} (size: {os.path.getsize(final_path)} bytes)")
        
    except Exception as e:
        app.logger.error(f"Failed to move output file: {e}")
        return jsonify({"error": f"File processing error: {str(e)}"}), 500
    finally:
        # 입력 파일 정리
        try:
            if os.path.exists(in_path):
                os.remove(in_path)
                app.logger.info(f"Cleaned up input file: {in_path}")
        except Exception as e:
            app.logger.warning(f"Failed to clean up input file: {e}")

    return _send_download(final_path, out_name)


@app.get("/index.html")
def index_html():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
