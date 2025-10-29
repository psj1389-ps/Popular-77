"""
Image to WEBP Converter Module
Handles conversion of various image formats to WEBP
"""

from PIL import Image, ImageOps
import os
import io
from typing import Tuple, Optional, List

def _get_supported_formats() -> List[str]:
    """Get list of supported input image formats"""
    return ['JPEG', 'JPG', 'PNG', 'BMP', 'TIFF', 'GIF', 'SVG', 'PSD', 'HEIC', 'RAW']

def get_image_info(image_path: str) -> dict:
    """Get basic information about an image file"""
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height
            }
    except Exception as e:
        return {'error': str(e)}

def image_to_webp(input_path: str, output_path: str, quality: int = 80, resize_factor: float = 1.0) -> bool:
    """
    Convert an image to WEBP format
    
    Args:
        input_path: Path to input image
        output_path: Path for output WEBP file
        quality: WEBP quality (1-100)
        resize_factor: Factor to resize image (0.1-3.0)
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Open and process the image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (WEBP doesn't support all modes)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Keep transparency for RGBA
                if img.mode == 'RGBA':
                    pass  # Keep as is
                else:
                    img = img.convert('RGBA')
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Apply resize if needed
            if resize_factor != 1.0:
                new_width = int(img.width * resize_factor)
                new_height = int(img.height * resize_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Auto-orient the image based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save as WEBP
            save_kwargs = {
                'format': 'WEBP',
                'quality': quality,
                'optimize': True
            }
            
            # Enable lossless for high quality settings
            if quality >= 95:
                save_kwargs['lossless'] = True
                save_kwargs.pop('quality')  # Remove quality for lossless
            
            img.save(output_path, **save_kwargs)
            return True
            
    except Exception as e:
        print(f"Error converting {input_path} to WEBP: {str(e)}")
        return False