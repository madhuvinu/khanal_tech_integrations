import { apiHelpers } from '@/api/index.js'
import { PLANT_ENDPOINTS } from '@/api/constants.js'

const MALLUR_ENDPOINT = PLANT_ENDPOINTS.Mallur.endpoint

export const mallurAPI = {
  /**
   * Get dashboard data for Mallur plant
   * @returns {Promise<Object>} Dashboard data
   */
  async getDashboardData() {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_dashboard_data'
      })
      return response
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      throw error
    }
  },

  /**
   * Get production data for a specific time range
   * @param {string} startDate - Start date in YYYY-MM-DD format
   * @param {string} endDate - End date in YYYY-MM-DD format
   * @returns {Promise<Object>} Production data
   */
  async getProductionData(startDate, endDate) {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_production_data',
        start_date: startDate,
        end_date: endDate
      })
      return response
    } catch (error) {
      console.error('Failed to fetch production data:', error)
      throw error
    }
  },

  /**
   * Get efficiency metrics for all production lines
   * @returns {Promise<Object>} Efficiency data
   */
  async getEfficiencyData() {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_efficiency_data'
      })
      return response
    } catch (error) {
      console.error('Failed to fetch efficiency data:', error)
      throw error
    }
  },

  /**
   * Get production line status
   * @returns {Promise<Object>} Production lines status
   */
  async getProductionLinesStatus() {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_production_lines_status'
      })
      return response
    } catch (error) {
      console.error('Failed to fetch production lines status:', error)
      throw error
    }
  },

  /**
   * Get quality metrics
   * @returns {Promise<Object>} Quality data
   */
  async getQualityMetrics() {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_quality_metrics'
      })
      return response
    } catch (error) {
      console.error('Failed to fetch quality metrics:', error)
      throw error
    }
  },

  /**
   * Get reports data
   * @param {string} reportType - Type of report (daily, weekly, monthly)
   * @param {string} date - Date for the report
   * @returns {Promise<Object>} Report data
   */
  async getReportData(reportType, date) {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_report_data',
        report_type: reportType,
        date: date
      })
      return response
    } catch (error) {
      console.error('Failed to fetch report data:', error)
      throw error
    }
  },

  /**
   * Update production line status
   * @param {string} lineId - Production line ID
   * @param {string} status - New status (active, maintenance, stopped)
   * @returns {Promise<Object>} Update result
   */
  async updateLineStatus(lineId, status) {
    try {
      const response = await apiHelpers.post(MALLUR_ENDPOINT, {
        method: 'update_line_status',
        line_id: lineId,
        status: status
      })
      return response
    } catch (error) {
      console.error('Failed to update line status:', error)
      throw error
    }
  },

  /**
   * Get real-time alerts
   * @returns {Promise<Object>} Alerts data
   */
  async getAlerts() {
    try {
      const response = await apiHelpers.get(MALLUR_ENDPOINT, {
        method: 'get_alerts'
      })
      return response
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      throw error
    }
  }
}

export default mallurAPI
