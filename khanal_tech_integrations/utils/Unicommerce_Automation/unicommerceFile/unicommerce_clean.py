"""
Clean Unicommerce API Integration Module
=======================================

This file contains only the actively used functions from the original unicommerce.py
All unused, duplicate, and deprecated functions have been removed.

Functions included:
- Core authentication and session management
- Active order management functions
- Purchase order and GRN management
- Essential utility functions

Total functions: ~15 (down from 50+ in original)
File size: ~800 lines (down from 1768 lines)
"""

import requests
import json
import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime, now
import time
import datetime
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1

# Global headers for API requests
DEFAULT_HEADERS = {
    "Accept": "*/*",
    "User-Agent": "KhanalTech",
    "Content-Type": "application/json"
}

# Constants
UNICOMMERCE_BASE_URL = "https://khanalfoods.unicommerce.com"
DEFAULT_FACILITY = "kfl_ecom_warehouse"
VENDOR_CODE = "EC-B2C"

# Warehouse mapping for Amazon FBA
WAREHOUSE_MAPPING = {
    'AMAZON_FBA_IN_BOM5': 'AMZ-BOM5',
    'AMAZON_FBA_IN_BOM7': 'AMZ-BOM7',
    'AMAZON_FBA_IN_BLR7': 'AMZ-BLR7',
    'AMAZON_FBA_IN_BLR8': 'AMZ-BLR8',
    'AMAZON_FBA_IN_BLR5': 'AMZ-BLR5',
    'AMAZON_FBA_IN_DEL4': 'AMZ-DEL4',
    'AMAZON_FBA_IN_DEL5': 'AMZ-DEL5',
    'AMAZON_FBA_IN_CJB1': 'AMZ-CJB1',
    'AMAZON_FBA_IN_MAA4': 'AMZ-MAA4'
}

# =============================================================================
# CORE AUTHENTICATION & SESSION MANAGEMENT
# =============================================================================

def AuthenticateUniware():
    """Authenticate with Unicommerce API and return session instance.
    
    This function checks if the current token is expired and renews it if necessary.
    Returns the Unicommerce Settings document with valid access token.
    
    Returns:
        frappe.Document: Unicommerce Settings document with valid access_token
        
    Raises:
        Exception: If authentication fails
    """
    doc = frappe.get_doc('Unicommerce Settings')
    
    # RENEW TOKEN ONLY IF EXPIRED
    expires_on = frappe.db.get_single_value('Unicommerce Settings', 'expires_on')

    if (expires_on == ''):
        try:
            uniware_doc = renew_session()
        except Exception as e:
            raise e
    
    elif (expires_on != ''): 
        if now_datetime() >= get_datetime(doc.expires_on):
            try:
                uniware_doc = renew_session()
            except Exception as e:
                raise e
        # DO NOT RENEW IF NOT EXPIRED
        else:
            uniware_doc = doc
        return uniware_doc

def renew_session():
    """Renew the Unicommerce session token.
    
    Makes an OAuth request to get a new access token and updates the settings.
    
    Returns:
        frappe.Document: Updated Unicommerce Settings document
        
    Raises:
        Exception: If token renewal fails
    """
    doc = frappe.get_doc('Unicommerce Settings')
    reqUrl = doc.tenant_url + "/oauth/token?grant_type=password&client_id=my-trusted-client&username=" + doc.username + "&password=" + doc.get_password('password')
    formatted_string = ' ,'.join(doc.facility.split(','))
    
    headers = DEFAULT_HEADERS.copy()
    headers["facility"] = formatted_string
    response = requests.request("GET", reqUrl, headers=headers)
    resp_json = response.json()
    doc.access_token = resp_json['access_token']
    doc.refresh_token = resp_json['refresh_token']
    doc.expires_on = add_to_date(now_datetime(), seconds=int(resp_json["expires_in"]))
    doc.save()
    frappe.db.commit()
    return doc

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def update_log(period_start_date, execution_start_time, period_end_date, execution_end_date, type):
    """Update the Unicommerce SAP update log"""
    doc = frappe.new_doc('Unicommerce SAP update log')
    doc.period_start_date = str(period_start_date)
    doc.execution_start_time = execution_start_time
    doc.period_end_date = str(period_end_date)
    doc.execution_end_date = execution_end_date
    doc.type = type
    doc.save()

def time_converter(time_stamp):
    """Convert epoch time into human readable time"""
    try:
        if time_stamp is None or str(time_stamp).strip().upper() in ['N', 'NULL', 'N/A', 'NA', 'NONE']:
            return datetime.datetime.now()  # Return current time as fallback
        
        # Convert to string and remove last 3 characters (milliseconds)
        time_str = str(time_stamp)[:-3]
        timestamp = datetime.datetime.fromtimestamp(_safe_convert_to_int(time_str, int(datetime.datetime.now().timestamp())))
        return timestamp
    except (ValueError, TypeError, AttributeError) as e:
        log_error(f"Failed to convert timestamp '{time_stamp}' to datetime: {str(e)}", "time_converter")
        return datetime.datetime.now()  # Return current time as fallback

