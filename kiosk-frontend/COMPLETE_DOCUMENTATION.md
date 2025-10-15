## Khanal Foods Kiosk System – Complete Documentation

### Table of Contents
- Project Overview
- Architecture
- Codebase Layout
- Routing and Navigation
- Authentication and Session
- Activity Logging
- Configuration and Constants
- Build and Deployment
- PWA and Icons
- Testing Checklist
- Troubleshooting

---

## Project Overview
The Khanal Foods Kiosk is a plant‑independent Vue 3 application served from the Frappe site under the path `/kiosk`. Users log in with a selected plant and access isolated plant areas (layouts, pages, and side navigation). The app uses same‑origin REST APIs for authentication and activity logging, Pinia for session/state, and Tailwind for UI.

Supported plants (each isolated):
- Mahadevpura
- Nandi Hills
- Malur
- Krishnagiri
- Champavath

Key properties
- Same‑origin API: served by Frappe, cookies and CSRF managed by the browser
- Plant‑isolated UI: no cross‑plant component reuse for business pages
- REST‑only logging by default; WebSocket optional via feature flag
- Mobile‑responsive, PWA manifest and icons configured

---

## Architecture
High level
```
Vue 3 (Vite) SPA → /kiosk              
  ├─ Core (auth, session, activity)   
  ├─ Plant modules (isolated)         
  └─ PWA                              

Frappe (dev.localhost:8001)
  ├─ Auth endpoints (login/logout/...)
  ├─ Plant endpoints (get_plants, …)
  └─ Activity endpoints (log_activity)
```

Important flows
- Login page (with plant dropdown) → Frappe `login` → verify plant access → generate plant token → redirect to `/kiosk/plant/{plant}/dashboard`.
- Navigation guard enforces authentication and correct plant context.
- Activity logger records navigation/actions via REST (same origin, with credentials).

---

## Codebase Layout
```
kiosk-frontend/
├─ src/
│  ├─ app/
│  │  └─ components/           # Shared app chrome (UserDropdown, UserProfile)
│  │  └─ pages/                # Login, 404, Unauthorized, PlantFeature
│  ├─ core/
│  │  ├─ auth/authService.js   # Axios client, login/logout, interceptors
│  │  ├─ stores/session.js     # Pinia store for session + timeouts
│  │  ├─ utils/activityLogger.js# REST logging, queue, sendBeacon, WS optional
│  │  └─ composables/useAuthService.js
│  ├─ plants/
│  │  ├─ mahadevpura/
│  │  ├─ nandi-hills/
│  │  ├─ malur/
│  │  ├─ krishnagiri/
│  │  └─ champavath/
│  │     └─ {layouts, pages, components}
│  ├─ config/constants.js       # Centralized constants (same-origin)
│  └─ router.js                 # createWebHistory('/kiosk/') routes
├─ vite.config.js               # base=/kiosk, outDir → Frappe www/kiosk, PWA
└─ COMPLETE_DOCUMENTATION.md
```

Plant modules
- Each plant has its own `layouts/PlantLayout.vue`, `components/SideNav.vue`, and feature pages.
- Side nav differs by plant as specified; theme is consistent across plants.

---

## Routing and Navigation
Router: `createWebHistory('/kiosk/')` with top‑level routes:
- `/login` and `/login/:plantId` (Login.vue with plant dropdown)
- `/plant/{plant}/...` nested under plant `PlantLayout.vue` with child pages:
  - Mahadevpura: dashboard, grn, production‑order, quality, inventory‑transfer
  - Nandi Hills: dashboard, grn, production‑order, quality, inventory‑transfer
  - Malur: dashboard, production‑order, inventory‑transfer
  - Krishnagiri: dashboard, grn, production‑order, quality, inventory‑transfer
  - Champavath: dashboard, grn, production‑order, inventory‑transfer
- `/unauthorized`, `/:pathMatch(.*)*` (NotFound)

Guards
- Require session for protected routes.
- Verify plant context (URL plant must match session plant); mismatch clears session and redirects to `/kiosk/login`.
- Sets document title and logs navigation (non‑blocking).

---

## Authentication and Session
Auth client: `core/auth/authService.js`
- Axios baseURL: `APP_CONFIG.FRAPPE_API_URL` (same‑origin `/api`)
- `withCredentials: true` to send Frappe cookies
- Interceptors: attach bearer if present; handle 401 → logout
- Exposed methods: login, logout, changePassword, etc.

Session store: `core/stores/session.js`
- Persists `kiosk-session` in localStorage
- Restores on reload if `expiresAt` not elapsed (handles ISO or epoch)
- Idle timeout clears session and redirects to `/kiosk/login`

