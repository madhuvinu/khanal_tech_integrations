import json , datetime
import frappe
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1,Get_FirstExpiry_Batch,get_GST
import requests
from frappe.utils import add_to_date, now, get_datetime, now_datetime



channel_list = ['Snapdeal','Amazon_IN','CRED','Flipkart_Smart']
# KHANAL INDUSTRIES WILL BE PROXY FOR AMAZON
# C03318 AMAZON IN KHANAL INDUSTRIES C03301
Channel_CustomerCode_mapping = {'Snapdeal' : 'C02574','Amazon_IN':'C01186','CRED':'C03358','Flipkart_Smart':'C03121'}
def get_context(context):
    if frappe.local.form_dict.endDate:
        endDate=frappe.local.form_dict.endDate
    else:
        endDate = frappe.utils.nowdate()
    if frappe.local.form_dict.startDate:
        startDate=frappe.local.form_dict.startDate
    else:
        startDate = add_to_date(endDate,days=-15)
    if frappe.local.form_dict.channel_id:
        channel_id=frappe.local.form_dict.channel_id
    else:
        channel_id = ""
    
    if frappe.local.form_dict.OrderType:
        OrderType=frappe.local.form_dict.OrderType
    else:
        OrderType = ""   
    
    
    
    print(startDate)
    print(channel_id)
    print(endDate)
    print(OrderType)
    
    SGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_id,'state':'KA','sap_delivery_docnum':"",
                                            'displayorderdatetime':('between',[startDate,endDate])},
                                            fields=['uniware_id','created','status','customer_name','sap_delivery_docnum']
                                    ) #
    IGST_orders = frappe.db.get_list('Unicommerce Orders', 
                                            filters={'status': ('in',['COMPLETE', 'PROCESSING']), 
                                            'channel_name': channel_id,'state':('not in',['KA']),'sap_delivery_docnum':"",
                                            'displayorderdatetime':('between',[startDate,endDate])},
                                            fields=['uniware_id','created','status','customer_name','sap_delivery_docnum']       
                                    )
    
    SGST_orderslist = []

    for order in SGST_orders:
        order_dict = {}
        order_dict['uniware_id'] = order['uniware_id']
        order_dict['created'] = order['created'].strftime("%Y-%m-%d %H:%M:%S")
        order_dict['status'] = order['status']
        order_dict['customer_name'] = order['customer_name']
        order_dict['sap_delivery_docnum'] = order['sap_delivery_docnum']
        SGST_orderslist.append(order_dict)

    SGST_ordersjson_result = json.dumps(SGST_orderslist)
    # print(SGST_ordersjson_result)
    IGST_orderslist = []

    for order in IGST_orders:
        order_dict = {}
        order_dict['uniware_id'] = order['uniware_id']
        order_dict['created'] = order['created'].strftime("%Y-%m-%d %H:%M:%S")
        order_dict['status'] = order['status']
        order_dict['customer_name'] = order['customer_name']
        order_dict['sap_delivery_docnum'] = order['sap_delivery_docnum']
        IGST_orderslist.append(order_dict)

    IGST_ordersjson_result = json.dumps(IGST_orderslist)
    # print(IGST_ordersjson_result)




    
    if OrderType== "SGST_orders":
        context['orders'] = SGST_ordersjson_result
    
    if OrderType== "IGST_orders":
        context['orders'] = SGST_ordersjson_result
    
    # for i in context.orders:
    #     print(i)
    return context
