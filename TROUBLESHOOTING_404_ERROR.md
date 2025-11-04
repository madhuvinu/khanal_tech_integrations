# Troubleshooting 404 Error - API Endpoints Not Found

## 🔴 **Error:**
```
Failed to load resource: the server responded with a status of 404 (NOT FOUND)
/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details
```

## ✅ **Solutions (Try in Order):**

---

## **Solution 1: Restart Frappe Server** ⚠️ **MOST LIKELY FIX**

Frappe needs to reload Python modules to register new endpoints.

### **Steps:**
```bash
# Stop the current Frappe server (Ctrl+C)
# Then restart:
cd /Users/harshakm/frappe-bench
bench start
```

**OR** if using process manager:
```bash
bench restart
```

**Why:** Frappe loads Python modules at startup. New endpoints need server restart to be registered.

---

## **Solution 2: Clear Browser Cache** 🧹

Sometimes cached API responses cause issues.

### **Steps:**
1. Open browser DevTools (F12)
2. Right-click on refresh button
3. Select "Empty Cache and Hard Reload"
4. Or use: `Ctrl+Shift+R` (Windows) / `Cmd+Shift+R` (Mac)

---

## **Solution 3: Verify Backend Endpoint Path** ✅

Check if the endpoint path matches the Python module structure.

### **Current Endpoint:**
```
/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details
```

### **Python File Structure:**
```
khanal_tech_integrations/
  api/
    plants/
      nandi_hills/
        disassembly.py
          └── get_disassembly_details()  # ✅ Function exists
```

### **Verify Function is Decorated:**
```python
# disassembly.py should have:
@frappe.whitelist(allow_guest=False)
def get_disassembly_details(doc_num):
    # ... function code
```

✅ **This looks correct!** The path matches the module structure.

---

## **Solution 4: Test Endpoint Directly** 🧪

Test if the endpoint works via browser/curl.

### **In Browser:**
1. Open: `http://localhost:8000/api/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details`
2. If you see a form/JSON response → Endpoint exists ✅
3. If you see 404 → Endpoint not registered ❌

### **Via Terminal:**
```bash
curl -X POST http://localhost:8000/api/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details \
  -H "Content-Type: application/json" \
  -d '{"doc_num": "37491"}' \
  --cookie "sid=YOUR_SESSION_ID"
```

---

## **Solution 5: Check Frappe Console** 🔍

Verify the endpoint is registered in Frappe.

### **Steps:**
1. Go to Frappe Console: `http://localhost:8000/app/console`
2. Run:
```python
import frappe
from khanal_tech_integrations.api.plants.nandi_hills.disassembly import get_disassembly_details

# Check if function exists
print(get_disassembly_details)
# Should show: <function get_disassembly_details at ...>

# Check if it's whitelisted
print(frappe.get_attr('khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details'))
```

If you get an error → Module not loaded properly ❌

---

## **Solution 6: Verify __init__.py Files** 📁

Ensure all `__init__.py` files exist and import correctly.

### **Check:**
1. ✅ `khanal_tech_integrations/api/__init__.py` exists
2. ✅ `khanal_tech_integrations/api/plants/__init__.py` exists
3. ✅ `khanal_tech_integrations/api/plants/nandi_hills/__init__.py` exists
4. ✅ `khanal_tech_integrations/api/plants/nandi_hills/__init__.py` imports `disassembly`

### **Current __init__.py:**
```python
# khanal_tech_integrations/api/plants/nandi_hills/__init__.py
from .disassembly import (
    get_disassembly_details,
    create_goods_issue,
    create_goods_receipt,
    get_completed_disassemblies,
    backfill_production_order_docentry
)
```
✅ **This looks correct!**

---

## **Solution 7: Check Base URL** 🌐

Verify the frontend is using the correct base URL.

### **Current Code:**
```javascript
// baseService.js
const BASE_URL = window.location.origin  // Should be: http://localhost:8003 or http://localhost:8000
```

### **Check:**
1. Open browser console
2. Check what URL is being called:
```javascript
console.log(window.location.origin)
// Should match your Frappe server URL
```

### **If Wrong:**
Update `baseService.js`:
```javascript
const BASE_URL = 'http://localhost:8000'  // Or your server URL
```

---

## **Solution 8: Check Authentication** 🔐

404 can also mean authentication failed.

### **Verify:**
1. Check if you're logged in
2. Check if CSRF token is set:
```javascript
console.log(window.csrf_token)
// Should show a token, not undefined
```

3. Check if session cookie exists in browser DevTools → Application → Cookies

---

## **Solution 9: Rebuild Frontend** 🏗️

If frontend code changed, rebuild it.

### **Steps:**
```bash
cd /Users/harshakm/frappe-bench/apps/khanal_tech_integrations/kiosk-frontend
npm run build
# OR
yarn build
```

Then restart Frappe server.

---

## **Solution 10: Check Frappe Logs** 📝

Look for errors in Frappe logs.

### **Steps:**
```bash
# Check Frappe logs
cd /Users/harshakm/frappe-bench
bench --site YOUR_SITE_NAME logs

# Or check console output when starting server
bench start
# Look for import errors or module loading issues
```

---

## 🎯 **Most Likely Fix:**

**99% of the time, it's Solution 1: Restart Frappe Server**

### **Quick Fix:**
```bash
# Stop server (Ctrl+C)
# Restart
cd /Users/harshakm/frappe-bench
bench start
```

---

## ✅ **Verification Checklist:**

After applying fixes, verify:

- [ ] Frappe server restarted
- [ ] Browser cache cleared
- [ ] Endpoint path matches Python module structure
- [ ] Function has `@frappe.whitelist()` decorator
- [ ] `__init__.py` files import correctly
- [ ] Base URL is correct
- [ ] User is authenticated
- [ ] CSRF token exists
- [ ] No errors in Frappe logs

---

## 🔧 **Quick Debug Script:**

Add this to your browser console to test:

```javascript
// Test endpoint directly
async function testEndpoint() {
  const endpoint = '/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details'
  const url = `${window.location.origin}${endpoint}`
  
  console.log('Testing URL:', url)
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': window.csrf_token
      },
      credentials: 'include',
      body: JSON.stringify({ doc_num: '37491' })
    })
    
    console.log('Status:', response.status)
    console.log('Response:', await response.text())
  } catch (error) {
    console.error('Error:', error)
  }
}

testEndpoint()
```

---

## 📞 **If Still Not Working:**

1. Check if other endpoints work (e.g., GRN endpoints)
2. Compare working endpoint with failing one
3. Check Frappe error logs
4. Verify Python module can be imported
5. Check if there are any syntax errors in `disassembly.py`

---

## 🎯 **Summary:**

**Most Common Fix:** Restart Frappe server ✅

**Check Order:**
1. Restart server
2. Clear cache
3. Verify endpoint path
4. Check authentication
5. Check logs

Good luck! 🚀

