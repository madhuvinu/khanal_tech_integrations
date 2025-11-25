# Push Notifications - Production Deployment Guide

## ✅ HTTPS Site: https://65.1.189.119/

Your production site uses HTTPS, which is **required** for service workers and push notifications to work.

---

## 📋 Pre-Deployment Checklist

### 1. **VAPID Keys on Production Server**

VAPID keys must be generated on your production server:

```bash
# SSH into your production server
ssh user@65.1.189.119

# Navigate to your bench directory
cd ~/frappe-bench

# Generate VAPID keys for your production site
bench --site [your-production-site-name] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys
```

**Important:** 
- Generate keys **once** on the production server
- Use your production admin email: `kflharshkfl@gmail.com` (or your production email)
- Keys are stored in `sites/[site-name]/site_config.json`

### 2. **Install Python Dependencies**

```bash
# On production server
cd ~/frappe-bench
bench pip install pywebpush==1.14.0
bench pip install cryptography==45.0.7
```

Or from requirements.txt:
```bash
bench pip install -r apps/khanal_tech_integrations/requirements.txt
```

### 3. **Deploy Frontend Build**

Build the frontend and deploy to production:

```bash
# On your local machine (or CI/CD)
cd kiosk-frontend
yarn build

# The build output goes to:
# ../khanal_tech_integrations/public/kiosk/
```

Then deploy the `public/kiosk/` directory to your production server.

### 4. **Verify Doctypes**

Make sure the doctypes are created on production:

```bash
# On production server
bench --site [site-name] migrate
bench clear-cache
bench restart
```

### 5. **Test Service Worker Accessibility**

After deployment, verify the service worker is accessible:

```bash
curl -I https://65.1.189.119/assets/khanal_tech_integrations/kiosk/sw.js
```

Should return `200 OK`.

---

## 🔧 Production Configuration

### Service Worker Scope

On HTTPS, the service worker can control `/kiosk/` paths even if it's located at `/assets/khanal_tech_integrations/kiosk/sw.js`.

The code automatically:
- Uses the service worker's directory as scope (works on HTTPS)
- Falls back to `/kiosk/` if needed

### Optional: Add Service-Worker-Allowed Header

If you want to ensure the service worker can control `/kiosk/` paths, add this to your nginx config:

```nginx
location ~* /assets/khanal_tech_integrations/kiosk/sw\.js$ {
    add_header Service-Worker-Allowed /;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

---

## 🧪 Testing on Production

### 1. **Open Your Production Site**

```
https://65.1.189.119/kiosk/plant/nandi-hills/production-order
```

### 2. **Check Browser Console**

Open DevTools (F12) and check:
- Service worker registration status
- Push notification support
- Any errors

### 3. **Test Push Notification**

1. Click the "🔔 Test Push" button
2. Allow notifications when prompted
3. Check if notification appears

### 4. **Verify Subscription**

Check in Frappe:
```python
# In Frappe console
frappe.get_all("Push Subscription", filters={"is_active": 1})
```

---

## 🚨 Common Issues

### Issue 1: "Service worker registration failed"

**Solution:**
- Verify service worker file is accessible: `https://65.1.189.119/assets/khanal_tech_integrations/kiosk/sw.js`
- Check browser console for specific errors
- Ensure HTTPS is properly configured

### Issue 2: "VAPID keys not found"

**Solution:**
- Generate VAPID keys on production server (see step 1)
- Verify keys in `sites/[site-name]/site_config.json`

### Issue 3: "Push subscription failed"

**Solution:**
- Check VAPID public key is accessible via API
- Verify user has granted notification permission
- Check browser console for errors

---

## 📝 Production Checklist

- [ ] VAPID keys generated on production server
- [ ] Python dependencies installed (`pywebpush`, `cryptography`)
- [ ] Frontend built and deployed
- [ ] Doctypes migrated on production
- [ ] Service worker accessible at `/assets/khanal_tech_integrations/kiosk/sw.js`
- [ ] HTTPS properly configured
- [ ] Test push notification works
- [ ] Subscriptions are being created in Frappe

---

## 🔐 Security Notes

1. **VAPID Private Key**: Never expose or commit to git
2. **HTTPS Required**: Push notifications only work over HTTPS (except localhost)
3. **User Permissions**: Users must explicitly grant notification permission
4. **Rate Limiting**: Consider adding rate limiting to push notification API

---

## 📞 Support

If you encounter issues:
1. Check browser console (F12) for errors
2. Check Frappe logs: `bench --site [site] logs`
3. Verify VAPID keys: `cat sites/[site]/site_config.json | grep vapid`
4. Test service worker: `curl -I https://65.1.189.119/assets/khanal_tech_integrations/kiosk/sw.js`

