#!/usr/bin/env python3
"""
향상된 투명 배경 기능 테스트 스크립트
- 컬러키 처리 기능 테스트
- tolerance 설정 테스트
- transparentColor 파라미터 테스트
"""

import requests
import os
from PIL import Image

# 테스트 설정
BASE_URL = "http://localhost:5000"
PDF_FILE = "sample.pdf"

def test_enhanced_png_transparent():
    """향상된 PNG 투명 배경 기능 테스트"""
    print("=== 향상된 PNG 투명 배경 기능 테스트 ===")
    
    if not os.path.exists(PDF_FILE):
        print(f"테스트 파일 {PDF_FILE}이 없습니다.")
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
            "name": "낮은 tolerance 설정",
            "params": {
                "format": "png",
                "transparentBg": "true", 
                "tolerance": "2"
            },
            "output": "enhanced_transparent_low_tolerance.png"
        },
        {
            "name": "커스텀 투명 색상 (연한 회색)",
            "params": {
                "format": "png",
                "transparentBg": "true",
                "transparentColor": "f0f0f0",
                "tolerance": "10"
            },
            "output": "enhanced_transparent_custom_color.png"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n테스트: {test_case['name']}")
        
        with open(PDF_FILE, 'rb') as f:
            files = {'file': f}
            data = test_case['params']
            
            try:
                response = requests.post(f"{BASE_URL}/api/pdf-to-images", files=files, data=data)
                
                if response.status_code == 200:
                    # 파일 저장
                    with open(test_case['output'], 'wb') as out_f:
                        out_f.write(response.content)
                    
                    # 이미지 모드 확인
                    img = Image.open(test_case['output'])
                    print(f"✓ 성공: {test_case['output']} (모드: {img.mode}, 크기: {len(response.content)} bytes)")
                    
                    # 투명도 확인
                    if img.mode == 'RGBA':
                        alpha_channel = img.getchannel('A')
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

def test_enhanced_webp_transparent():
    """향상된 WEBP 투명 배경 기능 테스트"""
    print("\n=== 향상된 WEBP 투명 배경 기능 테스트 ===")
    
    if not os.path.exists(PDF_FILE):
        print(f"테스트 파일 {PDF_FILE}이 없습니다.")
        return False
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "WEBP 무손실 투명 배경",
            "params": {
                "format": "webp",
                "transparentBg": "true",
                "webpLossless": "true",
                "tolerance": "8"
            },
            "output": "enhanced_transparent_webp_lossless.webp"
        },
        {
            "name": "WEBP 손실 압축 투명 배경",
            "params": {
                "format": "webp",
                "transparentBg": "true",
                "webpLossless": "false",
                "quality": "85",
                "tolerance": "8"
            },
            "output": "enhanced_transparent_webp_lossy.webp"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n테스트: {test_case['name']}")
        
        with open(PDF_FILE, 'rb') as f:
            files = {'file': f}
            data = test_case['params']
            
            try:
                response = requests.post(f"{BASE_URL}/api/pdf-to-images", files=files, data=data)
                
                if response.status_code == 200:
                    # 파일 저장
                    with open(test_case['output'], 'wb') as out_f:
                        out_f.write(response.content)
                    
                    # 이미지 모드 확인
                    img = Image.open(test_case['output'])
                    print(f"✓ 성공: {test_case['output']} (모드: {img.mode}, 크기: {len(response.content)} bytes)")
                    
                    # 투명도 확인
                    if img.mode == 'RGBA':
                        alpha_channel = img.getchannel('A')
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
    
    if not os.path.exists(PDF_FILE):
        print(f"테스트 파일 {PDF_FILE}이 없습니다.")
        return False
    
    with open(PDF_FILE, 'rb') as f:
        files = {'file': f}
        data = {
            "format": "png",
            "transparentBg": "true",
            "tolerance": "10"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/pdf-image/convert_to_images", files=files, data=data)
            
            if response.status_code == 200:
                # 파일 저장
                with open("compatibility_test.png", 'wb') as out_f:
                    out_f.write(response.content)
                
                # 이미지 모드 확인
                img = Image.open("compatibility_test.png")
                print(f"✓ 호환성 엔드포인트 성공: compatibility_test.png (모드: {img.mode}, 크기: {len(response.content)} bytes)")
                
            else:
                print(f"✗ 호환성 엔드포인트 실패: HTTP {response.status_code}")
                print(f"  오류: {response.text}")
                
        except Exception as e:
            print(f"✗ 예외 발생: {str(e)}")
    
    return True

if __name__ == "__main__":
    print("향상된 투명 배경 기능 테스트를 시작합니다...")
    
    # PNG 투명 배경 테스트
    test_enhanced_png_transparent()
    
    # WEBP 투명 배경 테스트
    test_enhanced_webp_transparent()
    
    # 호환성 엔드포인트 테스트
    test_compatibility_endpoint()
    
    print("\n테스트 완료!")