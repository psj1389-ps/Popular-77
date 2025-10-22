import requests
import os
import urllib.parse

def test_korean_filename():
    """한글 파일명으로 PDF 변환 테스트"""
    
    # 테스트할 파일 경로
    test_file = "test_single.pdf"
    
    if not os.path.exists(test_file):
        print(f"테스트 파일이 없습니다: {test_file}")
        return
    
    # 한글 파일명으로 업로드 시뮬레이션
    korean_filename = "한글파일명.pdf"
    
    print(f"테스트 시작: {korean_filename}")
    
    try:
        # 단일 페이지 변환 테스트
        print("\n=== 단일 페이지 변환 테스트 ===")
        with open(test_file, 'rb') as f:
            files = {'file': (korean_filename, f, 'application/pdf')}
            data = {
                'format': 'png',
                'dpi': '144',
                'pages': '1'
            }
            
            response = requests.post(
                'http://localhost:5000/api/pdf-to-images',
                files=files,
                data=data
            )
            
            print(f"응답 상태: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                print(f"Content-Disposition: {content_disposition}")
                
                # 파일명 추출 및 확인
                if "filename*=UTF-8''" in content_disposition:
                    encoded_filename = content_disposition.split("filename*=UTF-8''")[1]
                    decoded_filename = urllib.parse.unquote(encoded_filename)
                    print(f"디코딩된 파일명: {decoded_filename}")
                    
                    # 예상 파일명: 한글파일명.png
                    expected = "한글파일명.png"
                    if decoded_filename == expected:
                        print(f"✅ 파일명 올바름: {decoded_filename}")
                    else:
                        print(f"❌ 파일명 불일치 - 예상: {expected}, 실제: {decoded_filename}")
            
            if response.status_code == 200:
                print("✅ 단일 페이지 변환 성공")
            else:
                print(f"❌ 단일 페이지 변환 실패: {response.text}")
        
        # 다중 페이지 변환 테스트 (multi 파일 사용)
        multi_file = "test_multi.pdf"
        if os.path.exists(multi_file):
            print("\n=== 다중 페이지 변환 테스트 ===")
            korean_multi_filename = "한글다중페이지.pdf"
            
            with open(multi_file, 'rb') as f:
                files = {'file': (korean_multi_filename, f, 'application/pdf')}
                data = {
                    'format': 'png',
                    'dpi': '144'
                }
                
                response = requests.post(
                    'http://localhost:5000/api/pdf-to-images',
                    files=files,
                    data=data
                )
                
                print(f"응답 상태: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    print(f"Content-Disposition: {content_disposition}")
                    
                    # 파일명 추출 및 확인
                    if "filename*=UTF-8''" in content_disposition:
                        encoded_filename = content_disposition.split("filename*=UTF-8''")[1]
                        decoded_filename = urllib.parse.unquote(encoded_filename)
                        print(f"디코딩된 파일명: {decoded_filename}")
                        
                        # 예상 파일명: 한글다중페이지_png.zip
                        expected = "한글다중페이지_png.zip"
                        if decoded_filename == expected:
                            print(f"✅ 파일명 올바름: {decoded_filename}")
                        else:
                            print(f"❌ 파일명 불일치 - 예상: {expected}, 실제: {decoded_filename}")
                
                if response.status_code == 200:
                    print("✅ 다중 페이지 변환 성공")
                else:
                    print(f"❌ 다중 페이지 변환 실패: {response.text}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

# 기존 테스트 함수들
def test_single_page():
    """단일 페이지 변환 테스트"""
    print("=== 단일 페이지 테스트 ===")
    
    try:
        with open('test_single.pdf', 'rb') as f:
            files = {'file': ('test_single.pdf', f, 'application/pdf')}
            data = {
                'format': 'png',
                'dpi': '144',
                'pages': '1'
            }
            
            response = requests.post(
                'http://localhost:5000/api/pdf-to-images',
                files=files,
                data=data
            )
            
            print(f"상태 코드: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                print(f"Content-Disposition: {content_disposition}")
            
            if response.status_code == 200:
                print("✅ 단일 페이지 테스트 성공!")
                
                # 파일명 형식 확인
                if content_disposition and "1장.png" in content_disposition:
                    print("❌ 파일명 형식 오류: 여전히 '1장' 형식 사용")
                elif content_disposition and "test_single.png" in content_disposition:
                    print("✅ 파일명 형식 확인: test_single.png")
                else:
                    print(f"❌ 파일명 형식 오류: {content_disposition}")
            else:
                print(f"❌ 단일 페이지 테스트 실패: {response.text}")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def test_multi_page():
    """다중 페이지 변환 테스트"""
    print("\n=== 다중 페이지 테스트 ===")
    
    try:
        with open('test_multi.pdf', 'rb') as f:
            files = {'file': ('test_multi.pdf', f, 'application/pdf')}
            data = {
                'format': 'png',
                'dpi': '144'
            }
            
            response = requests.post(
                'http://localhost:5000/api/pdf-to-images',
                files=files,
                data=data
            )
            
            print(f"상태 코드: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                print(f"Content-Disposition: {content_disposition}")
            
            if response.status_code == 200:
                print("✅ 다중 페이지 테스트 성공!")
                
                # 파일명 형식 확인 - 새로운 형식 test_multi_png.zip 확인
                if content_disposition and "test_multi_png.zip" in content_disposition:
                    print("✅ 파일명 형식 확인: test_multi_png.zip (새 형식)")
                elif content_disposition and "test_multi_images.zip" in content_disposition:
                    print("❌ 파일명 형식 오류: 여전히 _images.zip 형식 사용")
                else:
                    print(f"❌ 파일명 형식 오류: {content_disposition}")
            else:
                print(f"❌ 다중 페이지 테스트 실패: {response.text}")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    # 기존 테스트
    test_single_page()
    test_multi_page()
    
    # 한글 파일명 테스트
    print("\n" + "="*50)
    test_korean_filename()