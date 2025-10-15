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
    if frappe.local.request.args.get("invoicCarCode"):
        invoicCarCode = frappe.local.request.args.get("invoicCarCode")
    else:
        invoicCarCode = None
    
    doc_settings = frappe.get_doc('SAP Settings')
    # Count_url = doc_settings.sap_b1_url+"PurchaseInvoices?$apply=filter(CardCode eq '{cardcode}')/aggregate(DocEntry with countdistinct as CountDistinct)"
    Count_url = doc_settings.sap_b1_url+"Invoices?$filter=CardCode eq '{cardcode}'"
    modfified_Url = Count_url.format(cardcode=invoicCarCode)   
    AP_invoice      = session.request("GET", modfified_Url, data=empty_payload,  headers=headersList,verify=False)
    resp_json           = AP_invoice.json()['value']
    AP_invoice_list=[]
    if resp_json: 
        for item in resp_json:
            keysss  = ['Address', 'NumAtCard','DocTotal','DocEntry','DocNum','DocDate'] 
            # keysss  = ['DocEntry','DocTotal'] 
            ListItem   = {values:item[values] for values in keysss }
       
            AP_invoice_list.append(ListItem)
    # graphjson=AP_invoice_list.json()   
    print (AP_invoice_list)    
    context={
        "invoices":AP_invoice_list,
    }
    return context



#  //This is JsonData.json
# // {"date_population": [
# // 		{
# // 		  "date": "1941",
# // 		  "population": 406760
# // 		},{
# // 		  "date": "1951",
# // 		  "population": 778977
# // 		},{
# // 		  "date": "1961",
# // 		  "population": 1207000
# // 		}
# // 	]
# // }
