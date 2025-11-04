import frappe
import json
from datetime import datetime, timedelta
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
from khanal_tech_integrations.utils.Unicommerce_Automation.unicommerceFile.unicommerce import get_single_order
import requests
from frappe.utils import add_to_date, now, get_datetime, now_datetime

headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json" 
    }
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_BOM5' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_BOM7' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_BLR7' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_BLR8' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_BLR5' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_BLR5' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_DEL4' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_DEL5' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','Amazon_IN_API' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','FLIPKART' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site dev.localhost execute --args  "('01-06-2025','30-06-2025','CRED' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','DOGSEE_SITE_IN' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','HN_SITE_IN' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_MAA4' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','AMAZON_FBA_IN_CJB1' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV

#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','Snapdeal' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','ONDC_NSTORE' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','HALFCIRCLEFULL' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#! bench --site khanaltech.com execute --args  "('01-06-2025','30-06-2025','MEESHO' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.CreateCreditFromINV
#  bench --site khanaltech.com execute   khanal_tech_integrations.utils.unicommerceFile.CreditNote.sample
#* bench --site khanaltech.com execute  khanal_tech_integrations.utils.unicommerceFile.CreditNote.Unicommerce_CreditNote_FromINN

@frappe.whitelist()  
def Unicommerce_CreditNote_FromINN():
    Today = frappe.utils.nowdate()
    # startD = add_to_date(Today,days=-7)
    Today = datetime.strptime(Today, '%Y-%m-%d').date()

    # Calculate the start date by subtracting 7 days
    startD = Today - timedelta(days=7)

    # Format the dates in the desired format
    Today_formatted = Today.strftime('%d-%m-%Y')
    startD_formatted = startD.strftime('%d-%m-%Y')

    print("Today:", Today_formatted)
    print("startD:", startD_formatted)
     
    Channel_list = [
            'Snapdeal',
            'Amazon_IN_API',
            'AMAZON_FBA_IN_BOM5',
            'AMAZON_FBA_IN_BOM7',
            'AMAZON_FBA_IN_BLR5',
            'AMAZON_FBA_IN_BLR7',
            'AMAZON_FBA_IN_BLR8',
            'AMAZON_FBA_IN_DEL4',
            'AMAZON_FBA_IN_DEL5',
            'AMAZON_FBA_IN_CJB1',
            'AMAZON_FBA_IN_MAA4',
            'CRED',
            'FLIPKART',
            'DOGSEE_SITE_IN',
            'HN_SITE_IN',
            'ONDC_NSTORE',
            'MEESHO',
            'HALFCIRCLEFULL'
        ]
    for single_channel in Channel_list:
        Push_result = CreateCreditFromINV(startDate=startD_formatted,endDate=Today_formatted,channel_Name=single_channel)
       
    return None

