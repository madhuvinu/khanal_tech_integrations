/**
 * Activity Logger - Real-time session activity tracking
 * Integrates with Frappe backend for audit trail
 */

import axios from 'axios'
import { useSessionStore } from '../stores/session.js'
import { APP_CONFIG } from '../../config/constants.js'

class ActivityLogger {
  constructor() {
    this.baseURL = APP_CONFIG.FRAPPE_API_URL
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: APP_CONFIG.API_TIMEOUT
    })
    
    // Feature-flag controlled WebSocket (disabled by default)
    this.wsConnection = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = APP_CONFIG.FEATURES.REAL_TIME_LOGGING ? APP_CONFIG.WS_RECONNECT_ATTEMPTS : 0
    this.reconnectDelay = APP_CONFIG.FEATURES.REAL_TIME_LOGGING ? APP_CONFIG.WS_RECONNECT_DELAY : 0
    this.activityQueue = []
    this.isOnline = navigator.onLine
    
    // Offline + batch processing
    this.setupOfflineHandling()
    this.startBatchProcessor()

    // Optional WS if enabled
    if (APP_CONFIG.FEATURES.REAL_TIME_LOGGING) {
      this.setupWebSocket()
    }
  }

  setupWebSocket() {
    // Skip WebSocket only if explicitly disabled
    if (APP_CONFIG.USE_DEV_AUTH) {
      console.log('Activity logger: Development mode - WebSocket disabled')
      return
    }

    try {
      const wsURL = APP_CONFIG.WS_URL
      this.wsConnection = new WebSocket(wsURL)
      
      this.wsConnection.onopen = () => {
      // connected
        this.reconnectAttempts = 0
        this.processQueuedActivities()
      }
      
      this.wsConnection.onmessage = (event) => {
        const data = JSON.parse(event.data)
        this.handleWebSocketMessage(data)
      }
      
      this.wsConnection.onclose = () => {
      // disconnected
        this.attemptReconnect()
      }
      
      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
    } catch (error) {
      console.error('Failed to setup WebSocket:', error)
    }
  }

  setupOfflineHandling() {
    window.addEventListener('online', () => {
      this.isOnline = true
      // online
      this.processQueuedActivities()
    })
    
    window.addEventListener('offline', () => {
      this.isOnline = false
      // offline
    })
  }

  startBatchProcessor() {
    // Process queued activities every 30 seconds
    setInterval(() => {
      if (this.activityQueue.length > 0) {
        this.processQueuedActivities()
      }
    }, 30000)

    // Flush on tab hide/close
    const flush = () => {
      try {
        if (this.activityQueue.length > 0) {
          navigator.sendBeacon?.(
            `${this.baseURL}/method/khanal_tech_integrations.api.activity.log_batch_activities`,
            new Blob([JSON.stringify({ activities: JSON.stringify(this.activityQueue) })], { type: 'application/json' })
          )
        }
      } catch (err) {
        console.warn('Failed to flush activity queue on unload:', err)
      }
    }
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') flush()
    })
    window.addEventListener('beforeunload', flush)
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      
      setTimeout(() => {
        console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        this.setupWebSocket()
      }, delay)
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'activity_logged':
        console.log('Activity logged successfully:', data.activity_id)
        break
      case 'error':
        console.error('Activity logging error:', data.message)
        break
      default:
        console.log('Unknown WebSocket message:', data)
    }
  }

  /**
   * Log user activity
   * @param {Object} activity - Activity data
   */
  async logActivity(activity) {
    const sessionStore = useSessionStore()
    const session = sessionStore.getSession()
    
    if (!session) {
      // Silently skip logging when no session - this is normal during app initialization
      return
    }

    // In development mode with dev auth, just log to console
    if (APP_CONFIG.USE_DEV_AUTH) {
      console.log('Activity logged (dev mode):', {
        type: activity.type,
        user: session.user.email,
        plant: session.plant.id,
        timestamp: new Date().toISOString(),
        metadata: activity.metadata
      })
      return
    }

    const activityData = {
      id: this.generateActivityId(),
      user_id: this.hashOrRedact(session.user.email),
      plant_id: session.plant.id,
      activity_type: activity.type,
      page: activity.page || window.location.pathname,
      action: activity.action || 'unknown',
      timestamp: new Date().toISOString(),
      duration: activity.duration || 0,
      metadata: {
        ...activity.metadata,
        user_agent: (navigator.userAgent || '').slice(0, 256),
        screen_resolution: `${screen.width}x${screen.height}`,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        referrer: document.referrer,
        url: window.location.href
      }
    }

    // REST-only: log via API or queue
    if (this.isOnline) {
      try {
        await this.logActivityViaAPI(activityData)
      } catch (error) {
        console.error('API logging failed, queuing activity:', error)
        this.queueActivity(activityData)
      }
    } else {
      this.queueActivity(activityData)
    }
  }

  async logActivityViaAPI(activityData) {
    // Frappe expects named argument 'activity_data'
    const payload = { activity_data: activityData }
    const response = await this.apiClient.post('/method/khanal_tech_integrations.api.activity.log_activity', payload)
    return response.data
  }

  queueActivity(activityData) {
    this.activityQueue.push(activityData)
    
    // Store in localStorage for persistence
    localStorage.setItem('kiosk-activity-queue', JSON.stringify(this.activityQueue))
    
    // Limit queue size
    if (this.activityQueue.length > 100) {
      this.activityQueue = this.activityQueue.slice(-50) // Keep last 50
    }
  }

  async processQueuedActivities() {
    if (this.activityQueue.length === 0) return
    
    const activities = [...this.activityQueue]
    this.activityQueue = []
    
    try {
      const response = await this.apiClient.post('/method/khanal_tech_integrations.api.activity.log_batch_activities', {
        activities: JSON.stringify(activities)
      })
      
      console.log(`Processed ${activities.length} queued activities`)
      
      // Clear localStorage queue
      localStorage.removeItem('kiosk-activity-queue')
      
    } catch (error) {
      console.error('Failed to process queued activities:', error)
      // Re-queue activities
      this.activityQueue = [...activities, ...this.activityQueue]
    }
  }

  /**
   * Log page view
   */
  async logPageView(page, duration = 0) {
    await this.logActivity({
      type: 'page_view',
      page,
      duration,
      metadata: {
        page_title: document.title,
        page_load_time: performance.now()
      }
    })
  }

  /**
   * Log user action
   */
  async logUserAction(action, details = {}) {
    await this.logActivity({
      type: 'user_action',
      action,
      metadata: {
        ...details,
        timestamp: Date.now()
      }
    })
  }

  /**
   * Log error
   */
  async logError(error, context = {}) {
    await this.logActivity({
      type: 'error_occurred',
      action: 'error',
      metadata: {
        error_message: error.message,
        error_stack: error.stack,
        error_name: error.name,
        context,
        timestamp: Date.now()
      }
    })
  }

  /**
   * Log session start
   */
  async logSessionStart() {
    const sessionStore = useSessionStore()
    const session = sessionStore.getSession()
    
    if (session) {
      await this.logActivity({
        type: 'session_start',
        action: 'session_start',
        metadata: {
          login_time: new Date(session.loginTime).toISOString(),
          plant_name: session.plant.name,
          user_roles: session.user.roles || []
        }
      })
    }
  }

  /**
   * Log session end
   */
  async logSessionEnd() {
    const sessionStore = useSessionStore()
    const session = sessionStore.getSession()
    
    if (session) {
      const sessionDuration = Date.now() - session.loginTime
      
      await this.logActivity({
        type: 'session_end',
        action: 'session_end',
        duration: sessionDuration,
        metadata: {
          session_duration: sessionDuration,
          logout_time: new Date().toISOString()
        }
      })
    }
  }

  /**
   * Start tracking page time
   */
  startPageTracking(page) {
    this.currentPage = page
    this.pageStartTime = Date.now()
  }

  /**
   * End tracking page time
   */
  async endPageTracking() {
    if (this.currentPage && this.pageStartTime) {
      const duration = Date.now() - this.pageStartTime
      await this.logPageView(this.currentPage, duration)
      this.currentPage = null
      this.pageStartTime = null
    }
  }

  /**
   * Generate unique activity ID
   */
  generateActivityId() {
    return `activity_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  hashOrRedact(value) {
    try {
      if (!value) return 'redacted'
      // lightweight hash (non-crypto) to avoid leaking raw emails
      let h = 0
      for (let i = 0; i < value.length; i++) {
        h = (h << 5) - h + value.charCodeAt(i)
        h |= 0
      }
      return `u_${Math.abs(h)}`
    } catch (_) {
      return 'redacted'
    }
  }

  /**
   * Get activity statistics
   */
  async getActivityStats(timeRange = 'today') {
    try {
      const response = await this.apiClient.get('/method/khanal_tech_integrations.api.activity.get_activity_stats', {
        params: { time_range: timeRange }
      })
      return response.data.message
    } catch (error) {
      console.error('Failed to get activity stats:', error)
      return null
    }
  }

  /**
   * Cleanup
   */
  destroy() {
    if (this.wsConnection) {
      this.wsConnection.close()
    }
    
    // Process any remaining queued activities
    if (this.activityQueue.length > 0) {
      this.processQueuedActivities()
    }
  }
}

// Export singleton instance
export const useActivityLogger = () => {
  if (!window.activityLogger) {
    window.activityLogger = new ActivityLogger()
  }
  return window.activityLogger
}

export default useActivityLogger