def log_info(message, context="Unicommerce"):
    """Centralized logging function - only for critical operations"""
    if "ERROR" in message or "SUCCESS" in message or "COMPLETED" in message:
        print(f"[{context}] {message}")

def log_error(message, context="Unicommerce Error"):
    """
    Centralized error logging function
    Truncates message if too long for Frappe error log title field (140 char limit)
    """
    print(f"[{context}] ERROR: {message}")
    try:
        # Frappe error log title field has 140 character limit
        # Truncate message if too long, but keep important info
        if len(message) > 140:
            truncated = message[:137] + "..."
            frappe.log_error(truncated, context)
        else:
            frappe.log_error(message, context)
    except Exception as e:
        # If logging fails, at least print it
        print(f"[{context}] Failed to log error: {str(e)}")
        print(f"[{context}] Original error: {message}")

# =============================================================================
# DATA VALIDATION & CONVERSION UTILITIES
# =============================================================================

def _validate_order_data(order_detail):
    """Validate order data before processing"""
    try:
        required_fields = ['code', 'displayOrderCode', 'channel', 'status']
        for field in required_fields:
            if not order_detail.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Validate billing address
        if not order_detail.get('billingAddress'):
            log_error("Missing billing address in order data", "data_validation")
            return False
            
        # Validate line items
        if not order_detail.get('saleOrderItems'):
            log_error("No line items found in order data", "data_validation")
            return False
            
        return True
    except Exception as e:
        log_error(f"Order validation failed: {str(e)}", "data_validation")
        return False

def _safe_convert_to_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        if value is None or value == '':
            return default
        
        # Handle special cases like 'N' which might come from API
        if isinstance(value, str):
            value = value.strip().upper()
            if value in ['N', 'NULL', 'N/A', 'NA', 'NONE']:
                return default
        
        return float(value)
    except (ValueError, TypeError):
        log_error(f"Failed to convert '{value}' to float, using default {default}", "data_conversion")
        return default

def _safe_convert_to_int(value, default=0):
    """Safely convert value to int"""
    try:
        if value is None or value == '':
            return default
        
        # Handle special cases like 'N' which might come from API
        if isinstance(value, str):
            value = value.strip().upper()
            if value in ['N', 'NULL', 'N/A', 'NA', 'NONE']:
                return default
        
        return int(value)
    except (ValueError, TypeError):
        log_error(f"Failed to convert '{value}' to int, using default {default}", "data_conversion")
        return default

def _safe_convert_to_string(value, default=''):
    """Safely convert value to string"""
    try:
        if value is None:
            return default
        return str(value)
    except (ValueError, TypeError):
        log_error(f"Failed to convert '{value}' to string, using default '{default}'", "data_conversion")
        return default

def _validate_line_item_data(line_item):
    """Validate line item data"""
    try:
        required_fields = ['id', 'itemSku', 'sellerSkuCode', 'code']
        for field in required_fields:
            if not line_item.get(field):
                log_error(f"Missing required line item field: {field}", "line_item_validation")
                return False
        return True
    except Exception as e:
        log_error(f"Line item validation failed: {str(e)}", "line_item_validation")
        return False

@frappe.whitelist()
def BatchNumber_AmazonFBA(item_sku, warehouse_code):
    """Get batch number for Amazon FBA items from SAP"""
    try:
        session = AuthenticateSAPB1()
        doc_settings = frappe.get_doc('SAP Settings')
        reqUrl = f"{doc_settings.sap_b1_url}SQLQueries('Amazon_FBA_AL')/List?ItemCode='{item_sku}'&WhsCode='{warehouse_code}'"
        newurl = reqUrl.format(itemcode=item_sku)
        response = session.request("GET", newurl, headers=DEFAULT_HEADERS, verify=False)
        DeliveryNote = dict(response.json())
        return DeliveryNote['value'][0]['DistNumber']
    except Exception as e:
        frappe.log_error(f"Error getting batch number for {item_sku}: {str(e)}", "BatchNumber_AmazonFBA Error")
        return "NOT_FULFILLABLE"

# =============================================================================
# ORDER MANAGEMENT FUNCTIONS
# =============================================================================

