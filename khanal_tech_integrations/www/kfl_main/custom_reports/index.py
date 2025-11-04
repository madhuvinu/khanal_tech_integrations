import frappe
from frappe import _
import khanal_tech_integrations.utils.Dashboard_Reports.dashboard_custom_report_queries as dashboard_custom_report_queries

def get_context(context):
    context.no_cache = True  # Prevent browser caching
    selected_report_name = frappe.form_dict.get("report_name")
    # Your report data logic here
    context.report_name = selected_report_name
    context.title = f"Report: {selected_report_name}"
    context.timestamp = frappe.utils.now()  # Add timestamp to prevent caching


    print(f"Report Name from form_dict: {selected_report_name}")
    # Fetch fresh report queries instead of using cached session data
    allowed_reports = dashboard_custom_report_queries.fetch_custom_reports_queries()
    print(f"Allowed Reports from fresh query: {allowed_reports}")
    names = [report['name'] for report in allowed_reports]
    print(f"Allowed Report Names: {names}")

    if selected_report_name not in names:
        frappe.throw(_("You do not have permission to access this report."), frappe.PermissionError)

    selected_report_display_name = next((r['report_name'] for r in allowed_reports if r['name'] == selected_report_name), None)
    context.report_display_name = selected_report_display_name or "Custom Report"
    # Select the template to render based on selected_report_name
    if selected_report_name == "sales_summary_report":
        context.template = "khanal_tech_integrations/www/kfl_main/custom_reports/sales_summary_report.html"
    else:
        context.template = "khanal_tech_integrations/www/kfl_main/custom_reports/generic_custom_report.html"

    print(f"Rendering template: {context.template}")
    # Render the selected template and return HTML
    html = frappe.render_template(context.template, context)

    # Write directly to response
    frappe.response["type"] = "page"
    frappe.response["response"] = html

    # Returning context won't matter — we're overriding rendering
    return context
