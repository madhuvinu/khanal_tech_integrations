import { createPinia } from 'pinia'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    currentPlant: null,
    isLoggedIn: false,
    user: null
  }),
  
  actions: {
    login(plantName, userData) {
      this.currentPlant = plantName
      this.isLoggedIn = true
      this.user = userData
      localStorage.setItem(`kiosk_${plantName}_logged_in`, 'true')
      localStorage.setItem(`kiosk_${plantName}_user`, JSON.stringify(userData))
    },
    
    logout() {
      if (this.currentPlant) {
        localStorage.removeItem(`kiosk_${this.currentPlant}_logged_in`)
        localStorage.removeItem(`kiosk_${this.currentPlant}_user`)
      }
      this.currentPlant = null
      this.isLoggedIn = false
      this.user = null
    },
    
    checkLogin(plantName) {
      const isLoggedIn = localStorage.getItem(`kiosk_${plantName}_logged_in`)
      const userData = localStorage.getItem(`kiosk_${plantName}_user`)
      
      if (isLoggedIn && userData) {
        this.currentPlant = plantName
        this.isLoggedIn = true
        this.user = JSON.parse(userData)
        return true
      }
      return false
    }
  }
})

export default createPinia()
