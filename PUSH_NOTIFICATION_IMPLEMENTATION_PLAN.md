# Push Notification Implementation Plan
## For Frappe + Vue.js Application

---

## 📋 **Overview**

This plan outlines the implementation of **Custom Web Push Notifications** for your self-hosted Frappe-based application with Vue.js frontend. 

**Important**: This is a **custom implementation** using Web Push API and VAPID protocol. We are **NOT using Frappe's built-in push notifications** because:
- Frappe's built-in push only works on Frappe Cloud (we're self-hosted)
- Frappe's built-in push is designed for mobile apps, not web browsers
- We need browser-based web push that works when the app is closed

The system will enable real-time push notifications to users even when the application is not actively open in the browser.

---

## 📝 **Implementation Progress Log**

### ✅ **Phase 1: Backend Setup**
- [x] Plan created and approved
- [x] Document updated to clarify custom implementation (not using Frappe built-in)
- [x] Python dependencies added to requirements.txt (pywebpush==1.14.0, cryptography>=41.0.0)
- [x] Frappe doctypes created (Push Subscription, Push Notification Log)
- [x] VAPID key generation script created (generate_vapid_keys.py)
- [x] API endpoints created (push_notifications.py)

### ⏳ **Phase 2: Frontend Setup**
- [x] Push notification service created (pushNotificationService.js)
- [x] Service worker updated (sw.js, sw-push.js)
- [x] Composable created (usePushNotifications.js)
- [x] Store created (pushNotifications.js)
- [ ] UI components created

### ⏳ **Phase 3: Integration**
- [ ] Integration with existing notifications
- [ ] Notification triggers added
- [ ] UI components created (permission prompt, settings)
- [ ] Testing completed

---

## 🚀 **Next Steps for Testing:**

1. **Generate VAPID Keys** (see Installation Steps above)
2. **Test Backend API:**
   - Test `get_vapid_public_key` endpoint
   - Test `subscribe_push` endpoint
   - Test `get_subscription_status` endpoint

3. **Test Frontend:**
   - Initialize push notifications in app
   - Request permission
   - Subscribe to push
   - Test receiving notifications

4. **Integration Testing:**
   - Send test notification from backend
   - Verify notification appears
   - Test notification click handling

---

## 📦 **Installation Notes**

### **Backend Dependencies Installed:**
- ✅ `pywebpush==1.14.0` - For sending Web Push notifications
- ✅ `cryptography>=41.0.0` - For VAPID key generation (may already be installed with Frappe)

### **Installation Steps:**

1. **Install Python Dependencies:**
   ```bash
   cd ~/frappe-bench
   bench pip install -r apps/khanal_tech_integrations/requirements.txt
   # Or install individually:
   bench pip install pywebpush==1.14.0
   bench pip install --upgrade cryptography
   ```

2. **Reload Frappe to register new doctypes:**
   ```bash
   bench --site [your-site-name] migrate
   bench clear-cache
   bench restart
   ```

3. **Generate VAPID Keys:**
   ```bash
   bench --site [your-site-name] execute khanal_tech_integrations.utils.generate_vapid_keys.generate_and_store_keys
   ```
   Note: Replace `admin@example.com` with your admin email in the script if needed.

4. **Install Frontend Dependencies (if needed):**
   ```bash
   cd kiosk-frontend
   yarn install  # or npm install
   ```

5. **Build Frontend:**
   ```bash
   cd kiosk-frontend
   yarn build  # or npm run build
   ```

### **Files Created:**

**Backend:**
- ✅ Backend API: `khanal_tech_integrations/api/push_notifications.py`
- ✅ VAPID Key Generator: `khanal_tech_integrations/utils/generate_vapid_keys.py`
- ✅ Doctype Python: `khanal_tech_integrations/khanal_tech_integrations/doctype/push_subscription/push_subscription.py`
- ✅ Doctype Python: `khanal_tech_integrations/khanal_tech_integrations/doctype/push_notification_log/push_notification_log.py`
- ✅ Doctype JSON: `khanal_tech_integrations/khanal_tech_integrations/doctype/push_subscription/push_subscription.json`
- ✅ Doctype JSON: `khanal_tech_integrations/khanal_tech_integrations/doctype/push_notification_log/push_notification_log.json`

**Frontend:**
- ✅ Frontend Service: `kiosk-frontend/src/core/services/pushNotificationService.js`
- ✅ Frontend Composable: `kiosk-frontend/src/composables/usePushNotifications.js`
- ✅ Frontend Store: `kiosk-frontend/src/stores/pushNotifications.js`
- ✅ Service Worker: `kiosk-frontend/public/sw.js`
- ✅ Push Handler: `kiosk-frontend/public/sw-push.js`

### **Frappe Doctypes Created:**
- `Push Subscription` - Stores user push subscriptions
- `Push Notification Log` - Logs all sent notifications

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Vue.js App    │────────│  Service Worker  │────────│  Push Service    │
│   (Frontend)    │         │  (Browser)       │         │  (FCM/VAPID)     │
└────────┬────────┘         └──────────────────┘         └─────────────────┘
         │
         │ HTTP API Calls
         │
