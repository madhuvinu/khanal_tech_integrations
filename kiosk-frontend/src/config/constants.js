/**
 * Application Constants and Configuration
 * Centralized configuration for the Khanal Foods Kiosk System
 */

export const APP_CONFIG = {
  // Application Information
  APP_NAME: 'Khanal Foods Kiosk',
  APP_VERSION: '1.0.0',
  APP_DESCRIPTION: 'Plant-Independent Kiosk System',
  
  // Environment
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
  
  // Frappe Backend Configuration
  // Dynamic API URL detection - works with any port
  FRAPPE_API_URL: (() => {
    if (typeof window === 'undefined') return '/api'
    
    // If running on Vite dev server (port 8081), route to Frappe backend
    if (window.location.port === '8081') {
      // Try to detect Frappe port from environment or use common defaults
      const frappePort = import.meta.env.VITE_FRAPPE_PORT || 
                        (window.location.hostname === 'localhost' ? '8003' : '8000')
      return `${window.location.protocol}//${window.location.hostname}:${frappePort}/api`
    }
    
    // If served from Frappe directly, use same origin
    return '/api'
  })(),
  FRAPPE_SITE_URL: (typeof window !== 'undefined') ? window.location.origin : '',
  WS_URL: (typeof window !== 'undefined')
    ? ((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host)
    : '',
  
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
    MAHADEVPURA: 'Mahadevpura',
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
  
  // Routes
  ROUTES: {
    PLANT_SELECTION: '/login',
    LOGIN: '/login',
    DASHBOARD: '/dashboard',
    PROFILE: '/profile',
    NOT_FOUND: '/404',
    UNAUTHORIZED: '/unauthorized'
  }
}

// Export individual configurations for easy access
export const {
  FRAPPE_API_URL,
  FRAPPE_SITE_URL,
  WS_URL,
  USE_REAL_AUTH,
  API_ENDPOINTS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  FEATURES,
  PLANTS,
  ROLES,
  PERMISSIONS
} = APP_CONFIG

export default APP_CONFIG
