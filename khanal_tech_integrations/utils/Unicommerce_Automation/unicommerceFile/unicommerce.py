import requests
import json
import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime, today
from frappe.utils import now
import time
import datetime
from frappe.query_builder.functions import Sum
from khanal_tech_integrations.utils.sap import AuthenticateSAPB1
# import pandas as pd

headersList = {"Accept": "*/*",
                "User-Agent": "KhanalTech",
                "Content-Type": "application/json" ,
                # "facility" : "kfl_ecom_warehouse" #khanalfoods #kfl_ecom_warehouse #!Test_Facility
                }

# bench --site khanltech.com execute  khanal_tech_integrations.utils.unicommerce.AuthenticateUniware
# bench --site khanaltech.com execute    khanal_tech_integrations.utils.unicommerce.fill_30days_orders
# bench --site khanaltech.com execute    khanal_tech_integrations.utils.unicommerce.PO_GRN_Completion
# bench --site khanaltech.com execute khanal_tech_integrations.utils.unicommerce.fill_60days_orders
# bench --site khanaltech.com execute --args "('01-12-2024','20-12-2024')"   khanal_tech_integrations.utils.unicommerce.get_order_list
# bench --site khanaltech.com execute  --args "('2025-05-31','2025-05-01' )"  khanal_tech_integrations.utils.unicommerce.get_return_list
# bench --site khanaltech.com execute  --args "('2025-06-01','2025-06-30' )"  khanal_tech_integrations.utils.unicommerce.fill_orders
# bench --site dev.localhost execute  --args "{'OD435601682388170100'}"  khanal_tech_integrations.utils.Unicommerce_Automation.unicommerceFile.unicommerce.get_single_order
# bench --site khanaltech.com execute  --args "('2024-05-30','2024-07-01' )"  khanal_tech_integrations.utils.unicommerce.AuthenticateUniware
# bench --site khanaltech.com execute    khanal_tech_integrations.utils.unicommerce.renew_session
def sum_dict(dictt):
  import collections
  counter = collections.Counter()
  for d in dictt:
    counter.update(d)
  result = dict(counter)

  return result

# TOKEN RENEWAL FOR UNICOMMERCE
def AuthenticateUniware():
    """Function to authenticate unicommerce API. 
    Renew the token only if expired and 
    returns the doc instance
	"""
    
    doc = frappe.get_doc('Unicommerce Settings')
    
    # RENEW TOKEN ONLY IF EXPIRED
    expires_on = frappe.db.get_single_value('Unicommerce Settings', 'expires_on')

    if (expires_on==''):
        try:
            uniware_doc = renew_session()
        except Exception as e:
            raise e
    
    elif (expires_on != ''): 
        if now_datetime() >= get_datetime(doc.expires_on):
            try:
                uniware_doc = renew_session()
            except Exception as e:
                raise e
        # DO NOT RENEW IF NOT EXPIRED
        else:
            uniware_doc = doc
        return uniware_doc

def renew_session():
    doc = frappe.get_doc('Unicommerce Settings')
    # print(doc.facility)
    reqUrl = doc.tenant_url + "/oauth/token?grant_type=password&client_id=my-trusted-client&username=" + doc.username + "&password=" + doc.get_password('password')
    formatted_string = ' ,'.join(doc.facility.split(','))
    print(formatted_string)

    headersList["facility"] = formatted_string
    response = requests.request("GET", reqUrl,  headers=headersList)
    resp_json = response.json()
    doc.access_token = resp_json['access_token']
    doc.refresh_token = resp_json['refresh_token']
    doc.expires_on = add_to_date(now_datetime(), seconds=int(resp_json["expires_in"]))
    doc.save()
    frappe.db.commit()
    return doc

def update_log(period_start_date,execution_start_time,period_end_date,execution_end_date,type):
    doc = frappe.new_doc('Unicommerce SAP update log')
    doc.period_start_date = str(period_start_date)
    doc.execution_start_time = execution_start_time
    doc.period_end_date = str(period_end_date)
    doc.execution_end_date = execution_end_date
    doc.type = type
    doc.save()

#Below function is to convert epoch_time into human readable time.
def time_converter(time_stamp):
    """Convert epoch time into human readable time with safe handling of 'N' values"""
    try:
        if time_stamp is None or str(time_stamp).strip().upper() in ['N', 'NULL', 'N/A', 'NA', 'NONE']:
            return datetime.datetime.now()  # Return current time as fallback
        
        # Convert to string and remove last 3 characters (milliseconds)
        time_str = str(time_stamp)[:-3]
        # Use safe conversion to handle 'N' values
        try:
            timestamp = datetime.datetime.fromtimestamp(int(time_str))
        except (ValueError, TypeError):
            # If conversion fails, return current time
            return datetime.datetime.now()
        return timestamp
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Failed to convert timestamp '{time_stamp}' to datetime: {str(e)}")
        return datetime.datetime.now()  # Return current time as fallback

def get_order_list(fromDate, toDate):
    """Get the list of orders from Unicommerce
	"""
    uniware_session = AuthenticateUniware()
    print(uniware_session.facility,'uniware_session.facility')
    print(fromDate, toDate,'uniware_session. fromDate, toDate')
    # headersList["facility"] = uniware_session.facility
    headersList = {
        'Authorization': 'bearer ' + uniware_session.access_token,
        'Content-Type': 'application/json'
    }
    facilityneeded=uniware_session.facility.split(',')
    search_Order_payload = {#"channel": channel,
                          "fromDate": fromDate, 
                          "toDate": toDate,   
                          "facilityCodes":facilityneeded
                             }
    # print(json.dumps(search_Order_payload),'*********')
    reqUrl = "https://khanalfoods.unicommerce.com/services/rest/v1/oms/saleOrder/search"
    response = requests.request("POST", reqUrl, json=(search_Order_payload),  headers=headersList)
    print(response.text)
    return response.json()


def get_single_order(order_id):
    """
    GET DETAILS OF A SINGLE ORDER given order_id = uniware ID
    """
    
    uniware_session = AuthenticateUniware()
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    # headersList["facility"] = uniware_session.facility
    facilityneeded=uniware_session.facility.split(',')

    single_order_payload = {
                            'code': order_id,
                            "facilityCodes":facilityneeded
                                }
    reqUrl = "https://khanalfoods.unicommerce.com/services/rest/v1/oms/saleorder/get"
    response = requests.request("POST", reqUrl, data=json.dumps(single_order_payload),  headers=headersList)
    return response.json().get('saleOrderDTO')


def fill_latest_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) #"2022-08-26"
    fromDate = add_to_date(datetime.datetime.now(),days=-1).strftime('%Y-%m-%dT%H:%M:%SZ') #"2022-08-26"
    fill_orders(fromDate, toDate)

def fill_5days_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) #"2022-08-26"
    fromDate = add_to_date(datetime.datetime.now(),days=-5).strftime('%Y-%m-%dT%H:%M:%SZ') #"2022-08-26"
    fill_orders(fromDate, toDate)

def fill_15days_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(),days=-15).strftime('%Y-%m-%dT%H:%M:%SZ')
    print('ToDate',toDate)
    print('fromdate',fromDate)
    fill_orders(fromDate, toDate)

def fill_30days_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(),days=-30).strftime('%Y-%m-%dT%H:%M:%SZ')
    print('ToDate',toDate)
    print('fromdate',fromDate)
    fill_orders(fromDate, toDate)
    return None
def fill_60days_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(),days=-60).strftime('%Y-%m-%dT%H:%M:%SZ')
    print('ToDate',toDate)
    print('fromdate',fromDate)
    fill_orders(fromDate, toDate)
    return None

def fill_80days_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    fromDate = add_to_date(datetime.datetime.now(),days=-80).strftime('%Y-%m-%dT%H:%M:%SZ')
    print('ToDate',toDate)
    print('fromdate',fromDate)
    fill_orders(fromDate, toDate)

@frappe.whitelist()
def fill_orders(fromDate, toDate):
    if fromDate or toDate:
        pass
    else:
        toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) #"2022-08-26"
        fromDate = add_to_date(datetime.datetime.now(),days=-1).strftime('%Y-%m-%dT%H:%M:%SZ') #"2022-08-26" proper_order = get_single_order('428766900222828100')
    startTime = now()
    o_list = get_order_list(fromDate,toDate)
    print("Numbers of orders : ",len(o_list))

    if o_list.get('elements'):
        for order in o_list['elements']:
            proper_order = get_single_order(order['code'])
            push_new_orders(proper_order,update=False)
    endTime = now()
    update_log(fromDate,startTime,toDate,endTime,'NEW')

