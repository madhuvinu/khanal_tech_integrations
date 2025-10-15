import requests
import json
import frappe
from frappe.utils import add_to_date, now, get_datetime, now_datetime
from datetime import datetime, timedelta
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
from collections import ChainMap
import collections
from khanal_tech_integrations.utils.DN_Creation_Unicommerce import DNsendmail,delivery_from_orderlist_batch
from khanal_tech_integrations.utils.unicommerce import AuthenticateUniware

headersList = {
                    "Accept": "*/*",
                    "User-Agent": "Khanal Tech",
                    "Content-Type": "application/json" 
                }


# utils/unicommerceFile/DeliveryNotes.py

    
def Unicommerce_Dispatch_INV():
    Today = frappe.utils.nowdate()
    Today = datetime.strptime(Today, '%Y-%m-%d').date()

    # Calculate the start date by subtracting 7 days
    startD = Today - timedelta(days=2)

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
                    'HALFCIRCLEFULL',
                    'MEESHO'
                    ]
    for single_channel in Channel_list:
        missing_Qty = False
        if missing_Qty:
            pass
        else:
            Push_result = Channel_delivery_Creation_Dispatched(Channel_Name=single_channel,startDate=startD_formatted,endDate=Today_formatted)
            title = 'Ar Invoice Creation for '+str(single_channel) + 'From Date :'+ str(startD_formatted) + 'To Date :'+ str(Today_formatted) +''
            DNsendmail(DICT = Push_result,Title=title)
    return Push_result

###############################################################################################################################################
#! bench --site khanaltech.com execute khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Unicommerce_Dispatch_INV

#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BOM7','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BOM5','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BLR7','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BLR8','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BLR5','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_DEL4','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_DEL5','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site dev.localhost execute --args  "('AMAZON_FBA_IN_CJB1','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_MAA4','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('Amazon_IN_API','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('CRED','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site dev.localhost execute --args  "('FLIPKART','01-06-2025','30-06-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('DOGSEE_SITE_IN','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('HN_SITE_IN','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('ONDC_NSTORE','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('HALFCIRCLEFULL','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('MEESHO','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched
#! bench --site khanaltech.com execute --args  "('Snapdeal','01-05-2025','31-05-2025' )"  khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Channel_delivery_Creation_Dispatched

