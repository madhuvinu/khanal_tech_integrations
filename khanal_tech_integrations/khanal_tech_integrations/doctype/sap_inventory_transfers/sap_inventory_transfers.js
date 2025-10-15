// Copyright (c) 2022, Khanal Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('SAP Inventory Transfers', {
	refresh: function(frm) {
		frm.add_custom_button('Inv Get',()=>{
			//frappe.throw('Testing it now')
			frappe.call({
        		method: "khanal_tech_integrations.utils.sap.bulk_process_inventory_transfers", //dotted path to server method
        		//method: "khanal_tech_integrations.khanal_tech_integrations.sap_api.update_orders", //dotted path to server method
        		//method: "khanal_tech_integrations.tasks.cron", //dotted path to server method
        		callback: function(r) {
            	// code snippet
        		}
    		});
		})

		frm.add_custom_button('PO Check',()=>{
			//frappe.throw('Testing it now')
			frappe.call({
        		method: "khanal_tech_integrations.khanal_tech_integrations.Prozo_SAP.Check_Uniware_PO_Exists", //dotted path to server method
        		//method: "khanal_tech_integrations.khanal_tech_integrations.sap_api.update_orders", //dotted path to server method
        		//method: "khanal_tech_integrations.tasks.cron", //dotted path to server method
        		callback: function(r) {
            	// code snippet
        		}
    		});
		})

		frm.add_custom_button('PO Create',()=>{
			//frappe.throw('Testing it now')
			frappe.call({
        		method: "khanal_tech_integrations.khanal_tech_integrations.Prozo_SAP.create_PO_in_uniware_for_INVdoc", //dotted path to server method
        		//method: "khanal_tech_integrations.khanal_tech_integrations.sap_api.update_orders", //dotted path to server method
        		//method: "khanal_tech_integrations.tasks.cron", //dotted path to server method
        		callback: function(r) {
            	// code snippet
        		}
    		});
		})

	 }
});


