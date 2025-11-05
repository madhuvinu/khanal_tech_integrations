#!/usr/bin/env python3
"""
Fix form layout to ensure warehouse field is visible
Run with: bench --site [site-name] execute khanal_tech_integrations.fix_form_layout.fix
"""
import frappe

def fix():
    """Ensure warehouse field is in form layout"""
    try:
        frappe.connect()
        
        # Get the doctype
        doc_type = frappe.get_doc("DocType", "Batch Number Configuration")
        
        # Check warehouse field
        warehouse_field = [f for f in doc_type.fields if f.fieldname == "warehouse"]
        if not warehouse_field:
            print("✗ Warehouse field not found!")
            return
        
        wf = warehouse_field[0]
        print(f"✓ Found warehouse field:")
        print(f"  - Type: {wf.fieldtype}")
        print(f"  - Hidden: {getattr(wf, 'hidden', 0)}")
        print(f"  - Index: {wf.idx}")
        
        # Ensure field is not hidden and is properly configured
        wf.hidden = 0
        wf.fieldtype = "MultiSelectPill"  # Ensure it's MultiSelectPill
        wf.options = "NH\nKG"
        wf.reqd = 1
        
        # In Frappe, if there's no custom layout, all fields should appear
        # But we can force refresh by reloading
        
        # Save the doctype
        doc_type.save(ignore_permissions=True)
        frappe.db.commit()
        print("\n✓ Saved doctype with warehouse field configuration")
        
        # Force reload
        frappe.reload_doc("khanal_tech_integrations", "doctype", "batch_number_configuration", force=True)
        
        # Clear caches
        frappe.clear_cache()
        
        print("\n" + "="*60)
        print("FIELD CONFIGURED AND RELOADED!")
        print("="*60)
        print("\nIf the field still doesn't appear:")
        print("1. Go to: Customize > DocType > Batch Number Configuration")
        print("2. Click on 'Form' tab")
        print("3. Look for 'warehouse' in the 'Hidden Fields' section")
        print("4. If found there, click on it and click 'Show'")
        print("5. Or click 'Add Field' and search for 'warehouse'")
        print("6. Drag it to the correct position (after 'variant', before 'grams_sku')")
        print("7. Click 'Save'")
        print("8. Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)")
        print("="*60)
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

