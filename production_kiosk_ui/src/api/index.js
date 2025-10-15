import axios from 'axios'
import { API_BASE, API_HEADERS } from './constants.js'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: API_HEADERS,
  timeout: 10000
})

// General API helper functions
export const apiHelpers = {
  async get(url, params = {}) {
    try {
      const response = await api.get(url, { params })
      return response.data
    } catch (error) {
      console.error('GET request failed:', error)
      throw error
    }
  },

  async post(url, data = {}) {
    try {
      const response = await api.post(url, data)
      return response.data
    } catch (error) {
      console.error('POST request failed:', error)
      throw error
    }
  },

  async put(url, data = {}) {
    try {
      const response = await api.put(url, data)
      return response.data
    } catch (error) {
      console.error('PUT request failed:', error)
      throw error
    }
  },

  async delete(url) {
    try {
      const response = await api.delete(url)
      return response.data
    } catch (error) {
      console.error('DELETE request failed:', error)
      throw error
    }
  }
}

// Frappe login API
export const authAPI = {
  async login(username, password) {
    try {
      const response = await api.post('/method/login', {
        usr: username,
        pwd: password
      })
      return response.data
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  },

  async logout() {
    try {
      const response = await api.post('/method/logout')
      return response.data
    } catch (error) {
      console.error('Logout failed:', error)
      throw error
    }
  },

  async getCurrentUser() {
    try {
      const response = await api.get('/method/frappe.auth.get_logged_user')
      return response.data
    } catch (error) {
      console.error('Get user failed:', error)
      throw error
    }
  }
}

export default api
