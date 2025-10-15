# AR Invoice Creation - Bench Commands

This document contains all the bench commands for the organized AR Invoice Creation modules.

## Main Functions

### Create Channel Invoices
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.create_channel_invoices --args '{"channel_name": "CRED", "start_date": "01-09-2025", "end_date": "30-09-2025"}'
```

### Backward Compatibility Wrapper
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.Channel_delivery_Creation_Dispatched2 --args '{"Channel_Name": "CRED", "startDate": "01-09-2025", "endDate": "30-09-2025"}'
```

## Batch Validation

### Validate Batch Availability
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.batch_validation.validate_batch_availability --args '{"payload": {...}, "channel_name": "CRED"}'
```

## Hold Management

### Resume from Hold
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.resume_from_hold --args '{"hold_id": "BH-0185"}'
```

### Get Hold Summary
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.get_hold_summary
```

### Get Active Holds
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.get_active_holds
```

### Cleanup Old Holds
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.cleanup_old_holds --args '{"days_old": 7}'
```

## Utility Functions

### Get Channel Summary
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.get_channel_summary --args '{"channel_name": "CRED", "start_date": "01-09-2025", "end_date": "30-09-2025"}'
```

### Clear Cache for Channel
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.clear_cache_for_channel --args '{"channel_name": "CRED"}'
```

### Get Cache Stats
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.get_cache_stats
```

## Specialized Functions

### Create Amazon Invoices (September 2025)
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.create_amazon_invoices
```

### Resume Latest Hold
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.resume_latest_hold
```

### Check Order Status
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.ar_invoice_creation.check_order_status
```

## SAP Integration Functions

### Clear SAP Cache
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.sap_integration.clear_sap_cache --args '{"channel_name": "CRED"}'
```

### Get Cached SAP Session
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.sap_integration.get_cached_sap_session
```

## Channel Configuration

### Get Supported Channels
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.channel_config.get_supported_channels
```

### Get Channel Configuration
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.channel_config.get_channel_configuration --args '{"channel_name": "CRED"}'
```

## Error Handling

### Send Success Notification
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.error_handling.send_success_notification --args '{"channel_name": "CRED", "doc_num": "12345", "payload": {...}}'
```

### Send Failure Notification
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.error_handling.send_failure_notification --args '{"channel_name": "CRED", "error_message": "Test error"}'
```

### Send Batch Quantity Alert
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.error_handling.send_batch_quantity_alert --args '{"failed_items": [...], "channel_name": "CRED"}'
```

## Order Processing

### Build Document Lines
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.order_processing.build_document_lines --args '{"completed_orderlist": [...], "channel_config": {...}, "account_code": "41106001", "bill_to_code": "B2C SGST ADD"}'
```

### Collect SAP Data Requirements
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.order_processing.collect_sap_data_requirements --args '{"completed_orderlist": [...]}'
```

## Invoice Creation

### Create SAP Invoice Payload
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.invoice_creation.create_sap_invoice_payload --args '{"channel_name": "CRED", "completed_orderlist": [...], "bill_to_code": "B2C SGST ADD", "start_date": "01-09-2025", "end_date": "30-09-2025"}'
```

### Post Invoice to SAP
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.sap_integration.post_invoice_to_sap --args '{"payload": {...}}'
```

### Update Order Records
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.invoice_creation.update_order_records --args '{"order_list": [...], "doc_entry": 12345, "doc_num": "INV-001", "sap_response": {...}}'
```

### Process Order Batch
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.invoice_creation.process_order_batch --args '{"channel_name": "CRED", "order_list": [...], "bill_to_code": "B2C SGST ADD", "start_date": "01-09-2025", "end_date": "30-09-2025"}'
```

## Utilities

### Get Orders for Processing
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.utilities.get_orders_for_processing --args '{"channel_name": "CRED", "start_date": "01-09-2025", "end_date": "30-09-2025", "origin_state_code": "KT"}'
```

### Get Email Recipients
```bash
bench --site dev.localhost execute khanal_tech_integrations.utils.Unicommerce_Automation.ar_invoice_organized.utilities.get_email_recipients
```

## Notes

- All functions maintain the exact same behavior as the original optimized file
- No modifications were made to any function logic
- All imports and dependencies are preserved
- Functions are organized by functional areas for better maintainability
- All bench commands use the organized module structure
