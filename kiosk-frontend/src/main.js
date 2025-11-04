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
  // Ignore ServiceWorker SSL errors (non-critical)
  if (error?.message?.includes('ServiceWorker') && error?.message?.includes('SSL certificate')) {
    console.warn('ServiceWorker SSL error (non-critical):', error.message)
    return
  }
  
  console.error('Global error:', error)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
}

// Handle ServiceWorker registration errors gracefully
// This catches any ServiceWorker registration errors that might occur
if ('serviceWorker' in navigator) {
  // Override any existing ServiceWorker registration to catch errors
  const originalRegister = navigator.serviceWorker.register
  navigator.serviceWorker.register = function(...args) {
    return originalRegister.apply(this, args).catch((error) => {
      // Catch SSL certificate errors and other ServiceWorker registration errors
      if (error?.message?.includes('SSL certificate') || 
          error?.message?.includes('certificate error') ||
          error?.name === 'SecurityError') {
        console.warn('ServiceWorker registration failed due to SSL certificate issue (non-critical, app will continue):', error.message)
        // Return a resolved promise to prevent the error from propagating
        return Promise.resolve()
      }
      // Re-throw other errors
      throw error
    })
  }
}

// Mount app
app.mount('#app')

// Export for testing
export { app, router, pinia }