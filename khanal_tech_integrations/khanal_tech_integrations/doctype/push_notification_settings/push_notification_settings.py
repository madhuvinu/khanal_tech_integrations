# Copyright (c) 2024, Khanal Tech and Contributors
# MIT License

import frappe
from frappe.model.document import Document


class PushNotificationSettings(Document):
	def load_from_db(self):
		"""Override load_from_db to ensure fresh data from database"""
		super().load_from_db()
		
		# Fetch fresh values from database using SQL (bypasses caching)
		result = frappe.db.sql("""
			SELECT vapid_email, vapid_public_key, vapid_private_key 
			FROM `tabPush Notification Settings` 
			WHERE name = 'Push Notification Settings'
		""", as_dict=True)
		
		if result and len(result) > 0:
			self.vapid_email = result[0].get('vapid_email')
			self.vapid_public_key = result[0].get('vapid_public_key')
			self.vapid_private_key = result[0].get('vapid_private_key')
	
	def onload(self):
		"""Load VAPID keys and display info - DO NOT SAVE"""
		# Ensure we have fresh data from database
		result = frappe.db.sql("""
			SELECT vapid_email, vapid_public_key, vapid_private_key 
			FROM `tabPush Notification Settings` 
			WHERE name = 'Push Notification Settings'
		""", as_dict=True)
		
		if result and len(result) > 0:
			self.vapid_email = result[0].get('vapid_email')
			self.vapid_public_key = result[0].get('vapid_public_key')
			vapid_private_key = result[0].get('vapid_private_key')
			self.vapid_private_key = vapid_private_key
			
			# Show masked private key (first 20 chars + ...)
			if vapid_private_key and len(vapid_private_key) > 0:
				self.vapid_private_key_display = vapid_private_key[:20] + "..." + vapid_private_key[-20:] if len(vapid_private_key) > 40 else "***"
			else:
				self.vapid_private_key_display = "Not configured"
		else:
			self.vapid_private_key_display = "Not configured"
		
		# Get active subscriptions count
		active_count = frappe.db.count("Push Subscription", {"is_active": 1})
		self.active_subscriptions_count = active_count
	
	def _migrate_from_site_config(self):
		"""Migrate VAPID keys from site_config.json to this DocType"""
		vapid_email = frappe.conf.get("vapid_email")
		vapid_public_key = frappe.conf.get("vapid_public_key")
		vapid_private_key = frappe.conf.get("vapid_private_key")
		
		if vapid_private_key and vapid_public_key:
			self.vapid_email = vapid_email or "admin@example.com"
			self.vapid_public_key = vapid_public_key
			self.vapid_private_key = vapid_private_key
			self.save(ignore_permissions=True)
			frappe.msgprint("VAPID keys migrated from site_config.json to DocType")
	
	def validate(self):
		"""Validate settings"""
		# Ensure required fields are set
		if not self.vapid_email:
			self.vapid_email = frappe.session.user or "admin@example.com"
	
	@frappe.whitelist()
	def regenerate_vapid_keys(self):
		"""Regenerate VAPID keys and store in DocType only (not site_config)"""
		from khanal_tech_integrations.utils.generate_vapid_keys import generate_vapid_keys
		
		# Get email from current value or user's email
		current_email = self.get('vapid_email')
		if not current_email or current_email == frappe.session.user:
			# Try to get user's email
			user_email = frappe.get_value("User", frappe.session.user, "email")
			email = current_email or user_email or "admin@example.com"
		else:
			email = current_email
		
		# Generate new keys
		private_key, public_key, public_key_base64 = generate_vapid_keys()
		
		# Store in DocType using update() to ensure fields are set
		self.update({
			"vapid_email": email,
			"vapid_public_key": public_key_base64,
			"vapid_private_key": private_key,
			"vapid_private_key_display": private_key[:20] + "..." + private_key[-20:] if len(private_key) > 40 else "***"
		})
		
		# Save all fields at once
		self.save(ignore_permissions=True)
		frappe.db.commit()
		
		frappe.msgprint("VAPID keys regenerated and stored in DocType!")
	
	@frappe.whitelist()
	def send_test_notification(self, user=None):
		"""Send a test push notification"""
		from khanal_tech_integrations.api.push_notifications import send_push_notification_api
		
		if not user:
			user = frappe.session.user
		
		result = send_push_notification_api(
			user=user,
			title=self.test_title or "Test Notification",
			message=self.test_message or "This is a test push notification",
			icon="/icons/icon.svg",
			data={"type": "test", "from": "settings"}
		)
		
		return result

