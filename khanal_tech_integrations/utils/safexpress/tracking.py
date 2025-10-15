import requests
import json
import frappe
from frappe.utils import add_to_date, now, get_datetime, now_datetime
import re

from khanal_tech_integrations.utils.sap import AuthenticateSAPB1

headersList = {
                "Accept": "*/*",
                "User-Agent": "Khanal Tech",
                "Content-Type": "application/json" 
            }

@frappe.whitelist()
def Update_Tracking_by_INV():
    Today = frappe.utils.nowdate()
    FilterDate = add_to_date(Today,days=-20)
    delivery_notes = frappe.db.get_list('SAP Delivery Notes',filters={ 'tracking_id': ['=', ''], 'transporter_name': ['=', ''] ,'updated': ['>', FilterDate]},pluck="docentry" )
    print(len(delivery_notes),'lenght of deliverynotes')
    for Docentry in delivery_notes:
        getDoc = frappe.db.get_list('SAP AR Invoice', filters={'ref_delivery_note': Docentry} ,pluck='docnum')
        # print(getDoc)
        if len(getDoc) == 0:
            # The list is empty, do something
            pass
        else:
            # The list is not empty, do something
            # print('else check safe',getDoc)
            for doc in getDoc:
                print(doc)
                url = "https://webs.safexpress.com:8443/SafexWaybillTracking/webresources/tracking/all"

                # prefixes = ["KAIN24", "AR2024", "HRIN24", "MHIN24","KAIN23", "AR2023", "HRIN23", "MHIN23","Manual"]
                prefixes = ["KAIN24", "AR2024", "HRIN24", "MHIN24","KAIN23", "AR2023", "HRIN23", "MHIN23"]
                for prefix in prefixes:
                    # if prefix == "Manual":
                    #     formatted_doc = str(doc)
                    # else:
                    formatted_doc = f"{prefix}/{doc}"
                    payload = {
                        "docNo": formatted_doc,
                        "docType": "INV"
                    }

                    response = requests.post(url, headers=headersList, json=payload,verify=False)
                    # print(response)
                    if response.status_code == 200:
                        result = response.json()
                        
                        # print(f"Success for prefix {prefix}: {result}")
                        if 'waybill' in result['shipment']:
                            DNList      = frappe.get_doc('SAP Delivery Notes' , Docentry )
                            # print(DNList)
                            waybill = result['shipment']['waybill']
                            print(waybill)
                            DNList.transporter_name     = "Safexpress"
                            DNList.tracking_id          = waybill
                            DNList.shipping_details     = result
                            print(result,'result')
                            # DNList.delivery_status      = result['shipment']['status']
                            # # print(result)
                            if 'shipment' in result and 'status' in result['shipment']:
                                DNList.delivery_status = result['shipment']['status']
                                DNList.save()
                            else:
                                DNList.delivery_status = 'Error'
                            DNList.save()
                            frappe.db.commit() #
                            logistics_detail_PATCH(Docentry=Docentry,TrackingNo=result['shipment']['waybill'])
                    else:
                        pass
                        print(f"Failed for prefix {prefix}: {response.content}")

    return None

def logistics_detail_PATCH(Docentry=None,TrackingNo=None):
    # print('logistics_detail_PATCH')
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    Url                     = doc_settings.sap_b1_url+"DeliveryNotes({Docentry})"
    reqUrl_modified         = Url.format(Docentry=Docentry)        
    payload = json.dumps({  "U_TN": "Safexpress",   "U_TrackingNo": TrackingNo,})
    
    session             = AuthenticateSAPB1()
    response = session.request("PATCH", reqUrl_modified, headers=headersList, data=payload,verify=False)
    print(response,'response')
    # print(response.text)
    return 'DN Patched'








@frappe.whitelist()   
def Update_Tracking_by_WayBill():
    delivery_notes = frappe.db.get_list('SAP Delivery Notes',filters={ 'delivery_status': ['=', ''], 'delivery_status': ['!=', 'DELIVERED'],'transporter_name':['=', 'Safexpress'] } ,pluck="docentry")
    print(len(delivery_notes),'lenght')
    for Docentry in delivery_notes:
        print(Docentry,'Docentry')
        doc=frappe.get_doc("SAP Delivery Notes",Docentry)
        # print(doc.tracking_id,'tracking_id')
        url = "https://webs.safexpress.com:8443/SafexWaybillTracking/webresources/tracking/all"
        payload = json.dumps({
        "docNo": doc.tracking_id,
        "docType": "WB"
        })
        headers = {
        'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        # print(response.status_code,'status_code')
        result = response.json()
        # print(result)
        if result['shipment']['message'] != 'Invalid Request' :
            doc.shipping_details            = result
            # print(doc,'lhkgjhfgdgchjkl;')
            if result['shipment']['result'] == 'success' :
                # print(result['shipment']['result'])
                doc.shipping_details         = result
                doc.delivery_status           = result['shipment']['status']
                # print(result)
            else:
                # print('Data not found')
                doc.delivery_status             ='Data Not Found'

            doc.save()
            frappe.db.commit() #
            print(doc,'saved')    # print(response.status_code,'status_code')
    pass





# bench --site dev.localhost execute khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_INV
# bench --site dev.localhost execute khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_WayBill
# bench --site khanaltech.com execute khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_INV
# bench --site khanaltech.com execute  --args "{ '30' }"  khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_INV

# bench --site khanaltech.com execute khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_WayBill
# bench --site khanaltech.com execute khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_WayBill