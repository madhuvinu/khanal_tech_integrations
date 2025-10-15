from . import __version__ as app_version
from khanal_tech_integrations.route import routes

app_name 		= "khanal_tech_integrations"
app_title 		= "Khanal Tech Integrations"
app_publisher 	= "Khanal Tech"
app_description = "Integrations of Khanal Tech for Khanal Foods"
app_email 		= "lian@khanalfoods.com"
app_license 	= "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/khanal_tech_integrations/css/khanal_tech_integrations.css"
# app_include_js = "/assets/khanal_tech_integrations/js/khanal_tech_integrations.js"

# include js, css files in header of web template
# web_include_css = "/assets/khanal_tech_integrations/css/khanal_tech_integrations.css"
# web_include_js = "/assets/khanal_tech_integrations/js/khanal_tech_integrations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "khanal_tech_integrations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "/home"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "khanal_tech_integrations.utils.jinja_methods",
# 	"filters": "khanal_tech_integrations.utils.jinja_filters"
# }

jinja = {
    "methods": [
        "khanal_tech_integrations.utils.context.get_session_custom_reports"
    ]
}
# Installation
# ------------

# before_install = "khanal_tech_integrations.install.before_install"
# after_install = "khanal_tech_integrations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "khanal_tech_integrations.uninstall.before_uninstall"
# after_uninstall = "khanal_tech_integrations.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "khanal_tech_integrations.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	# "ToDo": "custom_app.overrides.CustomToDo"
# 	"Customer": "khanal_tech_integrations.utils.test.test.TestCustomerValue"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# "*": {
	# 	"on_update": "method",
	# 	"on_cancel": "method",
	# 	"on_trash": "method"
	# },
	"Material Request" :{
		"on_submit":"khanal_tech_integrations.utils.procure_to_pay.MaterialRequest.post_material_request",
		"on_cancel":"khanal_tech_integrations.utils.procure_to_pay.MaterialRequest.cancel_material_request",
		# "before_validate":"khanal_tech_integrations.utils.procure_to_pay.MaterialRequest.prevent_material_req_amending",
	},
	"File": {
        "after_insert": "khanal_tech_integrations.khanal_tech_integrations.doctype.sap_ar_invoice_detail.sap_ar_invoice_detail.Set_to_Public"
    }

	# "User" :{
	# 	"before_save":"khanal_tech_integrations.utils.purchase.disable_welcome_email.Disable",	
	# },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"khanal_tech_integrations.tasks.all",
		#"khanal_tech_integrations.sap_api.test_function"
	],
	"daily": [
		"khanal_tech_integrations.tasks.daily",
		"khanal_tech_integrations.utils.logistics.delivery_notes.temp_update",
		"khanal_tech_integrations.utils.logistics.alert_invoice.sent_notification",
		"khanal_tech_integrations.utils.safexpress.attachpod_to_sap.Get_Waybill_in_ArInvoice",
		# "khanal_tech_integrations.utils.purchase.purchaseorder.close_purchase_orders",
		# "khanal_tech_integrations.utils.React_Api.Production_Kiosk.Error_Correction.Error_MessageList"
		"khanal_tech_integrations.utils.React_Api.Production_Kiosk.Error_Correction.consolidate_error_msg_list"

		
	],
	"hourly": [
		"khanal_tech_integrations.tasks.hourly",
	],
	"hourly_long": [
		"khanal_tech_integrations.utils.unicommerce.fill_latest_orders",
		"khanal_tech_integrations.utils.unicommerce.update_latest_orders",
		"khanal_tech_integrations.utils.logistics.delivery_notes.update",
	],
	"weekly": [
		"khanal_tech_integrations.tasks.weekly"
	],
	"monthly": [
		"khanal_tech_integrations.tasks.monthly"
	],
    "cron": {
        "*/5 * * * *":[ #every /n min
			"khanal_tech_integrations.utils.purchase.purchaseorder.update_purchase_orders",
            "khanal_tech_integrations.utils.B2B.Blink.process_email_attachments",
            "khanal_tech_integrations.utils.B2B.Instamart.process_email_attachments",
            "khanal_tech_integrations.utils.B2B.Bigbasket.process_email_attachments",
            "khanal_tech_integrations.utils.B2B.Zepto.process_email_attachments",
            "khanal_tech_integrations.utils.B2B.More.process_email_attachments",
            #"khanal_tech_integrations.tasks.cron",
			# "khanal_tech_integrations.utils.unicommerce.Update_Uniware_PO_Status"
            # #"khanal_tech_integrations.khanal_tech_integrations.sap_api.fill_orders"
        ],
		 "*/30 * * * *":[ #every 30 min
            #"khanal_tech_integrations.tasks.every_ten_minutes",
			# "khanal_tech_integrations.utils.sap.Update_inventory_level",
			# "khanal_tech_integrations.utils.unicommerce.fill_latest_orders",
			"khanal_tech_integrations.utils.unicommerce.Update_Uniware_PO_Status",
            "khanal_tech_integrations.utils.unicommerce.PO_GRN_Completion",
			
        ],
		 "*/60 * * * *":[ #every Hour
			# "khanal_tech_integrations.utils.unicommerce.update_latest_orders",
			# "khanal_tech_integrations.utils.sap.Update_inventory_level",
            #"khanal_tech_integrations.khanal_tech_integrations.sap_api.test_get",
            #"khanal_tech_integrations.utils.unicommerce.sap.fill_orders_worker"
        ],
		 "10 */3 * * *":[ # “At minute 10 past every 3 hours.”
            "khanal_tech_integrations.utils.sap.bulk_process_inventory_transfers",
        ],
		"15 */1 * * *":[ #At 15 min past everyhour # At minute 0 past every 12th hour.
            #"khanal_tech_integrations.utils.sap.post_delivery_note",
			"khanal_tech_integrations.utils.logistics.sales_order.update",
        ],
		"30 */3 * * *":[ # Every 3 hours
			"khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_WayBill",
            # "khanal_tech_integrations.utils.logistics.delivery_notes.update", 
            
			
        ],
		"20 */4 * * *":[ # Every 4 hours
			"khanal_tech_integrations.utils.logistics.ar_invoice.update",
			"khanal_tech_integrations.utils.sap.Update_inventory_level",
			"khanal_tech_integrations.utils.logistics.delivery_notes.updating_existingvalues"
        ],
		"45 */3 * * *":[ # At minute 10 past every 12th hour
			"khanal_tech_integrations.utils.purchase.purchaseorder.fetch_purchase_orders",
			"khanal_tech_integrations.utils.React_Api.Production_Kiosk.ApprovalPage.Receipt_productionList_InHooks",
            "khanal_tech_integrations.utils.React_Api.Production_Kiosk.productiongoods.Receipt_productionList_InHooks", # harsha added production kiosk higher level issue handler
			"khanal_tech_integrations.utils.React_Api.Grn_creation.ViewGrn.Fetch_GrnWithProductionKey"
        ],
		"45 */1 * * *":[ # At minute 45 past every 1th hour
			"khanal_tech_integrations.utils.Finance.Outgoingpayment.Get_VendorList_for_Initial_Email"
        ],
		"50 */2 * * *":[ # At minute 50 past every 2th hour
			"khanal_tech_integrations.utils.Finance.Outgoingpayment.Get_VendorList_for_Conforming_Email",
			"khanal_tech_integrations.utils.React_Api.Production_Kiosk.ApprovalPage.Issue_productionList_InHooks",
            "khanal_tech_integrations.utils.React_Api.Production_Kiosk.productiongoods.Issue_productionList_InHooks" # harsha added production kiosk higher level issue handler
        ],
		"35 */1 * * *":[ # At minute 35 past every hour
			"khanal_tech_integrations.utils.React_Api.Ledger.ApprovalPage.SentMail_ForApproved",
        ],
		"0 */18 * * *":[ # At minute 0 past every 18th hour
			"khanal_tech_integrations.utils.safexpress.tracking.Update_Tracking_by_INV",
        ],
		"0 */20 * * *":[ # At minute 0 past every 20th hour
			# "khanal_tech_integrations.utils.sap.Unicommerce_Automate",
        ],
		"0 */19 * * *":[ # At minute 0 past every 19th hour PO_GRN_Completion
			"khanal_tech_integrations.utils.logistics.alert_invoice.fetch_ar_invoice"
        ],
		"0 10 * * *":[ #At 10:00. am
			"khanal_tech_integrations.utils.logistics.notification.daily_progress",
        ],
		"40 01 * * *":[ #At 01:40. am in midnight (in local alway trun this off other wise if data is present mail will sent)
			# "khanal_tech_integrations.utils.logistics.alert_invoice.exceed_duedate",
			"khanal_tech_integrations.utils.Email_Notification.reminder_mail.exceed_duedate",
   			"khanal_tech_integrations.utils.unicommerce.update_2days_orders",
			
        ],
		"35 06 * * *":[ #At 06:35
			"khanal_tech_integrations.utils.purchase.inventory.Update_daily_inventory_level",
        ],
		"30 08 * * *":[ #At 08:30 AM
			"khanal_tech_integrations.utils.DN_Creation_Unicommerce.Unicommerce_Dispatch_DN",
        ],
		"40 03 * * *":[ #At 03:40 AM
			"khanal_tech_integrations.utils.safexpress.automated_invoice_attach.Fetching_from_Sap",
        ],

		"40 */2 * * *":[ #At minute 40 past every 2nd hour
			"khanal_tech_integrations.utils.cashfree.vrf.bank_verification.SELECT_LIST_OF_BP_MASTER_VENDORS_FOR_VERIFICATION",
			"khanal_tech_integrations.utils.cashfree.vrf.gst_verification.Gst_Verification_API"
		],
		"00 20 * * *":[ #At 20:00.
			"khanal_tech_integrations.utils.DN_Creation_Unicommerce.DN_Creation_from_Upload",
			#Run at 8 PM and check for which items DN is not made and Create DN for them
        ],
		"20 04 * * *":[ #At 04:20
			"khanal_tech_integrations.utils.React_Api.Ledger.JournalEntries.Daily_Update_JournalEntries",
        ],
		"0 0 * * 1": [  # This cron expression means "at 00:00 on Monday" 
			"khanal_tech_integrations.utils.schedulejob.UpadteJournalentries",
        ],

		"0 1 * * 1": [  # This cron expression means "at 00:00 on Monday" 
			"khanal_tech_integrations.utils.schedulejob.AgeingReport_Ap_Ar",
        ],

		"45 1 * * 1": [  # This cron expression means "at 00:00 on Monday" 
			"khanal_tech_integrations.utils.unicommerce.fill_15days_orders",
        ],
        # INVOICE UPDATION FROM UNICOMMERCE TO SAP
		"0 22 * * *": [  # This cron expression means "10:00 PM on every day" 
			"khanal_tech_integrations.utils.unicommerceFile.DeliveryNotes.Unicommerce_Dispatch_INV",
        ],
		# "40 2 * * 1": [  # This cron expression means "at 01:40 on Monday" 
		# 	"khanal_tech_integrations.utils.unicommerceFile.CreditNote.Unicommerce_CreditNote_FromINN",
        # ],
		"30 3 * * 1": [  # This cron expression means "at 02:40 on Monday" 
			"khanal_tech_integrations.utils.schedulejob.EcomReport_Weekly",
        ],
		"40 4 * * 1": [  # This cron expression means "at 03:40 on Monday" 
			"khanal_tech_integrations.utils.schedulejob.ExportReport_Weekly",
        ],
		"0 5 5 * *": [  # At 05:00 on day-of-month 5" 
			"khanal_tech_integrations.utils.schedulejob.EcomReport_Monthly",
        ],
		"0 6 5 * *": [  # At 06:00 on day-of-month 5" 
			"khanal_tech_integrations.utils.schedulejob.ExportReport_Monthly",
        ],

    },
}


# Testing
# -------

# before_tests = "khanal_tech_integrations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "khanal_tech_integrations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "khanal_tech_integrations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"khanal_tech_integrations.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []

website_redirects = [
    {"source": "/app/intranet", "target": "/intranet"},
    # {"source": "/docs(/.*)?", "target": "https://docs.tennismart.com/\1"},
    # {"source": r'/items/item\?item_name=(.*)', "target": '/items/\1', match_with_query_string=True},
]


website_route_rules = routes



#! bench export-fixtures
fixtures = [
	
    {"doctype": "Custom Field",},
    {"doctype": "Client Script",},
    {"doctype": "Workflow",},
	{"doctype": "Workflow State",},
    {"doctype": "Workflow Action",},
    ]