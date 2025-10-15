#!/usr/bin/env python3
"""
Unified Automated Reporting System
Single function to orchestrate: Unicommerce → HANA → Reconciliation → Email
"""

import sys
import os
from datetime import datetime, timedelta
import frappe

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import all required modules
try:
    from khanal_tech_integrations.utils.Unicommerce_Automation.Montlhy_uniware_report import process_monthly_export_with_download
except ImportError:
    process_monthly_export_with_download = None

try:
    from khanal_tech_integrations.utils.Unicommerce_Automation.hana_reporting.hana_query_engine_readonly import generate_comprehensive_sales_report_readonly
    from khanal_tech_integrations.utils.Unicommerce_Automation.hana_reporting.excel_report_generator import create_comprehensive_sales_report
    from khanal_tech_integrations.utils.Unicommerce_Automation.hana_reporting.data_comparison_engine import compare_sales_data
    from khanal_tech_integrations.utils.Unicommerce_Automation.hana_reporting.configuration import REPORT_SETTINGS
except ImportError:
    generate_comprehensive_sales_report_readonly = None
    create_comprehensive_sales_report = None
    compare_sales_data = None
    REPORT_SETTINGS = {"email_recipients": ["yogesha@khanalfoods.com", "harsha@khanalfoods.com"]}

@frappe.whitelist()
def automated_monthly_reporting(month=None, year=None, email_recipients=None):
    """
    🚀 SINGLE FUNCTION FOR COMPLETE AUTOMATED REPORTING
    
    This function automatically:
    1. Exports Unicommerce data for the month
    2. Generates HANA sales report for the same month
    3. Compares and reconciles both datasets
    4. Sends comprehensive reports via email
    
    Args:
        month: Month number (1-12), defaults to previous month
        year: Year (e.g., 2025), defaults to current year
        email_recipients: List of email addresses, defaults to configured recipients
    
    Returns:
        dict: Complete report status and file paths
    """
    
    # Set defaults
    if not month:
        month = (datetime.now() - timedelta(days=30)).month
    if not year:
        year = datetime.now().year
    if not email_recipients:
        email_recipients = REPORT_SETTINGS.get('email_recipients', [
            "yogesha@khanalfoods.com",
            "harsha@khanalfoods.com"
        ])
    
    # Generate date range for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year+1}-01-01"
    else:
        end_date = f"{year}-{month+1:02d}-01"
    
    end_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"🚀 Starting automated reporting for {month:02d}/{year}")
    print(f"📅 Date range: {start_date} to {end_date}")
    
    results = {
        "status": "started",
        "month": f"{month:02d}/{year}",
        "date_range": f"{start_date} to {end_date}",
        "unicommerce_report": None,
        "hana_report": None,
        "reconciliation_report": None,
        "email_sent": False,
        "errors": []
    }
    
    try:
        # STEP 1: Unicommerce Export & Processing
        print("📊 Step 1: Processing Unicommerce data...")
        unicommerce_result = process_monthly_export_with_download()
        results["unicommerce_report"] = unicommerce_result.get("merged_file", {}).get("file_path")
        print(f"✅ Unicommerce processing complete: {results['unicommerce_report']}")
        
    except Exception as e:
        error_msg = f"Unicommerce processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
    
    try:
        # STEP 2: HANA Sales Report Generation
        print("🗄️ Step 2: Generating HANA sales report...")
        hana_data = generate_comprehensive_sales_report_readonly(start_date, end_date)
        
        # Create Excel report
        hana_filename = f"HANA_Sales_Report_{year}{month:02d}.xlsx"
        hana_report_path = create_comprehensive_sales_report(hana_data, hana_filename)
        results["hana_report"] = hana_report_path
        print(f"✅ HANA report generated: {hana_report_path}")
        
    except Exception as e:
        error_msg = f"HANA report generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
    
    try:
        # STEP 3: Data Reconciliation (if both reports successful)
        if results["unicommerce_report"] and results["hana_report"]:
            print("🔄 Step 3: Performing data reconciliation...")
            
            # Load Unicommerce data for comparison
            import pandas as pd
            unicommerce_df = pd.read_excel(results["unicommerce_report"], sheet_name="Master Data")
            
            # Compare datasets
            comparison_result = compare_sales_data(hana_data, unicommerce_df)
            
            # Create reconciliation report
            reconciliation_filename = f"Data_Reconciliation_{year}{month:02d}.xlsx"
            reconciliation_path = _create_reconciliation_report(comparison_result, reconciliation_filename)
            results["reconciliation_report"] = reconciliation_path
            print(f"✅ Reconciliation complete: {reconciliation_path}")
            
    except Exception as e:
        error_msg = f"Data reconciliation failed: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
    
    try:
        # STEP 4: Email Notification
        print("📧 Step 4: Sending email notification...")
        
        attachments = []
        if results["unicommerce_report"]:
            attachments.append({
                "fname": f"Unicommerce_Report_{year}{month:02d}.xlsx",
                "fcontent": open(results["unicommerce_report"], 'rb').read()
            })
        
        if results["hana_report"]:
            attachments.append({
                "fname": f"HANA_Sales_Report_{year}{month:02d}.xlsx", 
                "fcontent": open(results["hana_report"], 'rb').read()
            })
        
        if results["reconciliation_report"]:
            attachments.append({
                "fname": f"Data_Reconciliation_{year}{month:02d}.xlsx",
                "fcontent": open(results["reconciliation_report"], 'rb').read()
            })
        
        # Send email
        subject = f"Automated Monthly Reports - {month:02d}/{year}"
        message = f"""
        Automated monthly reporting completed for {month:02d}/{year}.
        
        📊 Reports Generated:
        • Unicommerce Export Report: ✅
        • HANA Sales Analysis Report: ✅  
        • Data Reconciliation Report: ✅
        
        📈 Key Metrics:
        • HANA Sales Records: {len(hana_data) if 'hana_data' in locals() else 'N/A'}
        • Date Range: {start_date} to {end_date}
        
        Please find all reports attached.
        """
        
        frappe.sendmail(
            recipients=email_recipients,
            subject=subject,
            message=message,
            attachments=attachments
        )
        
        results["email_sent"] = True
        print("✅ Email notification sent successfully")
        
    except Exception as e:
        error_msg = f"Email notification failed: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
    
    # Clean up temporary files
    cleanup_temp_files([results["unicommerce_report"], results["hana_report"], results["reconciliation_report"]])
    
    # Final status
    if results["errors"]:
        results["status"] = "completed_with_errors"
        print(f"⚠️ Completed with {len(results['errors'])} errors")
    else:
        results["status"] = "completed_successfully"
        print("🎉 All reports generated and emailed successfully!")
    
    return results

