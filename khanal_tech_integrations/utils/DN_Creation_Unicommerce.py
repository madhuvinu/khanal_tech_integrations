import requests
import os
import pandas as pd
import json
import frappe
from frappe.utils import get_site_path
from frappe.utils import add_to_date, now, get_datetime, now_datetime
from datetime import datetime, timedelta
from collections import ChainMap
import collections
from khanal_tech_integrations.utils.Unicommerce_Automation.unicommerceFile.unicommerce_clean import AuthenticateUniware


headersList = {
                    "Accept": "*/*",
                    "User-Agent": "Khanal Tech",
                    "Content-Type": "application/json" 
                }
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1


def get_GST(origin_state,dest_state,item_code,itemss,ChannelName=None):
        
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
        subject = f"TaxCode Mistach for {item_code} in {ChannelName}"
        message = f"""
        TaxCode for {item_code} in {ChannelName} is not matching with UniTax.\n 
        State Code: {state_code}, 
        Tax Type: {tax_type}, 
        UniTax: {UniTax}, 
        Tax Rate: {tax_rate}
        Please review the item and correct the tax configuration.
        """
        frappe.sendmail(
            recipients=["prajwal@khanalfoods.com","sanjoli@khanalfoods.com"],
            subject = subject,
            message = message
        )
        print("Email sent to respective person for review.")
    gst_code        = state_code + tax_type + str(int(UniTax))
    print ("GST Code: ", gst_code)

    return gst_code

def get_customer_address(Cardcode,bill_to_code):
    SAPsession =  AuthenticateSAPB1()
    payload = ''     
    headersList = {
                "Accept": "*/*","User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Content-Type": "application/json" 
                  }
    doc_settings    = frappe.get_doc('SAP Settings')
    invoice_Url     = doc_settings.sap_b1_url+"BusinessPartners('"+ str(Cardcode)  + "')"
    response        = SAPsession.request("GET", invoice_Url, data=json.dumps(payload),  headers=headersList,verify=False)
    resdict         = response.json()
    The_State       = 'KA'
    for address in resdict['BPAddresses']:
      if address['AddressName'] == str(bill_to_code):
        The_State = address['State']
      else:
        pass
    Bill_to_value = 'Local'
    if The_State == 'KA':
        pass
    else:
        Bill_to_value = 'Central'

    # print([The_State, Bill_to_value ])
    return [The_State, Bill_to_value ]

#############################################################################################################################

