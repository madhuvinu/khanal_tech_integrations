import requests
import json
import frappe
from frappe.utils import add_to_date, now, get_datetime, now_datetime
#import time
import datetime
from collections import ChainMap
import collections


headersList = {
                    "Accept": "*/*",
                    "User-Agent": "Khanal Tech",
                    "Content-Type": "application/json" 
                }

#Function to authenticate SAP B1
def AuthenticateSAPB1():
    """
    Function to Authenticate SAP Business One
    """
    b1_session = requests.Session()

    doc = frappe.get_doc('SAP Settings')

    expires_on = frappe.db.get_single_value('SAP Settings','expires_on')
    
    if (expires_on==''):
        try:
            b1_session = renew_sap_session()
        except Exception as e:
            raise e
    elif expires_on !='':
        if now_datetime() >= get_datetime(doc.expires_on):
            try:
                # frappe.log_error('frappe AuthenticateSAPB1 now_date',now_datetime())
                # frappe.log_error('frappe AuthenticateSAPB1 sap_exp_date',get_datetime(doc.expires_on))
                b1_session = renew_sap_session()
            except Exception as e:
                raise e
        else:
            b1_session.cookies.set("B1SESSION", frappe.db.get_single_value('SAP Settings','b1session'))
            b1_session.cookies.set("ROUTEID", frappe.db.get_single_value('SAP Settings','routeid'))
    return b1_session

@frappe.whitelist()
def initiate_session():
    x = AuthenticateSAPB1()
    print (x.headers)
    print (x.cookies)

@frappe.whitelist()
def renew_sap_session():
    b1_session = requests.Session()
    print('b1_session',b1_session)
    doc = frappe.get_doc('SAP Settings')
    credentials_json = {"CompanyDB": doc.companydb,"Password": doc.get_password('password'),"UserName": doc.username}
    b1_url = doc.sap_b1_url
    reqUrl = b1_url + "Login"
    payload = json.dumps(credentials_json)
    response = b1_session.request("POST", reqUrl, data=payload,  headers=headersList,verify=False)
    cookies = b1_session.cookies.get_dict()
    # frappe.log_error('frappe renew_sap_session cookies',cookies)
    doc.b1session = cookies["B1SESSION"]
    # frappe.log_error('frappe renew_sap_session doc.b1session',doc.b1session)
    doc.routeid = cookies['ROUTEID']                                                        
    doc.expires_on = add_to_date(now_datetime(), minutes=int(response.json()['SessionTimeout']))
    doc.save(ignore_permissions=True)
    return b1_session


@frappe.whitelist()
def bulk_process_inventory_transfers():
    """
    Update Inventory transfers from SAP to Khanal Tech Integrations 
    """
    session = AuthenticateSAPB1()
    payload = ''

    #CHECK THE LAST MAX UPDATED INV. TRANSFERS
    start_page = 10
    try:
        last_page_doc = frappe.get_last_doc('SAP Inventory Transfers Update Logs')
        start_page = last_page_doc.last_skip
    except:
        start_page = 1
    #for i in range(int(start_page),2):
    i = int(start_page)
    if i and i>1:
        i = i - 1

    # INITIALIZATION
    doc_settings = frappe.get_doc('SAP Settings')
    reqUrl = doc_settings.sap_b1_url+"StockTransfers?$skip=" + str(20*i)
    session = AuthenticateSAPB1()
    response = session.request("GET", reqUrl, data=payload,  headers=headersList,verify=False)
        
    transfer_requests = dict(response.json())
    next_page = transfer_requests.get("odata.nextLink",None)

    while True:
    #while next_page is not None:
        print ('SKIP : ', i)
        doc_settings = frappe.get_doc('SAP Settings')
        reqUrl = doc_settings.sap_b1_url+"StockTransfers?$skip=" + str(20*i)
        session = AuthenticateSAPB1()
        response = session.request("GET", reqUrl, data=payload,  headers=headersList,verify=False)
        transfer_requests = dict(response.json())
        
        try:
            if transfer_requests['value'] is not None:
                for transfer_request in transfer_requests['value']:
                    # print (transfer_request['DocNum'],' i:',i)
                    if frappe.db.exists('SAP Inventory Transfers',transfer_request['DocEntry']):
                        #skip
                        pass
                    else:
                        doc     = frappe.new_doc('SAP Inventory Transfers')
                        doc.docentry        = transfer_request['DocEntry']
                        doc.series          = transfer_request['Series']
                        doc.docdate         = transfer_request['DocDate']
                        doc.docnum          = transfer_request['DocNum']
                        doc.fromwarehouse   = transfer_request['FromWarehouse']
                        doc.towarehouse     = transfer_request['ToWarehouse']
                        doc.cardcode        = transfer_request['CardCode']
                        doc.comments        = transfer_request['Comments']
                        doc.delivered       = transfer_request['U_Delivered']
                        #doc.save()
                        try:
                            #try saving, skip if already exist
                            doc.save()
                        except frappe.DuplicateEntryError:
                            pass

                        doc = frappe.get_doc("SAP Inventory Transfers",transfer_request['DocEntry'])
                        LineItems = get_single_inventory_transfer(transfer_request['DocEntry'])
                        for LineItem in LineItems:
                            doc.append("line_items",LineItem)
                        doc.save()
                    frappe.db.commit() #
                i +=1
                #increment the counter
            elif transfer_requests['value'] is None:
                break
            
        except Exception as e:
            #break
            print ('Exception : ',e)

        next_page = transfer_requests.get("odata.nextLink",None)
        if next_page is None:
            break

    #Update the last page
    doc1 = frappe.new_doc('SAP Inventory Transfers Update Logs')
    doc1.last_skip = i
    doc1.save()

    frappe.msgprint(msg='Data Inserted successfully',title='Success')
    return None
#############################################################################################
@frappe.whitelist()
def single_process_inventory_transfers(DocEntry):
    """
    Update Inventory transfers from SAP to Khanal Tech Integrations given a single docEntry.
    """
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    reqUrl = doc_settings.sap_b1_url+"StockTransfers(" + str(DocEntry) + ")"
    payload = ""

    headersList = {
                "Accept": "*/*",
                "User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Content-Type": "application/json" 
            }
    response = session.request("GET", reqUrl, data=payload,  headers=headersList,verify=False)
    transfer_request = dict(response.json())

    if transfer_request['DocEntry'] is not None:
        print ('Going into')
        if frappe.db.exists('SAP Inventory Transfers',transfer_request['DocEntry']):
            doc     = frappe.get_doc('SAP Inventory Transfers',transfer_request['DocEntry'])
            print('Already in the database.')
        else:
            doc     = frappe.new_doc('SAP Inventory Transfers')
            doc.docentry        = transfer_request['DocEntry']
            doc.series          = transfer_request['Series']
            doc.docdate         = transfer_request['DocDate']
            doc.docnum          = transfer_request['DocNum']
            doc.fromwarehouse   = transfer_request['FromWarehouse']
            doc.towarehouse     = transfer_request['ToWarehouse']
            doc.cardcode        = transfer_request['CardCode']
            doc.comments        = transfer_request['Comments']
            doc.delivered       = transfer_request['U_Delivered']
            #doc.save()
            try:
                #try saving, skip if already exist
                doc.save()
            except frappe.DuplicateEntryError:
                pass

        doc = frappe.get_doc("SAP Inventory Transfers",transfer_request['DocEntry'])
        doc.line_items = []
        doc.save()
        frappe.db.commit() #
        LineItems = get_single_inventory_transfer(transfer_request['DocEntry'])
        for LineItem in LineItems:
            doc.append("line_items",LineItem)
            print('Line Updated')
        doc.save()
        frappe.db.commit() #
    elif transfer_request['value'] is None:
        print('Response from SAP failed.')
    return None

###############################################################################################################
###############################################################################################################
###############################################################################################################

def get_single_inventory_transfer(DocEntry):
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    reqUrl = doc_settings.sap_b1_url+"StockTransfers(" + str(DocEntry) + ")"
    payload = ""

    headersList = {
                "Accept": "*/*",
                "User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Content-Type": "application/json" 
            }
    response = session.request("GET", reqUrl, data=payload,  headers=headersList,verify=False)
    inventory_transfer = dict(response.json())

    LineItems = inventory_transfer['StockTransferLines']
    
    LineItem_list = []
    for LineItem in LineItems:
       
        for BatchDetail in LineItem['BatchNumbers']:
            #doc.line_items
            LineItem_list.append({"itemcode":LineItem['ItemCode'],
                                  "itemdescription":LineItem['ItemDescription'],
            "quantity"          :LineItem['Quantity'],
            "towarehousecode"   : LineItem['WarehouseCode'],
            "unitprice"         : LineItem["UnitPrice"],
            "fromwarehousecode" : LineItem['FromWarehouseCode'], 
            "batchnumber"       : BatchDetail['BatchNumber'],
            "batchquantity"     :BatchDetail['Quantity'],
            'expirydate'        : BatchDetail['ExpiryDate'],
            'manufacturingdate' : BatchDetail['ManufacturingDate'],
            'addmisiondate'     :  BatchDetail['AddmisionDate'], })
            #print (LineItem['ItemCode'],LineItem['ItemDescription'],LineItem['Quantity'],LineItem['WarehouseCode'],LineItem['FromWarehouseCode'], BatchDetail['BatchNumber'],BatchDetail['Quantity'],BatchDetail['ExpiryDate'],BatchDetail['ManufacturingDate'])
    return LineItem_list

