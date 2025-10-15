
import frappe
from khanal_tech_integrations.utils.unicommerce import BatchNumber_AmazonFBA

from datetime import datetime


headersList = {
        "Accept": "*/*",
        "User-Agent": "Khanal Tech",
        "Content-Type": "application/json" 
    }

#! bench --site khanaltech.com execute  --args "( '10-02-2025','16-02-2025','NOT_FULFILLABLE','AMAZON_FBA_IN_BLR8','D802310L12L' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode
#! bench --site khanaltech.com execute  --args "( '02-09-2024','08-09-2024','D810716A17A','AMAZON_FBA_IN_BLR7','I310730A03B' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode

@frappe.whitelist()
def Replace_BatchCode(startDate=None,endDate=None,BatchCode=None,channel_name=None,Correct_batchCode=None): #
    
    print(channel_name,'channel_name')
 
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            # 'status':'COMPLETE', 
                                            'channel_name': str(channel_name),
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'vendorbatchnumber' :str(BatchCode), 
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        # doc.sap_ar_invoice_docentry=''
        # doc.save()
        # frappe.db.commit() 
        for item in doc.line_items:
            if item.vendorbatchnumber==str(BatchCode):
                item.vendorbatchnumber =Correct_batchCode
                doc.save()
                frappe.db.commit()     
                print(doc,'Saved') 
            else:
                pass

         
    pass


#bench --site khanaltech.com execute  --args "{ '23-02-2025','28-02-2025','FGDC0248','433750272976978100','FLIPKART','5E2BD' }" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeFromItemCode

#  #! bench --site khanaltech.com execute  --args "( '23-02-2025','28-02-2025','FGDC0076','30S4CN','FLIPKART','30S4CI' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.ReplaceItemCode_BatchCode

#! bench --site khanaltech.com execute  --args "( '01-03-2025','08-03-2025','FGDC0063','28C1CM','FLIPKART','01E2DH' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.ReplaceItemCode_BatchCode

@frappe.whitelist()
def ReplaceItemCode_BatchCode(startDate=None,endDate=None,ItemCode=None,BatchCode=None,channel_name=None,Correct_batchCode=None): #
#! bench --site khanaltech.com execute  --args "( '01-03-2025','08-03-2025','FGDC0097','14E2BW','DOGSEE_SITE_IN','29C1CB' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.ReplaceItemCode_BatchCode
    
    print(channel_name,'channel_name')
 
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            # 'status':'COMPLETE', 
                                            'channel_name': str(channel_name),
                                            'itemsku':ItemCode,
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'vendorbatchnumber' :str(BatchCode), 
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        # doc.sap_ar_invoice_docentry=''
        # doc.save()
        # frappe.db.commit() 
        for item in doc.line_items:
            if item.vendorbatchnumber==str(BatchCode):
                item.vendorbatchnumber =Correct_batchCode
                doc.save()
                frappe.db.commit()     
                print(doc,'Saved') 
            else:
                pass

         
    pass


#! bench --site khanaltech.com execute  --args "( '27-03-2024','29-03-2024','18E2CX','Amazon_IN_API','18E2CV' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode
# bench --site khanaltech.com execute  --args "( '10-02-2024','19-02-2024','GB3AB','DOGSEE_SITE_IN','GB3AN' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode
#* bench --site khanaltech.com execute  --args "( '11-02-2024','20-02-2024','D0822A4B','Amazon_IN_API','D1122A4C' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode
#* bench --site khanaltech.com execute  --args "( '11-02-2024','20-02-2024','17E2CV','Amazon_IN_API','17E2CW' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode
#* bench --site khanaltech.com execute  --args "( '10-01-2024','10-01-2024','G1Z209I12I','CRED','G1N117L18L' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode
# {'Snapdeal' : 'C02574',
#                                     'Amazon_IN_API':'C01186',
#                                     'CRED':'C03358',
#                                     'FLIPKART':'C03121',
#                                     'DOGSEE_SITE_IN':'C00623',
#                                     'HN_SITE_IN':'C01026',
#                                     'ONDC_NSTORE':'C03494',
#                                     }
@frappe.whitelist()
def Replace_Dn_Not_Created(startDate=None,endDate=None,channel_name=None): #
    print(startDate,'startDate')
    print(endDate,'endDate')
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                                'channel_name': str(channel_name),
                                                'displayorderdatetime':('between',[start_date,end_date]),
                                                'status':'complete', 
                                                'sap_ar_invoice_docentry': ['=', ''],
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    for singledoc in docList:
        # print(singledoc)
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        doc.sap_ar_invoice_docentry ='DN_NOT_CREATED'
        doc.save()
        frappe.db.commit()     
        print(doc,'Saved')  
    return

# {'Snapdeal' : 'C02574',
#                                     'Amazon_IN_API':'C01186',
#                                     'CRED':'C03358',
#                                     'FLIPKART':'C03121',
#                                     'DOGSEE_SITE_IN':'C00623',
#                                     'HN_SITE_IN':'C01026',
#                                     'ONDC_NSTORE':'C03494',
#                                     }
# bench --site khanaltech.com execute  --args "( '07-11-2023','30-11-2023','HN_SITE_IN' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_Dn_Not_Created



