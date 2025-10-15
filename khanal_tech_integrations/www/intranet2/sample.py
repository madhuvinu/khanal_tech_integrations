import frappe
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
headersList = {
                "Accept": "*/*",
                "User-Agent": "Khanal Tech",
                "Content-Type": "application/json" 
            }

def get_context(context):
    session = AuthenticateSAPB1()
    empty_payload = ''
    doc_settings = frappe.get_doc('SAP Settings')
    entry_url = doc_settings.sap_b1_url+"Orders?$filter=startswith(U_SubConPONo, 'PZ') &$orderby=DocDate desc"
    responceneed = session.request("GET", entry_url, data=empty_payload,  headers=headersList,verify=False)
    resp_json           = responceneed.json()['value']
    
    AP_invoice_list=[]
    if resp_json: 
        for item in resp_json:
            keysss  = ['DocDate', 'DocEntry','DocNum','CardCode','CardName','NumAtCard'] #U_TM
            ListItem   = {values:item[values] for values in keysss }
       
            AP_invoice_list.append(ListItem)

    # print(AP_invoice_list)  

    context={
        "AP_invoice_list":AP_invoice_list,
    }      
    return context