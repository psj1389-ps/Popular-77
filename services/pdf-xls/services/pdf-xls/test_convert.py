import requests
import os

# ADOBE_DISABLED 환경변수 설정
os.environ['ADOBE_DISABLED'] = 'true'

# 테스트 파일 업로드
url = 'http://localhost:5000/convert'
files = {'file': open('test.pdf', 'rb')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        # 성공적으로 변환된 경우 파일 저장
        with open('converted_output.xlsx', 'wb') as f:
            f.write(response.content)
        print("변환 성공! converted_output.xlsx 파일이 생성되었습니다.")
    else:
        print("변환 실패")
        
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    files['file'].close()