import frappe
import logging
from datetime import datetime
from .sap_integration import post_invoice_to_sap
from .channel_config import get_channel_configuration, get_sap_state_code
from .order_processing import build_document_lines

logger = logging.getLogger(__name__)

def create_sap_invoice_payload(channel_name, completed_orderlist, bill_to_code, start_date, end_date):
    """Create SAP invoice payload"""
    try:
        # Get channel configuration
        channel_config = get_channel_configuration(channel_name)
        
        # Determine account code and bill to based on tax type
        if bill_to_code == 'B2C SGST ADD':
            account_code = channel_config["account_code_sgst"]
            bill_to = 'Local'
            extra = 'Intra-state'
        else:  # B2C IGST ADD
            account_code = channel_config["account_code_igst"]
            bill_to = 'Central'
            extra = 'Inter-state'
        
        # Build payload header
        comment = f"{extra} Ecommerce B2C orders for {channel_name} from {start_date} to {end_date} Posted Using API from Unicommerce"
        
        payload = {
            "CardCode": channel_config["customer_code"],
            "Comments": comment,
            "PayToCode": bill_to_code,
            "ShipToCode": bill_to_code,
            "DocDate": datetime.strptime(start_date, "%d-%m-%Y").strftime("%Y-%m-%d"),
            "DocDueDate": datetime.strptime(end_date, "%d-%m-%Y").strftime("%Y-%m-%d"),
            "U_BillingFrom": get_sap_state_code(channel_config["origin_state_code"]),
            "U_BillTo": bill_to,
            "TransportationCode": 5,
            "UseBillToAddrToDetermineTax": "tYES",
            "Series": channel_config["series_number"],
            "DocumentLines": []
        }
        
        # Build document lines (this will use cached SAP data)
        payload["DocumentLines"] = build_document_lines(completed_orderlist, channel_config, account_code, bill_to_code)
        
        logger.info(f"Created SAP payload with {len(payload['DocumentLines'])} line items")
        return payload
        
    except Exception as e:
        logger.error(f"Failed to create SAP payload: {str(e)}")
        raise

def update_order_records(order_list, doc_entry, doc_num, sap_response=None):
    """Update Unicommerce order records with SAP invoice details and delivery line numbers"""
    updated_count = 0
    
    for order_id in order_list:
        try:
            order_doc = frappe.get_doc('Unicommerce Orders', order_id)
            
            # Update parent order fields
            order_doc.sap_ar_invoice_docentry = doc_entry
            order_doc.sap_ar_invoice_docnum = doc_num
            
            # Update child table (Order Line Items) with delivery line numbers
            if sap_response and sap_response.get('DocumentLines'):
                update_line_items_with_sap_numbers(order_doc, sap_response)
            
            order_doc.save()
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to update order {order_id}: {str(e)}")
            continue
    
    frappe.db.commit()
    logger.info(f"Updated {updated_count} order records with SAP invoice details")
    return updated_count

