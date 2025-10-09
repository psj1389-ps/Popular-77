from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import os
import shutil
import tempfile
import zipfile
from pdf2image import convert_from_bytes
from PIL import Image
import io
import logging

logging.basicConfig(level=logging.INFO)

# 영속 경로 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://popular-77.vercel.app", "https://*.vercel.app", "http://localhost:5173"]}})

# 비동기 처리를 위한 전역 변수
executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}  # job_id -> {"status": "pending|done|error", "path": "", "name": "", "ctype": "", "error": "", "progress": 0, "message": ""}

def set_progress(job_id, p, msg=None):
    """진행률 업데이트 도우미 함수"""
    info = JOBS.get(job_id)
    if not info: return
    info["progress"] = int(p)
    if msg:
        info["message"] = msg

def perform_jpg_conversion(file_path, quality, scale):
    """
    PDF를 JPG로 변환하는 핵심 함수
    
    Args:
        file_path: 저장된 PDF 경로
        quality: "low"|"medium"|"high"
        scale: 문자열/숫자(예: "1.0")
    
    Returns:
        (output_path, download_name, content_type)
        - 다중 페이지면 zip 경로와 이름(.zip), content_type="application/zip"
        - 단일 페이지면 jpg 경로와 이름(.jpg), content_type="image/jpeg"
    """
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # 임시 폴더에서 변환 작업 수행
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # 품질 설정
            dpi_map = {'low': 150, 'medium': 200, 'high': 300}
            dpi = dpi_map.get(quality, 200)
            
            # 크기 조절 적용
            dpi = int(dpi * float(scale))
            
            print(f"[DEBUG] 변환 시작 - 파일: {file_path}, 기본 파일명: {base_filename}")
            
            # pdf2image를 사용하여 PDF를 이미지로 변환
            with open(file_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
            
            # PDF를 PIL 이미지로 변환
            images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
            page_count = len(images)
            print(f"[DEBUG] PDF 변환 완료 - 총 {page_count}개 페이지 발견")
            
            if page_count == 0:
                raise Exception('PDF 파일에 페이지가 없습니다.')
            
            # 임시 폴더에 JPG 파일들 생성
            tmp_image_paths = []
            for page_num, pil_image in enumerate(images):
                output_image_filename = f"{base_filename}_page_{page_num+1}.jpg"
                tmp_image_path = os.path.join(tmp_dir, output_image_filename)
                pil_image.save(tmp_image_path, 'JPEG')
                tmp_image_paths.append(tmp_image_path)
                print(f"[DEBUG] 페이지 {page_num+1} 저장 완료: {output_image_filename}")
            
            print(f"[DEBUG] 최종 페이지 수: {page_count}")
            
            if page_count == 1:
                # 단일 페이지: JPG 파일을 OUTPUTS_DIR로 이동
                final_name = f"{base_filename}.jpg"
                final_path = os.path.join(OUTPUTS_DIR, final_name)
                shutil.move(tmp_image_paths[0], final_path)
                print(f"[DEBUG] 단일 페이지 처리 - JPG 파일({final_name})을 {final_path}로 이동")
                return final_path, final_name, "image/jpeg"
            
            else:
                # 다중 페이지: ZIP 파일을 OUTPUTS_DIR에 생성
                final_name = f"{base_filename}.zip"
                final_path = os.path.join(OUTPUTS_DIR, final_name)
                print(f"[DEBUG] 다중 페이지 처리 - {page_count}장을 ZIP 파일({final_name})로 압축")
                
                with zipfile.ZipFile(final_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for tmp_path in tmp_image_paths:
                        zf.write(tmp_path, arcname=os.path.basename(tmp_path))
                        print(f"[DEBUG] ZIP에 추가: {os.path.basename(tmp_path)}")
                
                print(f"[DEBUG] ZIP 파일 생성 완료: {final_name}")
                return final_path, final_name, "application/zip"
                
        except Exception as e:
            print(f"[ERROR] JPG 변환 중 오류 발생: {e}")
            raise

@app.route("/health")
def health():
    return "ok", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    input_path = None
    
    try:
        file = request.files['file']
        quality = request.form.get('quality', 'medium')
        scale = float(request.form.get('scale', '1'))
        
        if not file or file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400
        
        # 출력 폴더 생성
        if not os.path.exists('outputs'):
            os.makedirs('outputs')

        # 임시 PDF 파일 저장
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir='outputs')
        file.save(temp_pdf.name)
        input_path = temp_pdf.name
        temp_pdf.close()
        
        # 변환 함수 호출
        output_path, download_name, content_type = perform_jpg_conversion(input_path, quality, scale)
        
        # 파일 전송
        return send_file(output_path, as_attachment=True, download_name=download_name, mimetype=content_type)
    
    except Exception as e:
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500
    
    finally:
        # 입력 PDF 파일 정리
        try:
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
        except Exception as e:
            print(f"입력 파일 삭제 실패 (무시됨): {e}")

@app.route('/convert-async', methods=['POST'])
def convert_async():
    f = request.files.get("file") or request.files.get("pdfFile")
    if not f:
        return jsonify({"error": "file field is required"}), 400
    
    quality = request.form.get("quality", "medium")
    scale = request.form.get("scale", "1.0")
    
    # 업로드 저장
    job_id = uuid4().hex
    in_path = os.path.join(UPLOADS_DIR, f"{job_id}.pdf")
    f.save(in_path)
    
    JOBS[job_id] = {"status": "pending", "progress": 1, "message": "대기 중"}
    
    def run_job():
        try:
            set_progress(job_id, 10, "변환 준비 중")
            # 변환 시작 직전
            set_progress(job_id, 50, "페이지 래스터라이즈 중")
            out_path, name, ctype = perform_jpg_conversion(in_path, quality, scale)
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
    name = info.get("name") or (os.path.basename(path) if path else "output.jpg")
    if not path or not os.path.exists(path):
        return jsonify({"error": "output file missing"}), 500
    
    ctype = info.get("ctype")
    if not ctype:
        ctype = "application/zip" if path.lower().endswith(".zip") else "image/jpeg"
    
    return send_file(path, mimetype=ctype, as_attachment=True, download_name=name)

@app.errorhandler(Exception)
def handle_any_error(e):
    app.logger.exception("Unhandled error")
    return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)