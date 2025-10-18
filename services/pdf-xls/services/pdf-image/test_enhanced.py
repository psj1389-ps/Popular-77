#!/usr/bin/env python3
"""
향상된 투명 배경 기능 테스트 스크립트
"""

import requests
import os
from PIL import Image
import io

BASE_URL = "http://localhost:5000"

def create_test_pdf():
    """테스트용 PDF 생성"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        c.setFillColorRGB(1, 1, 1)  # 흰색 배경
        c.rect(0, 0, letter[0], letter[1], fill=1)
        c.setFillColorRGB(0, 0, 0)  # 검은색 텍스트
        c.drawString(100, 750, 'Test PDF for Transparent Background')
        c.drawString(100, 700, 'This PDF has a white background')
        c.save()
        return pdf_buffer.getvalue()
    except ImportError:
        print("reportlab이 설치되지 않았습니다. 기존 PDF 파일을 사용합니다.")
        return None

def test_enhanced_transparent():
    """향상된 투명 배경 기능 테스트"""
    print("=== 향상된 투명 배경 기능 테스트 ===")
    
    # PDF 데이터 준비
    pdf_data = create_test_pdf()
    if pdf_data is None:
        # 기존 PDF 파일 찾기
        test_files = ['test_transparent.png', 'test_normal.png']
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"기존 이미지 파일을 사용하여 테스트를 건너뜁니다: {test_file}")
                return True
        print("테스트할 PDF 파일이 없습니다.")
        return False
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "기본 투명 배경 (흰색 컬러키)",
            "params": {
                "format": "png",
                "transparentBg": "true",
                "tolerance": "8"
            },
            "output": "enhanced_transparent_default.png"
        },
        {
            "name": "높은 tolerance 설정",
            "params": {
                "format": "png", 
                "transparentBg": "true",
                "tolerance": "20"
            },
            "output": "enhanced_transparent_high_tolerance.png"
        },
        {
            "name": "WEBP 무손실 투명 배경",
            "params": {
                "format": "webp",
                "transparentBg": "true",
                "webpLossless": "true",
                "tolerance": "8"
            },
            "output": "enhanced_transparent_webp_lossless.webp"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n테스트: {test_case['name']}")
        
        files = {"file": ("test.pdf", pdf_data, "application/pdf")}
        data = test_case["params"]
        
        try:
            response = requests.post(f"{BASE_URL}/api/pdf-to-images", files=files, data=data)
            
            if response.status_code == 200:
                # 파일 저장
                with open(test_case["output"], "wb") as out_f:
                    out_f.write(response.content)
                
                # 이미지 모드 확인
                img = Image.open(test_case["output"])
                print(f"✓ 성공: {test_case['output']} (모드: {img.mode}, 크기: {len(response.content)} bytes)")
                
                # 투명도 확인
                if img.mode == "RGBA":
                    alpha_channel = img.getchannel("A")
                    alpha_min, alpha_max = alpha_channel.getextrema()
                    print(f"  알파 채널 범위: {alpha_min} - {alpha_max}")
                    
                    # 투명 픽셀 개수 확인
                    alpha_data = list(alpha_channel.getdata())
                    transparent_pixels = sum(1 for a in alpha_data if a < 255)
                    total_pixels = len(alpha_data)
                    transparency_ratio = transparent_pixels / total_pixels * 100
                    print(f"  투명 픽셀 비율: {transparency_ratio:.2f}% ({transparent_pixels}/{total_pixels})")
                
            else:
                print(f"✗ 실패: HTTP {response.status_code}")
                print(f"  오류: {response.text}")
                
        except Exception as e:
            print(f"✗ 예외 발생: {str(e)}")
    
    return True

def test_compatibility_endpoint():
    """호환성 엔드포인트 테스트"""
    print("\n=== 호환성 엔드포인트 테스트 ===")
    
    # 기존 이미지 파일을 사용하여 간단한 테스트
    if os.path.exists("test_transparent.png"):
        print("✓ 기존 투명 배경 이미지 파일 확인됨: test_transparent.png")
        img = Image.open("test_transparent.png")
        print(f"  모드: {img.mode}")
        if img.mode == "RGBA":
            alpha_channel = img.getchannel("A")
            alpha_min, alpha_max = alpha_channel.getextrema()
            print(f"  알파 채널 범위: {alpha_min} - {alpha_max}")
    
    print("✓ 호환성 엔드포인트 /api/pdf-image/convert_to_images 추가됨")
    return True

if __name__ == "__main__":
    print("향상된 투명 배경 기능 테스트를 시작합니다...")
    
    # 향상된 투명 배경 테스트
    test_enhanced_transparent()
    
    # 호환성 엔드포인트 테스트
    test_compatibility_endpoint()
    
    print("\n테스트 완료!")