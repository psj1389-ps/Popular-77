from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import os
import shutil
import tempfile
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from pptx import Presentation
from pptx.util import Inches
import io
from PIL import Image
import json
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, Inches as DocxInches
import subprocess
import platform
import pytesseract
import cv2
import numpy as np
import fitz  # PyMuPDF
import re
import urllib.parse
from typing import List, Tuple, Dict, Any
from pdf2docx import Converter
import logging

# 환경 변수 로드
load_dotenv()

# 환경변수 기반 설정
MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '100'))
ENABLE_DEBUG_LOGS = os.getenv('ENABLE_DEBUG_LOGS', 'true').lower() == 'true'
CONVERSION_TIMEOUT = int(os.environ.get('CONVERSION_TIMEOUT_SECONDS', '300'))
TEMP_FILE_CLEANUP = os.environ.get('TEMP_FILE_CLEANUP', 'true').lower() == 'true'

logging.basicConfig(level=logging.INFO)

# 영속 경로 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "https://popular-77.vercel.app",
            r"https://.*\.vercel\.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Disposition"]
    }
})
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
max_mb = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "100"))
app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024

# 비동기 처리를 위한 전역 변수
executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}  # job_id -> {"status": "pending|done|error", "path": "", "name": "", "ctype": "", "error": "", "progress": 0, "message": ""}

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'bmp'}

# 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def safe_base_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename or "output"))[0]
    # 위험 문자 제거만(한글/공백/숫자/영문/.-_는 허용)
    base = base.replace("/", "_").replace("\\", "_")
    base = re.sub(r'[\r\n\t"]+', "_", base)
    return base.strip() or "output"

def attach_download_headers(resp, download_name: str):
    quoted = urllib.parse.quote(download_name)
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quoted}"
    return resp

def set_progress(job_id, p, msg=None):
    """진행률 업데이트 도우미 함수"""
    info = JOBS.get(job_id)
    if not info: return
    info["progress"] = int(p)
    if msg:
        info["message"] = msg

def perform_doc_conversion(file_path, quality, base_name):
    """
    PDF를 DOCX로 변환하는 핵심 함수
    
    Args:
        file_path: 저장된 PDF 경로
        quality: "low"|"standard"
        base_name: 안전한 베이스 파일명
    
    Returns:
        (output_path, download_name, content_type)
        - 항상 docx 파일, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    """
    try:
        print(f"[DEBUG] 변환 시작 - 파일: {file_path}, 기본 파일명: {base_name}")
        
        # 최종 출력 경로
        final_name = f"{base_name}.docx"
        final_path = os.path.join(OUTPUTS_DIR, final_name)
        
        # 기존 pdf_to_docx 함수 호출
        pdf_to_docx(file_path, final_path, quality)
        
        print(f"[DEBUG] DOCX 변환 완료: {final_name}")
        return final_path, final_name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
    except Exception as e:
        print(f"[ERROR] DOCX 변환 중 오류 발생: {e}")
        raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pdf_to_docx_with_pdf2docx(pdf_path, output_path):
    """pdf2docx 라이브러리를 사용한 PDF → DOCX 변환"""
    try:
        print("pdf2docx 라이브러리를 사용하여 변환 중...")
        
        # Converter 객체 생성
        cv = Converter(pdf_path)
        
        # 변환 실행
        cv.convert(output_path, start=0, end=None)
        
        # 객체 닫기
        cv.close()
        
        print(f"pdf2docx 변환 완료: {output_path}")
        return True
        
    except Exception as e:
        print(f"pdf2docx 변환 실패: {e}")
        return False

def pdf_to_docx(pdf_path, output_path, quality='medium'):
    """PDF를 DOCX로 변환하는 함수"""
    try:
        # pdf2docx 라이브러리를 사용한 변환 시도
        print("=== pdf2docx 라이브러리 변환 시도 ===")
        if pdf_to_docx_with_pdf2docx(pdf_path, output_path):
            print("pdf2docx 변환 성공!")
            
            # 변환된 파일이 실제로 존재하고 크기가 적절한지 확인
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:  # 1KB 이상
                print(f"변환 완료: {output_path} (크기: {os.path.getsize(output_path)} bytes)")
                return True
            else:
                print("pdf2docx 변환 결과가 부적절함.")
                return False
        else:
            print("pdf2docx 변환 실패")
            return False
        
    except Exception as e:
        print(f"변환 중 오류 발생: {str(e)}")
        return False

