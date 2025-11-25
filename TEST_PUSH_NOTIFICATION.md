# Quick Push Notification Test Guide

## ✅ Backend Status: WORKING
- VAPID keys generated ✓
- API endpoint working ✓
- Public key available ✓

## 🧪 How to Test

### **Step 1: Build Frontend**
```bash
cd kiosk-frontend
yarn build
```

### **Step 2: Open Your App**
```
http://kfltest.localhost:8003/kiosk/plant/nandi-hills/production-order
```

### **Step 3: Click Test Button**
1. Look for the **"🔔 Test Push"** button (green button next to Refresh)
2. Click it
3. Browser will ask for notification permission → Click **"Allow"**
4. Wait for the alert message

### **Step 4: Check Results**

**Expected Success:**
- Alert shows: "✅ Test notification sent!"
- Browser notification popup appears
- Notification shows: "🧪 Test Push Notification"

**If Error:**
- Check browser console (F12) for error messages
- Check if you're logged in
- Verify backend is running

## 🔍 Troubleshooting

### **Error: "Push notifications are not supported"**
- Use Chrome, Firefox, or Edge (Safari has limited support)
- Check browser console for details

### **Error: "Permission denied"**
- Go to browser settings → Site settings → Notifications
- Allow notifications for kfltest.localhost

### **Error: "VAPID keys not configured"**
- Already verified - keys are working ✓

### **No notification appears**
- Check if subscription was created in Frappe
- Check browser console for errors
- Verify service worker is registered (Application tab in DevTools)

## 📊 Verify Subscription in Frappe

After clicking the test button, check if subscription was created:

```bash
bench --site kfltest.localhost console
```

```python
import frappe
subscriptions = frappe.get_all("Push Subscription", filters={"is_active": 1})
print(f"Active subscriptions: {len(subscriptions)}")
for sub in subscriptions:
    print(f"  - User: {sub.user}, Endpoint: {sub.endpoint[:50]}...")
```

## ✅ Success Checklist

- [ ] Button visible on page
- [ ] Click button → Permission prompt appears
- [ ] Grant permission → Subscription created
- [ ] Alert shows "Test notification sent!"
- [ ] Browser notification appears
- [ ] Subscription record in Frappe

---

**Ready to test!** Just build, open the page, and click the button! 🚀

