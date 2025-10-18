#!/usr/bin/env python3
"""
Test script for the fixed Vercel PDF-Image API endpoint
"""

import requests
import os

def test_vercel_api():
    """Test the Vercel API endpoint with a real PDF file"""
    
    # API endpoint
    url = "https://77-tools.xyz/api/pdf-image/convert_to_images"
    
    # Check if test PDF exists
    test_pdf = "f:\\Popular-77\\test.pdf"
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    print(f"🧪 Testing Vercel API endpoint: {url}")
    print(f"📄 Using test file: {test_pdf}")
    
    try:
        # Test 1: OPTIONS request (CORS preflight)
        print("\n1️⃣ Testing OPTIONS request (CORS preflight)...")
        options_response = requests.options(url, timeout=30)
        print(f"   Status: {options_response.status_code}")
        print(f"   CORS Headers: {dict(options_response.headers)}")
        
        if options_response.status_code != 200:
            print("❌ OPTIONS request failed")
            return False
        
        # Test 2: POST request with actual PDF file
        print("\n2️⃣ Testing POST request with PDF file...")
        
        with open(test_pdf, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {
                'format': 'png',
                'dpi': '144',
                'quality': 'high'
            }
            
            post_response = requests.post(url, files=files, data=data, timeout=120)
            
        print(f"   Status: {post_response.status_code}")
        print(f"   Content-Type: {post_response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {post_response.headers.get('content-length', 'N/A')}")
        
        if post_response.status_code == 200:
            # Success - save the result
            content_type = post_response.headers.get('content-type', '')
            
            if 'application/zip' in content_type:
                output_file = 'test_output.zip'
            elif 'image/png' in content_type:
                output_file = 'test_output.png'
            elif 'image/jpeg' in content_type:
                output_file = 'test_output.jpg'
            else:
                output_file = 'test_output.bin'
            
            with open(output_file, 'wb') as f:
                f.write(post_response.content)
            
            print(f"✅ Success! Output saved as: {output_file}")
            print(f"   File size: {len(post_response.content)} bytes")
            return True
            
        else:
            print(f"❌ POST request failed")
            print(f"   Response: {post_response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_frontend_page():
    """Test if the frontend page loads correctly"""
    
    url = "https://77-tools.xyz/tools/pdf-image"
    print(f"\n🌐 Testing frontend page: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Frontend page loads successfully")
            return True
        else:
            print(f"❌ Frontend page failed to load")
            return False
            
    except Exception as e:
        print(f"❌ Error loading frontend page: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Fixed PDF-Image API")
    print("=" * 50)
    
    # Test API endpoint
    api_success = test_vercel_api()
    
    # Test frontend page
    frontend_success = test_frontend_page()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   API Endpoint: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   Frontend Page: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    
    if api_success and frontend_success:
        print("\n🎉 All tests passed! The PDF-Image service is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the logs above.")