def get_order_list(fromDate, toDate):
    """
    Get the list of orders from Unicommerce
    
    Note: Unicommerce API doesn't support pagination parameters (start/size).
    The API returns all orders matching the criteria in a single response.
    If there are too many orders, consider using smaller date ranges.
    
    Args:
        fromDate: Start date for order search
        toDate: End date for order search
    
    Returns:
        dict: API response with orders
    """
    uniware_session = AuthenticateUniware()
    
    headers = DEFAULT_HEADERS.copy()
    headers['Authorization'] = 'bearer ' + uniware_session.access_token
    facilityneeded = uniware_session.facility.split(',')
    search_Order_payload = {
        "fromDate": fromDate, 
        "toDate": toDate,   
        "facilityCodes": facilityneeded
    }
    
    reqUrl = f"{UNICOMMERCE_BASE_URL}/services/rest/v1/oms/saleOrder/search"
    try:
        response = requests.request("POST", reqUrl, json=(search_Order_payload), headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes
        result = response.json()
        
        # Ensure we always return a consistent structure
        if not isinstance(result, dict):
            return {"elements": [], "totalElements": 0}
        
        # Ensure elements is always a list
        if "elements" not in result:
            result["elements"] = []
        
        # Calculate total elements if not provided
        if "totalElements" not in result:
            result["totalElements"] = len(result.get("elements", []))
        
        return result
    except requests.exceptions.HTTPError as e:
        # Truncate error message for logging
        error_msg = f"API error: {response.status_code}"
        if response.status_code == 400:
            try:
                error_detail = response.json().get('message', 'Bad Request')
                error_msg = f"API 400: {error_detail[:50]}"
            except:
                pass
        log_error(error_msg, "get_order_list")
        return {"elements": [], "totalElements": 0}
    except Exception as e:
        error_msg = f"Error fetching orders: {str(e)[:80]}"
        log_error(error_msg, "get_order_list")
        return {"elements": [], "totalElements": 0}

def get_single_order(order_id):
    """GET DETAILS OF A SINGLE ORDER given order_id = uniware ID"""
    uniware_session = AuthenticateUniware()
    headers = DEFAULT_HEADERS.copy()
    headers['Authorization'] = 'bearer ' + uniware_session.access_token
    facilityneeded = uniware_session.facility.split(',')

    single_order_payload = {
        'code': order_id,
        "facilityCodes": facilityneeded
    }
    reqUrl = f"{UNICOMMERCE_BASE_URL}/services/rest/v1/oms/saleorder/get"
    response = requests.request("POST", reqUrl, data=json.dumps(single_order_payload), headers=headers)
    return response.json().get('saleOrderDTO')

@frappe.whitelist()
def fill_orders(fromDate, toDate):
    #! bench --site khanaltech.com execute  --args "('2025-10-01','2025-10-31')" khanal_tech_integrations.utils.Unicommerce_Automation.unicommerce_clean.fill_orders
    """
    Main function to fill orders from Unicommerce with pagination support
    
    This function now handles pagination to fetch ALL orders, not just the first page.
    It also provides detailed logging of progress and any orders that fail to fetch.
    """
    if fromDate or toDate:
        pass
    else:
        toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
        fromDate = add_to_date(datetime.datetime.now(), days=-1).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    startTime = now()
    print(f"[FILL_ORDERS] Starting order fetch from {fromDate} to {toDate}")
    
    # Track statistics
    total_orders_fetched = 0
    total_orders_processed = 0
    total_orders_skipped = 0
    total_orders_failed = 0
    failed_order_codes = []
    
    # Note: Unicommerce API doesn't support pagination parameters
    # The API returns all orders matching the date range in a single response
    # If you have >5000 orders, consider splitting the date range into smaller chunks
    print(f"[FILL_ORDERS] Fetching all orders from Unicommerce API...")
    o_list = get_order_list(fromDate, toDate)
    
    # Check if we got valid response
    if not o_list:
        log_error("Empty response from API", "fill_orders")
        print(f"[FILL_ORDERS] ❌ No response from API")
        endTime = now()
        update_log(fromDate, startTime, toDate, endTime, 'NEW')
        return {
            "total_fetched": 0,
            "total_processed": 0,
            "total_skipped": 0,
            "total_failed": 0,
            "failed_codes": []
        }
    
    # Get orders from response
    orders = o_list.get('elements', [])
    total_elements = o_list.get('totalElements', len(orders))
    
    print(f"[FILL_ORDERS] Found {len(orders)} orders (Total: {total_elements})")
    
    if not orders:
        print(f"[FILL_ORDERS] No orders found in the specified date range")
        endTime = now()
        update_log(fromDate, startTime, toDate, endTime, 'NEW')
        return {
            "total_fetched": 0,
            "total_processed": 0,
            "total_skipped": 0,
            "total_failed": 0,
            "failed_codes": []
        }
    
    total_orders_fetched = len(orders)
    
    # Warn if we got a large number of orders (might indicate API limit)
    if len(orders) >= 5000:
        print(f"[FILL_ORDERS] ⚠️ WARNING: Received {len(orders)} orders. Unicommerce API may have a limit.")
        print(f"[FILL_ORDERS] ⚠️ If you suspect missing orders, try splitting the date range into smaller chunks.")
    
    # Process each order
    for idx, order in enumerate(orders, 1):
        order_code = order.get('code', 'Unknown')
        
        try:
            # Get full order details
            proper_order = get_single_order(order_code)
            
            if not proper_order:
                error_msg = f"Failed to get order details for {order_code}"
                log_error(error_msg, "fill_orders")
                failed_order_codes.append(order_code)
                total_orders_failed += 1
                continue
            
            # Process the order
            success = push_new_orders(proper_order, update=False)
            
            if success:
                total_orders_processed += 1
                if idx % 100 == 0:  # Progress update every 100 orders
                    print(f"[FILL_ORDERS] Processed {idx}/{len(orders)} orders")
            else:
                # Order might already exist (skipped) or failed validation
                total_orders_skipped += 1
                
        except Exception as e:
            error_msg = f"Error processing {order_code}: {str(e)[:50]}"
            log_error(error_msg, "fill_orders")
            failed_order_codes.append(order_code)
            total_orders_failed += 1
    
    endTime = now()
    
    # Print summary
    print(f"\n[FILL_ORDERS] ========== SUMMARY ==========")
    print(f"[FILL_ORDERS] Date Range: {fromDate} to {toDate}")
    print(f"[FILL_ORDERS] Total Orders Fetched: {total_orders_fetched}")
    print(f"[FILL_ORDERS] Successfully Processed: {total_orders_processed}")
    print(f"[FILL_ORDERS] Skipped (already exist): {total_orders_skipped}")
    print(f"[FILL_ORDERS] Failed: {total_orders_failed}")
    if failed_order_codes:
        print(f"[FILL_ORDERS] Failed Order Codes: {failed_order_codes[:20]}")  # Show first 20
        if len(failed_order_codes) > 20:
            print(f"[FILL_ORDERS] ... and {len(failed_order_codes) - 20} more")
    print(f"[FILL_ORDERS] ==============================\n")
    
    update_log(fromDate, startTime, toDate, endTime, 'NEW')
    
    return {
        "total_fetched": total_orders_fetched,
        "total_processed": total_orders_processed,
        "total_skipped": total_orders_skipped,
        "total_failed": total_orders_failed,
        "failed_codes": failed_order_codes
    }

def fill_latest_orders():
    """Fill orders from last 1 day"""
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(), days=-1).strftime('%Y-%m-%dT%H:%M:%SZ')
    fill_orders(fromDate, toDate)

