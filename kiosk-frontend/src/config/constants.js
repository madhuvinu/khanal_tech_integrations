/**
 * Application Constants and Configuration
 * Centralized configuration for the Khanal Foods Kiosk System
 */

// Central place to configure environment per machine. Edit src/config/kiosk.settings.js as needed.
import KIOSK_SETTINGS from './kiosk.settings.js'

// Infer site origin in browser, else fallback
const SITE_ORIGIN = (typeof window !== 'undefined' && window.location?.origin)
  ? window.location.origin
  : (KIOSK_SETTINGS.EXPLICIT_SITE_URL || 'http://localhost:8000')

// Compute API base
const FRAPPE_API_URL = (function computeApiUrl() {
  if (KIOSK_SETTINGS.EXPLICIT_API_URL) return KIOSK_SETTINGS.EXPLICIT_API_URL.replace(/\/$/, '')
  // If running via Vite dev server (port match), use DEV_BACKEND_URL
  if (typeof window !== 'undefined') {
    const onDevPort = String(window.location.port || '') === String(KIOSK_SETTINGS.DEV_SERVER.PORT)
    if (onDevPort && KIOSK_SETTINGS.DEV_BACKEND_URL) {
      return KIOSK_SETTINGS.DEV_BACKEND_URL.replace(/\/$/, '') + '/api'
    }
  }
  // Default to same-origin /api when served by Frappe
  return '/api'
})()

