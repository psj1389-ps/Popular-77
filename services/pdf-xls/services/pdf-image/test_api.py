#!/usr/bin/env python3
"""
API 테스트 스크립트 - 향상된 투명 배경 기능 테스트
"""
import requests
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """테스트용 PDF 생성"""
    pdf_path = "test_api.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Test PDF for Transparent Background")
    c.drawString(100, 700, "This is a test document")
    c.save()
    return pdf_path

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    pdf_path = create_test_pdf()
    
    # 테스트할 엔드포인트들
    endpoints = [
        "http://localhost:5000/api/pdf-to-images",
        "http://localhost:5000/api/pdf-image/convert_to_images"
    ]
    
    # 테스트 파라미터들
    test_cases = [
        {
            "name": "PNG 투명 배경",
            "params": {
                "format": "png",
                "transparentBg": "true",
                "quality": "high",
                "tolerance": "8"
            }
        },
        {
            "name": "WEBP 투명 배경 (무손실)",
            "params": {
                "format": "webp",
                "transparentBg": "true",
                "webpLossless": "true",
                "tolerance": "6"
            }
        },
        {
            "name": "WEBP 투명 배경 (손실)",
            "params": {
                "format": "webp",
                "transparentBg": "true",
                "webpLossless": "false",
                "quality": "85"
            }
        },
        {
            "name": "커스텀 투명 색상",
            "params": {
                "format": "png",
                "transparentBg": "true",
                "transparentColor": "f8f8f8",
                "tolerance": "5"
            }
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n=== 테스트 엔드포인트: {endpoint} ===")
        
        for test_case in test_cases:
            print(f"\n테스트 케이스: {test_case['name']}")
            
            try:
                with open(pdf_path, 'rb') as f:
                    files = {'file': f}
                    data = test_case['params']
                    
                    response = requests.post(endpoint, files=files, data=data, timeout=30)
                    
                    if response.status_code == 200:
                        # 응답 파일 저장
                        output_filename = f"output_{test_case['name'].replace(' ', '_')}_{endpoint.split('/')[-1]}"
                        
                        # Content-Type에 따라 확장자 결정
                        content_type = response.headers.get('content-type', '')
                        if 'zip' in content_type:
                            output_filename += '.zip'
                        elif test_case['params']['format'] == 'png':
                            output_filename += '.png'
                        elif test_case['params']['format'] == 'webp':
                            output_filename += '.webp'
                        
                        with open(output_filename, 'wb') as out_f:
                            out_f.write(response.content)
                        
                        print(f"✅ 성공: {output_filename} 저장됨 ({len(response.content)} bytes)")
                    else:
                        print(f"❌ 실패: HTTP {response.status_code}")
                        try:
                            error_data = response.json()
                            print(f"   오류: {error_data.get('error', 'Unknown error')}")
                        except:
                            print(f"   응답: {response.text[:200]}")
                            
            except Exception as e:
                print(f"❌ 예외 발생: {str(e)}")
    
    # 정리
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    
    print("\n=== API 테스트 완료 ===")

if __name__ == "__main__":
    test_api_endpoints()