@frappe.whitelist()
def Replace_Dn_Not_CreatedChangedValue(startDate=None,endDate=None,channel_name=None): #
    print(startDate,'startDate')
    print(endDate,'endDate')
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                                'channel_name': str(channel_name),
                                                'displayorderdatetime':('between',[start_date,end_date]),
                                                'status':'complete', 
                                                'sap_ar_invoice_docentry':'DN_NOT_CREATED',
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    for singledoc in docList:
        # print(singledoc)
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        doc.sap_ar_invoice_docentry =''
        doc.save()
        frappe.db.commit()     
        print(doc,'Saved')  
    return

# bench --site khanaltech.com execute  --args "( '01-10-2023','13-10-2023','CRED' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_Dn_Not_CreatedChangedValue

# bench --site khanaltech.com execute  --args "( '17-02-2025','22-02-2025','G5X203H09H','CRED','G5X227G01H' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCode



@frappe.whitelist()
def Replace_Dn_Not_tempSolution(startDate=None,endDate=None,channel_name=None,BatchCode=None): #
    print(startDate,'startDate')
    print(endDate,'endDate')
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                                'channel_name': str(channel_name),
                                                'displayorderdatetime':('between',[start_date,end_date]),
                                                'status':'complete', 
                                                'sap_ar_invoice_docentry': ['=', ''],
                                                'vendorbatchnumber' :str(BatchCode), 
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    for singledoc in docList:
        # print(singledoc)
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        doc.sap_ar_invoice_docentry ='DN_NOT_CREATED'
        doc.save()
        frappe.db.commit()     
        print(doc,'Saved')  
    return
    #! G5X227G01H
    # !bench --site khanaltech.com execute  --args "( '01-10-2023','10-10-2023','CRED','G5X227G01H )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_Dn_Not_tempSolution
# bench --site dev.localhost execute  khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_Dn_Not_Created
@frappe.whitelist( )
def Get_Salesperson():
    doc=frappe.db.get_list('SAP Salesperson')
    return doc



# bench --site dev.localhost execute khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Get_Salesperson




# !--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def With_Count_Replace_BatchCode(startDate=None, endDate=None, BatchCode=None, channel_name=None, Correct_batchCode=None,Breaking_value=None):
    print(startDate, 'startDate')
    print(endDate, 'endDate')
    print(channel_name, 'channel_name')
    print(BatchCode, 'BatchCode')
    print(Correct_batchCode, 'Correct_batchCode')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    docList = frappe.db.get_list('Unicommerce Orders',
                                 filters={
                                     'status': 'COMPLETE',
                                     'channel_name': str(channel_name),
                                     'displayorderdatetime': ('between', [start_date, end_date]),
                                     'vendorbatchnumber': str(BatchCode),
                                     'sap_ar_invoice_docentry': 'DN_NOT_CREATED',
                                 },
                                 )

    print('length of Document is ....', len(docList))
    count = 0  # Initialize a count variable to keep track of the number of processed documents  
    for singledoc in docList:
        doc = frappe.get_doc('Unicommerce Orders', singledoc.name)
        for item in doc.line_items:
            if item.vendorbatchnumber == str(BatchCode):
                item.vendorbatchnumber = Correct_batchCode
                doc.sap_ar_invoice_docentry =''
                doc.save()
                frappe.db.commit()
                count += 1  # Increment the count

                print(doc, 'Saved', count)
                if count == int(Breaking_value):
                    print('*' * 10)
                    print('Code Break at.............', Breaking_value)
                    break  # Exit the inner loop
        else:
            continue  # Continue to the next document

        break  # Exit the outer loop

    pass







# bench --site khanaltech.com execute  --args "( '17-02-2025','22-02-2025','FGDC0131','433750272976978100','AMAZON_FBA_IN_BLR8','35E2CD' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeFromItemCode

@frappe.whitelist()
#! bench --site khanaltech.com execute  --args "( '01-03-2025','08-03-2025','FGDC0097','DOGSEE_SITE_IN','29C1CB' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeFromItemCode

def Replace_BatchCodeFromItemCode(startDate=None,endDate=None,ItemCode=None,channel_name=None,Correct_batchCode=None): #
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            # 'status':'COMPLETE', 
                                            'channel_name': str(channel_name),
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'vendorbatchnumber' :'NOT_FULFILLABLE',
                                            'itemsku':ItemCode,
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        # doc.sap_ar_invoice_docentry=''
        # doc.save()
        # frappe.db.commit() 
        for item in doc.line_items:
            if item.itemsku==str(ItemCode):
                item.vendorbatchnumber =Correct_batchCode
                doc.save()
                frappe.db.commit()     
                print(doc,'Saved') 
            else:
                pass

         
    pass
