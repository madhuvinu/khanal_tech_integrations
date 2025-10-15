import requests
import os
import pandas as pd
import json
import frappe
import logging
from frappe.utils import get_site_path, now_datetime, get_datetime
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1

# Configure logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global headers for API requests
HEADERS = {
    "Accept": "*/*",
    "User-Agent": "Khanal Tech",
    "Content-Type": "application/json"
}

# Global cache for SAP data to minimize API calls - cleared per channel
_sap_cache = {
    'states': {},           # Cache state codes
    'items': {},            # Cache item tax rates
    'session': None,        # Reuse SAP session
    'session_time': None,   # Track session creation time
    'current_channel': None # Track current processing channel
}

# Cache timeout in minutes
CACHE_TIMEOUT_MINUTES = 30


def clear_sap_cache(channel_name=None):
    """
    Clear SAP cache for a new channel or force refresh
    
    Args:
        channel_name (str, optional): Channel name being processed
    """
    global _sap_cache
    
    if channel_name and _sap_cache.get('current_channel') != channel_name:
        logger.info(f"Clearing SAP cache for new channel: {channel_name}")
        _sap_cache = {
            'states': {},
            'items': {},
            'session': _sap_cache.get('session'),  # Keep session if valid
            'session_time': _sap_cache.get('session_time'),
            'current_channel': channel_name
        }
    elif not channel_name:
        logger.info("Force clearing all SAP cache")
        _sap_cache = {
            'states': {},
            'items': {},
            'session': None,
            'session_time': None,
            'current_channel': None
        }

def is_cache_valid():
    """Check if cache is still valid based on timeout"""
    if not _sap_cache.get('session_time'):
        return False
    
    time_diff = datetime.now() - _sap_cache['session_time']
    return time_diff.total_seconds() < (CACHE_TIMEOUT_MINUTES * 60)

def get_cached_sap_session():
    """Get cached SAP session or create new one"""
    if _sap_cache.get('session') and is_cache_valid():
        return _sap_cache['session']
    
    logger.info("Creating new SAP session")
    session = AuthenticateSAPB1()
    _sap_cache['session'] = session
    _sap_cache['session_time'] = datetime.now()
    return session


def get_supported_channels():
    """Get list of all supported e-commerce channels"""
    return [
        "AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7", "AMAZON_FBA_IN_BLR5", 
        "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8", "AMAZON_FBA_IN_DEL4", 
        "AMAZON_FBA_IN_DEL5", "AMAZON_FBA_IN_CJB1", "AMAZON_FBA_IN_MAA4",
        "Amazon_IN_API", "CRED", "FLIPKART", "DOGSEE_SITE_IN", "HN_SITE_IN",
        "ONDC_NSTORE", "HALFCIRCLEFULL", "MEESHO", "Snapdeal"
    ]
#! bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.Ar_Invoice_Creation_Unicommerce_Optimized.Channel_delivery_Creation_Dispatched2 --args '("Channel_Name": "Amazon_IN_API", "startDate": "01-09-2025", "endDate": "30-09-2025")'

#! bench --site khanaltech.com execute khanal_tech_integrations.utils.Unicommerce_Automation.Ar_Invoice_Creation_Unicommerce_Optimized.Channel_delivery_Creation_Dispatched2 --args '("FLIPKART","01-09-2025","30-09-2025")'
def get_warehouse_code(channel_warehouse_id):
    """
    Get warehouse code mapping for channel warehouse ID
    
    Args:
        channel_warehouse_id (str): Channel warehouse identifier
        
    Returns:
        str: SAP warehouse code
    """
    mapping = {
        "AMAZON_FBA_IN_BOM5": "AMZ-BOM5",
        "AMAZON_FBA_IN_BOM7": "AMZ-BOM7",
        "AMAZON_FBA_IN_BLR5": "AMZ-BLR5",
        "AMAZON_FBA_IN_BLR7": "AMZ-BLR7",
        "AMAZON_FBA_IN_BLR8": "AMZ-BLR8",
        "AMAZON_FBA_IN_DEL4": "AMZ-DEL4",
        "AMAZON_FBA_IN_DEL5": "AMZ-DEL5",
        "AMAZON_FBA_IN_CJB1": "AMZ-CJB1",
        "AMAZON_FBA_IN_MAA4": "AMZ-MAA4",
    }
    return mapping.get(channel_warehouse_id, "EC-FG")