// Compute WS URL
const WS_URL = (function computeWsUrl() {
  if (KIOSK_SETTINGS.EXPLICIT_WS_URL) return KIOSK_SETTINGS.EXPLICIT_WS_URL
  try {
    const site = KIOSK_SETTINGS.EXPLICIT_SITE_URL || SITE_ORIGIN
    const url = new URL(site)
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return url.origin
  } catch {
    if (typeof window !== 'undefined' && window.location) {
      return (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host
    }
    return 'ws://localhost:8000'
  }
})()

export const APP_CONFIG = {
  // Application Information
  APP_NAME: 'Khanal Foods Kiosk',
  APP_VERSION: '1.0.0',
  APP_DESCRIPTION: 'Plant-Independent Kiosk System',
  
  // Environment
  IS_DEVELOPMENT: typeof window !== 'undefined' ? !window.location.pathname.startsWith(KIOSK_SETTINGS.BASE_PATH) : false,
  IS_PRODUCTION: typeof window !== 'undefined' ? window.location.pathname.startsWith(KIOSK_SETTINGS.BASE_PATH) : true,
  
  // Frappe Backend Configuration
  BASE_PATH: KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, ''),
  FRAPPE_API_URL,
  FRAPPE_SITE_URL: KIOSK_SETTINGS.EXPLICIT_SITE_URL || SITE_ORIGIN,
  WS_URL,
  
  // Authentication Configuration
  USE_REAL_AUTH: true,
  
  // Session Configuration
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
  TOKEN_REFRESH_INTERVAL: 5 * 60 * 1000, // 5 minutes
  MAX_SESSION_DURATION: 8 * 60 * 60 * 1000, // 8 hours
  
  // Activity Logging Configuration
  ACTIVITY_BATCH_SIZE: 10,
  ACTIVITY_BATCH_INTERVAL: 30000, // 30 seconds
  ACTIVITY_RETRY_ATTEMPTS: 3,
  ACTIVITY_RETRY_DELAY: 1000, // 1 second
  
  // WebSocket Configuration
  WS_RECONNECT_ATTEMPTS: 5,
  WS_RECONNECT_DELAY: 1000, // 1 second
  WS_HEARTBEAT_INTERVAL: 30000, // 30 seconds
  
  // UI Configuration
  THEME: 'light', // light, dark
  LANGUAGE: 'en',
  DEFAULT_PLANT: 'mahadevpura',
  
  // API Configuration
  API_TIMEOUT: 10000, // 10 seconds
  API_RETRY_ATTEMPTS: 3,
  API_RETRY_DELAY: 1000, // 1 second
  
  // Feature Flags
  FEATURES: {
    REAL_TIME_LOGGING: false,
    OFFLINE_SUPPORT: true,
    PUSH_NOTIFICATIONS: false,
    ADVANCED_ANALYTICS: true,
    DEBUG_MODE: import.meta.env.DEV,
    CONSOLE_LOGGING: import.meta.env.DEV
  },
  
  // Plant Configuration
  PLANTS: {
    MAHADEVPURA: 'mahadevpura',
    NANDI_HILLS: 'nandi-hills',
    MALUR: 'malur',
    KRISHNAGIRI: 'krishnagiri',
    CHAMPAVATH: 'champavath'
  },
  
  // User Roles
  ROLES: {
    ADMIN: 'System Administrator',
    PLANT_MANAGER: 'Plant Manager',
    PLANT_OPERATOR: 'Plant Operator',
    SUPERVISOR: 'Supervisor',
    TECHNICIAN: 'Technician'
  },
  
  // Permissions
  PERMISSIONS: {
    DASHBOARD: 'dashboard',
    PROFILE: 'profile',
    GRN: 'grn',
    CRATE: 'crate',
    PRODUCTION_ORDER: 'production-order',
    DEPARTMENT: 'department',
    ADMIN: 'admin',
    SETTINGS: 'settings',
    REPORTS: 'reports'
  },
  
  // API Endpoints
  API_ENDPOINTS: {
    // Authentication
    LOGIN: '/method/login',
    LOGOUT: '/method/logout',
    VERIFY_PLANT_ACCESS: '/method/khanal_tech_integrations.api.auth.verify_plant_access',
    GET_USER_PERMISSIONS: '/method/khanal_tech_integrations.api.auth.get_user_permissions',
    GENERATE_PLANT_TOKEN: '/method/khanal_tech_integrations.api.auth.generate_plant_token',
    REFRESH_TOKEN: '/method/khanal_tech_integrations.api.auth.refresh_token',
    VERIFY_SESSION: '/method/khanal_tech_integrations.api.auth.verify_session',
    CHANGE_PASSWORD: '/method/khanal_tech_integrations.api.auth.change_password',
    REQUEST_PASSWORD_RESET: '/method/khanal_tech_integrations.api.auth.request_password_reset',
    RESET_PASSWORD_WITH_TOKEN: '/method/khanal_tech_integrations.api.auth.reset_password_with_token',
    
    // Plant Data
    GET_PLANTS: '/method/khanal_tech_integrations.api.auth.get_plants',
    GET_PLANT_DETAILS: '/method/khanal_tech_integrations.api.auth.get_plant_details',
    GET_USER_PLANTS: '/method/khanal_tech_integrations.api.auth.get_user_plants',
    GET_PLANT_STATS: '/method/khanal_tech_integrations.api.auth.get_plant_stats',
    GET_PLANT_DEPARTMENTS: '/method/khanal_tech_integrations.api.auth.get_plant_departments',
    
    // Activity Logging
    LOG_ACTIVITY: '/method/khanal_tech_integrations.api.activity.log_activity',
    GET_ACTIVITY_LOG: '/method/khanal_tech_integrations.api.activity.get_activity_log',
    EXPORT_ACTIVITY_LOG: '/method/khanal_tech_integrations.api.activity.export_activity_log'
  },
  
  // Plant-Specific API Endpoints
  PLANT_API_ENDPOINTS: {
    // Nandi Hills Plant APIs
    NANDI_HILLS: {
      // GRN Module
      GRN: {
        GET_PURCHASE_ORDERS: '/method/khanal_tech_integrations.api.plants.nandi_hills.grn.get_purchase_orders',
        GET_PO_LINE_ITEMS: '/method/khanal_tech_integrations.api.plants.nandi_hills.grn.get_po_line_items',
        CREATE_GRN_DRAFT: '/method/khanal_tech_integrations.api.plants.nandi_hills.grn.create_grn_draft',
        GET_GRN_LIST: '/method/khanal_tech_integrations.api.plants.nandi_hills.grn.get_grn_list',
        GET_GRN_DETAILS: '/method/khanal_tech_integrations.api.plants.nandi_hills.grn.get_grn_details'
      },
      // Disassembly Module
      DISASSEMBLY: {
        GET_DISASSEMBLY_DETAILS: '/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_disassembly_details',
        CREATE_GOODS_ISSUE: '/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.create_goods_issue',
        CREATE_GOODS_RECEIPT: '/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.create_goods_receipt',
        GET_COMPLETED_DISASSEMBLIES: '/method/khanal_tech_integrations.api.plants.nandi_hills.disassembly.get_completed_disassemblies'
      },
      // Production Module
      PRODUCTION: {
        SEARCH_BOM: '/method/khanal_tech_integrations.api.plants.nandi_hills.production.search_bom',
        GET_ITT1_COMPONENTS: '/method/khanal_tech_integrations.api.plants.nandi_hills.production.get_itt1_components',
        GET_OITT_HEADER: '/method/khanal_tech_integrations.api.plants.nandi_hills.production.get_oitt_header',
        GET_BATCH_NUMBERS: '/method/khanal_tech_integrations.api.plants.nandi_hills.production.get_batch_numbers'
      },
      // Batch Number Generator Module
      BATCH_NUMBER_GENERATOR: {
        GET_BATCHES: '/method/khanal_tech_integrations.api.plants.batch_number_generator.get_batches',
        GENERATE_BATCHES: '/method/khanal_tech_integrations.api.plants.batch_number_generator.generate_batches'
      }
    }
    // Add other plants here as needed:
    // MALUR: { ... },
    // KRISHNAGIRI: { ... },
    // CHAMPAVATH: { ... },
    // MAHADEVPURA: { ... }
  },
  
  // Error Messages
  ERROR_MESSAGES: {
    NETWORK_ERROR: 'Network error. Please check your connection.',
    AUTHENTICATION_FAILED: 'Authentication failed. Please check your credentials.',
    PLANT_ACCESS_DENIED: 'Access denied for this plant.',
    SESSION_EXPIRED: 'Your session has expired. Please login again.',
    INVALID_CREDENTIALS: 'Invalid email or password.',
    USER_NOT_FOUND: 'User not found.',
    PLANT_NOT_FOUND: 'Plant not found.',
    PERMISSION_DENIED: 'You do not have permission to access this resource.',
    SERVER_ERROR: 'Server error. Please try again later.',
    VALIDATION_ERROR: 'Please check your input and try again.'
  },
  
  // Success Messages
  SUCCESS_MESSAGES: {
    LOGIN_SUCCESS: 'Login successful!',
    LOGOUT_SUCCESS: 'Logged out successfully!',
    PASSWORD_CHANGED: 'Password changed successfully!',
    PROFILE_UPDATED: 'Profile updated successfully!',
    DATA_SAVED: 'Data saved successfully!',
    OPERATION_COMPLETED: 'Operation completed successfully!'
  },
  
  // Validation Rules
  VALIDATION: {
    EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    PASSWORD_MIN_LENGTH: 8,
    PASSWORD_MAX_LENGTH: 128,
    PLANT_ID_REGEX: /^[a-z0-9-_]+$/,
    USERNAME_REGEX: /^[a-zA-Z0-9._-]+$/
  },
  
  // Local Storage Keys
  STORAGE_KEYS: {
    SESSION: 'kiosk_session',
    SELECTED_PLANT: 'selected_plant',
    USER_PREFERENCES: 'user_preferences',
    THEME: 'kiosk_theme',
    LANGUAGE: 'kiosk_language',
    OFFLINE_DATA: 'kiosk_offline_data'
  },
  
  // Routes (prefixed with base path for direct navigation)
  ROUTES: {
    PLANT_SELECTION: `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/login`,
    LOGIN: `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/login`,
    DASHBOARD: `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/dashboard`,
    PROFILE: `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/profile`,
    NOT_FOUND: `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/404`,
    UNAUTHORIZED: `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/unauthorized`,
    plantDashboard: (plantId) => `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/plant/${plantId}/dashboard`,
    plantFeature: (plantId, feature) => `${KIOSK_SETTINGS.BASE_PATH.replace(/\/$/, '')}/plant/${plantId}/${feature}`
  }
}

export default APP_CONFIG