@frappe.whitelist()
def delivery_from_orderlist(channel,completed_orderlist,bill_to_code,startDate,endDate): #channel,completed_orderlist
    Channel_Mapping = {'C02574': 'Snapdeal',  'C01186': 'Amazon_IN_API', 'C03358': 'CRED',  'C03121': 'FLIPKART'}
    Channel_Name = Channel_Mapping[str(channel)]
    origin_state = 'Karnataka' #State Code hardcoded for now 
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

    comment = str(extra) +  "Ecommerce B2C orders for {} from {} to {} Posted Using API from Unicommerce".format(Channel_Name,startDate,endDate)
    print(comment)

    Delivery_payload = { "CardCode"      : str(channel), 
                         "Comments"      : comment,
                         "PayToCode"     : bill_to_code,
                         "ShipToCode"    : bill_to_code,
                         "DocDate"       : endDate,#EndDate of the date will be when the doc is posted 
                         "DocDueDate"    : endDate,  #Delivery Date
                         "TaxDate"       : endDate, #Document Date
                         "U_BillingFrom" : 'KT',
                         'U_BillTo'      : Bill_to,
                         "UseBillToAddrToDetermineTax": 'tYES',
                         #"PlaceOfSupply": PayToState, #Here i am inserting the State Code
                         "DocumentLines": []}
    LineNum_Count = 0
    Delivery_payload["DocumentLines"] = []
    for single_order in completed_orderlist:
        #if single_order.sap_delivery_docnum is None: #if SAP docnum is not created yet
        order_doc = frappe.get_doc('Unicommerce Orders', single_order)
        lineitemss = order_doc.line_items #
        # print('Order ID: ',single_order['name'],len(lineitemss))     
        for itemss in lineitemss:
            lineitem_delivery = {
                        "LineNum": 0, 
                        "ItemCode": None,
                        "AccountCode": account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                        'WarehouseCode': 'EC-B2C',
                        "Quantity": "1",
                        "TaxCode": "GST@12", #Will changed for specific items
                        'TaxType': 'tt_Yes', 
                        'TaxLiable': 'tYES',
                        'TaxTotal': 0.0,    
                        "UnitPrice": None,
                        'U_BuyerName': None,  #channel_name
                        'U_Order': None,
                        'U_OrderID': None, 
                        'U_OrderedOn': None, 
                        'U_City': None, 
                        'U_State': None,
                        'U_PINCode': None,
                        'U_Country': 'India',
                        'BatchNumbers': [{'BatchNumber': 'PLACEHOLDER_BATCH',
                                        "Quantity": 1  }]
                            }
            lineitem_delivery['LineNum'] = LineNum_Count
            itemss.delivery_linenum     = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
            lineitem_delivery['ItemCode'] = itemss.itemsku 
            print( lineitem_delivery['ItemCode'] )
            lineitem_delivery['Quantity'] = itemss.quantity
            # lineitem_delivery['UnitPrice'] = itemss.total_price
            lineitem_delivery['UnitPrice'] = float(itemss.selling_price)-float(itemss.totalintegratedgst)
            
            # itemss.total_price/1.int(itemss.integratedgstpercentage) 
            lineitem_delivery['TaxCode'] =  get_GST(origin_state,order_doc.state,itemss.itemsku)#'GST@' + str(itemss.integratedgstpercentage) 
            lineitem_delivery['U_BuyerName'] = order_doc.customer_name
            lineitem_delivery['U_Order'] = order_doc.uniware_id
            lineitem_delivery['U_City'] = order_doc.city
            lineitem_delivery['U_State'] = order_doc.state
            lineitem_delivery['U_OrderedOn'] = str(order_doc.created)[:10] #justThe Date
            lineitem_delivery['U_PINCode'] = order_doc.pin_code
            lineitem_delivery['U_Country'] = 'India'
            batch_assigned = Get_FirstExpiry_Batch(str(itemss.itemsku),Req_Quantity=itemss.quantity)
            if batch_assigned:
                lineitem_delivery['BatchNumbers'][0]['BatchNumber'] =  batch_assigned   #'G5H106I27I'     #itemss.vendorbatchnumber #itemwise batch fucntion here
                lineitem_delivery['BatchNumbers'][0]['Quantity'] =  itemss.quantity   #'G5H106I27I'     #itemss.vendorbatchnumber #itemwise batch fucntion here
                # print ('ITEM: ',itemss.itemsku,'Batch: ',batch_assigned)
            else:
                #print (itemss.itemsku, ' out of stock') # NEED BETTER WAY TO HANDLE THIS
                return {'error': itemss.itemsku + ' out of stock'}
            
            Delivery_payload["DocumentLines"].append(lineitem_delivery) #appending as a lineitems inside inv_payload dictionary
            LineNum_Count += 1 #increasing the counter

            #Here the shipping charge will be added as a freight line_item
            if float(itemss.shippingcharges)>0:
                freight_lineitem = {} #lineitem_delivery.copy()
                freight_lineitem['LineNum'] = LineNum_Count 
                freight_lineitem['ItemCode'] = 'EXCM0027'
                freight_lineitem['TaxCode'] = shipping_tax_code  #18% GST fixed for all freight charge
                freight_lineitem['UnitPrice'] = itemss.shippingcharges
                freight_lineitem['WarehouseCode'] = 'EC-B2C'
                freight_lineitem['U_BuyerName'] = order_doc.customer_name
                freight_lineitem['U_Order'] = order_doc.uniware_id
                freight_lineitem['U_City'] = order_doc.city
                freight_lineitem['U_State'] = order_doc.state
                freight_lineitem['U_OrderedOn'] = str(order_doc.created)[:10] #justThe Date
                freight_lineitem['U_PINCode'] = order_doc.pin_code
                freight_lineitem['U_Country'] = 'India'
                LineNum_Count += 1 #increasing the counter again
                Delivery_payload["DocumentLines"].append(freight_lineitem)
        order_doc.save()
    SAPsession =  AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes" #DeliveryNotes
    response1 = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    print('response is --- ',str(response1)[:20])
    ####response docNum to be collected and pushed into the data point of the order-
    ## DocType using a loop in the list - open doctype and writing data  ## 
    return response1.json()


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

