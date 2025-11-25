"""
Champavath Plant Production APIs
Handles plant-specific Production operations for Champavath plant
Common functionality is in khanal_tech_integrations.api.common.production_api
"""

import frappe
from khanal_tech_integrations.api.common.production_api import CommonProductionAPI
from khanal_tech_integrations.api.common.production_factory import get_production_api


class ChampavathProductionAPI(CommonProductionAPI):
    """
    Champavath Plant Production API Implementation
    Extends CommonProductionAPI with plant-specific customizations
    """
    
    def __init__(self):
        super().__init__('champavath')
    
    # Plant-specific methods can be added here
    # Common methods are inherited from CommonProductionAPI
    # Override them here ONLY if Champavath needs custom behavior


# ============================================================================
# WHITELISTED API ENDPOINTS
# These functions use the factory to get the right API instance
# ============================================================================

@frappe.whitelist(allow_guest=False)
def search_bom(search_query, plant_id='champavath'):
    """Search BOM tables in SAP"""
    if not search_query or len(search_query) < 2:
        return {
            "success": False,
            "message": "Search query must be at least 2 characters",
            "data": []
        }
    api = get_production_api(plant_id)
    return api.search_bom_in_sap(search_query)


@frappe.whitelist(allow_guest=False)
def get_itt1_components(bom_code, plant_id='champavath'):
    """Get ITT1 components for a BOM"""
    if not bom_code:
        return {
            "success": False,
            "message": "BOM code is required",
            "data": []
        }
    api = get_production_api(plant_id)
    return api.get_itt1_components(bom_code)


@frappe.whitelist(allow_guest=False)
def get_oitt_header(bom_code, plant_id='champavath'):
    """Get OITT header for a BOM"""
    if not bom_code:
        return {
            "success": False,
            "message": "BOM code is required",
            "data": None
        }
    api = get_production_api(plant_id)
    return api.get_oitt_header(bom_code)


@frappe.whitelist(allow_guest=False)
def get_batch_numbers(item_code, plant_id='champavath', warehouse=None, date_from=None, date_to=None):
    """Get batch numbers for an item"""
    if not item_code:
        return {
            "success": False,
            "message": "Item code is required",
            "data": []
        }
    api = get_production_api(plant_id)
    return api.get_batch_numbers(item_code, warehouse, date_from, date_to)


@frappe.whitelist(allow_guest=False)
def get_batch_numbers_from_batch_date_item(item_code, date_from=None, date_to=None, plant_id='champavath'):
    """Get batch numbers from Batch Date Item doctype"""
    from khanal_tech_integrations.api.plants.batchnumber_gen.batch_date_item_lookup import get_batch_numbers_by_item_code
    return get_batch_numbers_by_item_code(item_code, date_from=date_from, date_to=date_to)


@frappe.whitelist(allow_guest=False)
def get_warehouses(plant_id='champavath'):
    """Get warehouses from OWHS table"""
    api = get_production_api(plant_id)
    return api.get_warehouses()


# Write operations use CommonProductionPostAPI
@frappe.whitelist(allow_guest=False)
def approve_production_order(production_data, plant_id='champavath'):
    """Approve production order - uses CommonProductionPostAPI"""
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.approve_production_order(production_data)


@frappe.whitelist(allow_guest=False)
def goods_issue(production_order_doc_entry, production_data, plant_id='champavath'):
    """Goods issue - uses CommonProductionPostAPI"""
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.goods_issue(production_order_doc_entry, production_data)


@frappe.whitelist(allow_guest=False)
def goods_receipt(production_order_doc_entry, production_data, plant_id='champavath'):
    """Goods receipt - uses CommonProductionPostAPI"""
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.goods_receipt(production_order_doc_entry, production_data)


@frappe.whitelist(allow_guest=False)
def close_production(production_order_doc_entry, close_date=None, plant_id='champavath'):
    """Close production - uses CommonProductionPostAPI"""
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.close_production(production_order_doc_entry, close_date)


@frappe.whitelist(allow_guest=False)
def get_production_orders_list(filters=None, page=1, page_size=20, plant_id='champavath'):
    """Get production orders list - uses CommonProductionPostAPI"""
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.get_production_orders_list(filters, page, page_size)


@frappe.whitelist(allow_guest=False)
def get_production_order_for_resume(production_kiosk_name, plant_id='champavath'):
    """Get production order for resume - uses CommonProductionPostAPI"""
    from khanal_tech_integrations.api.common.production_factory import get_production_post_api
    
    api = get_production_post_api(plant_id)
    return api.get_production_order_for_resume(production_kiosk_name)