def push_new_orders(order_detail,update):
    
    if frappe.db.exists("Unicommerce Orders", order_detail['code'], cache=True):
        doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
        print('Doc does exist')
        doc.order_json = json.dumps(order_detail, indent=4)
        if update==False:
            return None
    else:
        doc = frappe.new_doc("Unicommerce Orders")
    
    if update==False:
        #doc.order_json = json.dumps(order_detail, indent=4)
        doc.uniware_id = order_detail['code']
        print(order_detail['code'],' -- New Order -- ')
        doc.channel_id = order_detail['displayOrderCode']
        doc.channel_name = order_detail['channel']
        doc.created = time_converter(order_detail['created'])
        doc.cod = order_detail['cod']
        doc.customer_name = order_detail['billingAddress']['name']
        doc.city = order_detail['billingAddress']['city']
        doc.district = order_detail['billingAddress']['district']
        doc.state = order_detail['billingAddress']['state']
        doc.pin_code = order_detail['billingAddress']['pincode']
        doc.displayorderdatetime = time_converter(order_detail['displayOrderDateTime'])
    
    if order_detail.get('shippingPackages'):
        shippingpackages = order_detail['shippingPackages'][0]
        doc.shippingpackages = shippingpackages
        
        doc.shipment_status = shippingpackages.get('status')
        doc.shipment_date = time_converter(shippingpackages.get('dispatched')) if shippingpackages.get('dispatched') else shippingpackages.get('dispatched')    


    if order_detail.get('returns'):
        returnsdeatils              = order_detail['returns'][0]
        doc.returnitems             = json.dumps(returnsdeatils, indent=4)
        doc.return_code             = returnsdeatils.get('code')
        doc.statuscode              = returnsdeatils.get('statusCode')
        doc.shippingprovider        = returnsdeatils.get('shippingProvider')
        doc.trackingnumber          = returnsdeatils.get('trackingNumber')
        doc.trackingstatus          = returnsdeatils.get('trackingStatus')
        doc.providerstatus          = returnsdeatils.get('providerStatus')
        doc.putawaycode             = returnsdeatils.get('putawayCode')
        doc.returninvoicecode       = returnsdeatils.get('returnInvoiceCode')
        doc.returninvoicedisplaycode = returnsdeatils.get('returnInvoiceDisplayCode')
        doc.actioncode               = returnsdeatils.get('actionCode')
        doc.type                     = returnsdeatils.get('type')
        doc.returncompleteddate      = returnsdeatils.get('returnCompletedDate')
        doc.inventoryreceiveddate    = returnsdeatils.get('inventoryReceivedDate')
        doc.returnfacilitycode       = returnsdeatils.get('returnFacilityCode')

    doc.status = order_detail['status']
    doc.updated = time_converter(order_detail['updated'])
    if update==True:
        print(order_detail['code'],'-- Updating Existing Order --')
        doc.status = order_detail['status']
        doc.updated = time_converter(order_detail['updated'])

    try:
        doc.save()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), str(e))
        return None
    
    # DO NOT UPDATE LINE ITEMS FOR UPDATE FUNCTION
    #if update==False:
    line_items = []

    warehouse_mapping = {
    'AMAZON_FBA_IN_BOM5': 'AMZ-BOM5',
    'AMAZON_FBA_IN_BOM7': 'AMZ-BOM7',
    'AMAZON_FBA_IN_BLR7': 'AMZ-BLR7',
    'AMAZON_FBA_IN_BLR8': 'AMZ-BLR8',
    'AMAZON_FBA_IN_BLR5': 'AMZ-BLR5',
    'AMAZON_FBA_IN_DEL4': 'AMZ-DEL4',
    'AMAZON_FBA_IN_DEL5': 'AMZ-DEL5',
    'AMAZON_FBA_IN_CJB1': 'AMZ-CJB1',
    'AMAZON_FBA_IN_MAA4': 'AMZ-MAA4'
    }

    for line_item in order_detail["saleOrderItems"]:
        try:
            batchDTO = line_item.get('batchDTO')
            if batchDTO is not None:
                batchCode = batchDTO.get('batchCode')
                batchFieldsDTO = batchDTO.get('batchFieldsDTO')
                vendorBatchNumber = batchFieldsDTO.get('vendorBatchNumber')
            else:
                channel_code = order_detail.get('channel')
                if channel_code in warehouse_mapping:
                    warehouse_code = warehouse_mapping[channel_code]
                    distcode = BatchNumber_AmazonFBA(line_item['itemSku'], warehouse_code)
                    vendorBatchNumber = distcode
                    batchCode =distcode
                else:
                    batchCode = 'NOT_FULFILLABLE'
                    vendorBatchNumber = 'NOT_FULFILLABLE'

            
            line_items.append({"id":line_item["id"],"itemsku": line_item["itemSku"],
                    "sellerskucode":line_item["sellerSkuCode"],"channelproductid":line_item["channelProductId"],
                    "quantity":1,"total_price":line_item["totalPrice"],"selling_price":line_item["sellingPrice"],
                    "created":time_converter(line_item["created"]),"updated":time_converter(line_item["updated"]),"totalintegratedgst":line_item["totalIntegratedGst"],
                    "integratedgstpercentage":line_item["integratedGstPercentage"],"sellingpricewithouttaxesanddiscount":line_item["sellingPriceWithoutTaxesAndDiscount"],
                    "shippingcharges":line_item["shippingCharges"],"shippingmethodcharges":line_item["shippingMethodCharges"],
                    "cashondeliverycharges":line_item["cashOnDeliveryCharges"],"cancellationreason":line_item["cancellationReason"],"state_gst_tax_percentage":line_item["stateGstPercentage"],"central_gst_tax_percentage":line_item["centralGstPercentage"],
                    "statusCode":line_item["statusCode"],"discount":line_item["discount"],"shippingchargetaxpercentage":line_item["shippingChargeTaxPercentage"],"bundleskucode":line_item["bundleSkuCode"],"code":line_item["code"],
                    "batchcode":batchCode,"vendorbatchnumber":vendorBatchNumber,
                    })
        except Exception as e:
            print(e)
            print ('FAIL! line item update failed :',order_detail['code'])
            frappe.log_error(frappe.get_traceback(), str(e) +' Order ID: ' + order_detail['code'])
            pass
    doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
    doc.line_items = [] # EMPTYING ALL LINE ITEMS FIRST
    doc.save()

    doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
    for line_item in line_items:
        doc.append("line_items",line_item)
    
    doc.save()
    frappe.db.commit()     
    
    if order_detail.get('returns'):
        returnsdeatils              = order_detail['returns'][0]
        return_items                = returnsdeatils.get('returnItems', [])
        print('Return Items:', return_items)
        for return_item in return_items:
            return_item_sku = return_item.get('saleOrderItemCode')
            print('Return Item SKU:', return_item_sku)
            for line in doc.line_items:
                print('Checking line code:', line.code)
                if line.code == return_item_sku:
                    print('Line Item Code:', line.code, 'Return Item SKU:', return_item_sku)
                    line.uniware_return_status = returnsdeatils.get('statusCode')
                    line.uniware_return_items = json.dumps(return_item, indent=4)
        doc.save()
        frappe.db.commit()
   
    
    doc.save()
    return None


# bench --site dev.localhost execute  --args "{'FGHN0034'}"  khanal_tech_integrations.utils.unicommerce.BatchNumber_AmazonFBA


#yogesh
@frappe.whitelist()
def BatchNumber_AmazonFBA(item_sku, warehouse_code):
    try:
        session = AuthenticateSAPB1()
        doc_settings = frappe.get_doc('SAP Settings')
        reqUrl         = f"{doc_settings.sap_b1_url}SQLQueries('Amazon_FBA_AL')/List?ItemCode='{item_sku}'&WhsCode='{warehouse_code}'"
        newurl         = reqUrl.format(itemcode=item_sku)
        response       = session.request("GET", newurl,  headers=headersList,verify=False)
        DeliveryNote   = dict(response.json())
        return DeliveryNote['value'][0]['DistNumber']

    except:
        return "NOT_FULFILLABLE"

def push_single_order_id(order_id=None):
    proper_order = get_single_order(order_id)
    push_new_orders(proper_order,update=False)
    return 'Ho Gaya'
    

def update_latest_orders():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%d')) #"2022-08-26"
    print(toDate)
    fromDate = add_to_date(datetime.datetime.now(),days=-30,as_string=True) #"2022-08-26"
    print(fromDate)
    update_orders(toDate,fromDate)


def update_5days_orders(days:int):
    if days:
        fromDate = add_to_date(datetime.datetime.now(),days=-days,as_string=True) #"2022-08-26"
    else:
        fromDate = add_to_date(datetime.datetime.now(),days=-5,as_string=True) #"2022-08-26"
        
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%d')) #"2022-08-26"
    fromDate = add_to_date(datetime.datetime.now(),days=-5,as_string=True) #"2022-08-26"
    update_orders(toDate,fromDate)
    
def update_2days_orders():
    """
    This function will run everyday at 1.40 am so that the DN creation 
    will be done on updated orders from previous day.
    """
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%d')) #"2022-08-26"
    fromDate = add_to_date(datetime.datetime.now(),days=-2,as_string=True) #"2022-08-26"
    update_orders(toDate,fromDate)
    return None


# 2024-07-05
# 2024-06-25

# THIS FUNCTION IS TO UPDATE THE EXISTING ORDERS IN THE KHANAL TECH INTEGRATION
# BY FETCHING THE DETAILS FROM UNIWARE AND UPDATING IT TO KHANAL TECH INTEGRATION
@frappe.whitelist()
def update_orders(toDate,fromDate):   
    startTime = now()
    # ORDER STATUS      : PENDING_VERIFICATION, CANCELLED, CREATED, PROCESSING, COMPLETE
    # SHIPMENT STATUS   : CREATED, DISPATCHED , DELIVERED, RETURN_EXPECTED
    # TODO: DONE
    doc = frappe.get_list("Unicommerce Orders",
                               #  filters={'status':'PROCESSING','created': ['between',[fromDate,toDate]]},
                                  filters=[['created','between',[fromDate,toDate]],
                                        #    {'status':['like','PROCESSING']}
                                         ],
                                fields = ['uniware_id','created','displayorderdatetime'])
    print('Length of selected Orders',len(doc))
    for item in doc:
        item_details = get_single_order(order_id=item['uniware_id'])
        if item_details.get('code') is not None:
            push_new_orders(item_details,update=True)
        else:
            print(item_details)
    endTime = now()
    update_log(fromDate,startTime,toDate,endTime,"UPDATE")
    return None

# UNICOMMERCE
def get_lineitems(order_code):
    uniware_session = AuthenticateUniware()
    facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = ','.join(uniware_session.facility.split(','))
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    single_order = get_single_order(order_code)
    x = order_code
    for items in single_order['saleOrderItems']:
        doc = frappe.new_doc('Line_Items')
        doc.order_id = x
        doc.item_code = items['itemSku']
        doc.sellerskucode = items['sellerSkuCode']
        doc.channelproductid = items['channelProductId']
        doc.quantity = items['displayOrderCode']
        doc.price = items['totalPrice']
        doc.selling_price = items['sellingPrice']
        doc.created = items['created']
        doc.updated = items['updated']
        doc.totalintegratedgst = items['totalIntegratedGst']
        doc.integratedgstpercentage = items['integratedGstPercentage']
        doc.sellingpricewithouttaxesanddiscount = items['sellingPriceWithoutTaxesAndDiscount']
        doc.discount = items['discount']
        doc.batch_details = items['batchDTO']
        doc.shippingchargetaxpercentage = items['shippingChargeTaxPercentage']
    try:
        doc.save()#try saving, skip if already exist
    except frappe.DuplicateEntryError:
        pass 