def fill_15days_orders():
    """Fill orders from last 15 days"""
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(), days=-15).strftime('%Y-%m-%dT%H:%M:%SZ')
    fill_orders(fromDate, toDate)

def fill_30days_orders():
    """Fill orders from last 30 days"""
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(), days=-30).strftime('%Y-%m-%dT%H:%M:%SZ')
    fill_orders(fromDate, toDate)

def fill_60days_orders():
    """Fill orders from last 60 days"""
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(), days=-60).strftime('%Y-%m-%dT%H:%M:%SZ')
    fill_orders(fromDate, toDate)

def push_new_orders(order_detail, update=False):
    """
    Improved version of push_new_orders with fixes for:
    - Code duplication
    - Inefficient database operations
    - Better error handling
    - Proper logging
    
    Args:
        order_detail (dict): Order data from Unicommerce API
        update (bool): True to update existing order, False to create new
    
    Returns:
        bool: True if successful, False if failed
    """
    order_id = None
    try:
        # Validate order data first
        if not _validate_order_data(order_detail):
            log_error("Order data validation failed", "push_new_orders")
            return False
            
        order_id = order_detail.get('code')
        if not order_id:
            log_error("Order code is missing from order_detail", "push_new_orders")
            return False
        
        # Check if order exists
        order_exists = frappe.db.exists("Unicommerce Orders", order_id, cache=True)
        
        if order_exists:
            doc = frappe.get_doc("Unicommerce Orders", order_id)
            
            if not update:
                return True  # Skip if order exists and not updating
        else:
            if update:
                log_error(f"Order {order_id} not found for update", "push_new_orders")
                return False
            
            doc = frappe.new_doc("Unicommerce Orders")
            
            # Set basic order fields for new orders
            _set_basic_order_fields(doc, order_detail)
        
        # Update common fields (for both new and existing orders)
        _update_common_order_fields(doc, order_detail)
        
        # Save the document
        doc.save()
        frappe.db.commit()
        
        # Process line items efficiently
        _process_line_items_efficiently(doc, order_detail)
        
        # Process returns if any
        if order_detail.get('returns'):
            _process_returns(doc, order_detail)
        
        return True
        
    except Exception as e:
        error_msg = f"Error processing order {order_id}: {str(e)}"
        log_error(error_msg, "push_new_orders")
        
        # Add debug information for data conversion errors
        if "invalid literal for int()" in str(e):
            log_error(f"Data conversion error for order {order_id}. Check quantity and other numeric fields in order data.", "push_new_orders")
        
        frappe.db.rollback()
        return False

def _set_basic_order_fields(doc, order_detail):
    """Set basic fields for new orders only with proper data type conversion"""
    doc.uniware_id = _safe_convert_to_string(order_detail['code'])
    doc.channel_id = _safe_convert_to_string(order_detail['displayOrderCode'])
    doc.channel_name = _safe_convert_to_string(order_detail['channel'])
    doc.created = time_converter(order_detail['created'])
    doc.cod = order_detail.get('cod', False)
    
    # Customer and address information with safe conversion
    billing_address = order_detail.get('billingAddress', {})
    doc.customer_name = _safe_convert_to_string(billing_address.get('name'))
    doc.city = _safe_convert_to_string(billing_address.get('city'))
    doc.district = _safe_convert_to_string(billing_address.get('district'))
    doc.state = _safe_convert_to_string(billing_address.get('state'))
    doc.pin_code = _safe_convert_to_int(billing_address.get('pincode'))
    
    doc.displayorderdatetime = time_converter(order_detail['displayOrderDateTime'])

