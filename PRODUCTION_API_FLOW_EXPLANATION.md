# Production API Structure Flow - Complete Explanation

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue.js)                         │
│  ProductionOrder.vue → productionServiceFactory.js → API Call    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python/Frappe)                       │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  plants/{plant}/production.py (Whitelisted Functions)     │  │
│  │  - search_bom()                                           │  │
│  │  - approve_production_order()                             │  │
│  │  - goods_issue()                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  common/production_factory.py (Factory Pattern)            │  │
│  │  - get_production_api(plant_id)      → READ API          │  │
│  │  - get_production_post_api(plant_id)  → WRITE API         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                    │
│              ┌───────────────┴───────────────┐                   │
│              ▼                               ▼                   │
│  ┌──────────────────────┐      ┌──────────────────────────┐    │
│  │ production_api.py    │      │ production_post_api.py   │    │
│  │ (READ Operations)    │      │ (WRITE Operations)       │    │
│  │                      │      │                          │    │
│  │ - search_bom_in_sap  │      │ - approve_production_   │    │
│  │ - get_itt1_components│      │   order()               │    │
│  │ - get_oitt_header    │      │ - goods_issue()          │    │
│  │ - get_batch_numbers  │      │ - goods_receipt()        │    │
│  │ - get_warehouses     │      │ - close_production()     │    │
│  └──────────────────────┘      │ - get_production_orders_ │    │
│              │                  │   list()                  │    │
│              │                  │ - get_production_order_   │    │
│              │                  │   for_resume()          │    │
│              │                  └──────────────────────────┘    │
│              │                               │                   │
│              └───────────────┬───────────────┘                   │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  plants/base/production_api.py (Base Class)               │  │
│  │  - Provides SAP connection, validation, utilities         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SAP HANA (Read) / SAP B1 (Write)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Complete Flow Examples**

### **Example 1: READ Operation - Search BOM**

```
Step 1: Frontend Request
────────────────────────
ProductionOrder.vue
  ↓
productionServiceFactory.js
  ↓ getProductionService('malur')
  ↓
malur/productionService.js
  ↓ searchBOM('ABC')
  ↓
POST /api/method/khanal_tech_integrations.api.plants.malur.production.search_bom


Step 2: Backend Whitelisted Function
─────────────────────────────────────
plants/malur/production.py
  @frappe.whitelist(allow_guest=False)
  def search_bom(search_query, plant_id='malur'):
      from khanal_tech_integrations.api.common.production_factory import get_production_api
      
      api = get_production_api(plant_id)  # Returns MalurProductionAPI instance
      return api.search_bom_in_sap(search_query)


Step 3: Factory Routing
────────────────────────
common/production_factory.py
  def get_production_api(plant_id):
      normalized = normalize_plant_id('malur')  # → 'malur'
      
      if normalized == 'malur':
          from ...plants.malur.production import MalurProductionAPI
          return MalurProductionAPI()  # Returns instance
      
      # MalurProductionAPI extends CommonProductionAPI


Step 4: API Execution
─────────────────────
common/production_api.py (CommonProductionAPI)
  class CommonProductionAPI(BaseProductionAPI):
      def search_bom_in_sap(self, search_query):
          connection, cursor, schema = self.sap.get_hana_connection()
          # Query SAP HANA OITT table
          cursor.execute(query)
          results = cursor.fetchall()
          return {"success": True, "data": results}


Step 5: Response
────────────────
Frontend receives:
{
  "success": true,
  "data": [
    {"Code": "BOM001", "Name": "Product BOM", ...}
  ]
}
```

---

### **Example 2: WRITE Operation - Approve Production Order**

