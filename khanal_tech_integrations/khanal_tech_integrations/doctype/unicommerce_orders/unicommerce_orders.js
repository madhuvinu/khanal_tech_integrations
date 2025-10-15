// Copyright (c) 2022, Khanal Tech and contributors
// For license information, please see license.txt


frappe.ui.form.on('Unicommerce Orders', {
	refresh: function(frm) {
		frm.add_custom_button('Fetch Unicommerce Orders',()=>{
			//frappe.throw('Testing it now')
			frappe.call({
        		method: "khanal_tech_integrations.unicommerce.fill_orders", //dotted path to server method
        		//method: "khanal_tech_integrations.khanal_tech_integrations.sap_api.update_orders", //dotted path to server method
        		//method: "khanal_tech_integrations.tasks.cron", //dotted path to server method
        		callback: function(r) {
            	// code snippet
        		}
    		});
		})
		frm.add_custom_button('Update Unicommerce Orders',()=>{
			//frappe.throw('Testing it now')
			frappe.call({
        		//method: "khanal_tech_integrations.khanal_tech_integrations.sap_api.fill_orders", //dotted path to server method
        		method: "khanal_tech_integrations.khanal_tech_integrations.sap_api.update_orders", //dotted path to server method
        		//method: "khanal_tech_integrations.tasks.cron", //dotted path to server method
        		callback: function(r) {
            	// code snippet
        		}
    		});
		})
	}
});