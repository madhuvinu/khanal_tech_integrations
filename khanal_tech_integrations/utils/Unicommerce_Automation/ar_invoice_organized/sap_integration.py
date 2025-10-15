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
