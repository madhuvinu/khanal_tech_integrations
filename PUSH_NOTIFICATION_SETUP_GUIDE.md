# Push Notification Setup Guide

## ✅ Implementation Status

### **Completed:**
1. ✅ Backend API endpoints created
2. ✅ Frappe doctypes created (Push Subscription, Push Notification Log)
3. ✅ VAPID key generation script created
4. ✅ Frontend service created
5. ✅ Service worker configured
6. ✅ Composable and store created
7. ✅ Dependencies added to requirements.txt

### **Next Steps:**

## 📋 Setup Instructions

### **1. Install Python Dependencies**

```bash
cd ~/frappe-bench
bench pip install pywebpush==1.14.0
bench pip install --upgrade cryptography
```

Or install from requirements.txt:
```bash
bench pip install -r apps/khanal_tech_integrations/requirements.txt
```

### **2. Reload Frappe to Register New Doctypes**

```bash
bench --site [your-site-name] migrate
bench clear-cache
bench restart
```

### **3. Generate VAPID Keys**

```bash
bench --site [your-site-name] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys
```

#### **What are VAPID Keys?**

**VAPID** (Voluntary Application Server Identification) keys are cryptographic keys used to identify your server to push notification services (like Google's FCM). They work like a digital signature that proves your server is authorized to send push notifications.

**Why do we need them?**
- **Security**: Prevents unauthorized servers from sending push notifications to your users
- **Authentication**: Browser push services (FCM, Mozilla Push Service) require VAPID keys to verify your server's identity
- **Required by Web Push Protocol**: All web push notifications must use VAPID keys

**What gets generated?**
- **Public Key**: Shared with browsers during subscription (safe to expose)
- **Private Key**: Kept secret on your server (used to sign notifications)

#### **Do we need to generate them every time?**

**NO! You only generate them ONCE per site.**

- ✅ **Generate once**: When you first set up push notifications
- ✅ **Stored permanently**: Keys are saved in your Frappe site config
- ✅ **Reused forever**: Same keys are used for all future push notifications
- ❌ **Don't regenerate**: Generating new keys will break existing subscriptions (users would need to re-subscribe)

**When would you regenerate?**
- Only if the keys are lost or compromised
- If you're setting up a new site/environment
- If you intentionally want to invalidate all existing subscriptions

**Important:** The script will:
- Generate VAPID public and private keys
- Store them securely in site config (not in code)
- Display the public key (you can copy it, but it's also stored automatically)
- The private key is stored securely and never displayed

### **4. Verify Installation**

Check that doctypes are created:
```bash
bench --site [your-site-name] console
```

In console:
```python
import frappe
frappe.get_doc("DocType", "Push Subscription")
frappe.get_doc("DocType", "Push Notification Log")
```

### **5. Test Backend API**

Test the VAPID key endpoint:
```bash
curl -X GET "http://localhost:8000/api/method/khanal_tech_integrations.api.push_notifications.get_vapid_public_key_api" \
  -H "Cookie: sid=your-session-id"
```

### **6. Frontend Integration**

The frontend code is ready. To use it in your Vue components:

```javascript
import { usePushNotifications } from '@/composables/usePushNotifications'

const {
  isSupported,
  permission,
  isSubscribed,
  canSubscribe,
  needsPermission,
  requestPermission,
  subscribe,
  unsubscribe,
  toggle
} = usePushNotifications()
```

Or use the store:
```javascript
import { usePushNotificationsStore } from '@/stores/pushNotifications'

const pushStore = usePushNotificationsStore()
await pushStore.initialize()
```

## 🧪 Testing

### **Test Subscription:**
1. Open your app in browser
2. Initialize push notifications
3. Request permission
4. Subscribe
5. Check Frappe: `Push Subscription` doctype should have a record

### **Test Sending Notification:**

In Frappe console or via API:
```python
from khanal_tech_integrations.api.push_notifications import send_push_notification

result = send_push_notification(
    user="user@example.com",
    title="Test Notification",
    message="This is a test push notification",
    data={
        "type": "test",
        "route": "/dashboard"
    }
)
```

## ⚠️ Important Notes

1. **HTTPS Required:** Push notifications only work over HTTPS in production (localhost is exception)
2. **Browser Support:** Chrome, Firefox, Edge support. Safari has limited support.
3. **Service Worker:** Must be registered and active
4. **VAPID Keys:** Keep private key secure, never expose it

## 🔧 Troubleshooting

### **Issue: VAPID keys not found**
- Solution: Run the VAPID key generation script

### **Issue: Service worker not registering**
- Check browser console for errors
- Verify service worker file exists at `/sw.js`
- Check VitePWA configuration

### **Issue: Permission denied**
- User must explicitly grant permission
- Check browser notification settings
- Some browsers require user interaction to request permission

### **Issue: Subscription fails**
- Verify VAPID public key is correct
- Check network tab for API errors
- Verify backend API is accessible

## 📚 Next Steps

1. Create UI component for permission prompt
2. Add notification settings page
3. Integrate with existing notification system
4. Add notification triggers for production orders, GRN, etc.
5. Test end-to-end flow

