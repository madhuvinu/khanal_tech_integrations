import frappe
import json
from datetime import datetime, timedelta
from khanal_tech_integrations.utils.hana_connection_pool import HANAConnectionPool
from hdbcli import dbapi

def fetch_and_convert_docentry(docentry):
    """
    Fetch UpdateTS and CreateTS from OPDN for a given DocEntry
    and convert them to human-readable timestamps.
    """
    try:
        # Connect to HANA using the connection pool
        pool = HANAConnectionPool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        # Use the correct database schema TEST_DB_28072025
        query = f'SELECT "DocEntry", "UpdateTS", "CreateTS" FROM TEST_DB_28072025.OPDN WHERE "DocEntry" = {docentry}'
        print(f"Executing query: {query}")
        
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row:
            docentry, update_ts, create_ts = row
            
            # Assuming TS is in seconds from 1970-01-01
            base = datetime(1970, 1, 1)
            update_dt = base + timedelta(seconds=update_ts)
            create_dt = base + timedelta(seconds=create_ts)
            
            print(f"DocEntry: {docentry}")
            print(f"UpdateTS: {update_ts} (epoch) -> {update_dt} (converted)")
            print(f"CreateTS: {create_ts} (epoch) -> {create_dt} (converted)")
            
            return {
                'docentry': docentry,
                'update_ts_epoch': update_ts,
                'update_ts': update_dt,
                'create_ts_epoch': create_ts,
                'create_ts': create_dt
            }
        else:
            print("No record found")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        if 'pool' in locals():
            pool.close_all()

def fetch_opdn_with_joins(docentry):
    """
    Fetch OPDN data with JOINs to PDN1 and OWHS tables
    Similar to the query: FROM TEST_DB_28072025.OPDN a INNER JOIN TEST_DB_28072025.PDN1 b ON a."DocEntry" = b."DocEntry" INNER JOIN TEST_DB_28072025.OWHS c ON c."WhsCode" = b."WhsCode"
    """
    try:
        # Connect to HANA using the connection pool
        pool = HANAConnectionPool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        # Complex query with JOINs
        query = f'''
        SELECT 
            a."DocEntry", 
            a."UpdateTS", 
            a."CreateTS",
            b."WhsCode",
            c."WhsName"
        FROM TEST_DB_28072025.OPDN a
        INNER JOIN TEST_DB_28072025.PDN1 b ON a."DocEntry" = b."DocEntry"
        INNER JOIN TEST_DB_28072025.OWHS c ON c."WhsCode" = b."WhsCode"
        WHERE a."DocEntry" = {docentry}
        '''
        
        print(f"Executing complex query: {query}")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            results = []
            for row in rows:
                docentry, update_ts, create_ts, whs_code, whs_name = row
                
                # Convert timestamps
                base = datetime(1970, 1, 1)
                update_dt = base + timedelta(seconds=update_ts)
                create_dt = base + timedelta(seconds=create_ts)
                
                result = {
                    'docentry': docentry,
                    'update_ts_epoch': update_ts,
                    'update_ts': update_dt,
                    'create_ts_epoch': create_ts,
                    'create_ts': create_dt,
                    'whs_code': whs_code,
                    'whs_name': whs_name
                }
                results.append(result)
                
                print(f"DocEntry: {docentry}, UpdateTS: {update_ts} (epoch) -> {update_dt} (converted), CreateTS: {create_ts} (epoch) -> {create_dt} (converted), Warehouse: {whs_name}")
            
            return results
        else:
            print("No records found")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        if 'pool' in locals():
            pool.close_all()

# Example usage
if __name__ == "__main__":
    print("Testing simple query...")
    result = fetch_and_convert_docentry(14475)
    if result:
        print("Successfully fetched and converted timestamps")
    
    print("\nTesting complex query with JOINs...")
    results = fetch_opdn_with_joins(14475)
    if results:
        print(f"Successfully fetched {len(results)} records with warehouse information")

