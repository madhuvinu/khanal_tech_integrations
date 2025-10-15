import frappe
import logging
from .sap_integration import batch_preload_sap_data, get_gst_code
from .channel_config import get_warehouse_code, get_supported_channels

logger = logging.getLogger(__name__)

def create_base_line_item(item, order_doc, account_code, warehouse_code, origin_state, channel_name, bill_to_code=None):
    """Create base line item dictionary for SAP payload"""
    try:
        return {
            "ItemCode": item.itemsku,
            "Quantity": item.quantity,
            "AccountCode": account_code,
            "WarehouseCode": warehouse_code,
            "TaxCode": get_gst_code(origin_state, order_doc.state, item.itemsku, item, channel_name, bill_to_code),
            "TaxType": "tt_Yes",
            "TaxLiable": "tYES",
            "TaxTotal": 0.0,
            "U_BuyerName": order_doc.customer_name,
            "U_Order": order_doc.uniware_id,
            "U_Sale_order_itemcode": item.code,
            "U_City": order_doc.city,
            "U_State": order_doc.state,
            "U_OrderedOn": str(order_doc.created)[:10],
            "U_PINCode": order_doc.pin_code,
            "U_Country": "India"
        }
    except Exception as e:
        logger.error(f"Failed to create base line item for {item.itemsku}: {str(e)}")
        raise

def build_regular_item_line(item, order_doc, account_code, warehouse_code, origin_state, channel_name, line_num, bill_to_code=None):
    """Build line item for regular (non-bundle) items"""
    try:
        item_line = create_base_line_item(item, order_doc, account_code, warehouse_code, origin_state, channel_name, bill_to_code)
        item_line.update({
            "LineNum": line_num,
            "ItemCode": item.itemsku,
            "U_Sale_order_itemcode": item.code,
            "U_Order_JSON": getattr(order_doc, 'order_json', ''),
            "UnitPrice": round(float(item.sellingpricewithouttaxesanddiscount) - float(item.discount), 3)
        })
        
        if hasattr(item, 'vendorbatchnumber') and item.vendorbatchnumber:
            item_line["BatchNumbers"] = [{
                "BatchNumber": item.vendorbatchnumber,
                "Quantity": item.quantity
            }]
        
        return item_line
        
    except Exception as e:
        logger.error(f"Failed to build regular item line for {item.itemsku}: {str(e)}")
        raise

def build_freight_line_item(item, order_doc, channel_warehouse_id, bill_to_code, line_num):
    """
    Build freight/shipping charge line item
    
    Args:
        item: Line item with shipping charges
        order_doc: Order document
        channel_warehouse_id: Channel warehouse identifier
        bill_to_code: Bill to code (SGST/IGST)
        line_num: Line number for SAP
        
    Returns:
        dict: Freight line item for SAP payload
    """
    try:
        # Calculate shipping charge tax
        shipping_charge = float(item.shippingcharges)
        tax_percentage = float(item.shippingchargetaxpercentage)
        
        # Validate tax percentage
        allowed_tax_codes = {0, 5, 12, 18, 24}
        tax_percentage = int(tax_percentage) if tax_percentage in allowed_tax_codes else 0
        
        # Determine tax code using consistent KACS/KAIG format for all channels
        if bill_to_code == "B2C SGST ADD":
            freight_tax_code = f"KACS{tax_percentage}"
        else:
            freight_tax_code = f"KAIG{tax_percentage}"
        
        # Calculate unit price (excluding tax)
        unit_price = shipping_charge * (100 / (100 + tax_percentage)) if tax_percentage > 0 else shipping_charge
        
        # Get warehouse code for freight
        freight_warehouse = get_warehouse_code(channel_warehouse_id)
        
        freight_line_item = {
            'LineNum': line_num,
            'ItemCode': 'EXCM0027',  # Standard freight item code
            'AccountCode': '41103000',  # Freight account code
            'WarehouseCode': freight_warehouse,
            'Quantity': 1,
            'TaxCode': freight_tax_code,
            'UnitPrice': round(unit_price, 3),
            'U_BuyerName': order_doc.customer_name,
            'U_Order': order_doc.uniware_id,
            'U_City': order_doc.city,
            'U_State': order_doc.state,
            'U_OrderedOn': str(order_doc.created)[:10],
            'U_PINCode': order_doc.pin_code,
            'U_Country': 'India',
            'U_Order_JSON': getattr(order_doc, 'order_json', '')
        }
        
        logger.info(f"Created freight line item: {freight_line_item}")
        return freight_line_item
        
    except Exception as e:
        logger.error(f"Failed to build freight line item: {str(e)}")
        raise

