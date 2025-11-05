#!/usr/bin/env python3
"""
Script to reload Batch Number Configuration doctype and verify warehouse field
Run with: bench --site [site-name] execute khanal_tech_integrations.reload_doctype.reload
"""
import frappe

def reload():
    """Reload the doctype and verify warehouse field"""
    try:
        # Get the doctype
        doc_type = frappe.get_doc("DocType", "Batch Number Configuration")
        
        # Check if warehouse field exists
        warehouse_field = None
        for field in doc_type.fields:
            if field.fieldname == "warehouse":
                warehouse_field = field
                break
        
        print(f"Checking warehouse field...")
        if warehouse_field:
            print(f"✓ Found warehouse field:")
            print(f"  - Type: {warehouse_field.fieldtype}")
            print(f"  - Label: {warehouse_field.label}")
            print(f"  - Hidden: {getattr(warehouse_field, 'hidden', 'N/A')}")
            print(f"  - Index: {warehouse_field.idx}")
            
            # Ensure it's set correctly
            if warehouse_field.fieldtype != "MultiSelectPill":
                print(f"\n⚠ Fixing field type from '{warehouse_field.fieldtype}' to 'MultiSelectPill'")
                warehouse_field.fieldtype = "MultiSelectPill"
                warehouse_field.hidden = 0
            
            if getattr(warehouse_field, 'hidden', 0) == 1:
                print(f"\n⚠ Field is hidden! Setting hidden=0")
                warehouse_field.hidden = 0
        else:
            print("✗ Warehouse field NOT found! Adding it...")
            doc_type.append("fields", {
                "fieldname": "warehouse",
                "fieldtype": "MultiSelectPill",
                "idx": 4,
                "hidden": 0,
                "label": "Warehouse",
                "options": "NH\nKG",
                "reqd": 1,
                "in_list_view": 1
            })
        
        # Just reload the doctype without saving (field is already correct)
        print("\nReloading doctype...")
        frappe.reload_doc("khanal_tech_integrations", "doctype", "batch_number_configuration", force=True)
        print("✓ Doctype reloaded!")
        
        # Clear all caches
        frappe.clear_cache()
        print("✓ Cache cleared!")
        
        print("\n" + "="*50)
        print("SUCCESS! Please:")
        print("1. Refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)")
        print("2. Check if Warehouse field appears")
        print("="*50)
        
    except Exception as e:
        frappe.log_error(f"Error reloading doctype: {str(e)}", "Doctype Reload Error")
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