@frappe.whitelist()
def delivery_from_orderlist(channel,completed_orderlist,bill_to_code,startDate,endDate): #channel,completed_orderlist
    Channel_Mapping = {'C02574': 'Snapdeal',  'C01186': 'Amazon_IN_API', 'C03358': 'CRED',  'C03121': 'FLIPKART','AMAZON_FBA_IN_BOM5' : 'C03564',}
    Channel_Name = Channel_Mapping[str(channel)]
    origin_state = 'Karnataka' #State Code hard coded for now 
    extra = None
    ##TODO: To update the state code dynamically
    if bill_to_code == 'B2C SGST ADD':
        Bill_to = 'Local'
        account_code = '41106001'
        shipping_tax_code = 'KACS@18'
        extra = 'Intra-state'

    elif bill_to_code == 'B2C IGST ADD':
        Bill_to = 'Central'
        account_code = '41106002'
        shipping_tax_code = 'KAIG@18'
        extra = 'Inter-state'

    #PayToState = get_customer_address(channel,bill_to_code)[0]
    #Bill_to = get_customer_address(channel,bill_to_code)[1]
    comment = str(extra) +  "Ecommerce B2C orders for {} from {} to {} Posted Using API from Unicommerce".format(Channel_Name,startDate,endDate)
    print(comment)
    uniware_session = AuthenticateUniware()
    Delivery_payload = { "CardCode"      : str(channel), 
                         "Comments"      : comment,
                         "PayToCode"     : bill_to_code,
                         "ShipToCode"    : bill_to_code,
                         "DocDate"       : endDate,     #EndDate of the date will be when the doc is posted 
                         "DocDueDate"    : endDate,     #Delivery Date
                         "TaxDate"       : endDate,     #Document Date
                         "U_BillingFrom" : 'KT',
                         'U_BillTo'      : Bill_to,
                         "UseBillToAddrToDetermineTax": 'tYES', #"PlaceOfSupply": PayToState, #Here i am inserting the State Code
                         "DocumentLines": []}                   # Delivery_payload['EWayBillDetails']["BillToStateGSTCode"] = state_code
    LineNum_Count = 0
    Delivery_payload["DocumentLines"] = []
    for single_order in completed_orderlist:                    #if single_order.sap_delivery_docnum is None: #if SAP docnum is not created yet
        order_doc = frappe.get_doc('Unicommerce Orders', single_order)
        lineitemss = order_doc.line_items #
        # print('Order ID: ',single_order['name'],len(lineitemss))     
        for itemss in lineitemss:
            lineitem_delivery = { 
                        "LineNum"       : 0, 
                        "ItemCode"      : None,
                        "AccountCode"   : account_code,         # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                        'WarehouseCode' : 'EC-FG', 
                        "Quantity"      : "1",
                        "TaxCode"       : "GST@12",             # Will changed for specific items
                        'TaxType'       : 'tt_Yes', 
                        'TaxLiable'     : 'tYES',
                        # 'TaxTotal'      : 0.0,     
                        "UnitPrice"     : None,
                        'U_BuyerName'   : None,                 #channel_name
                        'U_Order'       : None,
                        'U_OrderID'     : None, 
                        'U_OrderedOn'   : None, 
                        'U_City'        : None,
                        'U_State'       : None,
                        'U_PINCode'     : None,
                        'U_Country'     : 'India',
                        'BatchNumbers'  : [{'BatchNumber'   : 'PLACEHOLDER_BATCH',
                                             "Quantity"     : 1  }]   }
            # print(single_order['name'],itemss.itemsku)
            lineitem_delivery['LineNum']        = LineNum_Count
            itemss.delivery_linenum             = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
            lineitem_delivery['ItemCode']       = itemss.itemsku 
            print( lineitem_delivery['ItemCode'] )
            lineitem_delivery['Quantity']       = itemss.quantity
            # lineitem_delivery['UnitPrice']      = itemss.total_price
            # lineitem_delivery['WarehouseCode']      = 'AMZ-BOM5' if channel == "AMAZON_FBA_IN_BOM5" else 'EC-FG',
            # lineitem_delivery['WarehouseCode']      = 'EC-FG',
            # lineitem_delivery['UnitPrice']     = float(itemss.selling_price)-float(itemss.totalintegratedgst)
            lineitem_delivery['UnitPrice'] = float(itemss.sellingpricewithouttaxesanddiscount) - float(itemss.discount)

            lineitem_delivery['TaxCode']        = get_GST(origin_state,order_doc.state,itemss.itemsku,Channel_Name)#'GST@' + str(itemss.integratedgstpercentage) 
            lineitem_delivery['U_BuyerName']    = order_doc.customer_name
            lineitem_delivery['U_Order']        = order_doc.uniware_id
            lineitem_delivery['U_City']         = order_doc.city
            lineitem_delivery['U_State']        = order_doc.state
            lineitem_delivery['U_OrderedOn']    = str(order_doc.created)[:10] #justThe Date
            lineitem_delivery['U_PINCode']      = order_doc.pin_code
            lineitem_delivery['U_Country']      = 'India'
            batch_assigned                      = itemss.vendorbatchnumber
            if batch_assigned:
                lineitem_delivery['BatchNumbers'][0]['BatchNumber'] =  batch_assigned   #'G5H106I27I'     #itemss.vendorbatchnumber #itemwise batch fucntion here
                lineitem_delivery['BatchNumbers'][0]['Quantity']    =  itemss.quantity   #'G5H106I27I'     #itemss.vendorbatchnumber #itemwise batch fucntion here
                # print ('ITEM: ',itemss.itemsku,'Batch: ',batch_assigned)
            else:
                #print (itemss.itemsku, ' out of stock') # NEED BETTER WAY TO HANDLE THIS
                return {'error': itemss.itemsku + ' out of stock'}
            
            Delivery_payload["DocumentLines"].append(lineitem_delivery) #appending as a lineitems inside inv_payload dictionary
            # print ('Delivery_payload before: ',Delivery_payload)
            LineNum_Count += 1 #increasing the counter

            #Here the shipping charge will be added as a freight line_item
            if int(itemss.shippingcharges)>0:
                freight_lineitem                    = {} #lineitem_delivery.copy()
                freight_lineitem['LineNum']         = LineNum_Count 
                freight_lineitem['ItemCode']        = 'EXCM0027'
                # freight_lineitem['TaxCode']         = shipping_tax_code  #18% GST fixed for all freight charge
                freight_lineitem['UnitPrice']       = itemss.shippingcharges
                freight_lineitem['WarehouseCode']   = 'EC-FG'
                freight_lineitem['U_BuyerName']     = order_doc.customer_name
                freight_lineitem['U_Order']         = order_doc.uniware_id
                freight_lineitem['U_City']          = order_doc.city
                freight_lineitem['U_State']         = order_doc.state
                freight_lineitem['U_OrderedOn']     = str(order_doc.created)[:10] #justThe Date
                freight_lineitem['U_PINCode']       = order_doc.pin_code
                freight_lineitem['U_Country']       = 'India'
                LineNum_Count += 1 #increasing the counter again
                Delivery_payload["DocumentLines"].append(freight_lineitem)
            # print ('Delivery_payload before: ',Delivery_payload)
        order_doc.save()
        # print('List of lineitem in delivery payload : ',len(Delivery_payload['DocumentLines']))
    
    SAPsession =  AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes" #DeliveryNotes
    response1 = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    print('response is --- ',str(response1)[:20])
    ####response docNum to be collected and pushed into the data point of the order-
    ## DocType using a loop in the list - open doctype and writing data  ## 
    return response1.json()

