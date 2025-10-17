#!/usr/bin/env python3
"""
흰색 배경 PDF로 투명 처리 테스트
"""
import requests
from PIL import Image

def test_white_bg_transparency():
    """흰색 배경 PDF로 투명 처리 테스트"""
    print("🧪 흰색 배경 PDF 투명 처리 테스트...")
    
    # 서버 URL
    url = "http://localhost:5000/api/pdf-to-images"
    
    # 흰색 배경 PDF 파일
    pdf_file = "test_white_background.pdf"
    
    print(f"📄 테스트 PDF 파일: {pdf_file}")
    
    # PNG 투명 처리 테스트
    print("\n🔍 PNG 투명 처리 테스트")
    try:
        with open(pdf_file, 'rb') as f:
            files = {'file': f}
            data = {
                "format": "png",
                "transparentBg": "true",
                "whiteThreshold": "250"
            }
            response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            # 응답 파일 저장
            output_file = "test_white_bg_transparent.png"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            # 이미지 분석
            img = Image.open(output_file)
            print(f"   ✅ 변환 성공: {img.size}, 모드: {img.mode}")
            
            # 투명도 확인
            if img.mode == 'RGBA':
                alpha_channel = img.getchannel('A')
                alpha_data = list(alpha_channel.getdata())
                
                transparent_pixels = sum(1 for p in alpha_data if p == 0)
                semi_transparent = sum(1 for p in alpha_data if 0 < p < 255)
                opaque_pixels = sum(1 for p in alpha_data if p == 255)
                total_pixels = len(alpha_data)
                
                print(f"   📊 투명 픽셀: {transparent_pixels} ({(transparent_pixels/total_pixels)*100:.1f}%)")
                print(f"   📊 반투명 픽셀: {semi_transparent} ({(semi_transparent/total_pixels)*100:.1f}%)")
                print(f"   📊 불투명 픽셀: {opaque_pixels} ({(opaque_pixels/total_pixels)*100:.1f}%)")
                
                if transparent_pixels > 0:
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
    print("🚀 흰색 배경 PDF 투명 처리 테스트")
    print("=" * 40)
    
    success = test_white_bg_transparency()
    
    print("=" * 40)
    if success:
        print("🎉 투명 처리 테스트 성공!")
    else:
        print("❌ 투명 처리 테스트 실패")