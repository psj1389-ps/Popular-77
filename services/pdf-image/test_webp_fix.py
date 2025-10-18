#!/usr/bin/env python3
"""
WEBP 투명 처리 문제 해결 테스트
"""
import requests
import os
from PIL import Image

def test_webp_transparency():
    """WEBP 투명 처리 테스트"""
    print("🧪 WEBP 투명 처리 테스트...")
    
    # 테스트 PDF 파일 찾기
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if not pdf_files:
        print("❌ 테스트용 PDF 파일을 찾을 수 없습니다.")
        return False
    
    test_pdf = pdf_files[0]
    print(f"📄 테스트 PDF 파일: {test_pdf}")
    
    url = "http://localhost:5000/api/pdf-to-images"
    
    # WEBP 투명 처리 테스트 (transparentBg=true 필수)
    with open(test_pdf, 'rb') as f:
        data = {
            'format': 'webp',
            'transparentBg': 'true',  # 이것이 중요!
            'whiteThreshold': '250',
            'webpLossless': 'true'
        }
        files = {'file': f}
        
        try:
            response = requests.post(url, data=data, files=files)
            if response.status_code == 200:
                # WEBP 파일 저장
                output_path = f"test_webp_transparent_fixed.webp"
                with open(output_path, 'wb') as out_f:
                    out_f.write(response.content)
                
                # 이미지 분석
                img = Image.open(output_path)
                print(f"   ✅ WEBP 변환 성공: {img.size}, 모드: {img.mode}")
                
                if img.mode == 'RGBA':
                    # 투명 픽셀 계산
                    alpha_channel = img.split()[-1]
                    transparent_pixels = sum(1 for pixel in alpha_channel.getdata() if pixel == 0)
                    total_pixels = img.width * img.height
                    transparency_ratio = (transparent_pixels / total_pixels) * 100
                    print(f"   📊 투명 픽셀 비율: {transparency_ratio:.1f}%")
                    return transparency_ratio > 50  # 50% 이상 투명하면 성공
                else:
                    print(f"   ⚠️  투명 채널이 없습니다: {img.mode}")
                    return False
            else:
                print(f"   ❌ API 요청 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ 오류 발생: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 WEBP 투명 처리 수정 테스트")
    print("=" * 50)
    
    success = test_webp_transparency()
    
    print("=" * 50)
    if success:
        print("🎉 WEBP 투명 처리 성공!")
    else:
        print("❌ WEBP 투명 처리 실패")