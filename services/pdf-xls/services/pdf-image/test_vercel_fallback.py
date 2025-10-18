import requests
import os

print('Testing Vercel API after fallback implementation...')
url = 'https://77-tools.xyz/api/pdf-image/convert_to_images'
test_pdf = 'f:/Popular-77/test.pdf'

if os.path.exists(test_pdf):
    print('Sending POST request...')
    with open(test_pdf, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        data = {'format': 'png', 'dpi': '144'}
        resp = requests.post(url, files=files, data=data, timeout=120)
    
    print(f'Status: {resp.status_code}')
    content_type = resp.headers.get('content-type', 'N/A')
    print(f'Content-Type: {content_type}')
    
    if resp.status_code == 200:
        print(f'SUCCESS! Size: {len(resp.content)} bytes')
        with open('vercel_fallback_output.png', 'wb') as f:
            f.write(resp.content)
        print('Output saved as vercel_fallback_output.png')
    else:
        print(f'FAILED: {resp.text}')
else:
    print('Test PDF not found')