#!/usr/bin/env python3
"""
흰색 배경이 있는 테스트 PDF 생성
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, white

def create_white_background_pdf():
    """흰색 배경과 검은 텍스트가 있는 PDF 생성"""
    pdf_path = "test_white_background.pdf"
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # 흰색 배경 그리기
    c.setFillColor(white)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # 검은색 텍스트 추가
    c.setFillColor(black)
    c.setFont("Helvetica", 24)
    c.drawString(100, height - 100, "Test Document")
    c.drawString(100, height - 150, "White Background Test")
    
    c.setFont("Helvetica", 16)
    c.drawString(100, height - 200, "This PDF has a white background")
    c.drawString(100, height - 230, "that should become transparent")
    c.drawString(100, height - 260, "when transparency is enabled.")
    
    # 검은색 사각형 추가 (투명하지 않아야 함)
    c.setFillColor(black)
    c.rect(100, height - 350, 200, 50, fill=1, stroke=0)
    
    # 흰색 텍스트 (사각형 위에)
    c.setFillColor(white)
    c.drawString(120, height - 335, "Black Rectangle")
    
    c.save()
    print(f"✅ 흰색 배경 PDF 생성: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_white_background_pdf()