def batch_details(order_code,item_code):
    uniware_session = AuthenticateUniware()
    # headersList["facility"] = uniware_session.facility
    facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = ','.join(uniware_session.facility.split(','))
    
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    single_order = get_single_order(order_code)
    x = order_code
    for items in single_order['saleOrderItems']:
        doc = frappe.new_doc('Line_Items')
        doc.order_id = x
        doc.item_code = items['itemSku']
        doc.sellerskucode = items['sellerSkuCode']
        doc.channelproductid = items['channelProductId']
        doc.quantity = items['displayOrderCode']
        doc.price = items['totalPrice']
        doc.selling_price = items['sellingPrice']
        doc.created = items['created']
        doc.updated = items['updated']
        doc.totalintegratedgst = items['totalIntegratedGst']
        doc.integratedgstpercentage = items['integratedGstPercentage']
        doc.sellingpricewithouttaxesanddiscount = items['sellingPriceWithoutTaxesAndDiscount']
        doc.discount = items['discount']
        doc.batch_details = items['batchDTO']
        doc.shippingchargetaxpercentage = items['shippingChargeTaxPercentage']
    try:
            doc.save()
    except frappe.DuplicateEntryError:
        pass

#@frappe.whitelist()
def test_get():
    frappe.publish_realtime('msgprint', 'Starting long job...')
    # this job takes a long time to process
    #frappe.enqueue(function_test2())
    frappe.enqueue(fill_orders(),queue="long",
                    is_async=True,
                    now=False,
                    timeout=4000,job_name=None)
    frappe.publish_realtime('msgprint', 'Ending long job...')

@frappe.whitelist()
def Update_Uniware_PO_Status(days=None):
    Today = frappe.utils.nowdate()
    if days == None:
      start = add_to_date(Today,days=-4)
    else:
      start = add_to_date(Today,days=-days)
    
    List_of_InevntoryStockTransfer = frappe.db.get_list('SAP Inventory Transfers',
                                                filters={ 'towarehouse': 'EC-FG',
                                                        'uniware_po_status': ('in',['APPROVED', 'GRN_COMPLETED']), 
                                                        'docdate'     : ['>',start ] ,
                                                        }
                                                    )
    
    for inv_document in List_of_InevntoryStockTransfer:
        Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', inv_document['name'])
        
        if Single_inv_doc.uniware_po_id != None: 
            # checking if PO is in unicommerce created for this doc
            single_PO_payload = {  "purchaseOrderCode": Single_inv_doc.uniware_po_id  }
            PO_checking_url = "https://khanalfoods.unicommerce.com/services/rest/v1/purchase/purchaseOrder/getPurchaseOrderDetails"
            uniware_session = AuthenticateUniware()
            
            # headersList["facility"] = uniware_session.facility
            facilityneeded=uniware_session.facility.split(',')
            headersList["facility"] = ','.join(uniware_session.facility.split(','))
            headersList['Authorization'] = 'bearer ' + uniware_session.access_token
            response = requests.request("POST", PO_checking_url, data=json.dumps(single_PO_payload),  headers=headersList)
            PO_Dict = dict(response.json())
            # print(PO_Dict)
            if PO_Dict['successful']:
                Single_inv_doc.uniware_po_status = PO_Dict['statusCode']
                # print(PO_Dict['statusCode'])
                Single_inv_doc.save()
                frappe.db.commit()
    return None

def create_GRN(PO_number,facility='kfl_ecom_warehouse'):
    createGRN_payload = {   "wsGRN": {"vendorInvoiceNumber": "Generated via API", 
                                      "vendorInvoiceDate": today(), 
                                      "currencyCode": "INR"   }, #Date to be filled 
                                      "purchaseOrderCode": str(PO_number)  , "vendorInvoiceDateCheckDisable": False}
    uniware_session = AuthenticateUniware()
    # # headersList["facility"] = uniware_session.facility
    # facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = 'kfl_ecom_warehouse'
    if facility:
      headersList["facility"] = 'kfl_ecom_warehouse'
      
    GRN_creation_url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/create"
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    GRNcreation_response = requests.request("POST", GRN_creation_url, data=json.dumps(createGRN_payload),  headers=headersList)
    Created_GRN_Dict = dict(GRNcreation_response.json())
    if Created_GRN_Dict['successful']: #GRN is created already then add SKUs into this 
        print('Newly created GRN is :',Created_GRN_Dict['inflowReceiptCode'])
    return Created_GRN_Dict

@frappe.whitelist()
def Getting_GRN_LineItems(single_GRN):
    existing_GRN = {   "inflowReceiptCode": str(single_GRN) } 
    uniware_session = AuthenticateUniware()
    GRN_details_url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/getInflowReceipt"
    # headersList["facility"] = uniware_session.facility
    facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = ','.join(uniware_session.facility.split(','))
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    GRN_details_response = requests.request("POST", GRN_details_url, data=json.dumps(existing_GRN),  headers=headersList)
    Existing_GRN_Items = GRN_details_response.json()['inflowReceiptItems']
    GRN_SKUadding_formated_List = []
    for batchwise_item in Existing_GRN_Items:
        inflowItem = { "skuCode": None, "quantity": 1, "unitPrice": 1,
            "wsBatchDetail": { "wsBatchGroupFieldValue" : { "vendorBatchNumber": "NA" }}                     }
        inflowItem['skuCode'] = batchwise_item['itemSKU']
        inflowItem["quantity"] = batchwise_item['quantity']
        inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] = batchwise_item['batchDTO']['batchFieldsDTO']['vendorBatchNumber'] #The small change
        #'batchDTO' : {'batchCode': '','batchFieldsDTO': {'vendorBatchNumber':'NA'}
        GRN_SKUadding_formated_List.append(inflowItem)
    final_list = GRN_SKUadding_formated_List
    return final_list

def Adding_SKUs_to_grn(GRN_no,Inv_transfer_doc_LineItems):
    """Function to create GRNs for existing POs from the inventory transfers
    """
    GRN_SKUwise_Details = {
                            "inflowReceiptCode": "NAN",
                            "inflowReceiptItem": None }
    GRN_SKUwise_Details["inflowReceiptCode"] = GRN_no
    uniware_session = AuthenticateUniware()
    for one_item in Inv_transfer_doc_LineItems:
        inflowItems = { "skuCode": None, "quantity": 1, "unitPrice": 1,
            "wsBatchDetail": { "wsBatchGroupFieldValue" : { "vendorBatchNumber": "NA" }} }
        inflowItems['skuCode'] = one_item.itemcode
        inflowItems["quantity"] = one_item.batchquantity #batchwise quantity to be used
        inflowItems['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] = one_item.batchnumber #batchcode from SAP 
        GRN_SKUwise_Details["inflowReceiptItem"] = inflowItems
        SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
        
        headersList['Authorization'] = 'bearer ' + uniware_session.access_token
        response = requests.request("POST", SKU_adding_Url, data=json.dumps(GRN_SKUwise_Details),  headers=headersList)
    #Check the GRN Details with all lineitems
    Existing_GRN_Items = Getting_GRN_LineItems(GRN_no)
    
    return Existing_GRN_Items


def Adding_SKUs_to_grn_v2(GRN_no,InventoryTransfer):
    """Function to create GRNs for existing POs from the inventory transfers
    without the batch data & details
    """
    doc = frappe.qb.DocType("SAP Inventory Transfers Line Items")
    InventoryTransfer_doc = frappe.get_doc('SAP Inventory Transfers', InventoryTransfer)
    original_inv_transfer_line_items = InventoryTransfer_doc.line_items
    print(original_inv_transfer_line_items[0])
   
    # line_data = (
    #         frappe.qb.from_(doc)
    #         .select(doc.itemcode, Sum(doc.batchquantity).as_("quantity"))
    #         .where(doc.parent.eq(InventoryTransfer))
    #         .groupby(doc.itemcode)
    #         ).run(as_dict=True)
    # #print (line_data)
    
    GRN_SKUwise_Details = {
                            "inflowReceiptCode": "NAN",
                            "inflowReceiptItem": None }
    GRN_SKUwise_Details["inflowReceiptCode"] = GRN_no
    
    for one_item in original_inv_transfer_line_items:
        #print (one_item)
        uniware_session = AuthenticateUniware()
        inflowItems = { "skuCode": None, 
                       "quantity": 1, 
                       "unitPrice": 1,
                         "wsBatchDetail": { "wsBatchGroupFieldValue" :  { "vendorBatchNumber": "NA" }    }   
                         }
        inflowItems['skuCode'] = one_item.itemcode
        inflowItems["quantity"] = one_item.batchquantity #batchwise quantity to be used
        inflowItems['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] = one_item.batchnumber #batchcode from SAP 
        GRN_SKUwise_Details["inflowReceiptItem"] = inflowItems
        SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
        
        headersList['Authorization'] = 'bearer ' + uniware_session.access_token
        response = requests.request("POST", SKU_adding_Url, data=json.dumps(GRN_SKUwise_Details),  headers=headersList)
    return response.json()

def converting_documentslineitems_GRNinflow_format(document):
    Inv_transfer_doc_LineItems = document.line_items
    GRN_SKUadding_formated_List = []
    for one_item in Inv_transfer_doc_LineItems:
        inflowItem = { "skuCode": None, "quantity": 1, "unitPrice": 1,
            "wsBatchDetail": { "wsBatchGroupFieldValue" : { "vendorBatchNumber": "NA" }}                     }
        inflowItem['skuCode'] = one_item.itemcode
        inflowItem["quantity"] = one_item.batchquantity #batchwise quantity to be used
        inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] = one_item.batchnumber #batchcode from SAP 
        GRN_SKUadding_formated_List.append(inflowItem)
    return GRN_SKUadding_formated_List

#NO LONGER REQUIRED
@frappe.whitelist()
def Getting_GRN_LineItems(single_GRN):
    existing_GRN = {   "inflowReceiptCode": str(single_GRN) } 
    uniware_session = AuthenticateUniware()
    GRN_details_url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/getInflowReceipt"
    
    # headersList["facility"] = uniware_session.facility
    facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = 'kfl_ecom_warehouse'
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    GRN_details_response = requests.request("POST", GRN_details_url, data=json.dumps(existing_GRN),  headers=headersList)
    Existing_GRN_Items = GRN_details_response.json()['inflowReceipt']['inflowReceiptItems']
    GRN_SKUadding_formated_List = []
    for batchwise_item in Existing_GRN_Items:
        inflowItem = { "skuCode": None, "quantity": 1, "unitPrice": 1,
            "wsBatchDetail": { "wsBatchGroupFieldValue" : { "vendorBatchNumber": "NA" }}                     }
        inflowItem['skuCode'] = batchwise_item['itemSKU']
        inflowItem["quantity"] = batchwise_item['quantity']
        inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] = batchwise_item['batchDTO']['batchFieldsDTO']['vendorBatchNumber'] #The small change
        GRN_SKUadding_formated_List.append(inflowItem)
    final_list = GRN_SKUadding_formated_List
    return final_list

