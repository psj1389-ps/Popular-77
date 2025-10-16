from PIL import Image
import os, fitz
from utils.file_utils import parse_pages

def _parse_hex_color(hex_str: str):
    if not hex_str:
        return (255, 255, 255)
    s = hex_str.strip().lstrip("#")
    if len(s) == 3: s = "".join(ch*2 for ch in s)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

def _apply_colorkey_rgba(img: Image.Image, key_rgb=(255, 255, 255), tol=10):
    # 알파가 전부 255(완전 불투명)일 때만 컬러키 투명화 시도
    if img.getchannel("A").getextrema() == (255, 255):
        r0, g0, b0 = key_rgb
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if abs(r - r0) <= tol and abs(g - g0) <= tol and abs(b - b0) <= tol:
                    px[x, y] = (r, g, b, 0)
    return img

def _remove_white_to_alpha(rgba: Image.Image, white_threshold: int = 250) -> Image.Image:
    """PDF-PNG 방식의 밝기 기반 투명 처리 - 더 효과적인 배경 제거"""
    # 밝은 영역(종이 배경)을 투명으로 처리
    gray = rgba.convert("L")
    alpha_mask = gray.point(lambda p: 0 if p >= white_threshold else 255)
    out = rgba.copy()
    out.putalpha(alpha_mask)
    return out

def _quality_to_int(q):
    if q is None: return 90
    s = str(q).strip().lower()
    if s.isdigit(): return max(1, min(100, int(s)))
    return {"low": 75, "medium": 85, "high": 95}.get(s, 90)

def pdf_to_images(
    pdf_path: str,
    out_dir: str,
    fmt: str = "png",
    dpi: int = 144,
    quality=None,
    pages_spec: str | None = None,
    transparent_bg: bool = False,
    transparent_color: str | None = None,
    tolerance: int = 8,
    webp_lossless: bool = True,
    white_threshold: int = 250
):
    fmt = fmt.lower()
    q = _quality_to_int(quality)
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)

    doc = fitz.open(pdf_path)
    total = doc.page_count
    pages = parse_pages(pages_spec, total)
    out_paths = []

    for pno in pages:
        page = doc[pno - 1]
        use_alpha = transparent_bg and fmt in ("png", "webp")
        pix = page.get_pixmap(matrix=mat, alpha=use_alpha)

        out_path = os.path.join(out_dir, f"page-{pno}.{fmt}")

        if fmt == "png":
            if use_alpha:
                # PyMuPDF 알파 렌더링 + 향상된 투명 처리
                img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
                
                # PDF-PNG 방식의 밝기 기반 투명 처리 (더 효과적)
                if transparent_color or white_threshold < 255:
                    img = _remove_white_to_alpha(img, white_threshold)
                else:
                    # 기존 컬러키 방식도 유지 (호환성)
                    img = _apply_colorkey_rgba(img, _parse_hex_color(transparent_color), tolerance)
                
                img.save(out_path, "PNG", optimize=True)
            else:
                pix.save(out_path)
        elif fmt in ("jpg", "jpeg"):
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(out_path, "JPEG", quality=q, optimize=True)
        elif fmt == "webp":
            mode = "RGBA" if use_alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            if use_alpha:
                img = img.convert("RGBA")
                
                # PDF-PNG 방식의 밝기 기반 투명 처리 (더 효과적)
                if transparent_color or white_threshold < 255:
                    img = _remove_white_to_alpha(img, white_threshold)
                else:
                    # 기존 컬러키 방식도 유지 (호환성)
                    img = _apply_colorkey_rgba(img, _parse_hex_color(transparent_color), tolerance)
                
                if webp_lossless:
                    img.save(out_path, "WEBP", lossless=True, method=6)
                else:
                    img.save(out_path, "WEBP", quality=q, method=6)
            else:
                img.save(out_path, "WEBP", quality=q, method=6)
        elif fmt in ("tif", "tiff"):
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(out_path, "TIFF", compression="tiff_lzw")
        elif fmt in ("bmp", "gif"):
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(out_path, fmt.upper())
        else:
            mode = "RGBA" if use_alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            img.save(out_path, fmt.upper())

        out_paths.append(out_path)

    doc.close()
    return out_paths