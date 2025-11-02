"""
이미지를 GIF로 변환하는 모듈
"""

import os
import io
from PIL import Image, ImageSequence
import imageio
from typing import List, Tuple, Optional, Union


def _is_supported_image(file_path: str) -> bool:
    """지원되는 이미지 파일인지 확인"""
    try:
        with Image.open(file_path) as img:
            return True
    except Exception:
        return False


def _get_supported_formats() -> List[str]:
    """지원되는 이미지 포맷 목록 반환"""
    return ['JPEG', 'JPG', 'PNG', 'BMP', 'TIFF', 'TIF', 'WEBP', 'ICO', 'GIF']


def get_image_info(file_path: str) -> dict:
    """이미지 파일 정보 반환"""
    try:
        with Image.open(file_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
    except Exception as e:
        return {'error': str(e)}


def images_to_gif(
    image_paths: List[str],
    output_path: str,
    duration: float = 0.5,
    loop: int = 0,
    quality: str = "medium",
    resize_factor: float = 1.0
) -> Tuple[bool, str]:
    """
    여러 이미지를 GIF 애니메이션으로 변환
    
    Args:
        image_paths: 이미지 파일 경로 리스트
        output_path: 출력 GIF 파일 경로
        duration: 프레임 간 지속시간 (초)
        loop: 반복 횟수 (0은 무한반복)
        quality: 품질 설정 ('low', 'medium', 'high')
        resize_factor: 크기 조정 비율
    
    Returns:
        (성공여부, 메시지)
    """
    try:
        if not image_paths:
            return False, "이미지 파일이 없습니다."
        
        # 품질 설정에 따른 최적화 옵션
        optimize_options = {
            'low': {'optimize': True, 'colors': 64},
            'medium': {'optimize': True, 'colors': 128},
            'high': {'optimize': True, 'colors': 256}
        }
        
        options = optimize_options.get(quality, optimize_options['medium'])
        
        images = []
        target_size = None
        
        # 이미지 로드 및 전처리
        for i, img_path in enumerate(image_paths):
            if not _is_supported_image(img_path):
                continue
                
            with Image.open(img_path) as img:
                # RGBA로 변환 (투명도 지원)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 첫 번째 이미지 크기를 기준으로 설정
                if target_size is None:
                    target_size = img.size
                    if resize_factor != 1.0:
                        target_size = (
                            int(target_size[0] * resize_factor),
                            int(target_size[1] * resize_factor)
                        )
                
                # 크기 조정
                if img.size != target_size:
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # P 모드로 변환 (GIF 최적화)
                img = img.convert('P', palette=Image.ADAPTIVE, colors=options['colors'])
                images.append(img.copy())
        
        if not images:
            return False, "변환 가능한 이미지가 없습니다."
        
        # GIF 저장
        images[0].save(
            output_path,
            format='GIF',
            save_all=True,
            append_images=images[1:],
            duration=int(duration * 1000),  # 밀리초로 변환
            loop=loop,
            optimize=options['optimize']
        )
        
        return True, f"GIF 생성 완료: {len(images)}개 프레임"
        
    except Exception as e:
        return False, f"GIF 변환 중 오류 발생: {str(e)}"


def image_to_gif(
    input_path: str,
    output_path: str,
    quality: str = "medium",
    resize_factor: float = 1.0
) -> Tuple[bool, str]:
    """
    단일 이미지를 GIF로 변환 (정적 GIF)
    
    Args:
        input_path: 입력 이미지 파일 경로
        output_path: 출력 GIF 파일 경로
        quality: 품질 설정
        resize_factor: 크기 조정 비율
    
    Returns:
        (성공여부, 메시지)
    """
    try:
        if not _is_supported_image(input_path):
            return False, "지원되지 않는 이미지 형식입니다."
        
        # 품질 설정
        optimize_options = {
            'low': {'optimize': True, 'colors': 64},
            'medium': {'optimize': True, 'colors': 128},
            'high': {'optimize': True, 'colors': 256}
        }
        
        options = optimize_options.get(quality, optimize_options['medium'])
        
        with Image.open(input_path) as img:
            # RGBA로 변환
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 크기 조정
            if resize_factor != 1.0:
                new_size = (
                    int(img.size[0] * resize_factor),
                    int(img.size[1] * resize_factor)
                )
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # P 모드로 변환하여 GIF 저장
            img = img.convert('P', palette=Image.ADAPTIVE, colors=options['colors'])
            img.save(output_path, format='GIF', optimize=options['optimize'])
        
        return True, "GIF 변환 완료"
        
    except Exception as e:
        return False, f"GIF 변환 중 오류 발생: {str(e)}"


def extract_gif_frames(
    gif_path: str,
    output_dir: str,
    format: str = 'PNG'
) -> Tuple[bool, str, List[str]]:
    """
    GIF에서 개별 프레임을 추출
    
    Args:
        gif_path: GIF 파일 경로
        output_dir: 출력 디렉토리
        format: 출력 이미지 포맷
    
    Returns:
        (성공여부, 메시지, 추출된 파일 경로 리스트)
    """
    try:
        extracted_files = []
        
        with Image.open(gif_path) as gif:
            if not gif.is_animated:
                return False, "애니메이션 GIF가 아닙니다.", []
            
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(gif_path))[0]
            
            for i, frame in enumerate(ImageSequence.Iterator(gif)):
                # RGBA로 변환
                frame = frame.convert('RGBA')
                
                # 파일명 생성
                frame_filename = f"{base_name}_frame_{i:03d}.{format.lower()}"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # 프레임 저장
                frame.save(frame_path, format=format)
                extracted_files.append(frame_path)
        
        return True, f"{len(extracted_files)}개 프레임 추출 완료", extracted_files
        
    except Exception as e:
        return False, f"프레임 추출 중 오류 발생: {str(e)}", []