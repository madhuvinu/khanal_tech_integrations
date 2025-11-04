import frappe
import json

from frappe.utils import add_to_date, now, get_datetime, now_datetime
from datetime import datetime, timedelta
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
from collections import ChainMap
import collections
from khanal_tech_integrations.utils.DN_Creation_Unicommerce import DNsendmail,delivery_from_orderlist_batch
from khanal_tech_integrations.utils.Unicommerce_Automation.unicommerceFile.unicommerce import AuthenticateUniware

headersList = {
                    "Accept": "*/*",
                    "User-Agent": "Khanal Tech",
                    "Content-Type": "application/json" 
                }

headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json" 
    }

# ! function Used For Creating INV from perticular Channel_Name with startDate & endDate

#* bench --site dev.localhost execute --args  "('26-06-2024','26-06-2024','HN_SITE_IN' )"  khanal_tech_integrations.utils.unicommerceFile.Invoive.CreateInvoceFromDN


# #* bench --site khanaltech.com execute --args  "('01-07-2024','31-07-2024','Amazon_IN_API' )"  khanal_tech_integrations.utils.unicommerceFile.Invoive.CreateInvoceFromDN

@frappe.whitelist()
def CreateInvoceFromDN(startDate=None,endDate=None,channel_Name=None): #
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'start_date')
    print(end_date,'end_date')
    print(channel_Name,'channel_Name')
    # DNLIST = frappe.db.get_list('Unicommerce Orders', 
    #         filters={
    #             'sap_delivery_docentry': ['!=', ''],
    #             'sap_ar_invoice_docentry':['=',''],
    #             # 'displayorderdatetime': ['between', [start_date, end_date]]
    #             # 'displayorderdatetime'     :('between',[startDate,endDate]),
    #         },
    #         pluck='sap_delivery_docentry'
    #     )
    DNLIST = frappe.db.get_list('Unicommerce Orders', 
            filters={
                'sap_delivery_docnum': ['!=', ''],
                'sap_ar_invoice_docentry':['=',''],
                'channel_name'      : channel_Name,
                'displayorderdatetime'     :('between',[start_date,end_date]),

                # 'displayorderdatetime': ['between', [start_date, end_date]]
                # 'displayorderdatetime'     :('between',[startDate,endDate]),
            },
            pluck='sap_delivery_docnum'
        )
    # print(DNLIST)
    # order_doc.sap_delivery_docentry 
    unique_DNLIST = list(set(DNLIST))
    print(unique_DNLIST)
    for SingleDNDocEntry in unique_DNLIST:
        ArinvoiceDocEntry=Create_ArInvoive(SingleDNDocEntry)
        # getFiltervalue = frappe.db.get_list('Unicommerce Orders', 
        # filters={'sap_delivery_docentry': SingleDNDocEntry},
        # pluck='name')  # Assuming 'name' is the primary key of 'Unicommerce Orders'
        getFiltervalue = frappe.db.get_list('Unicommerce Orders', 
        filters={'sap_delivery_docnum': SingleDNDocEntry},
        pluck='name')  # Assuming 'name' is the primary key of 'Unicommerce Orders'
    
        for order in getFiltervalue:
            frappe.db.set_value('Unicommerce Orders', order, 'sap_ar_invoice_docentry', ArinvoiceDocEntry)
    return None




# @frappe.whitelist()
# def sample(): #
    
#     DNLIST = frappe.db.get_list('Unicommerce Orders', 
#             filters={
#                 'sap_delivery_docnum': 10060,
                
#             },
#             pluck='name'
#         )
#     for i in DNLIST:
#         frappe.db.set_value('Unicommerce Orders', i, 'sap_ar_invoice_docentry', '')
#         frappe.db.set_value('Unicommerce Orders', i, 'sap_delivery_docentry', '')
#         frappe.db.set_value('Unicommerce Orders', i, 'sap_delivery_docnum', '')
#         frappe.db.set_value('Unicommerce Orders', i, 'sap_ar_creditnote_docentry', '')
#     print(DNLIST)



  
#! bench --site dev.localhost execute  khanal_tech_integrations.utils.unicommerceFile.Invoive.sample


@frappe.whitelist()
def GetSingleDNDeatils(DNDocNum=None):
    SAPsession =  AuthenticateSAPB1()
    doc_settings    = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes?$select=DocEntry, DocNum&$filter=DocNum eq {DocNum} and Series eq 318 and DocumentStatus eq 'bost_Open'"
    modfified_Url = invoice_Url.format(DocNum=DNDocNum)   
    response        = SAPsession.request("GET", modfified_Url,   headers=headersList,verify=False)
    Dn_Dict  = dict(response.json())
    # print(Dlsn_Dict,'Dn_Dict')
    try:
        if Dn_Dict['value']:
            for Single_DN in Dn_Dict['value']:
                getSingle_Url = doc_settings.sap_b1_url+"DeliveryNotes({DocEntry})"
                modfified_getSingle_Url = getSingle_Url.format(DocEntry=Single_DN['DocEntry'])   
                responsevalue        = SAPsession.request("GET", modfified_getSingle_Url,   headers=headersList,verify=False)
                Single_Dict         = dict(responsevalue.json())
                print(Single_Dict['DocEntry'],'.....is the DocEntry')
                return Single_Dict
        else:
            print('No open delivery notes found with the given DocNum. with series DN2024')


    except Exception as e:
        print (e)
        return e


