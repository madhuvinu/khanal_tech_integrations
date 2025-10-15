import frappe
import logging
from .sap_integration import create_database_connection, close_database_connection

logger = logging.getLogger(__name__)

@frappe.whitelist()
def validate_batch_availability(payload, channel_name=None, order_list=None):
    """
    Validate batch availability in SAP B1 HANA DB

    Args:
        payload (dict): SAP payload with line items
        channel_name (str, optional): Channel name for context
        order_list (list, optional): List of orders being processed

    Returns:
        tuple: (failed_items, available_items) lists
    """
    logger.info("Starting batch availability validation")

    failed_items = []
    available_items = []

    try:
        connection, cursor = create_database_connection()

        for line_item in payload.get('DocumentLines', []):
            item_code = line_item.get('ItemCode')
            warehouse_code = line_item.get('WarehouseCode')
            batch_numbers = line_item.get('BatchNumbers', [])
            
            for batch_info in batch_numbers:
                batch_number = batch_info.get('BatchNumber')
                required_qty = float(batch_info.get('Quantity', 0))

                # Check batch-specific inventory using OIBT (Item Batch Transaction) table
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM("Quantity"), 0) AS "BatchQty"
                    FROM OIBT 
                    WHERE "ItemCode" = ? AND "WhsCode" = ? AND "BatchNum" = ?
                """, (item_code, warehouse_code, batch_number))

                result = cursor.fetchone()

                if result and result[0] is not None:
                    batch_qty = float(result[0])

                    if batch_qty >= required_qty:
                        available_items.append({
                            'ItemCode': item_code,
                            'BatchNumber': batch_number,
                            'Warehouse': warehouse_code,
                            'RequiredQty': required_qty,
                            'AvailableQty': batch_qty,
                            'Status': 'AVAILABLE'
                        })
                    else:
                        failed_items.append({
                            'ItemCode': item_code,
                            'BatchNumber': batch_number,
                            'Warehouse': warehouse_code,
                            'RequiredQty': required_qty,
                            'AvailableQty': batch_qty,
                            'Status': 'INSUFFICIENT_STOCK'
                        })
                else:
                    cursor.execute("""
                        SELECT "WhsCode", SUM("Quantity") AS "TotalQty"
                        FROM OIBT
                        WHERE "ItemCode" = ? AND "BatchNum" = ?
                        GROUP BY "WhsCode"
                    """, (item_code, batch_number))
                    
                    other_locations = cursor.fetchall()
                    
                    if other_locations:
                        available_locations = [{"WhsCode": row[0], "Quantity": row[1]} for row in other_locations]
                        failed_items.append({
                            'ItemCode': item_code,
                            'BatchNumber': batch_number,
                            'Warehouse': warehouse_code,
                            'RequiredQty': required_qty,
                            'AvailableQty': 0,
                            'Status': 'BATCH_IN_WRONG_WAREHOUSE',
                            'AvailableLocations': available_locations
                        })
                    else:
                        failed_items.append({
                            'ItemCode': item_code,
                            'BatchNumber': batch_number,
                            'Warehouse': warehouse_code,
                            'RequiredQty': required_qty,
                            'AvailableQty': 0,
                            'Status': 'BATCH_NOT_FOUND'
                        })

        close_database_connection(connection, cursor)

    except Exception as e:
        logger.error(f"Batch validation failed: {str(e)}")
        return [], []
    
    consolidated_failed_items = consolidate_failed_items(failed_items)
    
    logger.info(f"Batch validation complete: {len(available_items)} available, {len(consolidated_failed_items)} failed (consolidated from {len(failed_items)})")
    return consolidated_failed_items, available_items

def consolidate_failed_items(failed_items):
    """
    Consolidate failed items by ItemCode + BatchNumber + Warehouse
    Sum up the required quantities for duplicate items
    """
    consolidated = {}
    
    for item in failed_items:
        key = f"{item['ItemCode']}_{item['BatchNumber']}_{item['Warehouse']}"
        
        if key in consolidated:
            consolidated[key]['RequiredQty'] += item['RequiredQty']
        else:
            consolidated[key] = item.copy()
    
    return list(consolidated.values())

def create_batch_hold_record(failed_items, channel_name, order_list, payload):
    """Create a hold record for batch quantity issues"""
    try:
        total_orders = len(order_list)
        total_failed_items = len(failed_items)
        
        failure_ratio = total_failed_items / total_orders if total_orders > 0 else 0
        if failure_ratio > 0.8:
            priority = "Critical"
        elif failure_ratio > 0.5:
            priority = "High"
        elif failure_ratio > 0.2:
            priority = "Medium"
        else:
            priority = "Low"
        
        order_summary = generate_order_summary(order_list, failed_items)
        
        failed_items_table = []
        for item in failed_items:
            failed_items_table.append({
                'item_code': item.get('ItemCode', ''),
                'batch_number': item.get('BatchNumber', ''),
                'warehouse': item.get('Warehouse', ''),
                'required_qty': float(item.get('RequiredQty', 0)),
                'available_qty': float(item.get('AvailableQty', 0)),
                'status': item.get('Status', ''),
                'available_locations': frappe.as_json(item.get('AvailableLocations', []))
            })
        
        minimal_payload = {
            'CardCode': payload.get('CardCode'),
            'DocDate': payload.get('DocDate'),
            'DocDueDate': payload.get('DocDueDate'),
            'PayToCode': payload.get('PayToCode'),
            'U_BillingFrom': payload.get('U_BillingFrom'),
            'DocumentLines': payload.get('DocumentLines', [])[:10]  # Only first 10 lines for reference
        }
        
        hold_doc = frappe.get_doc({
            'doctype': 'SAP Batch Hold',
            'channel_name': channel_name,
            'order_list': frappe.as_json(order_list),  # Essential for resume
            'payload': frappe.as_json(minimal_payload), # Minimal payload to prevent packet size issues
            'status': 'Hold - Batch Quantity Issues',
            'created_by': frappe.session.user,
            'hold_reason': f'Batch quantity insufficient for {len(failed_items)} items',
            'total_orders': total_orders,
            'total_failed_items': total_failed_items,
            'full_payload_size': len(payload.get('DocumentLines', [])),  # Store original size for reference
            'payload_truncated': True  # Flag to indicate payload was truncated
        })
        hold_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        logger.info(f"Batch hold record created: {hold_doc.name}")
        return hold_doc.name
        
    except Exception as e:
        logger.error(f"Failed to create batch hold record: {str(e)}")
        return None

def format_failed_items_summary(failed_items):
    """Create a readable summary of failed items"""
    if not failed_items:
        return "No failed items"
    
    summary_lines = ["=" * 80, "FAILED ITEMS SUMMARY", "=" * 80, ""]
    
    for i, item in enumerate(failed_items, 1):
        summary_lines.extend([
            f"{i}. Item Code: {item.get('ItemCode', 'N/A')}",
            f"   Batch Number: {item.get('BatchNumber', 'N/A')}",
            f"   Warehouse: {item.get('Warehouse', 'N/A')}",
            f"   Required Quantity: {item.get('RequiredQty', 'N/A')}",
            f"   Available Quantity: {item.get('AvailableQty', 'N/A')}",
            f"   Status: {item.get('Status', 'N/A')}",
            ""
        ])
    
    summary_lines.extend(["=" * 80, f"Total Failed Items: {len(failed_items)}", "=" * 80])
    return "\n".join(summary_lines)

def generate_order_summary(order_list, failed_items):
    """Generate a concise summary of orders and failed items"""
    if not order_list:
        return "No orders available"
    
    failed_item_codes = list(set([item.get('ItemCode', 'N/A') for item in failed_items if isinstance(item, dict)]))
    
    order_ids = []
    for order in order_list[:5]:
        if isinstance(order, dict):
            order_id = order.get('name', order.get('order_id', order.get('id', 'N/A')))
        else:
            order_id = str(order)
        order_ids.append(order_id)
    
    summary_lines = [
        f"📊 Total Orders: {len(order_list)}",
        f"❌ Failed Items: {len(failed_items)}",
        f"🔧 Affected Item Codes: {', '.join(failed_item_codes[:5])}",
        f"📋 Sample Order IDs: {', '.join(order_ids)}"
    ]
    
    if len(order_list) > 5:
        summary_lines.append(f"... and {len(order_list) - 5} more orders")
    
    if len(failed_item_codes) > 5:
        summary_lines.append(f"... and {len(failed_item_codes) - 5} more items")
    
    return "\n".join(summary_lines)
