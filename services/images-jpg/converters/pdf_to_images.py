from PIL import Image
import os, fitz
from utils.file_utils import parse_pages

def _parse_hex_color(hex_str: str):
    if not hex_str:
        return (255, 255, 255)
    s = hex_str.strip().lstrip("#")
    if len(s) == 3: s = "".join(ch*2 for ch in s)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

# 투명 제거 유틸 (JPG에서는 사용하지 않지만 호환성 위해 유지)
def _remove_white_to_alpha(img: Image.Image, white_threshold: int = 250) -> Image.Image:
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    datas = img.getdata()
    newData = []
    for item in datas:
        r, g, b, a = item
        if r >= white_threshold and g >= white_threshold and b >= white_threshold:
            newData.append((255, 255, 255, 0))
        else:
            newData.append((r, g, b, a))
    img.putdata(newData)
    return img

# Pixmap을 RGBA로 변환 (WEBP/PNG용이었으나 유지)
def _pix_to_rgba(pix):
    img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
    return img

def _quality_to_int(q):
    if q is None: return 90
    s = str(q).strip().lower()
    if s.isdigit(): return max(1, min(100, int(s)))
    return {"low": 75, "medium": 85, "high": 95}.get(s, 90)

def pdf_to_images(
    pdf_path: str,
    out_dir: str,
    fmt: str = "jpg",  # JPG만 허용
    dpi: int = 144,
    quality=None,
    pages_spec: str | None = None,
    transparent_bg: bool = False,
    transparent_color: str | None = None,
    tolerance: int = 8,
    webp_lossless: bool = True,
    white_threshold: int = 250
):
    # 입력 형식과 무관하게 JPG로 강제
    fmt_in = (fmt or 'jpg').lower()
    fmt = 'jpg'

    q = _quality_to_int(quality)
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)

    doc = fitz.open(pdf_path)
    total = doc.page_count
    pages = parse_pages(pages_spec, total)
    out_paths = []

    for pno in pages:
        page = doc[pno - 1]
        # JPG는 알파 채널을 지원하지 않으므로 alpha=False로 픽스맵 생성
        pix = page.get_pixmap(matrix=mat, alpha=False)

        out_path = os.path.join(out_dir, f"page-{pno}.jpg")

        # 항상 JPEG 저장
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(out_path, "JPEG", quality=q, optimize=True)

        out_paths.append(out_path)

    doc.close()
    return out_paths