def order_requirements():
    pass
    #orders = frappe.db.get_list('Unicommerce Orders',filters={'status': 'COMPLETE','sap_delivery_docnum':""},group_by,)

def date_filter_test():
    SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                                filters={'status': ('in',['COMPLETE', 'PROCESSING']), 'channel_name': 'FLIPKART',
                                                        'state':'KA','sap_delivery_docnum':"",
                                                        'displayorderdatetime':('between',['2022-11-03','2022-11-04']),
                                                        })
    IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                                filters={'status': ('in',['COMPLETE', 'PROCESSING']), 'channel_name': 'FLIPKART',
                                                        'state':('not in',['KA']),'sap_delivery_docnum':"",
                                                        'displayorderdatetime':['between',['2022-11-03','2022-11-03']],
                                                        })
    print ('SGST : ',len(SGST_orders))
    print ('IGST : ',len(IGST_orders))

# post_delivery_note('2022-10-04','2022-10-04')

#######################################################################################################################################################################################
# bench --site khanaltech.com execute --args  "('FLIPKART', '20-06-2024','26-06-2024' )"  khanal_tech_integrations.utils.DN_Creation_Unicommerce.Channel_post_delivery_note1
# ! function Used For Creating DN from perticular Channel_Name with startDate & endDate
@frappe.whitelist()
def Channel_post_delivery_note1(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list send to create a single invoice out of it'
    """
    channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','DOGSEE_SITE_IN','HN_SITE_IN','ONDC_NSTORE']
    channel_id = Channel_Name
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {'Snapdeal' : 'C02574',
                                    'Amazon_IN_API':'C01186',
                                    'CRED':'C03358',
                                    'FLIPKART':'C03121',
                                    'DOGSEE_SITE_IN':'C00623',
                                    'HN_SITE_IN':'C01026',
                                    'ONDC_NSTORE':'C03494',
                                    }
    print ('Customer is : ', channel_id)
    print ('startDate: ',startDate)
    print('endDate : ',endDate)
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    # start_date = datetime(2024, 7, 1)
    # end_date = start_date + timedelta(days=1)

    # print(start_date,end_date)
    # print(start_date,end_date)
    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                        filters={
                            # 'shipment_status': ('in',['DISPATCHED','DELIVERED']), 
                            'channel_name': channel_id,
                            'state': 'KA',
                            'displayorderdatetime': ['between', [start_date, end_date]],
                            # 'displayorderdatetime' :startDate
                            'sap_delivery_docnum':"",
                        },
                        pluck='name'
                    )
                                        
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                            filters={
                                # 'shipment_status': ('in',['DISPATCHED','DELIVERED']), 
                                'channel_name': channel_id,
                                'state':('not in',['KA']),
                                'displayorderdatetime': ['between', [start_date, end_date]],
                                'sap_delivery_docnum':"",
                                # 'displayorderdatetime' :startDate
                            },
                            pluck='name'
                            )
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                            # 'shipment_status': ('in',['DISPATCHED', 'DELIVERED']), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                            # 'shipment_status': ('in',['DISPATCHED', 'DELIVERED']), 
                                        'channel_name': channel_id,'state':('not in',['KA']),
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
    CustomerCode_from_channel = Channel_CustomerCode_mapping[channel_id]
    
    print ('SGST_orders : ',len(SGST_orders))
    print ('IGST_orders : ',len(IGST_orders))
    Summary_Dict = [ {'Order_Type':'SGST Orders', 'No of Orders': len(SGST_orders),'DeliveryNote Docnum':None },
                     {'Order_Type':'IGST Orders', 'No of Orders': len(IGST_orders),'DeliveryNote Docnum':None } ]
    

    # LOCAL ORDERS
    if len(SGST_orders)>0 :
        bill_to_code = 'B2C SGST ADD'
        Delivery_response = delivery_from_orderlist_batch(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
        # print(Delivery_response,'Delivery_response')
        print(str(Delivery_response)[:40])
        print('PUSHING SGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("***********SGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.sap_delivery_docentry = Delivery_response['DocEntry']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['error']
            print (Delivery_response['error'])
            print ('ERROR',Delivery_response)
        #frappe.db.commit()

    #Outside state orders
    if len(IGST_orders)>0:
        bill_to_code = 'B2C IGST ADD'
     
        Delivery_response = delivery_from_orderlist_batch(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        print('PUSHING IGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("**********IGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.sap_delivery_docentry = Delivery_response['DocEntry']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['error']
            print (Delivery_response['error'])
            print ('ERROR',Delivery_response)
            frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    # Sending mail about the result
    return Summary_Dict
####################################################################################
@frappe.whitelist()
def DNsendmail(DICT,Title=None):
    recipients=['sourav@khanalfoods.com','harsha@khanalfoods.com','yogesha@khanalfoods.com','manoj@khanalfoods.com']
    # create HTML table with some CSS for spacing
    table = "<table style='border-collapse: collapse; margin-top: 10px;'><tr><th style='border: 1px solid black; padding: 5px;'>Order_Type</th><th style='border: 1px solid black; padding: 5px;'>No of Orders</th><th style='border: 1px solid black; padding: 5px;'>INV_docnum</th></tr>"
    for item in DICT:
        table += f"<tr><td style='border: 1px solid black; padding: 5px;'>{item['Order_Type']}</td><td style='border: 1px solid black; padding: 5px;'>{item['No of Orders']}</td><td style='border: 1px solid black; padding: 5px;'>{item['AR Invoice Docnum']}</td></tr>"
    table += "</table>"

    email_args={
        "recipients":recipients,
        "message":table,
        "subject":Title,
        # "message_type": "html"
                }
    frappe.enqueue(method=frappe.sendmail,queue='short',timeout=300, **email_args)
    return None
########################################################################################################################################################
def Unicommerce_Dispatch_DN():
    Today = frappe.utils.nowdate()
    startD = add_to_date(Today,days=-1)
    
    print(startD)
    Channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','DOGSEE_SITE_IN','HN_SITE_IN','ONDC_NSTORE']
    for single_channel in Channel_list:
        missing_Qty = False
        if missing_Qty:
            pass
        else:
            Push_result = Channel_delivery_Creation_Dispatched(Channel_Name=single_channel,startDate=startD,endDate=startD)
            title = 'The DeliveryNote Creation for '+str(single_channel) + ' for Date :'+ str(startD) +''
            DNsendmail(DICT = Push_result,Title=title)
    return Push_result

###############################################################################################################################################
#! bench --site dev.localhost execute --args  "('FLIPKART', '01-06-2024','10-06-2024' )"  khanal_tech_integrations.utils.DN_Creation_Unicommerce.Channel_post_delivery_note1

@frappe.whitelist()
def Channel_delivery_Creation_Dispatched(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list 
    send to create a single invoice out of it.
    """
    channel_id = Channel_Name
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {
                                    'C02574':['Snapdeal'],
                                    'C03564':['AMAZON_FBA_IN_BOM7', 'AMAZON_FBA_IN_BOM5'],
                                    'C03575':['AMAZON_FBA_IN_BLR5', 'AMAZON_FBA_IN_BLR7', 'AMAZON_FBA_IN_BLR8', 'Amazon_IN_API'],
                                    'C03579':['AMAZON_FBA_IN_DEL4', 'AMAZON_FBA_IN_DEL5'],
                                    'C03358':['CRED'],  
                                    'C03121':['FLIPKART'],
                                    'C00623':['DOGSEE_SITE_IN'],
                                    'C01026':['HN_SITE_IN'],
                                    'C03494':['ONDC_NSTORE'],
                                    'C03412':['HALFCIRCLEFULL'],
                                    'C03586':['MEESHO']
                                    }
    # print ('startDate: ',startDate)
    # print('endDate : ',endDate)
    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                        'status': ('in',['COMPLETE']), 
                                        'channel_name'      : channel_id,
                                        'state'             :'KA',
                                        'sap_delivery_docnum':"",
                                        'shipment_date'     :('between',[startDate,endDate]),
                                        'shipment_status'   : ('in',['DISPATCHED',  'DELIVERED','SHIPPED','RETURN_EXPECTED' ]), 
                                        },
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                            'status'   : ('in',['COMPLETE',    #   'PROCESSING'
                                                                  ]), 
                                        'channel_name'      : channel_id,
                                        'state'             :('not in',['KA']),
                                        'sap_delivery_docnum':"",
                                        'shipment_date'     :('between',[startDate,endDate]),
                                        'shipment_status'   : ('in',['DISPATCHED',  'DELIVERED','SHIPPED','RETURN_EXPECTED' ]), 
                                        },
                                        pluck='name') #
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                            'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={
                                            'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
                                        'channel_name': channel_id,'state':('not in',['KA']),
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
    CustomerCode_from_channel = Channel_CustomerCode_mapping[channel_id]
    
    
    
    Summary_Dict = [ {'Order_Type':'SGST Orders', 'No of Orders': len(SGST_orders),'DeliveryNote Docnum':None },
                     {'Order_Type':'IGST Orders', 'No of Orders': len(IGST_orders),'DeliveryNote Docnum':None } ]
    

    # LOCAL ORDERS
    if len(SGST_orders)>0 :
        bill_to_code = 'B2C SGST ADD'
        print ('SGST_orders : ',len(SGST_orders))
        print('PUSHING SGST ORDERS')
        
        Delivery_response = delivery_from_orderlist_batch(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        if Delivery_response.get('DocNum') is not None:
            print("* * * * * * * * * * * SGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.sap_delivery_docentry = Delivery_response['DocEntry']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['error']
            print ('ERROR',Delivery_response)
        #frappe.db.commit()

    #Outside state orders
    if len(IGST_orders)>0:
        bill_to_code = 'B2C IGST ADD'
        print('PUSHING IGST ORDERS')
     
        Delivery_response = delivery_from_orderlist_batch(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
        # print(Delivery_response,'Delivery_response')
        print(str(Delivery_response)[:40])
        if Delivery_response.get('DocNum') is not None:
            print("* * * * * * * * * * * IGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.sap_delivery_docentry = Delivery_response['DocEntry']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['error']
            print ('ERROR',Delivery_response)
            #frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    # Sending mail about the result
    return Summary_Dict

####################################################################################################################################################
# ! function Used to  POST INV in SAP 
@frappe.whitelist()
def delivery_from_orderlist_batch(channel,channel_id,completed_orderlist,bill_to_code,startDate,endDate):
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
    for single_order in completed_orderlist:
        order_doc = frappe.get_doc('Unicommerce Orders', single_order)
        lineitemss = order_doc.line_items 
        for itemss in lineitemss:
            lineitem_delivery = { "LineNum": 0,
                        "ItemCode"      : None,
                        "AccountCode"   : account_code, 
                        'WarehouseCode' : 'AMZ-BOM5' if channel_warehouse_id == "AMAZON_FBA_IN_BOM5" else 
                                          'AMZ-BOM7' if channel_warehouse_id == "AMAZON_FBA_IN_BOM7" else 
                                          'AMZ-BLR5' if channel_warehouse_id == "AMAZON_FBA_IN_BLR5" else 
                                          'AMZ-BLR7' if channel_warehouse_id == "AMAZON_FBA_IN_BLR7" else 
                                          'AMZ-BLR8' if channel_warehouse_id == "AMAZON_FBA_IN_BLR8" else 
                                          'AMZ-DEL4' if channel_warehouse_id == "AMAZON_FBA_IN_DEL4" else 
                                          'AMZ-DEL5' if channel_warehouse_id == "AMAZON_FBA_IN_DEL5" else
                                          'AMZ-CJB1' if channel_warehouse_id == "AMAZON_FBA_IN_CJB1" else
                                          'AMZ-MAA4' if channel_warehouse_id == "AMAZON_FBA_IN_MAA4" else
                                          'EC-FG',
                        "Quantity"      : "1",
                        "TaxCode"       : "GST@12",     # Will changed for specific items
                        'TaxType'       : 'tt_Yes',  
                        'TaxLiable'     : 'tYES',
                        'TaxTotal'      : 0.0,      
                        "UnitPrice"     : None,
                        'U_BuyerName'   : None,         #Channel Name
                        'U_Order'       : None,
                        'U_OrderID'     : None, 
                        'U_OrderedOn'   : None,
                        'U_City'        : None,
                        'U_State'       : None, 
                        'U_PINCode'     : None, 
                        'U_Country'     : 'India',
                        'BatchNumbers'  : [{'BatchNumber'   : 'PLACEHOLDER_BATCH',
                                              "Quantity"    : 1  }]  }           
            if itemss.bundleskucode and itemss.bundleskucode.startswith("CFG"):
                lineitem_delivery1  = lineitem_delivery.copy()
                lineitem_delivery1['LineNum']       = LineNum_Count
                itemss.delivery_linenum             = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
                lineitem_delivery1['ItemCode']      = itemss.bundleskucode   
                lineitem_delivery1['Quantity']      = itemss.quantity
                lineitem_delivery1['UnitPrice']     = 0.0
                lineitem_delivery1['TaxCode']       =  get_GST(origin_state,order_doc.state,itemss.itemsku,itemss,channel_warehouse_id)#'GST@' + str(itemss.integratedgstpercentage) 
                lineitem_delivery1['U_BuyerName']   = order_doc.customer_name
                lineitem_delivery1['U_Order']       = order_doc.uniware_id
                lineitem_delivery1['U_City']        = order_doc.city
                lineitem_delivery1['U_State']       = order_doc.state
                lineitem_delivery1['U_OrderedOn']   = str(order_doc.created)[:10] #justThe Date
                lineitem_delivery1['U_PINCode']     = order_doc.pin_code
                lineitem_delivery1['U_Country']     = 'India'
                lineitem_delivery1['TreeType']      = 'iSalesTree' #Is a NON-INVENTORY ITEM
                lineitem_delivery1.pop('BatchNumbers')
                Delivery_payload["DocumentLines"].append(lineitem_delivery1)
                LineNum_Count += 1 
                lineitem_code = itemss.code                             
                if lineitem_code:
                    for next_item in lineitemss :
                        (lineitem_code == next_item.code.rsplit('-', 1)[0])
                        print ("pritning the lineitem_code1",lineitem_code)
                        lineitem_delivery2 = lineitem_delivery.copy()
                        lineitem_delivery2['LineNum'] = LineNum_Count
                        next_item.delivery_linenum = LineNum_Count + 1
                        lineitem_delivery2['ItemCode'] = next_item.itemsku
                        lineitem_delivery2['Quantity'] = next_item.quantity
                        lineitem_delivery2['UnitPrice'] = round(float(next_item.sellingpricewithouttaxesanddiscount) - float(next_item.discount),2)
                        lineitem_delivery2['TaxCode'] = get_GST(origin_state, order_doc.state, next_item.itemsku,itemss, channel_warehouse_id)
                        lineitem_delivery2['U_BuyerName'] = order_doc.customer_name
                        lineitem_delivery2['U_Order'] = order_doc.uniware_id
                        lineitem_delivery2['U_City'] = order_doc.city
                        lineitem_delivery2['U_State'] = order_doc.state
                        lineitem_delivery2['U_OrderedOn'] = str(order_doc.created)[:10]
                        lineitem_delivery2['U_PINCode'] = order_doc.pin_code
                        lineitem_delivery2['U_Country'] = "India"
                        lineitem_delivery2['TreeType'] = "iIngredient" #Is a NON-INVENTORY ITEM
                        if hasattr(next_item, 'vendorbatchnumber') and next_item.vendorbatchnumber:
                            lineitem_delivery2['BatchNumbers'] = [{
                            'BatchNumber': next_item.vendorbatchnumber,  # Assign specific batch per item
                            'Quantity': next_item.quantity
                        }]
                        else:
                            print(f"{next_item.itemsku} is out of stock")
                            return {'Error': f'Child item {next_item.itemsku} is out of stock'}

                        Delivery_payload["DocumentLines"].append(lineitem_delivery2)
                        LineNum_Count += 1
                    break       
            else:
                lineitem_delivery['LineNum']        = LineNum_Count
                itemss.delivery_linenum             = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
                lineitem_delivery['ItemCode']       = itemss.itemsku 
                lineitem_delivery['Quantity']       = itemss.quantity
                lineitem_delivery['UnitPrice']      = round(float(itemss.sellingpricewithouttaxesanddiscount) - float(itemss.discount),2)
                lineitem_delivery['TaxCode']        = get_GST(origin_state,order_doc.state,itemss.itemsku,itemss,channel_warehouse_id)#'GST@' + str(itemss.integratedgstpercentage) 
                lineitem_delivery['U_BuyerName']    = order_doc.customer_name
                lineitem_delivery['U_Order']        = order_doc.uniware_id
                lineitem_delivery['U_City']         = order_doc.city
                lineitem_delivery['U_State']        = order_doc.state
                lineitem_delivery['U_OrderedOn']    = str(order_doc.created)[:10] #justThe Date
                lineitem_delivery['U_PINCode']      = order_doc.pin_code
                lineitem_delivery['U_Country']      = 'India'
                if hasattr(itemss, 'vendorbatchnumber') and itemss.vendorbatchnumber:
                    lineitem_delivery['BatchNumbers'] = [{
                    'BatchNumber': itemss.vendorbatchnumber,  # Assign specific batch per item
                    'Quantity': itemss.quantity
                    }]
                else:
                    print(f"{itemss.itemsku} is out of stock")
                    return {'Error': f'Child item {next_item.itemsku} is out of stock'}
                Delivery_payload["DocumentLines"].append(lineitem_delivery)
                LineNum_Count += 1 #increasing the counter

                if any(channel_warehouse_id in channels for channels in Channel_Mapping.values()) and int(float(itemss.shippingcharges)) > 0:
                    tax_percentagee = float(itemss.shippingchargetaxpercentage)
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
                        'UnitPrice': float(itemss.shippingcharges) * (100 / (100 + (int(tax_percentage)))),
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
                else:
                    print(" ")

            order_doc.save()
            frappe.db.commit()
    print('List of lineitem in delivery payload : ',len(Delivery_payload['DocumentLines']))
    print('\n\n\n\n',json.dumps(Delivery_payload),'\n\n\n\n')
    SAPsession =  AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"Invoices" #DeliveryNotes
    response1 = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    print('response is --- ',str(response1))
    ###response docNum to be collected and pushed into the data point of the order-
    # DocType using a loop in the list - open doctype and writing data  ## 
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
                            "manoj@khanalfoods.com" , 
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

        # Write to Excel
        filename = f"SAP_Invoice_Failure_{now_datetime().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(get_site_path(), 'private', 'files', filename)
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            header_df.to_excel(writer, index=False, sheet_name="Invoice Data", startrow=0)
            df.to_excel(writer, index=False, sheet_name="Invoice Data", startrow=2)

        # Email the file
        recipient_email = [
            "yogesha@khanalfoods.com",
            "manoj@khanalfoods.com",
            "Harsha@khanalfoods.com",
            "yaknaprabha@khanalfoods.com",
            "sourav@khanalfoods.com"
        ]

        frappe.sendmail(
            recipients=recipient_email,
            subject="SAP Invoice Posting Failed  "+ channel_warehouse_id,
            message=(
                        "SAP invoice creation failed.\n\n"
                        "Please refer to the attached Excel file and ensure that inventory is available "
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
###########################################################################################################
@frappe.whitelist()
def DN_Creation_from_Upload(): 
    Sample_input = {
        "list":
        [
            {   "ItemCode":"FGHN0015", "Quantity":4,   "BatchCode":"Batch_HN1"  },
            {   "ItemCode":"FGHN0025", "Quantity":12,  "BatchCode":"Batch_HN23" },
            {   "ItemCode":"FGDC0031", "Quantity":7,   "BatchCode":"Batch_DC02" },
            {   "ItemCode":"FGDC0068", "Quantity":11,  "BatchCode":"Batch_DC13" },
         ]
        }
 
    startDate = frappe.utils.nowdate()
    Unicommerce_outside_Channels = [ 'JioMart' , 'AmazonFlex' ,'Wagr',  'PawsIndia', 'HalfCircleFull', 'NorthEast','PetKonnect' ]
    Channel_Mapping = { 'JioMart'       : 'C03172',
                       'AmazonFlex'     : 'C00127',
                       'Wagr'           : 'C03170',
                       'PawsIndia'      : 'C03161',
                       'HalfCircleFull' : 'C03412',
                       'NorthEast'      : 'C02836',
                       'PetKonnect'     : 'C03321', #Pet konnet private limited
                       }
    
    origin_state = 'Karnataka' #State Code hardcoded for now 

    bill_to_code    = 'B2C IGST ADD'
    Bill_to         = 'Central'
    account_code    = '41106002'
    for Channel_Name in Unicommerce_outside_Channels:
        Selected_Channelwise_Items = frappe.db.get_list('Dispatch Record', 
                                            filters={
                                                    'channelname': Channel_Name,
                                                    'sap_delivery_docnum':"",
                                                    },
                                            )
        Channel_Code = Channel_Mapping[Channel_Name]
        print("For channel : ",Channel_Name,"Numbers of items -- ",len(Selected_Channelwise_Items))
        comment =  "E-com B2C orders for {} from {} Posted Using API from Dispatch Upload".format(Channel_Name,startDate) #startDate
        print(comment)

        Delivery_payload = { "CardCode"      : Channel_Code, 
                            "Comments"      : comment,
                            "PayToCode"     : bill_to_code,
                            "ShipToCode"    : bill_to_code,
                            "DocDate"       : startDate,    # EndDate of the date will be when the doc is posted 
                            "DocDueDate"    : startDate,    # Delivery Date
                            "TaxDate"       : startDate,    # Document Date
                            "U_BillingFrom" : 'KT',
                            'U_BillTo'      : Bill_to,
                            "UseBillToAddrToDetermineTax": 'tYES', #"PlaceOfSupply": PayToState, #Here i am inserting the State Code
                            "DocumentLines": []}
        LineNum_Count = 0
        Delivery_payload["DocumentLines"] = []  
        if len(Selected_Channelwise_Items) > 0:
            for single_item_doc in Selected_Channelwise_Items:#[2:4]:
                single_item = frappe.get_doc('Dispatch Record', single_item_doc['name'])  
                lineitem_delivery = {
                            "LineNum"       : 0, 
                            "ItemCode"      : None,
                            "AccountCode"   : account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                            'WarehouseCode' : 'EC-FG',
                            "Quantity"      : "1",
                            "TaxCode"       : "GST@12", #Will changed for specific items
                            'TaxType'       : 'tt_Yes', 
                            'TaxLiable'     : 'tYES',
                            'TaxTotal'      : 0.0,    
                            "UnitPrice"     : None,
                            'U_Country'     : 'India',
                            'BatchNumbers'  : [{'BatchNumber'   : 'PLACEHOLDER_BATCH',
                                                   "Quantity"   : 1  }] }
                lineitem_delivery['LineNum']        = LineNum_Count    #filling the LineNum value(It will be the couting on frontEND SAP)
                lineitem_delivery['ItemCode']       = single_item.itemcode
                print( lineitem_delivery['ItemCode'] )
                single_item.delivery_linenum        = lineitem_delivery['LineNum']  + 1
                lineitem_delivery['Quantity']       = single_item.quantity
                lineitem_delivery['U_OrderedOn']    = single_item.added_date
                lineitem_delivery['TaxCode']        = get_GST(origin_state,'MH',single_item.itemcode,Channel_Name)#'GST@' + str(itemss.integratedgstpercentage) 
                single_item.save()

                lineitem_delivery['BatchNumbers'][0]['BatchNumber'] =  single_item.batchcode 
                lineitem_delivery['BatchNumbers'][0]['Quantity']    =  single_item.quantity
                
                Delivery_payload["DocumentLines"].append(lineitem_delivery) #appending as a lineitems inside inv_payload dictionary
                LineNum_Count   += 1 #increasing the counter


                
            SAPsession          =  AuthenticateSAPB1()
            doc_settings        = frappe.get_doc('SAP Settings')
            DN_Creation_URL     = doc_settings.sap_b1_url+"DeliveryNotes" #DeliveryNotes
            response            = SAPsession.request("POST", DN_Creation_URL, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
            response1           = response.json()
            
            if response1.get('error') is None:
                print("Orders - Delivery_response['DocNum'] : ",response1['DocNum'])
                
                for singledoc in Selected_Channelwise_Items:
                    order_doc = frappe.get_doc('Dispatch Record', singledoc['name'])  
                    order_doc.sap_delivery_docnum   = response1['DocNum']
                    order_doc.sap_delivery_docentry = response1['DocEntry']
                
                    order_doc.save()
                    frappe.db.commit()
            else:
                print(response1['error'])
    return None

# bench --site khanaltech.com execute --args  "('CRED', '06-11-2023','08-11-2023' )"  khanal_tech_integrations.utils.DN_Creation_Unicommerce.Channel_post_delivery_note1
# bench --site 1mint.localhost execute  khanal_tech_integrations.utils.DN_Creation_Unicommerce.Unicommerce_Dispatch_DN