def get_channel_configuration(channel_name):
    """
    Get channel-specific configuration including customer codes, account codes, etc.
    
    Args:
        channel_name (str): Name of the e-commerce channel
        
    Returns:
        dict: Channel configuration dictionary
        
    Raises:
        ValueError: If channel is not supported
    """
    channel_configs = {
        "AMAZON_FBA_IN_BOM5": {
            "customer_code": "C03564",
            "account_code_sgst": "41160004",
            "account_code_igst": "41160005", 
            "series_number": "442",
            "origin_state": "Maharashtra",
            "origin_state_code": "MH",
            "warehouse_code": "AMZ-BOM5"
        },
        "AMAZON_FBA_IN_BOM7": {
            "customer_code": "C03564",
            "account_code_sgst": "41160004",
            "account_code_igst": "41160005",
            "series_number": "442", 
            "origin_state": "Maharashtra",
            "origin_state_code": "MH",
            "warehouse_code": "AMZ-BOM7"
        },
        "AMAZON_FBA_IN_BLR5": {
            "customer_code": "C03575",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka", 
            "origin_state_code": "KT",
            "warehouse_code": "AMZ-BLR5"
        },
        "AMAZON_FBA_IN_BLR7": {
            "customer_code": "C03575",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT", 
            "warehouse_code": "AMZ-BLR7"
        },
        "AMAZON_FBA_IN_BLR8": {
            "customer_code": "C03575",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "AMZ-BLR8"
        },
        "AMAZON_FBA_IN_DEL4": {
            "customer_code": "C03579",
            "account_code_sgst": "41160007",
            "account_code_igst": "41160008",
            "series_number": "441",
            "origin_state": "Haryana",
            "origin_state_code": "HR",
            "warehouse_code": "AMZ-DEL4"
        },
        "AMAZON_FBA_IN_DEL5": {
            "customer_code": "C03579", 
            "account_code_sgst": "41160007",
            "account_code_igst": "41160008",
            "series_number": "441",
            "origin_state": "Haryana",
            "origin_state_code": "HR",
            "warehouse_code": "AMZ-DEL5"
        },
        "AMAZON_FBA_IN_CJB1": {
            "customer_code": "C03596",
            "account_code_sgst": "41160012",
            "account_code_igst": "41160013", 
            "series_number": "461",
            "origin_state": "Tamil Nadu",
            "origin_state_code": "TN",
            "warehouse_code": "AMZ-CJB1"
        },
        "AMAZON_FBA_IN_MAA4": {
            "customer_code": "C03596",
            "account_code_sgst": "41160012",
            "account_code_igst": "41160013",
            "series_number": "461", 
            "origin_state": "Tamil Nadu",
            "origin_state_code": "TN",
            "warehouse_code": "AMZ-MAA4"
        },
        "Amazon_IN_API": {
            "customer_code": "C03575",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KA",
            "warehouse_code": "EC-FG"
        },
        "CRED": {
            "customer_code": "C03358",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002", 
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        },
        "FLIPKART": {
            "customer_code": "C03121",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT", 
            "warehouse_code": "EC-FG"
        },
        "DOGSEE_SITE_IN": {
            "customer_code": "C00623",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        },
        "HN_SITE_IN": {
            "customer_code": "C01026",
            "account_code_sgst": "41106001", 
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        },
        "ONDC_NSTORE": {
            "customer_code": "C03494",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        },
        "HALFCIRCLEFULL": {
            "customer_code": "C03412",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412", 
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        },
        "MEESHO": {
            "customer_code": "C03586",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002",
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        },
        "Snapdeal": {
            "customer_code": "C02574",
            "account_code_sgst": "41106001",
            "account_code_igst": "41106002", 
            "series_number": "412",
            "origin_state": "Karnataka",
            "origin_state_code": "KT",
            "warehouse_code": "EC-FG"
        }
    }
    
    if channel_name not in channel_configs:
        raise ValueError(f"Unsupported channel: {channel_name}. Supported channels: {list(channel_configs.keys())}")
    
    return channel_configs[channel_name]

