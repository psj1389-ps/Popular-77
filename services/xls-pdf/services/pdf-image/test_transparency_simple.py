#!/usr/bin/env python3
"""
PDF-Image 서비스 투명 처리 간단 테스트
"""
import requests
import os
from PIL import Image

def test_transparency():
    """투명 처리 기능 테스트"""
    print("🧪 PDF-Image 투명 처리 테스트...")
    
    # 서버 URL
    url = "http://localhost:5000/api/pdf-to-images"
    
    # 기존 테스트 파일 사용
    test_pdf = "test_sample.pdf"
    if not os.path.exists(test_pdf):
        print("❌ test_sample.pdf 파일을 찾을 수 없습니다.")
        return False
    
    print(f"📄 테스트 PDF 파일: {test_pdf}")
    
    # PNG 투명 처리 테스트
    print("\n🔍 PNG 투명 처리 테스트")
    try:
        with open(test_pdf, 'rb') as f:
            files = {'file': f}
            data = {
                "format": "png",
                "transparentBg": "true",
                "whiteThreshold": "250"
            }
            response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            # 응답 파일 저장
            with open("test_png_transparent_new.png", 'wb') as f:
                f.write(response.content)
            
            # 이미지 분석
            img = Image.open("test_png_transparent_new.png")
            print(f"   ✅ 변환 성공: {img.size}, 모드: {img.mode}")
            
            # 투명도 확인
            if img.mode == 'RGBA':
                alpha_channel = img.getchannel('A')
                transparent_pixels = sum(1 for pixel in alpha_channel.getdata() if pixel == 0)
                total_pixels = img.width * img.height
                transparency_ratio = (transparent_pixels / total_pixels) * 100
                print(f"   📊 투명 픽셀 비율: {transparency_ratio:.1f}%")
                
                if transparency_ratio > 0:
                    print(f"   🎉 PNG 투명 처리 성공!")
                    return True
                else:
                    print(f"   ❌ PNG 투명 픽셀이 없습니다.")
                    return False
            else:
                print(f"   ❌ PNG RGBA 모드가 아닙니다.")
                return False
        else:
            print(f"   ❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ 요청 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PDF-Image 투명 처리 간단 테스트")
    print("=" * 40)
    
    success = test_transparency()
    
    print("=" * 40)
    if success:
        print("🎉 투명 처리 테스트 성공!")
    else:
        print("❌ 투명 처리 테스트 실패")