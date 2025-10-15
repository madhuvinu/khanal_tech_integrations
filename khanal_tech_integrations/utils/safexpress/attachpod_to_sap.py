
import frappe
import json
import requests
import base64
import time
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
from khanal_tech_integrations.utils.safexpress.auth import AuthenticateSafexpress
from frappe.utils.file_manager import get_file_path
from frappe.utils import file_manager

from frappe.utils import add_to_date
from datetime import datetime  # Added import for datetime

headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json" 
    }


@frappe.whitelist()
def Get_Waybill_in_ArInvoice(Day=4): #
    Today = frappe.utils.nowdate()
    FilterDate = add_to_date(Today,days=-int(Day))
    List_of_INV= frappe.db.get_list('SAP AR Invoice Detail',filters={'series_name': ['in', ["KAIN24","KAIN25" ,"AR2024","AR2025" ,"HRIN24","HRIN25", "MHIN24","MHIN25","KAIN23", "AR2023", "HRIN23", "MHIN23", "Manual"]],'lastupdated_date':['>', FilterDate],'pod_url': ['=', ''],'way_bill_number': ['=', ''] },pluck="docentry" )
    print('lenght of db list is......',len(List_of_INV))
    for Single_Ar in List_of_INV:
        Update_waybill_and_filePath(Single_Ar)

    pass

# @frappe.whitelist()
# def Update_waybill_and_filePath(Single_Ar): #

#     doc=frappe.get_doc('SAP AR Invoice Detail',Single_Ar)
#     if doc.pod_url:
#         print(doc.pod_url,'pod_url Already Present')
#     else:
#         print('No waybill_and_filePath')
#         url = "https://webs.safexpress.com:8443/SafexWaybillTracking/webresources/tracking/all"
       
#         formatted_doc = f"{doc.series_name}/{doc.docnum}"
#         payload = {
#             "docNo": formatted_doc,
#             "docType": "INV"
#         }
#         response = requests.post(url, headers=headersList, json=payload,verify=False)
#         print(response,'Safexpress')
#         if response.status_code == 200:
            
#             result = response.json()
#             # print(result,'\n\n')
#             # print(f"Success for prefix {prefix}: {result}")
#             if 'waybill' in result['shipment']:
#                 # print(result['shipment'],'\n\n')
#                 doc.way_bill_number=result['shipment']['waybill']
#                 doc.save()
#                 frappe.db.commit()
#                 print(result['shipment']['waybill'],'waybill Number')
#                 Get_Single_Pod(Single_Ar)
#                 PATCH_POD_AR_invoice(Single_Ar)
#                 print(doc,'Document has been Saved after Attaching to SAP')
#             else:
#                 # RemovePOD_Link(Single_Ar)
#                 pass
     
#         else:
#             print(response.status_code,'is becauuse of',response.text)

#############################################################################################################################
def Update_waybill_and_filePath(Single_Ar): 
    try:
        doc = frappe.get_doc('SAP AR Invoice Detail', Single_Ar)

        if doc.pod_url:
            print(doc.pod_url, 'POD URL Already Present')
            return  # Exit function if POD already exists

        print('No waybill_and_filePath')

        url = "https://webs.safexpress.com:8443/SafexWaybillTracking/webresources/tracking/all"

        # Prepare possible combinations of series name
        possible_series = [doc.series_name.upper(), doc.series_name.lower()]

        for series in possible_series:
            formatted_doc = f"{series}/{doc.docnum}"
            payload = {
                "docNo": formatted_doc,
                "docType": "INV"
            }

            response = requests.post(url, headers=headersList, json=payload, verify=False)
            print(response, 'Safexpress API Response for', formatted_doc)

            if response.status_code == 200:
                result = response.json()

                if result.get('shipment') and result['shipment'].get('waybill'):
                    doc.way_bill_number = result['shipment']['waybill']
                    doc.save()
                    frappe.db.commit()
                    print(result['shipment']['waybill'], 'Waybill Number Found')

                    # Fetch and format deliveryDate
                    delivery_date_raw = result['shipment'].get('deliveryDate')  # Extract raw delivery date
                    print(delivery_date_raw, 'Raw Delivery Date Found')

                    try:
                        delivery_date_formatted = datetime.strptime(delivery_date_raw, "%d-%b-%Y").strftime("%Y-%m-%d")
                        doc.pod_date = delivery_date_formatted
                        doc.save()
                        frappe.db.commit()
                        print(delivery_date_formatted, 'Formatted Delivery Date Saved')
                    except Exception as e:
                        print(f"Error formatting delivery date: {str(e)}")

                    # Call your other functions after waybill is found
                    Get_Single_Pod(Single_Ar)  # This will execute
                    PATCH_POD_AR_invoice(Single_Ar)
                    print(doc, 'Document has been Saved after Attaching to SAP')
                    break  # Exit loop after success

            else:
                print(response.status_code, 'API Error:', response.text)

    except Exception as e:
        frappe.log_error(f"Error in Update_waybill_and_filePath for {Single_Ar}: {str(e)}")
        print(f"Exception Occurred for {Single_Ar}:", str(e))

