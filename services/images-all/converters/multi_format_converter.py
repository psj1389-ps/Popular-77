"""
Multi-Format Image Converter Module
Handles conversion between various image formats (JPG, PNG, WEBP, BMP, TIFF, SVG, PSD, HEIC, RAW)
"""

from PIL import Image, ImageOps
import os
import io
from typing import Tuple, Optional, List, Dict
import cairosvg
from pillow_heif import register_heif_opener
import rawpy
import xml.etree.ElementTree as ET
import base64

# Register HEIF opener for HEIC support
register_heif_opener()

class MultiFormatConverter:
    """Multi-format image converter supporting various input and output formats"""
    
    # Supported formats mapping
    SUPPORTED_FORMATS = {
        'input': ['JPEG', 'JPG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'SVG', 'PSD', 'HEIC', 'RAW'],
        'output': ['JPEG', 'JPG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'SVG', 'PSD', 'HEIC', 'RAW']
    }
    
    # Format extensions mapping
    FORMAT_EXTENSIONS = {
        'JPEG': '.jpg',
        'JPG': '.jpg', 
        'PNG': '.png',
        'WEBP': '.webp',
        'BMP': '.bmp',
        'TIFF': '.tiff',
        'SVG': '.svg',
        'PSD': '.psd',
        'HEIC': '.heic',
        'RAW': '.dng'
    }
    
    # Quality settings for different formats
    QUALITY_SETTINGS = {
        'low': {'JPEG': 60, 'WEBP': 60, 'PNG': None, 'BMP': None, 'TIFF': None, 'SVG': None, 'PSD': None, 'HEIC': 60, 'RAW': None},
        'medium': {'JPEG': 80, 'WEBP': 80, 'PNG': None, 'BMP': None, 'TIFF': None, 'SVG': None, 'PSD': None, 'HEIC': 80, 'RAW': None},
        'high': {'JPEG': 95, 'WEBP': 95, 'PNG': None, 'BMP': None, 'TIFF': None, 'SVG': None, 'PSD': None, 'HEIC': 95, 'RAW': None}
    }
    
    def __init__(self):
        """Initialize the converter"""
        pass
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported input and output formats"""
        return self.SUPPORTED_FORMATS.copy()
    
    def get_image_info(self, image_path: str) -> Dict:
        """Get basic information about an image file"""
        try:
            # Handle RAW files
            if self._is_raw_file(image_path):
                with rawpy.imread(image_path) as raw:
                    rgb = raw.postprocess()
                    return {
                        'format': 'RAW',
                        'mode': 'RGB',
                        'size': (rgb.shape[1], rgb.shape[0]),
                        'width': rgb.shape[1],
                        'height': rgb.shape[0]
                    }
            
            # Handle SVG files
            if image_path.lower().endswith('.svg'):
                return {
                    'format': 'SVG',
                    'mode': 'RGBA',
                    'size': (None, None),  # SVG is vector-based
                    'width': None,
                    'height': None
                }
            
            # Handle other formats with PIL
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
    
    def convert_image(self, input_path: str, output_dir: str, output_format: str = 'WEBP', 
                     quality: str = 'medium', resize_factor: float = 1.0, 
                     preserve_transparency: bool = False) -> List[str]:
        """
        Convert an image to specified format
        
        Args:
            input_path: Path to input image
            output_dir: Directory for output file
            output_format: Target format ('JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF')
            quality: Quality setting ('low', 'medium', 'high' or 1-100)
            resize_factor: Factor to resize image (0.1-3.0)
            preserve_transparency: Whether to preserve transparency
        
        Returns:
            List[str]: List of output file paths if successful, empty list otherwise
        """
        try:
            # Validate output format
            output_format = output_format.upper()
            if output_format not in self.SUPPORTED_FORMATS['output']:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            extension = self.FORMAT_EXTENSIONS[output_format]
            output_path = os.path.join(output_dir, f"{base_name}{extension}")
            
            # Load image based on input format
            img = self._load_image(input_path)
            
            # Process transparency
            img = self._process_transparency(img, output_format, preserve_transparency)
            
            # Apply resize if needed
            if resize_factor != 1.0:
                new_width = int(img.width * resize_factor)
                new_height = int(img.height * resize_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Auto-orient the image based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Save with format-specific settings
            self._save_image(img, output_path, output_format, quality)
            
            return [output_path]
            
        except Exception as e:
            print(f"Error converting {input_path} to {output_format}: {str(e)}")
            return []
    
    def _load_image(self, input_path: str) -> Image.Image:
        """Load image from various formats"""
        file_ext = os.path.splitext(input_path)[1].lower()
        
        # Handle RAW files
        if self._is_raw_file(input_path):
            with rawpy.imread(input_path) as raw:
                rgb = raw.postprocess()
                return Image.fromarray(rgb)
        
        # Handle SVG files
        if file_ext == '.svg':
            # Convert SVG to PNG first, then load as PIL Image
            png_data = cairosvg.svg2png(url=input_path)
            return Image.open(io.BytesIO(png_data))
        
        # Handle other formats with PIL
        return Image.open(input_path)
    
    def _process_transparency(self, img: Image.Image, output_format: str, preserve_transparency: bool) -> Image.Image:
        """Process transparency based on output format and settings"""
        # Formats that support transparency
        transparency_formats = ['PNG', 'WEBP']
        
        if preserve_transparency and output_format in transparency_formats:
            # Preserve transparency - convert to RGBA if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            elif img.mode not in ('RGBA',):
                # Add alpha channel if not present
                img = img.convert('RGBA')
        else:
            # Remove transparency - convert to RGB with white background
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
        
        return img
    
    def _save_image(self, img: Image.Image, output_path: str, output_format: str, quality: str):
        """Save image with format-specific settings"""
        save_kwargs = {'format': output_format}
        
        # Get quality setting
        if isinstance(quality, str):
            quality_value = self.QUALITY_SETTINGS.get(quality.lower(), self.QUALITY_SETTINGS['medium'])[output_format]
        else:
            quality_value = int(quality) if output_format in ['JPEG', 'WEBP', 'HEIC'] else None
        
        # Format-specific settings
        if output_format == 'JPEG':
            if quality_value:
                save_kwargs['quality'] = max(1, min(100, quality_value))
            save_kwargs['optimize'] = True
            
        elif output_format == 'WEBP':
            if quality_value:
                if quality_value >= 95:
                    save_kwargs['lossless'] = True
                else:
                    save_kwargs['quality'] = max(1, min(100, quality_value))
            save_kwargs['optimize'] = True
            
        elif output_format == 'PNG':
            save_kwargs['optimize'] = True
            
        elif output_format == 'TIFF':
            save_kwargs['compression'] = 'lzw'
            
        elif output_format == 'HEIC':
            if quality_value:
                save_kwargs['quality'] = max(1, min(100, quality_value))
            save_kwargs['optimize'] = True
            
        elif output_format == 'SVG':
            # Convert PIL Image to SVG
            self._save_as_svg(img, output_path)
            return
            
        elif output_format == 'PSD':
            # For PSD, we'll save as TIFF with layers (best approximation)
            save_kwargs['format'] = 'TIFF'
            save_kwargs['compression'] = 'lzw'
            
        elif output_format == 'RAW':
            # For RAW output, we'll save as DNG (Adobe's open RAW format)
            # Since PIL doesn't support RAW output directly, we'll save as TIFF
            save_kwargs['format'] = 'TIFF'
            save_kwargs['compression'] = 'lzw'
        
        # Save the image
        img.save(output_path, **save_kwargs)
    
    def _save_as_svg(self, img: Image.Image, output_path: str):
        """Convert PIL Image to SVG format"""
        # Convert image to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Create SVG with embedded image
        width, height = img.size
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
     width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <image x="0" y="0" width="{width}" height="{height}" 
           xlink:href="data:image/png;base64,{img_data}"/>
</svg>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
    
    def _is_raw_file(self, file_path: str) -> bool:
        """Check if file is a RAW format"""
        raw_extensions = ['.cr2', '.nef', '.arw', '.dng', '.raf', '.orf', '.rw2', '.raw']
        return any(file_path.lower().endswith(ext) for ext in raw_extensions)

# Convenience functions for backward compatibility
def convert_image_format(input_path: str, output_dir: str, output_format: str = 'WEBP', 
                        quality: str = 'medium', resize_factor: float = 1.0, 
                        preserve_transparency: bool = False) -> List[str]:
    """
    Convert an image to specified format (convenience function)
    """
    converter = MultiFormatConverter()
    return converter.convert_image(input_path, output_dir, output_format, quality, resize_factor, preserve_transparency)

def get_supported_formats() -> Dict[str, List[str]]:
    """Get supported formats (convenience function)"""
    converter = MultiFormatConverter()
    return converter.get_supported_formats()

def get_image_info(image_path: str) -> Dict:
    """Get image info (convenience function)"""
    converter = MultiFormatConverter()
    return converter.get_image_info(image_path)