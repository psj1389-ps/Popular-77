import requests
import os

print('Testing direct Flask service...')
url = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images'
test_pdf = 'f:/Popular-77/test.pdf'

if os.path.exists(test_pdf):
    print('Sending POST request to Flask service...')
    with open(test_pdf, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        data = {'format': 'png', 'dpi': '144'}
        resp = requests.post(url, files=files, data=data, timeout=120)
    
    print(f'Status: {resp.status_code}')
    content_type = resp.headers.get('content-type', 'N/A')
    print(f'Content-Type: {content_type}')
    
    if resp.status_code == 200:
        print(f'SUCCESS! Size: {len(resp.content)} bytes')
        with open('direct_flask_output.png', 'wb') as f:
            f.write(resp.content)
        print('Output saved as direct_flask_output.png')
    else:
        print(f'FAILED: {resp.text}')
else:
    print('Test PDF not found')