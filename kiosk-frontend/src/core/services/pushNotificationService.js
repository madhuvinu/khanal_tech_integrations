/**
 * Push Notification Service
 * Handles Web Push notification subscriptions and management
 */

import { APP_CONFIG } from '@/config/constants'

class PushNotificationService {
  constructor() {
    this.registration = null
    this.subscription = null
    this.vapidPublicKey = null
  }

  /**
   * Initialize push notification service
   * @returns {Promise<boolean>} True if initialized successfully
   */
  async initialize() {
    try {
      // Check if browser supports push notifications
      const hasServiceWorker = 'serviceWorker' in navigator
      const hasPushManager = 'PushManager' in window
      const hasNotification = 'Notification' in window
      
      console.log('🔔 Push notification support check:', {
        hasServiceWorker,
        hasPushManager,
        hasNotification,
        protocol: window.location.protocol,
        host: window.location.host,
        userAgent: navigator.userAgent.substring(0, 50) + '...'
      })
      
      // Check if we're in a secure context (HTTPS or localhost)
      const isSecureContext = window.isSecureContext || 
        window.location.hostname === 'localhost' || 
        window.location.hostname === '127.0.0.1' ||
        window.location.protocol === 'https:'
      
      if (!hasServiceWorker) {
        console.warn('❌ Service Worker API not supported in this browser')
        alert('Service Worker API not supported. Please use Chrome, Firefox, or Edge.')
        return false
      }
      
      // Warn if not secure context (but still try to register)
      if (!isSecureContext && window.location.protocol === 'http:') {
        console.warn('⚠️ Service workers on HTTP only work for localhost/127.0.0.1')
        console.warn('💡 Current hostname:', window.location.hostname)
        console.warn('💡 Try accessing via http://localhost:8003 instead')
        // Still try to register - some browsers may allow it
      }
      
      if (!hasPushManager) {
        console.warn('❌ PushManager API not supported in this browser')
        // Check if iOS Safari
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
        const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent)
        const isStandalone = window.navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches
        
        if (isIOS && !isStandalone) {
          alert('📱 For push notifications on iPhone:\n\n1. Tap the Share button (bottom)\n2. Tap "Add to Home Screen"\n3. Open from Home Screen\n\nPush notifications only work when installed as an app.')
        } else if (isIOS && isStandalone) {
          // iOS PWA but still no PushManager - older iOS version
          alert('Push notifications require iOS 16.4 or later. Please update your iPhone.')
        } else {
          alert('PushManager API not supported. Please use Chrome, Firefox, or Edge.')
        }
        return false
      }

      if (!hasNotification) {
        console.warn('❌ Notification API not supported in this browser')
        alert('Notification API not supported. Please use Chrome, Firefox, or Edge.')
        return false
      }

      // Register service worker first
      console.log('📝 Registering service worker...')
      try {
        const registration = await this.registerServiceWorker()
        if (!registration) {
          console.warn('❌ Service worker registration failed - push notifications disabled')
          return false
        }
        console.log('✅ Service worker registered:', registration)
      } catch (swError) {
        console.warn('⚠️ Service worker registration failed (SSL or 404 issue):', swError.message)
        console.warn('Push notifications will not work. This is expected with self-signed SSL certificates.')
        return false
      }

      // Get VAPID public key from backend
      console.log('🔑 Fetching VAPID public key...')
      await this.fetchVapidPublicKey()
      console.log('✅ VAPID key fetched')

      console.log('✅ Push notifications initialized successfully')
      return true
    } catch (error) {
      console.error('❌ Error initializing push notifications:', error)
      // Don't show alert - just log and return false
      return false
    }
  }

  /**
   * Fetch VAPID public key from backend
   */
  async fetchVapidPublicKey() {
    try {
      const response = await fetch(
        `${APP_CONFIG.FRAPPE_API_URL}/method/khanal_tech_integrations.api.push_notifications.get_vapid_public_key_api`,
        {
          method: 'GET',
          credentials: 'include'
        }
      )

      const data = await response.json()
      
      if (data.message && data.message.success && data.message.public_key) {
        this.vapidPublicKey = data.message.public_key
        return this.vapidPublicKey
      } else {
        throw new Error('Failed to get VAPID public key')
      }
    } catch (error) {
      console.error('Error fetching VAPID public key:', error)
      throw error
    }
  }

  /**
   * Register service worker
   */
  async registerServiceWorker() {
    try {
      if (!('serviceWorker' in navigator)) {
        throw new Error('Service workers are not supported in this browser')
      }

      // Check if service worker is already registered
      if (navigator.serviceWorker.controller) {
        console.log('✅ Service worker already controlling the page')
        this.registration = await navigator.serviceWorker.ready
        return this.registration
      }

      // Wait a bit for VitePWA to register (if it does)
      try {
        this.registration = await Promise.race([
          navigator.serviceWorker.ready,
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 2000))
        ])
        console.log('✅ Service worker ready (registered by VitePWA)')
        return this.registration
      } catch (e) {
        console.log('⏳ Service worker not ready yet, attempting manual registration...')
      }

      // Try to register manually - VitePWA generates service worker at build time
      // The service worker file should be in the public directory or generated by VitePWA
      // Need to use the correct base path based on environment
      const basePath = APP_CONFIG.BASE_PATH || '/kiosk'
      const normalizedBasePath = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath
      
      // In production, assets are served from /assets/khanal_tech_integrations/kiosk/
      // In development, they're served from /kiosk/
      const isProduction = APP_CONFIG.IS_PRODUCTION
      const assetBase = isProduction 
        ? '/assets/khanal_tech_integrations/kiosk'
        : normalizedBasePath
      
      const swPaths = [
        `${assetBase}/sw.js`,  // Primary path (production or dev)
        `${normalizedBasePath}/sw.js`,  // Base path fallback
        '/sw.js',  // Root (fallback)
        '/workbox-sw.js',  // Root VitePWA generated
        '/service-worker.js'  // Alternative
      ]
      
      console.log('🔍 Trying service worker paths:', swPaths)
      console.log('📍 Environment:', { isProduction, basePath, normalizedBasePath, assetBase })
      
      let registered = false
      let lastError = null
      
      for (const swPath of swPaths) {
        try {
          console.log(`📝 Attempting to register service worker at: ${swPath}`)
          
          // Service worker scope: must match the service worker's directory
          // Service worker at /assets/khanal_tech_integrations/kiosk/sw.js can only control
          // paths under /assets/khanal_tech_integrations/kiosk/ by default
          // For HTTP (non-HTTPS), we need to use the service worker's actual directory as scope
          let scope = '/'
          
          if (swPath.startsWith('/assets/')) {
            // Use the service worker's directory as scope (required for HTTP)
            const swDir = swPath.substring(0, swPath.lastIndexOf('/'))
            scope = swDir + '/'
          } else if (swPath.startsWith('/kiosk/')) {
            scope = '/kiosk/'
          }
          
          console.log(`📌 Using scope: ${scope} for service worker: ${swPath}`)
          
          // For HTTP, we must use the service worker's directory as scope
          // The "operation is insecure" error happens when trying to use a scope
          // outside the service worker's directory without HTTPS
          this.registration = await navigator.serviceWorker.register(swPath, {
            scope: scope,
            updateViaCache: 'none'
          })
          console.log(`✅ Service worker registered at: ${swPath}`, this.registration)
          registered = true
          break
        } catch (err) {
          console.log(`❌ Failed to register at ${swPath}:`, err.message)
          lastError = err
        }
      }
      
      if (!registered) {
        // Last attempt: wait a bit more and check if VitePWA registered it
        console.log('⏳ Waiting for VitePWA to register service worker...')
        await new Promise(resolve => setTimeout(resolve, 2000))
        try {
          this.registration = await navigator.serviceWorker.ready
          console.log('✅ Service worker ready after wait')
          return this.registration
        } catch (e) {
          console.error('❌ Service worker registration failed:', lastError || e)
          throw new Error(`Failed to register service worker: ${lastError?.message || e.message}`)
        }
      }
      
      return this.registration
    } catch (error) {
      console.error('❌ Error registering service worker:', error)
      console.error('Service worker registration details:', {
        error: error.message,
        stack: error.stack,
        controller: navigator.serviceWorker.controller,
        registrations: await navigator.serviceWorker.getRegistrations().catch(() => [])
      })
      return null
    }
  }

  /**
   * Request notification permission
   * @returns {Promise<string>} Permission status (granted, denied, default)
   */
  async requestPermission() {
    try {
      if (!('Notification' in window)) {
        throw new Error('Notifications are not supported')
      }

      const permission = await Notification.requestPermission()
      return permission
    } catch (error) {
      console.error('Error requesting notification permission:', error)
      throw error
    }
  }

  /**
   * Get current notification permission
   * @returns {string} Permission status
   */
  getPermission() {
    if (!('Notification' in window)) {
      return 'unsupported'
    }
    return Notification.permission
  }

  /**
   * Subscribe to push notifications
   * @param {string} plantId - Optional plant ID
   * @returns {Promise<Object>} Subscription object
   */
  async subscribe(plantId = null) {
    try {
      // Check permission first
      if (this.getPermission() !== 'granted') {
        const permission = await this.requestPermission()
        if (permission !== 'granted') {
          throw new Error('Notification permission denied')
        }
      }

      // Ensure service worker is ready
      if (!this.registration) {
        await this.registerServiceWorker()
      }

      // Ensure VAPID key is available
      if (!this.vapidPublicKey) {
        await this.fetchVapidPublicKey()
      }

      // Convert VAPID public key to Uint8Array
      const applicationServerKey = this.urlBase64ToUint8Array(this.vapidPublicKey)

      // Check for existing subscription and unsubscribe if VAPID key changed
      try {
        const existingSubscription = await this.registration.pushManager.getSubscription()
        if (existingSubscription) {
          console.log('📋 Found existing subscription, checking VAPID key...')
          
          // Try to subscribe - if it fails with InvalidStateError, unsubscribe first
          try {
            this.subscription = await this.registration.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: applicationServerKey
            })
            console.log('✅ Subscription created/updated')
          } catch (subscribeError) {
            // If error is about different applicationServerKey, unsubscribe first
            if ((subscribeError.name === 'InvalidStateError' || subscribeError.name === 'DOMException') && 
                (subscribeError.message.includes('different application server key') ||
                 subscribeError.message.includes('different applicationServerKey') ||
                 subscribeError.message.includes('gcm_sender_id'))) {
              console.log('⚠️ VAPID key changed. Unsubscribing from old subscription...')
              await existingSubscription.unsubscribe()
              console.log('✅ Unsubscribed from old subscription')
              
              // Notify backend about unsubscribe
              try {
                await this.sendUnsubscribeToBackend(existingSubscription.endpoint)
              } catch (unsubBackendError) {
                console.warn('⚠️ Could not notify backend of unsubscribe:', unsubBackendError)
              }
              
              // Now subscribe with new key
              this.subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
              })
              console.log('✅ Subscribed with new VAPID key')
            } else {
              throw subscribeError
            }
          }
        } else {
          // No existing subscription, create new one
          this.subscription = await this.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
          })
          console.log('✅ New subscription created')
        }
      } catch (error) {
        // If getSubscription fails or subscribe fails for other reasons
        if ((error.name === 'InvalidStateError' || error.name === 'DOMException') && 
            (error.message.includes('different application server key') ||
             error.message.includes('different applicationServerKey') ||
             error.message.includes('gcm_sender_id'))) {
          console.log('⚠️ InvalidStateError: Attempting to unsubscribe and resubscribe...')
          
          // Try to get and unsubscribe
          try {
            const existingSub = await this.registration.pushManager.getSubscription()
            if (existingSub) {
              await existingSub.unsubscribe()
              console.log('✅ Unsubscribed')
            }
          } catch (unsubError) {
            console.warn('⚠️ Could not unsubscribe:', unsubError)
          }
          
          // Retry subscription
          this.subscription = await this.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
          })
          console.log('✅ Subscription created after unsubscribe')
        } else {
          throw error
        }
      }

      // Get subscription details
      const subscriptionData = {
        endpoint: this.subscription.endpoint,
        keys: {
          p256dh: this.arrayBufferToBase64(this.subscription.getKey('p256dh')),
          auth: this.arrayBufferToBase64(this.subscription.getKey('auth'))
        }
      }

      // Send subscription to backend
      console.log('📤 Sending subscription to backend...', { plantId, endpoint: subscriptionData.endpoint })
      const backendResult = await this.sendSubscriptionToBackend(subscriptionData, plantId)
      console.log('✅ Backend subscription result:', backendResult)

      return {
        success: true,
        subscription: subscriptionData,
        backend: backendResult
      }
    } catch (error) {
      console.error('Error subscribing to push notifications:', error)
      throw error
    }
  }

  /**
   * Unsubscribe from push notifications
   * @returns {Promise<boolean>} True if unsubscribed successfully
   */
  async unsubscribe() {
    try {
      if (!this.subscription) {
        // Try to get existing subscription
        if (this.registration) {
          this.subscription = await this.registration.pushManager.getSubscription()
        }
      }

      if (this.subscription) {
        // Unsubscribe from push service
        await this.subscription.unsubscribe()

        // Notify backend
        await this.sendUnsubscribeToBackend(this.subscription.endpoint)

        this.subscription = null
        return true
      }

      return false
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error)
      throw error
    }
  }

  /**
   * Get current subscription
   * @returns {Promise<Object|null>} Current subscription or null
   */
  async getSubscription() {
    try {
      if (!this.registration) {
        await this.registerServiceWorker()
      }

      this.subscription = await this.registration.pushManager.getSubscription()
      
      if (this.subscription) {
        return {
          endpoint: this.subscription.endpoint,
          keys: {
            p256dh: this.arrayBufferToBase64(this.subscription.getKey('p256dh')),
            auth: this.arrayBufferToBase64(this.subscription.getKey('auth'))
          }
        }
      }

      return null
    } catch (error) {
      console.error('Error getting subscription:', error)
      return null
    }
  }

  /**
   * Send subscription to backend
   * @param {Object} subscriptionData - Subscription data
   * @param {string} plantId - Optional plant ID
   */
  async sendSubscriptionToBackend(subscriptionData, plantId = null) {
    try {
      const response = await fetch(
        `${APP_CONFIG.FRAPPE_API_URL}/method/khanal_tech_integrations.api.push_notifications.subscribe_push_api`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            subscription: JSON.stringify(subscriptionData),
            plant_id: plantId
          })
        }
      )

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ Subscription API error:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📝 Subscription API response:', data)
      
      if (data.message && data.message.success) {
        console.log('✅ Subscription saved to backend:', data.message)
        return data.message
      } else {
        const errorMsg = data.message?.message || data.exc || 'Failed to save subscription'
        console.error('❌ Subscription save failed:', errorMsg)
        throw new Error(errorMsg)
      }
    } catch (error) {
      console.error('Error sending subscription to backend:', error)
      throw error
    }
  }

  /**
   * Send unsubscribe request to backend
   * @param {string} endpoint - Subscription endpoint
   */
  async sendUnsubscribeToBackend(endpoint) {
    try {
      const response = await fetch(
        `${APP_CONFIG.FRAPPE_API_URL}/method/khanal_tech_integrations.api.push_notifications.unsubscribe_push_api`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            endpoint: endpoint
          })
        }
      )

      const data = await response.json()
      return data.message
    } catch (error) {
      console.error('Error sending unsubscribe to backend:', error)
      throw error
    }
  }

  /**
   * Convert URL-safe base64 to Uint8Array
   * @param {string} base64String - Base64 string
   * @returns {Uint8Array} Uint8Array
   */
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
  }

  /**
   * Convert ArrayBuffer to base64
   * @param {ArrayBuffer} buffer - ArrayBuffer
   * @returns {string} Base64 string
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return window.btoa(binary)
  }
}

// Export singleton instance
export default new PushNotificationService()

