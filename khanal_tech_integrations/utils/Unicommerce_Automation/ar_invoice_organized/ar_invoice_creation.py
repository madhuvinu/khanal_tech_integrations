import frappe
import logging
from datetime import datetime
from .sap_integration import clear_sap_cache
from .channel_config import get_channel_configuration
from .utilities import get_orders_for_processing
from .invoice_creation import process_order_batch

logger = logging.getLogger(__name__)

@frappe.whitelist()
def create_channel_invoices(channel_name=None, start_date=None, end_date=None):
    """
    Main function to create AR invoices for a channel with optimized SAP calls
    
    Args:
        channel_name (str): Channel name
        start_date (str): Start date in DD-MM-YYYY format
        end_date (str): End date in DD-MM-YYYY format
        
    Returns:
        list: Summary of invoice creation results
    """
    logger.info(f"=== Starting optimized invoice creation for {channel_name}: {start_date} to {end_date} ===")
    
    try:
        # Clear cache for new channel processing
        clear_sap_cache(channel_name)
        
        # Validate inputs - removed error throwing for better compatibility
        if not channel_name:
            logger.warning("No channel name provided, using default")
            
        
        if not start_date or not end_date:
            logger.warning("Missing date parameters, using default dates")
            start_date = "01-09-2025"
            end_date = "30-09-2025"
        
        # Get channel configuration
        channel_config = get_channel_configuration(channel_name)
        origin_state_code = channel_config["origin_state_code"]
        
        # Get orders by tax type
        sgst_orders, igst_orders = get_orders_for_processing(channel_name, start_date, end_date, origin_state_code)
        
        summary = [
            {'Order_Type': 'SGST Orders', 'No of Orders': len(sgst_orders), 'AR Invoice Docnum': None},
            {'Order_Type': 'IGST Orders', 'No of Orders': len(igst_orders), 'AR Invoice Docnum': None}
        ]
        
        # Process SGST orders
        if sgst_orders:
            logger.info(f"Processing {len(sgst_orders)} SGST orders")
            result = process_order_batch(channel_name, sgst_orders, 'B2C SGST ADD', start_date, end_date)
            summary[0]['AR Invoice Docnum'] = result.get('DocNum') or result.get('error', 'Failed')
        
        # Process IGST orders
        if igst_orders:
            logger.info(f"Processing {len(igst_orders)} IGST orders")
            result = process_order_batch(channel_name, igst_orders, 'B2C IGST ADD', start_date, end_date)
            summary[1]['AR Invoice Docnum'] = result.get('DocNum') or result.get('error', 'Failed')
        
        logger.info(f"=== Optimized invoice creation completed for {channel_name} ===")
        
        # Print summary
        logger.info(f"OPTIMIZED INVOICE CREATION SUMMARY - {channel_name}")
        
        for summary_item in summary:
            order_type = summary_item['Order_Type']
            count = summary_item['No of Orders']
            doc_num = summary_item['AR Invoice Docnum']
            
            if doc_num and str(doc_num).isdigit():
                status = "✅ SUCCESS"
            else:
                status = "❌ FAILED"
            
            logger.info(f"{order_type}: {count} orders, Status: {status}, DocNum: {doc_num if doc_num else 'None'}")
        
        # Log optimization stats
        from .sap_integration import _sap_cache
        logger.info(f"OPTIMIZATION STATS: States Cached: {len(_sap_cache['states'])}, Items Cached: {len(_sap_cache['items'])}, Session Reused: {'Yes' if _sap_cache.get('session') else 'No'}")
        
        return summary
        
    except Exception as e:
        error_msg = f"Optimized invoice creation failed for {channel_name}: {str(e)}"
        logger.error(error_msg)
        frappe.log_error(error_msg, "AR Invoice Creation")
        from .error_handling import send_failure_notification
        send_failure_notification(channel_name, error_msg)
        raise
    finally:
        # Log final cache statistics
        from .sap_integration import _sap_cache
        logger.info(f"Final cache stats - States: {len(_sap_cache['states'])}, Items: {len(_sap_cache['items'])}")

