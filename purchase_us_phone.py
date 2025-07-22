#!/usr/bin/env python3
"""
Script to purchase a US phone number for Azure Communication Services
"""
import os
import json
import sys
from datetime import datetime
from azure.communication.phonenumbers import PhoneNumbersClient
from azure.identity import DefaultAzureCredential

def purchase_us_phone_number():
    """Purchase a US phone number for the vida-voicebot ACS resource"""
    
    # Configuration
    resource_group = "vida-home-dev"
    acs_resource_name = "vida-voicebot"
    
    try:
        # Get ACS connection string
        import subprocess
        result = subprocess.run([
            "az", "communication", "list-key", 
            "--name", acs_resource_name,
            "--resource-group", resource_group,
            "--query", "primaryConnectionString",
            "-o", "tsv"
        ], capture_output=True, text=True, check=True)
        
        connection_string = result.stdout.strip()
        
        if not connection_string:
            raise Exception("Failed to get ACS connection string")
        
        print(f"Using ACS resource: {acs_resource_name}")
        
        # Initialize the phone numbers client
        phone_numbers_client = PhoneNumbersClient.from_connection_string(connection_string)
        
        # Search for available US toll-free numbers
        print("Searching for available US toll-free numbers...")
        search_request = {
            "country_code": "US",
            "phone_number_type": "tollFree",
            "assignment_type": "application",
            "capabilities": ["calling"]
        }
        
        search_result = phone_numbers_client.begin_search_available_phone_numbers(**search_request)
        search_result = search_result.result()
        
        if not search_result.phone_numbers:
            print("No toll-free numbers available, trying geographic numbers...")
            # Try geographic numbers if toll-free not available
            search_request["phone_number_type"] = "geographic"
            search_request["area_code"] = "425"  # Seattle area code
            
            search_result = phone_numbers_client.begin_search_available_phone_numbers(**search_request)
            search_result = search_result.result()
        
        if not search_result.phone_numbers:
            raise Exception("No US phone numbers available")
        
        # Get the first available number
        phone_number = search_result.phone_numbers[0]
        print(f"Found available number: {phone_number}")
        
        # Purchase the phone number
        print("Purchasing phone number...")
        purchase_result = phone_numbers_client.begin_purchase_phone_numbers(search_result.search_id)
        purchase_result = purchase_result.result()
        
        print(f"Successfully purchased phone number: {phone_number}")
        
        # Save result to file
        result_data = {
            "success": True,
            "phone_number": phone_number,
            "acs_resource": acs_resource_name,
            "search_id": search_result.search_id,
            "error": "",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("us_phone_number_result.json", "w") as f:
            json.dump(result_data, f, indent=2)
        
        return phone_number
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error purchasing phone number: {error_msg}")
        
        # Save error result
        result_data = {
            "success": False,
            "phone_number": "",
            "acs_resource": acs_resource_name,
            "search_id": "",
            "error": error_msg,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("us_phone_number_result.json", "w") as f:
            json.dump(result_data, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    purchase_us_phone_number()
