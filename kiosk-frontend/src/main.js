/**
 * Main Application Entry Point
 * Sets up Vue app with all necessary plugins and configurations
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router.js'

// Import frappe-ui API utilities (not UI components to avoid build issues)
import { setConfig, frappeRequest } from 'frappe-ui'

// Import main app component
import App from './App.vue'

// Import global styles
import './index.css'

// NOTE: CSRF token is injected by the boot script at the bottom of kiosk.html
// Don't initialize it here - it will be available when API calls are made
// baseService.js handles CSRF token lazily in ensureCSRFToken() method

// Create Vue app
const app = createApp(App)

// Create Pinia store
const pinia = createPinia()
app.use(pinia)

// Configure frappe-ui resource fetcher (CRITICAL - this handles all CSRF automatically!)
setConfig('resourceFetcher', frappeRequest)

// Use router
app.use(router)

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Global Vue error:', error)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
  
  // Don't propagate errors that are already handled
  // (e.g., network errors, auth errors handled by interceptors)
  if (error?.response) {
    const status = error.response.status
    if (status === 401 || status === 403 || status === 417) {
      // These are handled by interceptors, don't propagate
      return
    }
  }
  
  // For chunk load errors, force reload instead of showing error boundary
  if (error?.name === 'ChunkLoadError' || error?.message?.includes('ChunkLoadError')) {
    console.warn('ChunkLoadError detected, reloading page...')
    setTimeout(() => window.location.reload(), 1000)
    return
  }
}

// Mount app
app.mount('#app')

// Export for testing
export { app, router, pinia }