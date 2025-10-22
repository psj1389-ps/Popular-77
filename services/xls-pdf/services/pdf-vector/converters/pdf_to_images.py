import os
import fitz
from PIL import Image

def pdf_to_images(pdf_path, out_dir, fmt="png", dpi=144, quality=90, pages_spec=None):
    fmt = fmt.lower()
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)
    doc = fitz.open(pdf_path)
    out_paths = []
    
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = os.path.join(out_dir, f"page-{i}.{fmt}")
        
        if fmt == "png":
            pix.save(out_path)
        else:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if fmt in ("jpg", "jpeg"):
                img.save(out_path, "JPEG", quality=quality, optimize=True)
            elif fmt == "webp":
                img.save(out_path, "WEBP", quality=quality, method=6)
            elif fmt in ("tif", "tiff"):
                img.save(out_path, "TIFF", compression="tiff_lzw")
            else:
                img.save(out_path, fmt.upper())
        
        out_paths.append(out_path)
    
    doc.close()
    return out_paths