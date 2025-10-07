from flask import Flask, render_template, request, send_file, jsonify
import os
import fitz  # PyMuPDF
from PIL import Image
import io
import tempfile
import logging
import zipfile
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 제한

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vite 관련 요청 로그 필터링
class ViteLogFilter(logging.Filter):
    def filter(self, record):
        # Vite 관련 요청은 로그에서 제외
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if '/@vite/' in message:
                return False
        return True

# Werkzeug 로거에 필터 적용
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(ViteLogFilter())

@app.route('/')
def index():
    return render_template('index.html')

# Vite 클라이언트 요청을 조용히 처리 (로그 없이)
@app.route('/@vite/client')
def vite_client():
    return '', 204

@app.route('/@vite/<path:path>')
def vite_assets(path):
    return '', 204



@app.route('/convert', methods=['POST'])
def convert():
    try:
        file = request.files['file']
        quality = request.form.get('quality', 'medium')
        scale = float(request.form.get('scale', '1'))
        
        if not file or file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'PDF 파일만 업로드 가능합니다.'}), 400
        
        # PDF 바이트 읽기
        pdf_bytes = file.read()
        
        # 품질 설정 (DPI) - 기본값을 300으로 상향 조정
        dpi_map = {'low': 200, 'medium': 300, 'high': 400}
        dpi = dpi_map.get(quality, 300)
        
        # PyMuPDF로 PDF 열기
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        logger.info(f"PDF 페이지 수: {pdf_document.page_count}")
        
        # 단일 루프로 모든 페이지 처리 (메모리 최적화)
        images = []
        first_page_size = None
        
        # 첫 페이지에서 기준 크기 설정
        first_page = pdf_document[0]
        mat = fitz.Matrix(dpi/72.0 * scale, dpi/72.0 * scale)
        first_pix = first_page.get_pixmap(matrix=mat)
        
        # 첫 페이지 이미지로 기준 크기 설정
        try:
            first_img_data = first_pix.pil_tobytes(format="PNG")
            first_img = Image.open(io.BytesIO(first_img_data))
            if first_img.mode != 'RGB':
                first_img = first_img.convert('RGB')
            first_page_size = first_img.size
            logger.info(f"기준 페이지 크기 설정: {first_page_size}")
            images.append(first_img)
            logger.info(f"페이지 1 처리 완료: 모드={first_img.mode}, 크기={first_img.size}")
        except Exception as e:
            logger.error(f"첫 페이지 처리 실패: {str(e)}")
            first_img_data = first_pix.tobytes("ppm")
            first_img = Image.open(io.BytesIO(first_img_data))
            if first_img.mode != 'RGB':
                first_img = first_img.convert('RGB')
            first_page_size = first_img.size
            images.append(first_img)
        
        first_pix = None  # 메모리 해제
        
        # 나머지 페이지들을 단일 루프로 처리
        for page_num in range(1, pdf_document.page_count):
            page = pdf_document[page_num]
            mat = fitz.Matrix(dpi/72.0 * scale, dpi/72.0 * scale)
            pix = page.get_pixmap(matrix=mat)
            
            try:
                # PNG 형식으로 변환하여 안정적인 처리
                img_data = pix.pil_tobytes(format="PNG")
                img = Image.open(io.BytesIO(img_data))
                
                # RGB 모드로 강제 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 기준 크기로 리사이즈 (첫 페이지 기준)
                if img.size != first_page_size:
                    resized_img = Image.new('RGB', first_page_size, 'white')
                    img.thumbnail(first_page_size, Image.Resampling.LANCZOS)
                    # 중앙 배치
                    x = (first_page_size[0] - img.width) // 2
                    y = (first_page_size[1] - img.height) // 2
                    resized_img.paste(img, (x, y))
                    img = resized_img
                
                images.append(img)
                logger.info(f"페이지 {page_num + 1} 처리 완료: 모드={img.mode}, 크기={img.size}")
                
            except Exception as e:
                logger.error(f"페이지 {page_num + 1} 변환 실패: {str(e)}")
                # 대체 방법으로 처리
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if img.size != first_page_size:
                    resized_img = Image.new('RGB', first_page_size, 'white')
                    img.thumbnail(first_page_size, Image.Resampling.LANCZOS)
                    x = (first_page_size[0] - img.width) // 2
                    y = (first_page_size[1] - img.height) // 2
                    resized_img.paste(img, (x, y))
                    img = resized_img
                
                images.append(img)
                logger.info(f"페이지 {page_num + 1} 대체 방법으로 처리 완료")
            
            # 즉시 메모리 해제
            pix = None
        
        pdf_document.close()
        logger.info(f"총 {len(images)}개 페이지 변환 완료 (기준 크기: {first_page_size})")
        
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
        
        # 파일명 설정
        base_filename = os.path.splitext(file.filename)[0]
        
        try:
            # 고품질 저장 파라미터 설정
            save_params = {
                'format': 'TIFF',
                'compression': 'tiff_lzw',  # 무손실 압축
                'dpi': (dpi, dpi),  # 고해상도 DPI 설정
            }
            
            # 단일 페이지와 다중 페이지 분기 처리
            if len(images) == 1:
                # 단일 페이지: 파일명.TIFF로 저장
                tiff_filename = f"outputs/{base_filename}.TIFF"
                logger.info("단일 페이지 TIFF 생성")
                images[0].save(tiff_filename, **save_params)
                logger.info(f"단일 페이지 TIFF 저장 완료: {tiff_filename}")
                
                # 단일 페이지 TIFF 파일 반환
                return send_file(tiff_filename, 
                               as_attachment=True, 
                               download_name=f"{base_filename}.TIFF",
                               mimetype='image/tiff')
            else:
                # 다중 페이지: 개별 TIFF 파일들을 ZIP으로 압축
                zip_filename = f"outputs/{base_filename}_TIFF.ZIP"
                logger.info(f"다중 페이지 ZIP 생성 시작: {len(images)}페이지")
                
                # ZIP 파일 생성
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for i, img in enumerate(images, 1):
                        # 각 페이지를 개별 TIFF 파일로 저장
                        page_filename = f"page_{i}.tiff"
                        temp_tiff_path = f"outputs/temp_{page_filename}"
                        
                        # 임시 TIFF 파일 생성
                        img.save(temp_tiff_path, **save_params)
                        
                        # ZIP에 추가
                        zipf.write(temp_tiff_path, page_filename)
                        
                        # 임시 파일 삭제
                        os.remove(temp_tiff_path)
                        
                        logger.info(f"페이지 {i} ZIP에 추가 완료")
                
                logger.info(f"다중 페이지 ZIP 파일 생성 완료: {zip_filename}")
                
                # ZIP 파일 반환
                return send_file(zip_filename, 
                               as_attachment=True, 
                               download_name=f"{base_filename}_TIFF.ZIP",
                               mimetype='application/zip')
            
            # 메모리 관리: 이미지 리스트 객체 명시적 삭제 (대용량 파일 처리 시 메모리 누수 방지)
            logger.info("메모리 정리 시작")
            for img in images:
                if hasattr(img, 'close'):
                    img.close()
            del images
            logger.info("메모리 정리 완료")
                    
        except Exception as e:
            logger.error(f"TIFF 저장 중 오류: {str(e)}")
            # 메모리 정리 (오류 발생 시에도 수행)
            try:
                for img in images:
                    if hasattr(img, 'close'):
                        img.close()
                del images
            except:
                pass
            raise
        
        return send_file(tiff_filename, 
                       as_attachment=True, 
                       download_name=f"{os.path.splitext(file.filename)[0]}.TIFF",
                       mimetype='image/tiff')
    
    except Exception as e:
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/convert-to-tiff', methods=['POST'])
def convert_to_tiff():
    """다중 파일 업로드를 지원하는 TIFF 변환 엔드포인트"""
    try:
        # request.files.getlist()로 여러 파일 받기
        files = request.files.getlist('file')
        
        if not files or len(files) == 0:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 검증
        for file in files:
            if file.filename == '':
                return jsonify({'error': '빈 파일이 포함되어 있습니다.'}), 400
        
        # 분기 처리 로직
        if len(files) == 1 and files[0].filename.lower().endswith('.pdf'):
            # 단일 PDF 파일: 기존 PyMuPDF 로직 사용
            return convert_single_pdf_to_tiff(files[0])
        else:
            # 여러 이미지 파일 또는 단일 이미지: Pillow로 다중 페이지 TIFF 저장
            return convert_images_to_multi_tiff(files)
    
    except Exception as e:
        logger.error(f"변환 중 오류: {str(e)}")
        return jsonify({'error': f'변환 중 오류가 발생했습니다: {str(e)}'}), 500

