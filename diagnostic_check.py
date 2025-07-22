#!/usr/bin/env python3
"""
Diagnostic script to check ACS voice integration configuration
"""
import os
import requests
import json
from urllib.parse import urlparse

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("=== Environment Variables Check ===")
    
    required_vars = [
        "ACS_CONNECTION_STRING",
        "COGNITIVE_SERVICE_ENDPOINT", 
        "AGENT_PHONE_NUMBER",
        "CALLBACK_URI_HOST",
        "AZURE_OPENAI_SERVICE_KEY",
        "AZURE_OPENAI_SERVICE_ENDPOINT",
        "OPENAI_ASSISTANT_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "key" in var.lower() or "connection" in var.lower():
                print(f"✓ {var}: [REDACTED - {len(value)} chars]")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def check_callback_url():
    """Check if the callback URL is accessible"""
    print("\n=== Callback URL Check ===")
    
    callback_host = os.getenv("CALLBACK_URI_HOST")
    if not callback_host:
        print("❌ CALLBACK_URI_HOST not set")
        return False
    
    # Check health endpoint
    health_url = f"{callback_host}/api/health"
    print(f"Checking health endpoint: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Health endpoint accessible: {response.text}")
            return True
        else:
            print(f"❌ Health endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach health endpoint: {e}")
        return False

def check_phone_number_format():
    """Check if phone number is in correct format"""
    print("\n=== Phone Number Format Check ===")
    
    agent_phone = os.getenv("AGENT_PHONE_NUMBER")
    if not agent_phone:
        print("❌ AGENT_PHONE_NUMBER not set")
        return False
    
    if agent_phone.startswith("+") and len(agent_phone) >= 10:
        print(f"✅ Phone number format looks correct: {agent_phone}")
        return True
    else:
        print(f"❌ Phone number format may be incorrect: {agent_phone}")
        print("   Expected format: +1234567890")
        return False

def check_azure_openai_connection():
    """Check Azure OpenAI connection"""
    print("\n=== Azure OpenAI Connection Check ===")
    
    endpoint = os.getenv("AZURE_OPENAI_SERVICE_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_SERVICE_KEY")
    
    if not endpoint or not key:
        print("❌ Azure OpenAI credentials not set")
        return False
    
    # Simple endpoint check
    try:
        # Just check if the endpoint is reachable (without making actual API call)
        parsed = urlparse(endpoint)
        if parsed.scheme and parsed.netloc:
            print(f"✅ Azure OpenAI endpoint format looks correct: {endpoint}")
            return True
        else:
            print(f"❌ Azure OpenAI endpoint format incorrect: {endpoint}")
            return False
    except Exception as e:
        print(f"❌ Error checking Azure OpenAI endpoint: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    print("🔍 ACS Voice Integration Diagnostic Check")
    print("=" * 50)
    
    checks = [
        check_environment_variables(),
        check_phone_number_format(),
        check_azure_openai_connection(),
        check_callback_url()
    ]
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All {total} checks passed!")
        print("\nIf you're still having issues, check:")
        print("1. Azure Communication Services resource status")
        print("2. Phone number assignment in Azure portal")
        print("3. Application logs for detailed error messages")
    else:
        print(f"❌ {total - passed} out of {total} checks failed")
        print("\nPlease fix the failed checks and try again.")

if __name__ == "__main__":
    main()
