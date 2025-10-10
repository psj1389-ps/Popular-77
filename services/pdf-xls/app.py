# services/pdf-xls/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed
import os

app = Flask(__name__)

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
    return "PDF to XLS Converter is running!"

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)