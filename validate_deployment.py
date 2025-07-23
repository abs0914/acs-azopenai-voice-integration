#!/usr/bin/env python3
"""
Deployment validation script for Azure Web App tf-ai-aivoice-dev-api-68s3
"""
import requests
import json
import sys
from urllib.parse import urljoin

# Configuration
WEB_APP_URL = "https://tf-ai-aivoice-dev-api-68s3.azurewebsites.net"
TIMEOUT = 30

def test_endpoint(url, endpoint, expected_status=200, method='GET'):
    """Test a specific endpoint"""
    full_url = urljoin(url, endpoint)
    try:
        print(f"Testing {method} {full_url}...")
        
        if method == 'GET':
            response = requests.get(full_url, timeout=TIMEOUT)
        elif method == 'POST':
            response = requests.post(full_url, timeout=TIMEOUT)
        
        if response.status_code == expected_status:
            print(f"✅ {endpoint}: {response.status_code} - OK")
            return True
        else:
            print(f"❌ {endpoint}: {response.status_code} - Expected {expected_status}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ {endpoint}: Timeout after {TIMEOUT}s")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 {endpoint}: Connection error")
        return False
    except Exception as e:
        print(f"❌ {endpoint}: Error - {str(e)}")
        return False

def validate_deployment():
    """Run all validation tests"""
    print("🔍 Validating Azure Web App Deployment")
    print("=" * 50)
    
    tests = [
        # Basic health checks
        ("Root endpoint", "/", 200),
        ("Health check", "/api/health", 200),
        
        # API endpoints
        ("Callbacks endpoint", "/api/callbacks", 405),  # Method not allowed is expected for GET
        
        # Voice Live integration tests
        ("Voice Live test", "/api/testVoiceLive", 200),
        ("Voice Live call test", "/api/testVoiceLiveCall", 200, 'POST'),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, endpoint, expected_status, *method in tests:
        method = method[0] if method else 'GET'
        if test_endpoint(WEB_APP_URL, endpoint, expected_status, method):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is successful.")
        return True
    else:
        print("⚠️  Some tests failed. Check the application logs.")
        return False

def check_environment_config():
    """Check if environment variables are properly configured"""
    print("\n🔧 Checking Environment Configuration")
    print("-" * 30)
    
    try:
        # Try to get some basic info from the health endpoint
        response = requests.get(f"{WEB_APP_URL}/api/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print("✅ Application is responding")
            
            # Try to get more detailed info if available
            try:
                data = response.json()
                if 'status' in data:
                    print(f"✅ Health status: {data['status']}")
                if 'version' in data:
                    print(f"✅ Version: {data['version']}")
            except:
                print("ℹ️  Health endpoint returned non-JSON response")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Could not check environment: {str(e)}")

def main():
    """Main validation function"""
    print("Azure Web App Deployment Validator")
    print("Web App: tf-ai-aivoice-dev-api-68s3")
    print("URL:", WEB_APP_URL)
    print()
    
    # Run basic deployment validation
    deployment_ok = validate_deployment()
    
    # Check environment configuration
    check_environment_config()
    
    print("\n" + "=" * 50)
    if deployment_ok:
        print("✅ DEPLOYMENT VALIDATION PASSED")
        print("\nNext steps:")
        print("1. Test voice integration with actual phone calls")
        print("2. Monitor application logs for any runtime issues")
        print("3. Set up monitoring and alerting")
        sys.exit(0)
    else:
        print("❌ DEPLOYMENT VALIDATION FAILED")
        print("\nTroubleshooting steps:")
        print("1. Check Azure portal logs under 'Log stream'")
        print("2. Verify all environment variables are set")
        print("3. Check GitHub Actions deployment logs")
        print("4. Review DEPLOYMENT_FIX_GUIDE.md for detailed instructions")
        sys.exit(1)

if __name__ == "__main__":
    main()
