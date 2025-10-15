import frappe
import frappe.utils


def get_salesperson_from_session_user():
	User_doc 					= frappe.get_doc("User", frappe.session.user)
	Required_Salespersons 		= [ ]
	
	for person in frappe.db.get_list('SAP Salesperson', fields=['salesperson_name', 'email','salesperson_code']):
		if person['email'] 	== User_doc.email:
			print("Dashboard to be filtered for :: " , person['salesperson_name'])  
			Required_Salespersons.append(person['salesperson_code'])
		else:
			pass
	
	return Required_Salespersons #list of salesperson code

def get_all_subordinates_ID(manager_SP_ID): #manager_SP_ID = None
	childreen_list = get_subordinates(manager_SP_ID)
	if len(get_subordinates(childreen_list)) != 0:
		childreen_list += get_subordinates(childreen_list)
	
	return childreen_list


def get_subordinates(manager_SP_ID): 
	if manager_SP_ID == [] or None:
		list_of_suboridinate = []
	elif isinstance(manager_SP_ID, list):
		list_of_suboridinate = frappe.db.get_list('SAP Salesperson', filters={  'reporting_manger_code':[ 'in' , manager_SP_ID ]}, fields=['salesperson_name','salesperson_code'],pluck='salesperson_code')  
	
	else:
		list_of_suboridinate = frappe.db.get_list('SAP Salesperson', filters={  'reporting_manger_code': manager_SP_ID }, fields=['salesperson_name','salesperson_code'],pluck='salesperson_code')
	
	return list_of_suboridinate



def get_context(context):
	logged_in = frappe.session.user
	startDate = frappe.local.request.args.get("startDate")
	endDate = frappe.local.request.args.get("endDate")
	print (startDate,endDate)


	# all_filteredchild_list = get_all_subordinates_ID(grandparent)
	#in ["lian@khanalfoods.com","buddhiraj@khanalfoods.com","babu@khanalfoods.com","anand.tiwari@khanalfoods.com"] :
    
	if logged_in != 'Guest':
		if startDate and endDate:
			context['logistics_data'] = get_invoice_status_map(fromDate=str(startDate),toDate=str(endDate))
		else:
			context['logistics_data'] = get_invoice_status_map(fromDate='2022-08-01',toDate='2022-10-11')

	return context



def get_invoice_status_map(fromDate=None,toDate=None):
	
	query_text_raw = """
			SELECT DISTINCT 
				SO.created_date, SO.docnum "SO Number",	 SO.customer_code "Customer Code",
				SO.customer_name "Customer Name", DN.docnum "DN #",
				DN.created_date "DN Created On", DN.shipped_date, 
				DN.transporter_name, DN.tracking_id,
				INV.docnum,INV.bill_total,SO.sales_person_code
				
			FROM `tabSAP Sales Order` SO 
			LEFT JOIN `tabSAP Delivery Notes` DN ON SO.docentry=DN.ref_sales_order AND DN.cancellation_status = 'csNo'
			LEFT JOIN `tabSAP AR Invoice` INV ON INV.ref_delivery_note=DN.docentry AND INV.cancellation_status = 'csNo'
			WHERE SO.created_date>='{FromDate}' AND SO.created_date<='{ToDate}' 
			ORDER BY SO.docnum DESC
			
			""" 
	if fromDate and toDate:
		modified_query_text = query_text_raw.format(FromDate = fromDate,ToDate = toDate)
		#final_sql_result = 'x'
		#print (modified_query_text)
		final_sql_result =	frappe.db.sql(modified_query_text)
		#print (fromDate,toDate,final_sql_result[0])
	
	return final_sql_result