# OLD FUNCTION
@frappe.whitelist()
def Create_GRNs_Uniware_PO():
    List_of_InventoryStockTransfer = frappe.db.get_list('SAP Inventory Transfers',filters={'fromwarehouse': 'EC-FG', 'towarehouse': 'EC-B2C' })
    for inv_document in List_of_InventoryStockTransfer:
        Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', inv_document['name'])
        if Single_inv_doc.uniware_po_id != None and Single_inv_doc.uniware_po_status== 'APPROVED': #checking if PO is in unicommerce created for this doc
            if Single_inv_doc.uniware_grn_no == None:
                #Single_inv_doc.uniware_grn_no = []
                uniware_grn_no = ''
                #Then we need to create A single GRN and post some items into it 
                Created_GRN_Dict = create_GRN(Single_inv_doc.uniware_po_id)
                print (Created_GRN_Dict)
                if Created_GRN_Dict['successful'] == True: #GRN is created already then add SKUs into this 
                    print ('New GRN created is : ',Created_GRN_Dict['inflowReceiptCode'])
                    uniware_grn_no = Created_GRN_Dict['inflowReceiptCode']
                    Single_inv_doc.uniware_grn_no = uniware_grn_no
                    ##Contain the code to enter SKUs into a GRN
                    Freshly_added_SKUs = Adding_SKUs_to_grn(Created_GRN_Dict['inflowReceiptCode'],Single_inv_doc.line_items)
                    print('Nos of items added into the GRN is', len(Freshly_added_SKUs))
                    Single_inv_doc.save()
                    frappe.db.commit()

                else:
                    print('GRN creation failed for PO No :', Single_inv_doc.uniware_po_id  )
                    ##Contain the code to enter SKUs into a GRN

            elif Single_inv_doc.uniware_grn_no != None:
                print(Single_inv_doc.uniware_grn_no)
                uniware_grn_no = Single_inv_doc.uniware_grn_no
                # while Single_inv_doc.uniware_po_status != 'COMPLETE': #<<<<<<<<<<<<<<<<<<Things could break from here
                
                #while True: #<<<<<<<<<<<<<<<<<<Things could break from here
                Already_GRN_Added_SKUs = []
                GRNs = str(uniware_grn_no)
                GRNs = GRNs.split(',')
                for GRN in GRNs: #uniware_GRN is a list of GRNs
                    for item in Getting_GRN_LineItems(GRN):
                        Already_GRN_Added_SKUs.append(item)
                #Now we need to compare this big list with 
                #Set substraction result = A-B
                A = converting_documentslineitems_GRNinflow_format(Single_inv_doc)
                B = Already_GRN_Added_SKUs
                Result = [item for item in A if item not in B]
                print (Result)
                if len(Result) > 0:
                    Newly_created_GRN = create_GRN(Single_inv_doc.uniware_po_id)
                    if Newly_created_GRN['successful'] == True: #GRN is created already then add SKUs into this 
                        uniware_grn_no = uniware_grn_no + ',' + Newly_created_GRN['inflowReceiptCode']
                        Single_inv_doc.uniware_grn_no = uniware_grn_no
                        GRN_SKUwise_Details = {"inflowReceiptCode": "NA",
                                                "inflowReceiptItem": None }
                        GRN_SKUwise_Details["inflowReceiptCode"] = Newly_created_GRN['inflowReceiptCode']
                        uniware_session = AuthenticateUniware()
                        for one_item in Result:
                            SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
                            headersList["facility"] = uniware_session.facility
                            facilityneeded=uniware_session.facility.split(',')
                            headersList["facility"] = ','.join(uniware_session.facility.split(','))
                            headersList['Authorization'] = 'bearer ' + uniware_session.access_token
                            response = requests.request("POST", SKU_adding_Url, data=json.dumps(one_item),  headers=headersList)
                        Single_inv_doc.save()
                else:
                    break

#bench --site medusa.localhost execute khanal_tech_integrations.utils.unicommerce.Create_GRNs_Uniware_PO
# bench --site 1mint.localhost execute khanal_tech_integrations.utils.unicommerce.fill_30days_orders

def Create_GRN_from_PO():
    InventoryTransfers = frappe.db.get_list('SAP Inventory Transfers',
                                        filters={'fromwarehouse': 'EC-FG', 'towarehouse': 'EC-B2C', 'uniware_po_status': 'APPROVED'},pluck='name')
    
    for InventoryTransfer in InventoryTransfers:
        InventoryTransfer_doc = frappe.get_doc('SAP Inventory Transfers', InventoryTransfer)
        Created_GRN_Dict = create_GRN(InventoryTransfer_doc.uniware_po_id)
        
        if Created_GRN_Dict['successful']:
            uniware_grn_no = Created_GRN_Dict['inflowReceiptCode']
            Adding_SKUs_status = Adding_SKUs_to_grn_v2(uniware_grn_no,InventoryTransfer) #.line_items)
            if Adding_SKUs_status['successful'] == True:
                InventoryTransfer_doc.uniware_grn_no = uniware_grn_no
                InventoryTransfer_doc.save()
    return None
@frappe.whitelist()
def Create_GRNs_fill_Items(inv_tranfer_docentry):
    uniware_session = AuthenticateUniware()
    InventoryTransfer_doc = frappe.get_doc('SAP Inventory Transfers', inv_tranfer_docentry)
    original_inv_transfer_line_items = InventoryTransfer_doc.line_items
    
    GRN_SKUadding_formated_List = []
    for one_item in original_inv_transfer_line_items:
        inflowItem = { "skuCode": None, "quantity": 1, "unitPrice": 1,
            "wsBatchDetail": { "wsBatchGroupFieldValue" : { "vendorBatchNumber": "NA" }}                     }
        inflowItem['skuCode'] = one_item.itemcode
        inflowItem["quantity"] = one_item.batchquantity #batchwise quantity to be used
        inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber']  = one_item.batchnumber #batchcode from SAP 
        inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['expiryDate']         = one_item.expirydate.strftime('%Y-%m-%d')         #time.mktime(one_item.expirydate.timetuple()) 
        GRN_SKUadding_formated_List.append(inflowItem)
    #All items are added now its time to get the unique values and create GRN and addd the item subsequently
    while len(GRN_SKUadding_formated_List) !=0:
        print('Remaining item nos =',len(GRN_SKUadding_formated_List))
        Filter_item_List = []
        Listof_Items_ToPush = []
        for single_item in GRN_SKUadding_formated_List:
            if single_item['skuCode'] not in Filter_item_List:
                Filter_item_List.append(single_item['skuCode'])
                Listof_Items_ToPush.append(single_item)
                GRN_SKUadding_formated_List.remove(single_item)
        #Step to create GRn for the PO and push items 
        Created_GRN_Dict = create_GRN(InventoryTransfer_doc.uniware_po_id)
        print(Created_GRN_Dict)
        if Created_GRN_Dict['successful']:
            uniware_grn_no = Created_GRN_Dict['inflowReceiptCode']
            print('new created GRN',uniware_grn_no)
            for again_single_item in Listof_Items_ToPush:
                GRN_SKUwise_Details = {
                                    "inflowReceiptCode": str(uniware_grn_no) ,
                                    "inflowReceiptItem": again_single_item }
                # GRN_SKUwise_Details["inflowReceiptItem"] = Listof_Items_ToPush
                SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
                
                headersList['Authorization'] = 'bearer ' + uniware_session.access_token
                response = requests.request("POST", SKU_adding_Url, data=json.dumps(GRN_SKUwise_Details),  headers=headersList)
                # print ('Operation Adding List is --',response.json())
            
    return None                
##############################################################################
##############################################################################
@frappe.whitelist()
def delete():
    x = 'Unicommerce Orders'
    print(len(frappe.get_list(x)))
    for documentt in frappe.get_list(x):
        documentt = frappe.get_doc( x , documentt.name)
        print (documentt.name)
        documentt.delete()
        frappe.db.commit()
