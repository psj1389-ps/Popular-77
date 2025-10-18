import requests
import os

def test_korean_filename_conversion():
    """한글 파일명으로 PDF 변환 테스트"""
    
    # 테스트할 파일 경로
    test_file = "f:\\Popular-77\\services\\pdf-image\\test_single.pdf"
    
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
            
            if response.status_code == 200:
                print("✅ 단일 페이지 변환 성공")
            else:
                print(f"❌ 단일 페이지 변환 실패: {response.text}")
        
        # 다중 페이지 변환 테스트 (multi 파일 사용)
        multi_file = "f:\\Popular-77\\services\\pdf-image\\test_multi.pdf"
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
                
                if response.status_code == 200:
                    print("✅ 다중 페이지 변환 성공")
                else:
                    print(f"❌ 다중 페이지 변환 실패: {response.text}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    test_korean_filename_conversion()