@frappe.whitelist()
def Channel_delivery_Creation_Dispatched(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list 
    send to create a single invoice out of it.
    """
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    channel_id = Channel_Name
    end_date = end_date.replace(hour=23, minute=59, second=59)


    # print(max_end_date,'max_end_date')
    print(start_date,'start_date')
    print(end_date,'end_date')
    origin_state = 'MH' if Channel_Name in ["AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7"] else 'KA' if Channel_Name in ["AMAZON_FBA_IN_BLR5", "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8", "Amazon_IN_API"] else 'HR' if Channel_Name in ["AMAZON_FBA_IN_DEL4", "AMAZON_FBA_IN_DEL5"] else 'TN' if Channel_Name in ["AMAZON_FBA_IN_CJB1","AMAZON_FBA_IN_MAA4"] else 'KA'

    Channel_CustomerCode_mapping = {
                                    'C02574':['Snapdeal'],
                                    'C03564':['AMAZON_FBA_IN_BOM7', 'AMAZON_FBA_IN_BOM5'],
                                    'C03575':['AMAZON_FBA_IN_BLR5', 'AMAZON_FBA_IN_BLR7', 'AMAZON_FBA_IN_BLR8', 'Amazon_IN_API'],
                                    'C03579':['AMAZON_FBA_IN_DEL4', 'AMAZON_FBA_IN_DEL5'],
                                    'C03596':['AMAZON_FBA_IN_CJB1', 'AMAZON_FBA_IN_MAA4'],
                                    'C03358':['CRED'],  
                                    'C03121':['FLIPKART'],
                                    'C00623':['DOGSEE_SITE_IN'],
                                    'C01026':['HN_SITE_IN'],
                                    'C03494':['ONDC_NSTORE'],
                                    'C03412':['HALFCIRCLEFULL'],
                                    'C03586':['MEESHO']
                                    }

    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                        'status': ('in',['COMPLETE']), 
                                        'channel_name'      : Channel_Name,
                                        'state'             :origin_state,
                                        'sap_ar_invoice_docentry':"",
                                        'displayorderdatetime'     :('between',[start_date,end_date]),
                                        #'shipment_status'   : ('in',['DISPATCHED',  'DELIVERED','SHIPPED','RETURN_EXPECTED',"RETURNED","" ]), 
                                        },
                                        pluck='name') 
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                        'status'   : ('in',['COMPLETE']), 
                                        'channel_name'      : Channel_Name,
                                        'state'             :('not in',[origin_state]),
                                        'sap_ar_invoice_docentry':"",
                                        'displayorderdatetime'     :('between',[start_date,end_date]),
                                        #'shipment_status'   : ('in',['DISPATCHED',  'DELIVERED','SHIPPED','RETURN_EXPECTED',"RETURNED","" ]), 
                                        },
                                        pluck='name') 
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                                        'status': ('in',['COMPLETE',]), 
                                                        'channel_name': Channel_Name,
                                                        'state':origin_state,
                                                        'sap_ar_invoice_docentry':""
                                                    },
                                            pluck='name') 
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                                        'status': ('in',['COMPLETE',]), 
                                                        'channel_name': Channel_Name,
                                                        'state':('not in',[origin_state]),
                                                        'sap_ar_invoice_docentry':""
                                                    },
                                            pluck='name')    
    channel_to_customer_code = {channel: customer_code 
                            for customer_code, channels in Channel_CustomerCode_mapping.items() 
                            for channel in channels}
    # Get the customer code for the channel
    CustomerCode_from_channel = channel_to_customer_code.get(channel_id)
    
    Summary_Dict = [ {'Order_Type':'SGST Orders', 'No of Orders': len(SGST_orders),'AR Invoice Docnum':None },
                     {'Order_Type':'IGST Orders', 'No of Orders': len(IGST_orders),'AR Invoice Docnum':None } ]
    
    # LOCAL ORDERS
    if len(SGST_orders)>0 :
        bill_to_code = 'B2C SGST ADD'
        print ('SGST_orders : ',len(SGST_orders))
        print('PUSHING SGST ORDERS')
        
        
        Invoice_response = delivery_from_orderlist_batch(CustomerCode_from_channel,channel_id,SGST_orders,bill_to_code,startDate,endDate)
        print(str(Invoice_response)[:40])
        if Invoice_response and Invoice_response.get('DocNum') is not None:
            print("* * * * * * * * * * * SGST_orders - Invoice_response['DocNum']   ",Invoice_response['DocNum'])
            Summary_Dict[0]['AR Invoice Docnum'] = Invoice_response['DocNum']
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)
                order_doc.sap_ar_invoice_docentry = Invoice_response['DocEntry']
                order_doc.sap_ar_invoice_docnum = Invoice_response['DocNum']
                order_doc.save()
                order_doc.save()
                frappe.db.commit()
        elif Invoice_response.get('error') is not None:
            Summary_Dict[0]['AR Invoice Docnum'] = Invoice_response['error']
            print ('ERROR',Invoice_response)

    #Outside state orders
    if len(IGST_orders)>0:
        bill_to_code = 'B2C IGST ADD'
        print('PUSHING IGST ORDERS')
     
        Invoice_response = delivery_from_orderlist_batch(CustomerCode_from_channel,channel_id,IGST_orders,bill_to_code,startDate,endDate)
        print(str(Invoice_response)[:40])
        if Invoice_response.get('DocNum') is not None:
            print("* * * * * * * * * * * IGST_orders - Invoice_response['DocNum']   ",Invoice_response['DocNum'])
            Summary_Dict[1]['AR Invoice Docnum'] = Invoice_response['DocNum']
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc) 
                order_doc.sap_ar_invoice_docentry = Invoice_response['DocEntry']
                order_doc.sap_ar_invoice_docnum = Invoice_response['DocNum']
                order_doc.save()
                order_doc.save()
                frappe.db.commit()
        elif Invoice_response.get('error') is not None:
            Summary_Dict[1]['AR Invoice Docnum'] = Invoice_response['error']
            print ('ERROR',Invoice_response)
    return Summary_Dict