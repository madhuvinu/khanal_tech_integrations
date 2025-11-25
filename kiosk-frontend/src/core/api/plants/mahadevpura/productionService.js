/**
 * Mahadevpura Plant Production Service
 * Plant-specific Production operations for Mahadevpura
 */

import { BaseAPIService } from '../../common/baseService'

export class MahadevpuraProductionService extends BaseAPIService {
  constructor() {
    super('MahadevpuraProductionService')
    this.plantId = 'mahadevpura'
  }

  /**
   * Search BOM by Name or Code (Header Level - OITT)
   * @param {string} searchQuery - Search term (minimum 2 characters)
   * @returns {Promise<Object>}
   */
  async searchBOM(searchQuery) {
    this.logAPICall('searchBOM', { searchQuery })
    
    if (!searchQuery || searchQuery.length < 2) {
      return {
        success: false,
        message: 'Search query must be at least 2 characters',
        data: []
      }
    }
    
    return await this.postPlantAPI(this.plantId, 'production', 'search_bom', {
      search_query: searchQuery,
      plant_id: this.plantId
    })
  }

  /**
   * Get ITT1 components for a BOM
   * @param {string} bomCode - BOM code from OITT
   * @returns {Promise<Object>}
   */
  async getITT1Components(bomCode) {
    this.logAPICall('getITT1Components', { bomCode })
    this.validateParams({ bomCode }, ['bomCode'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_itt1_components', {
      bom_code: bomCode,
      plant_id: this.plantId
    })
  }

  /**
   * Get OITT header for a BOM
   * @param {string} bomCode - BOM code
   * @returns {Promise<Object>}
   */
  async getOITTHeader(bomCode) {
    this.logAPICall('getOITTHeader', { bomCode })
    this.validateParams({ bomCode }, ['bomCode'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_oitt_header', {
      bom_code: bomCode,
      plant_id: this.plantId
    })
  }

  /**
   * Get batch numbers for an item
   * @param {string} itemCode - Item code
   * @param {string} warehouse - Warehouse code (optional)
   * @param {string} dateFrom - From date (optional)
   * @param {string} dateTo - To date (optional)
   * @returns {Promise<Object>}
   */
  async getBatchNumbers(itemCode, warehouse = null, dateFrom = null, dateTo = null) {
    this.logAPICall('getBatchNumbers', { itemCode, warehouse, dateFrom, dateTo })
    this.validateParams({ itemCode }, ['itemCode'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_batch_numbers', {
      item_code: itemCode,
      warehouse: warehouse,
      date_from: dateFrom,
      date_to: dateTo,
      plant_id: this.plantId
    })
  }

  /**
   * Get batch numbers from Batch Date Item doctype
   * @param {string} itemCode - Item code
   * @param {string} dateFrom - Optional from date in YYYY-MM-DD format. If not provided, returns latest
   * @param {string} dateTo - Optional to date in YYYY-MM-DD format. Defaults to current date if dateFrom is provided
   * @returns {Promise<Object>}
   */
  async getBatchNumbersFromBatchDateItem(itemCode, dateFrom = null, dateTo = null) {
    this.logAPICall('getBatchNumbersFromBatchDateItem', { itemCode, dateFrom, dateTo })
    this.validateParams({ itemCode }, ['itemCode'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_batch_numbers_from_batch_date_item', {
      item_code: itemCode,
      date_from: dateFrom,
      date_to: dateTo,
      plant_id: this.plantId
    })
  }

  /**
   * Get warehouses from SAP OWHS table filtered by plant warehouse prefix
   * @returns {Promise<Object>}
   */
  async getWarehouses() {
    this.logAPICall('getWarehouses', {})
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_warehouses', {
      plant_id: this.plantId
    })
  }

  /**
   * Approve production order (create and release)
   * @param {Object} productionData - Production order data
   * @returns {Promise<Object>}
   */
  async approveProductionOrder(productionData) {
    this.logAPICall('approveProductionOrder', { productionData })
    this.validateParams({ productionData }, ['productionData'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'approve_production_order', {
      production_data: productionData,
      plant_id: this.plantId
    })
  }

  /**
   * Create goods issue (Inventory Gen Exit)
   * @param {number} productionOrderDocEntry - Production order DocEntry
   * @param {Object} productionData - Production data with inputs
   * @returns {Promise<Object>}
   */
  async goodsIssue(productionOrderDocEntry, productionData) {
    this.logAPICall('goodsIssue', { productionOrderDocEntry, productionData })
    this.validateParams({ productionOrderDocEntry, productionData }, ['productionOrderDocEntry', 'productionData'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'goods_issue', {
      production_order_doc_entry: productionOrderDocEntry,
      production_data: productionData,
      plant_id: this.plantId
    })
  }

  /**
   * Create goods receipt (Inventory Gen Entry)
   * @param {number} productionOrderDocEntry - Production order DocEntry
   * @param {Object} productionData - Production data with outputs and byproducts
   * @returns {Promise<Object>}
   */
  async goodsReceipt(productionOrderDocEntry, productionData) {
    this.logAPICall('goodsReceipt', { productionOrderDocEntry, productionData })
    this.validateParams({ productionOrderDocEntry, productionData }, ['productionOrderDocEntry', 'productionData'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'goods_receipt', {
      production_order_doc_entry: productionOrderDocEntry,
      production_data: productionData,
      plant_id: this.plantId
    })
  }

  /**
   * Close production order
   * @param {number} productionOrderDocEntry - Production order DocEntry
   * @param {string} closeDate - Close date in YYYY-MM-DD format (optional)
   * @returns {Promise<Object>}
   */
  async closeProduction(productionOrderDocEntry, closeDate = null) {
    this.logAPICall('closeProduction', { productionOrderDocEntry, closeDate })
    this.validateParams({ productionOrderDocEntry }, ['productionOrderDocEntry'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'close_production', {
      production_order_doc_entry: productionOrderDocEntry,
      close_date: closeDate,
      plant_id: this.plantId
    })
  }

  /**
   * Get list of production orders from Production Kiosk
   * @param {Object} filters - Filter criteria (optional)
   * @param {number} page - Page number (default: 1)
   * @param {number} pageSize - Records per page (default: 20)
   * @returns {Promise<Object>}
   */
  async getProductionOrdersList(filters = {}, page = 1, pageSize = 20) {
    this.logAPICall('getProductionOrdersList', { filters, page, pageSize })
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_production_orders_list', {
      filters: JSON.stringify(filters),
      page: page,
      page_size: pageSize,
      plant_id: this.plantId
    })
  }

  /**
   * Get production order details for resuming workflow
   * @param {string} productionKioskName - Production Kiosk document name (e.g., PID-0005)
   * @returns {Promise<Object>}
   */
  async getProductionOrderForResume(productionKioskName) {
    this.logAPICall('getProductionOrderForResume', { productionKioskName })
    this.validateParams({ productionKioskName }, ['productionKioskName'])
    
    return await this.postPlantAPI(this.plantId, 'production', 'get_production_order_for_resume', {
      production_kiosk_name: productionKioskName,
      plant_id: this.plantId
    })
  }
}

// Export singleton instance
export const mahadevpuraProductionService = new MahadevpuraProductionService()

export default mahadevpuraProductionService