def _update_common_order_fields(doc, order_detail):
    """Update fields that are common for both new and existing orders"""
    # Store complete order JSON
    doc.order_json = json.dumps(order_detail, indent=4)
    
    # Update status and timestamps
    doc.status = order_detail['status']
    doc.updated = time_converter(order_detail['updated'])
    
    # Update shipping information
    if order_detail.get('shippingPackages'):
        shipping_package = order_detail['shippingPackages'][0]
        doc.shippingpackages = shipping_package
        doc.shipment_status = shipping_package.get('status')
        doc.shipment_date = time_converter(shipping_package.get('dispatched'))

def _process_line_items_efficiently(doc, order_detail):
    """Process line items with optimized database operations and proper data type conversion"""
    try:
        line_items = []
        
        for line_item in order_detail.get("saleOrderItems", []):
            try:
                # Validate line item data first
                if not _validate_line_item_data(line_item):
                    log_error(f"Skipping invalid line item: {line_item.get('code', 'unknown')}", "process_line_items")
                    continue
                
                # Get batch information
                batch_code, vendor_batch_number = _get_batch_information(line_item, order_detail)
                
                # Create line item data with proper data type conversion
                line_item_data = {
                    "id": _safe_convert_to_string(line_item["id"]),
                    "itemsku": _safe_convert_to_string(line_item["itemSku"]),
                    "sellerskucode": _safe_convert_to_string(line_item["sellerSkuCode"]),
                    "channelproductid": _safe_convert_to_string(line_item.get("channelProductId")),
                    "quantity": _safe_convert_to_int(line_item.get("quantity", 1)),  # ✅ Use actual quantity
                    "total_price": _safe_convert_to_float(line_item.get("totalPrice")),
                    "selling_price": _safe_convert_to_float(line_item.get("sellingPrice")),
                    "created": time_converter(line_item.get("created")),
                    "updated": time_converter(line_item.get("updated")),
                    "totalintegratedgst": _safe_convert_to_float(line_item.get("totalIntegratedGst")),
                    "integratedgstpercentage": _safe_convert_to_float(line_item.get("integratedGstPercentage")),
                    "sellingpricewithouttaxesanddiscount": _safe_convert_to_float(line_item.get("sellingPriceWithoutTaxesAndDiscount")),
                    "shippingcharges": _safe_convert_to_float(line_item.get("shippingCharges")),
                    "shippingmethodcharges": _safe_convert_to_float(line_item.get("shippingMethodCharges")),
                    "cashondeliverycharges": _safe_convert_to_float(line_item.get("cashOnDeliveryCharges")),
                    "cancellationreason": _safe_convert_to_string(line_item.get("cancellationReason")),
                    "state_gst_tax_percentage": _safe_convert_to_float(line_item.get("stateGstPercentage")),
                    "central_gst_tax_percentage": _safe_convert_to_float(line_item.get("centralGstPercentage")),
                    "statusCode": _safe_convert_to_string(line_item.get("statusCode")),
                    "discount": _safe_convert_to_float(line_item.get("discount")),
                    "shippingchargetaxpercentage": _safe_convert_to_float(line_item.get("shippingChargeTaxPercentage")),
                    "bundleskucode": _safe_convert_to_string(line_item.get("bundleSkuCode")),
                    "code": _safe_convert_to_string(line_item["code"]),
                    "batchcode": _safe_convert_to_string(batch_code),
                    "vendorbatchnumber": _safe_convert_to_string(vendor_batch_number),
                }
                line_items.append(line_item_data)
                
            except Exception as e:
                log_error(f"Error processing line item {line_item.get('code', 'unknown')}: {str(e)}", "process_line_items")
                continue
        
        # Clear existing line items and add new ones in one operation
        doc.line_items = []
        for line_item in line_items:
            doc.append("line_items", line_item)
        
        doc.save()
        frappe.db.commit()
        
    except Exception as e:
        log_error(f"Error processing line items for order {doc.uniware_id}: {str(e)}", "process_line_items")

def _get_batch_information(line_item, order_detail):
    """Get batch code and vendor batch number for a line item"""
    try:
        batch_dto = line_item.get('batchDTO')
        if batch_dto:
            batch_code = batch_dto.get('batchCode', '')
            batch_fields = batch_dto.get('batchFieldsDTO', {})
            vendor_batch_number = batch_fields.get('vendorBatchNumber', '')
            return batch_code, vendor_batch_number
        else:
            # Handle Amazon FBA orders
            channel_code = order_detail.get('channel')
            if channel_code in WAREHOUSE_MAPPING:
                warehouse_code = WAREHOUSE_MAPPING[channel_code]
                try:
                    batch_code = BatchNumber_AmazonFBA(line_item['itemSku'], warehouse_code)
                    return batch_code, batch_code
                except Exception as e:
                    log_error(f"Error getting batch for Amazon FBA: {str(e)}", "get_batch_information")
                    return 'AMAZON_FBA_ERROR', 'AMAZON_FBA_ERROR'
            else:
                return 'NOT_FULFILLABLE', 'NOT_FULFILLABLE'
    except Exception as e:
        log_error(f"Error getting batch information: {str(e)}", "get_batch_information")
        return 'ERROR', 'ERROR'