def convert_single_pdf_to_tiff(file):
    """단일 PDF를 TIFF로 변환 (기존 로직 재사용)"""
    # 기존 /convert 라우트의 로직을 재사용
    # 여기서는 기존 convert 함수의 핵심 로직을 호출
    return convert_pdf_file(file)

def convert_images_to_multi_tiff(files):
    """여러 이미지를 다중 페이지 TIFF로 변환"""
    try:
        image_list = []
        
        # 각 파일을 Pillow로 열어 이미지 객체 리스트 생성
        for file in files:
            # 지원되는 이미지 형식 확인
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf']
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                return jsonify({'error': f'지원되지 않는 파일 형식: {file.filename}'}), 400
            
            if file_ext == '.pdf':
                # PDF 파일인 경우 PyMuPDF로 처리
                pdf_images = convert_pdf_to_images(file)
                image_list.extend(pdf_images)
            else:
                # 이미지 파일인 경우 Pillow로 처리
                try:
                    img = Image.open(file.stream)
                    # RGB 모드로 변환
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    image_list.append(img)
                except Exception as e:
                    return jsonify({'error': f'이미지 파일 읽기 실패 ({file.filename}): {str(e)}'}), 400
        
        if not image_list:
            return jsonify({'error': '변환할 수 있는 이미지가 없습니다.'}), 400
        
        # 출력 디렉토리 생성
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
        
        # 다중 페이지 TIFF 파일명 생성
        base_name = os.path.splitext(files[0].filename)[0] if len(files) == 1 else 'multi_images'
        tiff_filename = f"outputs/{base_name}.TIFF"
        
        # 다중 페이지 TIFF 저장
        if len(image_list) == 1:
            # 단일 이미지
            image_list[0].save(tiff_filename, format='TIFF', compression='tiff_lzw')
        else:
            # 다중 페이지 TIFF
            first_image = image_list[0]
            remaining_images = image_list[1:]
            
            first_image.save(
                tiff_filename,
                format='TIFF',
                save_all=True,
                append_images=remaining_images,
                compression='tiff_lzw'
            )
        
        logger.info(f"다중 페이지 TIFF 생성 완료: {tiff_filename} ({len(image_list)}페이지)")
        
        # 메모리 정리
        for img in image_list:
            if hasattr(img, 'close'):
                img.close()
        
        return send_file(tiff_filename, 
                       as_attachment=True, 
                       download_name=f"{base_name}.TIFF",
                       mimetype='image/tiff')
    
    except Exception as e:
        logger.error(f"이미지 변환 중 오류: {str(e)}")
        return jsonify({'error': f'이미지 변환 중 오류가 발생했습니다: {str(e)}'}), 500