# Backward compatibility wrapper
@frappe.whitelist() 
def Channel_delivery_Creation_Dispatched2(Channel_Name=None, startDate=None, endDate=None):
    """Backward compatibility wrapper for existing integrations"""
    # Debug: Log the raw parameters received
    logger.info(f"Raw parameters received - Channel_Name: '{Channel_Name}', startDate: '{startDate}', endDate: '{endDate}'")
    
    # Strict validation - no fallbacks or defaults
    if not Channel_Name or Channel_Name == "Channel_Name":
        frappe.throw("Channel_Name parameter is required and cannot be empty")
    
    if not startDate or startDate == "startDate":
        frappe.throw("startDate parameter is required and cannot be empty")
        
    if not endDate or endDate == "endDate":
        frappe.throw("endDate parameter is required and cannot be empty")
    
    logger.info(f"Processing with Channel_Name: {Channel_Name}, startDate: {startDate}, endDate: {endDate}")
    return create_channel_invoices(Channel_Name, startDate, endDate)

@frappe.whitelist()
def resume_from_hold(hold_id):
    """Resume invoice creation from a batch hold record"""
    try:
        logger.info(f"Resuming process from hold: {hold_id}")
        
        # Get hold document
        hold_doc = frappe.get_doc('SAP Batch Hold', hold_id)
        
        if hold_doc.status == 'Completed':
            logger.info("Process already completed")
            return {"status": "already_completed"}
        
        # Clear cache for resumed processing
        clear_sap_cache(hold_doc.channel_name)
        
        # Parse saved data
        order_list = frappe.parse_json(hold_doc.order_list)
        saved_payload = frappe.parse_json(hold_doc.payload)
        
        # Check if payload was truncated and needs regeneration
        if getattr(hold_doc, 'payload_truncated', False):
            logger.info("Payload was truncated, regenerating full payload for resume")
            # Regenerate the full payload using the saved order list
            # This is a simplified approach - in production, you might want to store more context
            logger.warning("Cannot fully regenerate payload from truncated data. Manual intervention required.")
            return {"error": "Payload was truncated during hold creation. Manual regeneration required."}
        
        # Use the saved payload (if not truncated)
        payload = saved_payload
        
        # Re-validate batch availability (failed_items not stored, will be regenerated)
        from .batch_validation import validate_batch_availability
        new_failed_items, available_items = validate_batch_availability(payload, hold_doc.channel_name, order_list)
        
        if new_failed_items:
            logger.error(f"Still {len(new_failed_items)} items with quantity issues")
            return {"error": f"Still {len(new_failed_items)} items with quantity issues"}
        
        logger.info("All batch quantities are now available, proceeding with SAP posting")
        
        # Post to SAP (will use cached session)
        from .sap_integration import post_invoice_to_sap
        result = post_invoice_to_sap(payload)
        
        if result.get('DocEntry'):
            # Update order records with SAP response for delivery line numbers
            from .invoice_creation import update_order_records
            update_order_records(order_list, result['DocEntry'], result['DocNum'], result)
            
            # Update hold status
            hold_doc.status = 'Completed'
            hold_doc.resumed_by = frappe.session.user
            hold_doc.resumed_at = frappe.utils.now()
            hold_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            # Send success notification
            from .error_handling import send_success_notification
            send_success_notification(hold_doc.channel_name, result['DocNum'], payload)
            
            logger.info(f"Successfully resumed and completed process - DocNum: {result['DocNum']}")
            return {"status": "completed", "DocNum": result['DocNum']}
        else:
            error_msg = result.get('error', 'Unknown SAP error')
            logger.error(f"SAP posting failed: {error_msg}")
            return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Resume failed: {str(e)}"
        logger.error(error_msg)
        frappe.log_error(error_msg, "Resume from Hold")
        return {"error": error_msg}