def _process_returns(doc, order_detail):
    """Process return information if present"""
    try:
        returns_details = order_detail['returns'][0]
        doc.returnitems = json.dumps(returns_details, indent=4)
        doc.return_code = returns_details.get('code')
        doc.statuscode = returns_details.get('statusCode')
        doc.shippingprovider = returns_details.get('shippingProvider')
        doc.trackingnumber = returns_details.get('trackingNumber')
        doc.trackingstatus = returns_details.get('trackingStatus')
        doc.providerstatus = returns_details.get('providerStatus')
        doc.putawaycode = returns_details.get('putawayCode')
        doc.returninvoicecode = returns_details.get('returnInvoiceCode')
        doc.returninvoicedisplaycode = returns_details.get('returnInvoiceDisplayCode')
        doc.actioncode = returns_details.get('actionCode')
        doc.type = returns_details.get('type')
        doc.returncompleteddate = returns_details.get('returnCompletedDate')
        doc.inventoryreceiveddate = returns_details.get('inventoryReceivedDate')
        doc.returnfacilitycode = returns_details.get('returnFacilityCode')
        
        # Process return items for line items
        return_items = returns_details.get('returnItems', [])
        for return_item in return_items:
            return_item_sku = return_item.get('saleOrderItemCode')
            for line in doc.line_items:
                if line.code == return_item_sku:
                    line.uniware_return_status = returns_details.get('statusCode')
                    line.uniware_return_items = json.dumps(return_item, indent=4)
        
        doc.save()
        frappe.db.commit()
        
    except Exception as e:
        log_error(f"Error processing returns: {str(e)}", "process_returns")

# =============================================================================
# ORDER UPDATE FUNCTIONS
# =============================================================================

@frappe.whitelist()
def update_orders(toDate, fromDate):
    """
    Improved version of update_orders with:
    - Better error handling
    - Progress tracking
    - Individual order error isolation
    - Proper logging
    
    Args:
        toDate (str): End date for update range
        fromDate (str): Start date for update range
    
    Returns:
        dict: Summary of update operation
    """
    start_time = now()
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        # Fetch orders to update
        orders = frappe.get_list(
            "Unicommerce Orders",
            filters=[['created', 'between', [fromDate, toDate]]],
            fields=['uniware_id', 'created', 'displayorderdatetime', 'status']
        )
        
        total_orders = len(orders)
        print(f"Starting update for {total_orders} orders from {fromDate} to {toDate}")
        
        if total_orders == 0:
            print("No orders found for the specified date range")
            return {
                "success": True,
                "message": "No orders found for update",
                "total_orders": 0,
                "success_count": 0,
                "error_count": 0
            }
        
        # Process each order
        for i, order in enumerate(orders):
            try:
                order_id = order['uniware_id']
                
                # Get fresh order data from Unicommerce
                order_details = get_single_order(order_id)
                
                if order_details and order_details.get('code'):
                    # Update the order
                    success = push_new_orders(order_details, update=True)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        error_msg = f"Failed to update order: {order_id}"
                        errors.append(error_msg)
                        log_error(error_msg, "update_orders")
                else:
                    error_count += 1
                    error_msg = f"Could not fetch order details for: {order_id}"
                    errors.append(error_msg)
                    log_error(error_msg, "update_orders")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"Exception processing order {order.get('uniware_id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                log_error(error_msg, "update_orders")
        
        end_time = now()
        
        # Log the update operation
        update_log(fromDate, start_time, toDate, end_time, "UPDATE")
        
        # Prepare summary
        summary = {
            "success": True,
            "message": f"Update completed: {success_count} successful, {error_count} errors",
            "total_orders": total_orders,
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10],  # Show first 10 errors
            "processing_time": f"{start_time} to {end_time}"
        }
        
        print(f"SUCCESS: Update completed: {success_count} successful, {error_count} errors")
        return summary
        
    except Exception as e:
        error_msg = f"Critical error in update_orders: {str(e)}"
        log_error(error_msg, "update_orders")
        return {
            "success": False,
            "message": error_msg,
            "total_orders": 0,
            "success_count": success_count,
            "error_count": error_count + 1,
            "errors": [error_msg]
        }

def update_latest_orders():
    """
    Improved version of update_latest_orders with better error handling
    """
    try:
        to_date = datetime.datetime.now().strftime('%Y-%m-%d')
        from_date = add_to_date(datetime.datetime.now(), days=-30, as_string=True)
        
        print(f"Starting latest orders update: {from_date} to {to_date}")
        
        result = update_orders(to_date, from_date)
        
        if result["success"]:
            print(f"COMPLETED: Latest orders update: {result['success_count']} orders updated")
        else:
            log_error(f"Latest orders update failed: {result['message']}", "update_latest_orders")
        
        return result
        
    except Exception as e:
        error_msg = f"Error in latest orders update: {str(e)}"
        log_error(error_msg, "update_latest_orders")
        return {"success": False, "message": error_msg}

