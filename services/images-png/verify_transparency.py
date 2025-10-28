#!/usr/bin/env python3
"""
투명 처리 결과 검증 스크립트
"""
from PIL import Image
import os

def verify_transparency():
    """생성된 이미지들의 투명도 검증"""
    print("🔍 투명도 검증...")
    
    # 검증할 파일들
    test_files = [
        "output_PNG_투명_배경_pdf-to-images.png",
        "output_WEBP_투명_배경_(무손실)_pdf-to-images.webp",
        "output_WEBP_투명_배경_(손실)_pdf-to-images.webp"
    ]
    
    for filename in test_files:
        if os.path.exists(filename):
            print(f"\n📄 파일: {filename}")
            try:
                img = Image.open(filename)
                print(f"   크기: {img.size}, 모드: {img.mode}")
                
                if img.mode in ('RGBA', 'LA'):
                    # 알파 채널 분석
                    alpha_channel = img.getchannel('A')
                    alpha_data = list(alpha_channel.getdata())
                    
                    transparent_pixels = sum(1 for p in alpha_data if p == 0)
                    semi_transparent = sum(1 for p in alpha_data if 0 < p < 255)
                    opaque_pixels = sum(1 for p in alpha_data if p == 255)
                    total_pixels = len(alpha_data)
                    
                    print(f"   투명 픽셀: {transparent_pixels} ({(transparent_pixels/total_pixels)*100:.1f}%)")
                    print(f"   반투명 픽셀: {semi_transparent} ({(semi_transparent/total_pixels)*100:.1f}%)")
                    print(f"   불투명 픽셀: {opaque_pixels} ({(opaque_pixels/total_pixels)*100:.1f}%)")
                    
                    if transparent_pixels > 0:
                        print(f"   ✅ 투명 처리 성공!")
                    else:
                        print(f"   ❌ 투명 픽셀이 없습니다.")
                        
                elif 'transparency' in img.info:
                    print(f"   ✅ 투명 정보 포함됨: {img.info['transparency']}")
                else:
                    print(f"   ❌ 투명 정보가 없습니다.")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {filename}")

if __name__ == "__main__":
    verify_transparency()