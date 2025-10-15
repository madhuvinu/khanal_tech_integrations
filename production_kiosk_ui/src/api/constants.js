// Base URL and plant endpoints - dynamically determined from current location
// Uses environment variable if available, otherwise falls back to window.location.origin
export const BASE_URL = import.meta.env.VITE_BASE_URL || window.location.origin
export const API_BASE = `${BASE_URL}/api`

export const PLANT_ENDPOINTS = {
  NandhiHills: {
    name: 'Nandhi Hills',
    endpoint: '/method/khanal_tech_integrations.api.nandhi_hills',
    color: '#4F46E5',
    logo: '/assets/khanal_tech_integrations/images/nandhi-hills-logo.png'
  },
  Dogsee: {
    name: 'Dogsee',
    endpoint: '/method/khanal_tech_integrations.api.dogsee',
    color: '#059669',
    logo: '/assets/khanal_tech_integrations/images/dogsee-logo.png'
  },
  Mallur: {
    name: 'Mallur',
    endpoint: '/method/khanal_tech_integrations.api.mallur',
    color: '#DC2626',
    logo: '/assets/khanal_tech_integrations/images/mallur-logo.png'
  },
  Champawath: {
    name: 'Champawath',
    endpoint: '/method/khanal_tech_integrations.api.champawath',
    color: '#7C3AED',
    logo: '/assets/khanal_tech_integrations/images/champawath-logo.png'
  },
  Krishnagiri: {
    name: 'Krishnagiri',
    endpoint: '/method/khanal_tech_integrations.api.krishnagiri',
    color: '#EA580C',
    logo: '/assets/khanal_tech_integrations/images/krishnagiri-logo.png'
  }
}

export const API_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
