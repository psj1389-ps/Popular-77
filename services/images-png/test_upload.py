#!/usr/bin/env python3
"""
Test script for images-png service
"""
import requests
import os
from PIL import Image

# Create a simple test image
def create_test_image():
    # Create a simple WEBP test image
    img = Image.new('RGB', (100, 100), color='red')
    test_path = 'test_image.webp'
    img.save(test_path, 'WEBP')
    return test_path

def test_api():
    # Create test image
    test_image_path = create_test_image()
    
    try:
        # Test the API endpoint
        url = 'http://localhost:5001/api/images-png'
        
        with open(test_image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'quality': 'medium',
                'scale': '1.0',
                'transparent_background': 'false'
            }
            
            print(f"Testing API: {url}")
            response = requests.post(url, files=files, data=data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ API test successful!")
                # Save the response as PNG
                with open('test_output.png', 'wb') as out_f:
                    out_f.write(response.content)
                print("Output saved as test_output.png")
            else:
                print(f"❌ API test failed!")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
    finally:
        # Clean up test image
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

if __name__ == '__main__':
    test_api()