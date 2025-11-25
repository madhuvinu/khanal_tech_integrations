#!/usr/bin/env python3
"""
Test push notification sending
Run: bench --site [site-name] execute khanal_tech_integrations.utils.test_push_send.test_send
"""

import frappe
import json
from pywebpush import webpush, WebPushException


def test_send():
    """Test sending a push notification"""
    print("=" * 70)
    print("🧪 Testing Push Notification Send")
    print("=" * 70)
    
    # Get VAPID keys
    result = frappe.db.sql("""
        SELECT vapid_email, vapid_public_key, vapid_private_key 
        FROM `tabPush Notification Settings` 
        WHERE name = 'Push Notification Settings'
    """, as_dict=True)
    
    if not result:
        print("❌ No VAPID keys found")
        return
    
    vapid_email = result[0].get('vapid_email')
    vapid_public_key = result[0].get('vapid_public_key')
    vapid_private_key = result[0].get('vapid_private_key')
    
    print(f"\n1️⃣ VAPID Keys:")
    print(f"   Email: {vapid_email}")
    print(f"   Public Key: {vapid_public_key[:50]}...")
    print(f"   Private Key: {vapid_private_key[:50]}...")
    print(f"   Private Key Length: {len(vapid_private_key)}")
    
    # Get latest subscription
    subs = frappe.db.sql("""
        SELECT name, user, endpoint, `keys` 
        FROM `tabPush Subscription` 
        WHERE is_active = 1
        ORDER BY creation DESC
        LIMIT 1
    """, as_dict=True)
    
    if not subs:
        print("\n❌ No active subscriptions found")
        return
    
    sub = subs[0]
    print(f"\n2️⃣ Subscription:")
    print(f"   ID: {sub['name']}")
    print(f"   User: {sub['user']}")
    print(f"   Endpoint: {sub['endpoint'][:80]}...")
    
    # Parse keys
    keys_str = sub.get('keys', '{}')
    if isinstance(keys_str, str):
        keys = json.loads(keys_str)
    else:
        keys = keys_str
    
    print(f"   Keys p256dh: {keys.get('p256dh', 'N/A')[:50]}...")
    print(f"   Keys auth: {keys.get('auth', 'N/A')}")
    
    # Prepare payload
    payload = {
        "title": "🧪 Test from Backend",
        "body": "If you see this, push notifications work!",
        "icon": "/assets/khanal_tech_integrations/images/favicon.png",
        "data": {"type": "test"}
    }
    
    # VAPID claims
    vapid_claims = {
        "sub": f"mailto:{vapid_email}"
    }
    
    print(f"\n3️⃣ Sending notification...")
    print(f"   Payload: {json.dumps(payload)[:100]}...")
    
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        # Load the PEM key properly
        print(f"\n   Loading PEM key...")
        private_key_obj = serialization.load_pem_private_key(
            vapid_private_key.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        # Convert to DER format for pywebpush
        der_key = private_key_obj.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Base64url encode the DER key
        import base64
        der_key_b64 = base64.urlsafe_b64encode(der_key).decode('utf-8').rstrip('=')
        print(f"   DER key (base64url): {der_key_b64[:50]}...")
        
        # Send push notification with DER key
        response = webpush(
            subscription_info={
                "endpoint": sub['endpoint'],
                "keys": keys
            },
            data=json.dumps(payload),
            vapid_private_key=der_key_b64,
            vapid_claims=vapid_claims
        )
        
        print(f"\n✅ SUCCESS! Push notification sent!")
        print(f"   Response: {response}")
        return {"success": True}
        
    except WebPushException as e:
        print(f"\n❌ WebPushException: {str(e)}")
        print(f"   Response: {e.response}")
        if e.response:
            print(f"   Status: {e.response.status_code}")
            print(f"   Body: {e.response.text}")
        return {"success": False, "error": str(e)}
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

