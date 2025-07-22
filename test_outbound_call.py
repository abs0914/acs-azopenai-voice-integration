#!/usr/bin/env python3
"""
Test script to make an outbound call via the ACS voice integration API
"""
import os
import requests
import json

def test_outbound_call():
    """Test making an outbound call"""
    
    # Get the callback host from environment
    callback_host = os.getenv("CALLBACK_URI_HOST")
    if not callback_host:
        print("❌ CALLBACK_URI_HOST environment variable not set")
        print("Please set it to your Azure Web App URL, e.g.:")
        print("export CALLBACK_URI_HOST='https://your-app-name.azurewebsites.net'")
        return False
    
    # API endpoint
    api_url = f"{callback_host}/api/initiateOutboundCall"
    
    # Test payload - you can modify this
    payload = {
        "phone_number": "+1234567890",  # Replace with your test phone number
        "client_name": "John Smith",
        "origin": "Seattle, USA", 
        "desired_destination": "Barcelona, Spain",
        "travel_dates": "May 2025",
        "other_details": "['2 adults', '1 child', '1 infant']"
    }
    
    print(f"🔄 Testing outbound call to: {api_url}")
    print(f"📞 Target phone number: {payload['phone_number']}")
    print(f"👤 Client name: {payload['client_name']}")
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Call initiated successfully!")
            try:
                response_data = response.json()
                print(f"📋 Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"📋 Response Text: {response.text}")
        else:
            print(f"❌ Call failed with status {response.status_code}")
            print(f"📋 Response: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

def main():
    """Main function"""
    print("📞 ACS Voice Integration - Outbound Call Test")
    print("=" * 50)
    
    print("⚠️  IMPORTANT: Make sure to update the phone_number in the payload")
    print("   to a valid phone number you want to test with.")
    print()
    
    # Ask user to confirm
    confirm = input("Do you want to proceed with the test call? (y/N): ")
    if confirm.lower() != 'y':
        print("Test cancelled.")
        return
    
    success = test_outbound_call()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed. Check the error messages above.")

if __name__ == "__main__":
    main()
