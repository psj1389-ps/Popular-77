import os, fitz
from utils.file_utils import parse_pages

def pdf_to_svgs(pdf_path, out_dir, text_as_path=False, zoom=1.0, pages_spec=None, prefix="page"):
    doc = fitz.open(pdf_path)
    total = doc.page_count
    pages = parse_pages(pages_spec, total)
    out_paths = []
    mat = fitz.Matrix(zoom, zoom)
    for p in pages:
        svg = doc[p-1].get_svg_image(matrix=mat, text_as_path=text_as_path)
        out_path = os.path.join(out_dir, f"{prefix}-{p}.svg")
        with open(out_path, "w", encoding="utf-8") as fp:
            fp.write(svg)
        out_paths.append(out_path)
    doc.close()
    return out_paths