@frappe.whitelist()
def post_delivery_note(startDate=None,endDate=None):
    """
    This function will go through each channel -- get completed order list send to create a single invoice out of orderlist-per-channel'
    """
    channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','HN_SITE_IN','DOGSEE_SITE_IN','ONDC_NSTORE']
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON
    # C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {'Snapdeal'      : 'C02574',
                                    'Amazon_IN_API' : 'C01186',
                                    'CRED'          : 'C03358',
                                    'FLIPKART'      : 'C03121',
                                    'HN_SITE_IN'    : 'C01026',
                                    'DOGSEE_SITE_IN': 'C00623', 
                                    'ONDC_NSTORE'   :'C03494',
                                    
                                    
                                    }

    for channel_id in channel_list: #need to change
        print ('Customer is : ', channel_id)
        print ('startDate: ',startDate,'endDate : ',endDate)
        if startDate or endDate:
            SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_id,'state':'KA','sap_delivery_docnum':"",
                                            'displayorderdatetime':('between',[startDate,endDate])},
                                            pluck='name') #
            IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_id,'state':('not in',['KA']),'sap_delivery_docnum':"",
                                            'displayorderdatetime':('between',[startDate,endDate])},
                                            pluck='name') #
        else:
            SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_id,'state':'KA',
                                            'sap_delivery_docnum':""},
                                            pluck='name') #
            IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_id,'state':('not in',['KA']),
                                            'sap_delivery_docnum':""},
                                            pluck='name') #
        CustomerCode_from_channel = Channel_CustomerCode_mapping[channel_id]
        
        print ('SGST_orders : ',len(SGST_orders))
        print ('IGST_orders : ',len(IGST_orders))

        # LOCAL ORDERS
        if len(SGST_orders)>0 :
            print ('SGST_orders : ',SGST_orders)
            bill_to_code = 'B2C SGST ADD'
            Delivery_response = delivery_from_orderlist(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
            if Delivery_response.get('error') is None:
                print("SGST_orders - Delivery_response['DocNum']",Delivery_response['DocNum'])
                for singledoc in SGST_orders:#[2:4]:
                    order_doc = frappe.get_doc('Unicommerce Orders', singledoc['name'])  #order_doc.sap_delivery_no
                    #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                    order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                    for lineitem in order_doc.line_items:
                        lineitem.sap_delivery_no = Delivery_response['DocNum']
                    order_doc.save()
            elif Delivery_response.get('error') is not None:
                print (Delivery_response['error'])
            #frappe.db.commit()

        #Outside state orders
        if len(IGST_orders)>0:
            print('IGST_orders : ',IGST_orders)
            bill_to_code = 'B2C IGST ADD'
            Delivery_response = delivery_from_orderlist(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
            if Delivery_response.get('error') is None:
                print("IGST_orders - Delivery_response['DocNum']",Delivery_response['DocNum'])
                for singledoc in IGST_orders:#[2:4]:
                    order_doc = frappe.get_doc('Unicommerce Orders', singledoc['name'])  #order_doc.sap_delivery_no
                    order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                    for lineitem in order_doc.line_items:
                        lineitem.sap_delivery_no = Delivery_response['DocNum']
                    order_doc.save()
                    frappe.db.commit()
            elif Delivery_response.get('error') is not None:
                print (Delivery_response['error'])
            #frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    return None
#######################################################################################################################################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################
#######################################################################################################################################################################################
@frappe.whitelist()
def Channel_post_delivery_note(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list send to create a single invoice out of it'
    """
    
    channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART']
    channel_id = Channel_Name
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {'Snapdeal' : 'C02574','Amazon_IN_API':'C01186','CRED':'C03358','FLIPKART':'C03121'}
    print ('Customer is : ', channel_id)
    print ('startDate: ',startDate)
    print('endDate : ',endDate)
    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':'KA','sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startDate,endDate])},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':('not in',['KA']),'sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startDate,endDate])},
                                        pluck='name') #
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':('not in',['KA']),
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
    CustomerCode_from_channel = Channel_CustomerCode_mapping[channel_id]
    
    print ('SGST_orders : ',len(SGST_orders))
    print ('IGST_orders : ',len(IGST_orders))

    # LOCAL ORDERS
    if len(SGST_orders)>0 :
        bill_to_code = 'B2C SGST ADD'
        Delivery_response = delivery_from_orderlist(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
        if Delivery_response.get('error') is None:
            print("SGST_orders - Delivery_response['DocNum']    ",Delivery_response['DocNum'])
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            print (Delivery_response['error'])
        #frappe.db.commit()

    #Outside state orders
    if len(IGST_orders)>0:
        bill_to_code = 'B2C IGST ADD'
        Delivery_response = delivery_from_orderlist(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
        if Delivery_response.get('error') is None:
            print("IGST_orders - Delivery_response['DocNum']     ",Delivery_response['DocNum'])
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            print (Delivery_response['error'])
            #frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    return None
###################################################################################################################################################################################################
#@frappe.whitelist()
def Update_inventory_level():
    """
    Update Inventory transfers from SAP to Khanal Tech Integrations 
    """
    # INITIALIZATION
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    reqUrl = doc_settings.sap_b1_url+"SQLQueries('ECB2CwhseBatchQuantity')/List" #Item batch Quantity from EC-G will be changed only
    
    response = session.request("GET", reqUrl, headers=headersList,verify=False)
    Query_results = dict(response.json())
    next_page = Query_results.get("odata.nextLink",None)

    while next_page is not None:
        session = AuthenticateSAPB1()
        if Query_results['value'] is not None:
            for single_query_values in Query_results['value']:
                if frappe.db.exists("Inventory in Whse", single_query_values['ItemCode']+'-'+single_query_values['DistNumber']+'-'+single_query_values['WhsCode']):
                    doc = frappe.get_doc("Inventory in Whse", single_query_values['ItemCode']+'-'+single_query_values['DistNumber']+'-'+single_query_values['WhsCode'])
                else:
                    doc = frappe.new_doc('Inventory in Whse')
                print(single_query_values['ItemCode'])    
                doc.itemcode   = single_query_values['ItemCode']
                doc.mnfdate    = single_query_values['MnfDate']
                doc.distnumber = single_query_values['DistNumber']
                doc.expdate    = single_query_values['ExpDate']
                doc.whscode    = single_query_values['WhsCode']
                doc.quantity   = str(single_query_values['Quantity'])
                try:
                    doc.save()
                    #frappe.db.commit()
                except Exception as e:
                    print (e)

        session = AuthenticateSAPB1()
        reqUrl = doc_settings.sap_b1_url+"" + next_page
        print(next_page)
        response = session.request("GET", reqUrl,  headers=headersList,verify=False)
            
        Query_results = dict(response.json())
        next_page = Query_results.get("odata.nextLink",None)
        #frappe.db.commit()
    frappe.msgprint(msg='Data Inserted successfully',title='Success')
    return None

def Get_FirstExpiry_Batch(itemsku,Req_Quantity=None): #itemcode and quantity needed
    All_batchwise_itemlist = frappe.db.get_list('Inventory in Whse', 
                                                 filters={'whscode'  : 'EC-B2C',
                                                          'quantity':     ['>=', int(Req_Quantity)],
                                                          'itemcode' : str(itemsku)
                                                          },
                                                 order_by='expdate'
                                                ) 
    if len(All_batchwise_itemlist)>0:
        Single_Batch_Doc = frappe.get_doc('Inventory in Whse', All_batchwise_itemlist[0]['name'])
        Soon_to_Be_Expired_Batch = Single_Batch_Doc.distnumber
        
        Single_Batch_Doc.quantity = int(float(Single_Batch_Doc.quantity)) -  int(Req_Quantity) #substracting one item as it has been used
        Single_Batch_Doc.save()
        frappe.db.commit()
        return Soon_to_Be_Expired_Batch
    else:
        return None # Return empty handed

def get_GST(origin_state,dest_state,item_code):
    session = AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    reqUrl = doc_settings.sap_b1_url+"States?$select=Code&$filter=startswith(Country,'IN') and startswith(Name,'"+ origin_state +"')"
    response = session.request("GET", reqUrl, headers=headersList,verify=False)
    state_code = dict(response.json())['value'][0]['Code']
    reqUrl = doc_settings.sap_b1_url+"Items?$select=ItemCode,ItemName,ForeignName,U_TaxRate&$filter=startswith(ItemCode, '" + item_code +"') &$orderby=ItemCode"
    response = session.request("GET", reqUrl, headers=headersList,verify=False)
    tax_rate = dict(response.json())['value'][0]['U_TaxRate']
    

    if state_code == 'KT':
        state_code = 'KA'
    if state_code==dest_state:
        tax_type = 'CS'
    else:
        tax_type = 'IG'
    gst_code = state_code + tax_type + str(int(tax_rate))
    return gst_code

def get_customer_address(Cardcode,bill_to_code):
    SAPsession =  AuthenticateSAPB1()
    payload = ''     #
    headersList = {
                "Accept": "*/*","User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Content-Type": "application/json" 
                  }
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"BusinessPartners('"+ str(Cardcode)  + "')"
    response = SAPsession.request("GET", invoice_Url, data=json.dumps(payload),  headers=headersList,verify=False)
    resdict = response.json()
    The_State = 'KA'
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
    return [The_State, Bill_to_value ]


##########################################################################################

# All_batchwise_itemlist = frappe.db.get_list('Inventory in Whse', filters={'whscode'  : 'EC-FG'  },fields=['itemcode', 'quantity'] ) 
from collections import defaultdict,Counter
@frappe.whitelist()
def get_pivoted_whseLevel():
    itemlist = frappe.db.get_list('Inventory in Whse', filters={'whscode'  : 'EC-FG'  },fields=['itemcode', 'quantity'] ) 
    intfy = [ {'itemcode':i['itemcode'],'W_quantity':int(float((i['quantity'])))} for i in itemlist ]
    dd =  defaultdict(Counter)
    for product in intfy:
        levels = {k: v for k, v in product.items() if k != "itemcode"}
        dd[product["itemcode"]].update(levels)
    ########Summarized_LIST
    list1 = [{**{"itemcode": k}, **v} for k, v in dd.items()]
    listt = [{i['itemcode']:i['W_quantity']} for i in list1 ]
    return listt

@frappe.whitelist()
def get_channel_pivoted_itemlist(channel_name=None,startDate=None,endDate=None):
    All_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                                    'channel_name': channel_name,'sap_delivery_docnum':"",
                                                    'displayorderdatetime':('between',[startDate,endDate])},
                                            fields=['shippingpackages']) #
    ALL_item_list       = []
    for single_order_item in All_orders:
        temp_dict       = json.loads(single_order_item['shippingpackages'])
        temp_dict_items = list(temp_dict['items'].values())
        ALL_item_list.append(temp_dict_items)
    ##################--itemName,itemSku,quantity
    # frappe.log_error('ALL_item_list',ALL_item_list)
    flat_list = [item for sublist in ALL_item_list for item in sublist]
    # frappe.log_error('flat_list',flat_list)
    Itemcode_quantity_list = [{'SKU_code':i['itemSku'],'Order_Quantity':i['quantity']} for i in flat_list ]
    ##################
    dd =  defaultdict(Counter)
    for product in Itemcode_quantity_list:
        levels = {k: v for k, v in product.items() if k != "SKU_code"}
        dd[product["SKU_code"]].update(levels)
    ########Summarized_LIST
    list2 = [{**{"SKU_code": k}, **v} for k, v in dd.items()]
    # frappe.log_error('list2',list2)
    return list2
    
        
@frappe.whitelist()
def comparision_orders_stock(channel_name=None,startDate=None,endDate=None):
    channel_items   = get_channel_pivoted_itemlist(channel_name=channel_name,startDate=startDate,endDate=endDate)
    inventory_items = get_pivoted_whseLevel() #{'FGHNXXX' : quantity}
    inventory_dict  = dict(ChainMap(*inventory_items))
    # frappe.log_error('inventory_dict',inventory_dict)
    ####################channelitems - {'SKU_code':'FGHNXXXX' ,'Order_Quantity':'Quantity'}
    the_comparision_list = []
    for single_dict in channel_items:
        if inventory_dict.get(single_dict['SKU_code']) is not None:
            single_dict['Whse_quantitiy'] = inventory_dict[single_dict['SKU_code']]
            the_comparision_list.append(single_dict)
        else:
            single_dict['Whse_quantitiy'] = 0
            the_comparision_list.append(single_dict)
    ###############
    frappe.log_error('the_compa÷rision_list',the_comparision_list)
    sendmail(msg=the_comparision_list)
    return the_comparision_list 


####### {'SKU_code':'FGHNXXXX' ,'Order_Quantity':'Quantity','Whse_Quantity':'Quantity3'}
    
#comparision_orders_stock(channel_name='Amazon_IN_API',startDate='2023-01-01',endDate='2023-01-01')
    
# Channel_post_delivery_note(Channel_Name=None,startDate=None,endDate=None):
# bench --site khanaltech.com execute  --args "{ '30' }"  khanal_tech_integrations.utils.logistics.delivery_notes.manual_update
# bench --site khanaltech.com execute  --args "{'CRED','2023-02-16', '2023-02-20'}"  khanal_tech_integrations.utils.sap.Channel_post_delivery_note
# Channel_post_delivery_note('CRED','2023-01-01', '2023-01-01')

bundle_items = {'FGHN0213':[{'ItemCode':'FGHN0072','Quantity':1},
                            {'ItemCode':'FGHN0099','Quantity':1},],
                'FGHN0174':[{'ItemCode':'FGHN0025','Quantity':2},],
                'FGHN0164':[{'ItemCode':'FGHN0025','Quantity':4},],
                 'FGHN0162':[{'ItemCode':'FGHN0015','Quantity':4},],
                 'FGHN0212':[{'ItemCode':'FGHN0072','Quantity':1},
                            {'ItemCode':'FGHN0026','Quantity':1},],
                 'FGHN0167':[{'ItemCode':'FGHN0079','Quantity':2},],
                 'FGHN0214':[{'ItemCode':'FGHN0079','Quantity':1},
                            {'ItemCode':'FGHN0082','Quantity':1},],
                 'FGHN0215':[{'ItemCode':'FGHN0079','Quantity':1},
                            {'ItemCode':'FGHN0075','Quantity':1},],
                 'FGHN0211':[{'ItemCode':'FGHN0079','Quantity':1},
                            {'ItemCode':'FGHN0074','Quantity':1},],
                 'FGDC0274':[{'ItemCode':'FGDC0063','Quantity':4},],
                 'FGDC0273':[{'ItemCode':'FGDC0063','Quantity':2},],
                 'FGDC0273':[{'ItemCode':'FGDC0031','Quantity':2},],
                }
@frappe.whitelist()
def delivery_from_orderlist1(channel,completed_orderlist,bill_to_code,startDate,endDate):
    Channel_Mapping = {'C02574': 'Snapdeal',  
                       'C01186': 'Amazon_IN_API', 
                       'C03358': 'CRED',  
                       'C03121': 'FLIPKART',
                       'C00623'  :'DOGSEE_SITE_IN',
                       'C01026': 'HN_SITE_IN',
                       'C03494': 'ONDC_NSTORE',
                                    }
    Channel_Name = Channel_Mapping[str(channel)]
    origin_state = 'Karnataka' #State Code hard coded for now 
    extra = None
    ##TODO: To update the state code dynamically
    if bill_to_code     == 'B2C SGST ADD':
        Bill_to         = 'Local'
        account_code    = '41106001'
        shipping_tax_code = 'KACS18'
        extra           = 'Intra-State'

    elif bill_to_code == 'B2C IGST ADD':
        Bill_to         = 'Central'
        account_code    = '41106002'
        shipping_tax_code = 'KAIG18'
        extra           = 'Inter-State'

    comment = str(extra) +  "Dispatched B2C orders for {} from {} to {} Posted Using API".format(Channel_Name,startDate,endDate)
    print(comment)

    Delivery_payload = { "CardCode"      : str(channel), 
                         "Comments"      : comment,
                         "PayToCode"     : bill_to_code,
                         "ShipToCode"    : bill_to_code,
                         "DocDate"       : startDate, #frappe.utils.nowdate(),# endDate,  #EndDate of the date will be when the doc is posted 
                        "DocDueDate"     : endDate,  
                         "U_BillingFrom" : 'KT',
                         'U_BillTo'      : Bill_to,
                         "UseBillToAddrToDetermineTax": 'tYES',#(Tick Marking)
                         "DocumentLines": []}
    # Delivery_payload['EWayBillDetails']["BillToStateGSTCode"] = state_code
    LineNum_Count = 0
    Delivery_payload["DocumentLines"] = []
    for single_order in completed_orderlist:
        order_doc = frappe.get_doc('Unicommerce Orders', single_order)
        lineitemss = order_doc.line_items #  
        for itemss in lineitemss:
            lineitem_delivery = { "LineNum": 0,
                        "ItemCode"      : None,
                        "AccountCode"   : account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                        'WarehouseCode' : 'EC-B2C',
                        "Quantity"      : "1",
                        "TaxCode"       : "GST@12", # Will changed for specific items
                        'TaxType'       : 'tt_Yes',  
                        'TaxLiable'     : 'tYES',
                        'TaxTotal'      : 0.0,      
                        "UnitPrice"     : None,
                        'U_BuyerName'   : None,  #Channel_name
                        'U_Order'       : None,
                        'U_OrderID'     : None, 
                        'U_OrderedOn'   : None,
                        'U_City'        : None,
                        'U_State'       : None, 
                        'U_PINCode'     : None, 
                        'U_Country'     : 'India',
                        'BatchNumbers'  : [{'BatchNumber'   : 'PLACEHOLDER_BATCH',
                                            "Quantity"      : 1  }]  }
            if itemss.itemsku  in bundle_items_CFG.keys():
                individual_item_BOM = bundle_items_CFG[itemss.itemsku]
                CFG_Item    , *_    = individual_item_BOM.keys()
                child_Items , *_    = individual_item_BOM.values()
                lineitem_delivery1  = lineitem_delivery.copy()
                lineitem_delivery1['LineNum']   = LineNum_Count
                itemss.delivery_linenum         = LineNum_Count + 1    #filling the LineNum value(It will be the counting on frontEND SAP)
                lineitem_delivery1['ItemCode']  = CFG_Item    
                lineitem_delivery1['Quantity']  = itemss.quantity
                # lineitem_delivery['UnitPrice'] = itemss.total_price
                lineitem_delivery1['UnitPrice'] = float(itemss.selling_price)-float(itemss.totalintegratedgst)
                lineitem_delivery1['TaxCode']   =  get_GST(origin_state,order_doc.state,itemss.itemsku)#'GST@' + str(itemss.integratedgstpercentage) 
                lineitem_delivery1['U_BuyerName'] = order_doc.customer_name
                lineitem_delivery1['U_Order']   = order_doc.uniware_id
                lineitem_delivery1['U_City']    = order_doc.city
                lineitem_delivery1['U_State']   = order_doc.state
                lineitem_delivery1['U_OrderedOn'] = str(order_doc.created)[:10] #justThe Date
                lineitem_delivery1['U_PINCode'] = order_doc.pin_code
                lineitem_delivery1['U_Country'] = 'India'
                lineitem_delivery1['TreeType']  = 'iSalesTree' #Is a NON-INVENTORY ITEM
                lineitem_delivery1.pop('BatchNumbers')
                Delivery_payload["DocumentLines"].append(lineitem_delivery1)
                LineNum_Count += 1
                #Add sku as SalesItemTREEgit 
                #PRICE as suggested
                #BATch code removed 
                for childItem in child_Items:
                    lineitem_delivery2 = lineitem_delivery = { "LineNum": 0,
                                                "ItemCode"      : None,
                                                "AccountCode"   : account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                                                'WarehouseCode' : 'EC-B2C',
                                                "Quantity"      : "1",
                                                "TaxCode"       : "GST@12", #Will changed for specific items
                                                'TaxType'       : 'tt_Yes',  
                                                'TaxLiable'     : 'tYES',
                                                'TaxTotal'      : 0.0,      
                                                "UnitPrice"     : None,
                                                'U_BuyerName'   : None,  #Customer_name
                                                'U_Order'       : None,
                                                'U_OrderID'     : None, 
                                                'U_OrderedOn'   : None,
                                                'U_City'        : None,
                                                'U_State'       : None, 
                                                'U_PINCode'     : None, 
                                                'U_Country'     : 'India',
                                                'BatchNumbers'  : [{'BatchNumber'   : 'PLACEHOLDER_BATCH',
                                                                      "Quantity"    : 1  }]
                                                    }
                    lineitem_delivery2['LineNum']        = LineNum_Count
                    itemss.delivery_linenum              = LineNum_Count + 1    #filling the LineNum value(It will be the counting on frontEND SAP
                    lineitem_delivery2['ItemCode']       = childItem['ItemCode'] 
                    print( 'ChildItem is --- ---> ', childItem['ItemCode'] ,childItem['Quantity'])
                    lineitem_delivery2['Quantity']       = int(childItem['Quantity'] )#* itemss.quantity
                    lineitem_delivery2['UnitPrice']      = None
                    lineitem_delivery2['TaxCode']        = get_GST(origin_state,order_doc.state,childItem['ItemCode'] )#'GST@' + str(itemss.integratedgstpercentage) 
                    lineitem_delivery2['U_BuyerName']    = order_doc.customer_name
                    lineitem_delivery2['U_Order']        = order_doc.uniware_id
                    lineitem_delivery2['U_City']         = order_doc.city
                    lineitem_delivery2['U_State']        = order_doc.state
                    lineitem_delivery2['U_OrderedOn']    = str(order_doc.created)[:10] #justThe Date
                    lineitem_delivery2['U_PINCode']      = order_doc.pin_code
                    lineitem_delivery2['U_Country']      = 'India'
                    lineitem_delivery2['TreeType']       = 'iIngredient' #Is a NON-INVENTORY ITEM
                    batch_assigned                       =  Get_FirstExpiry_Batch(str( childItem['ItemCode'] ),Req_Quantity= childItem['Quantity']  )
                    # print(batch_assigned)
                    if batch_assigned:
                        lineitem_delivery2['BatchNumbers'][0]['BatchNumber']     =  batch_assigned   #'G5H106I27I'    
                        lineitem_delivery2['BatchNumbers'][0]['Quantity']        =  int(childItem['Quantity'] )    #'G5H106I27I'   
                        Delivery_payload["DocumentLines"].append(lineitem_delivery2)
                        LineNum_Count += 1 
                        order_doc.save()
                    else:
                        print (itemss.itemsku, ' out of stock') # NEED BETTER WAY TO HANDLE THIS
                        return {'Error : Childitems - '  : childItem['ItemCode'] + ' out of stock'}
                    # Delivery_payload["DocumentLines"].append(lineitem_delivery2) #appending as a lineitems inside inv_payload dictionary
                    # LineNum_Count += 1 #increasing the counter
                    #Connect SKU
                    #add as ChildItem
                    #LineItem increment
            else:
                lineitem_delivery['LineNum']        = LineNum_Count
                itemss.delivery_linenum             = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
                lineitem_delivery['ItemCode']       = itemss.itemsku 
                lineitem_delivery['Quantity']       = itemss.quantity
                # lineitem_delivery['UnitPrice']      = itemss.total_price
                lineitem_delivery['UnitPrice']      = float(itemss.selling_price)-float(itemss.totalintegratedgst)
                lineitem_delivery['TaxCode']        =  get_GST(origin_state,order_doc.state,itemss.itemsku)#'GST@' + str(itemss.integratedgstpercentage) 
                lineitem_delivery['U_BuyerName']    = order_doc.customer_name
                lineitem_delivery['U_Order']        = order_doc.uniware_id
                lineitem_delivery['U_City']         = order_doc.city
                lineitem_delivery['U_State']        = order_doc.state
                lineitem_delivery['U_OrderedOn']    = str(order_doc.created)[:10] #justThe Date
                lineitem_delivery['U_PINCode']      = order_doc.pin_code
                lineitem_delivery['U_Country']      =  'India'
                batch_assigned = Get_FirstExpiry_Batch(str(itemss.itemsku),Req_Quantity=itemss.quantity)
                if batch_assigned:
                    lineitem_delivery['BatchNumbers'][0]['BatchNumber']     =  batch_assigned   #'G5H106I27I'    
                    lineitem_delivery['BatchNumbers'][0]['Quantity']        =  itemss.quantity     #'G5H106I27I'   
                else:
                    # print (itemss.itemsku, ' out of stock')
                    # NEED BETTER WAY TO HANDLE THIS
                    return {'Error ': itemss.itemsku + ' out of stock.'}
                
                Delivery_payload["DocumentLines"].append(lineitem_delivery) #appending as a lineitems inside inv_payload dictionary
                LineNum_Count += 1 #increasing the counter
                #Here the shipping charge will be added as a freight line_item
                if float(itemss.shippingcharges)>0:
                    freight_lineitem = {} #lineitem_delivery.copy()
                    freight_lineitem['LineNum']         = LineNum_Count 
                    freight_lineitem['ItemCode']        = 'EXCM0027'
                    freight_lineitem['TaxCode']         = shipping_tax_code  #18% GST fixed for all freight charge
                    freight_lineitem['UnitPrice']       = itemss.shippingcharges
                    freight_lineitem['WarehouseCode']   = 'EC-B2C'
                    freight_lineitem['U_BuyerName']     = order_doc.customer_name
                    freight_lineitem['U_Order']         =  order_doc.uniware_id
                    freight_lineitem['U_City']          = order_doc.city
                    freight_lineitem['U_State']         = order_doc.state
                    freight_lineitem['U_OrderedOn']     = str(order_doc.created)[:10] #justThe Date
                    freight_lineitem['U_PINCode']       = order_doc.pin_code
                    freight_lineitem['U_Country']       = 'India'
                    LineNum_Count += 1 #increasing the counter again
                    Delivery_payload["DocumentLines"].append(freight_lineitem)
            order_doc.save()
            frappe.db.commit()
    print('Numbers of Lineitem in delivery payload : ',  len(Delivery_payload['DocumentLines']))
    SAPsession =  AuthenticateSAPB1()
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes" #DeliveryNotes
    response1 = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    #### Response docNum to be collected and pushed into the data point of the order-
    #### DocType using a loop in the list - open doctype and writing data  ## 
    resDict = response1.json()
    if resDict.get('DocNum') is not None:
        for singledoc in completed_orderlist:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = resDict['DocNum']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = resDict['DocNum']
                order_doc.save()
                frappe.db.commit()
    return resDict

#delivery_from_orderlist1(channel='C03358',completed_orderlist=['8J4V03PVNEY','404-6306238-2539517'],bill_to_code='B2C IGST ADD',startDate='2023-03-01',endDate='2023-03-03')

@frappe.whitelist()
def sendmail(msg):
    recipients=['buddhiraj@khanalfoods.com','shahil@khanalfoods.com','harsha@khanalfoods.com','yogesha@khanalfoods.com']
    title="Missing Quantity Unicommerce"
    missing_Qty=[]
    for item in msg:
        sku_code = item['SKU_code']
        order_quantity = item['Order_Quantity']
        whse_quantity = item['Whse_quantitiy']

        if order_quantity > whse_quantity:
            missing_item = {'sku_code': sku_code, 'order_quantity': order_quantity, 'whse_quantity': whse_quantity}
            missing_Qty.append(missing_item)
        else:
            pass
    if missing_Qty:
    # create HTML table with some CSS for spacing
        table = "<table style='border-collapse: collapse; margin-top: 10px;'><tr><th style='border: 1px solid black; padding: 5px;'>SKU Code</th><th style='border: 1px solid black; padding: 5px;'>Order Quantity</th><th style='border: 1px solid black; padding: 5px;'>Warehouse Quantity</th></tr>"
        for item in missing_Qty:
            table += f"<tr><td style='border: 1px solid black; padding: 5px;'>{item['sku_code']}</td><td style='border: 1px solid black; padding: 5px;'>{item['order_quantity']}</td><td style='border: 1px solid black; padding: 5px;'>{item['whse_quantity']}</td></tr>"
        table += "</table>"

        email_args={
            "recipients":recipients,
            "message":table,
            "subject":title,
            # "message_type": "html"
        }
        frappe.enqueue(method=frappe.sendmail,queue='short',timeout=300, **email_args)
    else:
        pass

def DN_manual_entry(channel_name,startdate=None,enddate=None,docnum=None,igst=True):
    if igst == True:
        ls = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_name,'state':('not in',['KA']),'sap_delivery_docnum':"",
                                            'displayorderdatetime':('between',[startdate,enddate])},
                                            pluck='name') #IGST
        
    else:
        ls = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_name,'state':'KA','sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startdate,enddate])},
                                        pluck='name') #SGST
        
        print('length of this list is',len(ls))
    for ord in ls:
        doc = frappe.get_doc('Unicommerce Orders',ord)
        doc.sap_delivery_docnum = docnum
        doc.save()
        frappe.db.commit()
    return "MODIFIED"
bundle_items_CFG = {
                'FGDC0032':{'CFGDC0001':[{'ItemCode':'FGDC0031','Quantity':3},]}, 
                'FGDC0033':{'CFGDC0002':[{'ItemCode':'FGDC0031','Quantity':5},]},     
                'FGDC0064':{'CFGDC0003':[{'ItemCode':'FGDC0063','Quantity':3},]},   
                'FGDC0065':{'CFGDC0004':[{'ItemCode':'FGDC0063','Quantity':5},]},  
                'FGDC0201':{'CFGDC0005':[{'ItemCode':'FGDC0055','Quantity':3},]},  
                'FGDC0039':{'CFGDC0006':[{'ItemCode':'FGDC0038','Quantity':3},]},  
                'FGDC0040':{'CFGDC0007':[{'ItemCode':'FGDC0038','Quantity':5},]}, 
                'FGDC0077':{'CFGDC0008':[{'ItemCode':'FGDC0076','Quantity':3},]},  
                'FGDC0092':{'CFGDC0009':[{'ItemCode':'FGDC0091','Quantity':3},]}, 
                'FGDC0098':{'CFGDC0010':[{'ItemCode':'FGDC0097','Quantity':3},]},  
                'FGDC0119':{'CFGDC0011':[{'ItemCode':'FGDC0118','Quantity':3},]}, 
                'FGDC0200':{'CFGDC0012':[{'ItemCode':'FGDC0049','Quantity':3},]}, 
                'FGDC0086':{'CFGDC0013':[{'ItemCode':'FGDC0085','Quantity':3},]}, 
                'FGDC0087':{'CFGDC0014':[{'ItemCode':'FGDC0085','Quantity':5},]}, 
                'FGDC0099':{'CFGDC0015':[{'ItemCode':'FGDC0097','Quantity':5},]}, 
                'FGDC0112':{'CFGDC0016':[{'ItemCode':'FGDC0111','Quantity':3},]}, 
                'FGDC0132':{'CFGDC0017':[{'ItemCode':'FGDC0131','Quantity':3},]}, 
                ###################################################################
                'FGHN0106':{'CFGHN0001':[{'ItemCode':'FGHN0015','Quantity':5},]}, 
                'FGHN0107':{'CFGHN0003':[{'ItemCode':'FGHN0025','Quantity':3},]}, 
                'FGHN0108':{'CFGHN0004':[{'ItemCode':'FGHN0025','Quantity':5},]},
                'FGHN0126':{'CFGHN0002':[{'ItemCode':'FGHN0015','Quantity':2},]},
                'FGHN0122':{'CFGHN0005':[{'ItemCode':'FGHN0094','Quantity':3},]},
                'FGHN0124':{'CFGHN0006':[{'ItemCode':'FGHN0058','Quantity':2},]}, 
                'FGHN0118':{'CFGHN0007':[{'ItemCode':'FGHN0059','Quantity':1},
                                         {'ItemCode':'FGHN0058','Quantity':1},]}, 
                'FGHN0120':{'CFGHN0008':[{'ItemCode':'FGHN0015','Quantity':1},
                                         {'ItemCode':'FGHN0025','Quantity':1},
                                         {'ItemCode':'FGHN0041','Quantity':1},]},  
                'FGHN0056':{'CFGHN0009':[{'ItemCode':'FGHN0054','Quantity':3},]},  
                'FGHN0105':{'CFGHN0010':[{'ItemCode':'FGHN0015','Quantity':3},]},  
                'FGHN0113':{'CFGHN0011':[{'ItemCode':'FGHN0041','Quantity':2},]},  
                'FGHN0125':{'CFGHN0012':[{'ItemCode':'FGHN0054','Quantity':5},]},  
                'FGHN0119':{'CFGHN0013':[{'ItemCode':'FGHN0015','Quantity':1},
                                         {'ItemCode':'FGHN0025','Quantity':1},]},  
                'FGHN0123':{'CFGHN0014':[{'ItemCode':'FGHN0039','Quantity':1},
                                         {'ItemCode':'FGHN0030','Quantity':1},]},  
                'FGHN0128':{'CFGHN0015':[{'ItemCode':'FGHN0030','Quantity':1}, 
                                         {'ItemCode':'FGHN0039','Quantity':1},
                                         {'ItemCode':'FGHN0086','Quantity':1},
                                         {'ItemCode':'FGHN0096','Quantity':1},]},  }
@frappe.whitelist()
def Channel_post_delivery_note1(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list send to create a single invoice out of it'
    """
    channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','DOGSEE_SITE_IN','HN_SITE_IN','ONDC_NSTORE']
    channel_id = Channel_Name
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {'Snapdeal'      : 'C02574',
                                    'Amazon_IN_API' : 'C01186',
                                    'CRED'          : 'C03358',
                                    'FLIPKART'      : 'C03121',
                                    'DOGSEE_SITE_IN': 'C00623',
                                    'HN_SITE_IN'    : 'C01026',
                                    'ONDC_NSTORE'   : 'C03494',
                                    }
    print ('Customer is : ', channel_id)
    print ('startDate: ',startDate)
    print('endDate : ',endDate)
    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
                                        'channel_name': channel_id,'state':'KA','sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startDate,endDate])},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
                                        'channel_name': channel_id,'state':('not in',['KA']),'sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startDate,endDate])},
                                        pluck='name') #
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
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
        Delivery_response = delivery_from_orderlist1(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        print('PUSHING SGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("***********SGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
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
     
        Delivery_response = delivery_from_orderlist1(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        print('PUSHING IGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("**********IGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['error']
            print (Delivery_response['error'])
            print ('ERROR',Delivery_response)
            #frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    # Sending mail about the result
    return Summary_Dict

def Unicommerce_Automate():
    Today = frappe.utils.nowdate()
    start = add_to_date(Today,days=-2)
    # FilterDate = add_to_date(Today,days=-2)
    Channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','DOGSEE_SITE_IN','HN_SITE_IN','ONDC_NSTORE']
    for single_channel in Channel_list:
        Comparision_check = comparision_orders_stock(channel_name=single_channel,startDate=start,endDate=start)
        missing_Qty = []
        for item in Comparision_check:
            sku_code = item['SKU_code']
            order_quantity = item['Order_Quantity']
            whse_quantity = item['Whse_quantitiy']

        if order_quantity > whse_quantity:
            missing_item = {'sku_code': sku_code, 'order_quantity': order_quantity, 'whse_quantity': whse_quantity}
            missing_Qty.append(missing_item)
        else:
            pass
    ##################
        if missing_Qty:
            pass
        else:
            Push_result = Channel_post_delivery_note1(Channel_Name=single_channel,startDate=start,endDate=start)
            #Sending Mail
            title = 'The DeliveryNote details for '+str(single_channel) + 'From Date :'+ str(start) +'Start Date :'+  str(start) 
            DNsendmail(DICT = Push_result,Title=title)
    return Push_result
        
        
        
#############    

@frappe.whitelist()
def DNsendmail(DICT,Title=None):
    recipients=['buddhiraj@khanalfoods.com','mratyunjay@khanalfoods.com','shahil@khanalfoods.com','harsha@khanalfoods.com','yogesha@khanalfoods.com']
    # create HTML table with some CSS for spacing
    table = "<table style='border-collapse: collapse; margin-top: 10px;'><tr><th style='border: 1px solid black; padding: 5px;'>Order_Type</th><th style='border: 1px solid black; padding: 5px;'>No of Orders</th><th style='border: 1px solid black; padding: 5px;'>DN_docnum</th></tr>"
    for item in DICT:
        table += f"<tr><td style='border: 1px solid black; padding: 5px;'>{item['Order_Type']}</td><td style='border: 1px solid black; padding: 5px;'>{item['No of Orders']}</td><td style='border: 1px solid black; padding: 5px;'>{item['DeliveryNote Docnum']}</td></tr>"
    table += "</table>"

    email_args={
        "recipients":recipients,
        "message":table,
        "subject":Title,
        # "message_type": "html"
                }
    frappe.enqueue(method=frappe.sendmail,queue='short',timeout=300, **email_args)
    return None

@frappe.whitelist()
def manual_inventory_update(Total:int=20) -> None :
    """
    Update Inventory Level from SAP to Frappe
    """
    
    print(Total,'Total')

    for i in range(Total):
        print(i,'count')
    # INITIALIZATION
        doc_settings = frappe.get_doc('SAP Settings')
        reqUrl        =  doc_settings.sap_b1_url+"SQLQueries('ECB2CwhseBatchQuantity')//List?&$skip="
        modfified_Url =  reqUrl + str(20*i)
        session       = AuthenticateSAPB1()
        response      = session.request("GET", modfified_Url,  headers=headersList,verify=False)
            
        QueryResult = dict(response.json())

        if QueryResult['value'] is not None:
            for single_query_values in QueryResult['value']:
                if frappe.db.exists("Inventory in Whse", single_query_values['ItemCode']+'-'+single_query_values['DistNumber']+'-'+single_query_values['WhsCode']):
                    doc = frappe.get_doc("Inventory in Whse", single_query_values['ItemCode']+'-'+single_query_values['DistNumber']+'-'+single_query_values['WhsCode'])
                else:
                    doc = frappe.new_doc('Inventory in Whse')
                #print(single_query_values['ItemCode'])    
                doc.itemcode   = single_query_values['ItemCode']
                doc.mnfdate    = single_query_values['MnfDate']
                doc.distnumber = single_query_values['DistNumber']
                doc.expdate    = single_query_values['ExpDate']
                doc.whscode    = single_query_values['WhsCode'] 
                doc.quantity   = str(single_query_values['Quantity'])
                try:
                    doc.save()
                    frappe.db.commit()
                except Exception as e:
                    print (e)
        #frappe.db.commit()
    frappe.msgprint(msg='Data Inserted successfully',title='Success')
    return None
##################


@frappe.whitelist()
def Channel_delivery_note_Skip(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list send to create a single invoice out of it'
    """
    channel_id = Channel_Name
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {'Snapdeal'      : 'C02574',
                                    'Amazon_IN_API' : 'C01186',
                                    'CRED'          : 'C03358',
                                    'FLIPKART'      : 'C03121',
                                    'HN_SITE_IN'    : 'C01026',
                                    'DOGSEE_SITE_IN': 'C00623', 
                                    'ONDC_NSTORE'   :'C03494',
                                    }
    print ('Customer is : ' , channel_id)
    print ('StartDate : '   ,  startDate)
    print ('EndDate : '     ,    endDate)
    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['CREATED','COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startDate,endDate])},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['CREATED','COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':('not in',['KA']),
                                        'sap_delivery_docnum':"",
                                        'displayorderdatetime':('between',[startDate,endDate])},
                                        pluck='name') #
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['CREATED','COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':""
                                        },
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['CREATED','COMPLETE', 'PROCESSING']), 
                                        'channel_name': channel_id,'state':('not in',['KA']),
                                        'sap_delivery_docnum':""
                                        },
                                        pluck='name') #
    CustomerCode_from_channel = Channel_CustomerCode_mapping[channel_id]
    
    print ('SGST_orders : ',len(SGST_orders))
    print ('SGST_orders : ',len(IGST_orders))
    
    Summary_Dict = [ {'Order_Type':'SGST Orders', 'No of Orders': len(SGST_orders),'DeliveryNote Docnum':None },
                     {'Order_Type':'IGST Orders', 'No of Orders': len(IGST_orders),'DeliveryNote Docnum':None } ]
    

    # LOCAL ORDERS
    if len(SGST_orders)>0 :
        bill_to_code = 'B2C SGST ADD'
        Delivery_response = SKIP_delivery_from_orderlist1(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        print('PUSHING SGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("***********SGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
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
     
        Delivery_response = SKIP_delivery_from_orderlist1(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        print('PUSHING IGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("**********IGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['error']
            print (Delivery_response['error'])
            print ('ERROR',Delivery_response)
            #frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    # Sending mail about the result
    return Summary_Dict
           
           
           
           
@frappe.whitelist()
def SKIP_delivery_from_orderlist1(channel,completed_orderlist,bill_to_code,startDate,endDate):
    Channel_Mapping = {'C02574': 'Snapdeal',  'C01186': 'Amazon_IN_API', 'C03358': 'CRED',  'C03121': 'FLIPKART',
                              'C01026' :'HN_SITE_IN' ,
                                     'C00623': 'DOGSEE_SITE_IN','C03494':'ONDC_NSTORE',   }
    Channel_Name = Channel_Mapping[str(channel)]
    origin_state = 'Karnataka' #State Code hard coded for now 
    extra = None
    ##TODO: To update the state code dynamically
    if bill_to_code == 'B2C SGST ADD':
        Bill_to = 'Local'
        account_code = '41106001'
        shipping_tax_code = 'KACS18'
        extra = 'Intra-state'

    elif bill_to_code == 'B2C IGST ADD':
        Bill_to = 'Central'
        account_code = '41106002'
        shipping_tax_code = 'KAIG18'
        extra = 'Inter-state'

    comment = str(extra) +  "Ecommerce B2C orders for {} from {} to {} Posted Using API from Unicommerce".format(Channel_Name,startDate,endDate)

    Delivery_payload = { "CardCode"      : str(channel), 
                         "Comments"      : comment,
                         "PayToCode"     : bill_to_code,
                         "ShipToCode"    : bill_to_code,
                         "DocDate"       : startDate, #frappe.utils.nowdate(),# endDate,  #EndDate of the date will be when the doc is posted 
                        "DocDueDate"    : endDate,  
                         "U_BillingFrom" : 'KT',
                         'U_BillTo'      : Bill_to,
                         "UseBillToAddrToDetermineTax": 'tYES',
                         #"PlaceOfSupply": PayToState, #Here i am inserting the State Code
                         "DocumentLines": []}
    # Delivery_payload['EWayBillDetails']["BillToStateGSTCode"] = state_code
    LineNum_Count = 0
    Delivery_payload["DocumentLines"] = []
    for single_order in completed_orderlist:
        order_doc = frappe.get_doc('Unicommerce Orders', single_order)
        lineitemss = order_doc.line_items #  
        for itemss in lineitemss:
            lineitem_delivery = { "LineNum": 0,
                        "ItemCode": None,
                        "AccountCode": account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                        'WarehouseCode': 'EC-B2C',
                        "Quantity": "1",
                        "TaxCode": "GST@12", # Will changed for specific items
                        'TaxType': 'tt_Yes',  
                        'TaxLiable': 'tYES',
                        'TaxTotal': 0.0,      
                        "UnitPrice": None,
                        'U_BuyerName': None,  #channel_name
                        'U_Order': None,
                        'U_OrderID': None, 
                        'U_OrderedOn': None,
                        'U_City': None,
                        'U_State': None, 
                        'U_PINCode': None, 
                        'U_Country': 'India',
                        'BatchNumbers': [{'BatchNumber': 'PLACEHOLDER_BATCH',
                                        "Quantity": 1  }]  }
            if itemss.itemsku  in bundle_items_CFG.keys() and itemss.delivery_linenum != "NA" :
                individual_item_BOM = bundle_items_CFG[itemss.itemsku]
                CFG_Item    , *_    = individual_item_BOM.keys()
                child_Items , *_    = individual_item_BOM.values()
                lineitem_delivery1  = lineitem_delivery.copy()
                lineitem_delivery1['LineNum']   = LineNum_Count
                itemss.delivery_linenum         = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
                lineitem_delivery1['ItemCode']  = CFG_Item    
                lineitem_delivery1['Quantity']  = itemss.quantity
                # lineitem_delivery1['UnitPrice'] = itemss.total_price
                lineitem_delivery1['UnitPrice']      = float(itemss.selling_price)-float(itemss.totalintegratedgst)
                lineitem_delivery1['TaxCode']   =  get_GST(origin_state,order_doc.state,itemss.itemsku)#'GST@' + str(itemss.integratedgstpercentage) 
                lineitem_delivery1['U_BuyerName'] = order_doc.customer_name
                lineitem_delivery1['U_Order']   = order_doc.uniware_id
                lineitem_delivery1['U_City']    = order_doc.city
                lineitem_delivery1['U_State']   = order_doc.state
                lineitem_delivery1['U_OrderedOn'] = str(order_doc.created)[:10] #justThe Date
                lineitem_delivery1['U_PINCode'] = order_doc.pin_code
                lineitem_delivery1['U_Country'] = 'India'
                lineitem_delivery1['TreeType']  = 'iSalesTree' #Is a NON-INVENTORY ITEM
                lineitem_delivery1.pop('BatchNumbers')
                Delivery_payload["DocumentLines"].append(lineitem_delivery1)
                LineNum_Count += 1
                #Add sku as SalesItemTREEgit 
                #PRICE as suggested
                #BATch code removed 
                for childItem in child_Items:
                    lineitem_delivery2 = lineitem_delivery = { "LineNum": 0,
                                                "ItemCode" : None,
                                                "AccountCode": account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                                                'WarehouseCode': 'EC-B2C',
                                                "Quantity": "1",
                                                "TaxCode": "GST@12", #Will changed for specific items
                                                'TaxType': 'tt_Yes',  
                                                'TaxLiable': 'tYES',
                                                'TaxTotal': 0.0,      
                                                "UnitPrice": None,
                                                'U_BuyerName': None,  #Customer_name
                                                'U_Order': None,
                                                'U_OrderID': None, 
                                                'U_OrderedOn': None,
                                                'U_City': None,
                                                'U_State': None, 
                                                'U_PINCode': None, 
                                                'U_Country': 'India',
                                                'BatchNumbers': [{'BatchNumber': 'PLACEHOLDER_BATCH',
                                                                "Quantity": 1  }]
                                                    }
                    lineitem_delivery2['LineNum']        = LineNum_Count
                    itemss.delivery_linenum              = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
                    lineitem_delivery2['ItemCode']       = childItem['ItemCode'] 
                    print( 'ChildItem is --- --- ---> ', childItem['ItemCode'] ,childItem['Quantity'])
                    lineitem_delivery2['Quantity']       = int(childItem['Quantity'] )#* itemss.quantity
                    lineitem_delivery2['UnitPrice']      = None
                    lineitem_delivery2['TaxCode']        = get_GST(origin_state,order_doc.state,childItem['ItemCode'] )#'GST@' + str(itemss.integratedgstpercentage) 
                    lineitem_delivery2['U_BuyerName']    = order_doc.customer_name
                    lineitem_delivery2['U_Order']        = order_doc.uniware_id
                    lineitem_delivery2['U_City']         = order_doc.city
                    lineitem_delivery2['U_State']        = order_doc.state
                    lineitem_delivery2['U_OrderedOn']    = str(order_doc.created)[:10] #justThe Date
                    lineitem_delivery2['U_PINCode']      = order_doc.pin_code
                    lineitem_delivery2['U_Country']      = 'India'
                    lineitem_delivery2['TreeType']       = 'iIngredient' #Is a NON-INVENTORY ITEM
                    batch_assigned                       =  Get_FirstExpiry_Batch(str( childItem['ItemCode'] ),Req_Quantity= childItem['Quantity']  )
                    # print(batch_assigned)
                    if batch_assigned:
                        lineitem_delivery2['BatchNumbers'][0]['BatchNumber']     =  batch_assigned   #'G5H106I27I'    
                        lineitem_delivery2['BatchNumbers'][0]['Quantity']        =  int(childItem['Quantity'] )    #'G5H106I27I'   
                        Delivery_payload["DocumentLines"].append(lineitem_delivery2)
                        LineNum_Count += 1 
                    else:
                        print (itemss.itemsku, ' out of stock-----') # NEED BETTER WAY TO HANDLE THIS
                        itemss.delivery_linenum              = "NA"
                        # return {'Error : Childitems - '  : childItem['ItemCode'] + ' out of stock'}
                    # Delivery_payload["DocumentLines"].append(lineitem_delivery2) #appending as a lineitems inside inv_payload dictionary
                    # LineNum_Count += 1 #increasing the counter
                    #Connect SKU
                    #add as ChildItem
                    #LineItem increment
            elif itemss.delivery_linenum != "NA" :
                lineitem_delivery['LineNum']        = LineNum_Count
                itemss.delivery_linenum             = LineNum_Count + 1    #filling the LineNum value(It will be the couting on frontEND SAP)
                lineitem_delivery['ItemCode']       = itemss.itemsku 
                print( lineitem_delivery['ItemCode'] )
                lineitem_delivery['Quantity']       = itemss.quantity
                # lineitem_delivery['UnitPrice']      = itemss.total_price
                lineitem_delivery1['UnitPrice']      = float(itemss.selling_price)-float(itemss.totalintegratedgst)
                lineitem_delivery['TaxCode']        =  get_GST(origin_state,order_doc.state,itemss.itemsku)#'GST@' + str(itemss.integratedgstpercentage) 
                lineitem_delivery['U_BuyerName']    = order_doc.customer_name
                lineitem_delivery['U_Order']        = order_doc.uniware_id
                lineitem_delivery['U_City']         = order_doc.city
                lineitem_delivery['U_State']        = order_doc.state
                lineitem_delivery['U_OrderedOn']    = str(order_doc.created)[:10] #justThe Date
                lineitem_delivery['U_PINCode']      = order_doc.pin_code
                lineitem_delivery['U_Country']      =  'India'
                batch_assigned = Get_FirstExpiry_Batch(str(itemss.itemsku),Req_Quantity=itemss.quantity)
                if batch_assigned:
                    lineitem_delivery['BatchNumbers'][0]['BatchNumber']     =  batch_assigned   #'G5H106I27I'    
                    lineitem_delivery['BatchNumbers'][0]['Quantity']        =  itemss.quantity     #'G5H106I27I'   
                    Delivery_payload["DocumentLines"].append(lineitem_delivery) 
                    LineNum_Count += 1 
                    
                else:
                    print (itemss.itemsku, ' out of stock-----') # NEED BETTER WAY TO HANDLE THIS
                    itemss.delivery_linenum              = "NA"
                    # return {'Error  ': itemss.itemsku + ' out of stock.'}
                
                #appending as a lineitems inside inv_payload dictionary
                #Here the shipping charge will be added as a freight line_item
                # if int(itemss.shippingcharges)>0:
                #     freight_lineitem = {} #lineitem_delivery.copy()
                #     freight_lineitem['LineNum']         = LineNum_Count 
                #     freight_lineitem['ItemCode']        = 'EXCM0027'
                #     freight_lineitem['TaxCode']         = shipping_tax_code  #18% GST fixed for all freight charge
                #     freight_lineitem['UnitPrice']       = itemss.shippingcharges
                #     freight_lineitem['WarehouseCode']   = 'EC-B2C'
                #     freight_lineitem['U_BuyerName']     = order_doc.customer_name
                #     freight_lineitem['U_Order']         =  order_doc.uniware_id
                #     freight_lineitem['U_City']          = order_doc.city
                #     freight_lineitem['U_State']         = order_doc.state
                #     freight_lineitem['U_OrderedOn']     = str(order_doc.created)[:10] #justThe Date
                #     freight_lineitem['U_PINCode']       = order_doc.pin_code
                #     freight_lineitem['U_Country']       = 'India'
                #     LineNum_Count += 1 #increasing the counter again
                #     Delivery_payload["DocumentLines"].append(freight_lineitem)
                # print ('Delivery_payload before: ',Delivery_payload)
            order_doc.save()
    print('List of lineitem in delivery payload : ',len(Delivery_payload['DocumentLines']))
    SAPsession =  AuthenticateSAPB1()
    # print(Delivery_payload)
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes" #DeliveryNotes
    response1 = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    print('response is --- ',str(response1)[:40])
    ####response docNum to be collected and pushed into the data point of the order-
    ## DocType using a loop in the list - open doctype and writing data  ## 
    return response1.json()


#######################
def Unicommerce_Operate(startD,endD):
    print(startD,endD)
    Channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','DOGSEE_SITE_IN','HN_SITE_IN','ONDC_NSTORE']
    for single_channel in Channel_list:
        missing_Qty = False
        if missing_Qty:
            pass
        else:
            Push_result = Channel_delivery_Creation_Dispatched(Channel_Name=single_channel,startDate=startD,endDate=endD)
    return Push_result

###############################################################################################################################################
@frappe.whitelist()
def Channel_delivery_Creation_Dispatched(Channel_Name=None,startDate=None,endDate=None):
    """
    This function will go to selected channel -- get completed order list 
    send to create a single invoice out of it.
    """
    channel_id = Channel_Name
    # KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON C03318 AMAZON IN KHANAL INDUSTRIES C03301
    Channel_CustomerCode_mapping = {'Snapdeal'      : 'C02574',
                                    'Amazon_IN_API' : 'C01186',
                                    'CRED'          : 'C03358',
                                    'FLIPKART'      : 'C03121',
                                    'DOGSEE_SITE_IN': 'C00623',
                                    'HN_SITE_IN'    : 'C01026',
                                    'ONDC_NSTORE'   : 'C03494',   }
    print ('Channel Name is : ', channel_id)
    # print ('startDate: ',startDate)
    # print('endDate : ',endDate)
    if startDate or endDate:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',   #   'PROCESSING'
                                                                  ]), 
                                        'channel_name'      : channel_id,
                                        'state'             :'KA',
                                        'sap_delivery_docnum':"",
                                        'shipment_date'     :('between',[startDate,endDate]),
                                        'shipment_status'   : ('in',['DISPATCHED',  'DELIVERED','SHIPPED' ]), 
                                        },
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status'   : ('in',['COMPLETE',    #   'PROCESSING'
                                                                  ]), 
                                        'channel_name'      : channel_id,
                                        'state'             :('not in',['KA']),
                                        'sap_delivery_docnum':"",
                                        'shipment_date'     :('between',[startDate,endDate]),
                                        'shipment_status'   : ('in',['DISPATCHED',  'DELIVERED','SHIPPED' ]), 
                                        },
                                        pluck='name') #
    else:
        SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
                                        'channel_name': channel_id,'state':'KA',
                                        'sap_delivery_docnum':""},
                                        pluck='name') #
        IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                        filters={'status': ('in',['COMPLETE',
                                                                #   'PROCESSING'
                                                                  ]), 
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
        Delivery_response = delivery_from_orderlist1(CustomerCode_from_channel,SGST_orders,bill_to_code,startDate,endDate)
        print('PUSHING SGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("***********SGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[0]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in SGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                #DELIVERY DOC NUM IS NOT GETTING UPDATED NEED TO FIX THIS
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
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
     
        Delivery_response = delivery_from_orderlist1(CustomerCode_from_channel,IGST_orders,bill_to_code,startDate,endDate)
        print(str(Delivery_response)[:40])
        print('PUSHING IGST ORDERS')
        if Delivery_response.get('DocNum') is not None:
            print("**********IGST_orders - Delivery_response['DocNum']   ",Delivery_response['DocNum'])
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['DocNum']
            for singledoc in IGST_orders:
                order_doc = frappe.get_doc('Unicommerce Orders', singledoc)  #order_doc.sap_delivery_no
                order_doc.sap_delivery_docnum = Delivery_response['DocNum']
                order_doc.save()
                for lineitem in order_doc.line_items:
                    lineitem.sap_delivery_no = Delivery_response['DocNum']
                order_doc.save()
                frappe.db.commit()
        elif Delivery_response.get('error') is not None:
            Summary_Dict[1]['DeliveryNote Docnum'] = Delivery_response['error']
            print (Delivery_response['error'])
            print ('ERROR',Delivery_response)
            #frappe.db.commit()
    # frappe.enqueue(Update_inventory_level,queue="long",job_name='Update_inventory_level')
    # Update_inventory_level() # Update Inventory level after all the DC creation.
    # Sending mail about the result
    return Summary_Dict


def Unicommerce_Automate():
    Today = frappe.utils.nowdate()
    start = add_to_date(Today,days=-2)
    # FilterDate = add_to_date(Today,days=-2)
    Channel_list = ['Snapdeal','Amazon_IN_API','CRED','FLIPKART','DOGSEE_SITE_IN','HN_SITE_IN','ONDC_NSTORE']
    for single_channel in Channel_list:
        missing_Qty = False
        if missing_Qty:
            pass
        else:
            Push_result = Channel_post_delivery_note1(Channel_Name=single_channel,startDate=start,endDate=start)
            #Sending Mail
            title = 'The DeliveryNote details for '+str(single_channel) + 'From Date :'+ str(start) +'Start Date :'+  str(start) 
            DNsendmail(DICT = Push_result,Title=title)
    return Push_result