#! bench --site khanaltech.com execute  --args "( '23-02-2025','28-02-2025','FGDC0248','433750272976978100','FLIPKART','5E2BF' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeFromOderID
@frappe.whitelist()
def Replace_BatchCodeFromOderID(startDate=None,endDate=None,ItemCode=None,OrderID=None,channel_name=None,Correct_batchCode=None): 
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            'channel_name': str(channel_name),
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'vendorbatchnumber' :'NOT_FULFILLABLE',
                                            'uniware_id':OrderID,
                                            'itemsku':ItemCode,
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    

    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        for item in doc.line_items:
            if item.itemsku==str(ItemCode):
                item.vendorbatchnumber = Correct_batchCode
                doc.save()
                frappe.db.commit()     
                print(doc,'Saved') 
            else:
                pass

         
    pass

#! bench --site khanaltech.com execute  --args "( '01-07-2025','27-07-2025','AMAZON_FBA_IN_DEL5' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeForFBA


@frappe.whitelist()
def Replace_BatchCodeForFBA(startDate=None,endDate=None,channel_name=None): 
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            'channel_name': str(channel_name),
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'vendorbatchnumber' :'NOT_FULFILLABLE',
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    warehouse_mapping = {
    'AMAZON_FBA_IN_BOM5': 'AMZ-BOM5',
    'AMAZON_FBA_IN_BOM7': 'AMZ-BOM7',
    'AMAZON_FBA_IN_BLR7': 'AMZ-BLR7',
    'AMAZON_FBA_IN_BLR8': 'AMZ-BLR8',
    'AMAZON_FBA_IN_BLR5': 'AMZ-BLR5',
    'AMAZON_FBA_IN_DEL4': 'AMZ-DEL4',
    'AMAZON_FBA_IN_DEL5': 'AMZ-DEL5',
    'AMAZON_FBA_IN_MAA4': 'AMZ-MAA4',
    'AMAZON_FBA_IN_CJB1': 'AMZ-CJB1'
    }
    warehouse_code = warehouse_mapping[channel_name]
    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        for item in doc.line_items:
            if item.itemsku:
                item.vendorbatchnumber = BatchNumber_AmazonFBA(item.itemsku, warehouse_code)
                print(item.itemsku,item.vendorbatchnumber,warehouse_code)
                if item.vendorbatchnumber != 'NOT_FULFILLABLE':
                    doc.save()
                    frappe.db.commit()     
                    print(doc,'Saved') 
                else:
                    print(item.itemsku + ' is not found at ' + warehouse_code)
            else:
                pass

         
    pass

#! bench --site khanaltech.com execute  --args "( '17-02-2025','22-02-2025','AMAZON_FBA_IN_BLR7' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeForFBA
#! bench --site khanaltech.com execute  --args "( '23-02-2025','28-02-2025','FGDC0063','28C1CM','FLIPKART','01E2DH' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.ReplaceItemCode_BatchCode
#! bench --site khanaltech.com execute  --args "( '01-03-2025','08-03-2025','FGDC0049','DOGSEE_SITE_IN','14E2BR' )" khanal_tech_integrations.utils.unicommerceFile.Replacevalue.Replace_BatchCodeFromItemCode

@frappe.whitelist()
def Replace_BatchCodeFromOderID(startDate=None,endDate=None,ItemCode=None,OrderID=None,channel_name=None,Correct_ItemCode=None): 
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            'channel_name': str(channel_name),
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'uniware_id':OrderID,
                                            'itemsku':ItemCode,
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    

    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        for item in doc.line_items:
            if item.itemsku==str(ItemCode):
                item.itemsku = Correct_ItemCode
                doc.save()
                frappe.db.commit()     
                print(doc,'Saved') 
            else:
                pass

         
    pass


@frappe.whitelist()
def Replace_BatchCodeFromOderID_AND_BATCHCODE(startDate=None,endDate=None,ItemCode=None,OrderID=None,channel_name=None,Old_Batchcode=None,Correct_batchCode=None): 
    print(channel_name,'channel_name')
    start_date = datetime.strptime(startDate, "%d-%m-%Y")
    end_date = datetime.strptime(endDate, "%d-%m-%Y")
    end_date = end_date.replace(hour=23, minute=59, second=59)
    print(start_date,'startDate')
    print(end_date,'endDate')

    docList=frappe.db.get_list('Unicommerce Orders', 
                                            filters={
                                            'channel_name': str(channel_name),
                                            'displayorderdatetime':('between',[start_date,end_date]),
                                            'vendorbatchnumber' :Old_Batchcode,
                                            'uniware_id':OrderID,
                                            'itemsku':ItemCode,
                                            'sap_ar_invoice_docentry': ['=', ''],                                           
                                            },
                                            
                                    )
    print('lenght of Document is ....',len(docList))

    

    for singledoc in docList:
        doc=frappe.get_doc('Unicommerce Orders',singledoc.name)
        for item in doc.line_items:
            if item.itemsku==str(ItemCode):
                item.vendorbatchnumber = Correct_batchCode
                doc.save()
                frappe.db.commit()     
                print(doc,'Saved') 
            else:
                pass

         
    pass