┌────────▼─────────────────────────────────────────────────────────────┐
│                    Frappe Backend (Python)                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Push Notification API Endpoints                                │   │
│  │  - Subscribe user to push                                      │   │
│  │  - Send push notification                                       │   │
│  │  - Manage subscriptions                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Database (Frappe)                                           │   │
│  │  - Push Subscription Doctype                                  │   │
│  │  - Notification Log Doctype                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Python Libraries                                             │   │
│  │  - pywebpush (for sending push notifications)                 │   │
│  │  - cryptography (for VAPID keys)                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Technology Stack**

### **Backend (Python/Frappe)**
- **pywebpush**: Python library for sending Web Push notifications
- **cryptography**: For VAPID key generation and management
- **Frappe Doctypes**: To store push subscriptions and notification logs

### **Frontend (Vue.js)**
- **Service Worker**: Already configured via VitePWA plugin
- **Push API**: Browser's native Push API
- **Notification API**: Browser's native Notification API
- **IndexedDB** (optional): For offline subscription management

---

## 📦 **Implementation Steps**

### **Phase 1: Backend Setup (Python/Frappe)**

#### **1.1 Install Python Dependencies**
```bash
# Add to requirements.txt
pywebpush==1.14.0
cryptography>=41.0.0
```

#### **1.2 Create Frappe Doctypes**

**A. Push Subscription Doctype**
- **Name**: `Push Subscription`
- **Fields**:
  - `user` (Link to User) - Required
  - `endpoint` (Data) - Required, unique
  - `keys` (JSON) - Required (p256dh, auth)
  - `user_agent` (Data) - Optional
  - `device_info` (JSON) - Optional
  - `plant_id` (Data) - Optional (for plant-specific notifications)
  - `is_active` (Check) - Default: 1
  - `last_notified` (Datetime) - Optional

**B. Push Notification Log Doctype**
- **Name**: `Push Notification Log`
- **Fields**:
  - `user` (Link to User) - Required
  - `title` (Data) - Required
  - `message` (Long Text) - Required
  - `icon` (Attach Image) - Optional
  - `badge` (Attach Image) - Optional
  - `data` (JSON) - Optional (for action handling)
  - `status` (Select) - Sent, Failed, Pending
  - `error_message` (Text) - Optional
  - `sent_at` (Datetime) - Optional

#### **1.3 Generate VAPID Keys**
```python
# Script to generate VAPID keys
from pywebpush import webpush, WebPushException
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem
```

**Store VAPID keys in Frappe Site Config:**
- Add to `site_config.json` or create a custom DocType for settings
- Keys: `vapid_private_key`, `vapid_public_key`, `vapid_email`

#### **1.4 Create API Endpoints**

**File**: `khanal_tech_integrations/api/push_notifications.py`

**Endpoints:**
1. **`subscribe_push`** - Register user's push subscription
2. **`unsubscribe_push`** - Remove user's push subscription
3. **`send_push_notification`** - Send notification to user(s)
4. **`get_subscription_status`** - Check if user has active subscription

---

### **Phase 2: Frontend Setup (Vue.js)**

#### **2.1 Create Push Notification Service**

**File**: `kiosk-frontend/src/core/services/pushNotificationService.js`

**Features:**
- Request notification permission
- Subscribe to push service
- Handle push notifications
- Manage subscription state
- Store subscription in IndexedDB (optional)

#### **2.2 Update Service Worker**

**File**: `kiosk-frontend/public/sw.js` (or via VitePWA config)

**Features:**
- Handle `push` event
- Show notification
- Handle notification click
- Handle notification close

#### **2.3 Create Push Notification Composable**

**File**: `kiosk-frontend/src/composables/usePushNotifications.js`

**Features:**
- Initialize push notifications
- Subscribe/unsubscribe
- Handle permission states
- React to incoming notifications

#### **2.4 Create Notification Store (Pinia)**

**File**: `kiosk-frontend/src/stores/pushNotifications.js`

**Features:**
- Store subscription state
- Store notification history
- Manage permission status
- Sync with backend

#### **2.5 Create Notification UI Component**

**File**: `kiosk-frontend/src/shared/components/PushNotificationPrompt.vue`

**Features:**
- Permission request UI
- Subscription status display
- Enable/disable notifications toggle

---

### **Phase 3: Integration**

#### **3.1 Integrate with Existing Notification System**
- Extend existing `notifications.py` API
- Connect push notifications with CRM notifications
- Unified notification center

#### **3.2 Add Notification Triggers**
- Production order status changes
- GRN approvals
- Quality check completions
- System alerts

#### **3.3 Add Notification Preferences**
- User settings for notification types
- Plant-specific notification settings
- Quiet hours configuration

---

## 🔐 **Security Considerations**

