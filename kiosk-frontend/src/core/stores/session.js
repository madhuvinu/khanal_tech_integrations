/**
 * Session Store - Manages user session and plant-specific data
 * Uses Pinia for state management with persistence
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSessionStore = defineStore('session', () => {
  // State
  const token = ref(null)
  const user = ref(null)
  const plant = ref(null)
  const permissions = ref([])
  const loginTime = ref(null)
  const expiresAt = ref(null)
  const isAuthenticated = ref(false)

  // Computed properties
  const currentUser = computed(() => user.value)
  const currentPlant = computed(() => plant.value)
  const userPermissions = computed(() => permissions.value)
  const sessionDuration = computed(() => {
    if (!loginTime.value) return 0
    return Date.now() - loginTime.value
  })
  const isSessionValid = computed(() => {
    if (!isAuthenticated.value || !expiresAt.value) return false
    // Convert expiresAt to timestamp if it's a string
    const expiryTime = typeof expiresAt.value === 'string' 
      ? new Date(expiresAt.value).getTime() 
      : expiresAt.value
    return Date.now() < expiryTime
  })

  // Actions
  function setSession(sessionData) {
    token.value = sessionData.token
    user.value = sessionData.user
    plant.value = sessionData.plant
    permissions.value = sessionData.plant?.permissions || []
    loginTime.value = Date.now()
    expiresAt.value = sessionData.expiresAt
    isAuthenticated.value = true

    // Store in localStorage for persistence
    localStorage.setItem('kiosk-session', JSON.stringify({
      token: token.value,
      user: user.value,
      plant: plant.value,
      permissions: permissions.value,
      loginTime: loginTime.value,
      expiresAt: expiresAt.value
    }))
  }

  function updateToken(newToken) {
    token.value = newToken
    
    // Update localStorage
    const stored = localStorage.getItem('kiosk-session')
    if (stored) {
      const sessionData = JSON.parse(stored)
      sessionData.token = newToken
      localStorage.setItem('kiosk-session', JSON.stringify(sessionData))
    }
  }

  function clearSession() {
    token.value = null
    user.value = null
    plant.value = null
    permissions.value = []
    loginTime.value = null
    expiresAt.value = null
    isAuthenticated.value = false

    // Clear localStorage
    localStorage.removeItem('kiosk-session')
    sessionStorage.clear()
  }

  function getSession() {
    if (isAuthenticated.value) {
      return {
        token: token.value,
        user: user.value,
        plant: plant.value,
        permissions: permissions.value,
        loginTime: loginTime.value,
        expiresAt: expiresAt.value
      }
    }
    return null
  }

  function hasPermission(permission) {
    return permissions.value.includes(permission)
  }

  function hasAnyPermission(permissionList) {
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  function hasAllPermissions(permissionList) {
    return permissionList.every(permission => permissions.value.includes(permission))
  }

  function updateUserData(userData) {
    user.value = { ...user.value, ...userData }
    
    // Update localStorage
    const stored = localStorage.getItem('kiosk-session')
    if (stored) {
      const sessionData = JSON.parse(stored)
      sessionData.user = user.value
      localStorage.setItem('kiosk-session', JSON.stringify(sessionData))
    }
  }

  function updatePlantData(plantData) {
    plant.value = { ...plant.value, ...plantData }
    
    // Update localStorage
    const stored = localStorage.getItem('kiosk-session')
    if (stored) {
      const sessionData = JSON.parse(stored)
      sessionData.plant = plant.value
      localStorage.setItem('kiosk-session', JSON.stringify(sessionData))
    }
  }

  function initializeFromStorage() {
    try {
      const stored = localStorage.getItem('kiosk-session')
      if (stored) {
        const sessionData = JSON.parse(stored)
        
        // Check if session is still valid
        const expiryTime = typeof sessionData.expiresAt === 'string' 
          ? new Date(sessionData.expiresAt).getTime() 
          : sessionData.expiresAt
        if (sessionData.expiresAt && Date.now() < expiryTime) {
          token.value = sessionData.token
          user.value = sessionData.user
          plant.value = sessionData.plant
          permissions.value = sessionData.permissions || []
          loginTime.value = sessionData.loginTime
          expiresAt.value = sessionData.expiresAt
          isAuthenticated.value = true
          return true
        } else {
          // Session expired, clear it
          clearSession()
        }
      }
    } catch (error) {
      console.error('Error initializing session from storage:', error)
      clearSession()
    }
    return false
  }

  function extendSession(newExpiresAt) {
    expiresAt.value = newExpiresAt
    
    // Update localStorage
    const stored = localStorage.getItem('kiosk-session')
    if (stored) {
      const sessionData = JSON.parse(stored)
      sessionData.expiresAt = newExpiresAt
      localStorage.setItem('kiosk-session', JSON.stringify(sessionData))
    }
  }

  // Session activity tracking
  const lastActivity = ref(Date.now())
  const activityTimeout = ref(null)

  function updateActivity() {
    lastActivity.value = Date.now()
    
    // Clear existing timeout
    if (activityTimeout.value) {
      clearTimeout(activityTimeout.value)
    }
    
    // Set new timeout for session expiry
    const timeoutDuration = 30 * 60 * 1000 // 30 minutes
    activityTimeout.value = setTimeout(() => {
      if (isAuthenticated.value) {
        console.log('Session timeout due to inactivity')
        clearSession()
        window.location.href = '/kiosk/login'
      }
    }, timeoutDuration)
  }

  function getSessionInfo() {
    return {
      isAuthenticated: isAuthenticated.value,
      user: user.value,
      plant: plant.value,
      permissions: permissions.value,
      sessionDuration: sessionDuration.value,
      lastActivity: lastActivity.value,
      isSessionValid: isSessionValid.value
    }
  }

  return {
    // State
    token,
    user,
    plant,
    permissions,
    loginTime,
    expiresAt,
    isAuthenticated,
    lastActivity,

    // Computed
    currentUser,
    currentPlant,
    userPermissions,
    sessionDuration,
    isSessionValid,

    // Actions
    setSession,
    updateToken,
    clearSession,
    getSession,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    updateUserData,
    updatePlantData,
    initializeFromStorage,
    extendSession,
    updateActivity,
    getSessionInfo
  }
})
