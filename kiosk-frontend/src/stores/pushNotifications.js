/**
 * Push Notifications Store
 * Manages push notification state and preferences
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import pushNotificationService from '@/core/services/pushNotificationService'

export const usePushNotificationsStore = defineStore('pushNotifications', () => {
  // State
  const isSupported = ref(false)
  const permission = ref('default')
  const isSubscribed = ref(false)
  const isInitialized = ref(false)
  const subscription = ref(null)
  const preferences = ref({
    enabled: true,
    productionOrders: true,
    grn: true,
    quality: true,
    system: true,
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00'
    }
  })

  // Computed
  const canSubscribe = computed(() => {
    return isSupported.value && permission.value === 'granted' && !isSubscribed.value
  })

  const canUnsubscribe = computed(() => {
    return isSubscribed.value
  })

  const needsPermission = computed(() => {
    return isSupported.value && permission.value === 'default'
  })

  // Actions
  async function initialize() {
    try {
      const initialized = await pushNotificationService.initialize()
      isSupported.value = initialized
      isInitialized.value = initialized

      if (initialized) {
        permission.value = pushNotificationService.getPermission()
        const currentSubscription = await pushNotificationService.getSubscription()
        if (currentSubscription) {
          isSubscribed.value = true
          subscription.value = currentSubscription
        }
      }
    } catch (error) {
      console.error('Error initializing push notifications:', error)
    }
  }

  async function requestPermission() {
    try {
      const newPermission = await pushNotificationService.requestPermission()
      permission.value = newPermission
      return newPermission
    } catch (error) {
      console.error('Error requesting permission:', error)
      throw error
    }
  }

  async function subscribe(plantId = null) {
    try {
      const result = await pushNotificationService.subscribe(plantId)
      if (result.success) {
        isSubscribed.value = true
        subscription.value = result.subscription
      }
      return result
    } catch (error) {
      console.error('Error subscribing:', error)
      throw error
    }
  }

  async function unsubscribe() {
    try {
      const result = await pushNotificationService.unsubscribe()
      if (result) {
        isSubscribed.value = false
        subscription.value = null
      }
      return result
    } catch (error) {
      console.error('Error unsubscribing:', error)
      throw error
    }
  }

  function updatePreferences(newPreferences) {
    preferences.value = { ...preferences.value, ...newPreferences }
    // Optionally save to backend
    // savePreferencesToBackend(preferences.value)
  }

  function isQuietHours() {
    if (!preferences.value.quietHours.enabled) {
      return false
    }

    const now = new Date()
    const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    const { start, end } = preferences.value.quietHours

    // Handle quiet hours that span midnight
    if (start > end) {
      return currentTime >= start || currentTime <= end
    } else {
      return currentTime >= start && currentTime <= end
    }
  }

  function shouldShowNotification(type) {
    if (!preferences.value.enabled || !isSubscribed.value) {
      return false
    }

    if (isQuietHours() && type !== 'system') {
      return false
    }

    return preferences.value[type] !== false
  }

  return {
    // State
    isSupported,
    permission,
    isSubscribed,
    isInitialized,
    subscription,
    preferences,
    
    // Computed
    canSubscribe,
    canUnsubscribe,
    needsPermission,
    
    // Actions
    initialize,
    requestPermission,
    subscribe,
    unsubscribe,
    updatePreferences,
    isQuietHours,
    shouldShowNotification
  }
})