```
Step 1: Frontend Request
────────────────────────
ProductionOrder.vue
  ↓
productionServiceFactory.js
  ↓ getProductionService('malur')
  ↓
malur/productionService.js
  ↓ approveProductionOrder(data)
  ↓
POST /api/method/khanal_tech_integrations.api.plants.malur.production.approve_production_order


Step 2: Backend Whitelisted Function
─────────────────────────────────────
plants/malur/production.py
  @frappe.whitelist(allow_guest=False)
  def approve_production_order(production_data, plant_id='malur'):
      from khanal_tech_integrations.api.common.production_factory import get_production_post_api
      
      api = get_production_post_api(plant_id)  # Returns CommonProductionPostAPI('malur')
      return api.approve_production_order(production_data)


Step 3: Factory Routing
────────────────────────
common/production_factory.py
  def get_production_post_api(plant_id):
      normalized = normalize_plant_id('malur')  # → 'malur'
      
      # For now, all plants use CommonProductionPostAPI
      return CommonProductionPostAPI(normalized)  # Returns CommonProductionPostAPI('malur')


Step 4: API Execution
─────────────────────
common/production_post_api.py (CommonProductionPostAPI)
  class CommonProductionPostAPI(BaseProductionAPI):
      def approve_production_order(self, production_data):
          # 1. Authenticate SAP B1
          b1_session = AuthenticateSAPB1()
          
          # 2. Build payload
          payload = {
              "ItemNo": production_data.get("ItemNo"),
              "PlannedQuantity": production_data.get("PlannedQuantity"),
              "ProductionOrderLines": [...]
          }
          
          # 3. POST to SAP B1
          response = b1_session.post(url, json=payload)
          
          # 4. Release production order
          b1_session.patch(release_url, json={"ProductionOrderStatus": "boposReleased"})
          
          # 5. Save to Production Kiosk doctype
          self._save_production_result(...)
          
          return {"success": True, "productionOrderDocEntry": doc_entry, ...}


Step 5: Response
────────────────
Frontend receives:
{
  "success": true,
  "productionOrderDocEntry": 12345,
  "productionOrderDocNum": "PO-001",
  "ProductionOrderStatus": "boposReleased",
  ...
}
```

---

## 🏗️ **File Responsibilities**

### **1. Frontend Files**

```
kiosk-frontend/src/
├── app/pages/ProductionOrder.vue
│   └── Shared component (used by all plants)
│
├── plants/{plant}/pages/ProductionOrder.vue
│   └── Plant-specific wrapper (can add customizations)
│
└── core/api/
    ├── common/productionServiceFactory.js
    │   └── Returns correct service based on plantId
    │
    └── plants/{plant}/productionService.js
        └── Service class with API methods
```

### **2. Backend Files**

```
khanal_tech_integrations/api/
├── common/
│   ├── production_api.py          # READ: SAP HANA queries
│   ├── production_post_api.py     # WRITE: SAP B1 posting
│   └── production_factory.py      # Factory: Routing logic
│
└── plants/
    ├── base/
    │   └── production_api.py       # Base class with utilities
    │
    └── {plant}/
        └── production.py           # Whitelisted functions only
```

---

## 🔀 **Data Flow Diagram**

### **READ Operation Flow**
```
Frontend
  │
  ├─→ productionService.searchBOM()
  │
  ├─→ POST /api/method/...plants.malur.production.search_bom
  │
Backend
  │
  ├─→ malur/production.py::search_bom()
  │   │
  │   ├─→ get_production_api('malur')
  │   │   │
  │   │   └─→ factory.py::get_production_api()
  │   │       │
  │   │       └─→ Returns MalurProductionAPI()
  │   │
  │   └─→ api.search_bom_in_sap()
  │       │
  │       └─→ production_api.py::search_bom_in_sap()
  │           │
  │           ├─→ Get SAP HANA connection
  │           ├─→ Query OITT table
  │           └─→ Return results
  │
  └─→ Response to Frontend
```

### **WRITE Operation Flow**
```
Frontend
  │
  ├─→ productionService.approveProductionOrder()
  │
  ├─→ POST /api/method/...plants.malur.production.approve_production_order
  │
Backend
  │
  ├─→ malur/production.py::approve_production_order()
  │   │
  │   ├─→ get_production_post_api('malur')
  │   │   │
  │   │   └─→ factory.py::get_production_post_api()
  │   │       │
  │   │       └─→ Returns CommonProductionPostAPI('malur')
  │   │
  │   └─→ api.approve_production_order()
  │       │
  │       └─→ production_post_api.py::approve_production_order()
  │           │
  │           ├─→ Authenticate SAP B1
  │           ├─→ Build payload
  │           ├─→ POST to SAP B1 (create order)
  │           ├─→ PATCH to SAP B1 (release order)
  │           ├─→ Save to Production Kiosk doctype
  │           └─→ Return response
  │
  └─→ Response to Frontend
```

---

## 🎯 **Key Design Decisions**

### **1. Why Separate Read and Write?**

```
READ Operations (production_api.py)
├── Source: SAP HANA Database
├── Operations: SELECT queries
├── Tables: OITT, ITT1, OBTQ, OBTN, OWHS
└── Purpose: Fetch data for display

WRITE Operations (production_post_api.py)
├── Source: SAP B1 REST API
├── Operations: POST, PATCH requests
├── Endpoints: ProductionOrders, InventoryGenExits, etc.
└── Purpose: Create/update data in SAP
```

