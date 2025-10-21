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
        perform_createpdf_libreoffice(in_path, out_path)
        
        # 변환 성공 확인: 출력 파일이 실제로 생성되었는지 검증
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            conversion_success = True
            app.logger.info(f"LibreOffice conversion successful - output file created: {out_path} (size: {os.path.getsize(out_path)} bytes)")
        else:
            app.logger.error(f"LibreOffice conversion failed - output file not found or empty: {out_path}")
            error_messages.append("LibreOffice: Output file not created or is empty")
            
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
