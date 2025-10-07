from flask import Flask, render_template, request, send_file, jsonify
import os
import zipfile
import fitz  # PyMuPDF
import tempfile

app = Flask(__name__)

@app.route("/health")
def health():
    return "ok", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    input_path = None
    image_paths = []
    zip_path = None
    
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
        
        # 품질 설정
        dpi_map = {'low': 150, 'medium': 200, 'high': 300}
        dpi = dpi_map.get(quality, 200)
        
        # 크기 조절 적용
        dpi = int(dpi * scale)
        
        # PDF를 이미지로 변환
        doc = fitz.open(input_path)
        base_filename = os.path.splitext(os.path.basename(file.filename))[0]
        
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            # 파일 이름을 원본 파일 이름 기반으로 만듭니다.
            output_image_filename = f"{base_filename}_page_{i+1}.jpg"
            image_path = os.path.join('outputs', output_image_filename)
            pix.save(image_path)
            image_paths.append(image_path)
        
        page_count = len(doc)
        doc.close()
        
        # --- 여기가 핵심 로직 ---
        if page_count == 1:
            # 페이지가 1장이면, 첫 번째 이미지를 바로 보냅니다.
            single_image_path = image_paths[0]
            download_name = os.path.basename(single_image_path)
            print(f"페이지가 1장이라 JPG 파일({download_name})을 직접 보냅니다.")
            return send_file(single_image_path, as_attachment=True, download_name=download_name)
        
        elif page_count > 1:
            # 페이지가 2장 이상이면, ZIP 파일로 압축합니다.
            zip_filename = f"{base_filename}_images.zip"
            zip_path = os.path.join('outputs', zip_filename)
            print(f"페이지가 {page_count}장이라 ZIP 파일({zip_filename})로 압축합니다.")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in image_paths:
                    zipf.write(file_path, os.path.basename(file_path))
            
            # ZIP 파일을 보냅니다.
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
        else:  # page_count == 0
            # 페이지가 없는 PDF일 경우
            return jsonify({'error': 'PDF 파일에 페이지가 없습니다.'}), 400
    
    except Exception as e:
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500
    
    finally:
        # 작업이 끝난 후 임시 파일들을 정리합니다.
        # 입력 PDF 파일 정리
        try:
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
        except Exception as e:
            print(f"입력 파일 삭제 실패 (무시됨): {e}")
            
        # 생성된 이미지 파일들 정리 (ZIP으로 묶었거나 1장 보낸 후)
        for path in image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"이미지 파일 삭제 실패 (무시됨): {e}")
        
        # 생성된 ZIP 파일 정리 (다운로드 보낸 후)
        if zip_path:
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception as e:
                print(f"ZIP 파일 삭제 실패 (무시됨): {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)