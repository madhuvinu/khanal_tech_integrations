import frappe
from frappe import _

def get_context(context):
    """Context for kiosk SPA"""
    context.title = _("Khanal Foods Kiosk")
    context.no_cache = 1
    
    # Get site configuration
    site_config = frappe.get_site_config()
    
    # Set base URL dynamically based on site
    context.base_url = frappe.utils.get_url()
    
    # Pass site info to frontend
    context.site_info = {
        'site': frappe.local.site,
        'base_url': context.base_url,
        'api_url': f"{context.base_url}/api",
        'socketio_url': f"{context.base_url.replace('http', 'ws')}/socket.io",
        'is_production': not frappe.conf.developer_mode,
        'developer_mode': frappe.conf.developer_mode
    }

def kiosk_static():
    """Serve static files for kiosk"""
    import os
    from frappe.utils import get_site_path
    
    # Get the requested path
    path = frappe.request.path
    print(f"DEBUG: Requested path: {path}")  # Debug line
    
    # Remove /kiosk prefix
    if path.startswith('/kiosk/'):
        file_path = path[7:]  # Remove '/kiosk/'
    else:
        file_path = path[7:]  # Remove '/kiosk'
    
    print(f"DEBUG: File path: {file_path}")  # Debug line
    
    # Build full file path - use the public directory
    kiosk_dir = os.path.join(frappe.get_app_path('khanal_tech_integrations'), 'public', 'kiosk')
    full_path = os.path.join(kiosk_dir, file_path)
    
    print(f"DEBUG: Kiosk dir: {kiosk_dir}")  # Debug line
    print(f"DEBUG: Full path: {full_path}")  # Debug line
    print(f"DEBUG: File exists: {os.path.exists(full_path)}")  # Debug line
    
    # Security check - ensure file is within kiosk directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(kiosk_dir)):
        frappe.throw("Access denied", frappe.PermissionError)
    
    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        frappe.throw("File not found", frappe.DoesNotExistError)
    
    # Set appropriate headers based on file type
    if file_path.endswith('.js'):
        frappe.local.response.headers['Content-Type'] = 'application/javascript'
    elif file_path.endswith('.css'):
        frappe.local.response.headers['Content-Type'] = 'text/css'
    elif file_path.endswith('.json'):
        frappe.local.response.headers['Content-Type'] = 'application/json'
    elif file_path.endswith('.png'):
        frappe.local.response.headers['Content-Type'] = 'image/png'
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        frappe.local.response.headers['Content-Type'] = 'image/jpeg'
    elif file_path.endswith('.svg'):
        frappe.local.response.headers['Content-Type'] = 'image/svg+xml'
    elif file_path.endswith('.woff2'):
        frappe.local.response.headers['Content-Type'] = 'font/woff2'
    elif file_path.endswith('.woff'):
        frappe.local.response.headers['Content-Type'] = 'font/woff'
    
    # Set cache headers
    frappe.local.response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    
    # Read and return file content
    with open(full_path, 'rb') as f:
        frappe.local.response.filecontent = f.read()
    
    frappe.local.response.type = 'download'
    frappe.local.response.filename = os.path.basename(file_path)

def kiosk_test():
    """Test page for kiosk development mode"""
    context = {
        'title': 'Kiosk Development Mode Test'
    }
    frappe.local.response.update({
        'type': 'page',
        'template': 'kiosk_test.html',
        'context': context
    })

def kiosk_api():
    """API endpoint for kiosk"""
    frappe.local.response.update({
        'status': 'success',
        'message': 'Kiosk API endpoint'
    })
