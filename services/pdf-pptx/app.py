from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed
import os, mimetypes

app = Flask(__name__)

def guess_mime_by_name(name: str) -> str:
    n = (name or "").lower()
    if n.endswith(".svg"): return "image/svg+xml"
    if n.endswith(".zip"): return "application/zip"
    if n.endswith(".ai"): return "application/pdf"  # Illustrator 호환 PDF
    if n.endswith(".pptx"): return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if n.endswith(".xlsx"): return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return mimetypes.guess_type(n)[0] or "application/octet-stream"

# CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://77-tools.xyz",
            "https://www.77-tools.xyz",
            "https://popular-77.vercel.app",
            "https://*.vercel.app"
        ],
        "expose_headers": ["Content-Disposition"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.before_request
def reject_front_routes():
    if request.path.startswith("/tools/"):
        raise NotFound()

@app.errorhandler(HTTPException)
def handle_http_exc(e):
    return jsonify({"error": e.description or "error"}), e.code

@app.errorhandler(Exception)
def handle_any_exc(e):
    app.logger.exception("Unhandled")
    return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return "PDF to PPTX Converter is running!"

@app.route("/health")
def health():
    return "ok", 200

@app.post("/convert-async")
def convert_async():
    """
    PDF to PPTX 비동기 변환 엔드포인트 (향후 구현 예정)
    현재는 기본 응답만 반환합니다.
    """
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    # 임시로 job_id 반환 (실제 변환 로직은 향후 구현)
    from uuid import uuid4
    job_id = uuid4().hex
    return jsonify({"job_id": job_id, "status": "pending"}), 202

@app.post("/convert")
def convert_compat():
    """
    구(舊) 클라이언트가 /convert로 올 때를 위한 하위호환 엔드포인트.
    내부적으로 /convert-async 로직을 그대로 실행해 job_id를 반환합니다.
    """
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    # 그대로 convert-async 실행
    return convert_async()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)