#####################################################################################################################



# def Get_Single_Pod(docentry):

#     """Get single pod details
#     """
#     doc=frappe.get_doc('SAP AR Invoice Detail',docentry)
#     safexpress_session = AuthenticateSafexpress()
#     headersList["x-api-key"]     = safexpress_session.api_key
#     headersList['authorization'] = safexpress_session.access_token
#     headersList['Identifier'] = safexpress_session.identifier
#     payload = {}
#     req_url=safexpress_session.pod_url+doc.way_bill_number
#     response = requests.request("GET", req_url, headers=headersList, data=payload)
#     if response.status_code == 200:
#         resp_json = response.json()
#         # Check if 'data' key is present in the response
#         if 'data' in resp_json and resp_json['data'] is not None:
#             base64_string = resp_json['data'].get('base64String')
#             if base64_string is not None and base64_string != "null":
#                 print('base64_string is not none')
#                 content_file = resp_json['data']['base64String']
#                 tiff_data = base64.b64decode(content_file)
#                 timestamp = str(int(time.time()))
#                 file_name = doc.series_name + '_' + doc.docnum + '_' + timestamp+'.tiff'
#                 file_obj = file_manager.save_file(file_name, tiff_data, 'SAP AR Invoice Detail', doc.docentry)
#                 file_path = get_file_path(file_obj.file_url)
#                 last_files_index = file_path.rfind("/files/")
#                 # Extract the substring after the last "/files/"
#                 cleaned_file_path = file_path[last_files_index:]
#                 ar_doc=frappe.get_doc('SAP AR Invoice Detail', doc.docentry)
#                 ar_doc.pod_url = cleaned_file_path
#                 ar_doc.save()
#                 frappe.db.commit()
#                 return cleaned_file_path
#             else:
#                 print((f"No base64_string for {base64_string}"))
#         else:
#             pass
#     else:
#         print(response.status_code,'is becauuse of',response.text)
     




# @frappe.whitelist()
# def PATCH_POD_AR_invoice(docentry): #
#     doc=frappe.get_doc('SAP AR Invoice Detail',docentry)
#     session             = AuthenticateSAPB1()
#     doc_settings = frappe.get_doc('SAP Settings')
#     Url                 = doc_settings.sap_b1_url+"Invoices({inv_docentry})"
#     reqUrl              = Url.format(inv_docentry=doc.docentry)
#     base_url = frappe.utils.get_url()
#     if doc.pod_url is not None:
#         # Perform the desired action here
#         print(base_url+doc.pod_url,'url')
#         payload = json.dumps(
#         { 
#         "U_TN"         :"Safexpress",
#         "U_TrackingNo" : doc.way_bill_number,    
#         "U_Pod_Link"   : base_url+doc.pod_url,
#         })
#         response = session.request("PATCH", reqUrl, headers=headersList, data=payload,verify=False)
#         print(response.text)
#         print(response)
#         return response
#     else:
#         print(doc,'removed waybill because of pod not present')
#         doc.way_bill_number =''
#         doc.save()
#         frappe.db.commit()



def Get_Single_Pod(docentry):
    try:
        doc = frappe.get_doc('SAP AR Invoice Detail', docentry)
        safexpress_session = AuthenticateSafexpress()
        headersList["x-api-key"] = safexpress_session.api_key
        headersList['authorization'] = safexpress_session.access_token
        headersList['Identifier'] = safexpress_session.identifier
        payload = {}
        req_url = safexpress_session.pod_url + doc.way_bill_number
        response = requests.request("GET", req_url, headers=headersList, data=payload)
        print(response,'AuthenticateSafexpress')
        if response.status_code == 200:
            resp_json = response.json()

            # Check if 'data' key is present in the response
            if 'data' in resp_json and resp_json['data'] is not None:
                base64_string = resp_json['data'].get('base64String')
                if base64_string is not None and base64_string != "null":
                    print('base64_string is not none')
                    content_file = resp_json['data']['base64String']
                    tiff_data = base64.b64decode(content_file)
                    timestamp = str(int(time.time()))
                    file_name = doc.series_name + '_' + doc.docnum + '_' + timestamp + '.tiff'

                    # url="https://gmupurbzq9.execute-api.eu-north-1.amazonaws.com/beta/testingbucketsample/"+file_name #!Test
                    url = "https://tg31l9q380.execute-api.us-west-1.amazonaws.com/dev/khanalfoods-fileupload-bucket/" + file_name  #!Live

                    headers = {
                        'Content-Type': 'image/tiff',
                    }
                    if response.status_code == 200:
                        response = requests.put(url, headers=headers, data=tiff_data)
                        ar_doc = frappe.get_doc('SAP AR Invoice Detail', doc.docentry)
                        # File_url='https://testingbucketsample.s3.eu-north-1.amazonaws.com/'+file_name #!Test
                        File_url = 'https://khanalfoods-fileupload-bucket.s3.us-west-1.amazonaws.com/' + file_name  #!Live
                        ar_doc.pod_url = File_url
                        ar_doc.pod_status='Completed'
                        ar_doc.save()
                        frappe.db.commit()
                else:
                    print((f"No base64_string for {base64_string}"))
            else:
                pass
        else:
            print(response.status_code, 'is because of', response.text)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Handle the exception as needed (e.g., log the error or take corrective action)

