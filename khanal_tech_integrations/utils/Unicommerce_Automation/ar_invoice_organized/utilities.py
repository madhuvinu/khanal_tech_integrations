import frappe
import logging

logger = logging.getLogger(__name__)

def get_email_recipients():
    """Get default email recipients for notifications"""
    return [
        "yogesha@khanalfoods.com",
        "harsha@khanalfoods.com", 
        "yaknaprabha@khanalfoods.com"
    ]

def get_orders_for_processing(channel_name, start_date, end_date, origin_state_code):
    """
    Get orders for processing, separated by SGST and IGST
    
    Returns:
        tuple: (sgst_orders, igst_orders)
    """
    try:
        # Convert dates
        start_dt = datetime.strptime(start_date, "%d-%m-%Y")
        end_dt = datetime.strptime(end_date, "%d-%m-%Y").replace(hour=23, minute=59, second=59)
        
        # Get SGST orders (same state)
        sgst_orders = frappe.db.get_list('Unicommerce Orders', filters={
            'status': ('in', ['COMPLETE']),
            'channel_name': channel_name,
            'state': origin_state_code,
            'sap_ar_invoice_docentry': "",
            'displayorderdatetime': ('between', [start_dt, end_dt]),
        }, pluck='name')
        
        # Get IGST orders (different state)
        igst_orders = frappe.db.get_list('Unicommerce Orders', filters={
            'status': ('in', ['COMPLETE']),
            'channel_name': channel_name,
            'state': ('not in', [origin_state_code]),
            'sap_ar_invoice_docentry': "",
            'displayorderdatetime': ('between', [start_dt, end_dt]),
        }, pluck='name')
        
        logger.info(f"Retrieved {len(sgst_orders)} SGST orders and {len(igst_orders)} IGST orders")
        return sgst_orders, igst_orders
        
    except Exception as e:
        logger.error(f"Failed to retrieve orders: {str(e)}")
        raise
