import requests

# 단일 페이지 테스트
print('=== 단일 페이지 테스트 ===')
with open('test_single.pdf', 'rb') as f:
    files = {'file': ('test_single.pdf', f, 'application/pdf')}
    data = {'format': 'png', 'dpi': '144', 'pages': '1'}
    response = requests.post('http://localhost:5000/api/pdf-to-images', files=files, data=data)
    
    print(f'상태 코드: {response.status_code}')
    print(f'Content-Type: {response.headers.get("Content-Type", "")}')
    print(f'Content-Disposition: {response.headers.get("Content-Disposition", "")}')
    
    if response.status_code == 200:
        print('✅ 단일 페이지 테스트 성공!')
        # 파일명 확인
        content_disp = response.headers.get("Content-Disposition", "")
        if "1장.png" in content_disp:
            print('✅ 파일명 형식 확인: 1장.png')
        else:
            print(f'❌ 파일명 형식 오류: {content_disp}')
    else:
        print(f'❌ 오류: {response.text}')

print('\n=== 다중 페이지 테스트 ===')
with open('test_multi.pdf', 'rb') as f:
    files = {'file': ('test_multi.pdf', f, 'application/pdf')}
    data = {'format': 'png', 'dpi': '144'}
    response = requests.post('http://localhost:5000/api/pdf-to-images', files=files, data=data)
    
    print(f'상태 코드: {response.status_code}')
    print(f'Content-Type: {response.headers.get("Content-Type", "")}')
    print(f'Content-Disposition: {response.headers.get("Content-Disposition", "")}')
    
    if response.status_code == 200:
        print('✅ 다중 페이지 테스트 성공!')
        # 파일명 확인
        content_disp = response.headers.get("Content-Disposition", "")
        if "test_multi_images.zip" in content_disp:
            print('✅ 파일명 형식 확인: test_multi_images.zip')
        else:
            print(f'❌ 파일명 형식 오류: {content_disp}')
    else:
        print(f'❌ 오류: {response.text}')