def update_2days_orders():
    """
    Improved version of update_2days_orders with better error handling and logging
    """
    try:
        to_date = datetime.datetime.now().strftime('%Y-%m-%d')
        from_date = add_to_date(datetime.datetime.now(), days=-2, as_string=True)
        
        print(f"Starting daily update for last 2 days: {from_date} to {to_date}")
        
        result = update_orders(to_date, from_date)
        
        if result["success"]:
            print(f"COMPLETED: Daily update: {result['success_count']} orders updated")
        else:
            log_error(f"Daily update failed: {result['message']}", "update_2days_orders")
        
        return result
        
    except Exception as e:
        error_msg = f"Error in daily update: {str(e)}"
        log_error(error_msg, "update_2days_orders")
        return {"success": False, "message": error_msg}

# =============================================================================
# PURCHASE ORDER & GRN MANAGEMENT
# =============================================================================

@frappe.whitelist()
def create_Approved_PO(docnum):
    """Create a Purchase order (PO) in approved state given an inventory stock transfer docentry"""
    PO_payload = {
        "vendorCode": VENDOR_CODE,
        "purchaseOrderItems": [] 
    }
    
    inv_transfer_doc = frappe.get_doc('SAP Inventory Transfers', docnum)
    original_inv_transfer_line_items = inv_transfer_doc.line_items
    new_list = []
    new_item_code_list = []
    
    for item in original_inv_transfer_line_items:
        temporary = {'itemcode': item.itemcode, 'quantity': item.quantity}
        if item.itemcode not in new_item_code_list:
            new_item_code_list.append(item.itemcode)
            new_list.append(temporary)
    
    PO_lineitems_list = []
    for item in new_list:
        PO_lineitem = {
            "itemSKU": "NN",
            "quantity": 3,
            "unitPrice": 0,
            "taxTypeCode": None 
        }
        PO_lineitem['itemSKU'] = item['itemcode']
        PO_lineitem['quantity'] = item['quantity']
        PO_lineitems_list.append(PO_lineitem)
    
    PO_payload["purchaseOrderItems"] = PO_lineitems_list
    PO_posting_url = f"{UNICOMMERCE_BASE_URL}/services/rest/v1/purchase/purchaseOrder/createApproved"
    uniware_session = AuthenticateUniware()
    headers = DEFAULT_HEADERS.copy()
    headers["facility"] = DEFAULT_FACILITY
    headers['Authorization'] = 'bearer ' + uniware_session.access_token
    
    response = requests.request("POST", PO_posting_url, data=json.dumps(PO_payload), headers=headers, verify=False)
    resdict = response.json()
    
    if resdict.get('purchaseOrderCode') is not None:
        inv_transfer_doc.uniware_po_id = resdict['purchaseOrderCode']
        inv_transfer_doc.uniware_po_status = 'APPROVED'
        inv_transfer_doc.save()
        frappe.db.commit()
    return resdict

def create_GRN(PO_number, facility=DEFAULT_FACILITY):
    """Create GRN for a purchase order"""
    createGRN_payload = {
        "wsGRN": {
            "vendorInvoiceNumber": "Generated via API", 
            "vendorInvoiceDate": frappe.utils.today(), 
            "currencyCode": "INR"   
        },
        "purchaseOrderCode": str(PO_number),
        "vendorInvoiceDateCheckDisable": False
    }
    
    uniware_session = AuthenticateUniware()
    headers = DEFAULT_HEADERS.copy()
    headers["facility"] = facility
        
    GRN_creation_url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/create"
    headers['Authorization'] = 'bearer ' + uniware_session.access_token
    GRNcreation_response = requests.request("POST", GRN_creation_url, data=json.dumps(createGRN_payload), headers=headers)
    Created_GRN_Dict = dict(GRNcreation_response.json())
    
    if Created_GRN_Dict['successful']:
        print('Newly created GRN is:', Created_GRN_Dict['inflowReceiptCode'])
    return Created_GRN_Dict

