/**
 * Main Application Entry Point
 * Sets up Vue app with all necessary plugins and configurations
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router.js'

// Import core services
import { useSessionStore } from './core/stores/session.js'
import { useActivityLogger } from './core/utils/activityLogger.js'

// Import main app component
import App from './App.vue'

// Import global styles
import './index.css'

// Create Vue app
const app = createApp(App)

// Create Pinia store
const pinia = createPinia()
app.use(pinia)

// Use router
app.use(router)

// Initialize session store
const sessionStore = useSessionStore()
sessionStore.initializeFromStorage()

// Initialize activity logger
const activityLogger = useActivityLogger()

// Global error handler
app.config.errorHandler = (error, instance, info) => {
  console.error('Global error:', error)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
  
  // Log error to activity logger
  activityLogger.logError(error, {
    component: instance?.$options.name || 'Unknown',
    info: info
  })
}

// Global properties
app.config.globalProperties.$activityLogger = activityLogger

// Mount app
app.mount('#app')

// Log app initialization
activityLogger.logActivity({
  type: 'app_initialization',
  action: 'app_start',
  metadata: {
    user_agent: navigator.userAgent,
    screen_resolution: `${screen.width}x${screen.height}`,
    viewport: `${window.innerWidth}x${window.innerHeight}`,
    timestamp: new Date().toISOString()
  }
})

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    activityLogger.logActivity({
      type: 'page_hidden',
      action: 'page_visibility_change',
      metadata: {
        timestamp: new Date().toISOString()
      }
    })
  } else {
    activityLogger.logActivity({
      type: 'page_visible',
      action: 'page_visibility_change',
      metadata: {
        timestamp: new Date().toISOString()
      }
    })
  }
})

// Handle beforeunload
window.addEventListener('beforeunload', () => {
  // Log session end
  activityLogger.logSessionEnd()
})

// Handle online/offline status
window.addEventListener('online', () => {
  activityLogger.logActivity({
    type: 'connection_restored',
    action: 'network_status_change',
    metadata: {
      timestamp: new Date().toISOString()
    }
  })
})

window.addEventListener('offline', () => {
  activityLogger.logActivity({
    type: 'connection_lost',
    action: 'network_status_change',
    metadata: {
      timestamp: new Date().toISOString()
    }
  })
})

// Export for testing
export { app, router, pinia }