def get_sap_state_code(database_state_code):
    """
    Map database state codes to SAP state codes
    
    Args:
        database_state_code (str): State code from database (e.g., 'KA')
        
    Returns:
        str: SAP state code (e.g., 'KT')
    """
    state_mapping = {
        'KA': 'KT',  # Karnataka: Database uses KA, SAP uses KT
        'MH': 'MH',  # Maharashtra: Same in both
        'HR': 'HR',  # Haryana: Same in both
        'TN': 'TN',  # Tamil Nadu: Same in both
        'DL': 'DL',  # Delhi: Same in both
        'GJ': 'GJ',  # Gujarat: Same in both
        'UP': 'UP',  # Uttar Pradesh: Same in both
        'WB': 'WB',  # West Bengal: Same in both
        'RJ': 'RJ',  # Rajasthan: Same in both
        'MP': 'MP',  # Madhya Pradesh: Same in both
        'AP': 'AP',  # Andhra Pradesh: Same in both
        'TL': 'TL',  # Telangana: Same in both
        'KL': 'KL',  # Kerala: Same in both
        'OR': 'OR',  # Odisha: Same in both
        'AS': 'AS',  # Assam: Same in both
        'BR': 'BR',  # Bihar: Same in both
        'JH': 'JH',  # Jharkhand: Same in both
        'CH': 'CH',  # Chandigarh: Same in both
        'HP': 'HP',  # Himachal Pradesh: Same in both
        'JK': 'JK',  # Jammu and Kashmir: Same in both
        'UT': 'UT',  # Uttarakhand: Same in both
        'PB': 'PB',  # Punjab: Same in both
        'CT': 'CT',  # Chhattisgarh: Same in both
        'GA': 'GA',  # Goa: Same in both
        'MN': 'MN',  # Manipur: Same in both
        'MZ': 'MZ',  # Mizoram: Same in both
        'NL': 'NL',  # Nagaland: Same in both
        'ML': 'ML',  # Meghalaya: Same in both
        'PY': 'PY',  # Puducherry: Same in both
    }
    
    return state_mapping.get(database_state_code, database_state_code)

def get_email_recipients():
    """Get default email recipients for notifications"""
    return [
        "yogesha@khanalfoods.com",
        "harsha@khanalfoods.com", 
        "sourav@khanalfoods.com"
    ]

