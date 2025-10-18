#!/usr/bin/env python3
"""
Test script to verify endpoints work correctly on Render deployment
"""
import requests
import os

BASE_URL = "https://pdf-image-00tt.onrender.com"
TEST_PDF = "test_sample.pdf"

def create_test_pdf():
    """Create a simple test PDF"""
    if os.path.exists(TEST_PDF):
        return True
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        c = canvas.Canvas(TEST_PDF, pagesize=letter)
        c.drawString(100, 750, "Test PDF for conversion")
        c.drawString(100, 700, "This is a test document")
        c.save()
        print(f"✓ Created test PDF: {TEST_PDF}")
        return True
    except ImportError:
        print("❌ reportlab not available")
        return False

def test_endpoint(endpoint_path, description):
    """Test a specific endpoint"""
    print(f"\n🧪 Testing {description}: {BASE_URL}{endpoint_path}")
    
    if not os.path.exists(TEST_PDF):
        print(f"❌ Test PDF not found: {TEST_PDF}")
        return False
    
    try:
        with open(TEST_PDF, 'rb') as f:
            files = {'file': (TEST_PDF, f, 'application/pdf')}
            data = {
                'format': 'png',
                'quality': 'medium',
                'dpi': '144'
            }
            
            response = requests.post(f"{BASE_URL}{endpoint_path}", files=files, data=data, timeout=60)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                content_disposition = response.headers.get('Content-Disposition', '')
                content_type = response.headers.get('Content-Type', '')
                
                if 'attachment' in content_disposition:
                    print(f"✅ SUCCESS - File download working")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content-Length: {len(response.content)} bytes")
                    return True
                else:
                    print(f"⚠️ Response OK but not file attachment")
                    print(f"   Content: {response.text[:100]}...")
                    return False
            else:
                print(f"❌ FAILED - Status {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 Testing PDF-Image Service on Render")
    print("=" * 50)
    
    # Create test PDF
    if not create_test_pdf():
        print("❌ Cannot create test PDF, exiting")
        return
    
    # Test endpoints
    endpoints = [
        ("/convert", "Web Interface Endpoint"),
        ("/api/pdf-to-images", "Main API Endpoint"),
        ("/api/pdf-image/convert_to_images", "Compatibility Endpoint"),
        ("/convert_to_images", "Legacy Endpoint")
    ]
    
    results = {}
    for path, desc in endpoints:
        results[path] = test_endpoint(path, desc)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    all_passed = True
    for path, desc in endpoints:
        status = "✅ PASS" if results[path] else "❌ FAIL"
        print(f"  {path}: {status}")
        if not results[path]:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All endpoints working correctly!")
        print("✅ The 404 error issue has been resolved.")
    else:
        print("⚠️ Some endpoints still have issues.")
        print("❌ Further investigation needed.")

if __name__ == "__main__":
    main()