from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import os
import zipfile
import tempfile
from pdf2image import convert_from_bytes
from PIL import Image
import io

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://popular-77.vercel.app", "http://localhost:5173"]}})

# 비동기 처리를 위한 전역 변수
executor = ThreadPoolExecutor(max_workers=2)
JOBS = {}  # job_id -> {"status": "pending|done|error", "path": "", "name": "", "ctype": "", "error": ""}

def perform_bmp_conversion(file_path, quality, scale):
    """
    PDF를 BMP로 변환하는 핵심 함수
    
    Args:
        file_path: 저장된 PDF 경로
        quality: "low"|"medium"|"high"
        scale: 문자열/숫자(예: "1.0")
    
    Returns:
        (output_path, download_name, content_type)
        - 다중 페이지면 zip 경로와 이름(.zip), content_type="application/zip"
        - 단일 페이지면 bmp 경로와 이름(.bmp), content_type="image/bmp"
    """
    image_paths = []
    
    try:
        # 품질 설정
        dpi_map = {'low': 150, 'medium': 200, 'high': 300}
        dpi = dpi_map.get(quality, 200)
        
        # 크기 조절 적용
        dpi = int(dpi * float(scale))
        
        # PDF를 이미지로 변환
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        print(f"[DEBUG] 변환 시작 - 파일: {file_path}, 기본 파일명: {base_filename}")
        
        # pdf2image를 사용하여 PDF를 이미지로 변환
        with open(file_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
        
        # PDF를 PIL 이미지로 변환
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        page_count = len(images)
        print(f"[DEBUG] PDF 변환 완료 - 총 {page_count}개 페이지 발견")
        
        if page_count == 0:
            raise Exception('PDF 파일에 페이지가 없습니다.')
        
        # 각 페이지를 BMP로 변환
        for page_num, pil_image in enumerate(images):
            # BMP 파일로 저장
            output_image_filename = f"{base_filename}_page_{page_num+1}.bmp"
            image_path = os.path.join('outputs', output_image_filename)
            pil_image.save(image_path, 'BMP')
            image_paths.append(image_path)
            print(f"[DEBUG] 페이지 {page_num+1} 저장 완료: {output_image_filename}")
        
        print(f"[DEBUG] 최종 페이지 수: {page_count}")
        
        if page_count == 1:
            # 페이지가 1장이면, 첫 번째 이미지를 바로 반환
            single_image_path = image_paths[0]
            download_name = f"{base_filename}.bmp"
            print(f"[DEBUG] 단일 페이지 처리 - BMP 파일({download_name})을 직접 반환")
            return single_image_path, download_name, "image/bmp"
        
        else:
            # 페이지가 2장 이상이면, ZIP 파일로 압축
            zip_filename = f"{base_filename}_images.zip"
            zip_path = os.path.join('outputs', zip_filename)
            print(f"[DEBUG] 다중 페이지 처리 - {page_count}장을 ZIP 파일({zip_filename})로 압축")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in image_paths:
                    zipf.write(file_path, os.path.basename(file_path))
                    print(f"[DEBUG] ZIP에 추가: {os.path.basename(file_path)}")
            
            print(f"[DEBUG] ZIP 파일 생성 완료: {zip_filename}")
            return zip_path, zip_filename, "application/zip"
    
    finally:
        # 생성된 이미지 파일들 정리 (ZIP으로 묶었거나 단일 파일 처리 후)
        for path in image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"이미지 파일 삭제 실패 (무시됨): {e}")

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
        output_path, download_name, content_type = perform_bmp_conversion(input_path, quality, scale)
        
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
    os.makedirs("uploads", exist_ok=True)
    job_id = uuid4().hex
    in_path = os.path.join("uploads", f"{job_id}.pdf")
    f.save(in_path)
    
    JOBS[job_id] = {"status": "pending"}
    
    def run_job():
        try:
            out_path, name, ctype = perform_bmp_conversion(in_path, quality, scale)
            JOBS[job_id] = {"status": "done", "path": out_path, "name": name, "ctype": ctype}
        except Exception as e:
            JOBS[job_id] = {"status": "error", "error": str(e)}
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
        return jsonify({"error": "job not found"}), 404
    return jsonify(info), 200

@app.route('/download/<job_id>', methods=['GET'])
def job_download(job_id):
    info = JOBS.get(job_id)
    if not info:
        return jsonify({"error": "job not found"}), 404
    if info.get("status") != "done":
        return jsonify({"error": "not ready"}), 409
    return send_file(
        info["path"],
        mimetype=info["ctype"],
        as_attachment=True,
        download_name=info["name"]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)