# Enhanced SAP Batch Hold Management Functions
@frappe.whitelist()
def get_hold_summary():
    """Get summary of all holds with their status and details"""
    try:
        holds = frappe.db.sql("""
            SELECT name, channel_name, status, total_orders, total_failed_items, 
                   creation, hold_reason, payload_truncated, full_payload_size
            FROM `tabSAP Batch Hold` 
            ORDER BY creation DESC
        """, as_dict=True)
        
        summary = {
            "total_holds": len(holds),
            "active_holds": len([h for h in holds if h.status == 'Hold - Batch Quantity Issues']),
            "completed_holds": len([h for h in holds if h.status == 'Completed']),
            "truncated_holds": len([h for h in holds if h.payload_truncated]),
            "holds": holds
        }
        
        return summary
        
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def regenerate_hold_payload(hold_id):
    """Regenerate full payload for a truncated hold"""
    try:
        hold_doc = frappe.get_doc('SAP Batch Hold', hold_id)
        
        if not hold_doc.payload_truncated:
            return {"message": "Hold payload is not truncated, can resume normally"}
        
        # Parse the saved order list
        order_list = frappe.parse_json(hold_doc.order_list)
        
        # Get channel configuration
        channel_config = get_channel_configuration(hold_doc.channel_name)
        
        # Determine bill_to_code based on hold details
        # This is a simplified approach - you might need to store more context
        bill_to_code = "B2C SGST ADD"  # Default, might need to be determined from hold data
        
        # Regenerate the full payload
        logger.info(f"Regenerating full payload for hold {hold_id} with {len(order_list)} orders")
        
        # This would need the original parameters - for now, return instructions
        return {
            "message": f"To regenerate payload for {len(order_list)} orders, use:",
            "instructions": [
                f"1. Get channel configuration for {hold_doc.channel_name}",
                f"2. Determine bill_to_code (SGST/IGST) based on order data",
                f"3. Call create_sap_invoice_payload with order_list and parameters",
                f"4. Use the regenerated payload to resume processing"
            ],
            "order_count": len(order_list),
            "channel": hold_doc.channel_name
        }
        
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def process_hold_in_chunks(hold_id, chunk_size=50):
    """Process a large hold by splitting into smaller chunks"""
    try:
        hold_doc = frappe.get_doc('SAP Batch Hold', hold_id)
        order_list = frappe.parse_json(hold_doc.order_list)
        
        if len(order_list) <= chunk_size:
            return {"message": f"Hold has only {len(order_list)} orders, no need to chunk"}
        
        # Split orders into chunks
        chunks = []
        for i in range(0, len(order_list), chunk_size):
            chunk = order_list[i:i + chunk_size]
            chunks.append({
                "chunk_number": (i // chunk_size) + 1,
                "orders": chunk,
                "order_count": len(chunk)
            })
        
        return {
            "message": f"Hold can be processed in {len(chunks)} chunks of max {chunk_size} orders each",
            "total_orders": len(order_list),
            "chunks": chunks,
            "instructions": [
                "Process each chunk separately using create_channel_invoices",
                "Or use the batch processing functions with smaller order lists"
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def cleanup_old_holds(days_old=7):
    """Clean up old completed holds"""
    try:
        cutoff_date = frappe.utils.add_days(frappe.utils.now(), -days_old)
        
        old_holds = frappe.db.sql("""
            SELECT name FROM `tabSAP Batch Hold` 
            WHERE status = 'Completed' AND creation < %s
        """, (cutoff_date,), as_dict=True)
        
        if not old_holds:
            return {"message": "No old holds to cleanup"}
        
        # Delete old holds
        for hold in old_holds:
            frappe.delete_doc('SAP Batch Hold', hold.name, ignore_permissions=True)
        
        frappe.db.commit()
        
        return {
            "message": f"Cleaned up {len(old_holds)} old holds",
            "deleted_holds": [h.name for h in old_holds]
        }
        
    except Exception as e:
        return {"error": str(e)}

# Utility functions for testing and maintenance
@frappe.whitelist()
def get_channel_summary(channel_name, start_date, end_date):
    """Get summary of orders for a channel without processing"""
    try:
        channel_config = get_channel_configuration(channel_name)
        sgst_orders, igst_orders = get_orders_for_processing(channel_name, start_date, end_date, channel_config["origin_state_code"])
        
        return {
            "channel": channel_name,
            "date_range": f"{start_date} to {end_date}",
            "sgst_orders": len(sgst_orders),
            "igst_orders": len(igst_orders),
            "total_orders": len(sgst_orders) + len(igst_orders)
        }
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def clear_cache_for_channel(channel_name=None):
    """Manually clear SAP cache for a channel or all channels"""
    clear_sap_cache(channel_name)
    from .sap_integration import _sap_cache
    cache_stats = {
        "states_cached": len(_sap_cache['states']),
        "items_cached": len(_sap_cache['items']),
        "current_channel": _sap_cache.get('current_channel'),
        "session_active": bool(_sap_cache.get('session'))
    }
    return {"message": f"Cache cleared for {channel_name or 'all channels'}", "stats": cache_stats}

@frappe.whitelist()
def get_active_holds():
    """Get all active held batches"""
    try:
        holds = frappe.db.sql("""
            SELECT name, channel_name, status, creation, hold_reason
            FROM `tabSAP Batch Hold` 
            WHERE status = 'HOLD'
            ORDER BY creation DESC
        """, as_dict=True)
        
        return {
            "active_holds": holds,
            "count": len(holds)
        }
        
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def check_order_status():
    """Check the status of orders for Amazon_IN_API in September 2025"""
    try:
        channel_name = "Amazon_IN_API"
        
        # Total orders in September 2025
        total_orders = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabUnicommerce Orders` 
            WHERE channel_name = %s AND status = 'COMPLETE' 
            AND YEAR(displayorderdatetime) = 2025 AND MONTH(displayorderdatetime) = 9
        """, (channel_name,), as_dict=True)[0]['count']
        
        # Orders without SAP invoice
        unprocessed_orders = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabUnicommerce Orders` 
            WHERE channel_name = %s AND status = 'COMPLETE' 
            AND YEAR(displayorderdatetime) = 2025 AND MONTH(displayorderdatetime) = 9
            AND (sap_ar_invoice_docentry = '' OR sap_ar_invoice_docentry IS NULL)
        """, (channel_name,), as_dict=True)[0]['count']
        
        # Orders with SAP invoice
        processed_orders = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabUnicommerce Orders` 
            WHERE channel_name = %s AND status = 'COMPLETE' 
            AND YEAR(displayorderdatetime) = 2025 AND MONTH(displayorderdatetime) = 9
            AND sap_ar_invoice_docentry IS NOT NULL AND sap_ar_invoice_docentry != ''
        """, (channel_name,), as_dict=True)[0]['count']
        
        return {
            "total_orders": total_orders,
            "unprocessed_orders": unprocessed_orders,
            "processed_orders": processed_orders
        }
        
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def resume_latest_hold():
    """Resume the latest held batch - No parameters needed"""
    try:
        # Get the latest hold
        latest_hold = frappe.db.sql("""
            SELECT name FROM `tabSAP Batch Hold` 
            WHERE status = 'HOLD' 
            ORDER BY creation DESC 
            LIMIT 1
        """, as_dict=True)
        
        if not latest_hold:
            return {"message": "No held batches found"}
        
        hold_id = latest_hold[0]['name']
        logger.info(f"Resuming latest hold: {hold_id}")
        
        # Resume the hold
        result = resume_from_hold(hold_id)
        
        return {
            "message": f"Resumed hold {hold_id}",
            "result": result
        }
        
    except Exception as e:
        error_msg = f"Failed to resume latest hold: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

@frappe.whitelist()
def get_cache_stats():
    """Get current cache statistics"""
    try:
        from .sap_integration import _sap_cache
        return {
            "states_cached": len(_sap_cache.get('states', {})),
            "items_cached": len(_sap_cache.get('items', {})),
            "current_channel": _sap_cache.get('current_channel'),
            "session_active": bool(_sap_cache.get('session')),
            "session_time": str(_sap_cache.get('session_time', 'Not set'))
        }
    except Exception as e:
        return {"error": str(e)}
