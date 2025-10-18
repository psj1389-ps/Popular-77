import requests
import os

url = 'https://77-tools.xyz/api/pdf-image/convert_to_images'
test_pdf = 'f:/Popular-77/test.pdf'

print('Testing Vercel API endpoint')
print(f'URL: {url}')

try:
    # Test OPTIONS
    print('1. Testing OPTIONS...')
    options_resp = requests.options(url, timeout=30)
    print(f'   Status: {options_resp.status_code}')
    
    # Test POST with file
    print('2. Testing POST with file...')
    if os.path.exists(test_pdf):
        with open(test_pdf, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {'format': 'png', 'dpi': '144'}
            post_resp = requests.post(url, files=files, data=data, timeout=120)
        
        print(f'   Status: {post_resp.status_code}')
        content_type = post_resp.headers.get('content-type', 'N/A')
        print(f'   Content-Type: {content_type}')
        
        if post_resp.status_code == 200:
            print(f'Success! Response size: {len(post_resp.content)} bytes')
        else:
            print(f'Failed: {post_resp.text[:300]}')
    else:
        print('Test PDF not found')
        
except Exception as e:
    print(f'Error: {e}')