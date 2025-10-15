import requests
import os
import khanal_tech_integrations
import pandas as pd
import json
import frappe
from frappe.utils import get_site_path
from frappe.utils import add_to_date, now, get_datetime, now_datetime
from datetime import datetime, timedelta
from collections import ChainMap
from collections import defaultdict
import collections
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1

headersList = {
                    "Accept": "*/*",
                    "User-Agent": "Khanal Tech",
                    "Content-Type": "application/json" 
                }

def get_GST(origin_state,dest_state,item_code,itemss,ChannelName=None):
    print("Getting GST for item:", item_code,origin_state,dest_state,ChannelName,itemss) 
    session         = AuthenticateSAPB1()
    doc_settings    = frappe.get_doc('SAP Settings')
    reqUrl          = doc_settings.sap_b1_url+"States?$select=Code&$filter=startswith(Country,'IN') and startswith(Name,'"+ origin_state +"')"
    response        = session.request("GET", reqUrl, headers=headersList,verify=False)
    state_code      = dict(response.json())['value'][0]['Code']
    reqUrl          = doc_settings.sap_b1_url+"Items?$select=ItemCode,ItemName,ForeignName,U_TaxRate&$filter=startswith(ItemCode, '" + item_code +"') &$orderby=ItemCode"
    response        = session.request("GET", reqUrl, headers=headersList,verify=False)
    tax_rate        = dict(response.json())['value'][0]['U_TaxRate']
    
    UniIGST         = int(itemss.integratedgstpercentage)   
    UniCGSTASGST    = float(itemss.state_gst_tax_percentage) + float(itemss.central_gst_tax_percentage)
    UniTax          = int(UniCGSTASGST + UniIGST)

    if state_code   == 'KT':
        state_code  = 'KA'
    if state_code   ==dest_state:
        tax_type    = 'CS'
    else:
        tax_type    = 'IG'
    if UniTax == tax_rate:
        print("Tax is same as UnicommerceTax")
    else:
        print("SAP Tax is not same as UnicommerceTax, using UnicommerceTax")
    #     subject = f"TaxCode Mistach for {item_code} in {ChannelName}"
    #     message = f"""
    #     TaxCode for {item_code} in {ChannelName} is not matching with UniTax.\n 
    #     State Code: {state_code}, 
    #     Tax Type: {tax_type}, 
    #     UniTax: {UniTax}, 
    #     Tax Rate: {tax_rate}
    #     Please review the item and correct the tax configuration.
    #     """
    #     frappe.sendmail(
    #         recipients=["yogesha@khanalfoods.com","harsha@khanalfoods.com"],
    #         subject = subject,
    #         message = message
    #     )
    #     print("Email sent to respective person for review.")
    gst_code        = state_code + tax_type + str(int(UniTax))
    print ("GST Code: ", gst_code)

    return gst_code

def create_base_lineitem(item, order_doc, account_code, warehouse_code, origin_state, channel_warehouse_id):
    return {
        "ItemCode": item.itemsku,
        "Quantity": item.quantity,
        "AccountCode": account_code,
        "WarehouseCode": warehouse_code,
        "TaxCode": get_GST(origin_state, order_doc.state, item.itemsku, item, channel_warehouse_id),
        "TaxType": "tt_Yes",
        "TaxLiable": "tYES",
        "TaxTotal": 0.0,
        "U_BuyerName": order_doc.customer_name,
        "U_Order": order_doc.uniware_id,
        "U_SO_ItemCode": item.code,
        "U_City": order_doc.city,
        "U_State": order_doc.state,
        "U_OrderedOn": str(order_doc.created)[:10],
        "U_PINCode": order_doc.pin_code,
        "U_Country": "India"
    }

def get_warehouse_code(channel_warehouse_id):
    mapping = {
        "AMAZON_FBA_IN_BOM5": "AMZ-BOM5",
        "AMAZON_FBA_IN_BOM7": "AMZ-BOM7",
        "AMAZON_FBA_IN_BLR5": "AMZ-BLR5",
        "AMAZON_FBA_IN_BLR7": "AMZ-BLR7",
        "AMAZON_FBA_IN_BLR8": "AMZ-BLR8",
        "AMAZON_FBA_IN_DEL4": "AMZ-DEL4",
        "AMAZON_FBA_IN_DEL5": "AMZ-DEL5",
        "AMAZON_FBA_IN_CJB1": "AMZ-CJB1",
        "AMAZON_FBA_IN_MAA4": "AMZ-MAA4",
    }
    return mapping.get(channel_warehouse_id, "EC-FG")