@frappe.whitelist()
def repull_single_order(order_ID=None):
    order_detail = get_single_order(order_id=order_ID)
  
    doc = frappe.get_doc("Unicommerce Orders",order_ID )
    item_dict = {
                 'FGHN0002':'FGHN0177',
                 'FGHN0200':'FGHN0222',
                 'FGDC0044': 'FGDC0038'}
    
    doc.uniware_id = order_detail['code']
   
    doc.channel_id = order_detail['displayOrderCode']
    doc.channel_name = order_detail['channel']
    doc.created = time_converter(order_detail['created'])
    doc.cod = order_detail['cod']
    doc.customer_name = order_detail['billingAddress']['name']
    doc.city = order_detail['billingAddress']['city']
    doc.district = order_detail['billingAddress']['district']
    doc.state = order_detail['billingAddress']['state']
    doc.pin_code = order_detail['billingAddress']['pincode']
    doc.displayorderdatetime = time_converter(order_detail['displayOrderDateTime'])
    
    if order_detail['shippingPackages']:
        doc.shippingpackages = order_detail['shippingPackages'][0]
    
    if order_detail.get('returns'):
        returnsdeatils              = order_detail['returns'][0]
        doc.returnitems             = json.dumps(returnsdeatils, indent=4)
        doc.return_code             = returnsdeatils.get('code')
        doc.statuscode              = returnsdeatils.get('statusCode')
        doc.shippingprovider        = returnsdeatils.get('shippingProvider')
        doc.trackingnumber          = returnsdeatils.get('trackingNumber')
        doc.trackingstatus          = returnsdeatils.get('trackingStatus')
        doc.providerstatus          = returnsdeatils.get('providerStatus')
        doc.putawaycode             = returnsdeatils.get('putawayCode')
        doc.returninvoicecode       = returnsdeatils.get('returnInvoiceCode')
        doc.returninvoicedisplaycode = returnsdeatils.get('returnInvoiceDisplayCode')
        doc.actioncode               = returnsdeatils.get('actionCode')
        doc.type                     = returnsdeatils.get('type')
        doc.returncompleteddate      = returnsdeatils.get('returnCompletedDate')
        doc.inventoryreceiveddate    = returnsdeatils.get('inventoryReceivedDate')
        doc.returnfacilitycode       = returnsdeatils.get('returnFacilityCode')
    
    doc.status = order_detail['status']
    doc.updated = time_converter(order_detail['updated'])

    try:
        doc.save()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), str(e))
        return None
    
    # DO NOT UPDATE LINE ITEMS FOR UPDATE FUNCTION
    #if update==False:
    line_items = []
    for line_item in order_detail["saleOrderItems"]:
        try:
            batchDTO = line_item.get('batchDTO')
            if batchDTO is not None:
                batchCode = batchDTO.get('batchCode')
                batchFieldsDTO = batchDTO.get('batchFieldsDTO')
                vendorBatchNumber = batchFieldsDTO.get('vendorBatchNumber')
            else:
                batchCode = 'NOT_FULFILLABLE'
                vendorBatchNumber = 'NOT_FULFILLABLE'
            
            line_items.append({"id":line_item["id"],"itemsku": item_dict[line_item["itemSku"]],
                    "sellerskucode":line_item["sellerSkuCode"],"channelproductid":line_item["channelProductId"],
                    "quantity":1,"total_price":line_item["totalPrice"],"selling_price":line_item["sellingPrice"],
                    "created":time_converter(line_item["created"]),"updated":time_converter(line_item["updated"]),"totalintegratedgst":line_item["totalIntegratedGst"],
                    "integratedgstpercentage":line_item["integratedGstPercentage"],"sellingpricewithouttaxesanddiscount":line_item["sellingPriceWithoutTaxesAndDiscount"],
                    "shippingcharges":line_item["shippingCharges"],"shippingmethodcharges":line_item["shippingMethodCharges"],"discount":line_item["discount"],
                    "cashondeliverycharges":line_item["cashOnDeliveryCharges"],"cancellationreason":line_item["cancellationReason"],
                    "statusCode":line_item["statusCode"],"shippingchargetaxpercentage":line_item["shippingChargeTaxPercentage"],
                    "batchcode":batchCode,"vendorbatchnumber":vendorBatchNumber
                    })
            print(line_item["itemSku"])
        except Exception as e:
            print(e)
            print ('FAIL! line item update failed :',order_detail['code'])
            frappe.log_error(frappe.get_traceback(), str(e) +' Order ID: ' + order_detail['code'])
            pass
    doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
    doc.line_items = [] # EMPTYING ALL LINE ITEMS FIRST
    doc.save()

    doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
    for line_item in line_items:
        doc.append("line_items",line_item)
    doc.save()
    frappe.db.commit()
    return None

#################################################################################################
#################################################################################################
#########                   PO GRN Creation code will be hereby                         #########
###########    The PO creation and All items into GRN filling is also DONE      #################
#################################################################################################
#################################################################################################

@frappe.whitelist()
def create_Approved_PO(docnum):
    """
    This function create a Purchase order (PO), in approved state given a 
    inventory stock transfer docentry.
    """
    PO_payload = {"vendorCode": "EC-B2C",
                    "purchaseOrderItems": [] 
                    }
    
    inv_transfer_doc = frappe.get_doc('SAP Inventory Transfers', docnum)
    original_inv_transfer_line_items = inv_transfer_doc.line_items
    new_list = []
    new_item_code_list = []
    for item in original_inv_transfer_line_items: #unique items will be stored in a list of dictionaries
      temporary = {'itemcode' :item.itemcode,'quantity': item.quantity}
      if item.itemcode not in new_item_code_list:
        new_item_code_list.append(item.itemcode)
        new_list.append(temporary)
    PO_lineitems_list = [] #this will contain all the items to be filled in the PO_payload
    for item in new_list:
      PO_lineitem = {
         "itemSKU": "NN",
         "quantity": 3,
         "unitPrice": 0,
         "taxTypeCode": None }
      PO_lineitem['itemSKU'] = item['itemcode']
      PO_lineitem['quantity'] = item['quantity']
      PO_lineitems_list.append(PO_lineitem)
    PO_payload["purchaseOrderItems"] = PO_lineitems_list
    PO_posting_url = "https://khanalfoods.unicommerce.com/services/rest/v1/purchase/purchaseOrder/createApproved" #create
    uniware_session = AuthenticateUniware()
    # headersList["facility"] = uniware_session.facility
    # facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = 'kfl_ecom_warehouse'

    
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    response = requests.request("POST", PO_posting_url, data=json.dumps(PO_payload),headers=headersList,verify=False)
    resdict = response.json()
    
    if resdict.get('purchaseOrderCode') is not None:
        print(resdict['purchaseOrderCode'])
        inv_transfer_doc.uniware_po_id = resdict['purchaseOrderCode']
        inv_transfer_doc.uniware_po_status = 'APPROVED'
        inv_transfer_doc.save()
        frappe.db.commit()
    return resdict


@frappe.whitelist()
def Create_GRNs_fill_Items(inv_tranfer_docentry:int)-> None:
    """
    This function create multiple GRNs and fills all the items with single/multiple batches.
    Note : A single GRN can contain a 
    """
    uniware_session = AuthenticateUniware()
    InventoryTransfer_doc = frappe.get_doc('SAP Inventory Transfers', inv_tranfer_docentry)
    original_inv_transfer_line_items = InventoryTransfer_doc.line_items

    try:
        GRN_SKUadding_formated_List = []
        for one_item in original_inv_transfer_line_items:
            inflowItem = { "skuCode": None, "quantity": 1, "unitPrice": 1,
                "wsBatchDetail": { "wsBatchGroupFieldValue" : { "vendorBatchNumber": "NA" }}                     }
            inflowItem['skuCode'] = one_item.itemcode
            inflowItem["quantity"] = one_item.batchquantity #batchwise quantity to be used
            inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber']  = one_item.batchnumber #batchcode from SAP 
            inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['expiryDate']         = one_item.expirydate.strftime('%Y-%m-%d') # time.mktime(one_item.expirydate.timetuple()) #expiary_date from SAP 
            #.strftime('%Y-%m-%d'))
            GRN_SKUadding_formated_List.append(inflowItem)
            #All items are added now its time to get the unique values and create GRN and addd the item subsequently
    
        while len(GRN_SKUadding_formated_List) !=0:
            print('Remaining item nos =',len(GRN_SKUadding_formated_List))
            
            Filter_item_List    = []
            Listof_Items_ToPush = []
            for single_item in GRN_SKUadding_formated_List:
                if single_item['skuCode'] not in Filter_item_List:
                    Filter_item_List.append(single_item['skuCode'])
                    Listof_Items_ToPush.append(single_item)
                    GRN_SKUadding_formated_List.remove(single_item)
            #Step to create GRn for the PO and push items 
            Created_GRN_Dict = create_GRN(InventoryTransfer_doc.uniware_po_id, facility='kfl_ecom_warehouse' )
            if Created_GRN_Dict['successful']:
                uniware_grn_no = Created_GRN_Dict['inflowReceiptCode']
                print('new created GRN',uniware_grn_no)
                for again_single_item in Listof_Items_ToPush:
                    GRN_SKUwise_Details = {
                                        "inflowReceiptCode": str(uniware_grn_no) ,
                                        "inflowReceiptItem": again_single_item }
                    # GRN_SKUwise_Details["inflowReceiptItem"] = Listof_Items_ToPush
                    SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
                    
                    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
                    # print(GRN_SKUwise_Details)
                    response = requests.request("POST", SKU_adding_Url, data=json.dumps(GRN_SKUwise_Details),  headers=headersList)
                    print("Adding item response :",response)
                Already_added_SKU_Lines = Getting_GRN_LineItems(uniware_grn_no)
                if len(Already_added_SKU_Lines) != 0:
                    Added_batches = [i['wsBatchDetail']['wsBatchGroupFieldValue']['vendorBatchNumber'] for i in Already_added_SKU_Lines]
                    for single_item in original_inv_transfer_line_items:
                        if single_item.batchnumber in Added_batches:
                            single_item.grn_no =  str(uniware_grn_no)
                            InventoryTransfer_doc.save()
                            frappe.db.commit()
        InventoryTransfer_doc.uniware_po_status = 'GRN_COMPLETED'
        InventoryTransfer_doc.save()
        frappe.db.commit()
    except:
        pass
    return None

########
@frappe.whitelist()
def Check_Uniware_PO_Exists(days=None):
    """Go through the list of all Inventory transfers and create PO
    for the inventory transfers if there is no corresponding PO created in uniware
    """
    Today = frappe.utils.nowdate()
    if days == None:
      start = add_to_date(Today,days=-12)
    else:
      start = add_to_date(Today,days=-days)
    List_of_InventoryStockTransfer = frappe.db.get_list('SAP Inventory Transfers',
                                                            filters={
                                                                'towarehouse' : 'EC-FG',
                                                                'docdate'     : ['>',start ]  })
    print(List_of_InventoryStockTransfer)
    for inv_document in List_of_InventoryStockTransfer:
        Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', inv_document['name'])
        k = Single_inv_doc.uniware_po_id
        print(inv_document['name'],'PO is - ', Single_inv_doc.uniware_po_id)
        if Single_inv_doc.uniware_po_id == None:# and len(Single_inv_doc.uniware_po_id ) !=5 :
            print('Then we have to create a PO for this in uniware. Inv. Trans. No. : ',Single_inv_doc.docentry)
            Uniware_response = create_Approved_PO(str(Single_inv_doc.docentry)) 
            print(Uniware_response,'Uniware_response')
            #{'successful': True, 'message': None, 'errors': [], 'warnings': None, 'vendorName': 'Ecommerce Dispatch', 'purchaseOrderCode': 'PO0026'}
            if Uniware_response['successful'] == True:
                Single_inv_doc.uniware_po_id = Uniware_response['purchaseOrderCode']
                Single_inv_doc.save()
                frappe.db.commit()
                Create_GRNs_fill_Items(Single_inv_doc.docentry)
            elif Uniware_response['successful'] == False:
                print('Po Creation Failed')
                print(Uniware_response)
                # if Uniware_response.get('errors') is not None:
                #     frappe.msgprint(msg=Uniware_response['errors'][0],title='Po Creation Failed')
    #Updating the PO Statuses
    # Update_Uniware_PO_Status()
    
    return None

