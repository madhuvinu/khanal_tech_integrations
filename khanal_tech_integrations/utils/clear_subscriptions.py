#!/usr/bin/env python3
"""
Clear all push subscriptions so users can re-subscribe with new VAPID keys
Run: bench --site [site-name] execute khanal_tech_integrations.utils.clear_subscriptions.clear_all
"""

import frappe


def clear_all():
    """Clear all push subscriptions"""
    count = frappe.db.count("Push Subscription")
    frappe.db.sql("DELETE FROM `tabPush Subscription`")
    frappe.db.commit()
    print(f"✅ Deleted {count} push subscription(s)")
    print("Users need to click 'Test Push' again to re-subscribe with the new VAPID keys")
    return {"deleted": count}

