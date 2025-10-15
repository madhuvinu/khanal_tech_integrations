import frappe
import logging
import os
import pandas as pd
from frappe.utils import get_site_path, now_datetime
from .utilities import get_email_recipients

logger = logging.getLogger(__name__)

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
