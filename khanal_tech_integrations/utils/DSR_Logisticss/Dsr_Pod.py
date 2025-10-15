import imaplib
from datetime import date
from datetime import datetime
import email
import boto3
import mimetypes
import io
import os
import frappe
import time
import json
from email import policy
from PIL import Image
import requests
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1

headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json" 
    }

def get_s3_settings():
    try:
        s3_settings = frappe.get_single("AWS")
        return {
            "access_key": s3_settings.access_key_id,
            "secret_key": s3_settings.secret_access_key,
            "region": s3_settings.region,
            "bucket": s3_settings.bucket_name_dsr,
            "prefix": s3_settings.folder_prefix or "DSR_Logistics_POD"
        }
    except Exception as e:
        frappe.throw(f"Failed to load S3 Settings: {str(e)}")

def process_dsr_emails():
    print("Starting DSR email processing...")
    try:
        dsr_settings = frappe.get_doc("DSR Settings")
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(dsr_settings.email, dsr_settings.password)
        print("Successfully logged into email.")
    except frappe.DoesNotExistError:
        frappe.throw("DSR Settings not found in Frappe.")
    except imaplib.IMAP4.error as e:
        frappe.throw(f"Email login failed: {str(e)}")
    
    mail.select("inbox")
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split() if status == "OK" else []
    print(f"Found {len(email_ids)} unread emails.")
    
    for email_id in email_ids:
        try:
            print(f"Processing email ID: {email_id.decode()}")
            status, data = mail.fetch(email_id, "(RFC822)")
            if status != "OK" or not data or not isinstance(data[0], tuple):
                print("Error fetching email content.")
                mark_email(mail, email_id, "Error")
                continue
            
            raw_email = data[0][1]
            parsed_results, attachments = parse_email_attachments(raw_email)
            print(f"Parsed {len(parsed_results)} attachments from email.")
            
            if not attachments:
                mark_email(mail, email_id, "No_Attachments")
                continue
            
            for parsed_data in parsed_results:
                print(f"Processing attachment: {parsed_data['filename']}")
                s3_urls = process_and_upload_attachment(parsed_data["filename"], attachments[parsed_data["filename"]])
                
                if s3_urls:
                    parsed_data.update(s3_urls)
                    print(f"Successfully uploaded to S3: {parsed_data['pod_url']}")
                    create_invoice_record(parsed_data)
                else:
                    print("Upload to S3 failed.")
            
            mark_email(mail, email_id, "Processed")
        except Exception as e:
            error_msg = f"Error processing email {email_id.decode()}: {str(e)}"
            print(error_msg)
            frappe.log_error(error_msg)
            notify_manual_intervention(
                subject="DSR POD Processing Failed",
                body=f"<b>Email ID:</b> {email_id.decode()}<br><b>Error:</b> {str(e)}<br>Please check and handle it manually."
            )
            mark_email(mail, email_id, "Error")    
    mail.logout()
    print("Finished processing DSR emails.")

