import os
import fitz
from PIL import Image
from utils.file_utils import parse_pages

def _parse_hex_color(hex_str: str):
    """16진수 색상 문자열을 RGB 튜플로 변환"""
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch*2 for ch in s)
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return (r, g, b)

def _apply_colorkey_rgba(img_rgba: Image.Image, key_rgb=(255, 255, 255), tol=10):
    """RGBA 이미지에서 지정된 색상을 투명하게 만드는 컬러키 처리"""
    # 알파가 전부 255(완전 불투명)라면 컬러키로 배경 투명화 시도
    if img_rgba.getchannel("A").getextrema() == (255, 255):
        r0, g0, b0 = key_rgb
        pixels = img_rgba.getdata()
        out = []
        for (r, g, b, a) in pixels:
            if abs(r - r0) <= tol and abs(g - g0) <= tol and abs(b - b0) <= tol:
                out.append((r, g, b, 0))  # 투명하게 만들기
            else:
                out.append((r, g, b, a))
        img_rgba.putdata(out)
    return img_rgba

def _quality_to_int(q):
    """품질 파라미터를 정수로 변환"""
    if q is None:
        return 90
    s = str(q).strip().lower()
    if s.isdigit():
        return max(1, min(100, int(s)))
    return {"low": 75, "medium": 85, "high": 95}.get(s, 90)

def pdf_to_images(
    pdf_path: str,
    out_dir: str,
    fmt: str = "png",
    dpi: int = 144,
    quality: int | str | None = 90,
    pages_spec: str | None = None,
    transparent_bg: bool = False,
    transparent_color: str | None = None,
    tolerance: int = 8,
    webp_lossless: bool = True
):
    """
    PDF를 이미지로 변환하는 함수
    
    Args:
        pdf_path: PDF 파일 경로
        out_dir: 출력 디렉토리
        fmt: 출력 형식 (png, jpg, webp, tiff, bmp, gif)
        dpi: 해상도
        quality: 품질 (1-100 또는 low/medium/high)
        pages_spec: 페이지 범위 ("1-3,5" 형식)
        transparent_bg: 투명 배경 사용 여부
        transparent_color: 투명화할 색상 (16진수)
        tolerance: 색상 허용 오차
        webp_lossless: WEBP 무손실 압축 사용 여부
    """
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
        # 투명 요청 시 alpha=True 렌더링
        use_alpha = transparent_bg and fmt in ("png", "webp")
        pix = page.get_pixmap(matrix=mat, alpha=use_alpha)

        out_path = os.path.join(out_dir, f"page-{pno}.{fmt}")

        if fmt == "png":
            if use_alpha:
                # PNG 투명
                img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
                # 컬러키 보정(기본은 흰색)
                key_rgb = _parse_hex_color(transparent_color) if transparent_color else (255, 255, 255)
                img = _apply_colorkey_rgba(img, key_rgb=key_rgb, tol=tolerance)
                img.save(out_path, "PNG", optimize=True)
            else:
                pix.save(out_path)  # 불투명 PNG
        elif fmt in ("jpg", "jpeg"):
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(out_path, "JPEG", quality=q, optimize=True)
        elif fmt == "webp":
            # WEBP는 RGBA 지원. 투명 사용 시 RGBA, 아니면 RGB
            mode = "RGBA" if use_alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            if use_alpha:
                key_rgb = _parse_hex_color(transparent_color) if transparent_color else (255, 255, 255)
                img = img.convert("RGBA")
                img = _apply_colorkey_rgba(img, key_rgb=key_rgb, tol=tolerance)
            # lossless는 투명 가장자리에 유리(용량 ↑)
            if webp_lossless and use_alpha:
                img.save(out_path, "WEBP", lossless=True, method=6)
            else:
                img.save(out_path, "WEBP", quality=q, method=6)
        elif fmt in ("tif", "tiff"):
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(out_path, "TIFF", compression="tiff_lzw")
        elif fmt in ("bmp", "gif"):
            # 알파 미지원 포맷. RGB로 저장
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(out_path, fmt.upper())
        else:
            # 그 외 포맷은 Pillow가 아는 선에서 저장 시도
            mode = "RGBA" if use_alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            img.save(out_path, fmt.upper())

        out_paths.append(out_path)

    doc.close()
    return out_paths