Login page: `app/pages/Login.vue`
- Email/password fields, plant dropdown (loaded from backend)
- After successful auth + plant verification + token generation, redirects to plant dashboard

Backend (Frappe)
- `login` and `logout` via core `/api/method/login|logout`
- `verify_plant_access`, `generate_plant_token` in `khanal_tech_integrations.api.auth`

---

## Activity Logging
Frontend: `core/utils/activityLogger.js`
- REST‑only by default; WebSocket guarded by `APP_CONFIG.FEATURES.REAL_TIME_LOGGING`
- Non‑blocking logging on navigation and actions
- Queue with localStorage persistence; retries; `sendBeacon` on unload/visibilitychange
- Privacy: hashes user email (sha256); truncates user‑agent

Endpoints
- Single: `POST /api/method/khanal_tech_integrations.api.activity.log_activity`
  - Named parameter: `{ activity_data: { ... } }`
- Batch (optional): `POST /api/method/khanal_tech_integrations.api.activity.log_batch_activities`
  - Named parameter: `{ activities: [ ... ] }`

Frappe: `khanal_tech_integrations/api/activity.py`
- Validates required fields, stores `Kiosk Activity Log`
- Requires authenticated session (guest disabled)

---

## Configuration and Constants
`src/config/constants.js` (same‑origin)
- `FRAPPE_API_URL: '/api'`
- `FRAPPE_SITE_URL: window.location.origin`
- `WS_URL` derived from `window.location` (ws/wss)
- Feature flags: `REAL_TIME_LOGGING`, etc.
- Endpoints map: `API_ENDPOINTS.LOGIN`, `...VERIFY_PLANT_ACCESS`, `...LOG_ACTIVITY`, etc.
- Routes map: `LOGIN`, `DASHBOARD`, etc. (Plant selection removed)

Frappe `site_config.json` (dev.localhost)
- `enable_websocket: true` (optional)
- `allow_cors` not required for same‑origin serving

---

## Build and Deployment
Vite config: `vite.config.js`
- `base: '/kiosk/'`
- `build.outDir: '../khanal_tech_integrations/www/kiosk'` (served by Frappe at `/kiosk`)
- PWA manifest via `vite-plugin-pwa` with kiosk paths

Build and publish
```bash
cd kiosk-frontend
yarn build
cd ../../.. /Users/yogeshadevarakonda/Frappe
bench --site dev.localhost clear-cache
```
Access at `http://dev.localhost:8001/kiosk`.

Notes
- For clean history routing under `/kiosk`, serving from Frappe `www/kiosk` works without nginx rewrites as assets are relative to `/kiosk/` and router base is `/kiosk/`.
- If hosting under assets path, set `base` accordingly; current setup uses `/kiosk`.

---

## PWA and Icons
PWA manifest configured in Vite plugin.
Icons (no 404s):
- `/assets/khanal_tech_integrations/assets/img/favicons/android-chrome-192x192.png`
- `/assets/khanal_tech_integrations/assets/img/favicons/android-chrome-512x512.png`

If you update icons, keep manifest paths aligned with files under Frappe public assets.

---

## Testing Checklist
Routing and guards
- `/kiosk` → `/kiosk/login`
- Protected routes redirect when not authenticated
- Wrong plant in URL clears session and redirects to login

Authentication
- Valid login → plant dashboard; session stored; `expiresAt` future
- Invalid password → error banner; no session persisted
- Unassigned plant → access denied message

Activity logging
- Navigation triggers `log_activity` 200 responses
- Go offline → actions queued; come online → flushed successfully
- Tab close with queued logs uses `sendBeacon`

PWA/icons
- Manifest loads without syntax errors; icons no 404

UX/accessibility
- Inputs visibly typeable (bg‑white, text-gray-900)
- Buttons disabled during async; no double submits

Performance
- No console errors; lazy‑loaded plant pages load fast locally

---

## Troubleshooting
- Blank page after deploy: ensure `base: '/kiosk/'` and `outDir` under `www/kiosk`; hard refresh (Cmd+Shift+R). If PWA installed, unregister service worker and reload.
- 401 on API calls: verify cookies (same origin), session not expired, `withCredentials: true` set in axios instance.
- Plant access denied: ensure `User Plant Access` record exists for the email and plant.
- Logging 403: activity endpoints require authenticated session; call after login only.

---

## Version
Current: v1.0.0
- Plant‑isolated structure
- Same‑origin authentication and session
- REST activity logging with privacy protections
- Responsive UI with shared header dropdown and profile modal

Last updated: 2025‑10‑14
