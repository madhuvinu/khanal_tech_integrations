"""
SAP Milk Data Sync Script
Fetches milk purchase data from SAP HANA database and syncs to Frappe doctypes
"""

import frappe
import datetime
from frappe import _
from frappe.utils import get_datetime, now


@frappe.whitelist()
def fetch_sap_milk_data():
    """
    Fetch milk purchase data from SAP HANA and sync to SAP Milk Data doctype.
    Uses incremental sync based on last_saved_date from SAP Milk Log.
    
    Returns:
        str: Success message with count of records inserted
    """
    connection = None
    cursor = None
    sap_connector = None
    
    try:
        # Step 1: Get last saved date from SAP Milk Log (stored as string in YYYY-MM-DD HH:MI:SS format)
        last_log_str = frappe.db.get_value("SAP Milk Log", {}, "last_saved_date")
        
        if not last_log_str:
            # Fallback to a default date if no log exists
            last_log_str = "2024-01-01 00:00:00"
            frappe.logger().info("No existing SAP Milk Log found, using default date: 2024-01-01 00:00:00")
        else:
            # Ensure it's a string in the correct format (YYYY-MM-DD HH:MI:SS, no microseconds)
            if isinstance(last_log_str, datetime.datetime):
                last_log_str = last_log_str.strftime('%Y-%m-%d %H:%M:%S')
            elif not isinstance(last_log_str, str):
                last_log_str = str(last_log_str)
            
            # Remove microseconds if present (e.g., "2025-11-05 17:05:00.158732" -> "2025-11-05 17:05:00")
            if '.' in last_log_str and len(last_log_str.split('.')) > 1:
                last_log_str = last_log_str.split('.')[0]
            
            # Ensure format is exactly YYYY-MM-DD HH:MI:SS (19 characters)
            if len(last_log_str) > 19:
                last_log_str = last_log_str[:19]
        
        # Step 2: Get HANA connection
        from khanal_tech_integrations.api.common.sap_connector import SAPConnector
        
        sap_connector = SAPConnector()
        connection, cursor, _ = sap_connector.get_hana_connection()
        
        # Database/Schema name
        db_name = "TEST_DB_28072025"
        
        # Extract date part for comparison (YYYY-MM-DD)
        last_log_date = last_log_str[:10] if len(last_log_str) >= 10 else "2024-01-01"
        
        # Extract time part from last_log_str and convert to integer (HHMMSS format)
        # Example: "2025-07-28 10:49:23" -> 104923
        last_log_time_int = 0
        if len(last_log_str) >= 19:
            try:
                time_part = last_log_str[11:19]  # Extract "HH:MI:SS"
                last_log_time_int = int(time_part.replace(':', ''))  # Convert to HHMMSS integer
            except:
                last_log_time_int = 0
        
        # Step 3: Build SQL query for SAP HANA
        # Note: UpdateTS and CreateTS are stored as integers representing time in HHMMSS format
        # Simplified query to avoid numeric overflow - select raw values and format in Python
        query = f"""
            SELECT 
                c."WhsName" AS "Plant Name",
                a."CardName" AS "Vendor Name",
                TO_VARCHAR(a."DocDate", 'YYYY-MM-DD') AS "Purchased Date",
                b."Quantity" AS "Raw_Milk in Ltr",
                (CASE 
                    WHEN b."U_SNF" IS NOT NULL THEN TO_VARCHAR(b."U_SNF")
                    WHEN b."U_SNFPrcnt" IS NOT NULL THEN TO_VARCHAR(b."U_SNFPrcnt")
                    ELSE NULL
                END) AS "SNF",
                COALESCE(
                    TO_VARCHAR(b."U_FAT"),
                    TO_VARCHAR(b."U_Fatprcnt")
                ) AS "FAT",
                TO_VARCHAR(b."U_TS_Value") AS "TS Value",
                b."Price" AS "Unit Price",
                a."CreateDate" AS "CreateDate_Raw",
                a."CreateTS" AS "CreateTS_Raw",
                a."UpdateDate" AS "UpdateDate_Raw",
                a."UpdateTS" AS "UpdateTS_Raw",
                a."DocEntry",
                a."DocNum"
            FROM {db_name}.OPDN a
            INNER JOIN {db_name}.PDN1 b ON a."DocEntry" = b."DocEntry"
            INNER JOIN {db_name}.OWHS c ON c."WhsCode" = b."WhsCode"
            WHERE 
                b."ItemCode" = 'RMND0027'
                AND a."UpdateTS" < 240000
                AND a."CreateTS" < 240000
                AND (
                    a."UpdateDate" > TO_DATE('{last_log_date}', 'YYYY-MM-DD')
                    OR (a."UpdateDate" = TO_DATE('{last_log_date}', 'YYYY-MM-DD') 
                        AND a."UpdateTS" > {last_log_time_int})
                    OR a."CreateDate" > TO_DATE('{last_log_date}', 'YYYY-MM-DD')
                    OR (a."CreateDate" = TO_DATE('{last_log_date}', 'YYYY-MM-DD') 
                        AND a."CreateTS" > {last_log_time_int})
                )
            ORDER BY a."DocDate" DESC, b."WhsCode"
        """
        
        frappe.logger().info(f"Executing SAP Milk query with last_log: {last_log_str}")
        frappe.logger().info(f"Query: {query[:500]}...")  # Log first 500 chars of query for debugging
        
        # Step 4: Execute query and fetch data
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries and format datetime values
            records = []
            for row in rows:
                record_dict = dict(zip(columns, row))
                
                # Format datetime values from raw fields to avoid SQL numeric overflow
                # CreateDate and CreateTS
                created_dt_str = None
                if record_dict.get("CreateDate_Raw") and record_dict.get("CreateTS_Raw"):
                    try:
                        create_ts = record_dict.get("CreateTS_Raw")
                        if create_ts and create_ts < 240000:
                            # Format date
                            create_date = record_dict.get("CreateDate_Raw")
                            if isinstance(create_date, datetime.datetime):
                                date_str = create_date.strftime('%Y-%m-%d')
                            else:
                                date_str = str(create_date)[:10]
                            
                            # Format time (HHMMSS -> HH:MM:SS)
                            ts_str = str(create_ts).zfill(6)  # Pad to 6 digits
                            time_str = f"{ts_str[0:2]}:{ts_str[2:4]}:{ts_str[4:6]}"
                            
                            created_dt_str = f"{date_str} {time_str}"
                    except Exception as e:
                        frappe.logger().warning(f"Error formatting Created_DateTime: {str(e)}")
                
                # UpdateDate and UpdateTS
                updated_dt_str = None
                if record_dict.get("UpdateDate_Raw") and record_dict.get("UpdateTS_Raw"):
                    try:
                        update_ts = record_dict.get("UpdateTS_Raw")
                        if update_ts and update_ts < 240000:
                            # Format date
                            update_date = record_dict.get("UpdateDate_Raw")
                            if isinstance(update_date, datetime.datetime):
                                date_str = update_date.strftime('%Y-%m-%d')
                            else:
                                date_str = str(update_date)[:10]
                            
                            # Format time (HHMMSS -> HH:MM:SS)
                            ts_str = str(update_ts).zfill(6)  # Pad to 6 digits
                            time_str = f"{ts_str[0:2]}:{ts_str[2:4]}:{ts_str[4:6]}"
                            
                            updated_dt_str = f"{date_str} {time_str}"
                    except Exception as e:
                        frappe.logger().warning(f"Error formatting Updated_DateTime: {str(e)}")
                
                # Add formatted datetime fields
                record_dict["Created_DateTime"] = created_dt_str
                record_dict["Updated_DateTime"] = updated_dt_str
                
                # Remove raw fields
                record_dict.pop("CreateDate_Raw", None)
                record_dict.pop("CreateTS_Raw", None)
                record_dict.pop("UpdateDate_Raw", None)
                record_dict.pop("UpdateTS_Raw", None)
                
                records.append(record_dict)
            
            frappe.logger().info(f"Fetched {len(records)} records from SAP")
            
            # Debug: Log first few records to see datetime values
            if records:
                frappe.logger().info(f"Sample record - Created: {records[0].get('Created_DateTime')}, Updated: {records[0].get('Updated_DateTime')}")
        except Exception as query_error:
            error_str = str(query_error)
            frappe.logger().error(f"Query execution error: {error_str}")
            # Create a short, descriptive title (max 140 chars)
            if "numeric overflow" in error_str.lower():
                error_title = "SAP Milk Sync: Numeric Overflow Error"
            else:
                # Extract error code if present (e.g., "(314," -> "Error 314")
                error_title = "SAP Milk Sync Query Error"
                if error_str.startswith("(") and "," in error_str:
                    try:
                        error_code = error_str.split(",")[0].strip("(")
                        error_title = f"SAP Milk Sync: Error {error_code}"
                    except:
                        pass
            
            # Ensure title doesn't exceed 140 chars (should already be short, but double-check)
            if len(error_title) > 140:
                error_title = error_title[:137] + "..."
            
            full_error_msg = f"SQL Query Error: {error_str}\nQuery: {query[:1000]}..."
            frappe.log_error(full_error_msg, error_title)
            raise
        
        # Step 5: Insert data into SAP Milk Data doctype
        # Check for duplicates based on DocEntry and DocNum combination
        inserted_count = 0
        skipped_count = 0
        latest_datetime_str = None  # Track latest datetime as string for comparison
        
        for row in records:
            try:
                # Get datetime strings (already in YYYY-MM-DD HH:MI:SS format from query)
                created_dt_str = row.get("Created_DateTime") or ""
                updated_dt_str = row.get("Updated_DateTime") or ""
                
                # Parse for storage in Frappe (as datetime objects)
                created_dt = None
                updated_dt = None
                
                if created_dt_str:
                    try:
                        created_dt = get_datetime(created_dt_str)
                    except:
                        pass
                
                if updated_dt_str:
                    try:
                        updated_dt = get_datetime(updated_dt_str)
                    except:
                        pass
                
                # Note: We don't track latest_datetime_str from records anymore
                # We'll use current datetime for last_saved_date instead
                
                # Check if record already exists (based on DocEntry - unique field)
                doc_entry = row.get("DocEntry")
                doc_num = row.get("DocNum")
                
                # Check for existing record with same DocEntry
                existing = frappe.db.exists("SAP Milk Data", {"doc_entry": doc_entry})
                
                if existing:
                    # Update existing record if it's newer (compare datetime strings)
                    existing_doc = frappe.get_doc("SAP Milk Data", existing)
                    existing_updated_str = ""
                    if existing_doc.updated_datetime:
                        existing_updated_str = existing_doc.updated_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    elif existing_doc.created_datetime:
                        existing_updated_str = existing_doc.created_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    
                    new_updated_str = updated_dt_str or created_dt_str
                    
                    if new_updated_str and (not existing_updated_str or new_updated_str > existing_updated_str):
                        # Update the existing record
                        existing_doc.plant_name = row.get("Plant Name") or ""
                        existing_doc.vendor_name = row.get("Vendor Name") or ""
                        existing_doc.purchased_date = row.get("Purchased Date")
                        existing_doc.raw_milk_in_ltr = row.get("Raw_Milk in Ltr") or 0
                        existing_doc.snf = row.get("SNF") or ""
                        existing_doc.fat = row.get("FAT") or ""
                        existing_doc.ts_value = row.get("TS Value") or ""
                        existing_doc.unit_price = row.get("Unit Price") or 0
                        existing_doc.created_datetime = created_dt
                        existing_doc.updated_datetime = updated_dt
                        existing_doc.save(ignore_permissions=True)
                        inserted_count += 1
                    else:
                        skipped_count += 1
                    continue
                
                # Create new document
                doc = frappe.get_doc({
                    "doctype": "SAP Milk Data",
                    "plant_name": row.get("Plant Name") or "",
                    "vendor_name": row.get("Vendor Name") or "",
                    "purchased_date": row.get("Purchased Date"),
                    "raw_milk_in_ltr": row.get("Raw_Milk in Ltr") or 0,
                    "snf": row.get("SNF") or "",
                    "fat": row.get("FAT") or "",
                    "ts_value": row.get("TS Value") or "",
                    "unit_price": row.get("Unit Price") or 0,
                    "created_datetime": created_dt,
                    "updated_datetime": updated_dt,
                    "doc_entry": doc_entry,
                    "doc_num": doc_num
                })
                
                doc.insert(ignore_permissions=True)
                inserted_count += 1
                
            except Exception as e:
                frappe.log_error(
                    f"Error inserting SAP Milk Data record: {str(e)}\nRow data: {row}",
                    "SAP Milk Sync Error"
                )
                continue
        
        # Step 6: Update SAP Milk Log with current datetime (when sync completed)
        # This tracks when the sync happened, not the latest record's datetime
        # Always update, even if no records were inserted (to track last check time)
        # Use current datetime for sync timestamp
        current_sync_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get or create SAP Milk Log document (use first document or create new one)
        log_name = frappe.db.get_value("SAP Milk Log", {}, "name")
        
        if log_name:
            # Update existing document with current sync datetime
            frappe.db.set_value("SAP Milk Log", log_name, "last_saved_date", current_sync_datetime)
        else:
            # Create new document
            log_doc = frappe.get_doc({
                "doctype": "SAP Milk Log",
                "last_saved_date": current_sync_datetime
            })
            log_doc.insert(ignore_permissions=True)
        
        frappe.db.commit()
        frappe.logger().info(f"Updated SAP Milk Log with last_saved_date (sync time): {current_sync_datetime}")
        
        # Close connection
        sap_connector.close_hana_connection(connection, cursor)
        
        # Return message with sync timestamp
        message = f"{inserted_count} records processed successfully"
        if skipped_count > 0:
            message += f" ({skipped_count} skipped - already up to date)"
        
        # Get the current sync time for the message
        sync_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if inserted_count > 0:
            message += f". Sync completed at: {sync_time}"
        else:
            message += f". No new records found. Last checked at: {sync_time}"
        
        return message
        
    except ImportError as e:
        error_msg = f"SAP HANA driver not found: {str(e)}"
        # Truncate error message for title (max 140 chars)
        error_title = "SAP Milk Sync: Import Error"
        if len(error_msg) <= 120:
            error_title = f"SAP Milk Sync: {error_msg}"
        else:
            error_title = f"SAP Milk Sync: {error_msg[:117]}..."
        frappe.log_error(error_msg, error_title)
        try:
            if connection and cursor and sap_connector:
                sap_connector.close_hana_connection(connection, cursor)
        except:
            pass
        return f"Error: {error_msg}"
        
    except Exception as e:
        error_msg = f"An error occurred while fetching SAP milk data: {str(e)}"
        # Truncate error message for title (max 140 chars)
        error_title = "SAP Milk Sync Error"
        if len(error_msg) <= 120:
            error_title = f"SAP Milk Sync: {error_msg}"
        else:
            error_title = f"SAP Milk Sync: {error_msg[:117]}..."
        frappe.log_error(error_msg, error_title)
        try:
            if connection and cursor and sap_connector:
                sap_connector.close_hana_connection(connection, cursor)
        except:
            pass
        return f"Error: {error_msg}"