def get_database_config():
    """
    Get database configuration from SAP Settings with validation
    
    Returns:
        dict: Database configuration
        
    Raises:
        ValueError: If required configuration is missing
    """
    try:
        doc_settings = frappe.get_doc('SAP Settings')
        
        required_fields = ['hana_host', 'hana_user', 'hana_password', 'hana_schema']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(doc_settings, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required SAP Settings fields: {missing_fields}")
        
        return {
        'host': doc_settings.hana_host.strip(),
        'port': int(getattr(doc_settings, 'hana_port', 30015)),
        'user': doc_settings.hana_user.strip(),
        'password': doc_settings.hana_password.strip(),
        'schema': getattr(doc_settings, 'hana_schema', '').strip(),
        'sap_url': getattr(doc_settings, 'sap_b1_url', '').strip()
    }
        
    except Exception as e:
        logger.error(f"Failed to get database configuration: {str(e)}")
        raise


def create_database_connection():
    """
    Create secure read-only database connection to SAP HANA
    
    Returns:
        tuple: (connection, cursor) objects
        
    Raises:
        Exception: If connection fails
    """
    try:
        config = get_database_config()
        
        import hdbcli.dbapi as hana_db
        connection = hana_db.connect(
            address=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        
        cursor = connection.cursor()
        
        cursor.execute(f"SET SCHEMA {config['schema']}")
        cursor.execute("SET TRANSACTION READ ONLY")
        
        logger.info(f"Read-only database connection established to schema: {config['schema']}")
        return connection, cursor
        
    except ImportError:
        logger.error("SAP HANA driver not found. Install with: pip install hdbcli")
        raise
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise


def close_database_connection(connection, cursor):
    """Safely close database connection"""
    try:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}")


def get_cached_state_code(origin_state):
    """
    Get state code from cache or SAP API
    
    Args:
        origin_state (str): Origin state name
        
    Returns:
        str: State code
    """
    if origin_state in _sap_cache['states']:
        return _sap_cache['states'][origin_state]
    
    try:
        session = get_cached_sap_session()
        config = get_database_config()
        
        state_url = (f"{config['sap_url']}States?$select=Code"
                    f"&$filter=startswith(Country,'IN') and startswith(Name,'{origin_state}')")
        response = session.request("GET", state_url, headers=HEADERS, verify=False)
        response.raise_for_status()
        
        state_data = response.json().get('value', [])
        if not state_data:
            raise ValueError(f"State not found in SAP: {origin_state}")
        
        state_code = state_data[0]['Code']
        
        _sap_cache['states'][origin_state] = state_code
        
        return state_code
        
    except Exception as e:
        logger.error(f"Failed to get state code for {origin_state}: {str(e)}")
        raise

def get_cached_item_tax_rate(item_code):
    """
    Get item tax rate from cache or SAP API
    
    Args:
        item_code (str): Item code
        
    Returns:
        float: Tax rate
    """
    # Check cache first
    if item_code in _sap_cache['items']:
        return _sap_cache['items'][item_code]
    
    try:
        session = get_cached_sap_session()
        config = get_database_config()
        
        item_url = (f"{config['sap_url']}Items?$select=ItemCode,ItemName,ForeignName,U_TaxRate"
                   f"&$filter=startswith(ItemCode, '{item_code}')&$orderby=ItemCode")
        response = session.request("GET", item_url, headers=HEADERS, verify=False)
        response.raise_for_status()
        
        item_data_sap = response.json().get('value', [])
        if not item_data_sap:
            raise ValueError(f"Item not found in SAP: {item_code}")
            
        tax_rate = item_data_sap[0]['U_TaxRate']
        
        _sap_cache['items'][item_code] = tax_rate
        
        return tax_rate
        
    except Exception as e:
        logger.error(f"Failed to get tax rate for {item_code}: {str(e)}")
        raise

def batch_preload_sap_data(item_codes, origin_states):
    """
    Preload SAP data in batches to minimize API calls
    
    Args:
        item_codes (list): List of item codes to preload
        origin_states (list): List of origin states to preload
    """
    try:
        session = get_cached_sap_session()
        config = get_database_config()
        
        unique_states = list(set(origin_states))
        uncached_states = [state for state in unique_states if state not in _sap_cache['states']]
        
        if uncached_states:
            logger.info(f"Batch loading {len(uncached_states)} states from SAP")
            
            for state in uncached_states:
                try:
                    state_url = (f"{config['sap_url']}States?$select=Code"
                                f"&$filter=startswith(Country,'IN') and startswith(Name,'{state}')")
                    response = session.request("GET", state_url, headers=HEADERS, verify=False)
                    response.raise_for_status()
                    
                    state_data = response.json().get('value', [])
                    if state_data:
                        _sap_cache['states'][state] = state_data[0]['Code']
                except Exception as e:
                    logger.warning(f"Failed to preload state {state}: {str(e)}")
        
        unique_items = list(set(item_codes))
        uncached_items = [item for item in unique_items if item not in _sap_cache['items']]
        
        if uncached_items:
            logger.info(f"Batch loading {len(uncached_items)} items from SAP")
            
            chunk_size = 50
            for i in range(0, len(uncached_items), chunk_size):
                chunk = uncached_items[i:i + chunk_size]
                
                try:
                    filter_conditions = " or ".join([f"startswith(ItemCode, '{item}')" for item in chunk])
                    item_url = (f"{config['sap_url']}Items?$select=ItemCode,ItemName,ForeignName,U_TaxRate"
                               f"&$filter={filter_conditions}&$orderby=ItemCode")
                    
                    response = session.request("GET", item_url, headers=HEADERS, verify=False)
                    response.raise_for_status()
                    
                    items_data = response.json().get('value', [])
                    for item_data in items_data:
                        item_code = item_data['ItemCode']
                        tax_rate = item_data['U_TaxRate']
                        _sap_cache['items'][item_code] = tax_rate
                        
                except Exception as e:
                    logger.warning(f"Failed to preload item chunk: {str(e)}")
                    for item in chunk:
                        try:
                            get_cached_item_tax_rate(item)
                        except Exception:
                            pass
        
        logger.info(f"SAP data preload complete: {len(_sap_cache['states'])} states, {len(_sap_cache['items'])} items cached")
        
    except Exception as e:
        logger.error(f"Batch preload failed: {str(e)}")


def get_gst_code(origin_state, dest_state, item_code, item_data, channel_name=None, bill_to_code=None):
    """
    Calculate GST code for an item based on origin and destination states
    Uses cached data to minimize SAP API calls
    
    Args:
        origin_state (str): Origin state name
        dest_state (str): Destination state code
        item_code (str): Item code in SAP
        item_data: Item data from Unicommerce
        channel_name (str, optional): Channel name for logging
        
    Returns:
        str: GST code string
        
    Raises:
        ValueError: If GST calculation fails
    """
    
    try:
        state_code = get_cached_state_code(origin_state)
        tax_rate = get_cached_item_tax_rate(item_code)
        
    except Exception as e:
        logger.error(f"SAP GST lookup failed for item {item_code}: {str(e)}")
        raise ValueError(f"Could not fetch GST data from SAP: {str(e)}")
    
    try:
        uni_igst = int(item_data.integratedgstpercentage)
        uni_cgst_sgst = float(item_data.state_gst_tax_percentage) + float(item_data.central_gst_tax_percentage)
        uni_tax = int(uni_cgst_sgst + uni_igst)
    except (AttributeError, ValueError) as e:
        logger.error(f"Invalid tax data for item {item_code}: {str(e)}")
        raise ValueError(f"Invalid tax data for item {item_code}")
    
    # Keep KT for Karnataka as SAP expects KT, not KA
    # if state_code == 'KT':
    #     state_code = 'KA'
    
    # Determine SGST vs IGST based on bill_to_code parameter
    is_sgst = bill_to_code == "B2C SGST ADD" if bill_to_code else (state_code == dest_state)
    
    if uni_tax != tax_rate:
        #logger.warning(f"Tax mismatch for {item_code}: SAP({tax_rate}) vs Unicommerce({uni_tax})")
        send_tax_mismatch_alert(item_code, channel_name, state_code, 'CS' if is_sgst else 'IG', uni_tax, tax_rate)
    
    # Generate GST code using correct format from old file
    if is_sgst:
        # For SGST transactions, use KACS format
        gst_code = f"KACS{int(uni_tax)}"
    else:
        # For IGST transactions, use KAIG format
        gst_code = f"KAIG{int(uni_tax)}"
    
    return gst_code

def send_tax_mismatch_alert(item_code, channel_name, state_code, tax_type, uni_tax, sap_tax):
    """Send email alert for tax code mismatch - COMMENTED OUT"""
    #logger.info(f"Tax mismatch detected for {item_code} but email notification disabled")


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

                # Check batch-specific available stock using OIBT (Item Batch Transaction) table
                # Using the exact SAP B1 validation query structure
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN T0."TotalQty" >= ? THEN 'True'
                            ELSE 'False'
                        END AS "IsBatchValid"
                    FROM 
                        (
                            SELECT SUM(T1."Quantity") AS "TotalQty"
                            FROM OIBT T1
                            WHERE T1."ItemCode" = ?
                              AND T1."WhsCode" = ?
                              AND T1."BatchNum" = ?
                        ) T0
                """, (required_qty, item_code, warehouse_code, batch_number))

                result = cursor.fetchone()

                if result and result[0] is not None:
                    is_batch_valid = result[0] == 'True'
                    
                    if is_batch_valid:
                        # Get actual quantity for reporting
                        cursor.execute("""
                            SELECT SUM("Quantity") AS "TotalQty"
                            FROM OIBT 
                            WHERE "ItemCode" = ? AND "WhsCode" = ? AND "BatchNum" = ?
                        """, (item_code, warehouse_code, batch_number))
                        
                        qty_result = cursor.fetchone()
                        available_qty = float(qty_result[0]) if qty_result and qty_result[0] is not None else 0
                        
                        available_items.append({
                            'ItemCode': item_code,
                            'BatchNumber': batch_number,
                            'Warehouse': warehouse_code,
                            'RequiredQty': required_qty,
                            'AvailableQty': available_qty,
                            'Status': 'AVAILABLE'
                        })
                    else:
                        # Get actual quantity for reporting
                        cursor.execute("""
                            SELECT SUM("Quantity") AS "TotalQty"
                            FROM OIBT 
                            WHERE "ItemCode" = ? AND "WhsCode" = ? AND "BatchNum" = ?
                        """, (item_code, warehouse_code, batch_number))
                        
                        qty_result = cursor.fetchone()
                        available_qty = float(qty_result[0]) if qty_result and qty_result[0] is not None else 0
                        
                        failed_items.append({
                            'ItemCode': item_code,
                            'BatchNumber': batch_number,
                            'Warehouse': warehouse_code,
                            'RequiredQty': required_qty,
                            'AvailableQty': available_qty,
                            'Status': 'INSUFFICIENT_STOCK'
                        })
                else:
                    # Check if batch exists in other warehouses
                    cursor.execute("""
                        SELECT "WhsCode", COALESCE(SUM("Quantity"), 0) AS "BatchQty"
                        FROM OIBT
                        WHERE "ItemCode" = ? AND "BatchNum" = ? AND "Quantity" > 0
                        GROUP BY "WhsCode"
                    """, (item_code, batch_number))
                    
                    other_locations = cursor.fetchall()
                    
                    if other_locations:
                        available_locations = [{"WhsCode": row[0], "BatchQty": row[1]} for row in other_locations]
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

def post_invoice_to_sap(payload):
    """Post invoice to SAP B1 and return the response"""
    try:
        session = get_cached_sap_session()  # Use cached session
        config = get_database_config()
        invoice_url = f"{config['sap_url']}Invoices"
        
        logger.info("Posting invoice to SAP B1")
        logger.info(f"Payload preview: {json.dumps(payload, indent=2)[:1000]}...")
        
        response = session.request(
            "POST", invoice_url,
            data=json.dumps(payload),
            headers=HEADERS,
            verify=False
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result.get('DocEntry'):
            logger.info(f"SAP invoice created successfully: DocNum {result.get('DocNum')}")
        else:
            logger.error(f"SAP invoice creation failed: {result}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        # Capture detailed SAP error response
        error_details = "Unknown error"
        try:
            if hasattr(e, 'response') and e.response is not None:
                error_details = e.response.text
                logger.error(f"SAP API Error {e.response.status_code}: {error_details}")
                
                # Try to parse JSON error response
                try:
                    error_json = e.response.json()
                    logger.error(f"SAP Error JSON: {json.dumps(error_json, indent=2)}")
                except:
                    pass
        except Exception as parse_error:
            logger.error(f"Failed to parse SAP error response: {str(parse_error)}")
        
        return {"error": f"SAP API Error {e.response.status_code if hasattr(e, 'response') and e.response else 'Unknown'}: {error_details}"}
        
    except Exception as e:
        logger.error(f"SAP invoice posting failed: {str(e)}")
        return {"error": str(e)}

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

def send_success_notification(channel_name, doc_num, payload):
    """Send success notification with Excel attachment"""
    try:
        # Create Excel report
        filename = f"SAP_Invoice_{doc_num}_{now_datetime().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(get_site_path(), 'private', 'files', filename)
        
        # Process line items for Excel
        line_items = []
        for item in payload.get("DocumentLines", []):
            base_data = item.copy()
            batches = base_data.pop("BatchNumbers", [])
            
            if batches:
                for batch in batches:
                    row = base_data.copy()
                    row["BatchNumber"] = batch.get("BatchNumber")
                    row["BatchQuantity"] = batch.get("Quantity")
                    line_items.append(row)
            else:
                base_data["BatchNumber"] = ""
                base_data["BatchQuantity"] = ""
                line_items.append(base_data)
        
        # Create DataFrames
        df_lines = pd.DataFrame(line_items)
        
        header_data = {key: payload.get(key) for key in [
            'CardCode', 'Comments', 'PayToCode', 'ShipToCode', 'DocDate', 
            'DocDueDate', 'U_BillingFrom', 'U_BillTo', 'TransportationCode',
            'UseBillToAddrToDetermineTax', 'Series'
        ]}
        header_data['SAP_DocNum'] = doc_num
        df_header = pd.DataFrame([header_data])
        
        # Write to Excel
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            df_header.to_excel(writer, index=False, sheet_name="Invoice Data", startrow=0)
            df_lines.to_excel(writer, index=False, sheet_name="Invoice Data", startrow=2)
        
        # Send email
        frappe.sendmail(
            recipients=get_email_recipients(),
            subject=f"SAP Invoice Created Successfully - {channel_name} - DocNum: {doc_num}",
            message="SAP invoice creation was successful. Please find the invoice details in the attached Excel file.",
            attachments=[{
                "fname": filename,
                "fcontent": open(file_path, 'rb').read()
            }]
        )
        
        # Cleanup file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        logger.info("Success notification sent")
        
    except Exception as e:
        logger.error(f"Failed to send success notification: {str(e)}")

def send_failure_notification(channel_name, error_message, payload=None):
    """Send failure notification"""
    try:
        subject = f"SAP Invoice Creation Failed - {channel_name}"
        message = f"""
        SAP invoice creation failed for channel: {channel_name}
        
        Error: {error_message}
        
        Please review the configuration and resolve the issue.
        """
        
        frappe.sendmail(
            recipients=get_email_recipients(),
            subject=subject,
            message=message,
            delayed=False
        )
        logger.info("Failure notification sent")
        
    except Exception as e:
        logger.error(f"Failed to send failure notification: {str(e)}")

def send_batch_quantity_alert(failed_items, channel_name):
    """Send detailed email notification about batch quantity issues"""
    try:
        subject = f"Batch Quantity Issues - {channel_name}"
        
        # Create HTML table for failed items
        table_rows = []
        for item in failed_items:
            shortage = float(item['RequiredQty']) - float(item['AvailableQty'])
            table_rows.append(f"""
            <tr>
                <td>{item['ItemCode']}</td>
                <td>{item['BatchNumber']}</td>
                <td>{item['Warehouse']}</td>
                <td>{item['RequiredQty']}</td>
                <td>{item['AvailableQty']}</td>
                <td style="color: red; font-weight: bold;">{shortage}</td>
            </tr>
            """)
        
        html_message = f"""
        <html>
        <body>
            <h2>Batch Quantity Issues Detected</h2>
            <p><strong>Channel:</strong> {channel_name}</p>
            <p><strong>Items with Issues:</strong> {len(failed_items)}</p>
            
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th>Item Code</th>
                        <th>Batch Number</th>
                        <th>Warehouse</th>
                        <th>Required Qty</th>
                        <th>Available Qty</th>
                        <th>Shortage</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
            
            <p>Please update stock in SAP and retry the invoice creation.</p>
        </body>
        </html>
        """
        
        frappe.sendmail(
            recipients=get_email_recipients(),
            subject=subject,
            message=html_message,
            as_markdown=False
        )
        
        logger.info("Batch quantity alert sent")
        
    except Exception as e:
        logger.error(f"Failed to send batch quantity alert: {str(e)}")


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
        failed_items, available_items = validate_batch_availability(payload, channel_name, order_list)
        
        if failed_items:
            error_msg = f"Batch validation failed for {len(failed_items)} items"
            logger.error(error_msg)
            send_batch_quantity_alert(failed_items, channel_name)
            create_batch_hold_record(failed_items, channel_name, order_list, payload)
            return {"error": error_msg, "failed_items": failed_items}
        
        # Post to SAP (uses cached session)
        result = post_invoice_to_sap(payload)
        
        if result.get('DocEntry'):
            # Update order records with SAP response for delivery line numbers
            update_order_records(order_list, result['DocEntry'], result['DocNum'], result)
            
            # Send success notification
            send_success_notification(channel_name, result['DocNum'], payload)
            
            logger.info(f"Successfully processed {len(order_list)} orders - DocNum: {result['DocNum']}")
        else:
            # Send failure notification
            error_msg = result.get('error', 'Unknown SAP error')
            send_failure_notification(channel_name, error_msg, payload)
        
        return result
        
    except Exception as e:
        error_msg = f"Order processing failed: {str(e)}"
        logger.error(error_msg)
        send_failure_notification(channel_name, error_msg)
        return {"error": error_msg}


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
        logger.info(f"OPTIMIZATION STATS: States Cached: {len(_sap_cache['states'])}, Items Cached: {len(_sap_cache['items'])}, Session Reused: {'Yes' if _sap_cache.get('session') else 'No'}")
        
        return summary
        
    except Exception as e:
        error_msg = f"Optimized invoice creation failed for {channel_name}: {str(e)}"
        logger.error(error_msg)
        frappe.log_error(error_msg, "AR Invoice Creation")
        send_failure_notification(channel_name, error_msg)
        raise
    finally:
        # Log final cache statistics
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
        new_failed_items, available_items = validate_batch_availability(payload, hold_doc.channel_name, order_list)
        
        if new_failed_items:
            logger.error(f"Still {len(new_failed_items)} items with quantity issues")
            return {"error": f"Still {len(new_failed_items)} items with quantity issues"}
        
        logger.info("All batch quantities are now available, proceeding with SAP posting")
        
        # Post to SAP (will use cached session)
        result = post_invoice_to_sap(payload)
        
        if result.get('DocEntry'):
            # Update order records with SAP response for delivery line numbers
            update_order_records(order_list, result['DocEntry'], result['DocNum'], result)
            
            # Update hold status
            hold_doc.status = 'Completed'
            hold_doc.resumed_by = frappe.session.user
            hold_doc.resumed_at = frappe.utils.now()
            hold_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
            # Send success notification
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
def create_amazon_invoices():
    """Create Amazon invoices for September 2025 - No parameters needed"""
    try:
        channel_name = "Amazon_IN_API"
        start_date = "01-09-2025"
        end_date = "30-09-2025"
        
        logger.info(f"=== Starting Amazon invoice creation: {start_date} to {end_date} ===")
        
        # Clear cache for new channel
        clear_sap_cache(channel_name)
        
        # Get channel configuration
        config = get_channel_configuration(channel_name)
        origin_state_code = config.get('origin_state_code', 'KA')
        
        # Get orders for processing
        sgst_order_names, igst_order_names = get_orders_for_processing(channel_name, start_date, end_date, origin_state_code)
        
        logger.info(f"Retrieved {len(sgst_order_names)} SGST orders and {len(igst_order_names)} IGST orders")
        
        if not sgst_order_names and not igst_order_names:
            logger.info("No orders found for processing")
            return {"message": "No orders found for processing"}
        
        # Process SGST orders
        sgst_result = None
        if sgst_order_names:
            logger.info(f"Processing {len(sgst_order_names)} SGST orders...")
            sgst_result = process_order_batch(channel_name, sgst_order_names, "B2C SGST ADD", start_date, end_date)
        
        # Process IGST orders
        igst_result = None
        if igst_order_names:
            logger.info(f"Processing {len(igst_order_names)} IGST orders...")
            igst_result = process_order_batch(channel_name, igst_order_names, "B2C IGST ADD", start_date, end_date)
        
        # Prepare results
        results = []
        if sgst_result:
            results.append({
                "Order_Type": "SGST Orders",
                "No of Orders": len(sgst_order_names),
                "AR Invoice Docnum": sgst_result.get('DocNum')
            })
        
        if igst_result:
            results.append({
                "Order_Type": "IGST Orders", 
                "No of Orders": len(igst_order_names),
                "AR Invoice Docnum": igst_result.get('DocNum')
            })
        
        logger.info(f"=== Amazon invoice creation completed ===")
        logger.info(f"AMAZON INVOICE CREATION SUMMARY")
        
        for result in results:
            order_type = result["Order_Type"]
            order_count = result["No of Orders"]
            docnum = result["AR Invoice Docnum"]
            status = "✅ SUCCESS" if docnum else "❌ FAILED"
            logger.info(f"{order_type}: {order_count} orders, Status: {status}, DocNum: {docnum}")
        
        return results
        
    except Exception as e:
        error_msg = f"Amazon invoice creation failed: {str(e)}"
        logger.error(error_msg)
        
        # Send failure notification
        send_failure_notification("Amazon_IN_API", str(e))
        
        raise

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
        return {
            "states_cached": len(_sap_cache.get('states', {})),
            "items_cached": len(_sap_cache.get('items', {})),
            "current_channel": _sap_cache.get('current_channel'),
            "session_active": bool(_sap_cache.get('session')),
            "session_time": str(_sap_cache.get('session_time', 'Not set'))
        }
    except Exception as e:
        return {"error": str(e)}

