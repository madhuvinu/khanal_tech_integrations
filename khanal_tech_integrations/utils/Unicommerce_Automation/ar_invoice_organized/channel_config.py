import frappe
import logging

logger = logging.getLogger(__name__)

def get_supported_channels():
    """Get list of all supported e-commerce channels"""
    return [
        "AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7", "AMAZON_FBA_IN_BLR5", 
        "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8", "AMAZON_FBA_IN_DEL4", 
        "AMAZON_FBA_IN_DEL5", "AMAZON_FBA_IN_CJB1", "AMAZON_FBA_IN_MAA4",
        "Amazon_IN_API", "CRED", "FLIPKART", "DOGSEE_SITE_IN", "HN_SITE_IN",
        "ONDC_NSTORE", "HALFCIRCLEFULL", "MEESHO", "Snapdeal"
    ]

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
