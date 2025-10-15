import frappe
from frappe import _

def get_context(context):
    context.title = "Production Kiosk"
    context.no_cache = 1
    
    # Get site URL for API calls
    context.site_url = frappe.utils.get_url()
    
    return context