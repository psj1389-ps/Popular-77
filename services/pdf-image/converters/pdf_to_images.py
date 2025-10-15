import os, fitz
from PIL import Image
from utils.file_utils import parse_pages

def pdf_to_images(pdf_path: str, out_dir: str, fmt: str = "png", dpi: int = 144, quality: int = 90, pages_spec: str | None = None):
    fmt = fmt.lower()
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)

    doc = fitz.open(pdf_path)
    total = doc.page_count
    page_list = parse_pages(pages_spec, total)

    out_paths = []
    for pno in page_list:
        page = doc[pno - 1]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = os.path.join(out_dir, f"page-{pno}.{fmt}")
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