def update_line_items_with_sap_numbers(order_doc, sap_response):
    """Update Order Line Items with SAP delivery line numbers using U_Sale_order_itemcode mapping"""
    try:
        # Get SAP document lines from response
        sap_lines = sap_response.get('DocumentLines', [])
        
        # Create mapping using U_Sale_order_itemcode as the key
        # This ensures exact matching between our line items and SAP lines
        sap_line_mapping = {}
        for sap_line in sap_lines:
            sale_order_itemcode = sap_line.get('U_Sale_order_itemcode', '')
            line_num = sap_line.get('LineNum', '')
            item_code = sap_line.get('ItemCode', '')
            
            if sale_order_itemcode and line_num:
                sap_line_mapping[sale_order_itemcode] = {
                    'LineNum': line_num,
                    'ItemCode': item_code
                }
                logger.info(f"Mapped SAP line: U_Sale_order_itemcode={sale_order_itemcode}, LineNum={line_num}, ItemCode={item_code}")
        
        logger.info(f"Created mapping for {len(sap_line_mapping)} SAP lines against {len(order_doc.line_items)} order line items")
        
        # Update each line item using U_Sale_order_itemcode mapping
        for line_item in order_doc.line_items:
            try:
                # Skip cancelled items
                if getattr(line_item, 'cancellationreason', None):
                    continue
                
                # Update SAP reference fields
                line_item.sap_delivery_no = sap_response.get('DocNum', '')
                line_item.sap_invoice_no = sap_response.get('DocNum', '')
                line_item.sap_filled_status = "Completed"
                
                # Get the sale order item code for this line item
                sale_order_itemcode = getattr(line_item, 'code', '')
                
                # Find matching SAP line using U_Sale_order_itemcode
                if sale_order_itemcode in sap_line_mapping:
                    sap_data = sap_line_mapping[sale_order_itemcode]
                    line_item.delivery_linenum = sap_data['LineNum']
                    logger.info(f"✅ Updated line item {getattr(line_item, 'itemsku', 'unknown')} (code: {sale_order_itemcode}) with LineNum: {sap_data['LineNum']} (SAP ItemCode: {sap_data['ItemCode']})")
                else:
                    line_item.delivery_linenum = ""
                    logger.warning(f"⚠️  No SAP line found for U_Sale_order_itemcode: {sale_order_itemcode} - item: {getattr(line_item, 'itemsku', 'unknown')}")
                
            except Exception as line_error:
                logger.error(f"❌ Failed to update line item {getattr(line_item, 'itemsku', 'unknown')}: {str(line_error)}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to update line items for order {order_doc.name}: {str(e)}")
        raise

def process_order_batch(channel_name, order_list, bill_to_code, start_date, end_date):
    """
    Process a batch of orders for invoice creation with optimized SAP calls
    
    Args:
        channel_name (str): Channel name
        order_list (list): List of order IDs
        bill_to_code (str): Bill to code (SGST or IGST)
        start_date (str): Start date in DD-MM-YYYY format
        end_date (str): End date in DD-MM-YYYY format
        
    Returns:
        dict: Processing result
    """
    logger.info(f"Processing {len(order_list)} orders for {channel_name} ({bill_to_code})")
    
    try:
        # Create SAP payload (this will batch preload SAP data)
        payload = create_sap_invoice_payload(channel_name, order_list, bill_to_code, start_date, end_date)
        
        # Validate batch availability
        from .batch_validation import validate_batch_availability
        failed_items, available_items = validate_batch_availability(payload, channel_name, order_list)
        
        if failed_items:
            error_msg = f"Batch validation failed for {len(failed_items)} items"
            logger.error(error_msg)
            from .error_handling import send_batch_quantity_alert, create_batch_hold_record
            send_batch_quantity_alert(failed_items, channel_name)
            create_batch_hold_record(failed_items, channel_name, order_list, payload)
            return {"error": error_msg, "failed_items": failed_items}
        
        # Post to SAP (uses cached session)
        result = post_invoice_to_sap(payload)
        
        if result.get('DocEntry'):
            # Update order records with SAP response for delivery line numbers
            update_order_records(order_list, result['DocEntry'], result['DocNum'], result)
            
            # Send success notification
            from .error_handling import send_success_notification
            send_success_notification(channel_name, result['DocNum'], payload)
            
            logger.info(f"Successfully processed {len(order_list)} orders - DocNum: {result['DocNum']}")
        else:
            # Send failure notification
            error_msg = result.get('error', 'Unknown SAP error')
            from .error_handling import send_failure_notification
            send_failure_notification(channel_name, error_msg, payload)
        
        return result
        
    except Exception as e:
        error_msg = f"Order processing failed: {str(e)}"
        logger.error(error_msg)
        from .error_handling import send_failure_notification
        send_failure_notification(channel_name, error_msg)
        return {"error": error_msg}
