"""
Nandi Hills Plant Production APIs
Handles plant-specific Production operations for Nandi Hills plant
Common functionality is in khanal_tech_integrations.api.common.production_api
"""

import frappe
from khanal_tech_integrations.api.common.production_api import CommonProductionAPI


class NandiHillsProductionAPI(CommonProductionAPI):
    """
    Nandi Hills Plant Production API Implementation
    Extends CommonProductionAPI with plant-specific customizations
    """
    
    def __init__(self):
        super().__init__('nandi_hills')
    
    # Plant-specific methods can be added here
    # Common methods (search_bom_in_sap, get_itt1_components, get_oitt_header, 
    # get_batch_numbers, get_warehouses) are inherited from CommonProductionAPI
    # Override them here ONLY if Nandi Hills needs custom behavior different from common


# ============================================================================
# WHITELISTED API ENDPOINTS
# These functions use the factory to get the right API instance
# Common methods use CommonProductionAPI, Nandi Hills specific methods are below
# ============================================================================

@frappe.whitelist(allow_guest=False)
def search_bom(search_query, plant_id='nandi_hills'):
    """
    Search BOM tables (OITT and ITT1) in SAP
    
    Args:
        search_query (str): Search term (minimum 2 characters)
        plant_id (str): Plant identifier
        
    Returns:
        dict: List of matching BOM records
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_api
    
    if not search_query or len(search_query) < 2:
        return {
            "success": False,
            "message": "Search query must be at least 2 characters",
            "data": []
        }
    
    api = get_production_api(plant_id)
    return api.search_bom_in_sap(search_query)


@frappe.whitelist(allow_guest=False)
def get_itt1_components(bom_code, plant_id='nandi_hills'):
    """
    Get ITT1 components for a BOM
    
    Args:
        bom_code (str): Father/BOM code
        plant_id (str): Plant identifier
        
    Returns:
        dict: List of ITT1 components
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_api
    
    if not bom_code:
        return {
            "success": False,
            "message": "BOM code is required",
            "data": []
        }
    
    api = get_production_api(plant_id)
    return api.get_itt1_components(bom_code)


@frappe.whitelist(allow_guest=False)
def get_oitt_header(bom_code, plant_id='nandi_hills'):
    """
    Get OITT header for a BOM
    
    Args:
        bom_code (str): BOM code
        plant_id (str): Plant identifier
        
    Returns:
        dict: OITT header details
    """
    if not bom_code:
        return {
            "success": False,
            "message": "BOM code is required",
            "data": None
        }
    
    from khanal_tech_integrations.api.common.production_factory import get_production_api
    api = get_production_api(plant_id)
    return api.get_oitt_header(bom_code)


@frappe.whitelist(allow_guest=False)
def get_batch_numbers(item_code, plant_id='nandi_hills', warehouse=None, date_from=None, date_to=None):
    """
    Get batch numbers for an item
    
    Args:
        item_code (str): Item code
        plant_id (str): Plant identifier
        warehouse (str): Warehouse code (optional)
        date_from (str): From date (optional)
        date_to (str): To date (optional)
        
    Returns:
        dict: List of batch numbers with quantities
    """
    if not item_code:
        return {
            "success": False,
            "message": "Item code is required",
            "data": []
        }
    
    from khanal_tech_integrations.api.common.production_factory import get_production_api
    api = get_production_api(plant_id)
    return api.get_batch_numbers(item_code, warehouse, date_from, date_to)


@frappe.whitelist(allow_guest=False)
def get_batch_numbers_from_batch_date_item(item_code, date_from=None, date_to=None, plant_id='nandi_hills'):
    """
    Get batch numbers from Batch Date Item doctype for an item code.
    If date_from and date_to are provided, filter by date range. Otherwise, return the latest batch numbers.
    
    Args:
        item_code: Item code to search for
        date_from: Optional from date in YYYY-MM-DD format
        date_to: Optional to date in YYYY-MM-DD format. Defaults to current date if date_from is provided
        plant_id: Plant identifier (optional, for future use)
    
    Returns:
        Dictionary with success status and list of batch numbers
    """
    from khanal_tech_integrations.api.plants.batchnumber_gen.batch_date_item_lookup import get_batch_numbers_by_item_code
    return get_batch_numbers_by_item_code(item_code, date_from=date_from, date_to=date_to)


@frappe.whitelist(allow_guest=False)
def get_warehouses(plant_id='nandi_hills'):
    """
    Get warehouses from OWHS table filtered by plant warehouse prefix
    
    Args:
        plant_id (str): Plant identifier (default: 'nandi_hills')
        
    Returns:
        dict: List of warehouses with WhsCode and WhsName
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_api
    api = get_production_api(plant_id)
    return api.get_warehouses()


@frappe.whitelist(allow_guest=False)
def approve_production_order(production_data, plant_id='nandi_hills'):
    """
    Create production order and set status to boposReleased
    Uses CommonProductionPostAPI for posting to SAP
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.approve_production_order(production_data)


@frappe.whitelist(allow_guest=False)
def goods_issue(production_order_doc_entry, production_data, plant_id='nandi_hills'):
    """
    Create Inventory Gen Exit (Goods Issue) for production order inputs
    Uses CommonProductionPostAPI for posting to SAP
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.goods_issue(production_order_doc_entry, production_data)


@frappe.whitelist(allow_guest=False)
def goods_receipt(production_order_doc_entry, production_data, plant_id='nandi_hills'):
    """
    Create Inventory Gen Entry (Goods Receipt) for production order outputs and byproducts
    Uses CommonProductionPostAPI for posting to SAP
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.goods_receipt(production_order_doc_entry, production_data)


@frappe.whitelist(allow_guest=False)
def close_production(production_order_doc_entry, close_date=None, plant_id='nandi_hills'):
    """
    Close production order by setting status to boposClosed
    Uses CommonProductionPostAPI for posting to SAP
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.close_production(production_order_doc_entry, close_date)


@frappe.whitelist(allow_guest=False)
def get_production_orders_list(filters=None, page=1, page_size=20, plant_id='nandi_hills'):
    """
    Get list of production orders from Production Kiosk doctype
    Uses CommonProductionPostAPI for fetching data
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.get_production_orders_list(filters, page, page_size)


@frappe.whitelist(allow_guest=False)
def get_production_order_for_resume(production_kiosk_name, plant_id='nandi_hills'):
    """
    Get full production order details for resuming workflow
    Uses CommonProductionPostAPI for fetching data
    """
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.get_production_order_for_resume(production_kiosk_name)


