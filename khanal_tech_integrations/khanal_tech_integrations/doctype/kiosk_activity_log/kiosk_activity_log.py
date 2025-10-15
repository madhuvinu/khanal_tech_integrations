# Copyright (c) 2025, Khanal Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class KioskActivityLog(Document):
    def before_save(self):
        """Set activity_id if not provided"""
        if not self.activity_id:
            self.activity_id = frappe.generate_hash()[:16]
    
    def validate(self):
        """Validate the activity log entry"""
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
        
        if not self.activity_id:
            self.activity_id = frappe.generate_hash()[:16]
