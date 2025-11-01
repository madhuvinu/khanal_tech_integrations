#!/usr/bin/env python3
"""
Manual test script for HANA Raw Milk Sync
Run this with: bench --site your_site execute test_manual_sync.py
"""

import frappe

def test_manual_sync():
    """Test the HANA sync manually"""
    try:
        print("🧪 Testing HANA Raw Milk Sync...")
        print("=" * 50)
        
        # Test 1: Check sync status
        print("1. Checking current sync status...")
        from khanal_tech_integrations.api.hana_sync import get_sync_status
        status = get_sync_status()
        print(f"   Status: {status}")
        
        # Test 2: Test HANA connection
        print("\n2. Testing HANA connection...")
        from khanal_tech_integrations.api.hana_sync import test_hana_connection
        connection_result = test_hana_connection()
        print(f"   {connection_result}")
        
        # Test 3: Run the actual sync
        print("\n3. Running HANA sync...")
        from khanal_tech_integrations.api.hana_sync import sync_raw_milk_from_hana
        sync_result = sync_raw_milk_from_hana()
        print(f"   {sync_result}")
        
        # Test 4: Check sync status again
        print("\n4. Checking sync status after sync...")
        final_status = get_sync_status()
        print(f"   Final Status: {final_status}")
        
        print("\n" + "=" * 50)
        print("✅ Manual sync test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        frappe.log_error(title="Manual Sync Test Failed", message=str(e))

if __name__ == "__main__":
    test_manual_sync()






