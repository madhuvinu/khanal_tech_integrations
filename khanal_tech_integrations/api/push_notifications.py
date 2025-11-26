# Copyright (c) 2024, Khanal Tech and Contributors
# MIT License

from __future__ import unicode_literals
import frappe
import json
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from py_vapid import Vapid01
import logging

logger = logging.getLogger(__name__)


@frappe.whitelist(allow_guest=False)
def subscribe_push_api(subscription, plant_id=None, device_info=None):
	"""
	Subscribe user to push notifications
	POST /api/method/khanal_tech_integrations.api.push_notifications.subscribe_push_api
	
	Args:
		subscription: JSON string of push subscription object
		plant_id: Optional plant ID
		device_info: Optional device information JSON
	"""
	try:
		user = frappe.session.user
		
		if not subscription:
			return {"success": False, "message": "Subscription data is required"}
		
		# Parse subscription if it's a string
		if isinstance(subscription, str):
			subscription_data = json.loads(subscription)
		else:
			subscription_data = subscription
		
		endpoint = subscription_data.get("endpoint")
		keys = subscription_data.get("keys", {})
		
		if not endpoint:
			return {"success": False, "message": "Endpoint is required"}
		
		# Check if subscription already exists for this endpoint (regardless of user)
		# This handles the case where the same browser/device is used by different users
		existing = frappe.db.get_value(
			"Push Subscription",
			{"endpoint": endpoint},
			"name"
		)
		
		if existing:
			# Update existing subscription - also update the user to current session user
			doc = frappe.get_doc("Push Subscription", existing)
			doc.user = user  # Update user to current logged-in user
			doc.keys = json.dumps(keys)
			doc.is_active = 1
			doc.plant_id = plant_id
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"success": True,
				"message": "Subscription updated",
				"subscription_id": doc.name,
				"user": user
			}
		else:
			# Create new subscription
			# Get user agent safely (frappe.request may not be available in all contexts)
			user_agent = ""
			try:
				if hasattr(frappe, 'request') and frappe.request:
					user_agent = frappe.request.headers.get("User-Agent", "")
			except:
				pass
			
			# Parse device_info if provided
			device_info_json = None
			if device_info:
				if isinstance(device_info, str):
					device_info_json = device_info
				else:
					device_info_json = json.dumps(device_info)
			
			doc = frappe.get_doc({
				"doctype": "Push Subscription",
				"user": user,
				"endpoint": endpoint,
				"keys": json.dumps(keys),
				"user_agent": user_agent,
				"device_info": device_info_json,
				"plant_id": plant_id,
				"is_active": 1
			})
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				"success": True,
				"message": "Subscription created",
				"subscription_id": doc.name
			}
			
	except Exception as e:
		logger.error(f"Error subscribing to push: {str(e)}", exc_info=True)
		frappe.log_error(f"Push subscription error: {str(e)}")
		return {"success": False, "message": str(e)}


@frappe.whitelist(allow_guest=False)
def unsubscribe_push_api(endpoint=None):
	"""
	Unsubscribe user from push notifications
	POST /api/method/khanal_tech_integrations.api.push_notifications.unsubscribe_push_api
	"""
	try:
		user = frappe.session.user
		
		if endpoint:
			# Unsubscribe specific endpoint
			existing = frappe.db.get_value(
				"Push Subscription",
				{"endpoint": endpoint, "user": user},
				"name"
			)
		else:
			# Unsubscribe all for user
			existing = frappe.db.get_value(
				"Push Subscription",
				{"user": user, "is_active": 1},
				"name"
			)
		
		if existing:
			doc = frappe.get_doc("Push Subscription", existing)
			doc.is_active = 0
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {"success": True, "message": "Unsubscribed successfully"}
		else:
			return {"success": False, "message": "No active subscription found"}
			
	except Exception as e:
		logger.error(f"Error unsubscribing from push: {str(e)}", exc_info=True)
		frappe.log_error(f"Push unsubscribe error: {str(e)}")
		return {"success": False, "message": str(e)}


