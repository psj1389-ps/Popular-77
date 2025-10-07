import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_pdf_with_graphics():
    """펭귄 캐릭터와 말풍선이 있는 테스트 PDF 생성"""
    # PDF 문서 생성
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 크기
    
    # 제목 텍스트 추가
    title_text = "깃과 깃허브가\n처음인 당신에게"
    page.insert_text((200, 100), title_text, fontsize=24, color=(0, 0, 0))
    
    # 말풍선 그리기 (둥근 사각형)
    bubble_rect = fitz.Rect(50, 200, 300, 280)
    page.draw_rect(bubble_rect, color=(0, 0, 0), width=2)
    
    # 말풍선 안의 텍스트
    bubble_text = "Git & Github 소개"
    page.insert_text((70, 240), bubble_text, fontsize=16, color=(0, 0, 0))
    
    # 간단한 펭귄 모양 그리기 (원과 타원으로)
    # 몸통 (타원)
    body_rect = fitz.Rect(400, 180, 480, 300)
    page.draw_oval(body_rect, color=(0, 0, 0), fill=(135, 206, 235))  # 하늘색
    
    # 머리 (원)
    head_rect = fitz.Rect(420, 150, 460, 190)
    page.draw_oval(head_rect, color=(0, 0, 0), fill=(255, 255, 255))  # 흰색
    
    # 눈 (작은 원들)
    eye1_rect = fitz.Rect(430, 160, 435, 165)
    eye2_rect = fitz.Rect(445, 160, 450, 165)
    page.draw_oval(eye1_rect, color=(0, 0, 0), fill=(0, 0, 0))
    page.draw_oval(eye2_rect, color=(0, 0, 0), fill=(0, 0, 0))
    
    # 부리 (삼각형 모양)
    beak_points = [fitz.Point(440, 170), fitz.Point(435, 175), fitz.Point(445, 175)]
    page.draw_polyline(beak_points, color=(255, 165, 0), fill=(255, 165, 0))  # 주황색
    
    # 두 번째 페이지 추가
    page2 = doc.new_page(width=595, height=842)
    
    # 두 번째 페이지 내용
    page2.insert_text((50, 100), "이 강의를 만든 이유", fontsize=20, color=(0, 0, 0))
    
    # 설명 텍스트
    explanation = """개발자라면 깃(Git)과 깃허브(Github) 정도는 필수적으로 알고 있어야 한다. 라는 말
이 있다. 필자 또한 이 말에 아는 정도 공감한다. 오늘날 소프트웨어 개발 프로젝트를
진행하는 팀 또는 개인 중 대다수가 프로젝트 버전 관리 시스템으로 깃을 사용하고 있
기 때문이다."""
    
    page2.insert_text((50, 150), explanation, fontsize=12, color=(0, 0, 0))
    
    # 또 다른 말풍선
    bubble2_rect = fitz.Rect(50, 350, 250, 420)
    page2.draw_rect(bubble2_rect, color=(0, 0, 0), width=2)
    page2.insert_text((70, 385), "이 강의를 만든 이유", fontsize=14, color=(0, 0, 0))
    
    # 작은 펭귄 캐릭터
    small_body = fitz.Rect(300, 350, 350, 420)
    page2.draw_oval(small_body, color=(0, 0, 0), fill=(135, 206, 235))
    
    small_head = fitz.Rect(315, 330, 335, 350)
    page2.draw_oval(small_head, color=(0, 0, 0), fill=(255, 255, 255))
    
    # PDF 저장
    output_path = "test_penguin_document.pdf"
    doc.save(output_path)
    doc.close()
    
    print(f"테스트 PDF가 생성되었습니다: {output_path}")
    return output_path

if __name__ == "__main__":
    create_test_pdf_with_graphics()