def PO_GRN_Completion(days=None):
    Today = frappe.utils.nowdate()
    if days is None:
      start = add_to_date(Today,days=-2)
    else:
      start = add_to_date(Today,days=-days)
    Check_Uniware_PO_Exists(days)
      
    GRN_not_done_List = frappe.db.get_list('SAP Inventory Transfers',
                                                            filters={
                                                                'towarehouse': 'EC-FG',
                                                                'uniware_po_status': 'APPROVED',
                                                                'docdate' : ['>',start ]
                                                            })
    print(GRN_not_done_List)
    if GRN_not_done_List:
        for single_docentry in GRN_not_done_List:
            Create_GRNs_fill_Items(single_docentry)

    return None
def GRN_Completion(days=None):
    Today = frappe.utils.nowdate()
    if days is None:
      start = add_to_date(Today,days=-10)
    else:
      start = add_to_date(Today,days=-days)
      
    GRN_not_done_List = frappe.db.get_list('SAP Inventory Transfers',
                                                            filters={
                                                                'towarehouse': 'EC-FG',
                                                                'uniware_po_status': 'APPROVED',
                                                                'docdate' : ['>',start ]
                                                            })
    print(GRN_not_done_List)
    if GRN_not_done_List:
        for single_docentry in GRN_not_done_List:
            Create_GRNs_fill_Items(single_docentry)
    return None
###############################################################################

###############################################################################
@frappe.whitelist()
def Single_PO_to_GRNs(docEntry):
  Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', docEntry)
  Uniware_response = create_Approved_PO(str(docEntry)) 
  #{'successful': True, 'message': None, 'errors': [], 'warnings': None, 'vendorName': 'Ecommerce Dispatch', 'purchaseOrderCode': 'PO0026'}
  if Uniware_response['successful'] == True:
      Single_inv_doc.uniware_po_id = Uniware_response['purchaseOrderCode']
      Single_inv_doc.save()
      frappe.db.commit()
      Create_GRNs_fill_Items(Single_inv_doc.docentry)
  elif Uniware_response['successful'] == False:
      frappe.msgprint(msg=Uniware_response['errors'][0],title='Po Creation Failed')
  
  return None
## APPROVED --> GRN_COMPLETED --> CLOSED  


########################################################################
########    MAking Returned for RETURN ORDERS   #########################   
########################################################################
Batch_dict = {'FGHN0222': '21G330A25C',

 'FGHN0203': '20G427L27L',
 'FGHN0202': '20G403B16B',
 'FGHN0201': '21L231E04CR',
 'FGHN0168': '21G303A12A',
 'FGHN0132': 'P1H107K25K',
 'FGHN0101': 'R2I217L19L',
 'FGHN0091': '13D123H23H',
 'FGHN0089': '13D123H23H',
 'FGHN0088': '16Y210H19H',
 'FGHN0086': '14Y116I26I',
 'FGHN0077': 'R1I217L03B',
 'FGHN0072': '02N202H20H',
 'FGHN0067': '19Z104I13J',
 'FGHN0066': '19Z127H21J',
 'FGHN0064': 'G7Z213L04A',
 'FGHN0063': 'G7X230A03B',
 'FGHN0059': 'H1L117B10C',
 'FGHN0058': '23I325K15L',
 'FGHN0057': 'H3Z218B20B',
 'FGHN0054': 'H3Z208L04A',
 'FGHN0053': 'H3Z208L02A',
 'FGHN0051': 'H3W124G08H',
 'FGHN0050': 'H4W124C10I',
 'FGHN0047': 'H4W124C23I',
 'FGHN0046': 'H4Z209K17K',
 'FGHN0043': 'H2X113D02I',
 'FGHN0041': '22G120I22I',
 'FGHN0039': '12Y219H30I',
 'FGHN0036': '12Y219H15I',
 'FGHN0035': 'G5S503I27I',
 'FGHN0034': 'G5X222B25B',
 'FGHN0033': 'G5X211C13C',
 'FGHN0031': 'HN0223C1',
 'FGHN0030': '11Y222J22J',
 'FGHN0025': '20G626H24I',
 'FGHN0020': '17Y129H15I',
 'FGHN0018': '17Y110H19H',
 'FGHN0015': '21G325A03C',
 'FGHN0011': 'G1Z217L18L',
 'FGHN0010': 'G1Z216K18K',
 'FGHN0009': 'G1Z207B14B',
 'FGHN0008': 'G8Z221A25A',
 'FGHN0007': 'G8Z207B15B',
 'FGHN0006': 'G3H131J15K',
 'FGHN0005': 'G3H128F27I',
 'FGDV0020': 'DV1222S',
 'FGDV0019': 'DV01230F',
 'FGDV0007': 'D112202C',
 'FGDV0006': 'D01122C4B',
 'FGDV0005': 'D1122C2C',
 'FGDV0004': 'D0822A4B',
 'FGDV0003': 'D1222A2A',
 'FGDV0002': 'D0722T4B',
 'FGDV0001': 'D0922T2A',
 'FGDC0269': 'GB2AC',
 'FGDC0253': '19E2CJ',
 'FGDC0251': '17E2CL',
 'FGDC0250': '1E2CL',
 'FGDC0247': '4E2AD',
 'FGDC0139': '33E2BJ',
 'FGDC0135': '34E2BC',
 'FGDC0131': '35E2BE',
 'FGDC0085': '27C1BP',
 'FGDC0063': '1E2CM',
 'FGDC0055': '14T1AS',
 'FGDC0049': '14E2AY',
 'FGDC0038': '17E2CK',
 'FGDC0031': '18E2CK',
 'FGHN0065':'G7Z225D30D',
 'FGHN0169':'20G303A28A'
 }


@frappe.whitelist()
def create_Returns(DN_docentry,return_file):
    print(DN_docentry,'DN_docentry')
    print(return_file,'-------------------------------------')
    
    data_dict = json.loads(return_file)
    return_ordr_list = [i['Order ID'] for i in data_dict['list']]
    # print(return_ordr_list,'return_ordr_list')
    session = AuthenticateSAPB1()
    payload = ''
    Today = frappe.utils.nowdate()
    FilterDate = add_to_date(Today,days=-45)
    doc_settings = frappe.get_doc('SAP Settings')
    # reqUrl = doc_settings.sap_b1_url+"Invoices(" + str(DocEntry) + ")"
    reqUrl        = doc_settings.sap_b1_url+"DeliveryNotes(" + str(DN_docentry) + ")"
    session       = AuthenticateSAPB1()
    response      = session.request("GET", reqUrl, data=payload,  headers=headersList,verify=False)
    
    DeliveryNote  = dict(response.json())
    return_payload = {      "DocDate": frappe.utils.nowdate(),
                            "CardCode": DeliveryNote['CardCode'],
                            "Comments": "Testing Again - Return Recon Based On Deliveries "+ str(DeliveryNote['DocNum'])+ ".",
                            "JournalMemo": "Returns - " + str(DeliveryNote['CardCode']),
                            "DocumentLines": [
                                                 ]
                     }
    LineNum_Count = 0
    print(len(DeliveryNote['DocumentLines']),'lenght')
    for single_Lineitem in DeliveryNote['DocumentLines']:
        single_return_item = {
                                "LineNum": 0,
                                "ItemCode": "FGHN0066",
                                "Quantity": 1.0,

                                "WarehouseCode": "EC-B2C",
                                "AccountCode": "41106001",
                                "UseBaseUnits": "tYES",
                        
                                "BaseType": 15,
                                "BaseEntry": 8912, #DocEntry goes here
                                "BaseLine": 13,

                                "BatchNumbers": [{  "BatchNumber": "null",  "Quantity": 1.0 }]
                            }
        

        if single_Lineitem['U_Order'] in return_ordr_list[487:488]:
            # print(return_ordr_list,'return_ordr_list')
            if single_Lineitem['ItemCode'][:2] == 'FG':
                # print(single_Lineitem['U_Order'],'data')
                single_return_item['LineNum']   = LineNum_Count
                single_return_item['ItemCode']  = single_Lineitem['ItemCode']
                single_return_item['Quantity']  = single_Lineitem['Quantity']
                
                single_return_item['BaseEntry'] = DeliveryNote['DocEntry']
                single_return_item['BaseLine']  = single_Lineitem['LineNum']

                if Batch_dict.get(single_Lineitem['ItemCode']) is not None:
                    single_return_item['BatchNumbers'][0]['BatchNumber'] = Batch_dict[single_Lineitem['ItemCode']] 
                else:
                    single_return_item['BatchNumbers'][0]['BatchNumber'] =  "NAN"
                    print(single_Lineitem['ItemCode'])

                single_return_item['BatchNumbers'][0]['BatchNumber'] = single_Lineitem['Quantity']
                
                LineNum_Count += 1
                return_payload['DocumentLines'].append(single_return_item)

        if single_Lineitem['U_Order'] in return_ordr_list:
            single_return_item['LineNum']   = LineNum_Count
            single_return_item['ItemCode']  = single_Lineitem['ItemCode']
            single_return_item['Quantity']  = single_Lineitem['Quantity']
            
            single_return_item['BaseEntry'] = DeliveryNote['DocEntry']
            single_return_item['BaseLine']  = single_Lineitem['LineNum']
            
            single_return_item['BatchNumbers'][0]['BatchNumber']    = Batch_dict[single_Lineitem['ItemCode']] or "FLIPKART_RETURN_April"
            single_return_item['BatchNumbers'][0]['Quantity']       = single_Lineitem['Quantity']

            
    ######
    # print('return_payload',return_payload)
    print('Numbers of item added to return payload is --',len(return_payload['DocumentLines']))
    return_url = doc_settings.sap_b1_url+"Returns"
    response1 = session.request("POST", return_url, data=json.dumps(return_payload),  headers=headersList,verify=False)
    resDict  = dict(response1.json())
    if resDict.get('error') is not None:
        print(resDict['error'])
  
    print('response is --- ',str(response1)[:40])
    return None
    
    