# 헬스체크
@app.route("/health")
def health():
    return "ok", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_sync():
    """동기 변환 - 즉시 파일 다운로드 응답"""
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    quality = request.form.get("quality", "medium")
    # 품질 매핑: low -> "low", medium/high -> "standard"
    payload_quality = "low" if quality == "low" else "standard"
    
    # 임시 파일로 저장
    temp_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{temp_id}.pdf")
    f.save(in_path)
    
    # 원본 파일명에서 base_name 추출
    base_name = safe_base_name(f.filename)
    
    try:
        # 동기적으로 변환 수행
        out_path, name, ctype = perform_doc_conversion(in_path, payload_quality, base_name)
        
        # 파일이 존재하는지 확인
        if not os.path.exists(out_path):
            return jsonify({"error": "변환된 파일을 찾을 수 없습니다"}), 500
        
        # 파일 다운로드 응답
        resp = send_file(out_path, mimetype=ctype, as_attachment=True, download_name=name)
        resp = attach_download_headers(resp, name)
        
        # 임시 파일 정리 (백그라운드에서)
        def cleanup():
            try:
                if os.path.exists(in_path):
                    os.remove(in_path)
                if os.path.exists(out_path):
                    os.remove(out_path)
            except:
                pass
        
        # 응답 후 정리 작업 예약
        executor.submit(cleanup)
        
        return resp
        
    except Exception as e:
        # 오류 발생 시 임시 파일 정리
        try:
            if os.path.exists(in_path):
                os.remove(in_path)
        except:
            pass
        
        app.logger.exception("변환 중 오류 발생")
        return jsonify({"error": f"변환 실패: {str(e)}"}), 500

@app.route('/convert-async', methods=['POST'])
def convert_async():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    quality = request.form.get("quality", "medium")
    # 품질 매핑: low -> "low", medium/high -> "standard"
    payload_quality = "low" if quality == "low" else "standard"
    
    # 업로드 저장
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    
    # 원본 파일명에서 base_name 추출
    base_name = safe_base_name(f.filename)
    
    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    
    def run_job():
        try:
            set_progress(job_id, 10, "변환 준비 중")
            # 변환 시작 직전
            set_progress(job_id, 50, "문서 분석 중")
            out_path, name, ctype = perform_doc_conversion(in_path, payload_quality, base_name)
            set_progress(job_id, 90, "파일 생성 중")
            
            JOBS[job_id] = {
                "status": "done", "path": out_path, "name": name, "ctype": ctype,
                "progress": 100, "message": "완료"
            }
            # 잡 완료 시 경로 로그
            app.logger.info(f"JOB {job_id} done: {out_path} exists={os.path.exists(out_path)}")
        except Exception as e:
            JOBS[job_id] = {
                "status": "error", "error": str(e),
                "progress": 0, "message": "변환 실패"
            }
        finally:
            # 입력파일 정리
            try:
                os.remove(in_path)
            except:
                pass
    
    executor.submit(run_job)
    return jsonify({"job_id": job_id}), 202

@app.route('/job/<job_id>', methods=['GET'])
def job_status(job_id):
    info = JOBS.get(job_id)
    if not info:
        return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
    
    # progress/message가 없으면 기본값 제공
    info.setdefault("progress", 0)
    info.setdefault("message", "")
    return jsonify(info), 200

@app.route('/download/<job_id>', methods=['GET'])
def job_download(job_id):
    info = JOBS.get(job_id)
    if not info:
        return jsonify({"error": "job not found"}), 404
    if info.get("status") != "done":
        return jsonify({"error": "not ready"}), 409
    
    path = info.get("path")
    name = info.get("name") or (os.path.basename(path) if path else "output.docx")
    if not path or not os.path.exists(path):
        return jsonify({"error": "output file missing"}), 500
    
    ctype = info.get("ctype")
    if not ctype:
        ctype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    resp = send_file(path, mimetype=ctype, as_attachment=True, download_name=name)
    return attach_download_headers(resp, name)

@app.errorhandler(404)
def not_found_error(error):
    """404 오류 처리"""
    app.logger.warning(f"404 오류: {request.url}")
    return jsonify({
        "error": "요청한 페이지를 찾을 수 없습니다",
        "available_endpoints": ["/", "/convert", "/convert-async", "/job/<job_id>", "/download/<job_id>", "/health"]
    }), 404

@app.errorhandler(Exception)
def handle_any_error(e):
    app.logger.exception("Unhandled error")
    return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, host='0.0.0.0', port=port)