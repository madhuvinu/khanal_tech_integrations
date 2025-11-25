"""
Common Production Post API - Shared production posting/writing functionality for all plants
This contains common methods for posting data to SAP (creating, updating, closing production orders).
Read operations are in production_api.py
"""

import frappe
import json
from datetime import datetime
from khanal_tech_integrations.api.plants.base.production_api import BaseProductionAPI


class CommonProductionPostAPI(BaseProductionAPI):
    """Common Production Post API with shared posting functionality for all plants"""
    
    def __init__(self, plant_id):
        """Initialize with plant ID"""
        super().__init__(plant_id)
    
    def approve_production_order(self, production_data):
        """
        Create production order and set status to boposReleased
        
        Args:
            production_data (dict): Production order data from UI
            
        Returns:
            dict: Production order response with DocEntry, DocNum, etc.
        """
        try:
            from khanal_tech_integrations.api.sap_b1_auth import AuthenticateSAPB1
            
            # Authenticate SAP B1
            b1_session = AuthenticateSAPB1()
            doc = frappe.get_doc('SAP Test Layer')
            b1_url = doc.sap_b1_url
            
            # Parse production_data if it's a string
            if isinstance(production_data, str):
                try:
                    production_data = json.loads(production_data)
                except json.JSONDecodeError as e:
                    frappe.throw(f"Invalid JSON in production_data: {str(e)}")
            
            # Validate that production_data is a dictionary
            if not isinstance(production_data, dict):
                frappe.throw(f"production_data must be a dictionary, got {type(production_data)}")
            
            # Check if ProductionOrderLines exists
            production_order_lines = production_data.get("ProductionOrderLines")
            
            # Handle case where ProductionOrderLines might be a string (JSON)
            if isinstance(production_order_lines, str):
                try:
                    production_order_lines = json.loads(production_order_lines)
                    production_data["ProductionOrderLines"] = production_order_lines
                except json.JSONDecodeError:
                    frappe.throw(f"ProductionOrderLines is not valid JSON: {production_order_lines}")
            
            # Validate that ProductionOrderLines exists and is not empty
            if not production_order_lines:
                frappe.throw("ProductionOrderLines is required and cannot be empty. Please provide at least one production order line.")
            
            if not isinstance(production_order_lines, list):
                frappe.throw(f"ProductionOrderLines must be a list, got {type(production_order_lines)}")
            
            if len(production_order_lines) == 0:
                frappe.throw("ProductionOrderLines cannot be an empty list. Please provide at least one production order line.")
            
            # Get BOM code to fetch IssueType from database
            bom_code = production_data.get("BOMCode") or production_data.get("ItemNo")
            issue_type_map = {}
            
            # Fetch ITT1 components from database to get IssueMthd for each item
            if bom_code:
                try:
                    from khanal_tech_integrations.api.common.production_factory import get_production_api
                    api = get_production_api(self.plant_id)
                    itt1_response = api.get_itt1_components(bom_code)
                    if itt1_response.get("success") and itt1_response.get("data"):
                        for comp in itt1_response.get("data", []):
                            item_code = comp.get("Code")
                            issue_mthd = comp.get("IssueMthd")
                            if item_code and issue_mthd:
                                issue_type_map[item_code] = issue_mthd
                except Exception as e:
                    frappe.log_error(f"Error fetching ITT1 components for IssueType: {str(e)}", "Production Order IssueType Error")
            
            # Build production order payload
            payload = {
                "ItemNo": production_data.get("ItemNo"),
                "PlannedQuantity": production_data.get("PlannedQuantity"),
                "PostingDate": production_data.get("PostingDate"),
                "Warehouse": production_data.get("Warehouse"),
                "ProductionOrderLines": []
            }
            
            # Add production order lines
            lines_processed = 0
            for idx, line in enumerate(production_order_lines):
                item_no = line.get("ItemNo")
                planned_qty = line.get("PlannedQuantity")
                
                if not item_no:
                    continue  # Skip this line
                
                # Get IssueType
                issue_type = line.get("ProductionOrderIssueType") or line.get("IssueType")
                if not issue_type:
                    issue_type = issue_type_map.get(item_no)
                
                # Map single character IssueMthd to SAP B1 IssueType format if needed
                if issue_type and len(issue_type) == 1:
                    issue_type_map_dict = {
                        'M': 'im_Manual',
                        'B': 'im_Backflush',
                        'P': 'im_Pick',
                        'A': 'im_Advanced'
                    }
                    issue_type = issue_type_map_dict.get(issue_type, 'im_Manual')
                
                # Default to Manual if still not found
                if not issue_type:
                    issue_type = 'im_Manual'
                
                # Ensure IssueType is in correct SAP B1 format
                if issue_type not in ['im_Manual', 'im_Backflush', 'im_Pick', 'im_Advanced']:
                    issue_type = 'im_Manual'
                
                # Validate required fields
                planned_qty = line.get("PlannedQuantity")
                warehouse = line.get("Warehouse")
                
                if planned_qty is None:
                    continue  # Skip this line
                
                if not warehouse:
                    continue  # Skip this line
                
                document_line = {
                    "ItemNo": item_no,
                    "PlannedQuantity": planned_qty,
                    "Warehouse": warehouse,
                    "ProductionOrderIssueType": issue_type
                }
                payload["ProductionOrderLines"].append(document_line)
                lines_processed += 1
            
            # Validate that ProductionOrderLines is not empty before sending to SAP
            if not payload["ProductionOrderLines"]:
                error_msg = f"ProductionOrderLines cannot be empty. Input had {len(production_order_lines)} items but only {lines_processed} were processed and added."
                self._save_production_result(production_data, None, False, error_msg, json.dumps(payload, indent=2, default=str))
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Create production order
            url = b1_url + "ProductionOrders"
            
            headersList = {
                "Accept": "*/*",
                "User-Agent": "Khanal Tech",
                "Content-Type": "application/json"
            }
            
            request_payload_str = json.dumps(payload, indent=2, default=str)
            
            # Final validation
            if "ProductionOrderLines" not in payload:
                error_msg = "ProductionOrderLines key is missing from payload"
                self._save_production_result(production_data, None, False, error_msg, request_payload_str)
                return {
                    "success": False,
                    "message": error_msg
                }
            
            if not payload["ProductionOrderLines"] or len(payload["ProductionOrderLines"]) == 0:
                error_msg = f"ProductionOrderLines array is empty. Expected at least 1 line item."
                self._save_production_result(production_data, None, False, error_msg, request_payload_str)
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Merge headers into session
            try:
                b1_session.headers.update(headersList)
            except Exception:
                pass
            
            # Make the POST request to SAP
            try:
                payload_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
                response = b1_session.request("POST", url, data=payload_json, headers=headersList, verify=False)
                
                if response.status_code not in [200, 201]:
                    error_data = {}
                    try:
                        if response.text:
                            error_data = response.json()
                    except Exception:
                        pass
                    
                    error_msg = None
                    if error_data:
                        error_msg = (
                            error_data.get('error', {}).get('message', {}).get('value') or
                            error_data.get('error', {}).get('message', {}).get('lang') or
                            error_data.get('error', {}).get('message') or
                            error_data.get('message') or
                            str(error_data.get('error', {}))
                        )
                    
                    if not error_msg:
                        error_msg = response.text or 'Unknown SAP error'
                    
                    return {
                        "success": False,
                        "message": error_msg
                    }
                
                response_data = response.json()
                doc_entry = response_data.get("DocEntry") or response_data.get("AbsoluteEntry")
                doc_num = response_data.get("DocNum") or response_data.get("DocumentNumber")
                
                # Release the production order
                patch_url = b1_url + f"ProductionOrders({doc_entry})"
                patch_payload = {
                    "ProductionOrderStatus": "boposReleased"
                }
                patch_response = b1_session.request("PATCH", patch_url, data=json.dumps(patch_payload), headers=headersList, verify=False)
                
                if patch_response.status_code not in [200, 201, 204]:
                    error_data = patch_response.json() if patch_response.text else {}
                    error_msg = error_data.get('error', {}).get('message', {}).get('value', patch_response.text)
                    return {
                        "success": False,
                        "message": f"Production order created but failed to release: {error_msg}",
                        "productionOrderDocEntry": doc_entry,
                        "productionOrderDocNum": doc_num,
                        "sapResponse": response_data
                    }
                
                # Fetch the updated production order
                get_url = b1_url + f"ProductionOrders({doc_entry})"
                get_response = b1_session.request("GET", get_url, headers=headersList, verify=False)
                
                if get_response.status_code in [200, 201]:
                    updated_response_data = get_response.json()
                else:
                    updated_response_data = response_data
                    updated_response_data["ProductionOrderStatus"] = "boposReleased"
                
                final_doc_entry = updated_response_data.get("DocEntry") or updated_response_data.get("AbsoluteEntry") or doc_entry
                final_doc_num = updated_response_data.get("DocNum") or updated_response_data.get("DocumentNumber") or doc_num
                
                # Save successful result
                self._save_production_result(
                    production_data, 
                    updated_response_data, 
                    True, 
                    "Production order created and released successfully",
                    request_payload_str,
                    json.dumps(updated_response_data, indent=2, default=str)
                )
                
                return {
                    "success": True,
                    "productionOrderDocEntry": final_doc_entry,
                    "productionOrderDocNum": final_doc_num,
                    "ProductionOrderStatus": updated_response_data.get("ProductionOrderStatus", "boposReleased"),
                    "sapResponse": updated_response_data,
                    "AbsoluteEntry": updated_response_data.get("AbsoluteEntry"),
                    "DocumentNumber": updated_response_data.get("DocumentNumber"),
                    "Series": updated_response_data.get("Series"),
                    "ItemNo": updated_response_data.get("ItemNo"),
                    "ProductionOrderType": updated_response_data.get("ProductionOrderType"),
                    "PlannedQuantity": updated_response_data.get("PlannedQuantity")
                }
                
            except Exception as e:
                error_msg = f"Network error: {str(e)[:100]}"
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = str(e)
            frappe.log_error(f"Error in approve_production_order: {error_msg[:200]}", "Production Order Approve Error")
            return {
                "success": False,
                "message": error_msg
            }
    
    def goods_issue(self, production_order_doc_entry, production_data):
        """
        Create Inventory Gen Exit (Goods Issue) for production order inputs
        
        Args:
            production_order_doc_entry (int): Production order DocEntry
            production_data (dict): Production data with inputs
            
        Returns:
            dict: Goods issue response
        """
        try:
            from khanal_tech_integrations.api.sap_b1_auth import AuthenticateSAPB1
            
            # Authenticate SAP B1
            b1_session = AuthenticateSAPB1()
            doc = frappe.get_doc('SAP Test Layer')
            b1_url = doc.sap_b1_url
            
            # Parse production_data if it's a string
            if isinstance(production_data, str):
                production_data = json.loads(production_data)
            
            # Fetch production order from SAP to get line numbers
            get_url = f"{b1_url}ProductionOrders({production_order_doc_entry})"
            get_response = b1_session.request("GET", get_url, headers={"Accept": "*/*", "Content-Type": "application/json"}, verify=False)
            
            if get_response.status_code not in [200, 201]:
                return {
                    "success": False,
                    "message": f"Failed to fetch production order: {get_response.text}"
                }
            
            production_order = get_response.json()
            production_order_lines = production_order.get("ProductionOrderLines", [])
            
            # Create a map of ItemNo to BaseLine
            item_to_baseline = {}
            for idx, po_line in enumerate(production_order_lines):
                item_code = po_line.get("ItemCode")
                if item_code:
                    line_num = po_line.get("LineNum", idx)
                    item_to_baseline[item_code] = line_num
            
            # Filter inputs (positive PlannedQuantity)
            inputs = [line for line in production_data.get("ProductionOrderLines", []) if line.get("PlannedQuantity", 0) > 0]
            
            if not inputs:
                return {
                    "success": False,
                    "message": "No input materials found (positive PlannedQuantity required)"
                }
            
            # Build document lines
            document_lines = []
            for input_line in inputs:
                item_no = input_line.get("ItemNo")
                base_line = item_to_baseline.get(item_no, None)
                
                if base_line is None:
                    for idx, po_line in enumerate(production_order_lines):
                        if po_line.get("ItemCode") == item_no:
                            base_line = po_line.get("LineNum", idx)
                            item_to_baseline[item_no] = base_line
                            break
                    
                    if base_line is None:
                        input_index = inputs.index(input_line)
                        if input_index < len(production_order_lines):
                            base_line = production_order_lines[input_index].get("LineNum", input_index)
                        else:
                            continue
                
                # Calculate total quantity
                total_quantity = 0
                batch_numbers_array = []
                
                selected_batches = input_line.get("selectedBatches", [])
                batch_number = input_line.get("BatchNumber")
                
                if selected_batches and len(selected_batches) > 0:
                    for batch in selected_batches:
                        batch_qty = batch.get("inputQuantity", 0) or batch.get("Quantity", 0)
                        if batch_qty > 0:
                            total_quantity += float(batch_qty)
                            batch_numbers_array.append({
                                "BatchNumber": batch.get("BatchNumber"),
                                "Quantity": float(batch_qty),
                                "ItemCode": item_no
                            })
                elif batch_number:
                    total_quantity = float(input_line.get("PlannedQuantity", 0))
                    batch_numbers_array.append({
                        "BatchNumber": batch_number,
                        "Quantity": total_quantity,
                        "ItemCode": item_no
                    })
                else:
                    total_quantity = float(input_line.get("PlannedQuantity", 0))
                
                if total_quantity > 0:
                    line = {
                        "Quantity": total_quantity,
                        "WarehouseCode": input_line.get("Warehouse"),
                        "AccountCode": "12500900",
                        "UseBaseUnits": "tYES",
                        "BaseEntry": int(production_order_doc_entry),
                        "BaseLine": base_line
                    }
                    
                    if batch_numbers_array:
                        line["BatchNumbers"] = batch_numbers_array
                    
                    document_lines.append(line)
            
            if not document_lines:
                return {
                    "success": False,
                    "message": "No valid document lines created."
                }
            
            # Build payload
            posting_date = production_data.get("PostingDate") or datetime.now().strftime("%Y-%m-%d")
            payload = {
                "DocDate": posting_date,
                "JournalMemo": "Issue for Production",
                "DocObjectCode": "oInventoryGenExit",
                "DocumentLines": document_lines
            }
            
            # Post to SAP
            url = f"{b1_url}InventoryGenExits"
            response = b1_session.post(url, json=payload, verify=False)
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', {}).get('value', response.text) or response.text or 'Unknown error'
                return {
                    "success": False,
                    "message": error_msg
                }
            
            response_data = response.json()
            
            # Save goods issue response
            try:
                production_kiosk = frappe.db.get_value("Production Kiosk", {"sap_absoluteentry": str(production_order_doc_entry)}, "name")
                if production_kiosk:
                    doc = frappe.get_doc("Production Kiosk", production_kiosk)
                    doc.goods_issue_response_json = json.dumps(response_data, indent=2, default=str)
                    doc.issue_for_production_docentry = str(response_data.get("DocEntry"))
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error saving goods issue response: {str(e)[:200]}", "Goods Issue Save Response Error")
            
            return {
                "success": True,
                "goodsIssueDocEntry": response_data.get("DocEntry"),
                "goodsIssueDocNum": response_data.get("DocNum")
            }
            
        except Exception as e:
            frappe.log_error(f"Error in goods_issue: {str(e)}", "Goods Issue Error")
            return {
                "success": False,
                "message": str(e)
            }
    
    def goods_receipt(self, production_order_doc_entry, production_data):
        """
        Create Inventory Gen Entry (Goods Receipt) for production order outputs and byproducts
        
        Args:
            production_order_doc_entry (int): Production order DocEntry
            production_data (dict): Production data with outputs and byproducts
            
        Returns:
            dict: Goods receipt response
        """
        try:
            from khanal_tech_integrations.api.sap_b1_auth import AuthenticateSAPB1
            
            # Authenticate SAP B1
            b1_session = AuthenticateSAPB1()
            doc = frappe.get_doc('SAP Test Layer')
            b1_url = doc.sap_b1_url
            
            # Parse production_data if it's a string
            if isinstance(production_data, str):
                production_data = json.loads(production_data)
            
            document_lines = []
            
            # Add main output (header ItemNo)
            output_quantity = production_data.get("PlannedQuantity", 0)
            output_batch = production_data.get("outputBatchNumber") or production_data.get("BatchNumber")
            if output_quantity > 0:
                output_line = {
                    "Quantity": float(output_quantity),
                    "WarehouseCode": production_data.get("Warehouse"),
                    "AccountCode": "12500900",
                    "UseBaseUnits": "tYES",
                    "BaseEntry": int(production_order_doc_entry),
                    "BaseLine": None
                }
                
                if output_batch:
                    output_line["BatchNumbers"] = [{
                        "BatchNumber": output_batch,
                        "Quantity": float(output_quantity),
                        "ItemCode": production_data.get("ItemNo")
                    }]
                
                document_lines.append(output_line)
            
            # Add byproducts (negative PlannedQuantity lines)
            byproducts = [line for line in production_data.get("ProductionOrderLines", []) if line.get("PlannedQuantity", 0) < 0]
            for byproduct in byproducts:
                byproduct_quantity = abs(byproduct.get("PlannedQuantity", 0))
                byproduct_batch = byproduct.get("outputBatchNumber") or byproduct.get("BatchNumber")
                
                byproduct_line = {
                    "Quantity": float(byproduct_quantity),
                    "WarehouseCode": byproduct.get("Warehouse") or production_data.get("Warehouse"),
                    "AccountCode": "12500900",
                    "UseBaseUnits": "tYES",
                    "BaseEntry": int(production_order_doc_entry),
                    "BaseLine": None
                }
                
                if byproduct_batch:
                    byproduct_line["BatchNumbers"] = [{
                        "BatchNumber": byproduct_batch,
                        "Quantity": float(byproduct_quantity),
                        "ItemCode": byproduct.get("ItemNo")
                    }]
                
                document_lines.append(byproduct_line)
            
            if not document_lines:
                return {
                    "success": False,
                    "message": "No output materials found"
                }
            
            # Build payload
            posting_date = production_data.get("PostingDate") or datetime.now().strftime("%Y-%m-%d")
            payload = {
                "DocDate": posting_date,
                "JournalMemo": "Receipt from Production",
                "DocObjectCode": "oInventoryGenEntry",
                "DocumentLines": document_lines
            }
            
            # Post to SAP
            url = f"{b1_url}InventoryGenEntries"
            response = b1_session.post(url, json=payload, verify=False)
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', {}).get('value', response.text) or response.text or 'Unknown error'
                return {
                    "success": False,
                    "message": error_msg
                }
            
            response_data = response.json()
            
            # Save goods receipt response
            try:
                production_kiosk = frappe.db.get_value("Production Kiosk", {"sap_absoluteentry": str(production_order_doc_entry)}, "name")
                if production_kiosk:
                    doc = frappe.get_doc("Production Kiosk", production_kiosk)
                    doc.goods_receipt_response_json = json.dumps(response_data, indent=2, default=str)
                    doc.receipt_from_production_docentry = str(response_data.get("DocEntry"))
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error saving goods receipt response: {str(e)[:200]}", "Goods Receipt Save Response Error")
            
            return {
                "success": True,
                "goodsReceiptDocEntry": response_data.get("DocEntry"),
                "goodsReceiptDocNum": response_data.get("DocNum")
            }
            
        except Exception as e:
            frappe.log_error(f"Error in goods_receipt: {str(e)}", "Goods Receipt Error")
            return {
                "success": False,
                "message": str(e)
            }
    
    def close_production(self, production_order_doc_entry, close_date=None):
        """
        Close production order by setting status to boposClosed
        
        Args:
            production_order_doc_entry (int): Production order DocEntry
            close_date (str): Deprecated - not used (SAP sets CloseDate automatically)
            
        Returns:
            dict: Close production response
        """
        try:
            from khanal_tech_integrations.api.sap_b1_auth import AuthenticateSAPB1
            
            # Authenticate SAP B1
            b1_session = AuthenticateSAPB1()
            doc = frappe.get_doc('SAP Test Layer')
            b1_url = doc.sap_b1_url
            
            # Build patch payload
            payload = {
                "ProductionOrderStatus": "boposClosed"
            }
            
            # Patch production order
            url = f"{b1_url}ProductionOrders({production_order_doc_entry})"
            response = b1_session.patch(url, json=payload, verify=False)
            
            if response.status_code not in [200, 201, 204]:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', {}).get('value', response.text)
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Fetch the updated production order to get the CloseDate
            get_url = f"{b1_url}ProductionOrders({production_order_doc_entry})"
            get_response = b1_session.get(get_url, verify=False)
            
            close_date = None
            if get_response.status_code == 200:
                order_data = get_response.json()
                close_date = order_data.get("CloseDate")
            
            # Update Production Kiosk document
            try:
                production_kiosk = frappe.db.get_value("Production Kiosk", {"sap_absoluteentry": str(production_order_doc_entry)}, "name")
                if production_kiosk:
                    doc = frappe.get_doc("Production Kiosk", production_kiosk)
                    doc.production_order_status = "boposClosed"
                    doc.sap_status = "Production Completed"
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error updating Production Kiosk status: {str(e)[:200]}", "Close Production Save Status Error")
            
            return {
                "success": True,
                "productionOrderDocEntry": production_order_doc_entry,
                "ProductionOrderStatus": "boposClosed",
                "CloseDate": close_date
            }
            
        except Exception as e:
            frappe.log_error(f"Error in close_production: {str(e)}", "Close Production Error")
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_production_orders_list(self, filters=None, page=1, page_size=20):
        """
        Get list of production orders from Production Kiosk doctype
        
        Args:
            filters (dict): Filter criteria (optional)
            page (int): Page number (default: 1)
            page_size (int): Records per page (default: 20)
            
        Returns:
            dict: List of production orders with pagination info
        """
        try:
            # Parse filters if string
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if not filters:
                filters = {}
            
            # Extract date range filters
            date_from = filters.pop('date_from', None)
            date_to = filters.pop('date_to', None)
            
            # Build date range filter
            if date_from or date_to:
                if date_from and date_to:
                    filters['modified'] = ['between', [date_from, date_to]]
                elif date_from:
                    filters['modified'] = ['>=', date_from]
                elif date_to:
                    from datetime import timedelta
                    date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                    date_to_end = (date_to_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                    filters['modified'] = ['<', date_to_end]
            
            # Filter to show only orders that have been created
            if 'sap_absoluteentry' not in filters:
                filters['sap_absoluteentry'] = ['is', 'set']
            
            # Get total count
            total_count = frappe.db.count('Production Kiosk', filters=filters)
            
            # Fetch records for sorting
            fetch_limit = min(1000, total_count)
            
            production_list_all = frappe.get_all(
                'Production Kiosk',
                filters=filters,
                fields=[
                    'name', 
                    'created_date',
                    'modified',
                    'sap_absoluteentry',
                    'sap_production_number',
                    'sap_status',
                    'production_order_status',
                    'status',
                    'user_email',
                    'user_name',
                    'error_message',
                    'request_payload_json',
                    'response_payload_json'
                ],
                order_by='modified desc',
                limit=fetch_limit
            )
            
            # Extract PostingDate from response_payload_json
            for order in production_list_all:
                posting_date = None
                posting_date_obj = None
                
                if order.get('response_payload_json'):
                    try:
                        response_data = json.loads(order['response_payload_json']) if isinstance(order['response_payload_json'], str) else order['response_payload_json']
                        if isinstance(response_data, dict):
                            posting_date = response_data.get('PostingDate') or response_data.get('postingDate')
                            if not posting_date and isinstance(response_data.get('value'), list) and len(response_data.get('value', [])) > 0:
                                posting_date = response_data['value'][0].get('PostingDate') or response_data['value'][0].get('postingDate')
                    except (json.JSONDecodeError, AttributeError, KeyError):
                        pass
                
                # Convert PostingDate string to datetime object
                if posting_date:
                    try:
                        if isinstance(posting_date, str):
                            if len(posting_date) == 10:
                                posting_date_obj = datetime.strptime(posting_date, '%Y-%m-%d')
                            else:
                                posting_date_obj = datetime.fromisoformat(posting_date.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        posting_date_obj = None
                
                order['posting_date'] = posting_date
                order['posting_date_obj'] = posting_date_obj
                
                # For display, use modified date
                if order.get('modified'):
                    if isinstance(order['modified'], str):
                        order['display_date'] = order['modified']
                    else:
                        order['display_date'] = order['modified'].strftime('%Y-%m-%d %H:%M:%S')
                elif order.get('created_date'):
                    if isinstance(order['created_date'], str):
                        order['display_date'] = order['created_date']
                    else:
                        order['display_date'] = order['created_date'].strftime('%Y-%m-%d %H:%M:%S')
                elif posting_date:
                    order['display_date'] = posting_date
                else:
                    order['display_date'] = None
            
            # Sort by modified date
            production_list_all.sort(key=lambda x: (
                x.get('modified') if x.get('modified') else datetime.min,
                x.get('created_date') if x.get('created_date') else datetime.min
            ), reverse=True)
            
            # Apply pagination
            start = (int(page) - 1) * int(page_size)
            production_list = production_list_all[start:start + int(page_size)]
            
            return {
                "success": True,
                "data": production_list,
                "total_count": total_count,
                "page": int(page),
                "page_size": int(page_size),
                "total_pages": (total_count + int(page_size) - 1) // int(page_size)
            }
            
        except Exception as e:
            frappe.log_error(f"Error fetching production orders list: {str(e)}", "Production Orders List Error")
            return {
                "success": False,
                "message": str(e),
                "data": [],
                "total_count": 0
            }
    
    def get_production_order_for_resume(self, production_kiosk_name):
        """
        Get full production order details for resuming workflow
        
        Args:
            production_kiosk_name (str): Production Kiosk document name
            
        Returns:
            dict: Full production order details
        """
        try:
            # Get the Production Kiosk document
            if not frappe.db.exists("Production Kiosk", production_kiosk_name):
                return {
                    "success": False,
                    "message": f"Production order {production_kiosk_name} not found"
                }
            
            doc = frappe.get_doc("Production Kiosk", production_kiosk_name)
            
            # Parse request payload
            request_data = None
            if doc.request_payload_json:
                try:
                    request_data = json.loads(doc.request_payload_json) if isinstance(doc.request_payload_json, str) else doc.request_payload_json
                except json.JSONDecodeError:
                    pass
            
            # Parse response payload
            response_data = None
            if doc.response_payload_json:
                try:
                    response_data = json.loads(doc.response_payload_json) if isinstance(doc.response_payload_json, str) else doc.response_payload_json
                except json.JSONDecodeError:
                    pass
            
            # Determine workflow state
            workflow_state = {
                "productionOrderCreated": bool(doc.sap_absoluteentry),
                "goodsIssueCompleted": bool(doc.issue_for_production_docentry),
                "goodsReceiptCompleted": bool(doc.receipt_from_production_docentry),
                "productionClosed": doc.production_order_status == "boposClosed" or doc.sap_status == "Production Completed"
            }
            
            # Calculate workflow step
            workflow_step = 0
            if workflow_state["productionOrderCreated"]:
                workflow_step = 1
            if workflow_state["goodsIssueCompleted"]:
                workflow_step = 2
            if workflow_state["goodsReceiptCompleted"]:
                workflow_step = 3
            if workflow_state["productionClosed"]:
                workflow_step = 4
            
            return {
                "success": True,
                "data": {
                    "name": doc.name,
                    "sap_absoluteentry": doc.sap_absoluteentry,
                    "sap_production_number": doc.sap_production_number,
                    "sap_status": doc.sap_status,
                    "production_order_status": doc.production_order_status,
                    "status": doc.status,
                    "created_date": str(doc.created_date) if doc.created_date else None,
                    "user_email": doc.user_email,
                    "user_name": doc.user_name,
                    "error_message": doc.error_message,
                    "request_payload": request_data,
                    "response_payload": response_data,
                    "workflow_state": workflow_state,
                    "workflow_step": workflow_step,
                    "issue_for_production_docentry": doc.issue_for_production_docentry,
                    "receipt_from_production_docentry": doc.receipt_from_production_docentry,
                    "journalentry_docentry": doc.journalentry_docentry
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error fetching production order for resume: {str(e)}", "Resume Production Order Error")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _save_production_result(self, production_data, sap_response, success, message, request_payload, response_payload=None):
        """
        Save production order request and response to Production Kiosk doctype
        Internal method - only called for successful responses
        
        Args:
            production_data: Original production data sent
            sap_response: SAP response data (must be successful)
            success: Boolean indicating success/failure
            message: Status message
            request_payload: JSON string of request payload
            response_payload: JSON string of response payload (optional)
        """
        try:
            # Extract SAP Doc Entry
            sap_doc_entry = sap_response.get("DocEntry") or sap_response.get("AbsoluteEntry") if sap_response else None
            
            if not sap_doc_entry:
                frappe.log_error("Cannot save Production Kiosk: No SAP Doc Entry in response", "Production Kiosk Save Error")
                return
            
            # Check if record already exists
            existing_doc = frappe.db.exists("Production Kiosk", {"sap_absoluteentry": str(sap_doc_entry)})
            
            if existing_doc:
                # Update existing record
                doc = frappe.get_doc("Production Kiosk", existing_doc)
                doc.sap_absoluteentry = str(sap_doc_entry)
                doc.sap_production_number = str(sap_response.get("DocNum") or sap_response.get("DocumentNumber") if sap_response else "")
                doc.sap_status = "Production Released"
                doc.error_message = message[:500] if message and len(message) > 500 else message
                doc.request_payload_json = request_payload
                doc.response_payload_json = response_payload or (json.dumps(sap_response, indent=2, default=str) if sap_response else None)
                doc.production_order_status = sap_response.get("ProductionOrderStatus") if sap_response else None
                doc.save(ignore_permissions=True)
                frappe.db.commit()
            else:
                # Create new record
                doc = frappe.get_doc({
                    "doctype": "Production Kiosk",
                    "sap_absoluteentry": str(sap_doc_entry),
                    "sap_production_number": str(sap_response.get("DocNum") or sap_response.get("DocumentNumber") if sap_response else ""),
                    "sap_status": "Production Released",
                    "error_message": message[:500] if message and len(message) > 500 else message,
                    "request_payload_json": request_payload,
                    "response_payload_json": response_payload or (json.dumps(sap_response, indent=2, default=str) if sap_response else None),
                    "production_order_status": sap_response.get("ProductionOrderStatus") if sap_response else None
                })
                doc.insert(ignore_permissions=True)
                frappe.db.commit()
            
        except Exception as e:
            error_msg = f"Error saving Production Kiosk: {str(e)[:200]}"
            frappe.log_error(error_msg, "Production Kiosk Save Error")

