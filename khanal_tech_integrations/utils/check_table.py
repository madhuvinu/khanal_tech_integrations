#!/usr/bin/env python3
"""
Check the actual table structure
"""
import frappe

def check_table():
    # Check if table exists
    tables = frappe.db.sql("SHOW TABLES LIKE 'tabPush Notification Settings'", as_dict=True)
    print(f"Tables found: {tables}")
    
    # Try to get all data
    try:
        data = frappe.db.sql("SELECT * FROM `tabPush Notification Settings`", as_dict=True)
        print(f"\nData in table: {data}")
    except Exception as e:
        print(f"Error reading table: {e}")
    
    # Check columns
    try:
        columns = frappe.db.sql("SHOW COLUMNS FROM `tabPush Notification Settings`", as_dict=True)
        print(f"\nColumns: {[c['Field'] for c in columns]}")
    except Exception as e:
        print(f"Error getting columns: {e}")