# Call the function with the appropriate 'docentry'




# def Get_Single_Pod(docentry):

#     """Get single pod details
#     """
#     doc=frappe.get_doc('SAP AR Invoice Detail',docentry)
#     safexpress_session = AuthenticateSafexpress()
#     headersList["x-api-key"]     = safexpress_session.api_key
#     headersList['authorization'] = safexpress_session.access_token
#     headersList['Identifier'] = safexpress_session.identifier
#     payload = {}
#     req_url=safexpress_session.pod_url+doc.way_bill_number
#     response = requests.request("GET", req_url, headers=headersList, data=payload)
#     if response.status_code == 200:
#         resp_json = response.json()
#         # Check if 'data' key is present in the response
#         if 'data' in resp_json and resp_json['data'] is not None:
#             base64_string = resp_json['data'].get('base64String')
#             if base64_string is not None and base64_string != "null":
#                 print('base64_string is not none')
#                 content_file = resp_json['data']['base64String']
#                 tiff_data = base64.b64decode(content_file)
#                 timestamp = str(int(time.time()))
#                 file_name = doc.series_name + '_' + doc.docnum + '_' + timestamp+'.tiff'
                
#                 # url="https://gmupurbzq9.execute-api.eu-north-1.amazonaws.com/beta/testingbucketsample/"+file_name #!Test
#                 url="https://tg31l9q380.execute-api.us-west-1.amazonaws.com/dev/khanalfoods-fileupload-bucket/"+file_name #!Live

                      
#                 headers = {
#                     'Content-Type': 'image/tiff',  
#                 }
#                 if response.status_code == 200:
#                     response = requests.put(url, headers=headers, data=tiff_data)
#                     ar_doc=frappe.get_doc('SAP AR Invoice Detail', doc.docentry)
#                     # File_url='https://testingbucketsample.s3.eu-north-1.amazonaws.com/'+file_name #!Test
#                     File_url= 'https://khanalfoods-fileupload-bucket.s3.us-west-1.amazonaws.com/'+file_name #!Live
#                     ar_doc.pod_url = File_url
#                     ar_doc.save()
#                     frappe.db.commit()
#                     return 
#             else:
#                 print((f"No base64_string for {base64_string}"))
#         else:
#             pass
#     else:
#         print(response.status_code,'is becauuse of',response.text)
     

def RemovePOD_Link(docentry):
    doc = frappe.get_doc('SAP AR Invoice Detail', docentry)
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    Url = doc_settings.sap_b1_url + "Invoices({inv_docentry})"
    reqUrl = Url.format(inv_docentry=doc.docentry)
    try:
        if doc.pod_url is  None:
            # Perform the desired action here
            payload = json.dumps(
                {
                    "U_TN": "",
                    # "TransportationCode": ,
                    "U_TrackingNo": "",
                    "U_Pod_Link": "",
                })
            response = session.request("PATCH", reqUrl, headers=headersList, data=payload, verify=False)
            print(response.text)
            print(response)
            return response
        else:
            print(doc, 'removed waybill because of pod not present')
            doc.way_bill_number = ''
            doc.save()
            frappe.db.commit()
    except Exception as e:
        print(f"An error occurred while processing docentry {docentry}: {str(e)}")



@frappe.whitelist()
def PATCH_POD_AR_invoice(docentry): #
    doc = frappe.get_doc('SAP AR Invoice Detail', docentry)
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    Url = doc_settings.sap_b1_url + "Invoices({inv_docentry})"
    reqUrl = Url.format(inv_docentry=doc.docentry)

    try:
        if doc.pod_url is not None:
            pod_date = str(doc.pod_date)
            
            # Perform the desired action here
            payload = json.dumps(
                {
                    "U_TN": "Safexpress",
                    "TransportationCode": 1,
                    "U_TrackingNo": doc.way_bill_number,
                    "U_Pod_Link": doc.pod_url,
                    "U_POD_DATE": pod_date

                })
            response = session.request("PATCH", reqUrl, headers=headersList, data=payload, verify=False)
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
        print(f"An error occurred while processing docentry {docentry}: {str(e)}")
# bench --site khanaltech.com execute --args "{ '60' }"  khanal_tech_integrations.utils.safexpress.attachpod_to_sap.Get_Waybill_in_ArInvoice

# bench --site harsh.localhost execute --args "{ '71' }"  khanal_tech_integrations.utils.safexpress.attachpod_to_sap.Get_Waybill_in_ArInvoice

# bench --site dev.localhost execute  --args "{ 'vyshali@khanalfoods.com' }" 

# https://testingbucketsample.s3.eu-north-1.amazonaws.com/KAIN22_22349_1692958250.tiff

