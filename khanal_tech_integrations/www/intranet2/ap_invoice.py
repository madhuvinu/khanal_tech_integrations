import frappe
import frappe.utils
# from khanal_tech_integrations.utils.banking.AP_invoices import get_AP_invoices
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1

headersList = {
                "Accept": "*/*",
                "User-Agent": "Khanal Tech",
                "Content-Type": "application/json" 
            }
########################
def get_context(context):
    session = AuthenticateSAPB1()
    empty_payload = ''
    
    if frappe.local.request.args.get("current_page"):
        current_page = frappe.local.request.args.get("current_page")
    else:
        current_page = 0
    doc_settings = frappe.get_doc('SAP Settings')
    Count_url = doc_settings.sap_b1_url+"PurchaseInvoices?$apply=aggregate(DocEntry with countdistinct as CountDistinct)"

    AP_invoice_count_response      = session.request("GET", Count_url, data=empty_payload,  headers=headersList,verify=False)
        
    AP_Invoice_count = dict(AP_invoice_count_response.json())
    if AP_Invoice_count.get('value') is not None:
        The_AP_Count = AP_Invoice_count['value'][0]['CountDistinct']
    
    
    AP_invoice_list = []
    i=current_page
    if int(current_page)>0:
        i = int(current_page)-1
    print (i)

    reqUrl          = doc_settings.sap_b1_url+"PurchaseInvoices?$orderby=DocDate desc&$skip=" + str(20*i)
    response        = session.request("GET", reqUrl, data=empty_payload,  headers=headersList,verify=False)
    resp_json = response.json()['value'] #List full of dictionaries
    
    for item in resp_json:
        keysss = ['DocDate', 'DocEntry','DocNum','CardCode','CardName','NumAtCard','DocTotal', 'DocumentStatus' ,'DocDueDate',]
        dict2 = {x:item[x] for x in keysss }
        AP_invoice_list.append(dict2)
    print(AP_invoice_list[0]) 
    #return AP_invoice_list
    # AP_invoice_list += twenty_response

    context={
        "ap_invoice_list":AP_invoice_list,
        "ap_invoice_count":The_AP_Count,
    }
    # for item in context['ap_invoice_list'][0]:
    #     print(item)
    return context