/**
 * Session Store - Following /frontend pattern
 * Uses cookie-based authentication (standard Frappe)
 * NO JWT, NO CSRF logic needed!
 */

import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { ref, computed } from 'vue'

export const useSessionStore = defineStore('kiosk-session', () => {
  // Get user from cookie (standard Frappe approach)
  function sessionUser() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser === 'Guest') {
      _sessionUser = null
    }
    return _sessionUser
  }

  // Get current plant from cookie
  function currentPlant() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    return cookies.get('current_plant') || null
  }

  // Reactive state
  const user = ref(sessionUser())
  const plant = ref(currentPlant())
  const isAuthenticated = computed(() => !!user.value)

  // Login resource (standard Frappe login)
  const login = createResource({
    url: 'khanal_tech_integrations.api.auth.plant_login',
    makeParams({ email, password, plantId }) {
      return {
        usr: email,
        pwd: password,
        plant_id: plantId
      }
    },
    onError(error) {
      console.error('[Login] Error:', error)
      throw new Error(error?.messages?.[0] || 'Login failed')
    },
    onSuccess(data) {
      user.value = sessionUser()
      plant.value = data.plant_id || plantId
      
      // Store plant in cookie for persistence
      document.cookie = `current_plant=${plant.value}; path=/`
      
      login.reset()
      
      // Redirect to dashboard
      window.location.href = `/kiosk/plant/${plant.value}/dashboard`
    }
  })

  // Logout resource - but we'll use a custom function instead
  const logoutResource = createResource({
    url: 'logout',
    auto: false,
    onSuccess() {
      // This won't be called since we handle logout manually
    },
    onError() {
      // Silently ignore errors - we handle logout manually
    }
  })

  // Custom logout function that handles errors gracefully
  async function logout() {
    // Clear frontend state immediately
    user.value = null
    plant.value = null
    
    // Clear plant cookie (frontend only)
    document.cookie = 'current_plant=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
    
    // Get CSRF token (required for Frappe POST requests)
    const getCSRFToken = () => {
      // Try window.csrf_token first
      if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
        return window.csrf_token
      }
      // Fallback to window.boot.csrf_token
      if (window.boot && window.boot.csrf_token) {
        return window.boot.csrf_token
      }
      return null
    }
    
    const csrfToken = getCSRFToken()
    
    // Call logout API to clear server-side session cookie (user_id cookie)
    // This is important - Frappe manages the session cookie on the server
    const headers = {
      'Content-Type': 'application/json'
    }
    
    // Add CSRF token if available (required for Frappe POST requests)
    if (csrfToken) {
      headers['X-Frappe-CSRF-Token'] = csrfToken
    }
    
    // Try to call logout API with timeout
    // This clears the server-side session cookie (user_id)
    const logoutPromise = fetch('/api/method/logout', {
      method: 'POST',
      credentials: 'include', // Important: sends cookies with request
      headers: headers
    }).catch((error) => {
      // Silently ignore errors - frontend state is already cleared
      console.log('[Logout] API call failed (frontend state cleared anyway):', error)
    })
    
    // Wait for logout API (max 1 second) then redirect
    // This ensures server-side session cookie is cleared
    try {
      await Promise.race([
        logoutPromise,
        new Promise((resolve) => setTimeout(resolve, 1000)) // 1 second timeout
      ])
    } catch (error) {
      // Ignore errors - we'll redirect anyway
    }
    
    // Redirect to login page
    // Server-side session cookie (user_id) should be cleared by now
    window.location.href = '/kiosk/login'
  }

  // Verify session (check if still logged in)
  const verifySession = createResource({
    url: 'frappe.auth.get_logged_user',
    auto: false,
    onSuccess(data) {
      if (data?.message) {
        user.value = sessionUser()
      } else {
        user.value = null
        window.location.href = '/kiosk/login'
      }
    },
    onError() {
      user.value = null
      window.location.href = '/kiosk/login'
    }
  })

  // Switch plant
  async function switchPlant(newPlantId) {
    plant.value = newPlantId
    document.cookie = `current_plant=${newPlantId}; path=/`
    window.location.href = `/kiosk/plant/${newPlantId}/dashboard`
  }

  return {
    // State
    user,
    plant,
    isAuthenticated,
    
    // Resources
    login,
    logout, // This is now a function, not a resource
    verifySession,
    
    // Methods
    switchPlant,
    sessionUser,
    currentPlant
  }
})

