import frappe
import json
import requests
from datetime import datetime, timedelta
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
from khanal_tech_integrations.utils.Unicommerce_Automation.unicommerceFile.unicommerce import get_single_order
from frappe.query_builder import DocType
from frappe.query_builder.functions import Lower
from datetime import datetime

headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json" 
    }

@frappe.whitelist()
def CreateCreditFromINV(startDate=None, endDate=None, channel_Name=None): 
    if not (startDate and endDate and channel_Name):
        frappe.throw("startDate, endDate, and channel_Name are required")

    try:
        start_date = datetime.strptime(startDate, "%d-%m-%Y")
        end_date = datetime.strptime(endDate, "%d-%m-%Y")
        end_date = end_date.replace(hour=23, minute=59, second=59)
    except Exception as e:
        frappe.throw(f"Invalid date format. Use DD-MM-YYYY. Error: {str(e)}")

    print(start_date, 'start_date')
    print(end_date, 'end_date')
    print(channel_Name, 'channel_Name')

    Orders = DocType("Unicommerce Orders")

    ARLIST = (
        frappe.qb.from_(Orders)
        .select(Orders.sap_ar_invoice_docentry) 
        .where(
            (Orders.status == "COMPLETE")
            & (Orders.sap_ar_invoice_docentry.isnotnull())
            & (Orders.sap_ar_creditnote_docentry.isnull())
            & (Orders.channel_name == channel_Name)
            & (Orders.displayorderdatetime.between(start_date, end_date))
            & (Orders.return_code.isnotnull())
            & (Lower(Orders.shipment_status).isin(["RETURNED", "RETURN_EXPECTED"]))
        )
        .run(pluck=True)
    )

    unique_ARLIST = list(set(ARLIST))
    print(unique_ARLIST)
    
    for SingleARDocEntry in unique_ARLIST:
        CreditNoteDocEntery = Create_CreditNote(SingleARDocEntry, channel_Name)

        # Fetch all matching Unicommerce Order names
        getFilterValue = frappe.db.get_list(
            'Unicommerce Orders',
            filters={'sap_ar_invoice_docentry': SingleARDocEntry},
            pluck='name'  # 'name' is the primary key of DocTypes in Frappe
        )

        # Update 'sap_ar_creditnote_docentry' field for all matching orders
        if CreditNoteDocEntery:
            ValueNeededToAdd = CreditNoteDocEntery
            for order in getFilterValue:
                frappe.db.set_value('Unicommerce Orders', order, 'sap_ar_creditnote_docentry', ValueNeededToAdd)
        else:
            print(f"No CreditNote created for {SingleARDocEntry}")

    # Commit the changes to the database
    frappe.db.commit()
    return None

    return unique_ARLIST  


@frappe.whitelist()
def GetSingleARDeatils(AR_DocEntry=None):
    SAPsession =  AuthenticateSAPB1()
    doc_settings    = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"Invoices({DocEntry})"
    modfified_Url = invoice_Url.format(DocEntry=AR_DocEntry)   
    response        = SAPsession.request("GET", modfified_Url,   headers=headersList,verify=False)
    AR_Dict  = dict(response.json())
    return AR_Dict


def extract_batch_numbers(order_details, item_code,LineNum,U_Order): 
    LineNum=int(LineNum)+1
    batch_numbers = []
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
    
def Create_CreditNote(SingleInvoice,channel_Name):
    INVDetails = GetSingleARDeatils(SingleInvoice)
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
   
    ArCreditNote_InvoicePayload['DocumentLines'] = []

    for line_item in INVDetails['DocumentLines']:        
        if line_item['U_Order']:
            orderr_id = line_item['U_Order']
            UnicommerceOrderDetails = get_single_order(orderr_id)  # Assuming line_item['U_Order'] holds the OrderID
            status = UnicommerceOrderDetails.get('status', '').strip().upper()
            if status != 'COMPLETE':
                #print(orderr_id, 'is not complete')
                continue
            statuses = [pkg.get('status') for pkg in UnicommerceOrderDetails.get('shippingPackages', [])]
            if 'RETURNED' not in statuses and 'RETURN_EXPECTED' not in statuses:
                #print(orderr_id, 'is not returned or return expected')
                continue
            BatchNumbers = extract_batch_numbers(UnicommerceOrderDetails, line_item['ItemCode'],line_item['LineNum'],line_item['U_Order'])
            #print(BatchNumbers,'BatchNumbers')
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
        print(json.dumps(ArCreditNote_InvoicePayload), 'ArCreditNote_InvoicePayload')

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



#! bench --site dev.localhost execute khanal_tech_integrations.utils.unicommerceFile.CreditNote2.GetSingleARDeatils --args='{"40278"}'
#! bench --site dev.localhost execute khanal_tech_integrations.utils.unicommerceFile.CreditNote2.CreateCreditFromINV --args='( "01-09-2025", "30-09-2025", "MEESHO")'