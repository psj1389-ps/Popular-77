from PIL import Image
import os
from typing import List, Optional
import io
import tempfile

# Extended format support imports
try:
    import cairosvg
    SVG_SUPPORT = True
except ImportError:
    SVG_SUPPORT = False

try:
    from psd_tools import PSDImage
    PSD_SUPPORT = True
except ImportError:
    PSD_SUPPORT = False

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False

try:
    import rawpy
    import numpy as np
    RAW_SUPPORT = True
except ImportError:
    RAW_SUPPORT = False

def _quality_to_int(q):
    """품질 설정을 정수로 변환"""
    if q is None: 
        return 90
    s = str(q).strip().lower()
    if s.isdigit(): 
        return max(1, min(100, int(s)))
    return {"low": 75, "medium": 85, "high": 95}.get(s, 90)

def _get_supported_formats():
    """지원되는 이미지 형식 목록 (PNG 제외)"""
    formats = ['webp', 'bmp', 'tiff', 'tif', 'gif', 'jpeg', 'jpg']
    
    # 추가 형식 지원 확인
    if SVG_SUPPORT:
        formats.append('svg')
    if PSD_SUPPORT:
        formats.append('psd')
    if HEIC_SUPPORT:
        formats.extend(['heic', 'heif'])
    if RAW_SUPPORT:
        formats.extend(['cr2', 'nef', 'arw', 'dng', 'raf', 'orf', 'rw2'])
    
    return formats

def _is_supported_image(file_input) -> bool:
    """파일이 지원되는 이미지 형식인지 확인
    Args:
        file_input: 파일 경로 문자열 또는 FileStorage 객체
    """
    # FileStorage 객체인 경우 filename 속성 사용
    if hasattr(file_input, 'filename'):
        filename = file_input.filename
    else:
        filename = file_input

    if not filename:
        return False
    
    file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
    supported_formats = _get_supported_formats()
    
    # 확장자 기반 1차 확인
    if file_ext not in supported_formats:
        return False
    
    # 특수 형식 처리
    if file_ext == 'svg' and SVG_SUPPORT:
        return True
    elif file_ext == 'psd' and PSD_SUPPORT:
        return True
    elif file_ext in ['heic', 'heif'] and HEIC_SUPPORT:
        return True
    elif file_ext in ['cr2', 'nef', 'arw', 'dng', 'raf', 'orf', 'rw2'] and RAW_SUPPORT:
        return True
    
    # 일반 이미지 형식 PIL로 확인
    try:
        # file_input이 경로(str)일 때만 Image.open 사용
        if isinstance(file_input, str):
            with Image.open(file_input) as img:
                return img.format.lower() in ['webp', 'bmp', 'tiff', 'gif', 'jpeg']
        else:
            # FileStorage 객체는 확장자만으로 판단
            return file_ext in ['webp', 'bmp', 'tiff', 'tif', 'gif', 'jpeg', 'jpg']
    except Exception:
        return False

def _convert_special_format_to_pil(image_path: str) -> Image.Image:
    """특수 형식 이미지를 PIL Image로 변환"""
    file_ext = os.path.splitext(image_path)[1].lower().lstrip('.')
    
    if file_ext == 'svg' and SVG_SUPPORT:
        # SVG를 PNG로 변환 후 PIL로 로드
        png_data = cairosvg.svg2png(url=image_path)
        return Image.open(io.BytesIO(png_data))
    
    elif file_ext == 'psd' and PSD_SUPPORT:
        # PSD 파일을 PIL Image로 변환
        psd = PSDImage.open(image_path)
        pil_image = psd.composite()
        return pil_image
    
    elif file_ext in ['heic', 'heif'] and HEIC_SUPPORT:
        # HEIC/HEIF는 pillow-heif로 자동 처리됨
        return Image.open(image_path)
    
    elif file_ext in ['cr2', 'nef', 'arw', 'dng', 'raf', 'orf', 'rw2'] and RAW_SUPPORT:
        # RAW 파일을 PIL Image로 변환
        with rawpy.imread(image_path) as raw:
            rgb_array = raw.postprocess()
            return Image.fromarray(rgb_array)
    
    else:
        # 일반 이미지 형식
        return Image.open(image_path)

def image_to_png(
    image_path: str,
    out_dir: str,
    quality: Optional[str] = None,
    resize_factor: float = 1.0,
    transparent_background: bool = False
) -> List[str]:
    """
    이미지 파일을 PNG 형식으로 변환
    
    Args:
        image_path: 입력 이미지 파일 경로
        out_dir: 출력 디렉토리
        quality: PNG 압축 레벨 (low/medium/high 또는 1-9)
        resize_factor: 크기 조절 비율 (기본값: 1.0)
        transparent_background: 투명 배경 사용 여부
    
    Returns:
        변환된 파일 경로 목록
    """
    if not _is_supported_image(image_path):
        raise ValueError(f"지원되지 않는 이미지 형식입니다: {image_path}")
    
    # PNG 압축 레벨 설정 (0-9, 높을수록 더 압축)
    compress_level = _quality_to_compress_level(quality)
    
    # 출력 파일명 생성
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(out_dir, f"{base_name}.png")
    
    try:
        # 특수 형식 처리 또는 일반 이미지 로드
        img = _convert_special_format_to_pil(image_path)
        
        # 투명 배경 처리
        if transparent_background:
            # RGBA 모드로 변환하여 투명도 지원
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
        else:
            # 투명 배경을 사용하지 않는 경우
            if img.mode in ('RGBA', 'LA', 'P'):
                # 투명한 배경을 흰색으로 변환
                if img.mode in ('P', 'LA'):
                    img = img.convert('RGBA')
                
                # 흰색 배경 생성
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])  # 알파 채널을 마스크로 사용
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
        
        # 크기 조절
        if resize_factor != 1.0:
            new_width = int(img.width * resize_factor)
            new_height = int(img.height * resize_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # PNG로 저장
        img.save(out_path, 'PNG', compress_level=compress_level, optimize=True)
        
        return [out_path]
        
    except Exception as e:
        raise RuntimeError(f"이미지 변환 중 오류 발생: {str(e)}")

def _quality_to_compress_level(q):
    """품질 설정을 PNG 압축 레벨로 변환"""
    if q is None: 
        return 6
    s = str(q).strip().lower()
    if s.isdigit(): 
        return max(0, min(9, int(s)))
    return {"low": 3, "medium": 6, "high": 9}.get(s, 6)

def get_image_info(image_path: str) -> dict:
    """
    이미지 파일 정보 반환
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        이미지 정보 딕셔너리
    """
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'has_transparency': img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info
            }
    except Exception as e:
        return {'error': str(e)}