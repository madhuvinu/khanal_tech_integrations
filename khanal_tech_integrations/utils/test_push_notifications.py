#!/usr/bin/env python3
"""
Test script for push notifications
Run: bench --site [site-name] execute khanal_tech_integrations.utils.test_push_notifications.test_push_setup
"""

import frappe
import json


def test_push_setup():
	"""
	Test push notification setup
	"""
	print("=" * 60)
	print("🧪 Testing Push Notification Setup")
	print("=" * 60)
	
	# Test 1: Check VAPID keys from DocType
	print("\n1️⃣ Testing VAPID Keys (from Push Notification Settings DocType)...")
	try:
		settings = frappe.get_single("Push Notification Settings")
		vapid_public = settings.get('vapid_public_key')
		vapid_private = settings.get('vapid_private_key')
		vapid_email = settings.get('vapid_email')
		
		if vapid_public and vapid_private:
			print(f"   ✅ VAPID Public Key: {vapid_public[:50]}...")
			print(f"   ✅ VAPID Private Key: {'*' * 50} (hidden, length: {len(vapid_private)})")
			print(f"   ✅ VAPID Email: {vapid_email}")
			
			# Verify key format
			if vapid_private.startswith('-----BEGIN PRIVATE KEY-----'):
				print("   ✅ Private key format: Valid PEM format")
			else:
				print("   ⚠️  Private key format: May be invalid")
			
			if len(vapid_public) > 80:
				print("   ✅ Public key format: Valid base64 length")
			else:
				print("   ⚠️  Public key format: May be invalid")
		else:
			print("   ❌ VAPID keys not found in DocType!")
			print("   Run: bench --site [site] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys")
			return
	except Exception as e:
		print(f"   ❌ Error accessing Push Notification Settings: {str(e)}")
		print("   Run: bench --site [site] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys")
		return
	
	# Test 2: Check doctypes
	print("\n2️⃣ Testing Doctypes...")
	try:
		frappe.get_doc("DocType", "Push Subscription")
		print("   ✅ Push Subscription doctype exists")
	except:
		print("   ❌ Push Subscription doctype not found!")
		return
	
	try:
		frappe.get_doc("DocType", "Push Notification Log")
		print("   ✅ Push Notification Log doctype exists")
	except:
		print("   ❌ Push Notification Log doctype not found!")
		return
	
	# Test 3: Check API endpoints
	print("\n3️⃣ Testing API Endpoints...")
	try:
		from khanal_tech_integrations.api.push_notifications import (
			get_vapid_public_key_api,
			send_push_notification_api
		)
		
		# Test VAPID key endpoint
		result = get_vapid_public_key_api()
		if result.get("success"):
			print("   ✅ get_vapid_public_key_api working")
		else:
			print(f"   ❌ get_vapid_public_key_api failed: {result.get('message')}")
		
		# Test send notification (will fail if no subscriptions, but that's OK)
		print("   ℹ️  send_push_notification_api available (requires active subscriptions)")
		
	except Exception as e:
		print(f"   ❌ API import failed: {str(e)}")
		return
	
	# Test 4: Check subscriptions
	print("\n4️⃣ Checking Subscriptions...")
	subscriptions = frappe.get_all(
		"Push Subscription",
		filters={"is_active": 1},
		fields=["name", "user", "plant_id", "last_notified"]
	)
	
	if subscriptions:
		print(f"   ✅ Found {len(subscriptions)} active subscription(s):")
		for sub in subscriptions[:5]:  # Show first 5
			print(f"      - User: {sub.user}, Plant: {sub.plant_id or 'N/A'}")
	else:
		print("   ℹ️  No active subscriptions found (users need to subscribe from frontend)")
	
	# Test 5: Check notification logs
	print("\n5️⃣ Checking Notification Logs...")
	logs = frappe.get_all(
		"Push Notification Log",
		fields=["name", "user", "title", "status", "sent_at"],
		order_by="creation desc",
		limit=5
	)
	
	if logs:
		print(f"   ✅ Found {len(logs)} recent notification(s):")
		for log in logs:
			print(f"      - {log.title} ({log.status}) - {log.sent_at or 'Not sent'}")
	else:
		print("   ℹ️  No notification logs yet")
	
	# Test 6: Check dependencies
	print("\n6️⃣ Checking Python Dependencies...")
	try:
		import pywebpush
		print(f"   ✅ pywebpush installed (version: {pywebpush.__version__ if hasattr(pywebpush, '__version__') else 'unknown'})")
	except ImportError:
		print("   ❌ pywebpush not installed!")
		print("   Run: bench pip install pywebpush==1.14.0")
	
	try:
		import cryptography
		print(f"   ✅ cryptography installed")
	except ImportError:
		print("   ❌ cryptography not installed!")
	
	print("\n" + "=" * 60)
	print("✅ Setup Test Complete!")
	print("=" * 60)
	print("\n📝 Next Steps:")
	print("   1. Open your app in browser: http://kfltest.localhost:8003/kiosk/")
	print("   2. Click the '🔔 Test Push' button")
	print("   3. Allow notifications when prompted")
	print("   4. Check if notification appears")
	print("\n")


def test_send_notification(user=None):
	"""
	Test sending a push notification
	Run: bench --site [site-name] execute khanal_tech_integrations.utils.test_push_notifications.test_send_notification --kwargs '{"user": "user@example.com"}'
	"""
	if not user:
		user = frappe.session.user
	
	print(f"🧪 Testing push notification to: {user}")
	
	from khanal_tech_integrations.api.push_notifications import send_push_notification_api
	
	result = send_push_notification_api(
		user=user,
		title="🧪 Test Notification",
		message="This is a test push notification from the backend!",
		icon="/icons/icon.svg",
		data={"type": "test", "timestamp": frappe.utils.now()}
	)
	
	print(f"Result: {json.dumps(result, indent=2)}")
	return result