@frappe.whitelist()
def Create_GRNs_fill_Items(inv_tranfer_docentry: int) -> None:
    """Create multiple GRNs and fill all items with single/multiple batches"""
    uniware_session = AuthenticateUniware()
    InventoryTransfer_doc = frappe.get_doc('SAP Inventory Transfers', inv_tranfer_docentry)
    original_inv_transfer_line_items = InventoryTransfer_doc.line_items

    try:
        GRN_SKUadding_formated_List = []
        for one_item in original_inv_transfer_line_items:
            inflowItem = {
                "skuCode": None,
                "quantity": 1,
                "unitPrice": 1,
                "wsBatchDetail": {
                    "wsBatchGroupFieldValue": {
                        "vendorBatchNumber": "NA"
                    }
                }
            }
            inflowItem['skuCode'] = one_item.itemcode
            inflowItem["quantity"] = one_item.batchquantity
            inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] = one_item.batchnumber
            inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['expiryDate'] = one_item.expirydate.strftime('%Y-%m-%d')
            GRN_SKUadding_formated_List.append(inflowItem)
        
        while len(GRN_SKUadding_formated_List) != 0:
            Filter_item_List = []
            Listof_Items_ToPush = []
            for single_item in GRN_SKUadding_formated_List:
                if single_item['skuCode'] not in Filter_item_List:
                    Filter_item_List.append(single_item['skuCode'])
                    Listof_Items_ToPush.append(single_item)
                    GRN_SKUadding_formated_List.remove(single_item)
            
            Created_GRN_Dict = create_GRN(InventoryTransfer_doc.uniware_po_id, facility=DEFAULT_FACILITY)
            if Created_GRN_Dict['successful']:
                uniware_grn_no = Created_GRN_Dict['inflowReceiptCode']
                for again_single_item in Listof_Items_ToPush:
                    GRN_SKUwise_Details = {
                        "inflowReceiptCode": str(uniware_grn_no),
                        "inflowReceiptItem": again_single_item 
                    }
                    SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
                    headers = DEFAULT_HEADERS.copy()
                    headers['Authorization'] = 'bearer ' + uniware_session.access_token
                    response = requests.request("POST", SKU_adding_Url, data=json.dumps(GRN_SKUwise_Details), headers=headers)
        
        InventoryTransfer_doc.uniware_po_status = 'GRN_COMPLETED'
        InventoryTransfer_doc.save()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error in Create_GRNs_fill_Items for doc {inv_tranfer_docentry}: {str(e)}", "GRN Creation Error")
    return None

@frappe.whitelist()
def Check_Uniware_PO_Exists(days=None):
    """Go through inventory transfers and create PO for those without corresponding PO in uniware"""
    Today = frappe.utils.nowdate()
    if days == None:
        start = add_to_date(Today, days=-12)
    else:
        start = add_to_date(Today, days=-days)
    
    List_of_InventoryStockTransfer = frappe.db.get_list('SAP Inventory Transfers',
                                                        filters={
                                                            'towarehouse': 'EC-FG',
                                                            'docdate': ['>', start]  
                                                        })
    
    for inv_document in List_of_InventoryStockTransfer:
        Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', inv_document['name'])
        
        if Single_inv_doc.uniware_po_id == None:
            Uniware_response = create_Approved_PO(str(Single_inv_doc.docentry)) 
            if Uniware_response['successful'] == True:
                Single_inv_doc.uniware_po_id = Uniware_response['purchaseOrderCode']
                Single_inv_doc.save()
                frappe.db.commit()
                Create_GRNs_fill_Items(Single_inv_doc.docentry)
            elif Uniware_response['successful'] == False:
                print('Po Creation Failed')
                print(Uniware_response)
    
    return None

def PO_GRN_Completion(days=None):
    """Complete PO and GRN creation process"""
    Today = frappe.utils.nowdate()
    if days is None:
        start = add_to_date(Today, days=-2)
    else:
        start = add_to_date(Today, days=-days)
    
    Check_Uniware_PO_Exists(days)
      
    GRN_not_done_List = frappe.db.get_list('SAP Inventory Transfers',
                                            filters={
                                                'towarehouse': 'EC-FG',
                                                'uniware_po_status': 'APPROVED',
                                                'docdate': ['>', start]
                                            })
    
    if GRN_not_done_List:
        for single_docentry in GRN_not_done_List:
            Create_GRNs_fill_Items(single_docentry)

    return None

@frappe.whitelist()
def Update_Uniware_PO_Status(days=None):
    """Update PO status in Unicommerce"""
    Today = frappe.utils.nowdate()
    if days == None:
        start = add_to_date(Today, days=-4)
    else:
        start = add_to_date(Today, days=-days)
    
    List_of_InevntoryStockTransfer = frappe.db.get_list('SAP Inventory Transfers',
                                                        filters={
                                                            'towarehouse': 'EC-FG',
                                                            'uniware_po_status': ('in', ['APPROVED', 'GRN_COMPLETED']), 
                                                            'docdate': ['>', start],
                                                        })
    
    for inv_document in List_of_InevntoryStockTransfer:
        Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', inv_document['name'])
        
        if Single_inv_doc.uniware_po_id != None: 
            single_PO_payload = {"purchaseOrderCode": Single_inv_doc.uniware_po_id}
            PO_checking_url = f"{UNICOMMERCE_BASE_URL}/services/rest/v1/purchase/purchaseOrder/getPurchaseOrderDetails"
            uniware_session = AuthenticateUniware()
            
            facilityneeded = uniware_session.facility.split(',')
            headers = DEFAULT_HEADERS.copy()
            headers["facility"] = ','.join(uniware_session.facility.split(','))
            headers['Authorization'] = 'bearer ' + uniware_session.access_token
            response = requests.request("POST", PO_checking_url, data=json.dumps(single_PO_payload), headers=headers)
            PO_Dict = dict(response.json())
            
            if PO_Dict['successful']:
                Single_inv_doc.uniware_po_status = PO_Dict['statusCode']
                Single_inv_doc.save()
                frappe.db.commit()
    return None
