"""
Activity Logging API for Plant-Specific Kiosk System
Handles real-time activity tracking and audit trail
"""

import frappe
import json
from datetime import datetime, timedelta
from frappe import _
from frappe.utils import now, get_datetime
import uuid

@frappe.whitelist()
def log_activity(activity_data):
    """
    Log a single activity
    
    Args:
        activity_data (dict): Activity data
    
    Returns:
        dict: Log result
    """
    try:
        # Parse activity_data if it's a string
        if isinstance(activity_data, str):
            activity_data = json.loads(activity_data)
        
        # Validate required fields
        required_fields = ["user_id", "plant_id", "activity_type", "timestamp"]
        for field in required_fields:
            if field not in activity_data:
                frappe.throw(f"Missing required field: {field}")
        
        # Create activity log document
        activity_doc = frappe.get_doc({
            "doctype": "Kiosk Activity Log",
            "activity_id": activity_data.get("id", str(uuid.uuid4())),
            "user": activity_data["user_id"],
            "plant": activity_data["plant_id"],
            "activity_type": activity_data["activity_type"],
            "page": activity_data.get("page", ""),
            "action": activity_data.get("action", ""),
            "duration": activity_data.get("duration", 0),
            "timestamp": get_datetime(activity_data["timestamp"]),
            "metadata": json.dumps(activity_data.get("metadata", {})),
            "ip_address": frappe.get_request_header("X-Forwarded-For") or frappe.local.request_ip,
            "user_agent": frappe.get_request_header("User-Agent")
        })
        
        activity_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "activity_id": activity_doc.activity_id,
            "message": "Activity logged successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error logging activity: {str(e)}")
        return {
            "success": False,
            "message": "Error logging activity"
        }

@frappe.whitelist()
def log_batch_activities(activities):
    """
    Log multiple activities in batch
    
    Args:
        activities (list): List of activity data
    
    Returns:
        dict: Batch log result
    """
    try:
        # Parse activities if it's a string
        if isinstance(activities, str):
            activities = json.loads(activities)
        
        logged_count = 0
        errors = []
        
        for activity_data in activities:
            try:
                result = log_activity(activity_data)
                if result.get("success"):
                    logged_count += 1
                else:
                    errors.append(result.get("message", "Unknown error"))
            except Exception as e:
                errors.append(str(e))
        
        return {
            "success": True,
            "logged_count": logged_count,
            "total_count": len(activities),
            "errors": errors
        }
        
    except Exception as e:
        frappe.log_error(f"Error logging batch activities: {str(e)}")
        return {
            "success": False,
            "message": "Error logging batch activities"
        }