1. **VAPID Keys**: Store securely, never expose private key
2. **HTTPS Required**: Push notifications only work over HTTPS (except localhost)
3. **User Authentication**: Verify user identity before subscribing
4. **Endpoint Validation**: Validate subscription endpoints
5. **Rate Limiting**: Prevent abuse of push notification API
6. **Data Encryption**: Encrypt sensitive data in notification payload

---

## 📱 **Notification Types**

### **Production Notifications**
- Production order approved
- Production order completed
- Goods issue created
- Goods receipt created
- Batch number generated

### **GRN Notifications**
- GRN submitted
- GRN approved
- GRN rejected
- GRN items received

### **System Notifications**
- System maintenance alerts
- Plant-specific announcements
- User role changes
- Session expiry warnings

---

## 🧪 **Testing Strategy**

### **Backend Testing**
- Unit tests for subscription management
- Unit tests for push sending
- Integration tests with mock push service

### **Frontend Testing**
- Service worker registration
- Push subscription flow
- Notification display
- Click handling

### **End-to-End Testing**
- Full subscription flow
- Notification delivery
- User interaction flows

---

## 📊 **Database Schema**

### **Push Subscription Table**
```sql
- name (varchar)
- user (varchar) -> User
- endpoint (varchar) [unique]
- keys (json)
- user_agent (varchar)
- device_info (json)
- plant_id (varchar)
- is_active (int)
- last_notified (datetime)
- creation (datetime)
- modified (datetime)
```

### **Push Notification Log Table**
```sql
- name (varchar)
- user (varchar) -> User
- title (varchar)
- message (text)
- icon (varchar)
- badge (varchar)
- data (json)
- status (varchar) [Sent, Failed, Pending]
- error_message (text)
- sent_at (datetime)
- creation (datetime)
```

---

## 🚀 **Deployment Checklist**

- [ ] Generate and store VAPID keys securely
- [ ] Install Python dependencies
- [ ] Create Frappe doctypes
- [ ] Deploy backend API endpoints
- [ ] Update service worker
- [ ] Deploy frontend changes
- [ ] Test on HTTPS (required for production)
- [ ] Configure notification permissions
- [ ] Set up monitoring/logging
- [ ] Document user guide

---

## 📝 **API Endpoints Specification**

### **1. Subscribe to Push Notifications**
```
POST /api/method/khanal_tech_integrations.api.push_notifications.subscribe_push

Request Body:
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  },
  "user_agent": "...",
  "plant_id": "mahadevpura"
}

Response:
{
  "success": true,
  "message": "Subscription saved"
}
```

### **2. Unsubscribe from Push Notifications**
```
POST /api/method/khanal_tech_integrations.api.push_notifications.unsubscribe_push

Request Body:
{
  "endpoint": "https://fcm.googleapis.com/..."
}

Response:
{
  "success": true,
  "message": "Unsubscribed"
}
```

### **3. Send Push Notification**
```
POST /api/method/khanal_tech_integrations.api.push_notifications.send_push_notification

Request Body:
{
  "user": "user@example.com",
  "title": "Production Order Approved",
  "message": "Your production order PO-001 has been approved",
  "icon": "/assets/icon.png",
  "data": {
    "type": "production_order",
    "doc_name": "PO-001",
    "route": "/production-order/PO-001"
  },
  "plant_id": "mahadevpura" // Optional filter
}

Response:
{
  "success": true,
  "sent_count": 1,
  "failed_count": 0
}
```

---

## 🎯 **Implementation Priority**

### **Phase 1 (MVP) - 2-3 days**
1. Backend API setup
2. Basic subscription management
3. Simple notification sending
4. Frontend subscription flow

### **Phase 2 (Enhanced) - 2-3 days**
1. Notification preferences
2. Notification history
3. Error handling & retry logic
4. UI components

### **Phase 3 (Advanced) - 2-3 days**
1. Notification analytics
2. Advanced filtering
3. Batch notifications
4. Notification templates

---

## ⚠️ **Limitations & Considerations**

1. **Browser Support**: Chrome, Firefox, Edge (Safari has limited support)
2. **HTTPS Required**: Must use HTTPS in production (except localhost)
3. **User Permission**: Requires explicit user permission
4. **Service Worker**: Requires service worker support
5. **Platform Support**: Works on desktop and Android, limited on iOS

---

## 📚 **Resources**

- [Web Push Protocol](https://datatracker.ietf.org/doc/html/rfc8030)
- [VAPID Specification](https://datatracker.ietf.org/doc/html/rfc8292)
- [pywebpush Documentation](https://github.com/web-push-libs/pywebpush)
- [MDN Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)

---

## ✅ **Approval Required**

Please review this plan and confirm:
1. ✅ Architecture approach
2. ✅ Technology choices
3. ✅ Implementation phases
4. ✅ Security considerations
5. ✅ Notification types to support

Once approved, I'll proceed with the implementation starting with Phase 1.