@frappe.whitelist()
def Channel_delivery_Creation_Dispatched2(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list 
    send to create a single invoice out of it.
    """
    print("new funciton called")
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
        
        
        Invoice_response = delivery_from_orderlist_batch2(CustomerCode_from_channel,channel_id,SGST_orders,bill_to_code,startDate,endDate)
        
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
        Invoice_response = delivery_from_orderlist_batch2(CustomerCode_from_channel,channel_id,IGST_orders,bill_to_code,startDate,endDate)
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


@frappe.whitelist()
def delivery_from_orderlist_batch2(channel,channel_id,completed_orderlist,bill_to_code,startDate,endDate):
    startDate_format = datetime.strptime(startDate, "%d-%m-%Y").strftime("%Y-%m-%d")
    endDate_format = datetime.strptime(endDate, "%d-%m-%Y").strftime("%Y-%m-%d")
    channel_warehouse_id = channel_id
    Channel_Mapping = { 
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
    origin_state = 'Maharashtra' if channel_warehouse_id in ["AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7"] else 'Karnataka' if channel_warehouse_id in ["AMAZON_FBA_IN_BLR5", "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8"] else 'Haryana' if channel_warehouse_id in ["AMAZON_FBA_IN_DEL4", "AMAZON_FBA_IN_DEL5"] else 'Tamil Nadu' if channel_warehouse_id in ["AMAZON_FBA_IN_CJB1", "AMAZON_FBA_IN_MAA4"] else 'Karnataka'
    extra = None
    ##TODO: To update the state code dynamically
    if bill_to_code == 'B2C SGST ADD':
        Bill_to = 'Local'
        account_code = (
                            '41160004' if channel_warehouse_id in ["AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7"] else
                            '41106001' if channel_warehouse_id in ["AMAZON_FBA_IN_BLR5", "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8", "Amazon_IN_API"] else
                            '41160007' if channel_warehouse_id in ["AMAZON_FBA_IN_DEL4", "AMAZON_FBA_IN_DEL5"] else
                            '41160012' if channel_warehouse_id in ["AMAZON_FBA_IN_CJB1", "AMAZON_FBA_IN_MAA4"] else
                            '41106001'
                        )
        extra = 'Intra-state'

    elif bill_to_code == 'B2C IGST ADD':
        Bill_to = 'Central'
        account_code = (
                            '41160005' if channel_warehouse_id in ["AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7"] else
                            '41106002' if channel_warehouse_id in ["AMAZON_FBA_IN_BLR5", "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8", "Amazon_IN_API"] else
                            '41160008' if channel_warehouse_id in ["AMAZON_FBA_IN_DEL4", "AMAZON_FBA_IN_DEL5"] else
                            '41160013' if channel_warehouse_id in ["AMAZON_FBA_IN_CJB1", "AMAZON_FBA_IN_MAA4"] else
                            '41106002'
                        )
        extra = 'Inter-state'

    comment = str(extra) +  "Ecommerce B2C orders for {} from {} to {} Posted Using API from Unicommerce".format(channel_warehouse_id,startDate,endDate)
    print('----------------',channel_warehouse_id,'----------------',)
    # Adding Series for different channels
    series_mapping = {
                        "Snapdeal"          : '412',
                        "Amazon_IN_API"     : '412',
                        "CRED"              : '412',
                        "FLIPKART"          : '412',
                        "DOGSEE_SITE_IN"    : '412',
                        "HN_SITE_IN"        : '412', 
                        "ONDC_NSTORE"       : '412', 
                        "AMAZON_FBA_IN_BOM5": '442', 
                        "AMAZON_FBA_IN_BOM7": '442',
                        "AMAZON_FBA_IN_BLR5": '412',
                        "AMAZON_FBA_IN_BLR7": '412',
                        "AMAZON_FBA_IN_BLR8": '412',
                        "AMAZON_FBA_IN_DEL4": '441',
                        "AMAZON_FBA_IN_DEL5": '441',
                        "AMAZON_FBA_IN_CJB1": '461',
                        "AMAZON_FBA_IN_MAA4": '461',
                        "HALFCIRCLEFULL"    : '412',
                        "MEESHO"            : '412'
                    }
    
    series_number = series_mapping.get(channel_warehouse_id, 372)
    Delivery_payload = { "CardCode"      : str(channel), 
                         "Comments"      : comment,
                         "PayToCode"     :  bill_to_code,
                         "ShipToCode"    :  bill_to_code,                       
                         "DocDate"       : startDate_format, #frappe.utils.nowdate(),# endDate,  #EndDate of the date will be when the doc is posted 
                         "DocDueDate"    : endDate_format,  
                         "U_BillingFrom": 'MH' if channel_warehouse_id in ["AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7"] else 
                                          'KT' if channel_warehouse_id in ["AMAZON_FBA_IN_BLR5", "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8"] else 
                                          'HR' if channel_warehouse_id in ["AMAZON_FBA_IN_DEL4", "AMAZON_FBA_IN_DEL5"] else 
                                          'TN' if channel_warehouse_id in ['AMAZON_FBA_IN_CJB1', 'AMAZON_FBA_IN_MAA4'] else 
                                          'KT',
                         "U_BillTo":  Bill_to,
                         'TransportationCode': 5,
                         "UseBillToAddrToDetermineTax": 'tYES',
                         "Series": series_number,
                         "DocumentLines": []}
    LineNum_Count = 0
    Delivery_payload["DocumentLines"] = []
    for order_id in completed_orderlist:
        processed_codes = set()
        order_doc = frappe.get_doc('Unicommerce Orders', order_id)
        lineitemss = order_doc.line_items 
        warehouse_code = get_warehouse_code(channel_warehouse_id)

        for item in lineitemss:
            if item.get("cancellationreason"):
                print(f"Skipping item {item.itemsku} due to cancellation reason: {item.cancellationreason}")
                continue
            if item.code in processed_codes:
                continue
            if item.bundleskucode:
                #CFG Bundle Parent
                parent_line = {
                    "LineNum": LineNum_Count,
                    "ItemCode": item.bundleskucode,
                    "AccountCode": account_code,
                    "WarehouseCode": warehouse_code,
                    "Quantity": item.quantity,
                    "TaxCode": get_GST(origin_state, order_doc.state, item.bundleskucode, item, channel_warehouse_id),
                    "TaxType": "tt_Yes",
                    "TaxLiable": "tYES",
                    "TaxTotal": 0.0,
                    "UnitPrice": 0.0,
                    "TreeType": "iSalesTree",
                    "U_BuyerName": order_doc.customer_name,
                    "U_Order": order_doc.uniware_id,
                    "U_SO_ItemCode": "",  # optional
                    "U_City": order_doc.city,
                    "U_State": order_doc.state,
                    "U_OrderedOn": str(order_doc.created)[:10],
                    "U_PINCode": order_doc.pin_code,
                    "U_Country": "India",
                    "U_Order_JSON":order_doc.order_json,
                }
                Delivery_payload["DocumentLines"].append(parent_line)
                LineNum_Count += 1

                #Children
                for child_item in lineitemss:
                    if child_item.get("cancellationreason"):
                        print(f"Skipping child item {child_item.itemsku} due to cancellation reason: {child_item.cancellationreason}")
                        continue
                    if child_item.code in processed_codes:
                        continue
                    if child_item.bundleskucode != item.bundleskucode:
                        continue
                    child_line = create_base_lineitem(child_item, order_doc, account_code, warehouse_code, origin_state, channel_warehouse_id)
                    child_line["LineNum"] = LineNum_Count
                    child_line["ItemCode"] = child_item.itemsku
                    child_line["U_SO_ItemCode"] = child_item.code
                    child_line["U_Order_JSON"] = order_doc.order_json
                    child_line["TreeType"] = "iIngredient"  # Non-inventory item
                    child_line["UnitPrice"] = round(float(child_item.sellingpricewithouttaxesanddiscount) - float(child_item.discount), 3)

                    if hasattr(child_item, 'vendorbatchnumber') and child_item.vendorbatchnumber:
                        child_line["BatchNumbers"] = [{
                            "BatchNumber": child_item.vendorbatchnumber,
                            "Quantity": child_item.quantity
                        }]
                    else:
                        return {"Error": f"Child item {child_item.itemsku} is out of stock"}
                    Delivery_payload["DocumentLines"].append(child_line)
                    processed_codes.add(child_item.code)  # Mark child item as processed
                    LineNum_Count += 1
            else:
                if item.get("cancellationreason"):
                    print(f"Skipping item {item.itemsku} due to cancellation reason: {item.cancellationreason}")
                    continue
                # Non-CFG Bundle Item
                if item.code in processed_codes:
                    print(f"Skipping {item.itemsku} as it has already been processed.")
                    continue
                
                item_line = create_base_lineitem(item, order_doc, account_code, warehouse_code, origin_state, channel_warehouse_id)
                item_line["LineNum"] = LineNum_Count
                item_line["ItemCode"] = item.itemsku
                item_line["U_SO_ItemCode"] = item.code
                item_line["U_Order_JSON"] = order_doc.order_json
                item_line["UnitPrice"] = round(float(item.sellingpricewithouttaxesanddiscount) - float(item.discount), 3)

                if hasattr(item, 'vendorbatchnumber') and item.vendorbatchnumber:
                    item_line["BatchNumbers"] = [{
                        "BatchNumber": item.vendorbatchnumber,
                        "Quantity": item.quantity
                    }]
                else:
                    return {"Error": f"Item {item.itemsku} is out of stock"}
                Delivery_payload["DocumentLines"].append(item_line)
                processed_codes.add(item.code)  # Mark item as processed
                LineNum_Count += 1
            order_doc.save()
            frappe.db.commit()
    
                    

            if any(channel_warehouse_id in channels for channels in Channel_Mapping.values()) and int(float(item.shippingcharges)) > 0:
                        tax_percentagee = float(item.shippingchargetaxpercentage)
                        allowed_tax_codes = {0, 5, 12, 18, 24}
                        tax_percentage = int(tax_percentagee) if tax_percentagee in allowed_tax_codes else 0
                        FLKRT_TaxCode = (f"KACS{tax_percentage}" if bill_to_code == "B2C SGST ADD"  else f"KAIG{tax_percentage}")
                        tax_state = 'MH' if channel_warehouse_id in ["AMAZON_FBA_IN_BOM5", "AMAZON_FBA_IN_BOM7"] else 'KA' if channel_warehouse_id in ["AMAZON_FBA_IN_BLR5", "AMAZON_FBA_IN_BLR7", "AMAZON_FBA_IN_BLR8"] else 'HR' if channel_warehouse_id in ["AMAZON_FBA_IN_DEL4", "AMAZON_FBA_IN_DEL5"] else 'TN' if channel_warehouse_id in ["AMAZON_FBA_IN_CJB1","AMAZON_FBA_IN_MAA4"] else 'KA',                        

                        freight_lineitem = {
                            'LineNum': LineNum_Count,
                            'ItemCode': 'EXCM0027',
                            'AccountCode': '41103000',
                            'WarehouseCode':'AMZ-BOM5' if channel_warehouse_id == "AMAZON_FBA_IN_BOM5" else 
                                            'AMZ-BOM7' if channel_warehouse_id == "AMAZON_FBA_IN_BOM7" else 
                                            'AMZ-BLR5' if channel_warehouse_id == "AMAZON_FBA_IN_BLR5" else 
                                            'AMZ-BLR7' if channel_warehouse_id == "AMAZON_FBA_IN_BLR7" else 
                                            'AMZ-BLR8' if channel_warehouse_id == "AMAZON_FBA_IN_BLR8" else 
                                            'AMZ-DEL4' if channel_warehouse_id == "AMAZON_FBA_IN_DEL4" else 
                                            'AMZ-DEL5' if channel_warehouse_id == "AMAZON_FBA_IN_DEL5" else 
                                            'AMZ-CJB1' if channel_warehouse_id == "AMAZON_FBA_IN_CJB1" else
                                            'AMZ-MAA4' if channel_warehouse_id == "AMAZON_FBA_IN_MAA4" else
                                            'EC-FG',
                            'Quantity': '1',
                            'TaxCode': FLKRT_TaxCode if channel_warehouse_id == 'FLIPKART' else f"{tax_state[0]}CS12" if bill_to_code == 'B2C SGST ADD' else f"{tax_state[0]}IG12",
                            'UnitPrice': float(item.shippingcharges) * (100 / (100 + (int(tax_percentage)))),
                            'U_BuyerName': order_doc.customer_name,
                            'U_Order': order_doc.uniware_id,
                            'U_City': order_doc.city,
                            'U_State': order_doc.state,
                            'U_OrderedOn': str(order_doc.created)[:10],
                            'U_PINCode': order_doc.pin_code,
                            'U_Country': 'India'
                        }
                        print(freight_lineitem)
                        Delivery_payload["DocumentLines"].append(freight_lineitem)
                        LineNum_Count += 1
                
        order_doc.save()
        frappe.db.commit()
        #print(json.dumps(Delivery_payload, indent=4))
    print('Delivery_payload is --- ',str(Delivery_payload))
    SAPsession =  AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"Invoices" #DeliveryNotes
    response1 = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    print('response is --- ',str(response1))
    
    resDict = response1.json()
    if resDict.get('DocEntry') is not None:
        for singledoc in completed_orderlist:                
                try:
                    order_doc = frappe.get_doc('Unicommerce Orders', singledoc)
                    order_doc.sap_ar_invoice_docentry = resDict['DocEntry']
                    order_doc.sap_ar_invoice_docnum = resDict['DocNum']
                    order_doc.save()
                except Exception as doc_error:
                    frappe.log_error(title="Unicommerce Order Update Error", message=f"{order_doc}:{str(doc_error)}")
                frappe.db.commit()
        doc_num = resDict.get("DocNum")
        line_items = []
        for item in Delivery_payload["DocumentLines"]:
            base_data = item.copy()
            batches = base_data.pop("BatchNumbers", [])
            if batches:
                for batch in batches:
                    row = base_data.copy()
                    row["BatchNumber"] = batch.get("BatchNumber")
                    row["BatchQuantity"] = batch.get("Quantity")
                    line_items.append(row)
            else:
                base_data["BatchNumber"] = ""
                base_data["BatchQuantity"] = ""
                line_items.append(base_data)
        df = pd.DataFrame(line_items)

        header_fields = {
            'CardCode': Delivery_payload.get('CardCode'),
            'Comments': Delivery_payload.get('Comments'),
            'PayToCode': Delivery_payload.get('PayToCode'),
            'ShipToCode': Delivery_payload.get('ShipToCode'),
            'DocDate': Delivery_payload.get('DocDate'),
            'DocDueDate': Delivery_payload.get('DocDueDate'),
            'U_BillingFrom': Delivery_payload.get('U_BillingFrom'),
            'U_BillTo': Delivery_payload.get('U_BillTo'),
            'TransportationCode': Delivery_payload.get('TransportationCode'),
            'UseBillToAddrToDetermineTax': Delivery_payload.get('UseBillToAddrToDetermineTax'),
            'Series': Delivery_payload.get('Series'),
            'SAP_DocNum': doc_num
        }
        # Create a DataFrame for header (single row)
        header_df = pd.DataFrame([header_fields])
        
        # Create an Excel writer
        filename = f"SAP_Delivery_Payload_{now_datetime().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(get_site_path(), 'private', 'files', filename)
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        
            # Write header in first row
            header_df.to_excel(writer, index=False, sheet_name="Delivery Data", startrow=0)
        
            # Write line items starting from row 2 (3rd row in Excel)
            df.to_excel(writer, index=False, sheet_name="Delivery Data", startrow=2)
        recipient_email = [ "yogesha@khanalfoods.com", 
                            "Harsha@khanalfoods.com" , 
                            "yaknaprabha@khanalfoods.com"
        ]
        frappe.sendmail(
            recipients=recipient_email,
            subject=comment,
            message = (
                        "SAP invoice posting was successful.\n\n"
                        "Kindly refer to the attached Excel file for the details of the payload that was submitted to SAP."
                    ),
            attachments=[{
                "fname": filename,
                "fcontent": open(file_path, 'rb').read()
            }]
        )
        
        # Delete file after sending
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File not found for deletion: {file_path}")
         
    else:
        frappe.log_error("SAP Invoice Failed", str(resDict))

        # Prepare line items: Only ItemCode, BatchNumber, Quantity
        line_items = []
        for item in Delivery_payload["DocumentLines"]:
            item_code = item.get("ItemCode", "")
            if item_code.startswith("CFG"):
                continue  # Skip CFG items
            
            warehouse_code = item.get("WarehouseCode", "")
            batches = item.get("BatchNumbers", [])
            if batches:
                for batch in batches:
                    quantity = batch.get("Quantity", 0)
                    try:
                        quantity = float(quantity)
                    except ValueError:
                        quantity = 0
                    line_items.append({
                        "ItemCode": item_code,
                        "BatchNumber": batch.get("BatchNumber", ""),
                        "Quantity": quantity,
                        "WarehouseCode": warehouse_code
                    })
            else:
                quantity = item.get("Quantity", 0)
                try:
                    quantity = float(quantity)
                except ValueError:
                    quantity = 0
                line_items.append({
                    "ItemCode": item_code,
                    "BatchNumber": "",
                    "Quantity": quantity,
                    "WarehouseCode": warehouse_code
                })

        # Convert to DataFrame and group by ItemCode + BatchNumber
        df = pd.DataFrame(line_items)
        df = df.groupby(["ItemCode", "BatchNumber", "WarehouseCode"], as_index=False).agg({"Quantity": "sum"})

        # Header fields
        header_fields = {
            'CardCode': Delivery_payload.get('CardCode'),
            'Comments': Delivery_payload.get('Comments'),
            'PayToCode': Delivery_payload.get('PayToCode'),
            'ShipToCode': Delivery_payload.get('ShipToCode'),
            'DocDate': Delivery_payload.get('DocDate'),
            'DocDueDate': Delivery_payload.get('DocDueDate'),
            'U_BillingFrom': Delivery_payload.get('U_BillingFrom'),
            'U_BillTo': Delivery_payload.get('U_BillTo'),
            'TransportationCode': Delivery_payload.get('TransportationCode'),
            'UseBillToAddrToDetermineTax': Delivery_payload.get('UseBillToAddrToDetermineTax'),
            'Series': Delivery_payload.get('Series'),
        }

        header_df = pd.DataFrame([header_fields])

        # Write to CSV
        filename = f"SAP_Invoice_Failure_{now_datetime().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(get_site_path(), 'private', 'files', filename)

        # Write header and line items to CSV
        with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            header_df.to_csv(csvfile, index=False)
            csvfile.write("\n")  # Add a blank line between header and line items
            df.to_csv(csvfile, index=False)

        # Email the file
        recipient_email = [
            "yogesha@khanalfoods.com",
            "Harsha@khanalfoods.com",
            "yaknaprabha@khanalfoods.com",
            "sourav@khanalfoods.com"
        ]

        frappe.sendmail(
            recipients=recipient_email,
            subject=f"SAP Invoice Posting Failed - {channel_warehouse_id}",
            message=(
                "SAP invoice creation failed.\n\n"
                "Please refer to the attached CSV file and ensure that inventory is available "
                "in the respective warehouse as per the listed items and batches.\n\n"
                + comment
            ),
            attachments=[{
                "fname": filename,
                "fcontent": open(file_path, 'rb').read()
            }]
        )

        # Delete the file after sending
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File not found for deletion: {file_path}")

        return {"error": "SAP Invoice creation failed", "response": str(resDict)}
    return resDict



#! bench --site .localhost     execute --args  "('AMAZON_IN_API','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BOM5','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BLR7','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BLR8','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_BLR5','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_DEL4','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_DEL5','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_CJB1','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('AMAZON_FBA_IN_MAA4','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('Amazon_IN_API','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('CRED','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('FLIPKART','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('DOGSEE_SITE_IN','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('HN_SITE_IN','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('ONDC_NSTORE','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('HALFCIRCLEFULL','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('MEESHO','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
#! bench --site khanaltech.com execute --args  "('Snapdeal','01-09-2025','30-09-2025' )"  khanal_tech_integrations.utils.Ar_Invoice_Creation_Unicommerce.Channel_delivery_Creation_Dispatched2