#####################################
@frappe.whitelist()
def delivery_from_orderlist(channel,completed_orderlist,bill_to_code,startDate,endDate): #channel,completed_orderlist
    # print(channel)
    # print(type(completed_orderlist))
    # print(bill_to_code)
    # print(startDate)
    # print(endDate)
 
    origin_state = 'Karnataka' #State Code hard coded for now 
    ##TODO: To update the state code dynamically
    if bill_to_code == 'B2C SGST ADD':
        Bill_to = 'Local'
        account_code = '41106001'
        shipping_tax_code = 'KACS@18'

    elif bill_to_code == 'B2C IGST ADD':
        Bill_to = 'Central'
        account_code = '41106002'
        shipping_tax_code = 'KAIG@18'

    #PayToState = get_customer_address(channel,bill_to_code)[0]
    #Bill_to = get_customer_address(channel,bill_to_code)[1]
    comment = "ecommerce B2C orders for {} from {} to {} Posted Using API from Unicommerce".format(channel,startDate,endDate)

    Delivery_payload = { "CardCode"      : str(channel), 
                         "Comments"      : comment,
                         "PayToCode"     : bill_to_code,
                         "ShipToCode"    : bill_to_code,
                         "U_BillingFrom" : 'KT',
                         'U_BillTo'      : Bill_to,
                         #"PlaceOfSupply": PayToState, #Here i am inserting the State Code
                         "DocumentLines": []}
    # Delivery_payload['EWayBillDetails']["BillToStateGSTCode"] = state_code
    # print ('Initial Delivery Payload :', Delivery_payload)
    LineNum_Count = 0
    Delivery_payload["DocumentLines"] = []
    for single_order in completed_orderlist:
        #if single_order.sap_delivery_docnum is None: #if SAp docnum is not created yet
        order_doc = frappe.get_doc('Unicommerce Orders', single_order['name']) #change single ordersingle_order['name']
        lineitemss = order_doc.line_items #
        # print('Order ID: ',single_order['name'],len(lineitemss))     
        for itemss in lineitemss:
            lineitem_delivery = { "LineNum": 0, "ItemCode": None,
                        "AccountCode": account_code, # 41106001 - Karnataka Local Sales, 41106002 - Karnataka Central Sales
                        'WarehouseCode': 'EC-B2C', "Quantity": "1",
                        "TaxCode": "GST@12", #Will changed for specific items
                        'TaxType': 'tt_Yes',  'TaxLiable': 'tYES',
                        'TaxTotal': 0.0,      "UnitPrice": None,
                        'U_BuyerName': None,  #channel_name
                        'U_Order': None, 'U_OrderID': None, 
                        'U_OrderedOn': None, 'U_City': None, 'U_State': None, 'U_PINCode': None, 'U_Country': 'India',
                        'BatchNumbers': [{'BatchNumber': 'PLACEHOLDER_BATCH',
                                        "Quantity": 1  }]
                            }
            # print(single_order['name'],itemss.itemsku)
            lineitem_delivery['LineNum'] = LineNum_Count
            itemss.delivery_linenum = LineNum_Count      #filling the LineNum value
            lineitem_delivery['ItemCode'] = itemss.itemsku 
            # print( lineitem_delivery['ItemCode'] )
            lineitem_delivery['Quantity'] = itemss.quantity
            # lineitem_delivery['UnitPrice'] = itemss.total_price
            lineitem_delivery['UnitPrice'] = float(itemss.selling_price)-float(itemss.totalintegratedgst)
            
            lineitem_delivery['TaxCode'] =  get_GST(origin_state,order_doc.state,itemss.itemsku)#'GST@' + str(itemss.integratedgstpercentage) 
            lineitem_delivery['U_BuyerName'] = order_doc.customer_name
            lineitem_delivery['U_Order'] = order_doc.uniware_id
            lineitem_delivery['U_City'] = order_doc.city
            lineitem_delivery['U_State'] = order_doc.state
            # print(order_doc.state, order_doc.pin_code)
            lineitem_delivery['U_OrderedOn'] = str(order_doc.created)[:10] #justThe Date
            lineitem_delivery['U_PINCode'] = order_doc.pin_code
            lineitem_delivery['U_Country'] = 'India'
            batch_assigned = Get_FirstExpiry_Batch(str(itemss.itemsku))
            if batch_assigned:
                lineitem_delivery['BatchNumbers'][0]['BatchNumber'] =  batch_assigned   #'G5H106I27I'     #itemss.vendorbatchnumber #itemwise batch fucntion here
                lineitem_delivery['BatchNumbers'][0]['Quantity'] =  itemss.quantity   #'G5H106I27I'     #itemss.vendorbatchnumber #itemwise batch fucntion here
                print ('ITEM: ',itemss.itemsku,'Batch: ',batch_assigned)
            else:
                #print (itemss.itemsku, ' out of stock') # NEED BETTER WAY TO HANDLE THIS
                return {'error': itemss.itemsku + ' out of stock'}
            
            Delivery_payload["DocumentLines"].append(lineitem_delivery) #appending as a lineitems inside inv_payload dictionary
            # print ('Delivery_payload before: ',Delivery_payload)
            LineNum_Count += 1 #increasing the counter

            #Here the shipping charge will be added as a freight line_item
            if int(itemss.shippingcharges)>0:
                freight_lineitem = {} #lineitem_delivery.copy()
                freight_lineitem['LineNum'] = LineNum_Count
                freight_lineitem['ItemCode'] = 'EXCM0027'
                freight_lineitem['TaxCode'] = shipping_tax_code  #18% GST fixed for all freight charge
                freight_lineitem['UnitPrice'] = itemss.shippingcharges
                # freight_lineitem['BatchNumbers'][0]['BatchNumber'] = None
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
            # print ('Delivery_payload before: ',Delivery_payload)
        order_doc.save()
        print('List of lineitem in delivery payload : ',len(Delivery_payload['DocumentLines']))
    
    SAPsession =  AuthenticateSAPB1()
    # print ('DELIVERY PAYLOAD')
    # print (json.dumps(Delivery_payload))
    doc_settings = frappe.get_doc('SAP Settings')
    invoice_Url = doc_settings.sap_b1_url+"DeliveryNotes" #DeliveryNotes
    response = SAPsession.request("POST", invoice_Url, data=json.dumps(Delivery_payload),  headers=headersList,verify=False)
    # print('response is',response.json())
    ####response docNum to be collected and pushed into the data point of the order-
    ## DocType using a loop in the list - open doctype and writing data  ## 
    return response.json()



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
                b1_session = renew_sap_session()
            except Exception as e:
                raise e
        else:
            b1_session.cookies.set("B1SESSION", frappe.db.get_single_value('SAP Settings','b1session'))
            b1_session.cookies.set("ROUTEID", frappe.db.get_single_value('SAP Settings','routeid'))
    #print (b1_session.cookies)
    return b1_session

def initiate_session():
    x = AuthenticateSAPB1()
    print (x.headers)
    print (x.cookies)

def renew_sap_session():
    b1_session = requests.Session()
    doc = frappe.get_doc('SAP Settings')
    credentials_json = {"CompanyDB": doc.companydb,"Password": doc.get_password('password'),"UserName": doc.username}
    b1_url = doc.sap_b1_url
    reqUrl = b1_url + "Login"
    payload = json.dumps(credentials_json)
    response = b1_session.request("POST", reqUrl, data=payload,  headers=headersList,verify=False)
    cookies = b1_session.cookies.get_dict()
    doc.b1session = cookies["B1SESSION"]
    doc.routeid = cookies['ROUTEID']                                                        
    doc.expires_on = add_to_date(now_datetime(), minutes=int(response.json()['SessionTimeout']))
    doc.save()
    return b1_session