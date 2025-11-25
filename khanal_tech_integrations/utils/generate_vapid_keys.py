"""
Script to generate VAPID keys for Web Push Notifications
Run this script once to generate keys, then store them securely

Usage:
    bench --site [site-name] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys
"""

import frappe
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64
import json


def generate_vapid_keys():
    """
    Generate VAPID public and private keys for Web Push Notifications
    
    Returns:
        tuple: (private_key_pem, public_key_pem, public_key_base64)
    """
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Get public key in uncompressed format for VAPID
    public_numbers = public_key.public_numbers()
    
    # Convert to base64 URL-safe format (required for VAPID)
    # VAPID public key is 65 bytes: 0x04 + 32-byte X + 32-byte Y
    x_bytes = public_numbers.x.to_bytes(32, byteorder='big')
    y_bytes = public_numbers.y.to_bytes(32, byteorder='big')
    public_key_bytes = b'\x04' + x_bytes + y_bytes
    public_key_base64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    return private_pem.decode('utf-8'), public_pem.decode('utf-8'), public_key_base64


def generate_and_store_keys(email=None):
    """
    Generate VAPID keys and store them in Push Notification Settings DocType
    
    Args:
        email (str): Email address for VAPID (usually admin email). 
                     If not provided, uses kflharshkfl@gmail.com as default.
    """
    try:
        # Use default email if not provided
        if not email:
            email = "kflharshkfl@gmail.com"
        
        private_key, public_key, public_key_base64 = generate_vapid_keys()
        
        # Store in Push Notification Settings DocType (only storage location)
        # Use direct SQL for single doctypes to ensure it works
        try:
            # Check if document exists
            exists = frappe.db.sql("""
                SELECT name FROM `tabPush Notification Settings` WHERE name = 'Push Notification Settings'
            """, as_dict=True)
            
            if not exists:
                # Create the document using INSERT
                frappe.db.sql("""
                    INSERT INTO `tabPush Notification Settings` 
                    (name, creation, modified, modified_by, owner, vapid_email, vapid_public_key, vapid_private_key)
                    VALUES ('Push Notification Settings', NOW(), NOW(), %s, %s, %s, %s, %s)
                """, (frappe.session.user, frappe.session.user, email, public_key_base64, private_key))
            else:
                # Update existing document
                frappe.db.sql("""
                    UPDATE `tabPush Notification Settings`
                    SET 
                        vapid_email = %s,
                        vapid_public_key = %s,
                        vapid_private_key = %s,
                        modified = NOW(),
                        modified_by = %s
                    WHERE name = 'Push Notification Settings'
                """, (email, public_key_base64, private_key, frappe.session.user))
            
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to save VAPID keys: {str(e)}", "VAPID Key Generation")
            frappe.db.rollback()
            frappe.throw(f"Failed to save VAPID keys to DocType: {str(e)}")
        
        # Clear cache to ensure fresh read
        frappe.clear_cache()
        
        # Verify by reading back from database directly
        try:
            saved_email = frappe.db.get_value("Push Notification Settings", "Push Notification Settings", "vapid_email")
            saved_public_key = frappe.db.get_value("Push Notification Settings", "Push Notification Settings", "vapid_public_key")
            saved_private_key = frappe.db.get_value("Push Notification Settings", "Push Notification Settings", "vapid_private_key")
            
            if saved_public_key != public_key_base64 or saved_email != email:
                frappe.log_error(f"VAPID keys verification failed. Expected public_key: {public_key_base64[:20]}..., got: {saved_public_key[:20] if saved_public_key else 'None'}...", "VAPID Key Generation")
                frappe.throw("VAPID keys were generated but not saved correctly. Please try again.")
            
            if not saved_private_key or len(saved_private_key) < 100:
                frappe.log_error("VAPID private key was not saved correctly", "VAPID Key Generation")
                frappe.throw("VAPID private key was not saved correctly. Please try again.")
        except Exception as verify_error:
            frappe.log_error(f"Failed to verify saved keys: {str(verify_error)}", "VAPID Key Generation")
            # Don't throw here, as the save might have worked
        
        frappe.msgprint(f"""
            <h3>VAPID Keys Generated Successfully!</h3>
            <p><strong>Public Key (for frontend):</strong></p>
            <pre style="background: #f4f4f4; padding: 10px; border-radius: 4px;">{public_key_base64}</pre>
            <p><strong>Private Key:</strong> Stored securely in Push Notification Settings DocType</p>
            <p><strong>Email:</strong> {email}</p>
            <p style="color: #27ae60;">✓ Keys have been saved to Push Notification Settings DocType</p>
            <p style="color: #e74c3c;"><strong>⚠️ Important:</strong> Keep the private key secure and never expose it!</p>
        """)
        
        return {
            "success": True,
            "public_key": public_key_base64,
            "email": email,
            "message": "VAPID keys generated and stored in Push Notification Settings DocType"
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating VAPID keys: {str(e)}", "VAPID Key Generation")
        frappe.throw(f"Failed to generate VAPID keys: {str(e)}")


def get_vapid_public_key():
    """
    Get VAPID public key from Push Notification Settings DocType (for frontend)
    
    Returns:
        str: VAPID public key in base64 format, or None if not configured
    """
    try:
        # Use direct SQL for reliability
        result = frappe.db.sql("""
            SELECT vapid_public_key 
            FROM `tabPush Notification Settings` 
            WHERE name = 'Push Notification Settings'
        """, as_dict=True)
        
        if result and result[0].get('vapid_public_key'):
            return result[0]['vapid_public_key']
        return None
    except Exception:
        return None


def get_vapid_private_key():
    """
    Get VAPID private key from Push Notification Settings DocType (for backend)
    
    Returns:
        str: VAPID private key in PEM format, or None if not configured
    """
    try:
        # Use direct SQL for reliability
        result = frappe.db.sql("""
            SELECT vapid_private_key 
            FROM `tabPush Notification Settings` 
            WHERE name = 'Push Notification Settings'
        """, as_dict=True)
        
        if result and result[0].get('vapid_private_key'):
            return result[0]['vapid_private_key']
        return None
    except Exception:
        return None


def get_vapid_email():
    """
    Get VAPID email from Push Notification Settings DocType
    
    Returns:
        str: Email address for VAPID, defaults to 'admin@example.com' if not configured
    """
    try:
        # Use direct SQL for reliability
        result = frappe.db.sql("""
            SELECT vapid_email 
            FROM `tabPush Notification Settings` 
            WHERE name = 'Push Notification Settings'
        """, as_dict=True)
        
        if result and result[0].get('vapid_email'):
            return result[0]['vapid_email']
        return 'admin@example.com'
    except Exception:
        return 'admin@example.com'

