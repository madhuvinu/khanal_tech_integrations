# Bench Commands for Reporting Organized

## 📋 Complete Bench Commands Reference

### Excel Validation and Sync
```bash
# Add validation remarks to Excel
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.excel_validation_and_sync.add_validation_remarks_to_excel" --kwargs '{"excel_file_path": "/path/to/file.xlsx"}'

# Sync missing orders from Excel
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.excel_validation_and_sync.sync_missing_orders_from_excel" --kwargs '{"excel_file_path": "/path/to/file.xlsx"}'
```

### Monthly Uniware Report
```bash
# Trigger previous month export
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.Montlhy_uniware_report.trigger_previous_month_sale_order_export"

# Complete monthly export with download
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.Montlhy_uniware_report.process_monthly_export_with_download"

# Check export job status
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.Montlhy_uniware_report.check_export_job_status" --kwargs '{"job_code": "JOB123"}'

# Download and merge CSV files
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.Montlhy_uniware_report.download_and_merge_csv_files" --kwargs '{"job_codes_dict": {"facility1": "job1", "facility2": "job2"}, "max_wait_minutes": 10}'
```

### Pivot Table Creator
```bash
# Create complete pivot analysis
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.pivot_table_creator.create_complete_pivot_analysis" --kwargs '{"excel_file_path": "/path/to/file.xlsx", "email_notification": true}'

# Create master data sheet
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.pivot_table_creator.create_master_data_sheet" --kwargs '{"excel_file_path": "/path/to/file.xlsx"}'

# Create pivot tables
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.pivot_table_creator.create_pivot_tables" --kwargs '{"excel_file_path": "/path/to/file.xlsx"}'

# Create pivot analysis for existing file
bench --site dev.localhost execute "khanal_tech_integrations.utils.Unicommerce_Automation.reporting_organized.pivot_table_creator.create_pivot_analysis_for_existing_file" --kwargs '{"excel_file_path": "/path/to/file.xlsx"}'
```

## 🎯 Usage Notes

- Replace `/path/to/file.xlsx` with actual file paths
- Replace `{"key": "value"}` with actual parameter dictionaries
- All functions are available through bench commands
- Use `--kwargs` for functions that require parameters
- Functions contain exact code from original files with no dummy values or fallback code

## 📊 Function Categories

### Excel Validation and Sync Functions
- `add_validation_remarks_to_excel()` - Main validation function
- `sync_missing_orders_from_excel()` - Main sync function
- Helper functions: `_safe_convert_to_float()`, `_normalize_header()`, `_find_best_column()`, `_norm_id()`, `_sanitize_order_code_for_api()`

### Monthly Uniware Report Functions
- `trigger_previous_month_sale_order_export()` - Main export function
- `process_monthly_export_with_download()` - Complete workflow
- `check_export_job_status()` - Status checking
- `download_and_merge_csv_files()` - File processing
- Helper functions: `validate_unicommerce_settings()`, `create_export_job()`, `get_export_columns_from_settings()`

### Pivot Table Creator Functions
- `create_complete_pivot_analysis()` - Main analysis function
- `create_master_data_sheet()` - Master data creation
- `create_pivot_tables()` - Pivot table creation
- `create_pivot_analysis_for_existing_file()` - Existing file analysis
- Helper functions: `_safe_convert_to_float()`, `_clean_facility_name()`, `_extract_month_from_date()`, `_standardize_column_names()`, `_add_calculated_columns()`, `_reorder_columns()`, `_reorder_workbook_sheets()`, `_style_master_data_sheet()`, `_create_excel_pivot_table()`, `_create_second_pivot_table()`, `_send_pivot_analysis_email()`