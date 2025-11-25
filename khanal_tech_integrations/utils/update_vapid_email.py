"""
Update VAPID email without regenerating keys
Run with: bench --site [site-name] execute khanal_tech_integrations.utils.update_vapid_email.update_email --kwargs '{"email": "your-email@example.com"}'
"""

import frappe


def update_email(email):
    """
    Update VAPID email in Push Notification Settings DocType without regenerating keys
    
    Args:
        email (str): New email address for VAPID
    """
    try:
        if not email:
            frappe.throw("Email address is required")
        
        # Get Push Notification Settings DocType
        settings = frappe.get_single("Push Notification Settings")
        
        # Check if VAPID keys exist
        if not settings.get('vapid_public_key'):
            frappe.throw("VAPID keys not found. Please generate keys first using: bench --site [site] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys")
        
        # Update email
        old_email = settings.get('vapid_email', 'Not set')
        settings.vapid_email = email
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.msgprint(f"""
            <h3>VAPID Email Updated Successfully!</h3>
            <p><strong>Old Email:</strong> {old_email}</p>
            <p><strong>New Email:</strong> {email}</p>
            <p style="color: #27ae60;">✓ Email updated in Push Notification Settings DocType</p>
        """)
        
        return {
            "success": True,
            "old_email": old_email,
            "new_email": email,
            "message": "VAPID email updated successfully in Push Notification Settings DocType"
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating VAPID email: {str(e)}", "VAPID Email Update")
        frappe.throw(f"Failed to update VAPID email: {str(e)}")

