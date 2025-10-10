import os, re, io, zipfile, tempfile, logging, urllib.parse
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import fitz  # PyMuPDF

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://77-tools.xyz",
            "https://www.77-tools.xyz",
            "https://popular-77.vercel.app"
        ],
        "expose_headers": ["Content-Disposition"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}  # job_id -> dict

def safe_base_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename or "output"))[0]
    base = base.replace("/", "_").replace("\\", "_")
    base = re.sub(r'[\r\n\t"]+', "_", base).strip()
    return base or "output"

def attach_download_headers(resp, download_name: str):
    quoted = urllib.parse.quote(download_name)
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quoted}"
    return resp

def set_progress(job_id, p, msg=None):
    info = JOBS.setdefault(job_id, {})
    info["progress"] = int(p)
    if msg is not None:
        info["message"] = msg

def perform_ai_analysis(in_path, base_name: str):
    """AI 분석 기능 - PDF에서 텍스트 추출 및 분석"""
    try:
        doc = fitz.open(in_path)
        page_count = doc.page_count
        
        # 전체 텍스트 추출
        full_text = ""
        for i in range(page_count):
            set_progress(current_job_id, 10 + int(70*(i+1)/page_count), f"페이지 {i+1}/{page_count} 텍스트 추출 중")
            page = doc.load_page(i)
            text = page.get_text()
            full_text += f"\n--- 페이지 {i+1} ---\n{text}\n"
        
        doc.close()
        
        # 분석 결과 생성
        set_progress(current_job_id, 85, "AI 분석 중")
        analysis_result = {
            "total_pages": page_count,
            "total_characters": len(full_text),
            "total_words": len(full_text.split()),
            "extracted_text": full_text.strip(),
            "summary": f"PDF 문서 분석 완료: {page_count}페이지, {len(full_text.split())}단어"
        }
        
        # JSON 파일로 저장
        final_name = f"{base_name}_analysis.json"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        
        import json
        with open(final_path, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        return final_path, final_name, "application/json"
        
    except Exception as e:
        app.logger.exception(f"AI analysis error: {e}")
        raise

@app.get("/")
def home():
    return "OK (pdf-ai)"

@app.get("/health")
def health():
    return "ok", 200

@app.post("/convert-async")
def convert_async():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400

    base_name = safe_base_name(f.filename)
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    
    # AI 분석 옵션
    analysis_type = request.form.get("analysis_type", "text_extraction")
    
    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    app.logger.info(f"[{job_id}] uploaded: {in_path}, base={base_name}, analysis_type={analysis_type}")

    def run_job():
        global current_job_id
        current_job_id = job_id
        try:
            set_progress(job_id, 10, "AI 분석 준비 중")
            out_path, name, ctype = perform_ai_analysis(in_path, base_name)
            JOBS[job_id] = {"status": "done", "path": out_path, "name": name, "ctype": ctype,
                            "progress": 100, "message": "완료"}
            app.logger.info(f"[{job_id}] done: {out_path} exists={os.path.exists(out_path)}")
        except Exception as e:
            app.logger.exception("AI analysis error")
            JOBS[job_id] = {"status": "error", "error": str(e), "progress": 0, "message": "오류"}
        finally:
            try: os.remove(in_path)
            except: pass

    executor.submit(run_job)
    return jsonify({"job_id": job_id}), 202

@app.get("/job/<job_id>")
def job_status(job_id):
    info = JOBS.get(job_id)
    if not info: return jsonify({"error": "job not found"}), 404
    info.setdefault("progress", 0); info.setdefault("message", "")
    return jsonify(info), 200

@app.get("/download/<job_id>")
def job_download(job_id):
    info = JOBS.get(job_id)
    if not info: return jsonify({"error":"job not found"}), 404
    if info.get("status") != "done": return jsonify({"error":"not ready"}), 409
    path, name, ctype = info.get("path"), info.get("name"), info.get("ctype")
    if not path or not os.path.exists(path): return jsonify({"error":"output file missing"}), 500
    resp = send_file(path, mimetype=ctype, as_attachment=True, download_name=name)
    return attach_download_headers(resp, name)

@app.errorhandler(Exception)
def handle_any(e):
    app.logger.exception("Unhandled")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)