def convert_pdf_to_images(file):
    """PDF 파일을 이미지 리스트로 변환"""
    try:
        import fitz  # PyMuPDF
        
        # PDF 문서 열기
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        images = []
        
        # 각 페이지를 이미지로 변환
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            mat = fitz.Matrix(2.0, 2.0)  # 2배 확대
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # RGB 모드로 변환
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            images.append(img)
        
        pdf_document.close()
        return images
    
    except Exception as e:
        logger.error(f"PDF 이미지 변환 중 오류: {str(e)}")
        raise

def convert_pdf_file(file):
    """기존 PDF 변환 로직을 재사용하는 헬퍼 함수"""
    # 기존 /convert 라우트의 핵심 로직을 여기에 구현
    # 이는 기존 코드와 동일한 로직을 사용
    try:
        import fitz  # PyMuPDF
        
        # 요청에서 품질 설정 가져오기 (기본값 설정)
        quality = request.form.get('quality', 'high')
        custom_width = request.form.get('custom_width')
        custom_height = request.form.get('custom_height')
        
        # 품질에 따른 DPI 설정
        dpi_settings = {
            'low': 150,
            'medium': 200, 
            'high': 300,
            'ultra': 400
        }
        dpi = dpi_settings.get(quality, 300)
        
        # PDF 문서 열기
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        images = []
        first_page_size = None
        
        logger.info(f"PDF 변환 시작: {file.filename} (DPI: {dpi})")
        
        # 각 페이지를 이미지로 변환
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # DPI에 따른 변환 매트릭스 계산
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # 페이지를 이미지로 변환
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # 첫 페이지 크기 저장
            if first_page_size is None:
                first_page_size = img.size
                logger.info(f"기준 페이지 크기 설정: {first_page_size}")
            
            # 사용자 정의 크기 적용
            if custom_width and custom_height:
                try:
                    target_width = int(custom_width)
                    target_height = int(custom_height)
                    target_size = (target_width, target_height)
                    
                    if target_size != img.size:
                        resized_img = Image.new('RGB', target_size, 'white')
                        img.thumbnail(target_size, Image.Resampling.LANCZOS)
                        x = (target_size[0] - img.width) // 2
                        y = (target_size[1] - img.height) // 2
                        resized_img.paste(img, (x, y))
                        img = resized_img
                        
                        if first_page_size != target_size:
                            first_page_size = target_size
                            logger.info(f"사용자 정의 크기 적용: {target_size}")
                except ValueError:
                    logger.warning("잘못된 사용자 정의 크기 값, 기본 크기 사용")
            
            # RGB 모드로 변환
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            images.append(img)
            logger.info(f"페이지 {page_num + 1}/{len(pdf_document)} 변환 완료")
        
        pdf_document.close()
        
        # 출력 디렉토리 생성
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
        
        # TIFF 파일명 생성
        tiff_filename = f"outputs/{os.path.splitext(file.filename)[0]}.TIFF"
        
        # TIFF 저장
        if len(images) == 1:
            images[0].save(tiff_filename, format='TIFF', compression='tiff_lzw', dpi=(dpi, dpi))
        else:
            first_image = images[0]
            remaining_images = images[1:]
            
            first_image.save(
                tiff_filename,
                format='TIFF',
                save_all=True,
                append_images=remaining_images,
                compression='tiff_lzw',
                dpi=(dpi, dpi)
            )
        
        # 메모리 정리
        for img in images:
            if hasattr(img, 'close'):
                img.close()
        
        return send_file(tiff_filename, 
                       as_attachment=True, 
                       download_name=f"{os.path.splitext(file.filename)[0]}.TIFF",
                       mimetype='image/tiff')
    
    except Exception as e:
        logger.error(f"PDF 변환 중 오류: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(debug=True)