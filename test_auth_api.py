#!/usr/bin/env python3
"""
Test script to verify kiosk authentication API
"""

import requests
import json

# Test configuration
BASE_URL = "http://kfltest.localhost:8003"
API_BASE = f"{BASE_URL}/api/method"

def test_api_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{API_BASE}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Testing {method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def main():
    print("🧪 Testing Kiosk Authentication API")
    print("=" * 50)
    
    # Test 1: Get plants
    print("\n1. Testing get_plants...")
    test_api_endpoint("khanal_tech_integrations.api.auth.get_plants")
    
    # Test 2: Test with sample data
    print("\n2. Testing with sample authentication...")
    test_data = {
        "user": "Administrator",
        "plant_id": "test-plant",
        "permissions": ["dashboard", "grn"]
    }
    
    # Test generate_plant_token
    print("\n3. Testing generate_plant_token...")
    test_api_endpoint("khanal_tech_integrations.api.auth.generate_plant_token", "POST", test_data)
    
    # Test verify_plant_access
    print("\n4. Testing verify_plant_access...")
    test_api_endpoint("khanal_tech_integrations.api.auth.verify_plant_access", "GET", {
        "user": "Administrator",
        "plant_id": "test-plant"
    })

if __name__ == "__main__":
    main()