def build_bundle_lines(item, line_items, order_doc, account_code, warehouse_code, origin_state, channel_name, line_num_count, processed_codes, bill_to_code=None):
    """Build lines for bundle items (parent + children) with enhanced error handling"""
    bundle_lines = []
    
    try:
        # Create parent line for bundle
        parent_line = create_base_line_item(item, order_doc, account_code, warehouse_code, origin_state, channel_name, bill_to_code)
        parent_line.update({
            "LineNum": line_num_count,
            "ItemCode": item.bundleskucode,
            "UnitPrice": 0.0,
            "TreeType": "iSalesTree",
            "U_Order_JSON": getattr(order_doc, 'order_json', '')
        })
        bundle_lines.append(parent_line)
        line_num_count += 1
        
        # Process child items
        child_count = 0
        for child_item in line_items:
            if (child_item.get("cancellationreason") or 
                child_item.code in processed_codes or
                child_item.bundleskucode != item.bundleskucode):
                continue
                
            try:
                child_line = create_base_line_item(child_item, order_doc, account_code, warehouse_code, origin_state, channel_name, bill_to_code)
                child_line.update({
                    "LineNum": line_num_count,
                    "ItemCode": child_item.itemsku,
                    "U_Sale_order_itemcod": child_item.code,
                    "U_Order_JSON": getattr(order_doc, 'order_json', ''),
                    "TreeType": "iIngredient",
                    "UnitPrice": round(float(child_item.sellingpricewithouttaxesanddiscount) - float(child_item.discount), 3)
                })
                
                # Add batch numbers if available
                if hasattr(child_item, 'vendorbatchnumber') and child_item.vendorbatchnumber:
                    child_line["BatchNumbers"] = [{
                        "BatchNumber": child_item.vendorbatchnumber,
                        "Quantity": child_item.quantity
                    }]
                else:
                    # Log missing batch number for child items
                    logger.warning(f"Child item {child_item.itemsku} missing batch number in bundle {item.bundleskucode}")
                
                bundle_lines.append(child_line)
                processed_codes.add(child_item.code)
                line_num_count += 1
                child_count += 1
                
            except Exception as child_error:
                logger.error(f"Failed to process child item {child_item.itemsku} in bundle {item.bundleskucode}: {str(child_error)}")
                # Continue processing other child items
                continue
        
        if child_count == 0:
            logger.warning(f"No valid child items found for bundle {item.bundleskucode}")
        
        logger.info(f"Processed bundle {item.bundleskucode} with {child_count} child items")
        return bundle_lines, line_num_count
        
    except Exception as e:
        logger.error(f"Failed to build bundle lines for {item.itemsku}: {str(e)}")
        raise

def collect_sap_data_requirements(completed_orderlist):
    """
    Collect all required SAP data before processing to enable batch loading
    
    Args:
        completed_orderlist (list): List of order IDs
        
    Returns:
        tuple: (item_codes, origin_states) for batch preloading
    """
    item_codes = set()
    origin_states = set()
    
    for order_id in completed_orderlist:
        try:
            order_doc = frappe.get_doc('Unicommerce Orders', order_id)
            line_items = order_doc.line_items
            
            for item in line_items:
                if not item.get("cancellationreason"):
                    item_codes.add(item.itemsku)
                    if getattr(item, 'bundleskucode', None):
                        item_codes.add(item.bundleskucode)
            
            
        except Exception as e:
            logger.error(f"Failed to collect SAP requirements for order {order_id}: {str(e)}")
            continue
    
    logger.info(f"Collected SAP requirements: {len(item_codes)} items, {len(origin_states)} states")
    return list(item_codes), list(origin_states)

def build_document_lines(completed_orderlist, channel_config, account_code, bill_to_code):
    """Build all document lines for the SAP payload with optimized SAP calls and freight handling"""
    document_lines = []
    line_num_count = 0
    
    item_codes, origin_states = collect_sap_data_requirements(completed_orderlist)
    origin_states.append(channel_config.get("origin_state", "Karnataka"))  # Add channel origin state
    
    batch_preload_sap_data(item_codes, origin_states)
    
    for order_id in completed_orderlist:
        try:
            processed_codes = set()
            order_doc = frappe.get_doc('Unicommerce Orders', order_id)
            line_items = order_doc.line_items
            warehouse_code = channel_config.get("warehouse_code", "EC-FG")
            origin_state = channel_config.get("origin_state", "Karnataka")
            channel_name = channel_config.get("customer_code", "")
            channel_warehouse_id = channel_config.get("channel_name", "")
            
            # Process regular line items
            for item in line_items:
                # Skip cancelled items
                if item.get("cancellationreason"):
                    continue
                    
                # Skip already processed items
                if item.code in processed_codes:
                    continue
                
                # Handle bundle items
                if getattr(item, 'bundleskucode', None):
                    bundle_lines, line_num_count = build_bundle_lines(
                        item, line_items, order_doc, account_code, warehouse_code,
                        origin_state, channel_name, line_num_count, processed_codes, bill_to_code
                    )
                    document_lines.extend(bundle_lines)
                else:
                    # Regular item
                    item_line = build_regular_item_line(
                        item, order_doc, account_code, warehouse_code,
                        origin_state, channel_name, line_num_count, bill_to_code
                    )
                    document_lines.append(item_line)
                    processed_codes.add(item.code)
                    line_num_count += 1
            
            # Process freight/shipping charges for supported channels
            if channel_warehouse_id in get_supported_channels():
                for item in line_items:
                    if (not item.get("cancellationreason") and 
                        hasattr(item, 'shippingcharges') and 
                        float(item.shippingcharges) > 0):
                        
                        try:
                            freight_line = build_freight_line_item(
                                item, order_doc, channel_warehouse_id, bill_to_code, line_num_count
                            )
                            document_lines.append(freight_line)
                            line_num_count += 1
                            logger.info(f"Added freight line for order {order_id}: {item.shippingcharges}")
                        except Exception as freight_error:
                            logger.error(f"Failed to add freight line for order {order_id}: {str(freight_error)}")
                            continue
            
        except Exception as e:
            logger.error(f"Failed to build lines for order {order_id}: {str(e)}")
            continue
    
    logger.info(f"Built {len(document_lines)} document lines for {len(completed_orderlist)} orders")
    return document_lines