### **2. Why Factory Pattern?**

**Without Factory (BAD):**
```python
# In every whitelisted function:
if plant_id == 'nandi_hills':
    api = NandiHillsProductionAPI()
elif plant_id == 'malur':
    api = MalurProductionAPI()
elif plant_id == 'krishnagiri':
    api = KrishnagiriProductionAPI()
# ... repeat for every plant and every function
```

**With Factory (GOOD):**
```python
# In every whitelisted function:
api = get_production_api(plant_id)  # Factory handles routing
```

### **3. Why Plant-Specific Files?**

```
plants/{plant}/production.py
├── Purpose: Whitelisted endpoints for Frappe routing
├── Contains: Only @frappe.whitelist decorated functions
├── Logic: Delegates to factory → common API
└── Customization: Can override methods if needed
```

---

## 📋 **Method Call Chain**

### **Read Operation: search_bom**

```
1. Frontend: productionService.searchBOM('ABC')
   │
2. HTTP: POST /api/method/...malur.production.search_bom
   │
3. Frappe Router: Routes to plants/malur/production.py::search_bom()
   │
4. Whitelisted Function: search_bom(search_query='ABC', plant_id='malur')
   │
5. Factory Call: get_production_api('malur')
   │
6. Factory Returns: MalurProductionAPI() instance
   │
7. API Method: api.search_bom_in_sap('ABC')
   │
8. CommonProductionAPI: Executes SAP HANA query
   │
9. Response: Returns {"success": True, "data": [...]}
   │
10. Frontend: Receives and displays results
```

### **Write Operation: approve_production_order**

```
1. Frontend: productionService.approveProductionOrder(data)
   │
2. HTTP: POST /api/method/...malur.production.approve_production_order
   │
3. Frappe Router: Routes to plants/malur/production.py::approve_production_order()
   │
4. Whitelisted Function: approve_production_order(production_data, plant_id='malur')
   │
5. Factory Call: get_production_post_api('malur')
   │
6. Factory Returns: CommonProductionPostAPI('malur') instance
   │
7. API Method: api.approve_production_order(production_data)
   │
8. CommonProductionPostAPI: 
   │   ├─→ Authenticate SAP B1
   │   ├─→ Build payload
   │   ├─→ POST to SAP B1 (create)
   │   ├─→ PATCH to SAP B1 (release)
   │   └─→ Save to Production Kiosk
   │
9. Response: Returns {"success": True, "productionOrderDocEntry": 12345, ...}
   │
10. Frontend: Receives and displays success message
```

---

## 🔑 **Key Concepts**

### **1. Factory Pattern**
- **Purpose**: Centralized routing logic
- **Location**: `common/production_factory.py`
- **Functions**: 
  - `get_production_api()` → Returns READ API
  - `get_production_post_api()` → Returns WRITE API

### **2. Inheritance Hierarchy**
```
BaseProductionAPI (base/production_api.py)
    │
    ├─→ CommonProductionAPI (common/production_api.py)
    │       │
    │       └─→ MalurProductionAPI (plants/malur/production.py)
    │       └─→ NandiHillsProductionAPI (plants/nandi_hills/production.py)
    │       └─→ ... (other plants)
    │
    └─→ CommonProductionPostAPI (common/production_post_api.py)
            (All plants use this for write operations)
```

### **3. Separation of Concerns**
- **Read**: `production_api.py` - Only queries SAP HANA
- **Write**: `production_post_api.py` - Only posts to SAP B1
- **Routing**: `production_factory.py` - Only decides which API to use
- **Endpoints**: `plants/{plant}/production.py` - Only whitelisted functions

---

## ✅ **Benefits of This Structure**

1. **Maintainability**: Change common logic in one place
2. **Scalability**: Easy to add new plants
3. **Testability**: Each component can be tested independently
4. **Clarity**: Clear separation between read and write operations
5. **Consistency**: All plants follow the same pattern
6. **Flexibility**: Plants can override methods when needed

---

## 🎓 **Summary**

**The flow is:**
1. **Frontend** calls API endpoint
2. **Whitelisted function** in plant file receives request
3. **Factory** decides which API instance to use
4. **Common API** (read or write) executes the operation
5. **Response** returns to frontend

**All plants use the same common code**, with the factory ensuring the correct instance is used based on `plant_id`.

