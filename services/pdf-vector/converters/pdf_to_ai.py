import os, fitz
from utils.file_utils import parse_pages

def save_pdf_as_ai(pdf_path, out_ai_path):
    doc = fitz.open(pdf_path)
    doc.save(out_ai_path, garbage=4, deflate=True, linear=True)  # AI 호환 PDF
    doc.close()
    return out_ai_path

def split_pdf_to_ai_pages(pdf_path, out_dir, pages_spec=None, prefix="page"):
    doc = fitz.open(pdf_path)
    total = doc.page_count
    pages = parse_pages(pages_spec, total)
    out_paths = []
    for p in pages:
        single = fitz.open()
        single.insert_pdf(doc, from_page=p-1, to_page=p-1)
        out_ai = os.path.join(out_dir, f"{prefix}-{p}.ai")
        single.save(out_ai, garbage=4, deflate=True, linear=True)
        single.close()
        out_paths.append(out_ai)
    doc.close()
    return out_paths