# @frappe.whitelist()
# def GetSingleDNDeatils(DN_DocEntry=None):
#     SAPsession =  AuthenticateSAPB1()
#     doc_settings    = frappe.get_doc('SAP Settings')
#     invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes({DocEntry})"
#     modfified_Url = invoice_Url.format(DocEntry=DN_DocEntry)   
#     response        = SAPsession.request("GET", modfified_Url,   headers=headersList,verify=False)
#     Single_Dict  = dict(response.json())
#     return Single_Dict

   

# bench --site dev.localhost execute --args  "{'10050'}"   khanal_tech_integrations.utils.unicommerceFile.DN_Invoive.Create_ArInvoive

@frappe.whitelist()
def Create_ArInvoive(SingleInvoice):
    DnDetails = GetSingleDNDeatils(SingleInvoice)
    if DnDetails:
        # Create a new dictionary with only the specified fields
        Ar_InvoicePayload = {
            'DocDate'                           : DnDetails.get('DocDate'),
            'DocDueDate'                        : DnDetails.get('DocDueDate'),
            'CardCode'                          : DnDetails.get('CardCode'),
            'Comments'                          : DnDetails.get('Comments'),
            'PayToCode'                         : DnDetails.get('PayToCode'),
            'ShipToCode'                        : DnDetails.get('ShipToCode'),
            'U_BillingFrom'                     : DnDetails.get('U_BillingFrom'),
            'U_BillTo'                          : DnDetails.get('U_BillTo'),
            'UseBillToAddrToDetermineTax'       : DnDetails.get('UseBillToAddrToDetermineTax'),
            'U_Pod_Link'                        : DnDetails.get('U_Pod_Link'),
            'U_TN'                              : DnDetails.get('U_TN'),
            'U_TrackingNo'                      : DnDetails.get('U_TrackingNo'),
            'U_ShippingDate'                    : DnDetails.get('U_ShippingDate'),

        }

        # Create a new list for DocumentLines with only the specified fields
        Ar_InvoicePayload['DocumentLines'] = []
        for line_item in DnDetails['DocumentLines']:
            PriceDetails=getpriceDetails(line_item['U_Order'],line_item['ItemCode'])
            print(PriceDetails,'PriceDetails')
            filtered_line_item = {
                'LineNum'            : line_item['LineNum'],
                'ItemCode'           : line_item['ItemCode'],
                'ItemDescription'    : line_item['ItemDescription'],
                'Quantity'           : line_item['Quantity'],
                'ShipDate'           : line_item['ShipDate'],
                'Price'              : PriceDetails,
                # 'PriceAfterVAT'      : line_item['PriceAfterVAT'],
                'Currency'           : line_item['Currency'],
                'TaxCode'            : line_item['TaxCode'],
                'WarehouseCode'      : line_item['WarehouseCode'],
                'TreeType'           : line_item['TreeType'],
                'AccountCode'        : line_item['AccountCode'],
                'BaseType'           : 15,
                'BaseEntry'          : DnDetails['DocEntry'],
                'BaseLine'           : line_item['LineNum'],
                'U_Order'            : line_item['U_Order'],
                'U_City'             : line_item['U_City'],
                'U_State'            : line_item['U_State'],
                'U_OrderedOn'        : line_item['U_OrderedOn'],
                'BatchNumbers'       :line_item['BatchNumbers'],
                

            }
            Ar_InvoicePayload['DocumentLines'].append(filtered_line_item)
        
       
    
        # Authenticate to SAP B1
        SAPsession =  AuthenticateSAPB1()
        doc_settings = frappe.get_doc('SAP Settings')
        invoice_url = doc_settings.sap_b1_url + "Invoices"

        print(Ar_InvoicePayload,'Ar_InvoicePayload')
        # # Send POST request to create item
        response = SAPsession.request("POST", invoice_url, data=json.dumps(Ar_InvoicePayload), headers=headersList, verify=False)
        
        # Check response status
        if response.status_code == 400:
            # If error, print error message
            response_data = json.loads(response.text)
            error_value = response_data['error']['message']['value']
            print('\n\n',error_value,'\n\n')
        else:
            # If successful, print success message
            response_data = json.loads(response.text)
            # print('\n\n\n',response_data["ItemCode"],'response_data')
            DocEntry = response_data["DocEntry"]
            DocNum = response_data["DocNum"]
            
            
            print('\n\n', f'{DocEntry} is The DocEntry in SAP, {DocNum} is The DocNum in SAP\n\n')
            return response_data["DocEntry"]

           


def getpriceDetails(U_Order,ItemCode):
    # doc = frappe.get_doc('Unicommerce Orders', U_Order)float(itemss.selling_price)-float(itemss.totalintegratedgst)
    # Retrieve selling_price and totalintegratedgst for the given U_Order and ItemCode
    list_of_Unicommerce = frappe.db.get_list(
        'Unicommerce Orders',
        filters={'uniware_id': U_Order, 'itemsku': ItemCode},
        fields=['line_items.selling_price', 'line_items.totalintegratedgst']
    )
    if list_of_Unicommerce:
        item = list_of_Unicommerce[0]
        selling_price = float(item['selling_price'])
        totalintegratedgst = float(item['totalintegratedgst'])
        # print(selling_price - totalintegratedgst,selling_price,totalintegratedgst)
        return selling_price - totalintegratedgst
    else:
        return 0  






