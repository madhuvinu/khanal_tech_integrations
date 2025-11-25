/**
 * Production Service Factory
 * Returns the appropriate production service instance based on plant ID
 */

import { nandi_hillsProductionService } from '../plants/nandi_hills/productionService'
import { malurProductionService } from '../plants/malur/productionService'
import { krishnagiriProductionService } from '../plants/krishnagiri/productionService'
import { champavathProductionService } from '../plants/champavath/productionService'
import { mahadevpuraProductionService } from '../plants/mahadevpura/productionService'

// Cache for service instances
const serviceCache = new Map()

/**
 * Get production service for a specific plant
 * @param {string} plantId - Plant identifier (mahadevpura, nandi-hills, nandihills, malur, krishnagiri, champavath)
 * @returns {BaseAPIService} Production service instance
 */
export function getProductionService(plantId) {
  // Normalize plant ID
  const normalizedPlantId = normalizePlantId(plantId)
  
  // Return cached instance if available
  if (serviceCache.has(normalizedPlantId)) {
    return serviceCache.get(normalizedPlantId)
  }
  
  let service
  
  switch (normalizedPlantId) {
    case 'nandi_hills':
    case 'nandihills':
    case 'nandi-hills':
      // Use nandi-hills service (most complete implementation)
      service = nandi_hillsProductionService
      break
      
    case 'malur':
      // Use malur service if available, otherwise fallback to nandi-hills
      service = malurProductionService || nandi_hillsProductionService
      break
      
    case 'krishnagiri':
      // Use krishnagiri service if available, otherwise fallback to nandi-hills
      service = krishnagiriProductionService || nandi_hillsProductionService
      break
      
    case 'champavath':
      // Use champavath service if available, otherwise fallback to nandi-hills
      service = champavathProductionService || nandi_hillsProductionService
      break
      
    case 'mahadevpura':
      // Use mahadevpura service if available, otherwise fallback to nandi-hills
      service = mahadevpuraProductionService || nandi_hillsProductionService
      break
      
    default:
      // For unknown plants, use nandi-hills service as default
      console.info(`[ProductionServiceFactory] Using nandi-hills service for plant: ${normalizedPlantId}`)
      service = nandi_hillsProductionService
      break
  }
  
  // Cache the service instance
  serviceCache.set(normalizedPlantId, service)
  
  return service
}

/**
 * Normalize plant ID to standard format
 * @param {string} plantId - Plant identifier
 * @returns {string} Normalized plant ID
 */
function normalizePlantId(plantId) {
  if (!plantId) return 'nandi_hills'
  
  const normalized = plantId.toLowerCase().trim()
  
  // Handle nandi-hills variations
  if (normalized === 'nandi-hills' || normalized === 'nandihills') {
    return 'nandi_hills'
  }
  
  return normalized
}

export default getProductionService

