/**
 * Composable for Push Notifications
 * Provides reactive push notification functionality
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import pushNotificationService from '@/core/services/pushNotificationService'
import { useSessionStore } from '@/core/stores/session'

export function usePushNotifications() {
  const sessionStore = useSessionStore()
  
  // Reactive state
  const isSupported = ref(false)
  const permission = ref('default')
  const isSubscribed = ref(false)
  const isInitialized = ref(false)
  const isLoading = ref(false)
  const error = ref(null)
  const subscription = ref(null)

  // Computed properties
  const canSubscribe = computed(() => {
    return isSupported.value && permission.value === 'granted' && !isSubscribed.value
  })

  const canUnsubscribe = computed(() => {
    return isSubscribed.value
  })

  const needsPermission = computed(() => {
    return isSupported.value && permission.value === 'default'
  })

  /**
   * Initialize push notifications
   */
  const initialize = async () => {
    try {
      isLoading.value = true
      error.value = null

      const initialized = await pushNotificationService.initialize()
      isSupported.value = initialized
      isInitialized.value = initialized

      if (initialized) {
        // Check current permission
        permission.value = pushNotificationService.getPermission()

        // Check if already subscribed
        const currentSubscription = await pushNotificationService.getSubscription()
        if (currentSubscription) {
          isSubscribed.value = true
          subscription.value = currentSubscription
        }
      }
    } catch (err) {
      error.value = err.message
      console.error('Error initializing push notifications:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Request notification permission
   */
  const requestPermission = async () => {
    try {
      isLoading.value = true
      error.value = null

      const newPermission = await pushNotificationService.requestPermission()
      permission.value = newPermission

      if (newPermission === 'granted') {
        // Auto-subscribe after permission is granted
        await subscribe()
      } else if (newPermission === 'denied') {
        error.value = 'Notification permission denied. Please enable it in your browser settings.'
      }

      return newPermission
    } catch (err) {
      error.value = err.message
      console.error('Error requesting permission:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Subscribe to push notifications
   */
  const subscribe = async (plantId = null) => {
    try {
      isLoading.value = true
      error.value = null

      // Get plant ID from session if not provided
      if (!plantId) {
        const session = sessionStore.getSession()
        plantId = session?.plant?.id || null
      }

      const result = await pushNotificationService.subscribe(plantId)
      
      if (result.success) {
        isSubscribed.value = true
        subscription.value = result.subscription
      }

      return result
    } catch (err) {
      error.value = err.message
      console.error('Error subscribing to push notifications:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  const unsubscribe = async () => {
    try {
      isLoading.value = true
      error.value = null

      const result = await pushNotificationService.unsubscribe()
      
      if (result) {
        isSubscribed.value = false
        subscription.value = null
      }

      return result
    } catch (err) {
      error.value = err.message
      console.error('Error unsubscribing from push notifications:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Toggle subscription
   */
  const toggle = async () => {
    if (isSubscribed.value) {
      await unsubscribe()
    } else {
      if (permission.value !== 'granted') {
        await requestPermission()
      } else {
        await subscribe()
      }
    }
  }

  // Initialize on mount
  onMounted(() => {
    initialize()
  })

  return {
    // State
    isSupported,
    permission,
    isSubscribed,
    isInitialized,
    isLoading,
    error,
    subscription,
    
    // Computed
    canSubscribe,
    canUnsubscribe,
    needsPermission,
    
    // Methods
    initialize,
    requestPermission,
    subscribe,
    unsubscribe,
    toggle
  }
}

