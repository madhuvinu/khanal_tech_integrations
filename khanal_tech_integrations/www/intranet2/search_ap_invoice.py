import frappe 


def get_context(context):
    vendorlist = frappe.db.get_list('SAP Vendor Details', fields=['vendor_code', 'vendor_name'])
    context={
        "vendorlist":vendorlist,
    }
    return context