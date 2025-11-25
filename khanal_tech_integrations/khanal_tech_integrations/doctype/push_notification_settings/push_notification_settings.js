// Copyright (c) 2024, Khanal Tech and Contributors
// MIT License

frappe.ui.form.on('Push Notification Settings', {
	refresh: function(frm) {
		// Handle regenerate button click
		// For button fields, we need to use the button's click handler
		frm.fields_dict.regenerate_keys_button.$input.on('click', function() {
			frappe.confirm(
				'Are you sure you want to regenerate VAPID keys?<br><br>⚠️ <strong>Warning:</strong> This will invalidate all existing push subscriptions. Users will need to re-subscribe.',
				function() {
					// Yes - regenerate
					frm.call('regenerate_vapid_keys').then(function(r) {
						frappe.show_alert({
							message: 'VAPID keys regenerated successfully!',
							indicator: 'green'
						}, 5);
						// Reload the form to show new keys
						frm.reload_doc();
					}).catch(function(err) {
						frappe.msgprint({
							title: __('Error'),
							indicator: 'red',
							message: __('Failed to regenerate keys: ' + (err.message || err))
						});
					});
				},
				function() {
					// No - cancel
				}
			);
		});
	}
});