@frappe.whitelist(allow_guest=True)
def get_vapid_public_key_api():
	"""
	Get VAPID public key for push subscription
	GET /api/method/khanal_tech_integrations.api.push_notifications.get_vapid_public_key_api
	"""
	try:
		# Get from DocType using direct SQL, fallback to site_config
		try:
			result = frappe.db.sql("""
				SELECT vapid_public_key 
				FROM `tabPush Notification Settings` 
				WHERE name = 'Push Notification Settings'
			""", as_dict=True)
			if result and result[0].get('vapid_public_key'):
				vapid_public_key = result[0]['vapid_public_key']
			else:
				vapid_public_key = None
		except:
			vapid_public_key = frappe.conf.get("vapid_public_key")
		
		if not vapid_public_key:
			return {
				"success": False,
				"message": "VAPID keys not configured. Please run: bench --site [site] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys"
			}
		
		return {
			"success": True,
			"public_key": vapid_public_key
		}
		
	except Exception as e:
		logger.error(f"Error getting VAPID key: {str(e)}", exc_info=True)
		return {"success": False, "message": str(e)}


@frappe.whitelist(allow_guest=False)
def send_push_notification_api(user=None, title="", message="", icon=None, badge=None, data=None, plant_id=None, broadcast=False):
	"""
	Send push notification to user(s)
	POST /api/method/khanal_tech_integrations.api.push_notifications.send_push_notification_api
	
	Args:
		user: User email (defaults to current user)
		title: Notification title
		message: Notification message
		icon: Icon URL
		badge: Badge URL
		data: Additional data (dict)
		plant_id: Optional plant filter
		broadcast: If True, send to ALL active subscriptions (for alerts)
	"""
	try:
		# Always use session user for consistency (subscriptions are created with session user)
		session_user = frappe.session.user
		
		# Handle broadcast mode - send to all users
		if broadcast or (isinstance(broadcast, str) and broadcast.lower() == 'true'):
			logger.info(f"Broadcast mode: sending to all active subscriptions")
			user = None  # Will fetch all subscriptions
		elif not user:
			user = session_user
		# If user is provided but different from session, log it (admin sending to another user)
		elif user.lower() != session_user.lower():
			logger.info(f"Admin {session_user} sending notification to {user}")
		
		# Get VAPID keys from Push Notification Settings DocType using direct SQL
		# Fallback to site_config for backward compatibility
		try:
			result = frappe.db.sql("""
				SELECT vapid_email, vapid_public_key, vapid_private_key 
				FROM `tabPush Notification Settings` 
				WHERE name = 'Push Notification Settings'
			""", as_dict=True)
			
			if result and len(result) > 0:
				vapid_email = result[0].get('vapid_email') or "admin@example.com"
				vapid_public_key = result[0].get('vapid_public_key')
				vapid_private_key = result[0].get('vapid_private_key')
				
				# Log for debugging
				if vapid_private_key:
					logger.info(f"Retrieved VAPID key from DocType: length={len(vapid_private_key)}, has_newlines={'\\n' in str(vapid_private_key)}")
				else:
					logger.warning("No VAPID private key found in DocType")
			else:
				# No data found, fallback to site_config
				vapid_email = frappe.conf.get("vapid_email", "admin@example.com")
				vapid_public_key = frappe.conf.get("vapid_public_key")
				vapid_private_key = frappe.conf.get("vapid_private_key")
		except Exception as e:
			logger.error(f"Error getting VAPID keys from DocType: {str(e)}")
			# Fallback to site_config
			vapid_email = frappe.conf.get("vapid_email", "admin@example.com")
			vapid_public_key = frappe.conf.get("vapid_public_key")
			vapid_private_key = frappe.conf.get("vapid_private_key")
		
		if not vapid_private_key or not vapid_public_key:
			logger.error("VAPID keys not found in DocType or site_config")
			return {
				"success": False,
				"message": "VAPID keys not configured. Please go to 'Push Notification Settings' DocType and click 'Regenerate VAPID Keys' button."
			}
		
		# Ensure VAPID private key is properly formatted
		# When stored in DocType Text field, newlines are preserved correctly
		# But we need to ensure it's a string and properly formatted
		if isinstance(vapid_private_key, bytes):
			vapid_private_key = vapid_private_key.decode('utf-8')
		
		vapid_private_key = str(vapid_private_key).strip()
		
		# Replace escaped newlines with actual newlines (in case stored as JSON string)
		if '\\n' in vapid_private_key:
			vapid_private_key = vapid_private_key.replace('\\n', '\n')
		
		# Validate key format before processing
		if not vapid_private_key.startswith('-----BEGIN PRIVATE KEY-----'):
			logger.error(f"Invalid VAPID key format - doesn't start with BEGIN marker. First 50 chars: {repr(vapid_private_key[:50])}")
			return {
				"success": False,
				"message": "Invalid VAPID private key format. Please regenerate keys in Push Notification Settings."
			}
		
		# Convert PEM key to DER base64url format (required by pywebpush)
		import base64
		vapid_private_key_der_b64 = None
		try:
			# Load PEM key
			key_obj = serialization.load_pem_private_key(
				vapid_private_key.encode('utf-8'),
				password=None,
				backend=default_backend()
			)
			# Convert to DER format
			der_key = key_obj.private_bytes(
				encoding=serialization.Encoding.DER,
				format=serialization.PrivateFormat.PKCS8,
				encryption_algorithm=serialization.NoEncryption()
			)
			# Base64url encode (without padding)
			vapid_private_key_der_b64 = base64.urlsafe_b64encode(der_key).decode('utf-8').rstrip('=')
			logger.info(f"VAPID key converted to DER base64url format (length: {len(vapid_private_key_der_b64)})")
		except Exception as e:
			logger.error(f"Failed to convert VAPID key to DER format: {str(e)}")
			return {
				"success": False,
				"message": f"Invalid VAPID private key format. Please regenerate keys in Push Notification Settings. Error: {str(e)}"
			}
		
		# Get subscriptions based on mode
		filters = {"is_active": 1}
		if plant_id:
			filters["plant_id"] = plant_id
		
		if user is None:
			# Broadcast mode - get ALL active subscriptions
			subscriptions = frappe.get_all(
				"Push Subscription",
				filters=filters,
				fields=["name", "endpoint", "keys", "user"]
			)
			logger.info(f"Broadcast: Found {len(subscriptions)} active subscriptions")
		else:
			# Single user mode - try exact match first
			filters["user"] = user
			subscriptions = frappe.get_all(
				"Push Subscription",
				filters=filters,
				fields=["name", "endpoint", "keys"]
			)
			
			# If no exact match, try case-insensitive search
			if not subscriptions:
				all_active_subs = frappe.get_all(
					"Push Subscription",
					filters={k: v for k, v in filters.items() if k != "user"},
					fields=["name", "endpoint", "keys", "user"]
				)
				# Filter by case-insensitive user match
				subscriptions = [s for s in all_active_subs if s.user and s.user.lower() == user.lower()]
				# Remove user field from result
				for sub in subscriptions:
					sub.pop('user', None)
			
			# If still no match and user != session_user, try session_user
			if not subscriptions and user.lower() != session_user.lower():
				logger.info(f"No subscriptions for {user}, trying session user {session_user}")
				filters["user"] = session_user
				subscriptions = frappe.get_all(
					"Push Subscription",
					filters=filters,
					fields=["name", "endpoint", "keys"]
				)
		
		if not subscriptions:
			# Log available users for debugging
			available_users = frappe.db.sql(
				"SELECT DISTINCT user FROM `tabPush Subscription` WHERE is_active=1",
				as_dict=True
			)
			user_list = [u.user for u in available_users]
			logger.warning(f"No active subscriptions found for user {user} (session: {session_user}). Available users: {user_list}")
			return {
				"success": False,
				"message": f"No active subscriptions found for user {user}. Please subscribe first by clicking the 'Test Push' button. Available users: {', '.join(user_list[:5])}",
				"sent_count": 0,
				"failed_count": 0
			}
		
		# Prepare notification payload
		payload = {
			"title": title,
			"body": message,
			"icon": icon or "/assets/khanal_tech_integrations/images/favicon.png",
			"badge": badge or "/assets/khanal_tech_integrations/images/favicon.png",
			"data": data or {}
		}
		
		# VAPID claims
		vapid_claims = {
			"sub": f"mailto:{vapid_email}"
		}
		
		sent_count = 0
		failed_count = 0
		errors = []
		
		# Send to each subscription
		for sub in subscriptions:
			try:
				# Get keys - they're stored as JSON string in the database
				keys_str = sub.get("keys", "{}")
				if isinstance(keys_str, str):
					keys = json.loads(keys_str)
				else:
					keys = keys_str
				
				endpoint = sub.get("endpoint")
				
				if not endpoint or not keys:
					continue
				
				# Ensure keys are in the correct format for pywebpush
				# pywebpush expects keys as a dict with 'p256dh' and 'auth' as base64url strings
				if not isinstance(keys, dict):
					raise ValueError(f"Keys must be a dict, got {type(keys)}")
				
				if "p256dh" not in keys or "auth" not in keys:
					raise ValueError(f"Keys missing required fields. Got: {list(keys.keys())}")
				
				# Send push notification using DER base64url key
				webpush(
					subscription_info={
						"endpoint": endpoint,
						"keys": keys
					},
					data=json.dumps(payload),
					vapid_private_key=vapid_private_key_der_b64,  # Use DER base64url format
					vapid_claims=vapid_claims
				)
				
				sent_count += 1
				
				# Update last_notified
				frappe.db.set_value("Push Subscription", sub.name, "last_notified", frappe.utils.now())
				
			except WebPushException as e:
				failed_count += 1
				error_msg = str(e)
				# Check if it's a key mismatch error (subscription created with different VAPID key)
				if "401" in error_msg or "Unauthorized" in error_msg or "Invalid" in error_msg:
					error_msg += " (Subscription may be invalid - user needs to re-subscribe after VAPID key regeneration)"
				errors.append(f"Subscription {sub.name}: {error_msg}")
				logger.error(f"WebPushException for subscription {sub.name}: {error_msg}")
				
				# If subscription is invalid, deactivate it
				if "410" in error_msg or "Gone" in error_msg:
					frappe.db.set_value("Push Subscription", sub.name, "is_active", 0)
					
			except Exception as e:
				failed_count += 1
				errors.append(f"Subscription {sub.name}: {str(e)}")
		
		frappe.db.commit()
		
		# Log notification
		try:
			log_doc = frappe.get_doc({
				"doctype": "Push Notification Log",
				"user": user,
				"title": title,
				"message": message,
				"icon": icon,
				"badge": badge,
				"data": json.dumps(data or {}),
				"status": "Sent" if sent_count > 0 else "Failed",
				"sent_at": frappe.utils.now()
			})
			if errors:
				log_doc.error_message = "\n".join(errors)
			log_doc.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as log_error:
			logger.error(f"Error logging notification: {str(log_error)}")
		
		return {
			"success": True,
			"message": f"Sent {sent_count} notification(s), {failed_count} failed",
			"sent_count": sent_count,
			"failed_count": failed_count,
			"errors": errors if errors else None
		}
		
	except Exception as e:
		logger.error(f"Error sending push notification: {str(e)}", exc_info=True)
		frappe.log_error(f"Push notification error: {str(e)}")
		return {
			"success": False,
			"message": str(e),
			"sent_count": 0,
			"failed_count": 0
		}
