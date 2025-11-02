import requests

# Test local service
try:
    with open('test-image.svg', 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:5001/api/images-png', files=files)
        print(f"Local service status: {response.status_code}")
        print(f"Local service response: {response.text[:500]}")
except Exception as e:
    print(f"Local service error: {e}")

print("\n" + "="*50 + "\n")

# Test Render service
try:
    with open('test-image.svg', 'rb') as f:
        files = {'file': f}
        response = requests.post('https://images-png.onrender.com/api/images-png', files=files)
        print(f"Render service status: {response.status_code}")
        print(f"Render service response: {response.text[:500]}")
except Exception as e:
    print(f"Render service error: {e}")