@frappe.whitelist()
def CreateCreditFromINV(startDate=None,endDate=None,channel_Name=None): 
    print(startDate,'start_date',endDate,'end_date',channel_Name,'channel_Name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'start_date')
    print(end_date,'end_date')
    print(channel_Name,'channel_Name')
    ARLIST = frappe.db.get_list('Unicommerce Orders', 
            filters={
               
                'sap_ar_invoice_docentry':['!=',''],
                'sap_ar_creditnote_docentry': ['=', ''],
                'channel_name'      : channel_Name,
                'displayorderdatetime'     :('between',[start_date,end_date]),
                'return_code':['!=',''],
                'shipment_status'   : ['in', ['RETURNED','RETURN_EXPECTED']],
                },
            pluck='sap_ar_invoice_docentry'
        )
    print(ARLIST)
    unique_ARLIST = list(set(ARLIST))
    print(unique_ARLIST)
    for SingleARDocEntry in unique_ARLIST:
        CreditNoteDocEntery=Create_CreditNote(SingleARDocEntry,channel_Name)
        getFilterValue = frappe.db.get_list(
        'Unicommerce Orders', 
        filters={'sap_ar_invoice_docentry': SingleARDocEntry},
        pluck='name'
        )  # Assuming 'name' is the primary key of 'Unicommerce Orders'
        if CreditNoteDocEntery:
            ValueNeededToAdd = CreditNoteDocEntery
        else:
            #ValueNeededToAdd = 'No Return'
            print('')
        
        for order in getFilterValue:
            frappe.db.set_value('Unicommerce Orders', order, 'sap_ar_creditnote_docentry', ValueNeededToAdd)

        frappe.db.commit()  
    return None

@frappe.whitelist()
def GetSingleARDeatils(AR_DocEntry=None):
    SAPsession =  AuthenticateSAPB1()
    doc_settings    = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"Invoices({DocEntry})"
    modfified_Url = invoice_Url.format(DocEntry=AR_DocEntry)   
    response        = SAPsession.request("GET", modfified_Url,   headers=headersList,verify=False)
    AR_Dict  = dict(response.json())
    return AR_Dict

@frappe.whitelist()
def Create_CreditNote(SingleInvoice,channel_Name):
    print(SingleInvoice,'SingleInvoice', channel_Name,'channel_Name')
    INVDetails = GetSingleARDeatils(SingleInvoice)
    # print(INVDetails)
    series_mapping = {
                        "Snapdeal"          : '448',
                        "Amazon_IN_API"     : '448',
                        "CRED"              : '448',
                        "FLIPKART"          : '448',
                        "DOGSEE_SITE_IN"    : '448',
                        "HN_SITE_IN"        : '448', 
                        "ONDC_NSTORE"       : '448', 
                        "AMAZON_FBA_IN_BOM5": '450', 
                        "AMAZON_FBA_IN_BOM7": '450',
                        "AMAZON_FBA_IN_BLR5": '448',
                        "AMAZON_FBA_IN_BLR7": '448',
                        "AMAZON_FBA_IN_BLR8": '448',
                        "AMAZON_FBA_IN_DEL4": '449',
                        "AMAZON_FBA_IN_DEL5": '449',
                        "AMAZON_FBA_IN_CJB1": '464',
                        "AMAZON_FBA_IN_MAA4": '464',
                        "HALFCIRCLEFULL"    : '448',
                        "MEESHO"            : '448'
                    }

    ArCreditNote_InvoicePayload = {
        'Series'                            : series_mapping.get(channel_Name, '448'),  # Default to '412' if channel not found 
        'DocDate'                           : INVDetails.get('DocDate'),
        'DocDueDate'                        : INVDetails.get('DocDueDate'),
        'CardCode'                          : INVDetails.get('CardCode'),
        'Comments'                          : INVDetails.get('Comments'),
        'PayToCode'                         : INVDetails.get('PayToCode'),
        'ShipToCode'                        : INVDetails.get('ShipToCode'),
        'U_BillingFrom'                     : INVDetails.get('U_BillingFrom'),
        'U_BillTo'                          : INVDetails.get('U_BillTo'),
        'UseBillToAddrToDetermineTax'       : INVDetails.get('UseBillToAddrToDetermineTax'),
        'U_Pod_Link'                        : INVDetails.get('U_Pod_Link'),
        'U_TN'                              : INVDetails.get('U_TN'),
        'U_TrackingNo'                      : INVDetails.get('U_TrackingNo'),
        'U_ShippingDate'                    : INVDetails.get('U_ShippingDate'),
    }
    BatchNumbers = []
    # Create a new list for DocumentLines with only the specified fields
    ArCreditNote_InvoicePayload['DocumentLines'] = []

    for line_item in INVDetails['DocumentLines']:        
        if line_item['U_Order']:

            UnicommerceOrderDetails = get_single_order(line_item['U_Order'])  # Assuming line_item['U_Order'] holds the OrderID
            BatchNumbers = extract_batch_numbers(UnicommerceOrderDetails, line_item['ItemCode'],line_item['LineNum'],line_item['U_Order'])
            print(BatchNumbers,'BatchNumbers')
            if BatchNumbers:
                

                filtered_line_item = {
                    'LineNum'            : line_item['LineNum'],
                    'ItemCode'           : line_item['ItemCode'],
                    'ItemDescription'    : line_item['ItemDescription'],
                    'Quantity'           : line_item['Quantity'],
                    'ShipDate'           : line_item['ShipDate'],
                    'Price'              : line_item['Price'],
                    'PriceAfterVAT'      : line_item['PriceAfterVAT'],
                    'Currency'           : line_item['Currency'],
                    'TaxCode'            : line_item['TaxCode'],
                    'WarehouseCode'      : 'EC-QA',
                    'TreeType'           : line_item['TreeType'],
                    'AccountCode'        : line_item['AccountCode'],
                    'BaseType'           : 13,
                    'BaseEntry'          : INVDetails['DocEntry'],
                    'BaseLine'           : line_item['LineNum'],
                    'U_Order'            : line_item['U_Order'],
                    'U_City'             : line_item['U_City'],
                    'U_State'            : line_item['U_State'],
                    'U_OrderedOn'        : line_item['U_OrderedOn'],
                    'WithoutInventoryMovement': 'tNO',  # Add this line
                    'BatchNumbers': BatchNumbers,  # Add this line
                }

                ArCreditNote_InvoicePayload['DocumentLines'].append(filtered_line_item)

    if ArCreditNote_InvoicePayload['DocumentLines']:
        print(ArCreditNote_InvoicePayload, 'ArCreditNote_InvoicePayload')

        SAPsession = AuthenticateSAPB1()
        doc_settings = frappe.get_doc('SAP Settings')
        creditnote_url = doc_settings.sap_b1_url + "CreditNotes"

        try:
            response = SAPsession.request("POST", creditnote_url, data=json.dumps(ArCreditNote_InvoicePayload), headers=headersList, verify=False)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
            
            response_data = response.json()
            DocEntry = response_data["DocEntry"]
            DocNum = response_data["DocNum"]
            print(f'\n\n{DocEntry} is The DocEntry in SAP, {DocNum} is The DocNum in SAP\n\n')
            getFilterValue = frappe.db.get_list(
            'Unicommerce Orders', 
            filters={'sap_ar_invoice_docentry': SingleInvoice},
            pluck='name'
            )  # Assuming 'name' is the primary key of 'Unicommerce Orders'
            for order in getFilterValue:
                frappe.db.set_value('Unicommerce Orders', order, 'sap_ar_creditnote_docentry', response_data["DocEntry"])
        
            frappe.db.commit()
            return DocEntry

        except requests.exceptions.HTTPError as http_err:
            response_data = response.json()
            error_value = response_data.get('error', {}).get('message', {}).get('value', str(http_err))
            print(f'\n\nError: {error_value}\n\n')
        
        except Exception as err:
            print('try if ')
            print(f'\n\nUnexpected error: {err}\n\n')
    return None

def extract_batch_numbers(order_details, item_code,LineNum,U_Order): 
    LineNum=int(LineNum)+1
    batch_numbers = []
    print(U_Order,'Order ID')
    if order_details.get('returns'):

        
        for return_item in order_details['returns']:
           
            for item in return_item['returnItems']:
                if item['itemSku'] == item_code:
                    # print('matching',uniqueCode)
                    doc = frappe.get_doc('Unicommerce Orders', U_Order)
                    for line_item in doc.line_items:
                        uniquevalueinSAP=f'{item_code}-{LineNum}'
                        uniquevalueinFrappe=f'{line_item.itemsku}-{line_item.delivery_linenum}'
                        batch_numbers.append({
                            'BatchNumber': line_item.vendorbatchnumber,
                            'Quantity': line_item.quantity,
                            'ItemCode': item_code
                        })
                        return batch_numbers
    else:
        return []    
    
# !bench --site khanaltech.com execute --args  "('01-06-2024','30-06-2024','HN_SITE_IN' )"  khanal_tech_integrations.utils.unicommerceFile.CreditNote.ChangeCNasEmpty
@frappe.whitelist()
def ChangeCNasEmpty(startDate=None,endDate=None,channel_Name=None,iD=None,creditnote=None): #
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'start_date')
    print(end_date,'end_date')
    print(channel_Name,'channel_Name')
    ARLIST = frappe.db.get_list('Unicommerce Orders', 
            filters={               
                'sap_ar_creditnote_docentry': 'No Return',
                'channel_name'      : channel_Name,
                'displayorderdatetime'     :('between',[start_date,end_date]),
            },
            pluck='name'
        )
    unique_ARLIST = list(set(ARLIST))
    print(unique_ARLIST)
    for name in unique_ARLIST:
        frappe.db.set_value('Unicommerce Orders', name, 'sap_ar_creditnote_docentry', '')

    frappe.db.commit()

    return 'saved Done'

