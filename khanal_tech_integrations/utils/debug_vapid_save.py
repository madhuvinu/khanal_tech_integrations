#!/usr/bin/env python3
"""
Debug script to check why VAPID keys aren't being saved
Run: bench --site [site-name] execute khanal_tech_integrations.utils.debug_vapid_save.debug_save
"""

import frappe


def debug_save():
    """
    Debug the save process step by step
    """
    print("=" * 70)
    print("🔍 Debugging VAPID Keys Save Process")
    print("=" * 70)
    
    # Step 1: Check if DocType exists
    print("\n1️⃣ Checking if DocType exists...")
    try:
        doctype = frappe.get_doc("DocType", "Push Notification Settings")
        print(f"   ✅ DocType exists: {doctype.name}")
    except Exception as e:
        print(f"   ❌ DocType not found: {str(e)}")
        return
    
    # Step 2: Check if document exists
    print("\n2️⃣ Checking if document exists...")
    try:
        if frappe.db.exists("Push Notification Settings", "Push Notification Settings"):
            print("   ✅ Document exists in database")
            doc = frappe.get_doc("Push Notification Settings", "Push Notification Settings")
            print(f"   Current vapid_email: {doc.get('vapid_email') or 'None'}")
            print(f"   Current vapid_public_key: {doc.get('vapid_public_key')[:50] if doc.get('vapid_public_key') else 'None'}...")
            print(f"   Current vapid_private_key: {'Present' if doc.get('vapid_private_key') else 'None'} (length: {len(doc.get('vapid_private_key')) if doc.get('vapid_private_key') else 0})")
        else:
            print("   ⚠️  Document does not exist, will be created")
    except Exception as e:
        print(f"   ❌ Error checking document: {str(e)}")
    
    # Step 3: Try to get single
    print("\n3️⃣ Testing frappe.get_single()...")
    try:
        settings = frappe.get_single("Push Notification Settings")
        print(f"   ✅ get_single() works")
        print(f"   Document name: {settings.name}")
        print(f"   Has vapid_email field: {'vapid_email' in settings.as_dict()}")
        print(f"   Current values:")
        print(f"     - vapid_email: {settings.get('vapid_email') or 'None'}")
        print(f"     - vapid_public_key: {settings.get('vapid_public_key')[:50] if settings.get('vapid_public_key') else 'None'}...")
        print(f"     - vapid_private_key: {'Present' if settings.get('vapid_private_key') else 'None'}")
    except Exception as e:
        print(f"   ❌ get_single() failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Try to set and save
    print("\n4️⃣ Testing set and save...")
    try:
        test_email = "test@example.com"
        test_public = "TEST_PUBLIC_KEY_12345"
        test_private = "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
        
        settings = frappe.get_single("Push Notification Settings")
        settings.vapid_email = test_email
        settings.vapid_public_key = test_public
        settings.vapid_private_key = test_private
        
        print(f"   ✅ Set values in memory")
        print(f"   Before save - vapid_email: {settings.vapid_email}")
        
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"   ✅ save() completed")
        
        # Verify
        frappe.clear_cache()
        verify = frappe.get_single("Push Notification Settings")
        verify_email = verify.get('vapid_email') or getattr(verify, 'vapid_email', None)
        if verify_email == test_email:
            print(f"   ✅ Verified: vapid_email saved correctly")
        else:
            print(f"   ❌ Verification failed: expected {test_email}, got {verify_email}")
        
        # Check database directly
        db_email = frappe.db.get_value("Push Notification Settings", "Push Notification Settings", "vapid_email")
        if db_email == test_email:
            print(f"   ✅ Database check: vapid_email is correct")
        else:
            print(f"   ❌ Database check failed: expected {test_email}, got {db_email}")
            
    except Exception as e:
        print(f"   ❌ Save failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Check field definitions
    print("\n5️⃣ Checking field definitions...")
    try:
        meta = frappe.get_meta("Push Notification Settings")
        fields = ['vapid_email', 'vapid_public_key', 'vapid_private_key']
        for fieldname in fields:
            field = meta.get_field(fieldname)
            if field:
                print(f"   ✅ {fieldname}: {field.fieldtype} (label: {field.label})")
            else:
                print(f"   ❌ {fieldname}: Field not found in meta!")
    except Exception as e:
        print(f"   ❌ Error checking fields: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Debug Complete")
    print("=" * 70)