@frappe.whitelist()
def get_activity_stats(time_range="today"):
    """
    Get activity statistics for the current user's plant
    
    Args:
        time_range (str): Time range for stats (today, week, month)
    
    Returns:
        dict: Activity statistics
    """
    try:
        user = frappe.get_user()
        plant_id = frappe.get_request_header("X-Plant-ID")
        
        if not plant_id:
            frappe.throw("Plant ID not specified")
        
        # Calculate date range
        now_dt = now()
        if time_range == "today":
            start_date = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == "week":
            start_date = now_dt - timedelta(days=7)
        elif time_range == "month":
            start_date = now_dt - timedelta(days=30)
        else:
            start_date = now_dt - timedelta(days=1)
        
        # Get activity counts by type
        activity_counts = frappe.db.sql("""
            SELECT 
                activity_type,
                COUNT(*) as count
            FROM `tabKiosk Activity Log`
            WHERE 
                user = %s
                AND plant = %s
                AND timestamp >= %s
            GROUP BY activity_type
        """, (user.name, plant_id, start_date), as_dict=True)
        
        # Get total activities
        total_activities = frappe.db.count("Kiosk Activity Log", {
            "user": user.name,
            "plant": plant_id,
            "timestamp": [">=", start_date]
        })
        
        # Get unique users (for admin)
        unique_users = frappe.db.sql("""
            SELECT COUNT(DISTINCT user) as count
            FROM `tabKiosk Activity Log`
            WHERE 
                plant = %s
                AND timestamp >= %s
        """, (plant_id, start_date), as_dict=True)
        
        # Get most active pages
        active_pages = frappe.db.sql("""
            SELECT 
                page,
                COUNT(*) as count
            FROM `tabKiosk Activity Log`
            WHERE 
                user = %s
                AND plant = %s
                AND timestamp >= %s
                AND page != ''
            GROUP BY page
            ORDER BY count DESC
            LIMIT 5
        """, (user.name, plant_id, start_date), as_dict=True)
        
        return {
            "time_range": time_range,
            "start_date": start_date.isoformat(),
            "end_date": now_dt.isoformat(),
            "total_activities": total_activities,
            "unique_users": unique_users[0].count if unique_users else 0,
            "activity_counts": {item.activity_type: item.count for item in activity_counts},
            "active_pages": active_pages
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting activity stats: {str(e)}")
        return {
            "error": "Error getting activity statistics"
        }

@frappe.whitelist()
def get_user_activity_log(user=None, plant_id=None, limit=50, offset=0):
    """
    Get activity log for a user
    
    Args:
        user (str): User email (optional, defaults to current user)
        plant_id (str): Plant ID (optional, defaults to current plant)
        limit (int): Number of records to return
        offset (int): Offset for pagination
    
    Returns:
        dict: Activity log data
    """
    try:
        current_user = frappe.get_user()
        
        # Use current user if not specified
        if not user:
            user = current_user.name
        
        # Use current plant if not specified
        if not plant_id:
            plant_id = frappe.get_request_header("X-Plant-ID")
        
        # Check permissions
        if user != current_user.name and "System Manager" not in [role.role for role in current_user.roles]:
            frappe.throw("Insufficient permissions to view other user's activity")
        
        # Get activity log
        activities = frappe.db.sql("""
            SELECT 
                activity_id,
                activity_type,
                page,
                action,
                duration,
                timestamp,
                metadata,
                ip_address
            FROM `tabKiosk Activity Log`
            WHERE 
                user = %s
                AND plant = %s
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """, (user, plant_id, limit, offset), as_dict=True)
        
        # Get total count
        total_count = frappe.db.count("Kiosk Activity Log", {
            "user": user,
            "plant": plant_id
        })
        
        # Parse metadata
        for activity in activities:
            if activity.metadata:
                try:
                    activity.metadata = json.loads(activity.metadata)
                except:
                    activity.metadata = {}
        
        return {
            "activities": activities,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting user activity log: {str(e)}")
        return {
            "error": "Error getting activity log"
        }

@frappe.whitelist()
def get_plant_activity_summary(plant_id, date_range="today"):
    """
    Get activity summary for a plant (admin only)
    
    Args:
        plant_id (str): Plant ID
        date_range (str): Date range (today, week, month)
    
    Returns:
        dict: Plant activity summary
    """
    try:
        # Check admin permissions
        current_user = frappe.get_user()
        if "System Manager" not in [role.role for role in current_user.roles]:
            frappe.throw("Insufficient permissions")
        
        # Calculate date range
        now_dt = now()
        if date_range == "today":
            start_date = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "week":
            start_date = now_dt - timedelta(days=7)
        elif date_range == "month":
            start_date = now_dt - timedelta(days=30)
        else:
            start_date = now_dt - timedelta(days=1)
        
        # Get plant activity summary
        summary = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_activities,
                COUNT(DISTINCT user) as unique_users,
                AVG(duration) as avg_duration,
                MAX(timestamp) as last_activity
            FROM `tabKiosk Activity Log`
            WHERE 
                plant = %s
                AND timestamp >= %s
        """, (plant_id, start_date), as_dict=True)
        
        # Get activity by hour
        hourly_activity = frappe.db.sql("""
            SELECT 
                HOUR(timestamp) as hour,
                COUNT(*) as count
            FROM `tabKiosk Activity Log`
            WHERE 
                plant = %s
                AND timestamp >= %s
            GROUP BY HOUR(timestamp)
            ORDER BY hour
        """, (plant_id, start_date), as_dict=True)
        
        # Get top users
        top_users = frappe.db.sql("""
            SELECT 
                user,
                COUNT(*) as activity_count
            FROM `tabKiosk Activity Log`
            WHERE 
                plant = %s
                AND timestamp >= %s
            GROUP BY user
            ORDER BY activity_count DESC
            LIMIT 10
        """, (plant_id, start_date), as_dict=True)
        
        return {
            "plant_id": plant_id,
            "date_range": date_range,
            "start_date": start_date.isoformat(),
            "end_date": now_dt.isoformat(),
            "summary": summary[0] if summary else {},
            "hourly_activity": hourly_activity,
            "top_users": top_users
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting plant activity summary: {str(e)}")
        return {
            "error": "Error getting plant activity summary"
        }

@frappe.whitelist()
def export_activity_log(plant_id, start_date, end_date, format="json"):
    """
    Export activity log for a plant (admin only)
    
    Args:
        plant_id (str): Plant ID
        start_date (str): Start date
        end_date (str): End date
        format (str): Export format (json, csv)
    
    Returns:
        dict: Export result
    """
    try:
        # Check admin permissions
        current_user = frappe.get_user()
        if "System Manager" not in [role.role for role in current_user.roles]:
            frappe.throw("Insufficient permissions")
        
        # Get activity log
        activities = frappe.db.sql("""
            SELECT 
                activity_id,
                user,
                plant,
                activity_type,
                page,
                action,
                duration,
                timestamp,
                metadata,
                ip_address,
                user_agent
            FROM `tabKiosk Activity Log`
            WHERE 
                plant = %s
                AND timestamp >= %s
                AND timestamp <= %s
            ORDER BY timestamp DESC
        """, (plant_id, start_date, end_date), as_dict=True)
        
        if format == "json":
            return {
                "success": True,
                "data": activities,
                "count": len(activities)
            }
        elif format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if activities:
                writer = csv.DictWriter(output, fieldnames=activities[0].keys())
                writer.writeheader()
                writer.writerows(activities)
            
            return {
                "success": True,
                "data": output.getvalue(),
                "count": len(activities)
            }
        else:
            frappe.throw("Invalid format. Use 'json' or 'csv'")
        
    except Exception as e:
        frappe.log_error(f"Error exporting activity log: {str(e)}")
        return {
            "error": "Error exporting activity log"
        }
