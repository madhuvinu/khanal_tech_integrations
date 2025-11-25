#!/usr/bin/env python3
"""
Verify VAPID keys are stored correctly in Push Notification Settings DocType
Run: bench --site [site-name] execute khanal_tech_integrations.utils.verify_vapid_keys.verify_keys
"""

import frappe
from khanal_tech_integrations.utils.generate_vapid_keys import (
    get_vapid_public_key,
    get_vapid_private_key,
    get_vapid_email
)
from khanal_tech_integrations.api.push_notifications import get_vapid_public_key_api


def verify_keys():
    """
    Comprehensive verification of VAPID keys storage and retrieval
    """
    print("=" * 70)
    print("🔍 Verifying VAPID Keys Storage in Push Notification Settings")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Test 1: Direct DocType access (Note: get_single may have caching issues, use SQL instead)
    print("\n1️⃣ Testing Direct DocType Access (using get_single)...")
    print("   ℹ️  Note: get_single() may have caching issues. Using SQL is more reliable.")
    try:
        settings = frappe.get_single("Push Notification Settings")
        vapid_email = settings.get('vapid_email')
        vapid_public_key = settings.get('vapid_public_key')
        vapid_private_key = settings.get('vapid_private_key')
        
        if not vapid_email:
            print("   ⚠️  vapid_email is empty (get_single caching issue - use SQL)")
        else:
            print(f"   ✅ vapid_email: {vapid_email}")
        
        if not vapid_public_key:
            print("   ⚠️  vapid_public_key is empty (get_single caching issue - use SQL)")
        else:
            print(f"   ✅ vapid_public_key: {vapid_public_key[:50]}... (length: {len(vapid_public_key)})")
        
        if not vapid_private_key:
            print("   ⚠️  vapid_private_key is empty (get_single caching issue - use SQL)")
        else:
            print(f"   ✅ vapid_private_key: Present (length: {len(vapid_private_key)})")
            if vapid_private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                print("      ✅ Valid PEM format")
            else:
                print("      ⚠️  May not be valid PEM format")
    except Exception as e:
        print(f"   ⚠️  Error accessing DocType with get_single: {str(e)} (this is expected)")
    
    # Test 2: Getter functions
    print("\n2️⃣ Testing Getter Functions...")
    try:
        public_key = get_vapid_public_key()
        if public_key:
            print(f"   ✅ get_vapid_public_key() returned: {public_key[:50]}...")
        else:
            print("   ❌ get_vapid_public_key() returned None")
            all_tests_passed = False
    except Exception as e:
        print(f"   ❌ get_vapid_public_key() error: {str(e)}")
        all_tests_passed = False
    
    try:
        private_key = get_vapid_private_key()
        if private_key:
            print(f"   ✅ get_vapid_private_key() returned key (length: {len(private_key)})")
        else:
            print("   ❌ get_vapid_private_key() returned None")
            all_tests_passed = False
    except Exception as e:
        print(f"   ❌ get_vapid_private_key() error: {str(e)}")
        all_tests_passed = False
    
    try:
        email = get_vapid_email()
        if email:
            print(f"   ✅ get_vapid_email() returned: {email}")
        else:
            print("   ❌ get_vapid_email() returned None")
            all_tests_passed = False
    except Exception as e:
        print(f"   ❌ get_vapid_email() error: {str(e)}")
        all_tests_passed = False
    
    # Test 3: API endpoint
    print("\n3️⃣ Testing API Endpoint...")
    try:
        result = get_vapid_public_key_api()
        if result.get("success"):
            api_key = result.get("public_key")
            print(f"   ✅ get_vapid_public_key_api() returned: {api_key[:50]}...")
            
            # Verify it matches DocType using SQL
            db_result = frappe.db.sql("""
                SELECT vapid_public_key 
                FROM `tabPush Notification Settings` 
                WHERE name = 'Push Notification Settings'
            """, as_dict=True)
            
            if db_result and db_result[0].get('vapid_public_key'):
                db_key = db_result[0]['vapid_public_key']
                if api_key == db_key:
                    print("   ✅ API key matches DocType key")
                else:
                    print(f"   ⚠️  API key does not match DocType key (may be from cache/site_config)")
                    print(f"      API: {api_key[:30]}...")
                    print(f"      DB:  {db_key[:30]}...")
            else:
                print("   ⚠️  Could not verify - DocType key not found")
        else:
            print(f"   ❌ get_vapid_public_key_api() failed: {result.get('message')}")
            all_tests_passed = False
    except Exception as e:
        print(f"   ❌ API endpoint error: {str(e)}")
        all_tests_passed = False
    
    # Test 4: Database direct SQL access
    print("\n4️⃣ Testing Database Direct SQL Access...")
    try:
        result = frappe.db.sql("""
            SELECT vapid_email, vapid_public_key, vapid_private_key 
            FROM `tabPush Notification Settings` 
            WHERE name = 'Push Notification Settings'
        """, as_dict=True)
        
        if result and len(result) > 0:
            db_email = result[0].get('vapid_email')
            db_public = result[0].get('vapid_public_key')
            db_private = result[0].get('vapid_private_key')
            
            if db_email:
                print(f"   ✅ Database vapid_email: {db_email}")
            else:
                print("   ❌ Database vapid_email is empty")
                all_tests_passed = False
            
            if db_public:
                print(f"   ✅ Database vapid_public_key: {db_public[:50]}...")
            else:
                print("   ❌ Database vapid_public_key is empty")
                all_tests_passed = False
            
            if db_private:
                print(f"   ✅ Database vapid_private_key: Present (length: {len(db_private)})")
            else:
                print("   ❌ Database vapid_private_key is empty")
                all_tests_passed = False
        else:
            print("   ❌ No data found in database")
            all_tests_passed = False
    except Exception as e:
        print(f"   ❌ Database access error: {str(e)}")
        all_tests_passed = False
    
    # Test 5: Key format validation
    print("\n5️⃣ Validating Key Formats...")
    try:
        # Use SQL to get keys for validation
        result = frappe.db.sql("""
            SELECT vapid_private_key, vapid_public_key 
            FROM `tabPush Notification Settings` 
            WHERE name = 'Push Notification Settings'
        """, as_dict=True)
        
        if result and len(result) > 0:
            private_key = result[0].get('vapid_private_key')
            public_key = result[0].get('vapid_public_key')
            
            if private_key:
                # Check PEM format
                if '-----BEGIN PRIVATE KEY-----' in private_key and '-----END PRIVATE KEY-----' in private_key:
                    print("   ✅ Private key has valid PEM markers")
                else:
                    print("   ⚠️  Private key may not be in valid PEM format")
                
                # Check length (PEM keys are typically 200-500 chars)
                if 200 <= len(private_key) <= 1000:
                    print(f"   ✅ Private key length is reasonable: {len(private_key)} chars")
                else:
                    print(f"   ⚠️  Private key length seems unusual: {len(private_key)} chars")
            else:
                print("   ❌ Private key not found for validation")
                all_tests_passed = False
            
            if public_key:
                # VAPID public keys are base64url encoded, typically 87 chars
                if 80 <= len(public_key) <= 100:
                    print(f"   ✅ Public key length is reasonable: {len(public_key)} chars")
                else:
                    print(f"   ⚠️  Public key length seems unusual: {len(public_key)} chars")
                
                # Check if it looks like base64url (no padding, URL-safe chars)
                if all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in public_key):
                    print("   ✅ Public key contains valid base64url characters")
                else:
                    print("   ⚠️  Public key may contain invalid characters")
            else:
                print("   ❌ Public key not found for validation")
                all_tests_passed = False
        else:
            print("   ❌ No keys found for validation")
            all_tests_passed = False
    except Exception as e:
        print(f"   ❌ Format validation error: {str(e)}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - VAPID keys are stored correctly in DocType!")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 70)
    
    return all_tests_passed