def parse_email_attachments(email_bytes):
    msg = email.message_from_bytes(email_bytes, policy=policy.default)
    results, attachments = [], {}
    
    for part in msg.walk():
        if part.get_content_disposition() in ('attachment', 'inline'):
            filename = part.get_filename()
            if not filename:
                continue            
            filename_without_ext = os.path.splitext(filename)[0]
            parts = filename_without_ext.split('_')
            if len(parts) != 4 or not parts[0].isdigit() or not parts[2].isdigit() or len(parts[3]) != 8:
                continue  

            try:
                date_obj = datetime.strptime(parts[3], "%d%m%Y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue  
            results.append({
                'waybill_number': parts[0],
                'series_name': parts[1],
                'invoice_number': parts[2],
                'pod_date': formatted_date,
                'filename': filename
            })
            attachments[filename] = part.get_payload(decode=True)
    return results, attachments

def process_and_upload_attachment(filename, attachment_data):
    try:
        settings = get_s3_settings()
        timestamp = str(int(time.time()))
        base_filename = filename.replace(' ', '_')
        sanitized_filename = f"{os.path.splitext(base_filename)[0]}_{timestamp}{os.path.splitext(base_filename)[1]}"
        s3_key = f"{settings['prefix']}/{sanitized_filename}"

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings["access_key"],
            aws_secret_access_key=settings["secret_key"],
            region_name=settings["region"]
        )

        file_stream = io.BytesIO(attachment_data)
        content_type = mimetypes.guess_type(sanitized_filename)[0] or "application/octet-stream"
        s3.upload_fileobj(
            Fileobj=file_stream,
            Bucket=settings["bucket"],
            Key=s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        pod_url = f"https://{settings['bucket']}.s3.amazonaws.com/{s3_key}"
        return {"pod_url": pod_url}

    except Exception as e:
        error_msg = f"Error processing {filename}: {str(e)}"
        print(error_msg)
        frappe.log_error(error_msg)
        notify_manual_intervention(
            subject="DSR POD Upload Failed",
            body=f"<b>Filename:</b> {filename}<br><b>Error:</b> {str(e)}<br>Please upload and link it manually."
        )
        return None

def create_invoice_record(parsed_data):
    print(f"Updating SAP AR Invoice Detail for Invoice {parsed_data}...")
    try:
        ar_invoice_record = frappe.get_all(
            "SAP AR Invoice Detail",
            filters={"docnum": parsed_data["invoice_number"]},
            fields=["name","docentry", "docnum", "way_bill_number", "pod_url"]
        )
        if not ar_invoice_record:
            print(f"No matching SAP AR Invoice Detail found for Invoice {parsed_data['invoice_number']}")
            return
        record_name = ar_invoice_record[0]["name"]
        docentry = ar_invoice_record[0]["docentry"]
        
        
        frappe.db.set_value("SAP AR Invoice Detail", record_name, {
            "way_bill_number": parsed_data["waybill_number"],
            "pod_url": parsed_data["pod_url"],
            "transporter_type": "DSR Logistics",
            "shipping_status": "Completed",
            "pod_status": "Completed",
            "pod_date": parsed_data["pod_date"]
        })
        frappe.db.commit()        
        PATCH_POD_AR_invoice(docentry)        
        print(f"Successfully updated SAP AR Invoice Detail {record_name}.")
    
    except Exception as e:
        error_msg = f"Error updating SAP AR Invoice Detail: {str(e)}"
        print(error_msg)
        frappe.log_error(error_msg)
        notify_manual_intervention(
            subject="SAP AR Invoice Update Failed",
            body=f"<b>Invoice Number:</b> {parsed_data['invoice_number']}<br><b>Error:</b> {str(e)}<br>Please update SAP manually."
        )

def mark_email(mail, email_id, label):
    flags = {"Processed": "\\Seen", "Error": "\\Flagged", "No_Attachments": "\\Seen"}
    if label in flags:
        mail.store(email_id, "+FLAGS", flags[label])
        mail.store(email_id, "+X-GM-LABELS", label)

def PATCH_POD_AR_invoice(docentry): 
    doc = frappe.get_doc('SAP AR Invoice Detail', docentry)
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    Url = doc_settings.sap_b1_url + "Invoices({inv_docentry})"
    reqUrl = Url.format(inv_docentry=doc.docentry)
    try:
        if doc.pod_url is not None:

            pod_date_str = doc.pod_date.strftime("%Y-%m-%d") if isinstance(doc.pod_date, date) else doc.pod_date

            payload = json.dumps(
                {
                    "U_TN": "DSR Logistics",
                    "TransportationCode": 7,
                    "U_TrackingNo": doc.way_bill_number,
                    "U_Pod_Link": doc.pod_url,
                    "U_POD_DATE": pod_date_str
                })
            response = session.request("PATCH", reqUrl, headers=headersList, data=payload, verify=False)
            print(f"SAP Update Response: {response.status_code}, {response.text}")
            print(response.text)
            print(response)
            return response
        else:
            print(doc, 'removed waybill because of pod not present')
            doc.way_bill_number = ''
            doc.pod_status = 'Pending'
            doc.save()
            frappe.db.commit()
    except Exception as e:
        error_msg = f"An error occurred while processing docentry {docentry}: {str(e)}"
        print(error_msg)
        frappe.log_error(error_msg)
        notify_manual_intervention(
            subject="SAP POD Patch Failed",
            body=f"<b>DocEntry:</b> {docentry}<br><b>Error:</b> {str(e)}<br>Please patch manually in SAP."
        )

def notify_manual_intervention(subject, body):
    recipient = ["mithun@khanalfoods.com","yogesha@khanalfoods.com"]  # Replace with actual responsible person(s)
    frappe.sendmail(
        recipients=recipient,
        subject=subject,
        message=body
    )
#! bench --site khanaltech.com execute khanal_tech_integrations.utils.DSR_Logistics.Dsr_Pod.process_dsr_emails
