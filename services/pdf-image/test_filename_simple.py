#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

def test_single_page():
    print('=== 단일 페이지 테스트 ===')
    with open('test_single.pdf', 'rb') as f:
        files = {'file': ('test_single.pdf', f, 'application/pdf')}
        data = {'format': 'png', 'dpi': '144', 'pages': '1'}
        response = requests.post('http://localhost:5000/api/pdf-to-images', files=files, data=data)
        
        print(f'상태 코드: {response.status_code}')
        print(f'Content-Type: {response.headers.get("Content-Type", "")}')
        print(f'Content-Disposition: {response.headers.get("Content-Disposition", "")}')
        
        if response.status_code == 200:
            with open('single_output.png', 'wb') as out:
                out.write(response.content)
            print('단일 페이지 파일 저장 완료: single_output.png')
            
            # 파일명 확인
            content_disp = response.headers.get("Content-Disposition", "")
            if "1장.png" in content_disp:
                print('✅ 단일 페이지 파일명 테스트 통과!')
                return True
            else:
                print('❌ 단일 페이지 파일명 테스트 실패')
                return False
        else:
            print(f'오류: {response.text}')
            return False

def test_multi_page():
    print('\n=== 다중 페이지 테스트 ===')
    with open('test_multi.pdf', 'rb') as f:
        files = {'file': ('test_multi.pdf', f, 'application/pdf')}
        data = {'format': 'png', 'dpi': '144'}
        response = requests.post('http://localhost:5000/api/pdf-to-images', files=files, data=data)
        
        print(f'상태 코드: {response.status_code}')
        print(f'Content-Type: {response.headers.get("Content-Type", "")}')
        print(f'Content-Disposition: {response.headers.get("Content-Disposition", "")}')
        
        if response.status_code == 200:
            with open('multi_output.zip', 'wb') as out:
                out.write(response.content)
            print('다중 페이지 파일 저장 완료: multi_output.zip')
            
            # 파일명 확인
            content_disp = response.headers.get("Content-Disposition", "")
            if "test_multi_images.zip" in content_disp:
                print('✅ 다중 페이지 파일명 테스트 통과!')
                return True
            else:
                print('❌ 다중 페이지 파일명 테스트 실패')
                return False
        else:
            print(f'오류: {response.text}')
            return False

if __name__ == "__main__":
    single_result = test_single_page()
    multi_result = test_multi_page()
    
    print('\n=== 테스트 결과 요약 ===')
    print(f'단일 페이지: {"통과" if single_result else "실패"}')
    print(f'다중 페이지: {"통과" if multi_result else "실패"}')
    
    if single_result and multi_result:
        print('🎉 모든 테스트 통과!')
    else:
        print('⚠️ 일부 테스트 실패')