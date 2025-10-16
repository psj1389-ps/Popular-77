import os, fitz
from PIL import Image
from utils.file_utils import parse_pages

def pdf_to_images(pdf_path: str, out_dir: str, fmt: str = "png", dpi: int = 144, quality: int = 90, pages_spec: str | None = None):
    fmt = fmt.lower()
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)

    try:
        doc = fitz.open(pdf_path)
        
        # Check if PDF is encrypted or password-protected
        if doc.needs_pass:
            doc.close()
            raise Exception("PDF 파일이 암호로 보호되어 있습니다. 암호가 없는 PDF 파일을 사용해주세요.")
        
        # Check if document is properly opened
        if doc.is_closed:
            raise Exception("PDF 파일을 열 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.")
            
        total = doc.page_count
        if total == 0:
            doc.close()
            raise Exception("PDF 파일에 페이지가 없습니다.")
            
        page_list = parse_pages(pages_spec, total)
    except Exception as e:
        if 'doc' in locals():
            doc.close()
        # Re-raise with more specific error message
        error_msg = str(e)
        if "needs_pass" in error_msg or "encrypted" in error_msg.lower():
            raise Exception("PDF 파일이 암호로 보호되어 있습니다. 암호가 없는 PDF 파일을 사용해주세요.")
        elif "closed" in error_msg.lower():
            raise Exception("PDF 파일을 열 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.")
        else:
            raise Exception(f"PDF 처리 중 오류가 발생했습니다: {error_msg}")

    out_paths = []
    try:
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
    except Exception as e:
        doc.close()
        raise Exception(f"이미지 변환 중 오류가 발생했습니다: {str(e)}")
    finally:
        if not doc.is_closed:
            doc.close()
    
    return out_paths