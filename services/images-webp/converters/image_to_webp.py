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

def image_to_webp(input_path: str, output_dir: str, quality: str = 'medium', resize_factor: float = 1.0, preserve_transparency: bool = False) -> List[str]:
    """
    Convert an image to WEBP format
    
    Args:
        input_path: Path to input image
        output_dir: Directory for output WEBP file
        quality: WEBP quality ('low', 'medium', 'high' or 1-100)
        resize_factor: Factor to resize image (0.1-3.0)
        preserve_transparency: Whether to preserve transparency (True) or use white background (False)
    
    Returns:
        List[str]: List of output file paths if successful, empty list otherwise
    """
    try:
        # Convert quality string to numeric value
        if isinstance(quality, str):
            quality_map = {'low': 60, 'medium': 80, 'high': 95}
            numeric_quality = quality_map.get(quality.lower(), 80)
        else:
            numeric_quality = int(quality)
        
        # Ensure quality is in valid range
        numeric_quality = max(1, min(100, numeric_quality))
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.webp")
        
        # Open and process the image
        with Image.open(input_path) as img:
            # Handle transparency based on preserve_transparency setting
            if preserve_transparency and img.mode in ('RGBA', 'LA', 'P'):
                # Preserve transparency - convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            else:
                # Remove transparency - convert to RGB with white background
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
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
            os.makedirs(output_dir, exist_ok=True)
            
            # Save as WEBP
            save_kwargs = {
                'format': 'WEBP',
                'quality': numeric_quality,
                'optimize': True
            }
            
            # Enable lossless for high quality settings
            if numeric_quality >= 95:
                save_kwargs['lossless'] = True
                save_kwargs.pop('quality')  # Remove quality for lossless
            
            img.save(output_path, **save_kwargs)
            return [output_path]
            
    except Exception as e:
        print(f"Error converting {input_path} to WEBP: {str(e)}")
        return []