#################################################################################################################################
def get_returns():
    """
    GET DETAILS OF A SINGLE ORDER
    order_id = uniware ID
    """
    uniware_session = AuthenticateUniware()
    print(uniware_session.access_token,'access_token')
    headersList = {
                    'Authorization': 'Bearer ' + uniware_session.access_token,
                    'facility': 'kfl_ecom_warehouse',
                    'Content-Type': 'application/json',
                    }
    single_order_payload =  {
                                "returnType":"CIR",
                                "createdTo":"2025-05-31T14:20:40",
                                "createdFrom":"2025-05-01T14:20:40"
                }
    reqUrl = "https://khanalfoods.unicommerce.com/services/rest/v1/oms/return/search"
    response = requests.request("POST", reqUrl, data=json.dumps(single_order_payload),  headers=headersList)
    print(response.text)
    
    return response.json()         
            
            
            
            
#################################################################################################
#################################################################################################
#########                   PO GRN Creation code will be hereby                         #########
###########    The PO creation and All items into GRN filling is also DONE      #################
#################################################################################################
#################################################################################################

def fill_latest_returns():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) #"2022-08-26"
    fromDate = add_to_date(datetime.datetime.now(),days=-1).strftime('%Y-%m-%dT%H:%M:%SZ') #"2022-08-26"
    fill_returns(fromDate, toDate)

def fill_5days_returns():
    toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) #"2022-08-26"
    fromDate = add_to_date(datetime.datetime.now(),days=-35).strftime('%Y-%m-%dT%H:%M:%SZ') #"2022-08-26"
    fill_returns(fromDate, toDate)

def fill_15days_returns():
    toDate = today() #"2022-08-26"
    fromDate = add_to_date(today(),days=-15, as_string=True) #"2022-08-26"
    print('ToDate',toDate)
    print('fromdate',fromDate)
    fill_returns(fromDate, toDate)

@frappe.whitelist()
def fill_returns(fromDate, toDate):
    if fromDate or toDate:
        pass
    else:
        toDate = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) #"2022-08-26"
        fromDate = add_to_date(datetime.datetime.now(),days=-1).strftime('%Y-%m-%dT%H:%M:%SZ') #"2022-08-26"
    startTime = now()
    o_list = get_return_list(fromDate,toDate)
    print(fromDate,toDate)

    if o_list['returnOrders']:
        for order in o_list['returnOrders']:
            proper_order = get_single_return(order['code'])
            push_new_return(proper_order,update=False)
    endTime = now()
    update_log(fromDate,startTime,toDate,endTime,'NEW')
    
def get_return_list(fromDate, toDate):
    """Get the list of orders from Unicommerce
	"""
    uniware_session = AuthenticateUniware()
    headersList = {
                    'Authorization': 'Bearer ' + uniware_session.access_token,
                    'facility': 'kfl_ecom_warehouse',
                    'Content-Type': 'application/json',
                    }
    search_Order_payload = { 
                            "returnType":"CIR",
                            "statusCode":"CREATED",
                            "createdFrom": fromDate, 
                          "createdTo": toDate                         }
    reqUrl = "https://khanalfoods.unicommerce.com/services/rest/v1/oms/return/search"
    response = requests.request("POST", reqUrl, data=json.dumps(search_Order_payload),  headers=headersList)
    print(response.text)

    return response.json()
def get_single_return(reverse_pickup_code : str):
    """
    GET DETAILS OF A SINGLE ORDER
    order_id = uniware ID
    """
    
    uniware_session = AuthenticateUniware()
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    single_return_payload =  { "reversePickupCode":reverse_pickup_code}
    reqUrl = "https://khanalfoods.unicommerce.com/services/rest/v1/oms/return/get"
    response = requests.request("POST", reqUrl, data=json.dumps(single_return_payload),  headers=headersList)
    
    return response.json()   



def push_new_return(order_detail : str,update : bool):
    if frappe.db.exists("Unicommerce Orders", str(order_detail['reversePickupCode']), cache=True):
        doc = frappe.get_doc("Unicommerce Orders",order_detail['reversePickupCode'])
        if update==False:
            return None
    else:
        doc = frappe.new_doc("Unicommerce Orders")
    
    if update==False:
        doc.reverse_pickup_code = order_detail['code']
        print(order_detail['code'])
        doc.type = order_detail['type']
        doc.channel_name = order_detail['channel']
        doc.created = time_converter(order_detail['created'])
        doc.cod = order_detail['cod']
        doc.customer_name = order_detail['billingAddress']['name']
        doc.city = order_detail['billingAddress']['city']
        doc.district = order_detail['billingAddress']['district']
        doc.state = order_detail['billingAddress']['state']
        doc.pin_code = order_detail['billingAddress']['pincode']
        doc.displayorderdatetime = time_converter(order_detail['displayOrderDateTime'])
    
    if order_detail['shippingPackages']:
        doc.shippingpackages = order_detail['shippingPackages'][0]
    
    if order_detail.get('returns'):
        returnsdeatils              = order_detail['returns'][0]
        doc.returnitems             = json.dumps(returnsdeatils, indent=4)
        doc.return_code             = returnsdeatils.get('code')
        doc.statuscode              = returnsdeatils.get('statusCode')
        doc.shippingprovider        = returnsdeatils.get('shippingProvider')
        doc.trackingnumber          = returnsdeatils.get('trackingNumber')
        doc.trackingstatus          = returnsdeatils.get('trackingStatus')
        doc.providerstatus          = returnsdeatils.get('providerStatus')
        doc.putawaycode             = returnsdeatils.get('putawayCode')
        doc.returninvoicecode       = returnsdeatils.get('returnInvoiceCode')
        doc.returninvoicedisplaycode = returnsdeatils.get('returnInvoiceDisplayCode')
        doc.actioncode               = returnsdeatils.get('actionCode')
        doc.type                     = returnsdeatils.get('type')
        doc.returncompleteddate      = returnsdeatils.get('returnCompletedDate')
        doc.inventoryreceiveddate    = returnsdeatils.get('inventoryReceivedDate')
        doc.returnfacilitycode       = returnsdeatils.get('returnFacilityCode')
    
    doc.status = order_detail['status']
    doc.updated = time_converter(order_detail['updated'])
    try:
        doc.save()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), str(e))
        return None
    
    line_items = []
    for line_item in order_detail["saleOrderItems"]:
        try:
            batchDTO = line_item.get('batchDTO')
            if batchDTO is not None:
                batchCode = batchDTO.get('batchCode')
                batchFieldsDTO = batchDTO.get('batchFieldsDTO')
                vendorBatchNumber = batchFieldsDTO.get('vendorBatchNumber')
            else:
                batchCode = 'NOT_FULFILLABLE'
                vendorBatchNumber = 'NOT_FULFILLABLE'
            
            line_items.append({"id":line_item["id"],"itemsku": line_item["itemSku"],
                    "sellerskucode":line_item["sellerSkuCode"],"channelproductid":line_item["channelProductId"],
                    "quantity":1,"total_price":line_item["totalPrice"],"selling_price":line_item["sellingPrice"],
                    "created":time_converter(line_item["created"]),"updated":time_converter(line_item["updated"]),"totalintegratedgst":line_item["totalIntegratedGst"],
                    "integratedgstpercentage":line_item["integratedGstPercentage"],"sellingpricewithouttaxesanddiscount":line_item["sellingPriceWithoutTaxesAndDiscount"],
                    "shippingcharges":line_item["shippingCharges"],"shippingmethodcharges":line_item["shippingMethodCharges"],
                    "cashondeliverycharges":line_item["cashOnDeliveryCharges"],"cancellationreason":line_item["cancellationReason"],"shippingchargetaxpercentage":line_item["shippingChargeTaxPercentage"],
                    "statusCode":line_item["statusCode"],
                    "batchcode":batchCode,"vendorbatchnumber":vendorBatchNumber
                    })
        except Exception as e:
            print(e)
            print ('FAIL! line item update failed :',order_detail['code'])
            frappe.log_error(frappe.get_traceback(), str(e) +' Order ID: ' + order_detail['code'])
            pass
    doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
    doc.line_items = [] # EMPTYING ALL LINE ITEMS FIRST
    doc.save()

    doc = frappe.get_doc("Unicommerce Orders",order_detail['code'])
    for line_item in line_items:
        doc.append("line_items",line_item)
    doc.save()
    frappe.db.commit()
    return None

    
##################################################################################


    
    
batchwise_list = [{'skuCode': 'FGHN0222',
  'quantity': 5,
  'unitPrice': 1,
  'wsBatchDetail': {'wsBatchGroupFieldValue': {'expiryDate': 1709510400.0,
    'vendorBatchNumber': '21G324A06C'}}},
 {'skuCode': 'FGHN0203',
  'quantity': 62,
  'unitPrice': 1,
  'wsBatchDetail': {'wsBatchGroupFieldValue': {'expiryDate': 1703548800.0,
    'vendorBatchNumber': '20G427L27L'}}},
 {'skuCode': 'FGHN0203',
  'quantity': 1,
  'unitPrice': 1,
  'wsBatchDetail': {'wsBatchGroupFieldValue': {'expiryDate': 1711411200.0,
    'vendorBatchNumber': '20G128B28C'}}},
 {'skuCode': 'FGHN0132',
  'quantity': 2,
  'unitPrice': 1,
  'wsBatchDetail': {'wsBatchGroupFieldValue': {'expiryDate': 1713052800.0,
    'vendorBatchNumber': 'P1H104D16D'}}},
 {'skuCode': 'FGDC0028',
  'quantity': 9,
  'unitPrice': 1,
  'wsBatchDetail': {'wsBatchGroupFieldValue': {'expiryDate': 1751241600.0,
    'vendorBatchNumber': 'nan'}}}]





