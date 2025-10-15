# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project overview

- Backend: Frappe app in `khanal_tech_integrations/` (Python). App config and hooks in `khanal_tech_integrations/hooks.py`; website routes via `website_route_rules`, Jinja methods exposed via `jinja.methods`.
- Desk frontend: Vue 3 app in `frontend/` built with Vite and Frappe UI. Builds to `khanal_tech_integrations/public/frontend/` and copies entry HTML to `khanal_tech_integrations/www/home.html`.
- Kiosk SPA: Vue 3 app in `kiosk-frontend/` (Pinia, Vue Router, PWA). Vite base is `/kiosk/`; production build outputs to `khanal_tech_integrations/www/kiosk/`.
- Integrations (Python): Modular utilities under `khanal_tech_integrations/utils/` for SAP, Unicommerce, B2B, Logistics/Safexpress, Finance, and Production Kiosk. Background processing is driven by `scheduler_events` (cron-style jobs) and `doc_events` (e.g., Material Request submit/cancel, File after_insert) in `hooks.py`.

## Commands

### Frappe/backend (bench)

```bash path=null start=null
# Start dev services
bench start

# Install app on a site (run from your bench root)
bench --site {{site_name}} install-app khanal_tech_integrations

# Migrate and clear cache after code changes
bench --site {{site_name}} migrate
bench --site {{site_name}} clear-cache

# Execute a Python function (replace with your callable)
bench --site {{site_name}} execute "module.path.function_name" --kwargs '{"param": "value"}'

# Run all tests for this app
bench --site {{site_name}} run-tests --app khanal_tech_integrations

# Run a single Doctype test
bench --site {{site_name}} run-tests --app khanal_tech_integrations --doctype "DocType Name"

# Run tests in a specific module
bench --site {{site_name}} run-tests --app khanal_tech_integrations --module khanal_tech_integrations.path.to.test_module
```

### Desk frontend (`frontend/`)

```bash path=null start=null
cd frontend

# Install deps and run dev server
yarn install
yarn dev
# Access via http://<your-site-host>:8080 (set "ignore_csrf": 1 in site_config.json for dev)

# Production build and copy entry HTML
yarn build
# Preview build locally
yarn serve
```

Notes:
- Build writes assets to `khanal_tech_integrations/public/frontend/` and copies `index.html` to `khanal_tech_integrations/www/home.html` (see `package.json` scripts and `vite.config.js`).

### Kiosk frontend (`kiosk-frontend/`)

```bash path=null start=null
cd kiosk-frontend

# Install deps
yarn install

# Type-check, lint, and fix
yarn type-check
# Lint all source files
yarn lint
# Auto-fix lint issues
yarn lint:fix

# Run dev server (Vite on http://dev.localhost:8081 with base /kiosk/)
yarn dev

# Build for production (outputs to ../khanal_tech_integrations/www/kiosk)
yarn build
# Preview prod build locally
yarn preview

# Tests (Vitest)
# Run all tests
yarn test
# Watch tests with UI
yarn test:ui
# Coverage
yarn test:coverage
# Run a single test file
vitest path/to/file.spec.ts
# Run tests by name pattern
vitest -t "pattern"
```

Notes:
- Requires Node >= 18 (see `engines` in `kiosk-frontend/package.json`).
- `vite.config.ts` sets `base: '/kiosk/'` and `outDir: '../khanal_tech_integrations/www/kiosk'`.

## Architecture highlights

- Routing and website: `home_page = "/home"` and `website_route_rules = routes` (imported from `khanal_tech_integrations.route`). Frontend “desk” app is served under `/home`; Kiosk SPA is served under `/kiosk/`.
- Server-side events:
  - `doc_events`: Integrates with ERP workflows (e.g., Material Request submit/cancel to P2P handlers; File after_insert to mark public in AR invoice detail).
  - `scheduler_events`: Extensive cron schedules for SAP inventory updates, Unicommerce order/invoice flows, B2B email processing, Safexpress tracking, finance verifications, and production kiosk list refreshers. Review `hooks.py` when modifying job cadence.
- Frontend build/deploy:
  - Desk app: Vite + Frappe UI. Build artifacts live under `public/frontend/`; entry HTML copied to `www/home.html`.
  - Kiosk: Vite PWA with custom base and Jinja boot variables injected at build. Deployed as static assets under `www/kiosk/`.

## Test and lint summary

- Backend: `bench --site {{site_name}} run-tests --app khanal_tech_integrations` (use `--doctype` or `--module` to scope).
- Kiosk: Vitest for unit tests; ESLint for linting; `vue-tsc` for type checks.
- Desk frontend: no dedicated test/lint scripts in `frontend/package.json` (build via Vite).
