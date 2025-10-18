import requests
import os
import json

print('=== Detailed Debug Test for PDF-Image Services ===\n')

# Test files
test_pdf = 'f:/Popular-77/test.pdf'
vercel_url = 'https://77-tools.xyz/api/pdf-image/convert_to_images'
direct_flask_url = 'https://pdf-image-00tt.onrender.com/api/pdf-to-images'

if not os.path.exists(test_pdf):
    print('❌ Test PDF not found')
    exit(1)

print(f'📄 Test PDF: {test_pdf} ({os.path.getsize(test_pdf)} bytes)\n')

# Test 1: Direct Flask Service
print('🔍 Test 1: Direct Flask Service')
print(f'URL: {direct_flask_url}')
try:
    with open(test_pdf, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        data = {'format': 'png', 'dpi': '144'}
        resp = requests.post(direct_flask_url, files=files, data=data, timeout=120)
    
    print(f'Status: {resp.status_code}')
    print(f'Content-Type: {resp.headers.get("content-type", "N/A")}')
    
    if resp.status_code == 200:
        print(f'✅ SUCCESS! Size: {len(resp.content)} bytes')
        with open('direct_flask_test.png', 'wb') as f:
            f.write(resp.content)
        print('Output saved as direct_flask_test.png')
    else:
        print(f'❌ FAILED: {resp.text}')
except Exception as e:
    print(f'❌ ERROR: {e}')

print('\n' + '='*60 + '\n')

# Test 2: Vercel Proxy with detailed headers
print('🔍 Test 2: Vercel Proxy Service')
print(f'URL: {vercel_url}')

# First, let's check what headers we're sending
with open(test_pdf, 'rb') as f:
    files = {'file': ('test.pdf', f, 'application/pdf')}
    data = {'format': 'png', 'dpi': '144'}
    
    # Create a test request to see the headers
    prepared = requests.Request('POST', vercel_url, files=files, data=data).prepare()
    print(f'Request headers: {dict(prepared.headers)}')
    print(f'Content-Type: {prepared.headers.get("Content-Type", "N/A")}')
    
    # Check if boundary is in content-type
    content_type = prepared.headers.get('Content-Type', '')
    if 'boundary=' in content_type:
        boundary = content_type.split('boundary=')[1]
        print(f'Boundary: {boundary}')
    else:
        print('❌ No boundary found in Content-Type')

print('\nSending request...')
try:
    with open(test_pdf, 'rb') as f:
        files = {'file': ('test.pdf', f, 'application/pdf')}
        data = {'format': 'png', 'dpi': '144'}
        resp = requests.post(vercel_url, files=files, data=data, timeout=120)
    
    print(f'Status: {resp.status_code}')
    print(f'Content-Type: {resp.headers.get("content-type", "N/A")}')
    print(f'Response headers: {dict(resp.headers)}')
    
    if resp.status_code == 200:
        print(f'✅ SUCCESS! Size: {len(resp.content)} bytes')
        with open('vercel_proxy_test.png', 'wb') as f:
            f.write(resp.content)
        print('Output saved as vercel_proxy_test.png')
    else:
        print(f'❌ FAILED: {resp.text}')
        
        # Try to parse JSON response for more details
        try:
            error_data = resp.json()
            print(f'Error details: {json.dumps(error_data, indent=2)}')
        except:
            print('Could not parse error response as JSON')
            
except Exception as e:
    print(f'❌ ERROR: {e}')

print('\n' + '='*60)
print('🔍 Analysis:')
print('- If Direct Flask works but Vercel fails, the issue is in the Vercel proxy')
print('- Check Vercel function logs for detailed debugging output')
print('- The enhanced logging should show exactly where parsing fails')