@frappe.whitelist()
def Create_GRNs_fill_Items_1time(GRN_SKU_formated_List=batchwise_list,uniware_po_id='PO0004')-> None:
    """
    This function create multiple GRNs and fills all the items with single/multiple batches.
    Note : A single GRN can contain a 
    """
    uniware_session = AuthenticateUniware()
    headersList["facility"] = 'kfl_ecom_warehouse'
    GRN_SKUadding_formated_List = GRN_SKU_formated_List
    #All items are added now its time to get the unique values and create GRN and addd the item subsequently
    
    while len(GRN_SKUadding_formated_List) !=0:
        print('Remaining item nos =',len(GRN_SKUadding_formated_List))
        Filter_item_List = []
        Listof_Items_ToPush = []
        for single_item in GRN_SKUadding_formated_List:
            if single_item['skuCode'] not in Filter_item_List:
                Filter_item_List.append(single_item['skuCode'])
                Listof_Items_ToPush.append(single_item)
                GRN_SKUadding_formated_List.remove(single_item)
        #Step to create GRn for the PO and push items 
        Created_GRN_Dict = create_GRN(uniware_po_id,facility='kfl_ecom_warehouse' )
        if Created_GRN_Dict['successful']:
            uniware_grn_no = Created_GRN_Dict['inflowReceiptCode']
            for again_single_item in Listof_Items_ToPush:
                GRN_SKUwise_Details = {
                                    "inflowReceiptCode": str(uniware_grn_no) ,
                                    "inflowReceiptItem": again_single_item }
                SKU_adding_Url = uniware_session.tenant_url + "/services/rest/v1/purchase/inflowReceipt/addItemSKU"
                
                headersList['Authorization'] = 'bearer ' + uniware_session.access_token
                response1 = requests.request("POST", SKU_adding_Url, data=json.dumps(GRN_SKUwise_Details),  headers=headersList)
    return None
  
  
  
  
  # OLD FUNCTION
@frappe.whitelist()
def Outwarding_Inventory_Transfers():
    List_of_InventoryStockTransfer = frappe.db.get_list('SAP Inventory Transfers',filters={'fromwarehouse': 'EC-FG', 'towarehouse': 'EC-B2C' })
    for inv_document in List_of_InventoryStockTransfer:
        Single_inv_doc = frappe.get_doc('SAP Inventory Transfers', inv_document['name'])
    return None


       
@frappe.whitelist()
def Batchwise_Inventory_Remove_uniware(inv_tranfer_docentry:int)-> None:
    """
    This function create multiple GRNs and fills all the items with single/multiple batches.
    Note : A single GRN can contain a 
    """
    uniware_session = AuthenticateUniware()
    InventoryTransfer_doc = frappe.get_doc('SAP Inventory Transfers', inv_tranfer_docentry)
    original_inv_transfer_line_items = InventoryTransfer_doc.line_items
    Remark = "Quantity Substracted for Stock Outwarding - " + str(InventoryTransfer_doc.docnum)
    
    for one_item in original_inv_transfer_line_items:           
        item_SKUCode        = one_item.itemcode
        item_BatchCode      = one_item.batchnumber 
        item_BatchQuantity  = one_item.batchquantity #batchwise quantity to be used
        #inflowItem['wsBatchDetail']['wsBatchGroupFieldValue']['expiryDate']         = one_item.expirydate.strftime('%Y-%m-%d') # time.mktime(one_item.expirydate.timetuple()) #expiary_date from SAP 
        ####################
        # Get the inventory bath level detail from Uniware
        # Search for the respective batch in the list of batches
        
        Single_SKU ={ "skuCode": item_SKUCode }
        Getting_InventoryDetail_Url = uniware_session.tenant_url + "/services/rest/v1/product/itemTypeInventory/get"
        headersList['Authorization'] = 'bearer ' + uniware_session.access_token
        # headersList["facility"] = uniware_session.facility
        facilityneeded=uniware_session.facility.split(',')
        headersList["facility"] = ','.join(uniware_session.facility.split(','))
        
        
        # print(GRN_SKUwise_Details)
        response = requests.request("POST", Getting_InventoryDetail_Url, data=json.dumps(Single_SKU),  headers=headersList)
        resDict = response.json()
        
        if resDict.get('inventoryDTOs') is not None or []:
            Items_Shelfwise = resDict['inventoryDTOs']
            for Single_shelf_Details in Items_Shelfwise:
                
                if Single_shelf_Details['vendorBatchNumber'] == item_BatchCode:
                    # Obtain the shelf code, uniware batch code etc and remove the Transfered Quantity inventoryDTOs
                    Adjustment_Payload = { "inventoryAdjustment": {
                                            "itemSKU"           : item_SKUCode ,
                                            "quantity"          : item_BatchQuantity ,
                                            "shelfCode"         : Single_shelf_Details['shelf'],
                                            "inventoryType"     : Single_shelf_Details['type'],
                                            "sla"               : 0,
                                            "adjustmentType"    : "REMOVE", #REPLACE
                                            "remarks"           : Remark  }   }
                    
                    Getting_InventoryDetail_Url     = uniware_session.tenant_url + "/services/rest/v1/inventory/adjust"
                    headersList['Authorization']    = 'bearer ' + uniware_session.access_token
                    # headersList["facility"] = uniware_session.facility
                    facilityneeded=uniware_session.facility.split(',')
                    headersList["facility"] = ','.join(uniware_session.facility.split(','))
                    response                        = requests.request("POST", Getting_InventoryDetail_Url, data=json.dumps(Adjustment_Payload),  headers=headersList)
                    AdjustDict                      = response.json()
                    
                    if AdjustDict['successful'] ==  True:
                        one_item.grn_no = Single_shelf_Details['shelf']
                        
                        #Save the doc
                        InventoryTransfer_doc.save()
                        frappe.db.commit()
                    else:
                        if AdjustDict['errors'] is not []:
                            one_item.grn_no = AdjustDict['errors'][0]['message']
                            print(AdjustDict['errors'][0]['description'])
                    
                else:
                    pass
    return None
# "errors": [
#         {
#             "code": 60003,
#             "fieldName": null,
#             "description": "FGDC0031: Inventory at Shelf:Shelf_001, Type:GOOD_INVENTORY, Item SKU:FGDC0031, Expected:100, Found:36",
#             "message": "INVENTORY_NOT_FOUND_AT_EXPECTED_LOCATION",
#             "errorParams": null
#         }
                    
                    
            
            
def get_Inventory_Export():
    """
    This function create multiple GRNs and fills all the items with single/multiple batches.
    Note : A single GRN can contain a 
    """
    uniware_session = AuthenticateUniware()
    Creating_Export_Job = uniware_session.tenant_url + "/services/rest/v1/export/job/create"
    json_data = {
        'exportJobTypeName': 'Shelfwise Inventory',
        'exportColums':
        [  'facility',
        # 'itemTypeSKUcode',
            'itemTypeName',
            'inventoryType',
            'shelf',
            'quantity',
            'batchCode',
            'expiry',
            'Vendor Batch Number'
            ],
        'frequency': 'ONETIME',
    }
    headersList['Authorization'] = 'bearer ' + uniware_session.access_token
    # headersList["facility"] = uniware_session.facility
    facilityneeded=uniware_session.facility.split(',')
    headersList["facility"] = ','.join(uniware_session.facility.split(','))
    response = requests.request("POST", Creating_Export_Job, data=json.dumps(json_data),  headers=headersList)
    resDict = response.json()
    return resDict
# def get_Export_Output(JobCode=None):
#     uniware_session = AuthenticateUniware()
#     Getting_Export_Output_Url = uniware_session.tenant_url + "/services/rest/v1/export/job/status"
#     json_data       = { "jobCode": JobCode }
#     headersList['Authorization'] = 'bearer ' + uniware_session.access_token
#     response        = requests.request("POST", Getting_Export_Output_Url, data=json.dumps(json_data),  headers=headersList)
#     resDict         = response.json()
#     # {
#     # "successful": True,
#     # "message": None,
#     # "errors": [],
#     # "warnings": None,
#     # "status": "COMPLETE",
#     # "filePath": "https://unicommerce-export-in.s3.amazonaws.com/khanalfoods/64f08af599a974330ee8821f/Export-Courier%20Returns-khanalfoods_31082023181337.csv"
#     #     }
#     csv_url = resDict["filePath"]
#     if resDict['status'] == "COMPLETE":
#         Selfwise_Inventory_DF = pd.read_csv(csv_url)
#     else:
#         print("Error reading the CSV file:", resDict['errors'])
#     return Selfwise_Inventory_DF

    
    
######################################################################################
# from csv import DictReader
# # open file in read mode
# with open("geeks.csv", 'r') as f:
# 	dict_reader = DictReader(f)
# 	list_of_dict = list(dict_reader)

# 	print(list_of_dict)
def update_order_status(toDate, fromDate):   
    startTime = now()
    
    try:
        # Fetch only orders with 'PROCESSING' status between fromDate and toDate
        doc = frappe.get_list("Unicommerce Orders",
                              filters=[
                                  ['created', 'between', [fromDate, toDate]],
                                  ['status', '=', 'PROCESSING']
                              ],
                              fields=['uniware_id', 'created', 'displayorderdatetime', 'status'])
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to fetch Unicommerce Orders")
        print("Error fetching orders:", e)
        return
    print(doc, "Fetched Orders")
    print(f"Length of selected Processing Orders: {len(doc)}")

    for item in doc:
        try:
            item_details = get_single_order(order_id=item['uniware_id'])

            if item_details.get('code') is not None:
                try:
                    push_new_orders(item_details, update=True)
                except Exception as push_err:
                    frappe.log_error(frappe.get_traceback(), f"Failed to update order: {item['uniware_id']}")
                    print(f"Error updating order {item['uniware_id']}: {push_err}")
            else:
                msg = f"Order not fetched correctly for ID {item['uniware_id']} — Response: {item_details}"
                frappe.log_error(message=msg, title="Order Fetch Failed")
                print(msg)
                
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Exception while processing order {item['uniware_id']}")
            print(f"Unexpected error for order {item['uniware_id']}: {e}")

    endTime = now()

    try:
        update_log(fromDate, startTime, toDate, endTime, "UPDATE")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to update log")
        print("Error updating log:", e)

    return None

#bench --site dev.localhost execute khanal_tech_integrations.utils.unicommerce.update_order_status --args "['2025-05-31T00:00:00', '2025-05-01T23:59:59']"