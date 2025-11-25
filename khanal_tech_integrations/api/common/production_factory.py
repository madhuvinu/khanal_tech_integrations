"""
Production API Factory - COMMON UTILITY (Not plant-specific)
This is a helper utility that returns the appropriate production API instances based on plant_id.
Separates read operations (production_api.py) from write operations (production_post_api.py)

Why this exists:
- It's a common utility that helps decide which API class to use
- It's NOT plant-specific code - it's a helper function
- All plants use this same factory
- It's in /common/ because it's shared by all plants

Usage:
    from khanal_tech_integrations.api.common.production_factory import get_production_api, get_production_post_api
    read_api = get_production_api('nandi_hills')  # Returns read API (CommonProductionAPI or plant-specific)
    write_api = get_production_post_api('nandi_hills')  # Returns write API (CommonProductionPostAPI)
"""

import frappe
from khanal_tech_integrations.api.common.production_api import CommonProductionAPI
from khanal_tech_integrations.api.common.production_post_api import CommonProductionPostAPI


def get_production_api(plant_id):
    """
    Get production READ API for a specific plant (for fetching data from SAP HANA)
    
    Args:
        plant_id (str): Plant identifier (mahadevpura, nandi_hills, nandihills, malur, krishnagiri, champavath)
        
    Returns:
        BaseProductionAPI: Production API instance for read operations
    """
    # Normalize plant ID
    normalized_plant_id = normalize_plant_id(plant_id)
    
    # Try to import plant-specific API
    try:
        if normalized_plant_id == 'nandi_hills' or normalized_plant_id == 'nandihills' or normalized_plant_id == 'nandi-hills':
            from khanal_tech_integrations.api.plants.nandi_hills.nandi_hills_production import NandiHillsProductionAPI
            return NandiHillsProductionAPI()
        elif normalized_plant_id == 'malur':
            from khanal_tech_integrations.api.plants.malur.malur_production import MalurProductionAPI
            return MalurProductionAPI()
        elif normalized_plant_id == 'krishnagiri':
            from khanal_tech_integrations.api.plants.krishnagiri.krishnagiri_production import KrishnagiriProductionAPI
            return KrishnagiriProductionAPI()
        elif normalized_plant_id == 'champavath':
            from khanal_tech_integrations.api.plants.champavath.champavath_production import ChampavathProductionAPI
            return ChampavathProductionAPI()
        elif normalized_plant_id == 'mahadevpura':
            from khanal_tech_integrations.api.plants.mahadevpura.mahadevpura_production import MahadevpuraProductionAPI
            return MahadevpuraProductionAPI()
        else:
            # Default to common API for unknown plants
            frappe.log_error(f"Unknown plant ID: {plant_id}, using common production API", "Production Factory")
            return CommonProductionAPI(normalized_plant_id)
    except ImportError as e:
        # If plant-specific API doesn't exist, use common API
        frappe.log_error(f"Plant-specific API not found for {normalized_plant_id}, using common API: {str(e)}", "Production Factory")
        return CommonProductionAPI(normalized_plant_id)


def get_production_post_api(plant_id):
    """
    Get production WRITE API for a specific plant (for posting data to SAP B1)
    All plants use CommonProductionPostAPI for now (no plant-specific write logic yet)
    
    Args:
        plant_id (str): Plant identifier (mahadevpura, nandi_hills, nandihills, malur, krishnagiri, champavath)
        
    Returns:
        CommonProductionPostAPI: Production POST API instance for write operations
    """
    # Normalize plant ID
    normalized_plant_id = normalize_plant_id(plant_id)
    
    # For now, all plants use the common POST API
    # In the future, if a plant needs custom write logic, we can add plant-specific POST APIs here
    return CommonProductionPostAPI(normalized_plant_id)


def normalize_plant_id(plant_id):
    """
    Normalize plant ID to standard format
    
    Args:
        plant_id (str): Plant identifier
        
    Returns:
        str: Normalized plant ID
    """
    if not plant_id:
        return 'nandi_hills'
    
    normalized = plant_id.lower().strip()
    
    # Handle nandi-hills variations
    if normalized == 'nandi-hills' or normalized == 'nandihills':
        return 'nandi_hills'
    
    return normalized
