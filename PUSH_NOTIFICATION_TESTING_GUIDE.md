# Push Notification Testing Guide

## ✅ Testing on Localhost

**Yes, it will work on `http://kfltest.localhost:8003`!**

Localhost is an **exception** to the HTTPS requirement for push notifications. You can test fully on localhost.

---

## 🧪 Step-by-Step Testing

### **1. Open Your App**

Navigate to:
```
http://kfltest.localhost:8003/kiosk/plant/nandi-hills/production-order
```

### **2. Check Browser Console**

Open browser DevTools (F12) and check the console. You should see:
```
Push notifications initialized: { isSupported: true, permission: "default" }
```

### **3. Request Permission**

The app will auto-initialize push notifications. To subscribe:

**Option A: Via Browser Console**
```javascript
// Check if push is supported
console.log('Push supported:', 'serviceWorker' in navigator && 'PushManager' in window)

// Request permission manually
const permission = await Notification.requestPermission()
console.log('Permission:', permission)

// Subscribe (if you have access to the composable)
// This will be done automatically or via UI
```

**Option B: Create a Test Button** (temporary for testing)

Add this to your ProductionOrder page temporarily:

```vue
<button @click="testPushSubscribe" class="bg-blue-500 text-white px-4 py-2 rounded">
  Subscribe to Push Notifications
</button>

<script setup>
import { usePushNotifications } from '@/composables/usePushNotifications'

const { subscribe, requestPermission, permission, isSubscribed } = usePushNotifications()

async function testPushSubscribe() {
  if (permission.value !== 'granted') {
    await requestPermission()
  }
  if (permission.value === 'granted') {
    await subscribe()
    alert('Subscribed! Check Frappe for Push Subscription record.')
  }
}
</script>
```

### **4. Verify Subscription in Frappe**

After subscribing, check Frappe:
```bash
# In Frappe console or via API
bench --site kfltest.localhost console
```

```python
import frappe
subscriptions = frappe.get_all("Push Subscription", filters={"is_active": 1})
print(subscriptions)
```

### **5. Test Sending a Notification**

**Via Frappe Console:**
```python
from khanal_tech_integrations.api.push_notifications import send_push_notification

result = send_push_notification(
    user="your-email@example.com",  # Your logged-in user
    title="Test Notification",
    message="This is a test push notification from localhost!",
    data={
        "type": "test",
        "route": "/kiosk/plant/nandi-hills/production-order"
    }
)

print(result)
```

**Via API:**
```bash
curl -X POST "http://kfltest.localhost:8003/api/method/khanal_tech_integrations.api.push_notifications.send_push_notification_api" \
  -H "Content-Type: application/json" \
  -H "Cookie: sid=your-session-id" \
  -d '{
    "user": "your-email@example.com",
    "title": "Test Notification",
    "message": "Testing push notifications!",
    "data": {
      "type": "test",
      "route": "/kiosk/plant/nandi-hills/production-order"
    }
  }'
```

### **6. What to Expect**

1. **Permission Prompt**: Browser will ask for notification permission
2. **Subscription**: After granting, subscription is saved to Frappe
3. **Notification**: When you send a test notification, you should see:
   - A browser notification popup
   - Even if the tab is closed (after first permission)

---

## 🔍 Troubleshooting

### **Issue: "Push notifications are not supported"**
- **Check**: Browser must support Push API (Chrome, Firefox, Edge)
- **Check**: Service worker must be registered
- **Solution**: Check browser console for errors

### **Issue: "Permission denied"**
- **Check**: User must grant permission
- **Solution**: Go to browser settings → Site settings → Notifications → Allow

### **Issue: "VAPID keys not configured"**
- **Check**: Verify keys are in site_config.json
- **Solution**: Re-run VAPID key generation

### **Issue: "Service worker not registered"**
- **Check**: Check Application tab in DevTools → Service Workers
- **Solution**: Clear cache and reload, or rebuild frontend

### **Issue: "Subscription failed"**
- **Check**: Browser console for API errors
- **Check**: Verify backend API is accessible
- **Solution**: Check network tab for failed requests

---

## 📊 Verification Checklist

- [ ] Push notifications initialized (check console)
- [ ] Permission granted (check browser notification settings)
- [ ] Subscription created (check Frappe: Push Subscription doctype)
- [ ] Test notification received (send test notification)
- [ ] Notification appears even when tab is closed

---

## 🎯 Quick Test Script

Add this to browser console on your page:

```javascript
// Test push notification flow
async function testPush() {
  // 1. Check support
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.error('Push not supported')
    return
  }
  
  // 2. Request permission
  const permission = await Notification.requestPermission()
  console.log('Permission:', permission)
  
  if (permission !== 'granted') {
    console.error('Permission denied')
    return
  }
  
  // 3. Get service worker
  const registration = await navigator.serviceWorker.ready
  
  // 4. Get VAPID key from backend
  const response = await fetch('/api/method/khanal_tech_integrations.api.push_notifications.get_vapid_public_key_api')
  const data = await response.json()
  const publicKey = data.message.public_key
  
  // 5. Subscribe
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey)
  })
  
  // 6. Send to backend
  const subData = {
    endpoint: subscription.endpoint,
    keys: {
      p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
      auth: arrayBufferToBase64(subscription.getKey('auth'))
    }
  }
  
  const saveResponse = await fetch('/api/method/khanal_tech_integrations.api.push_notifications.subscribe_push', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subData)
  })
  
  console.log('Subscription saved:', await saveResponse.json())
}

// Helper functions
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return window.btoa(binary)
}

// Run test
testPush()
```

---

## ✅ Success Indicators

When everything works, you should see:
1. ✅ Console: "Push notifications initialized"
2. ✅ Browser: Permission granted
3. ✅ Frappe: Push Subscription record created
4. ✅ Notification: Test notification appears
5. ✅ Works when tab is closed (after first permission)

Good luck testing! 🚀

