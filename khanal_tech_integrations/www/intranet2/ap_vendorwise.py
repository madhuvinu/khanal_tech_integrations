import frappe
import frappe.utils
from khanal_tech_integrations.utils.banking.AP_invoices import get_AP_invoices
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
from khanal_tech_integrations.utils.cashfree.benefeciary import get_cashfree_status
from khanal_tech_integrations.utils.razorpay.contacts import get_banklist_Vendor

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
        
    # vendor_code = 'V00525'
    vendor_code = frappe.local.request.args.get("ap_invoice")
    doc_settings = frappe.get_doc('SAP Settings')
    # Count_url = doc_settings.sap_b1_url+"PurchaseInvoices?$apply=aggregate(DocEntry with countdistinct as CountDistinct)"
    Count_url = doc_settings.sap_b1_url+"PurchaseInvoices?$apply=filter(CardCode eq '{cardcode}')/aggregate(DocEntry with countdistinct as CountDistinct)"
    modfified_Url = Count_url.format(cardcode=vendor_code)

    AP_invoice_count_response      = session.request("GET", modfified_Url, data=empty_payload,  headers=headersList,verify=False)
        
    AP_Invoice_count = dict(AP_invoice_count_response.json())
    print(AP_Invoice_count)
    
    AP_invoice_list = []
    i=current_page
    if int(current_page)>0:
        i = int(current_page)-1
    print (i)

    # reqUrl          = doc_settings.sap_b1_url+"PurchaseInvoices?$orderby=DocDate desc&$skip=" + str(20*i)
    reqUrl          = doc_settings.sap_b1_url+"PurchaseInvoices?$filter=CardCode eq '{cardcode}' &$orderby=DocDate desc&$skip=" +str(20*i)
    VendorSpeicific_url = reqUrl.format(cardcode=vendor_code)
    response        = session.request("GET", VendorSpeicific_url, data=empty_payload,  headers=headersList,verify=False)
    resp_json = response.json()['value'] #List full of dictionaries
    
    # print (resp_json)
    
    if resp_json: 
        for item in resp_json:
            keysss = ['DocDate', 'DocEntry','DocNum','CardCode','CardName','NumAtCard','DocTotal', 'DocumentStatus' ,'DocDueDate','U_TN','PaidToDate'] #U_TM
            dict2 = {x:item[x] for x in keysss }
            # dict2['CAshfreeActivity'] = "--"
            # print('U_TN = ', dict2['U_TN'])
            # if dict2['U_TN'] != None:
            #     Cashfree_Status = get_cashfree_status(str(dict2['DocEntry']) + str(dict2['CardCode']))
            #     dict2['CAshfreeActivity'] = Cashfree_Status
            # else:
            #     pass

            AP_invoice_list.append(dict2)

    else:
        AP_invoice_list = ''
    # print(AP_invoice_list,'%%') 
    # return redirect(url_for('login'))
    #return AP_invoice_listS
    # AP_invoice_list += twenty_response
    #vendorlist = frappe.db.get_list('Razorpay Fund Account',filters={'name_cardcode': vendor_code },fields=['bank_name', 'fa_id','account_code'])
    vendorlist = get_banklist_Vendor(vendorcode =  vendor_code ) 
    context={
        "ap_invoice_list":AP_invoice_list,
        "vendorlist":vendorlist
        # "ap_invoice_count":The_AP_Count,#AP_Invoice_count['value']
    }
    # print(context.ap_invoice_count)
    for item in vendorlist:
        print(item['BankCode'],"---bankcode")
    return context