def CancelB2CInvoicesByPostingDate(FromDate, ToDate, series_number):
    doc_settings = frappe.get_doc('SAP Settings')
    SAPsession = AuthenticateSAPB1()
    headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json"
    }
    
    skip = 0
    page_size = 100
    total_cancelled = 0
    print(f"\nStarting cancellation for series {series_number} from {FromDate} to {ToDate}")

    while True:
        cancel_get_url = (
             f"{doc_settings.sap_b1_url}Invoices"
             f"?$select=DocEntry,DocNum,DocType,DocDate,Series"
             f"&$filter=DocDate ge '{FromDate}' and DocDate le '{ToDate}' and Series eq {series_number}"
             f"&$orderby=DocEntry"
             f"&$top={page_size}&$skip={skip}"
         )

        response = SAPsession.request("GET", cancel_get_url, headers=headersList, verify=False)
        if response.status_code != 200:
            print(f"Failed to fetch invoices: {response.status_code} - {response.text}")
            break
        response.status_code == 200            
        invoices = response.json().get("value", [])
        if not invoices:
            break  # Exit loop if no more invoices are found
        print(f"Found {len(invoices)} invoices in Series {series_number} from {FromDate} to {ToDate}")

        for invoice in invoices:
                doc_entry = invoice.get("DocEntry")
                doc_num = invoice.get("DocNum")
                print(f"Processing Invoice DocEntry: {doc_entry}, DocNum: {doc_num}")
                
                cancel_url = f"{doc_settings.sap_b1_url}Invoices({doc_entry})/Cancel"
                cancel_response = SAPsession.request("POST", cancel_url, headers=headersList, verify=False)
                
                if cancel_response.status_code == 204:
                    total_cancelled += 1
                    print(f"Cancelled Invoice {doc_num} (DocEntry: {doc_entry})")
                else:
                    print(f"Failed to cancel Invoice {doc_num} (DocEntry: {doc_entry}): {cancel_response.status_code} - {cancel_response.text}")
        skip += len(invoices)
    print(f"Total Cancelled Invoices: {total_cancelled} for Series {series_number} from {FromDate} to {ToDate}")
            


#! bench --site dev.localhost execute --args "('2025-06-01T00:00:00','2025-06-30T23:59:59','461')" khanal_tech_integrations.utils.unicommerceFile.CreditNote.CancelB2CInvoicesByPostingDate


def CancelInvoiceByDocEntry(DocEntry):
    doc_settings = frappe.get_doc('SAP Settings')
    SAPsession = AuthenticateSAPB1()
    headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json"
    }

    cancel_get_url = f"{doc_settings.sap_b1_url}Invoices({DocEntry})/Cancel"

    response = SAPsession.request("POST", cancel_get_url, headers=headersList, verify=False)
    print(response)
    if response.status_code == 204:
        print(f"Invoice with DocEntry {DocEntry} has been successfully canceled.")
    else:
        print(f"Failed to cancel invoice with DocEntry {DocEntry}: {response.status_code} - {response.text}")

#! bench --site dev.localhost execute --args "{'38520'}" khanal_tech_integrations.utils.unicommerceFile.CreditNote.CancelInvoiceByDocEntry