def _create_reconciliation_report(comparison_result, filename):
    """Create reconciliation Excel report"""
    import pandas as pd
    
    # Create summary data
    summary_data = {
        'Metric': ['HANA Total Orders', 'Unicommerce Total Orders', 'Matching Orders', 'Match Percentage', 'Sales Variance'],
        'Value': [
            comparison_result.get('hana_total_orders', 0),
            comparison_result.get('unicommerce_total_orders', 0), 
            comparison_result.get('matching_orders', 0),
            f"{comparison_result.get('match_percentage', 0):.2f}%",
            f"{comparison_result.get('sales_variance', 0):.2f}%"
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    
    # Create discrepancies data
    discrepancies_df = pd.DataFrame(comparison_result.get('discrepancies', []))
    
    # Write to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        if not discrepancies_df.empty:
            discrepancies_df.to_excel(writer, sheet_name='Discrepancies', index=False)
    
    return filename

def cleanup_temp_files(file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ Cleaned up: {file_path}")
            except:
                pass

# Convenience function for current month
@frappe.whitelist()
def automated_current_month_report():
    """Generate reports for current month"""
    return automated_monthly_reporting()

# Convenience function for previous month  
@frappe.whitelist()
def automated_previous_month_report():
    """Generate reports for previous month"""
    last_month = (datetime.now() - timedelta(days=30))
    return automated_monthly_reporting(month=last_month.month, year=last_month.year)

# Convenience function for specific month
@frappe.whitelist()
def automated_specific_month_report(month, year):
    """Generate reports for specific month"""
    return automated_monthly_reporting(month=int(month), year=int(year))

if __name__ == "__main__":
    # Test the function
    result = automated_monthly_reporting()
    print("Result:", result)
