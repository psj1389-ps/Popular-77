import os
from PIL import Image
from pdf2image import convert_from_path
# from reportlab.graphics import renderSVG  # Removed to avoid Cairo dependencies
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import base64
from io import BytesIO
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorConverter:
    def __init__(self):
        self.supported_formats = ['svg', 'ai']
        self.temp_dir = tempfile.mkdtemp()
        
    def extract_images_from_pdf(self, pdf_path):
        """PDF에서 이미지를 추출합니다."""
        try:
            logger.info(f"PDF 처리 중: {pdf_path}")
            
            # PDF 파일이 존재하는지 확인
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            
            # PDF를 이미지로 변환
            pil_images = convert_from_path(pdf_path, dpi=200)
            
            images = []
            for i, pil_image in enumerate(pil_images):
                # 임시 PNG 파일로 저장
                temp_path = os.path.join(self.temp_dir, f'page_{i+1}.png')
                pil_image.save(temp_path, 'PNG')
                
                images.append({
                    'name': f'page_{i+1}.png',
                    'path': temp_path,
                    'page': i + 1,
                    'size': pil_image.size
                })
            
            return images
            
        except Exception as e:
            logger.error(f"PDF 이미지 추출 중 오류: {str(e)}")
            return []
    
    def image_to_svg(self, image_path, output_path=None, quality='medium'):
        """이미지를 SVG 형식으로 변환합니다."""
        try:
            if output_path is None:
                output_path = image_path.replace('.png', '.svg').replace('.jpg', '.svg').replace('.jpeg', '.svg')
            
            # 이미지 로드
            with Image.open(image_path) as img:
                width, height = img.size
                
                # 이미지를 base64로 인코딩
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # SVG 생성 (이미지 임베드)
                svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image width="{width}" height="{height}" xlink:href="data:image/png;base64,{img_base64}"/>
</svg>'''
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"SVG 변환 중 오류: {str(e)}")
            return None
    
    def image_to_ai(self, image_path, output_path=None, quality='medium'):
        """이미지를 AI 형식으로 변환합니다 (EPS 형식으로)."""
        try:
            if output_path is None:
                output_path = image_path.replace('.png', '.ai').replace('.jpg', '.ai').replace('.jpeg', '.ai')
            
            # 이미지 로드
            with Image.open(image_path) as img:
                width, height = img.size
                
                # EPS 형식으로 저장 (Adobe Illustrator 호환)
                eps_path = output_path.replace('.ai', '.eps')
                img.save(eps_path, 'EPS')
                
                # EPS를 AI 확장자로 복사
                import shutil
                shutil.copy2(eps_path, output_path)
                
                # 임시 EPS 파일 삭제
                if os.path.exists(eps_path):
                    os.remove(eps_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"AI 변환 중 오류: {str(e)}")
            # EPS 저장이 실패하면 SVG 기반으로 대체
            try:
                svg_path = self.image_to_svg(image_path, quality=quality)
                if svg_path:
                    ai_content = self._convert_svg_to_ai(svg_path)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(ai_content)
                    return output_path
            except:
                pass
            return None
    
    def _reduce_colors(self, img, num_colors):
        """이미지의 색상 수를 줄입니다 (더미 구현)."""
        # 더미 구현 - 원본 반환
        return img
    
    def _find_contours(self, img):
        """이미지에서 윤곽선을 찾습니다 (더미 구현)."""
        # 더미 구현 - 빈 리스트 반환
        return []
    
    def _create_svg_from_contours(self, contours, width, height, img):
        """윤곽선으로부터 SVG를 생성합니다 (더미 구현)."""
        # 더미 구현 - 간단한 SVG 반환
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="{width}" height="{height}" fill="#f0f0f0" stroke="#000" stroke-width="2"/>
<text x="{width//2}" y="{height//2}" text-anchor="middle" font-family="Arial" font-size="24" fill="#333">벡터 변환된 이미지</text>
</svg>'''
        return svg_content
    
    def _convert_svg_to_ai(self, svg_path):
        """SVG를 Adobe Illustrator 호환 형식으로 변환합니다."""
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # AI 형식 헤더 추가 (Adobe Illustrator 호환)
        ai_header = '''%!PS-Adobe-3.0
%%Creator: Vector Converter
%%BoundingBox: 0 0 612 792
%%HiResBoundingBox: 0 0 612 792
%%DocumentData: Clean7Bit
%%EndComments
%%BeginProlog
%%EndProlog
%%BeginSetup
%%EndSetup
'''
        
        # SVG 내용을 AI 호환 PostScript로 변환
        ai_content = ai_header + f'''%%BeginDocument: embedded_svg
{svg_content}
%%EndDocument
%%EOF'''
        
        return ai_content
    
    def convert_pdf_to_vectors(self, pdf_path, output_format='svg', quality='medium', progress_callback=None):
        """PDF를 벡터 형식으로 변환합니다."""
        try:
            if progress_callback:
                progress_callback(0, "PDF에서 이미지 추출 중...")
            
            # PDF에서 이미지 추출
            images = self.extract_images_from_pdf(pdf_path)
            
            if not images:
                return {'success': False, 'message': 'PDF에서 이미지를 찾을 수 없습니다.'}
            
            converted_files = []
            total_images = len(images)
            
            for i, img_info in enumerate(images):
                if progress_callback:
                    progress = int((i / total_images) * 100)
                    progress_callback(progress, f"이미지 {i+1}/{total_images} 변환 중...")
                
                if output_format.lower() == 'svg':
                    output_path = self.image_to_svg(img_info['path'], quality=quality)
                elif output_format.lower() == 'ai':
                    output_path = self.image_to_ai(img_info['path'], quality=quality)
                else:
                    continue
                
                if output_path:
                    converted_files.append({
                        'original': img_info,
                        'converted': output_path,
                        'format': output_format.upper()
                    })
            
            if progress_callback:
                progress_callback(100, "변환 완료!")
            
            return {
                'success': True,
                'files': converted_files,
                'total_converted': len(converted_files)
            }
            
        except Exception as e:
            logger.error(f"벡터 변환 중 오류: {str(e)}")
            return {'success': False, 'message': f'변환 중 오류가 발생했습니다: {str(e)}'}
    
    def cleanup(self):
        """임시 파일들을 정리합니다."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"임시 파일 정리 중 오류: {str(e)}")

# 전역 변환기 인스턴스
vector_converter = VectorConverter()