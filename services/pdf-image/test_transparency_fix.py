#!/usr/bin/env python3
"""
PDF-Image 서비스 투명 처리 수정 테스트
"""
import requests
import os
from PIL import Image

def test_transparency_fix():
    """수정된 투명 처리 기능 테스트"""
    print("🧪 PDF-Image 투명 처리 수정 테스트...")
    
    # 테스트 PDF 파일 찾기
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if not pdf_files:
        print("❌ 테스트용 PDF 파일을 찾을 수 없습니다.")
        return False
    
    test_pdf = pdf_files[0]
    print(f"📄 테스트 PDF 파일: {test_pdf}")
    
    # 서버 URL
    url = "http://localhost:5000/api/pdf-to-images"
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "PNG 투명 처리",
            "data": {
                "format": "png",
                "transparentBg": "true",
                "whiteThreshold": "250"
            }
        },
        {
            "name": "WebP 투명 처리 (무손실)",
            "data": {
                "format": "webp",
                "transparentBg": "true",
                "whiteThreshold": "250",
                "webpLossless": "true"
            }
        },
        {
            "name": "WebP 투명 처리 (손실)",
            "data": {
                "format": "webp",
                "transparentBg": "true",
                "whiteThreshold": "250",
                "webpLossless": "false",
                "quality": "90"
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 테스트 {i}: {test_case['name']}")
        
        try:
            with open(test_pdf, 'rb') as f:
                files = {'file': f}
                response = requests.post(url, files=files, data=test_case['data'], timeout=30)
            
            if response.status_code == 200:
                # 응답 파일 저장
                output_filename = f"test_output_{i}.{test_case['data']['format']}"
                with open(output_filename, 'wb') as f:
                    f.write(response.content)
                
                # 이미지 분석
                try:
                    img = Image.open(output_filename)
                    print(f"   ✅ 변환 성공: {img.size}, 모드: {img.mode}")
                    
                    # 투명도 확인
                    if img.mode in ('RGBA', 'LA') or 'transparency' in img.info:
                        if img.mode == 'RGBA':
                            alpha_channel = img.getchannel('A')
                            transparent_pixels = sum(1 for pixel in alpha_channel.getdata() if pixel == 0)
                            total_pixels = img.width * img.height
                            transparency_ratio = (transparent_pixels / total_pixels) * 100
                            print(f"   📊 투명 픽셀 비율: {transparency_ratio:.1f}%")
                            
                            if transparency_ratio > 0:
                                print(f"   🎉 투명 처리 성공!")
                                success_count += 1
                            else:
                                print(f"   ⚠️ 투명 픽셀이 없습니다.")
                        else:
                            print(f"   🎉 투명 정보 포함됨!")
                            success_count += 1
                    else:
                        print(f"   ❌ 투명 정보가 없습니다.")
                    
                except Exception as e:
                    print(f"   ❌ 이미지 분석 오류: {e}")
                
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                print(f"   응답: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 요청 오류: {e}")
    
    return success_count == len(test_cases)

if __name__ == "__main__":
    print("🚀 PDF-Image 투명 처리 수정 테스트")
    print("=" * 50)
    
    success = test_transparency_fix()
    
    print("=" * 50)
    if success:
        print("🎉 모든 투명 처리 테스트 성공!")
    else:
        print("❌ 일부 투명 처리 테스트 실패")