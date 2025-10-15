// Utility helper functions for the production kiosk UI

/**
 * Format a number with commas for better readability
 * @param {number} num - The number to format
 * @returns {string} - Formatted number string
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * Format a date to a readable string
 * @param {string|Date} date - The date to format
 * @param {string} format - The format type ('short', 'long', 'time')
 * @returns {string} - Formatted date string
 */
export function formatDate(date, format = 'short') {
  if (!date) return 'N/A'
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return 'Invalid Date'
  
  const options = {
    short: { year: 'numeric', month: 'short', day: 'numeric' },
    long: { year: 'numeric', month: 'long', day: 'numeric' },
    time: { hour: '2-digit', minute: '2-digit' }
  }
  
  return d.toLocaleDateString('en-US', options[format] || options.short)
}

/**
 * Format a percentage value
 * @param {number} value - The value to format as percentage
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted percentage string
 */
export function formatPercentage(value, decimals = 1) {
  if (value === null || value === undefined) return '0%'
  return `${Number(value).toFixed(decimals)}%`
}

/**
 * Get a random color for charts
 * @param {number} index - Index for consistent color selection
 * @returns {string} - Hex color code
 */
export function getChartColor(index = 0) {
  const colors = [
    '#4F46E5', '#059669', '#DC2626', '#7C3AED', '#EA580C',
    '#06B6D4', '#84CC16', '#F59E0B', '#EF4444', '#8B5CF6'
  ]
  return colors[index % colors.length]
}

/**
 * Calculate percentage change between two values
 * @param {number} oldValue - Previous value
 * @param {number} newValue - Current value
 * @returns {object} - Object with percentage and direction
 */
export function calculatePercentageChange(oldValue, newValue) {
  if (!oldValue || oldValue === 0) return { percentage: 0, direction: 'neutral' }
  
  const change = ((newValue - oldValue) / oldValue) * 100
  const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral'
  
  return {
    percentage: Math.abs(change),
    direction
  }
}

/**
 * Debounce function to limit API calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Generate a unique ID
 * @returns {string} - Unique identifier
 */
export function generateId() {
  return Math.random().toString(36).substr(2, 9)
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid email
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Get plant display name from plant key
 * @param {string} plantKey - Plant identifier key
 * @returns {string} - Display name for the plant
 */
export function getPlantDisplayName(plantKey) {
  const plantNames = {
    'NandhiHills': 'Nandhi Hills',
    'Dogsee': 'Dogsee',
    'Mallur': 'Mallur',
    'Champawath': 'Champawath',
    'Krishnagiri': 'Krishnagiri'
  }
  return plantNames[plantKey] || plantKey
}

/**
 * Get plant color scheme
 * @param {string} plantKey - Plant identifier key
 * @returns {object} - Color scheme object
 */
export function getPlantColorScheme(plantKey) {
  const colorSchemes = {
    'NandhiHills': { primary: '#4F46E5', light: '#818cf8', dark: '#3730a3' },
    'Dogsee': { primary: '#059669', light: '#10b981', dark: '#047857' },
    'Mallur': { primary: '#DC2626', light: '#ef4444', dark: '#b91c1c' },
    'Champawath': { primary: '#7C3AED', light: '#a855f7', dark: '#6d28d9' },
    'Krishnagiri': { primary: '#EA580C', light: '#f97316', dark: '#c2410c' }
  }
  return colorSchemes[plantKey] || { primary: '#6B7280', light: '#9CA3AF', dark: '#374151' }
}

/**
 * Format time duration in human readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} - Formatted duration string
 */
export function formatDuration(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h`
  return `${Math.round(seconds / 86400)}d`
}

/**
 * Check if a value is empty (null, undefined, empty string, empty array)
 * @param {any} value - Value to check
 * @returns {boolean} - True if value is empty
 */
export function isEmpty(value) {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * Deep clone an object
 * @param {any} obj - Object to clone
 * @returns {any} - Cloned object
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (typeof obj === 'object') {
    const clonedObj = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
  return obj
}
