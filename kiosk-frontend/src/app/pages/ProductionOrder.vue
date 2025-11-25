<template>
  <div class="flex relative">
    <!-- Sidebar for Production Orders -->
    <div 
      :class="[
        'fixed left-0 top-0 h-full bg-white shadow-xl z-40 transition-transform duration-300 ease-in-out overflow-y-auto',
        showSidebar ? 'translate-x-0' : '-translate-x-full',
        'w-96'
      ]"
    >
      <div class="p-4 border-b bg-blue-600 text-white">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold">📋 Production Orders</h2>
          <button @click="toggleSidebar" class="text-white hover:text-gray-200">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Date Range Filter -->
      <div class="p-4 border-b bg-gray-50">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Filter by Date Range</h3>
        <div class="space-y-2">
          <div>
            <label class="block text-xs text-gray-600 mb-1">From Date</label>
            <input
              v-model="dateFilterFrom"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-blue-600 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-600 mb-1">To Date</label>
            <input
              v-model="dateFilterTo"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-blue-600 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="flex gap-2">
            <button
              @click="applyDateFilter"
              class="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
            >
              Apply Filter
            </button>
            <button
              @click="clearDateFilter"
              class="flex-1 px-3 py-2 bg-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-400 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </div>
      
      <div class="p-4">
        <!-- Loading State -->
        <div v-if="loadingOrders" class="text-center py-8">
          <p class="text-gray-600">Loading production orders...</p>
        </div>
        
        <!-- Production Orders List -->
        <div v-else-if="productionOrders.length > 0" class="space-y-3">
          <div 
            v-for="order in productionOrders" 
            :key="order.name"
            class="border rounded-lg p-3 hover:bg-blue-50 transition-colors cursor-pointer"
            :class="{
              'border-green-300 bg-green-50': order.production_order_status === 'boposReleased',
              'border-red-300 bg-red-50': order.production_order_status === 'boposClosed',
              'border-yellow-300 bg-yellow-50': order.production_order_status && order.production_order_status !== 'boposReleased' && order.production_order_status !== 'boposClosed',
              'border-gray-300': !order.production_order_status
            }"
            @click="viewProductionOrder(order)"
            :title="order.sap_absoluteentry ? 'Click to resume this production order' : 'Click to view details'"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <span class="font-semibold text-blue-700">{{ order.name }}</span>
                  <span 
                    v-if="order.production_order_status"
                    class="text-xs px-2 py-1 rounded"
                    :class="{
                      'bg-green-200 text-green-800': order.production_order_status === 'boposReleased',
                      'bg-red-200 text-red-800': order.production_order_status === 'boposClosed',
                      'bg-yellow-200 text-yellow-800': order.production_order_status && order.production_order_status !== 'boposReleased' && order.production_order_status !== 'boposClosed',
                      'bg-gray-200 text-gray-800': !order.production_order_status
                    }"
                  >
                    {{ order.production_order_status }}
                  </span>
                </div>
                <div class="text-sm text-gray-600 space-y-1">
                  <p class="text-xs font-semibold text-blue-600 mb-1">
                    📅 {{ formatDate(order.display_date || order.posting_date || order.created_date || 'N/A') }}
                  </p>
                  <p v-if="order.sap_absoluteentry">
                    <span class="font-medium">SAP Entry:</span> {{ order.sap_absoluteentry }}
                  </p>
                  <p v-if="order.sap_production_number">
                    <span class="font-medium">DocNum:</span> {{ order.sap_production_number }}
                  </p>
                  <p v-if="order.user_name">
                    <span class="font-medium">User:</span> {{ order.user_name }}
                  </p>
                </div>
              </div>
              <button 
                @click.stop="viewProductionOrder(order)"
                class="ml-2 px-3 py-1 rounded hover:opacity-90 text-sm font-medium"
                :class="order.sap_absoluteentry ? 'bg-green-600 text-white' : 'bg-blue-600 text-white'"
                :title="order.sap_absoluteentry ? 'Resume this production order' : 'View details'"
              >
                {{ order.sap_absoluteentry ? 'Resume' : 'View' }}
              </button>
            </div>
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-else class="text-center py-8 text-gray-600">
          <p>No production orders found</p>
        </div>
        
        <!-- Pagination -->
        <div v-if="ordersPagination.total_pages > 1" class="mt-4 flex items-center justify-between">
          <button 
            @click="loadOrdersPage(ordersPagination.page - 1)"
            :disabled="ordersPagination.page <= 1"
            class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span class="text-sm text-gray-600">
            Page {{ ordersPagination.page }} of {{ ordersPagination.total_pages }}
          </span>
          <button 
            @click="loadOrdersPage(ordersPagination.page + 1)"
            :disabled="ordersPagination.page >= ordersPagination.total_pages"
            class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
    
    <!-- Overlay when sidebar is open -->
    <div 
      v-if="showSidebar"
      @click="toggleSidebar"
      class="fixed inset-0 bg-black bg-opacity-50 z-30"
    ></div>
    
    <!-- Main Content -->
    <div class="flex-1 p-6" :class="{ 'ml-0': !showSidebar }">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Production Order – {{ plantName }}</h1>
          <p class="text-gray-600">Production Kiosk | Goods Issue & Receipt</p>
        </div>
          <div class="flex gap-2">
            <button @click="toggleSidebar" class="px-4 py-2 bg-blue-600 text-red-600 rounded-lg hover:bg-blue-700">
              📋 View Orders ({{ productionOrders.length }})
            </button>
        <button @click="goToBatchGenerator" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
          Batch Number Generator
        </button>
          </div>
      </div>
    </div>

    <!-- Process Type (Required) -->
    <div class="bg-white rounded-lg shadow-md p-4 mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Process Type <span class="text-red-500">*</span>
      </label>
      <select 
        v-model="productionType" 
        required
        class="w-full px-4 py-2 border-2 border-blue-500 rounded-lg text-gray-900 font-semibold bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">Select Process Type...</option>
        <option value="Standard">Standard</option>
        <option value="Special">Special</option>
        <option value="Disassembly">Disassembly</option>
      </select>
    </div>

    <!-- Top Bar with Search and Refresh -->
    <div class="bg-blue-50 rounded-lg border-2 border-blue-500 p-4 mb-6">
      <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div class="flex-1 w-full relative">
          <div class="relative">
            <input
              v-model="bomSearchQuery"
              @input="onBOMSearchInput"
              @keyup.enter="searchBOMTables"
              @focus="showBOMResults = bomResults.length > 0"
              type="text"
              placeholder="Search BOM by Item Name (OITT/ITT1) - Type at least 2 characters..."
              class="w-full px-4 py-3 pl-12 border-2 border-blue-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-600 bg-white text-gray-900"
            />
            <svg class="absolute left-3 top-3.5 h-6 w-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          
          <!-- BOM Search Results Dropdown -->
          <div v-if="showBOMResults && bomResults.length > 0" class="absolute z-50 w-full mt-1 bg-white border-2 border-blue-400 rounded-lg shadow-lg max-h-96 overflow-y-auto">
            <div class="px-3 py-2 bg-blue-100 border-b border-blue-300">
              <p class="text-xs font-semibold text-blue-700">Found {{ bomResults.length }} BOM record(s)</p>
            </div>
            <div 
              v-for="(bom, idx) in bomResults" 
              :key="idx"
              @mousedown.prevent="selectBOM(bom)"
              class="p-4 hover:bg-blue-50 cursor-pointer border-b border-gray-200 transition-colors"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <p class="font-bold text-blue-700 text-base">{{ bom.Name }}</p>
                  <div class="flex gap-3 mt-2">
                    <p class="text-sm text-gray-600">📋 Code: <span class="font-semibold">{{ bom.Code }}</span></p>
                    <p class="text-sm text-gray-600">📦 Type: <span class="font-semibold">{{ bom.TreeType }}</span></p>
                    <p class="text-sm text-gray-600">🏭 WH: <span class="font-semibold">{{ bom.ToWH }}</span></p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="flex gap-2">
          <button
            @click="testPushNotification"
            :disabled="testingPush"
            class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ testingPush ? 'Testing...' : '🔔 Test Push' }}
          </button>
          <button
            @click="refreshData"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Refresh
          </button>
        </div>
      </div>
      <p class="text-sm text-blue-600 mt-2">
        💡 Search BOM components from OITT (Bill of Materials Header) and ITT1 (Bill of Materials Components) tables
      </p>
    </div>

    <!-- Selected BOM Display - Simplified -->
    <div v-if="selectedBOM" class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-400 p-4 mb-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-bold text-blue-700">{{ selectedBOM.ItemName || selectedBOM.Name }}</h3>
        <button
          @click="clearBOMSelection"
          class="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm"
        >
          Clear
        </button>
      </div>
    </div>


    <!-- BOM Components (ITT1) - Inputs -->
    <div v-if="selectedBOM" class="bg-white rounded-lg shadow-md overflow-hidden mb-6">
      <button
        @click="toggleSection('itt1')"
        class="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50"
      >
        <h2 class="text-xl font-semibold text-blue-700">🧩 Inputs</h2>
        <svg
          :class="{ 'rotate-180': !sections.itt1 }"
          class="h-5 w-5 text-gray-500 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div v-if="sections.itt1" class="px-6 pb-6">
        <div v-if="itt1Components.length > 0" class="space-y-4">
          <div v-for="(comp, idx) in itt1Components" :key="idx" class="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <h3 class="font-semibold text-lg text-blue-700 mb-3">{{ comp.ItemName }}</h3>
            <div class="grid grid-cols-2 md:grid-cols-6 gap-3">
              <div>
                <label class="block text-xs font-medium text-blue-700">Component Code</label>
                <input :value="comp.Code" readonly class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg bg-blue-50 text-blue-700 font-medium" />
              </div>
              <div>
                <label class="block text-xs font-medium text-blue-700">BOM Qty</label>
                <input :value="comp.Quantity !== undefined && comp.Quantity !== null ? comp.Quantity : '-'" readonly class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg bg-blue-50 text-blue-700 font-medium" />
              </div>
              <div>
                <label class="block text-xs font-medium text-blue-700">Base Qty Clear</label>
                <input :value="calculateBaseQtyClear(comp)" readonly class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg bg-blue-50 text-blue-700 font-medium" />
              </div>
              <div>
                <label class="block text-xs font-medium text-blue-700">Input Quantity *</label>
                <input v-model.number="comp.inputQuantity" @input="updateInputQuantity(comp, $event)" type="number" placeholder="" class="w-full px-3 py-2 border-2 border-blue-500 rounded-lg text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-xs font-medium text-blue-700">Batch Number</label>
                <input 
                  v-model="comp.batchNumber" 
                  type="text" 
                  placeholder="Enter batch" 
                  readonly
                  @click="openBatchModal(comp)"
                  class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer bg-blue-50 text-blue-700 font-medium"
                  :class="comp.batchNumber ? 'text-blue-700 font-semibold' : 'text-gray-500'"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-blue-700">Warehouse</label>
                <select v-model="comp.warehouse" class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg text-blue-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="" class="text-gray-600">Select...</option>
                  <option v-for="wh in filteredWarehouses" :key="wh" :value="wh" class="text-blue-700">{{ wh }}</option>
                </select>
              </div>
            </div>
            
            <!-- Batch Allocations Display -->
            <div v-if="comp.selectedBatches && comp.selectedBatches.length > 0" class="mt-4">
              <h4 class="text-sm font-semibold text-blue-700 mb-2">📊 Batch Allocations</h4>
              <div class="bg-white border-2 border-blue-200 rounded-lg overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-blue-50">
                    <tr>
                      <th class="px-3 py-2 text-left text-xs font-medium text-blue-700 uppercase">Batch Number</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-blue-700 uppercase">Warehouse</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-blue-700 uppercase">Available Qty</th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-blue-700 uppercase">Qty Used</th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-blue-700 uppercase">Action</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="(batch, batchIdx) in comp.selectedBatches" :key="batchIdx">
                      <td class="px-3 py-2 text-sm font-medium text-blue-600">{{ batch.BatchNumber }}</td>
                      <td class="px-3 py-2 text-sm text-gray-600">{{ batch.Warehouse }}</td>
                      <td class="px-3 py-2 text-sm text-gray-600">{{ batch.AvailableQty }}</td>
                      <td class="px-3 py-2 text-sm">
                        <input 
                          v-model.number="batch.inputQuantity" 
                          type="number" 
                          @input="updateComponentTotal(comp)"
                          class="w-full px-2 py-1 border border-blue-300 rounded text-blue-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                          :max="batch.AvailableQty"
                        />
                      </td>
                      <td class="px-3 py-2 text-center">
                        <button 
                          @click="removeBatchFromComponent(comp, batchIdx)"
                          class="text-red-600 hover:text-red-800"
                        >
                          ❌
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <div class="mt-3 grid grid-cols-3 gap-3 text-sm">
              <div class="bg-white p-2 rounded">
                <span class="text-gray-600">Base Qty:</span> <span class="font-semibold">{{ comp.U_BaseQty || '-' }}</span>
              </div>
              <div class="bg-white p-2 rounded">
                <span class="text-gray-600">Scrap:</span> <span class="font-semibold">{{ comp.U_Scrap || '-' }}%</span>
              </div>
              <div class="bg-white p-2 rounded">
                <span class="text-gray-600">Mat Type:</span> <span class="font-semibold">{{ comp.U_MatType || '-' }}</span>
              </div>
          </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Output Goods Section -->
    <div v-if="selectedBOM" class="bg-white rounded-lg shadow-md overflow-hidden mb-6">
      <button
        @click="toggleSection('output')"
        class="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50"
      >
        <h2 class="text-xl font-semibold text-blue-700">📦 Output</h2>
        <svg
          :class="{ 'rotate-180': !sections.output }"
          class="h-5 w-5 text-gray-500 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div v-if="sections.output" class="px-6 pb-6">
        <div class="border-2 border-blue-200 rounded-lg p-6 bg-blue-50">
          <h3 class="font-bold text-xl text-blue-700 mb-4">{{ selectedBOM.Name }}</h3>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div class="bg-white rounded p-3">
              <label class="block text-xs font-medium text-blue-700 mb-1">Code</label>
              <p class="text-blue-700 font-semibold">{{ selectedBOM.Code }}</p>
            </div>
            <div class="bg-white rounded p-3">
              <label class="block text-xs font-medium text-blue-700 mb-1">Tree Type</label>
              <p class="text-blue-700 font-semibold">{{ selectedBOM.TreeType }}</p>
            </div>
            <div class="bg-white rounded p-3">
              <label class="block text-xs font-medium text-blue-700 mb-1">BOM Qty</label>
              <input :value="selectedBOM.Quantity !== undefined && selectedBOM.Quantity !== null ? selectedBOM.Quantity : (oittHeader?.Quantity !== undefined && oittHeader?.Quantity !== null ? oittHeader.Quantity : '-')" readonly class="w-full px-3 py-2 border border-blue-300 rounded-lg bg-blue-50 text-blue-700 font-medium" />
            </div>
            <div class="bg-white rounded p-3">
              <label class="block text-xs font-medium text-blue-700 mb-1">Output Quantity *</label>
              <input v-model.number="outputQuantity" type="number" placeholder="" class="w-full px-3 py-2 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-blue-700" />
            </div>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-xs font-medium text-blue-700 mb-2">Date</label>
              <input v-model="outputBatchDate" type="date" class="w-full px-3 py-2 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-blue-700" />
            </div>
            <div>
              <label class="block text-xs font-medium text-blue-700 mb-2">Batch Number</label>
              <div class="flex gap-2">
                <input v-model="outputBatchNumber" type="text" placeholder="Enter batch number" readonly class="flex-1 px-3 py-2 border border-blue-300 rounded-lg bg-blue-50 cursor-pointer text-blue-700" @click="openOutputBatchLookup" />
                <button @click="openOutputBatchLookup" class="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  🔍
                </button>
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-blue-700 mb-2">Warehouse</label>
              <select v-model="outputWarehouse" class="w-full px-3 py-2 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-blue-700">
                <option value="">Select warehouse...</option>
                <option v-for="wh in filteredWarehouses" :key="wh" :value="wh" class="text-blue-700">{{ wh }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Byproducts Section (Negative quantity items) -->
        <div v-if="byProducts.length > 0" class="mt-6">
          <h4 class="text-lg font-bold text-blue-700 mb-4">🔄 Byproducts</h4>
          <div class="space-y-4">
            <div v-for="(product, idx) in byProducts" :key="idx" class="border-2 border-blue-200 rounded-lg p-4 bg-blue-50">
              <h5 class="font-bold text-lg text-blue-700 mb-3">{{ product.ItemName }}</h5>
              
              <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3">
                <div>
                  <label class="block text-xs font-medium text-blue-700 mb-1">Component Code</label>
                  <input :value="product.Code" readonly class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg bg-blue-50 text-blue-700 font-medium" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-blue-700 mb-1">Output Quantity *</label>
                  <input v-model.number="product.outputQuantity" type="number" placeholder="" class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-blue-700 mb-1">Date</label>
                  <input v-model="product.batchDate" type="date" class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-blue-700 mb-1">Batch Number</label>
                  <div class="flex gap-2">
                    <input v-model="product.outputBatchNumber" type="text" placeholder="Enter batch" readonly class="flex-1 px-3 py-2 border-2 border-blue-300 rounded-lg bg-blue-50 text-blue-700 cursor-pointer" @click="openByproductBatchLookup(product)" />
                    <button @click="openByproductBatchLookup(product)" class="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                      🔍
                    </button>
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-blue-700 mb-1">Warehouse</label>
                  <select v-model="product.outputWarehouse" class="w-full px-3 py-2 border-2 border-blue-300 rounded-lg text-blue-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="" class="text-gray-600">Select...</option>
                    <option v-for="wh in filteredWarehouses" :key="wh" :value="wh" class="text-blue-700">{{ wh }}</option>
                  </select>
                </div>
              </div>
              
              <div class="grid grid-cols-3 gap-3 text-sm">
                <div class="bg-white p-2 rounded">
                  <span class="text-gray-600">Base Qty:</span> <span class="font-semibold">{{ product.U_BaseQty || '-' }}</span>
                </div>
                <div class="bg-white p-2 rounded">
                  <span class="text-gray-600">Scrap:</span> <span class="font-semibold">{{ product.U_Scrap || '-' }}%</span>
                </div>
                <div class="bg-white p-2 rounded">
                  <span class="text-gray-600">Mat Type:</span> <span class="font-semibold">{{ product.U_MatType || '-' }}</span>
                </div>
              </div>
            </div>
      </div>
        </div>
      </div>
    </div>

    <!-- Workflow Timeline -->
    <div v-if="workflowData.productionOrderDocEntry" class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 mb-6 border-2 border-blue-300">
      <h2 class="text-xl font-semibold text-blue-900 mb-4">📋 Production Order Timeline</h2>
      <div class="space-y-4">
        <!-- Production Order Created -->
        <div class="flex items-start gap-4 bg-white rounded-lg p-4 border-2 border-green-300">
          <div class="flex-shrink-0 w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">
            ✓
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-green-700">Production Order Created & Released</h3>
            <p class="text-sm text-gray-600 mt-1">
              <span class="font-medium">DocEntry:</span> {{ workflowData.productionOrderDocEntry }} | 
              <span class="font-medium">DocNum:</span> {{ workflowData.productionOrderDocNum }} | 
              <span class="font-medium">Status:</span> {{ workflowData.productionOrderStatus || 'boposReleased' }}
            </p>
          </div>
        </div>
        
        <!-- Goods Issue -->
        <div v-if="workflowData.goodsIssueDocEntry" class="flex items-start gap-4 bg-white rounded-lg p-4 border-2 border-blue-300">
          <div class="flex-shrink-0 w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
            ✓
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-blue-700">Goods Issue Completed</h3>
            <p class="text-sm text-gray-600 mt-1">
              <span class="font-medium">DocEntry:</span> {{ workflowData.goodsIssueDocEntry }} | 
              <span class="font-medium">DocNum:</span> {{ workflowData.goodsIssueDocNum }}
            </p>
          </div>
        </div>
        <div v-else class="flex items-start gap-4 bg-gray-100 rounded-lg p-4 border-2 border-gray-300 opacity-60">
          <div class="flex-shrink-0 w-10 h-10 bg-gray-400 rounded-full flex items-center justify-center text-white font-bold">
            ○
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-gray-600">Goods Issue Pending</h3>
            <p class="text-sm text-gray-500 mt-1">Waiting for goods issue...</p>
          </div>
        </div>
        
        <!-- Goods Receipt -->
        <div v-if="workflowData.goodsReceiptDocEntry" class="flex items-start gap-4 bg-white rounded-lg p-4 border-2 border-purple-300">
          <div class="flex-shrink-0 w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold">
            ✓
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-purple-700">Goods Receipt Completed</h3>
            <p class="text-sm text-gray-600 mt-1">
              <span class="font-medium">DocEntry:</span> {{ workflowData.goodsReceiptDocEntry }} | 
              <span class="font-medium">DocNum:</span> {{ workflowData.goodsReceiptDocNum }}
            </p>
          </div>
        </div>
        <div v-else class="flex items-start gap-4 bg-gray-100 rounded-lg p-4 border-2 border-gray-300 opacity-60">
          <div class="flex-shrink-0 w-10 h-10 bg-gray-400 rounded-full flex items-center justify-center text-white font-bold">
            ○
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-gray-600">Goods Receipt Pending</h3>
            <p class="text-sm text-gray-500 mt-1">Waiting for goods receipt...</p>
          </div>
        </div>
        
        <!-- Production Closed -->
        <div v-if="workflowData.closeDate || workflowData.productionOrderStatus === 'boposClosed'" class="flex items-start gap-4 bg-white rounded-lg p-4 border-2 border-red-300">
          <div class="flex-shrink-0 w-10 h-10 bg-red-500 rounded-full flex items-center justify-center text-white font-bold">
            ✓
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-red-700">Production Closed</h3>
            <p class="text-sm text-gray-600 mt-1">
              <span v-if="workflowData.closeDate" class="font-medium">Close Date:</span> {{ workflowData.closeDate }}<span v-if="workflowData.closeDate && workflowData.productionOrderStatus"> | </span>
              <span class="font-medium">Status:</span> {{ workflowData.productionOrderStatus || 'boposClosed' }}
            </p>
          </div>
        </div>
        <div v-else class="flex items-start gap-4 bg-gray-100 rounded-lg p-4 border-2 border-gray-300 opacity-60">
          <div class="flex-shrink-0 w-10 h-10 bg-gray-400 rounded-full flex items-center justify-center text-white font-bold">
            ○
          </div>
          <div class="flex-1">
            <h3 class="font-semibold text-gray-600">Production Open</h3>
            <p class="text-sm text-gray-500 mt-1">Production order is still open</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">⚡ Production Actions</h2>
      <div class="flex flex-wrap gap-4">
        <!-- Computed property to check if production is fully completed/closed -->
        <button
          @click="submitApproval"
          :disabled="isProductionClosed || workflowState >= 1 || workflowLoading.approve || workflowData.productionOrderDocEntry"
          class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
        >
          <span v-if="workflowLoading.approve" class="animate-spin">⏳</span>
          <span v-else>✓</span>
          <span>{{ workflowLoading.approve ? 'Processing...' : 'Approve' }}</span>
        </button>
        <button
          @click="submitGoodsIssue"
          :disabled="isProductionClosed || workflowState < 1 || workflowLoading.goodsIssue || workflowData.goodsIssueDocEntry"
          class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
        >
          <span v-if="workflowLoading.goodsIssue" class="animate-spin">⏳</span>
          <span v-else>📤</span>
          <span>{{ workflowLoading.goodsIssue ? 'Processing...' : 'Goods Issue' }}</span>
        </button>
        <button
          @click="submitGoodsReceipt"
          :disabled="isProductionClosed || workflowState < 2 || workflowLoading.goodsReceipt || !workflowData.goodsIssueDocEntry || workflowData.goodsReceiptDocEntry"
          class="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
        >
          <span v-if="workflowLoading.goodsReceipt" class="animate-spin">⏳</span>
          <span v-else>📥</span>
          <span>{{ workflowLoading.goodsReceipt ? 'Processing...' : 'Goods Receipt' }}</span>
        </button>
        <button
          @click="closeProduction"
          :disabled="isProductionClosed || workflowState < 3 || workflowLoading.close || !workflowData.goodsReceiptDocEntry || workflowData.closeDate"
          class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
        >
          <span v-if="workflowLoading.close" class="animate-spin">⏳</span>
          <span v-else>✕</span>
          <span>{{ workflowLoading.close ? 'Processing...' : 'Close Production' }}</span>
        </button>
      </div>
      <p class="text-sm text-gray-500 mt-3">
        Current Workflow State: <span class="font-semibold">{{ ['Initial', 'Approved', 'Goods Issued', 'Goods Received'][workflowState] }}</span>
      </p>
    </div>
    </div>

    <!-- Batch Date Item Lookup Modal -->
    <div v-if="showBatchDateItemModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" @click.self="closeBatchDateItemModal">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden" @click.stop>
        <!-- Modal Header -->
        <div class="bg-indigo-600 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-xl font-bold">Batch Number Lookup - {{ currentBatchLookupItem?.Code || currentBatchLookupItem?.item_code }}</h3>
          <button @click="closeBatchDateItemModal" class="text-white hover:text-gray-200">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6">
          <!-- Date Range Selection -->
          <div class="mb-4 grid grid-cols-3 gap-2">
            <div>
              <label class="block text-sm font-medium text-blue-700 mb-2">From Date</label>
              <input v-model="batchDateItemLookupDateFrom" type="date" class="w-full px-3 py-2 border-2 border-indigo-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-blue-700" />
            </div>
            <div>
              <label class="block text-sm font-medium text-blue-700 mb-2">To Date (Current Date)</label>
              <input v-model="batchDateItemLookupDateTo" type="date" class="w-full px-3 py-2 border-2 border-indigo-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-blue-700" />
            </div>
            <div class="flex items-end">
              <button @click="searchBatchDateItems" class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
                🔍 Search
              </button>
            </div>
          </div>
          <p class="text-xs text-gray-500 mb-4">💡 Only batches from current date are shown. Change dates to search for other dates.</p>

          <!-- Loading State -->
          <div v-if="loadingBatchDateItems" class="text-center py-8">
            <p class="text-gray-600">Loading batch numbers...</p>
          </div>

          <!-- Batch Numbers List -->
          <div v-else-if="batchDateItemResults.length > 0" class="overflow-y-auto max-h-96 border rounded-lg">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-indigo-50 sticky top-0">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-indigo-700 uppercase">Batch Number</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-indigo-700 uppercase">Warehouse</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-indigo-700 uppercase">Variant</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-indigo-700 uppercase">Date</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-indigo-700 uppercase">Action</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(batch, idx) in batchDateItemResults" :key="idx" class="hover:bg-indigo-50">
                  <td class="px-4 py-3 text-sm font-medium text-indigo-600">{{ batch.batch_number }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ batch.warehouse }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ batch.variant || '-' }}</td>
                  <td class="px-4 py-3 text-sm text-gray-600">{{ batch.date }}</td>
                  <td class="px-4 py-3">
                    <button @click="selectBatchDateItem(batch)" class="px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm">
                      Select
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- No Results -->
          <div v-else class="text-center py-8 text-gray-600">
            <p>No batch numbers found for this item code</p>
            <button @click="searchBatchDateItems" class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
              Search
            </button>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-gray-50 px-6 py-4 flex justify-end">
          <button @click="closeBatchDateItemModal" class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Selection Modal -->
    <div v-if="showBatchModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" @click.self="closeBatchModal">
      <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden" @click.stop>
        <!-- Modal Header -->
        <div class="bg-blue-600 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-xl font-bold">Select Batch Number - {{ currentComponent.ItemName }}</h3>
          <button @click="closeBatchModal" class="text-white hover:text-gray-200">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6">
          <!-- Date Range Filter -->
          <div class="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-blue-700 mb-1">Admission Date (From)</label>
              <input v-model="batchDateFrom" type="date" class="w-full px-3 py-2 border-2 border-blue-500 rounded-lg text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-blue-700 mb-1">Admission Date (To)</label>
              <input v-model="batchDateTo" type="date" class="w-full px-3 py-2 border-2 border-blue-500 rounded-lg text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div class="flex items-end">
              <button 
                @click="searchBatches"
                class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Search
              </button>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="loadingBatches" class="text-center py-8">
            <p class="text-gray-600">Loading batches...</p>
          </div>

          <!-- Batch Table -->
          <div v-else-if="batchNumbers.length > 0" class="overflow-y-auto max-h-96">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50 sticky top-0">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input type="checkbox" @change="toggleSelectAll" :checked="allBatchesSelected" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Batch Number</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Warehouse</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Available Qty</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mfg Date</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exp Date</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shelf Life</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Admission Date (InDate)</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(batch, idx) in batchNumbers" :key="idx" class="hover:bg-blue-50">
                  <td class="px-4 py-3 whitespace-nowrap">
                    <input 
                      type="checkbox" 
                      :value="batch"
                      v-model="selectedBatchesInModal"
                      class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600">{{ batch.BatchNumber }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ batch.Warehouse }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ batch.Quantity }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ batch.ManufacturingDate || '-' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ batch.ExpiryDate || '-' }}</td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm">
                    <span :class="batch.RemainingShelfLife > 30 ? 'text-green-600' : 'text-red-600'">
                      {{ batch.RemainingShelfLife }} days
                    </span>
                  </td>
                  <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ batch.InDate || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- No Results -->
          <div v-else class="text-center py-8 text-gray-600">
            No batch numbers found
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-gray-50 px-6 py-4 flex justify-between items-center">
          <div class="text-sm text-gray-600">
            {{ selectedBatchesInModal.length }} batch(es) selected
          </div>
          <div class="flex gap-3">
            <button 
              @click="confirmBatchesSelection"
              :disabled="selectedBatchesInModal.length === 0"
              class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm Selection
            </button>
            <button 
              @click="closeBatchModal"
              class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Production Order Details Modal -->
    <div v-if="showOrderDetailsModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" @click.self="closeOrderDetailsModal">
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden" @click.stop>
        <!-- Modal Header -->
        <div class="bg-blue-600 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-xl font-bold">Production Order Details - {{ selectedOrder?.name }}</h3>
          <button @click="closeOrderDetailsModal" class="text-white hover:text-gray-200">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- Modal Body -->
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div v-if="selectedOrder" class="space-y-4">
            <!-- Basic Info -->
            <div class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-semibold text-gray-700 mb-3">📋 Basic Information</h4>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span class="font-medium text-gray-600">Order ID:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.name }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">SAP Entry:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.sap_absoluteentry || 'N/A' }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">SAP DocNum:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.sap_production_number || 'N/A' }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">Status:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.status || 'N/A' }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">SAP Status:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.sap_status || 'N/A' }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">Production Order Status:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.production_order_status || 'N/A' }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">Created Date:</span>
                  <span class="ml-2 text-blue-700">{{ formatDate(selectedOrder.created_date) }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-600">User:</span>
                  <span class="ml-2 text-blue-700">{{ selectedOrder.user_name || selectedOrder.user_email || 'N/A' }}</span>
                </div>
              </div>
            </div>
            
            <!-- Request Payload -->
            <div v-if="selectedOrder.request_payload_json" class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-semibold text-gray-700 mb-3">📤 Request Payload (JSON)</h4>
              <pre class="text-xs bg-white p-3 rounded border overflow-x-auto max-h-64 overflow-y-auto">{{ formatJSON(selectedOrder.request_payload_json) }}</pre>
            </div>
            
            <!-- Response Payload -->
            <div v-if="selectedOrder.response_payload_json" class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-semibold text-gray-700 mb-3">📥 Response Payload (JSON)</h4>
              <pre class="text-xs bg-white p-3 rounded border overflow-x-auto max-h-64 overflow-y-auto">{{ formatJSON(selectedOrder.response_payload_json) }}</pre>
            </div>
            
            <!-- Error Message -->
            <div v-if="selectedOrder.error_message" class="bg-red-50 rounded-lg p-4 border border-red-200">
              <h4 class="font-semibold text-red-700 mb-2">⚠️ Error Message</h4>
              <p class="text-sm text-red-600">{{ selectedOrder.error_message }}</p>
            </div>
          </div>
        </div>
        
        <!-- Modal Footer -->
        <div class="bg-gray-50 px-6 py-4 flex justify-end">
          <button @click="closeOrderDetailsModal" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Approval Response Modal -->
    <div v-if="showApprovalResponseModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" @click.self="closeApprovalResponseModal">
      <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden" @click.stop>
        <!-- Modal Header -->
        <div class="bg-green-600 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-xl font-bold">✅ Production Order Approved Successfully!</h3>
          <button @click="closeApprovalResponseModal" class="text-white hover:text-gray-200">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div v-if="approvalResponseData" class="space-y-4">
            <div class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-semibold text-gray-700 mb-3">📋 SAP Response Details:</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">AbsoluteEntry:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.AbsoluteEntry || approvalResponseData.productionOrderDocEntry || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">DocumentNumber:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.DocumentNumber || approvalResponseData.productionOrderDocNum || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">DocEntry:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.productionOrderDocEntry || approvalResponseData.AbsoluteEntry || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">DocNum:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.productionOrderDocNum || approvalResponseData.DocumentNumber || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">Series:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.Series || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">ItemNo:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.ItemNo || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">ProductionOrderStatus:</span>
                  <span class="font-semibold text-green-700">{{ approvalResponseData.ProductionOrderStatus || 'boposReleased' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">ProductionOrderType:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.ProductionOrderType || 'N/A' }}</span>
                </div>
                <div class="flex justify-between border-b pb-2">
                  <span class="font-medium text-gray-600">PlannedQuantity:</span>
                  <span class="font-semibold text-blue-700">{{ approvalResponseData.PlannedQuantity || 'N/A' }}</span>
                </div>
              </div>
            </div>
            
            <!-- Full JSON Response (Collapsible) -->
            <details class="bg-gray-50 rounded-lg p-4">
              <summary class="cursor-pointer font-semibold text-gray-700 mb-2">🔍 View Full JSON Response</summary>
              <pre class="mt-2 text-xs bg-white p-3 rounded border overflow-x-auto">{{ JSON.stringify(approvalResponseData.sapResponse || approvalResponseData, null, 2) }}</pre>
            </details>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="bg-gray-50 px-6 py-4 flex justify-end">
          <button @click="closeApprovalResponseModal" class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            OK
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/core/stores/session.js'
import { getProductionService } from '@/core/api/common/productionServiceFactory'
import { usePushNotifications } from '@/composables/usePushNotifications.js'
import { APP_CONFIG } from '@/config/constants'

// Get plant ID from session
const sessionStore = useSessionStore()
const plantId = computed(() => {
  const session = sessionStore.getSession()
  return session?.plant?.id || 'nandi_hills'
})

const plantName = computed(() => {
  const session = sessionStore.getSession()
  return session?.plant?.name || 'Plant'
})

// Get production service for current plant
// Note: Using plantId.value ensures reactivity - when plant changes, service updates
const productionService = computed(() => {
  const currentPlantId = plantId.value
  return getProductionService(currentPlantId)
})

// Push Notifications
const pushNotifications = usePushNotifications()
const {
  isSupported: pushSupported,
  permission: pushPermission,
  isSubscribed: pushSubscribed,
  subscribe: pushSubscribe,
  requestPermission: pushRequestPermission,
  initialize: initializePush
} = pushNotifications
const testingPush = ref(false)

// Search and BOM Data
const bomSearchQuery = ref('')
const bomResults = ref([])
const showBOMResults = ref(false)
const selectedBOM = ref(null)
const searchQuery = ref('')
const loading = ref(false)

// Production Data
const productionType = ref('')

// BOM Components
const itt1Components = ref([])
const byProducts = ref([]) // Negative quantity items (outputs/byproducts)
const oittHeader = ref(null)

// Workflow
const workflowState = ref(0)
const workflowData = ref({
  productionOrderDocEntry: null,
  productionOrderDocNum: null,
  productionOrderStatus: null,
  goodsIssueDocEntry: null,
  goodsIssueDocNum: null,
  goodsReceiptDocEntry: null,
  goodsReceiptDocNum: null,
  closeDate: null
})
const workflowLoading = ref({
  approve: false,
  goodsIssue: false,
  goodsReceipt: false,
  close: false
})

// Output Data
const outputQuantity = ref('')
const outputBatchNumber = ref('')
const outputBatchDate = ref('')
const outputWarehouse = ref('')

// UI State
const sections = ref({
  itt1: true,
  output: true
})

const warehouses = ref([])
const loadingWarehouses = ref(false)

const router = useRouter()
const goToBatchGenerator = () => {
  router.push('/batch-generator')
}

// Get warehouse prefix based on plant ID
const getWarehousePrefix = (plantId) => {
  const normalizedPlantId = plantId?.toLowerCase() || ''
  
  if (normalizedPlantId.includes('nandi') || normalizedPlantId === 'nandi_hills' || normalizedPlantId === 'nandihills') {
    return 'N' // Nandi Hills - warehouses starting with N
  } else if (normalizedPlantId.includes('mahadevpura') || normalizedPlantId === 'mahadevpura') {
    return 'D' // Mahadevpura - warehouses starting with D
  } else if (normalizedPlantId.includes('malur') || normalizedPlantId === 'malur') {
    return 'H' // Malur - warehouses starting with H
  } else if (normalizedPlantId.includes('krishnagiri') || normalizedPlantId === 'krishnagiri') {
    return 'K' // Krishnagiri - warehouses starting with K
  } else if (normalizedPlantId.includes('champavath') || normalizedPlantId === 'champavath') {
    return null // Champavath - all warehouses (no prefix filter)
  }
  
  return null // Default: no prefix filter
}

// Auto-select warehouse based on plant prefix
const autoSelectWarehouse = (warehouseList, prefix) => {
  if (!warehouseList || warehouseList.length === 0) {
    return ''
  }
  
  // If no prefix (Champavath), return first warehouse
  if (!prefix) {
    return warehouseList[0] || ''
  }
  
  // Find first warehouse starting with prefix
  const matchingWarehouse = warehouseList.find(wh => 
    wh && wh.toUpperCase().startsWith(prefix.toUpperCase())
  )
  
  return matchingWarehouse || warehouseList[0] || ''
}

// Computed property to filter warehouses based on plant prefix
const filteredWarehouses = computed(() => {
  if (!warehouses.value || warehouses.value.length === 0) {
    return []
  }
  
  const prefix = getWarehousePrefix(plantId.value)
  
  // If no prefix (Champavath), return all warehouses
  if (!prefix) {
    return warehouses.value
  }
  
  // Filter warehouses starting with the prefix
  return warehouses.value.filter(wh => 
    wh && wh.toUpperCase().startsWith(prefix.toUpperCase())
  )
})

// Fetch warehouses from SAP on mount
const fetchWarehouses = async () => {
  try {
    loadingWarehouses.value = true
    const response = await productionService.value.getWarehouses()
    
    if (response.success && response.data) {
      // Extract warehouse codes from the response
      warehouses.value = response.data.map(wh => wh.WhsCode)
      
      // Auto-select warehouse for output if BOM is already selected and warehouse is not set
      if (selectedBOM.value && !outputWarehouse.value && warehouses.value.length > 0) {
        const prefix = getWarehousePrefix(plantId.value)
        const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
        if (selectedWarehouse) {
          outputWarehouse.value = selectedWarehouse
        }
      }
      
      // Auto-select warehouse for byproducts if they exist and warehouses are not set
      if (byProducts.value && byProducts.value.length > 0 && warehouses.value.length > 0) {
        const prefix = getWarehousePrefix(plantId.value)
        byProducts.value.forEach(product => {
          if (!product.outputWarehouse) {
            const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
            if (selectedWarehouse) {
              product.outputWarehouse = selectedWarehouse
            }
          }
        })
      }
    } else {
      console.error('Failed to fetch warehouses:', response.message)
      // Fallback to empty array or default warehouses if API fails
      warehouses.value = []
    }
  } catch (error) {
    console.error('Error fetching warehouses:', error)
    // Fallback to empty array if API fails
    warehouses.value = []
  } finally {
    loadingWarehouses.value = false
  }
}

// Batch Selection Modal
const showBatchModal = ref(false)
const batchNumbers = ref([])
const loadingBatches = ref(false)
const currentComponent = ref(null)
const batchDateFrom = ref('')
const batchDateTo = ref('')
const selectedBatchesInModal = ref([])

// Batch Date Item Lookup Modal
const showBatchDateItemModal = ref(false)
const batchDateItemResults = ref([])
const loadingBatchDateItems = ref(false)
const currentBatchLookupItem = ref(null)
const batchDateItemLookupDateFrom = ref('')
const batchDateItemLookupDateTo = ref('')

// Approval Response Modal
const showApprovalResponseModal = ref(false)
const approvalResponseData = ref(null)

// Sidebar and Production Orders List
const showSidebar = ref(false)
const productionOrders = ref([])
const loadingOrders = ref(false)
const ordersPagination = ref({
  page: 1,
  page_size: 20,
  total_pages: 1,
  total_count: 0
})
const dateFilterFrom = ref('')
const dateFilterTo = ref('')
const currentDateFilters = ref({})

// Production Order Details Modal
const showOrderDetailsModal = ref(false)
const selectedOrder = ref(null)

// Search with debounce
let searchTimeout = null
const onBOMSearchInput = () => {
  clearTimeout(searchTimeout)
  
  if (bomSearchQuery.value.length < 2) {
    bomResults.value = []
    showBOMResults.value = false
    // Clear all data when search is cleared
    if (bomSearchQuery.value.length === 0) {
      clearBOMSelection()
    }
    return
  }
  
  searchTimeout = setTimeout(() => {
    searchBOMTables()
  }, 300)
}

const searchBOMTables = async () => {
  try {
    loading.value = true
    console.log('Searching BOM with query:', bomSearchQuery.value)
    
    if (!bomSearchQuery.value || bomSearchQuery.value.trim().length < 2) {
      bomResults.value = []
      showBOMResults.value = false
      return
    }
    
    const response = await productionService.value.searchBOM(bomSearchQuery.value.trim())
    
    console.log('BOM Search Response:', response)
    
    // Handle different response structures
    let data = null
    if (response) {
      // Check if response has success and data properties
      if (response.success !== undefined && response.data !== undefined) {
        data = response.data
      } 
      // Check if response is the data directly (array)
      else if (Array.isArray(response)) {
        data = response
      }
      // Check if response has a message property (Frappe format)
      else if (response.message) {
        data = response.message
      }
    }
    
    if (data && Array.isArray(data) && data.length > 0) {
      bomResults.value = data
      showBOMResults.value = true
      console.log('BOM Results set:', bomResults.value.length, 'items')
    } else if (response && response.success === false) {
      console.warn('Search failed:', response.message || 'Unknown error')
      bomResults.value = []
      showBOMResults.value = false
    } else {
      console.warn('No results found or invalid response structure:', response)
      bomResults.value = []
      showBOMResults.value = false
    }
  } catch (error) {
    console.error('Error searching BOM:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })
    bomResults.value = []
    showBOMResults.value = false
  } finally {
    loading.value = false
  }
}

const selectBOM = async (bom) => {
  selectedBOM.value = bom
  showBOMResults.value = false
  
  // Reset manually edited inputs when selecting a new BOM
  manuallyEditedInputs.value.clear()
  
  // All search results are OITT headers - fetch their ITT1 components automatically
  oittHeader.value = bom
  bomSearchQuery.value = bom.Name || bom.Code
  
      // Initialize output fields - outputQuantity will be set to BOM Qty after fetching OITT
      outputQuantity.value = ''
      outputBatchNumber.value = ''
      outputBatchDate.value = new Date().toISOString().split('T')[0] // Set to today
      outputWarehouse.value = bom.ToWH || ''
  
  // Fetch full OITT header to get complete details (for BOM Qty display)
  await fetchOITTForBOM(bom.Code)
  // Automatically fetch ITT1 components for the selected BOM
  await fetchITT1ForBOM(bom.Code)
  
  // If outputQuantity is still empty after fetching, try to set it from selectedBOM
  if (!outputQuantity.value && (bom.Quantity !== undefined && bom.Quantity !== null)) {
    outputQuantity.value = bom.Quantity
    // Auto-calculate input quantities after setting output quantity
    setTimeout(() => {
      updateInputQuantities()
    }, 100)
  }
  
  // Auto-fetch batch number for current date only
  await autoFetchOutputBatchNumber()
  
  // Auto-fetch batch numbers for byproducts (after they are loaded)
  // Wait a bit for byproducts to be populated from fetchITT1ForBOM
  setTimeout(async () => {
    await autoFetchByproductBatchNumbers()
  }, 200)
}

const fetchITT1ForBOM = async (bomCode) => {
  try {
    loading.value = true
    const response = await productionService.value.getITT1Components(bomCode)
    
    console.log('ITT1 Response:', response)
    
    if (response && response.success && response.data && Array.isArray(response.data)) {
      // Separate positive (inputs) and negative (byproducts) quantities
      const allComponents = response.data.map(comp => ({
        ...comp,
        inputQuantity: '',
        batchNumber: '',
        warehouse: comp.Warehouse || '',
        selectedBatches: []
      }))
      
      console.log('Mapped components:', allComponents)
      
      // Filter components by quantity sign
      itt1Components.value = allComponents.filter(comp => comp.Quantity >= 0)
      // Set current date for byproducts
      const currentDate = new Date().toISOString().split('T')[0]
      byProducts.value = allComponents.filter(comp => comp.Quantity < 0).map(comp => ({
        ...comp,
        outputQuantity: Math.abs(comp.Quantity).toString(), // Convert to positive for display
        outputBatchNumber: '',
        batchDate: currentDate, // Set to current date automatically
        outputWarehouse: comp.Warehouse || ''
      }))
      
      console.log('ITT1 Components:', itt1Components.value)
      
      // Auto-calculate input quantities after components are loaded
      if (outputQuantity.value) {
        updateInputQuantities()
      }
    } else {
      console.warn('Invalid response or empty data:', response)
      itt1Components.value = []
      byProducts.value = []
    }
  } catch (error) {
    console.error('Error fetching ITT1:', error)
    itt1Components.value = []
    byProducts.value = []
  } finally {
    loading.value = false
  }
}

const fetchOITTForBOM = async (bomCode) => {
  try {
    loading.value = true
    const response = await productionService.value.getOITTHeader(bomCode)
    
    if (response.success && response.data) {
      oittHeader.value = response.data
      // Initialize outputQuantity to BOM Qty if not already set
      if (!outputQuantity.value && (response.data.Quantity !== undefined && response.data.Quantity !== null)) {
        outputQuantity.value = response.data.Quantity
      } else if (!outputQuantity.value && (selectedBOM.value?.Quantity !== undefined && selectedBOM.value?.Quantity !== null)) {
        outputQuantity.value = selectedBOM.value.Quantity
      }
      
      // Auto-calculate input quantities after setting output quantity
      if (outputQuantity.value) {
        // Use setTimeout to ensure ITT1 components are loaded first
        setTimeout(() => {
          updateInputQuantities()
        }, 100)
      }
    }
  } catch (error) {
    console.error('Error fetching OITT:', error)
  } finally {
    loading.value = false
  }
}

const clearBOMSelection = () => {
  selectedBOM.value = null
  bomSearchQuery.value = ''
  itt1Components.value = []
  byProducts.value = []
  outputQuantity.value = ''
  outputBatchNumber.value = ''
  outputBatchDate.value = ''
  outputWarehouse.value = ''
  manuallyEditedInputs.value.clear()
}

const toggleSection = (section) => {
  sections.value[section] = !sections.value[section]
}

// Get Output BOM Qty (readonly field in Output section)
const getOutputBOMQty = () => {
  if (selectedBOM.value?.Quantity !== undefined && selectedBOM.value?.Quantity !== null) {
    return parseFloat(selectedBOM.value.Quantity)
  }
  if (oittHeader.value?.Quantity !== undefined && oittHeader.value?.Quantity !== null) {
    return parseFloat(oittHeader.value.Quantity)
  }
  return 0
}

// Calculate Base Qty Clear = Input Component BOM Qty / Output BOM Qty
// Returns the numeric value for calculations
const getBaseQtyClearValue = (comp) => {
  const inputBOMQty = comp.Quantity !== undefined && comp.Quantity !== null ? parseFloat(comp.Quantity) : 0
  const outputBOMQty = getOutputBOMQty()
  
  if (outputBOMQty === 0 || inputBOMQty === 0) {
    return 0
  }
  
  return inputBOMQty / outputBOMQty
}

// Calculate Base Qty Clear for display = Input Component BOM Qty / Output BOM Qty
const calculateBaseQtyClear = (comp) => {
  const value = getBaseQtyClearValue(comp)
  
  if (value === 0) {
    return '-'
  }
  
  // Round to 4 decimal places for display
  return value.toFixed(4)
}

// Track if user has manually edited input quantities (to prevent auto-override)
const manuallyEditedInputs = ref(new Set())

// Handle manual input quantity changes
const updateInputQuantity = (comp, event) => {
  const value = event.target.value ? parseFloat(event.target.value) : ''
  comp.inputQuantity = value
  // Mark this component as manually edited
  manuallyEditedInputs.value.add(comp.Code)
}

// Auto-calculate Input Quantity when Output Quantity changes
const updateInputQuantities = () => {
  const outputQty = outputQuantity.value ? parseFloat(outputQuantity.value) : 0
  
  if (outputQty > 0) {
    itt1Components.value.forEach(comp => {
      // Only auto-calculate if user hasn't manually edited this component
      if (!manuallyEditedInputs.value.has(comp.Code)) {
        // Calculate: Input Quantity = Base Qty Clear * Output Quantity
        const baseQtyClear = getBaseQtyClearValue(comp)
        if (baseQtyClear > 0) {
          comp.inputQuantity = baseQtyClear * outputQty
        }
      }
    })
  } else {
    // Clear input quantities if output quantity is empty or 0 (only if not manually edited)
    itt1Components.value.forEach(comp => {
      if (!manuallyEditedInputs.value.has(comp.Code)) {
        comp.inputQuantity = ''
      }
    })
  }
}

// Watch for changes in outputQuantity and auto-update input quantities
watch(outputQuantity, () => {
  updateInputQuantities()
})

const fetchITT1Details = async () => {
  if (!selectedBOM.value?.Code) return
  
  try {
    loading.value = true
    const response = await productionService.value.getITT1Components(selectedBOM.value.Code)
    
    if (response.success && response.data) {
      itt1Components.value = response.data
    } else {
      // Mock data for development
      itt1Components.value = [
        {
          Code: 'ITEM001',
          ItemName: 'Raw Material 1',
          Quantity: 100,
          Warehouse: 'NH01',
          U_BaseQty: 100,
          U_Scrap: 5,
          U_MatType: 'Raw',
          inputQuantity: 100,
          batchNumber: '',
          warehouse: 'NH01'
        }
      ]
    }
  } catch (error) {
    console.error('Error fetching ITT1:', error)
  } finally {
    loading.value = false
  }
}

const fetchOITTDetails = async () => {
  if (!selectedBOM.value?.Code) return
  
  try {
    loading.value = true
    const response = await productionService.value.getOITTHeader(selectedBOM.value.Code)
    
    if (response.success && response.data) {
      oittHeader.value = response.data
    } else {
      // Mock data for development
      oittHeader.value = {
        Code: 'BOM001',
        Name: 'Sample BOM',
        TreeType: 'S',
        ToWH: 'NH01'
      }
    }
  } catch (error) {
    console.error('Error fetching OITT:', error)
  } finally {
    loading.value = false
  }
}

// Test Push Notification
const testPushNotification = async () => {
  try {
    testingPush.value = true
    
    console.log('🔔 Testing push notification...', {
      pushSupported: pushSupported.value,
      permission: pushPermission.value,
      isSubscribed: pushSubscribed.value,
      hasServiceWorker: 'serviceWorker' in navigator,
      hasPushManager: 'PushManager' in window,
      hasNotification: 'Notification' in window
    })
    
    // Check browser support directly
    if (!('serviceWorker' in navigator)) {
      alert('❌ Service Worker API not supported.\n\nPlease use Chrome, Firefox, or Edge browser.')
      return
    }
    
    if (!('PushManager' in window)) {
      alert('❌ PushManager API not supported.\n\nPlease use Chrome, Firefox, or Edge browser.')
      return
    }
    
    if (!('Notification' in window)) {
      alert('❌ Notification API not supported.\n\nPlease use Chrome, Firefox, or Edge browser.')
      return
    }
    
    // Try to initialize if not already initialized
    if (!pushSupported.value) {
      console.log('⏳ Push not initialized, attempting to initialize...')
      await initializePush()
      
      // Check again
      if (!pushSupported.value) {
        alert('❌ Push notifications initialization failed.\n\nCheck browser console (F12) for details.\n\nPossible issues:\n- Service worker not registered\n- VAPID keys not configured\n- Network error\n\nNote: Make sure you rebuild the frontend after changes!')
        return
      }
    }
    
    // Check permission
    if (pushPermission.value !== 'granted') {
      const permission = await pushRequestPermission()
      if (permission !== 'granted') {
        alert('Notification permission is required to test push notifications')
        return
      }
    }
    
    // Always ensure subscription is saved to backend
    // Even if browser shows subscribed, backend might not have it
    // IMPORTANT: If VAPID keys were regenerated, user MUST re-subscribe
    console.log('📝 Ensuring subscription is saved to backend...')
    try {
      // Force re-subscribe to ensure backend has the subscription
      // This will create a new subscription with the current VAPID public key
      await pushSubscribe(plantId.value)
      console.log('✅ Subscription saved to backend')
    } catch (error) {
      console.error('❌ Subscription failed:', error)
      // If subscription fails, it might be because VAPID keys were regenerated
      // User needs to clear browser storage and re-subscribe
      if (error.message && (error.message.includes('401') || error.message.includes('Invalid'))) {
        alert('⚠️ Subscription invalid!\n\nVAPID keys may have been regenerated. Please:\n1. Clear browser storage for this site\n2. Refresh the page\n3. Click "Test Push" again to re-subscribe')
        return
      }
      // If subscription fails, still try to send notification (might work if subscription exists)
      console.warn('⚠️ Continuing despite subscription error...')
    }
    
    // Get current user - use the same identifier that was used during subscription
    // The backend uses frappe.session.user, so we should not pass user parameter
    // and let the backend use the session user instead
    const session = sessionStore.getSession()
    const currentUser = session?.user?.email || session?.user?.name || null
    
    console.log('📤 Sending test notification...', { currentUser, plantId: plantId.value })
    
    // Send test notification via API
    // Note: Don't pass user parameter - backend will use frappe.session.user automatically
    const response = await fetch(
      `${APP_CONFIG.FRAPPE_API_URL}/method/khanal_tech_integrations.api.push_notifications.send_push_notification_api`,
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          // user: currentUser, // Let backend use session user instead
          title: '🧪 Test Push Notification',
          message: `This is a test push notification from ${plantName.value}! If you see this, push notifications are working correctly.`,
          icon: '/icons/icon.svg',
          data: {
            type: 'test',
            route: window.location.pathname,
            timestamp: new Date().toISOString()
          },
          plant_id: plantId.value
        })
      }
    )
    
    const data = await response.json()
    
    if (data.message && data.message.success && data.message.sent_count > 0) {
      alert(`✅ Test notification sent!\n\nSent: ${data.message.sent_count}\nFailed: ${data.message.failed_count}\n\nCheck your browser notifications (top-right corner or notification center)!`)
    } else if (data.message && data.message.failed_count > 0) {
      // If sending failed, show a local notification to demonstrate where it appears
      console.warn('Backend send failed, showing local notification as demo...')
      if ('Notification' in window && Notification.permission === 'granted') {
        const demoNotification = new Notification('🧪 Demo: Test Push Notification', {
          body: `This is where push notifications appear! Backend send failed: ${data.message?.errors?.[0] || 'Unknown error'}`,
          icon: '/icons/icon.svg',
          badge: '/icons/icon.svg',
          tag: 'test-demo',
          requireInteraction: false
        })
        
        demoNotification.onclick = () => {
          window.focus()
          demoNotification.close()
        }
        
        alert(`⚠️ Backend send failed, but showing local notification as demo.\n\nSent: ${data.message.sent_count}\nFailed: ${data.message.failed_count}\n\nLook for the notification in your browser's notification area (top-right corner)!`)
      } else {
        alert(`❌ Failed to send notification: ${data.message?.errors?.[0] || data.message?.message || 'Unknown error'}\n\nAlso, notification permission is not granted.`)
      }
    } else {
      alert(`❌ Failed to send notification: ${data.message?.message || 'Unknown error'}`)
    }
  } catch (error) {
    console.error('Error testing push notification:', error)
    alert(`❌ Error: ${error.message}`)
  } finally {
    testingPush.value = false
  }
}

const refreshData = () => {
  fetchOITTDetails()
  fetchITT1Details()
}

// Workflow Actions
const buildProductionData = () => {
  if (!selectedBOM.value) {
    return null
  }
  
  // Build production order lines from inputs and byproducts
  const productionOrderLines = []
  
  // Add inputs (positive quantity)
  itt1Components.value.forEach(comp => {
    if (comp.inputQuantity && comp.inputQuantity > 0) {
      // Handle batch numbers - support both single batch and multi-batch
      let batchNumber = comp.batchNumber
      if (comp.selectedBatches && comp.selectedBatches.length > 0) {
        // For multi-batch, use the first batch or aggregate
        batchNumber = comp.selectedBatches[0].BatchNumber
      }
      
      productionOrderLines.push({
        ItemNo: comp.Code,
        PlannedQuantity: comp.inputQuantity,
        Warehouse: comp.warehouse || comp.Warehouse,
        ProductionOrderIssueType: comp.IssueMthd || 'im_Manual',
        BatchNumber: batchNumber,
        selectedBatches: comp.selectedBatches || []
      })
    }
  })
  
  // Add byproducts (negative quantity)
  byProducts.value.forEach(product => {
    if (product.outputQuantity && product.outputQuantity > 0) {
      productionOrderLines.push({
        ItemNo: product.Code,
        PlannedQuantity: -parseFloat(product.outputQuantity), // Negative for byproducts
        Warehouse: product.outputWarehouse || product.Warehouse,
        ProductionOrderIssueType: product.IssueMthd || 'im_Manual',
        outputBatchNumber: product.outputBatchNumber,
        BatchNumber: product.outputBatchNumber
      })
    }
  })
  
  return {
    ItemNo: selectedBOM.value.Code,
    PlannedQuantity: parseFloat(outputQuantity.value) || 0,
    PostingDate: outputBatchDate.value || new Date().toISOString().split('T')[0],
    Warehouse: outputWarehouse.value || selectedBOM.value.ToWH,
    outputBatchNumber: outputBatchNumber.value,
    ProductionOrderLines: productionOrderLines
  }
}

const submitApproval = async () => {
  try {
    workflowLoading.value.approve = true
    
    // Validate required fields
    if (!selectedBOM.value) {
      alert('⚠️ Please select a BOM first')
      workflowLoading.value.approve = false
      return
    }
    
    if (!outputQuantity.value || outputQuantity.value <= 0) {
      alert('⚠️ Please enter output quantity')
      workflowLoading.value.approve = false
      return
    }
    
    if (!productionType.value) {
      alert('⚠️ Please select a Process Type')
      workflowLoading.value.approve = false
      return
    }
    
    // Validate inputs have quantities and batches
    const hasInvalidInputs = itt1Components.value.some(comp => {
      if (comp.inputQuantity && comp.inputQuantity > 0) {
        const hasBatch = comp.batchNumber || (comp.selectedBatches && comp.selectedBatches.length > 0)
        return !hasBatch
      }
      return false
    })
    
    if (hasInvalidInputs) {
      alert('⚠️ Please ensure all input materials have batch numbers')
      workflowLoading.value.approve = false
      return
    }
    
    // Build production data
    const productionData = buildProductionData()
    if (!productionData) {
      alert('⚠️ Failed to build production data')
      workflowLoading.value.approve = false
      return
    }
    
    // Call API
    console.log('Submitting approval with data:', productionData)
    const response = await productionService.value.approveProductionOrder(productionData)
    console.log('Approve API Response:', response)
    
    if (response && response.success) {
      workflowState.value = 1
      workflowData.value.productionOrderDocEntry = response.productionOrderDocEntry || response.AbsoluteEntry
      workflowData.value.productionOrderDocNum = response.productionOrderDocNum || response.DocumentNumber
      workflowData.value.productionOrderStatus = response.ProductionOrderStatus
      
      // Store full response data for modal display
      const sapResponse = response.sapResponse || response
      approvalResponseData.value = {
        ...response,
        ...sapResponse,
        AbsoluteEntry: sapResponse.AbsoluteEntry || response.AbsoluteEntry || response.productionOrderDocEntry,
        DocumentNumber: sapResponse.DocumentNumber || response.DocumentNumber || response.productionOrderDocNum,
        DocEntry: response.productionOrderDocEntry || sapResponse.DocEntry || sapResponse.AbsoluteEntry,
        DocNum: response.productionOrderDocNum || sapResponse.DocNum || sapResponse.DocumentNumber,
        Series: sapResponse.Series || response.Series,
        ItemNo: sapResponse.ItemNo || response.ItemNo,
        ProductionOrderStatus: sapResponse.ProductionOrderStatus || response.ProductionOrderStatus || 'boposReleased',
        ProductionOrderType: sapResponse.ProductionOrderType || response.ProductionOrderType,
        PlannedQuantity: sapResponse.PlannedQuantity || response.PlannedQuantity,
        sapResponse: sapResponse
      }
      
      // Show response modal
      showApprovalResponseModal.value = true
      
      // Refresh production orders list if sidebar is open
      if (showSidebar.value) {
        fetchProductionOrders(ordersPagination.value.page)
      }
      
      // Also log full response to console for debugging
      console.log('Full SAP Response:', sapResponse)
      
      // Also dispatch a global success event for toast notification
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('global-success', {
          detail: { 
            message: `Production Order Approved! DocEntry: ${response.productionOrderDocEntry || response.AbsoluteEntry}, DocNum: ${response.productionOrderDocNum || response.DocumentNumber}` 
          }
        }))
      }
    } else {
      const errorMessage = response?.message || response?.error || 'Failed to approve production order'
      console.error('Approve failed:', errorMessage, response)
      alert(`❌ Error: ${errorMessage}`)
      
      // Also dispatch a global error event
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('global-error', {
          detail: { message: errorMessage }
        }))
      }
    }
  } catch (error) {
    console.error('Error approving production order:', error)
    const errorMessage = error?.response?.data?.message || error?.message || 'Failed to approve production order'
    alert(`❌ Error: ${errorMessage}`)
    
    // Also dispatch a global error event
    if (window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent('global-error', {
        detail: { message: errorMessage }
      }))
    }
  } finally {
    workflowLoading.value.approve = false
  }
}

const submitGoodsIssue = async () => {
  try {
    workflowLoading.value.goodsIssue = true
    
    if (!workflowData.value.productionOrderDocEntry) {
      alert('⚠️ Please approve the production order first')
      return
    }
    
    // Build production data
    const productionData = buildProductionData()
    if (!productionData) {
      alert('⚠️ Failed to build production data')
      return
    }
    
    // Call API
    const response = await productionService.value.goodsIssue(
      workflowData.value.productionOrderDocEntry,
      productionData
    )
    
    if (response.success) {
      workflowState.value = 2
      workflowData.value.goodsIssueDocEntry = response.goodsIssueDocEntry
      workflowData.value.goodsIssueDocNum = response.goodsIssueDocNum
      alert(`✅ Goods Issued!\nDocEntry: ${response.goodsIssueDocEntry}\nDocNum: ${response.goodsIssueDocNum}`)
    } else {
      alert(`❌ Error: ${response.message || 'Failed to issue goods'}`)
    }
  } catch (error) {
    console.error('Error issuing goods:', error)
    alert(`❌ Error: ${error.message || 'Failed to issue goods'}`)
  } finally {
    workflowLoading.value.goodsIssue = false
  }
}

const submitGoodsReceipt = async () => {
  try {
    workflowLoading.value.goodsReceipt = true
    
    if (!workflowData.value.productionOrderDocEntry) {
      alert('⚠️ Please approve the production order first')
      return
    }
    
    // Validate output batch
    if (!outputBatchNumber.value) {
      alert('⚠️ Please enter output batch number')
      return
    }
    
    // Build production data
    const productionData = buildProductionData()
    if (!productionData) {
      alert('⚠️ Failed to build production data')
      return
    }
    
    // Call API
    const response = await productionService.value.goodsReceipt(
      workflowData.value.productionOrderDocEntry,
      productionData
    )
    
    if (response.success) {
      workflowState.value = 3
      workflowData.value.goodsReceiptDocEntry = response.goodsReceiptDocEntry
      workflowData.value.goodsReceiptDocNum = response.goodsReceiptDocNum
      alert(`✅ Goods Received!\nDocEntry: ${response.goodsReceiptDocEntry}\nDocNum: ${response.goodsReceiptDocNum}`)
    } else {
      alert(`❌ Error: ${response.message || 'Failed to receive goods'}`)
    }
  } catch (error) {
    console.error('Error receiving goods:', error)
    alert(`❌ Error: ${error.message || 'Failed to receive goods'}`)
  } finally {
    workflowLoading.value.goodsReceipt = false
  }
}

const closeProduction = async () => {
  try {
    workflowLoading.value.close = true
    
    if (!workflowData.value.productionOrderDocEntry) {
      alert('⚠️ Please approve the production order first')
      return
    }
    
    // Call API
    const closeDate = new Date().toISOString().split('T')[0]
    const response = await productionService.value.closeProduction(
      workflowData.value.productionOrderDocEntry,
      closeDate
    )
    
    if (response.success) {
      workflowData.value.productionOrderStatus = response.ProductionOrderStatus
      workflowData.value.closeDate = response.CloseDate
      alert(`✅ Production Closed!\nClose Date: ${response.CloseDate}`)
      // Don't reset workflow state after closing - keep it disabled
      // All buttons will be disabled because isProductionClosed will be true
    } else {
      alert(`❌ Error: ${response.message || 'Failed to close production'}`)
    }
  } catch (error) {
    console.error('Error closing production:', error)
    alert(`❌ Error: ${error.message || 'Failed to close production'}`)
  } finally {
    workflowLoading.value.close = false
  }
}

// Check if production is fully closed/completed
const isProductionClosed = computed(() => {
  return workflowData.value.closeDate || workflowData.value.productionOrderStatus === 'boposClosed'
})

// Multi-batch selection functions
const allBatchesSelected = computed(() => {
  return batchNumbers.value.length > 0 && selectedBatchesInModal.value.length === batchNumbers.value.length
})

const toggleSelectAll = () => {
  if (allBatchesSelected.value) {
    selectedBatchesInModal.value = []
  } else {
    selectedBatchesInModal.value = [...batchNumbers.value]
  }
}

const confirmBatchesSelection = () => {
  if (currentComponent.value && selectedBatchesInModal.value.length > 0) {
    // Initialize selectedBatches array if it doesn't exist
    if (!currentComponent.value.selectedBatches) {
      currentComponent.value.selectedBatches = []
    }
    
    // Preserve existing total quantity before adding new batches
    const existingTotal = currentComponent.value.inputQuantity || 0
    const existingBatchesTotal = currentComponent.value.selectedBatches.reduce((sum, b) => sum + (b.inputQuantity || 0), 0)
    const remainingQuantity = existingTotal - existingBatchesTotal
    
    // Filter out batches that already exist
    const newBatches = selectedBatchesInModal.value.filter(batch => 
      !currentComponent.value.selectedBatches.some(b => b.BatchNumber === batch.BatchNumber)
    )
    const newBatchCount = newBatches.length
    
    // Add each new batch with its details
    newBatches.forEach((batch, index) => {
      // If there's remaining quantity to distribute, distribute it evenly
      // Otherwise, set to 0 (user can manually adjust)
      let batchQuantity = 0
      if (newBatchCount > 0 && remainingQuantity > 0) {
        // Distribute remaining quantity evenly among new batches
        batchQuantity = Math.floor(remainingQuantity / newBatchCount)
        // Add remainder to first batch
        if (index === 0) {
          batchQuantity += remainingQuantity % newBatchCount
        }
      } else if (newBatchCount === 1 && existingTotal > 0 && existingBatchesTotal === 0) {
        // If this is the first batch and there's an existing quantity, use it
        batchQuantity = existingTotal
      }
      
        currentComponent.value.selectedBatches.push({
          BatchNumber: batch.BatchNumber,
          Warehouse: batch.Warehouse,
          AvailableQty: batch.Quantity,
        inputQuantity: batchQuantity,
          ManufacturingDate: batch.ManufacturingDate,
          ExpiryDate: batch.ExpiryDate,
          RemainingShelfLife: batch.RemainingShelfLife,
          InDate: batch.InDate
        })
    })
    
    // Update the total quantity (this will sum all batch quantities)
    updateComponentTotal(currentComponent.value)
    
    // Clear modal selections
    selectedBatchesInModal.value = []
    
    // Close modal
    closeBatchModal()
  }
}

const removeBatchFromComponent = (comp, batchIdx) => {
  if (comp.selectedBatches && comp.selectedBatches[batchIdx]) {
    comp.selectedBatches.splice(batchIdx, 1)
    updateComponentTotal(comp)
  }
}

const updateComponentTotal = (comp) => {
  if (comp.selectedBatches && comp.selectedBatches.length > 0) {
    const total = comp.selectedBatches.reduce((sum, batch) => {
      return sum + (batch.inputQuantity || 0)
    }, 0)
    comp.inputQuantity = total
    
    // Update batchNumber field for compatibility with single-batch selection
    if (comp.selectedBatches.length === 1) {
      comp.batchNumber = comp.selectedBatches[0].BatchNumber
      comp.warehouse = comp.selectedBatches[0].Warehouse
    } else {
      comp.batchNumber = `${comp.selectedBatches.length} batches selected`
    }
  }
}

const openBatchModal = async (comp) => {
  currentComponent.value = comp
  showBatchModal.value = true
  selectedBatchesInModal.value = []
  allBatchesSelected.value = false
  
  // Auto-fetch batches when modal opens
  await searchBatches()
  
  // Auto-select the most recent batch if available (for single-batch compatibility)
  if (batchNumbers.value.length > 0 && !comp.batchNumber && !comp.selectedBatches) {
    // This is the old single-batch behavior - keeping for backward compatibility
  }
}

const searchBatches = async () => {
  if (!currentComponent.value?.Code) {
    console.log('No component selected')
    return
  }
  
  console.log('Fetching batches for:', {
    Code: currentComponent.value.Code,
    warehouse: currentComponent.value.warehouse,
    dateFrom: batchDateFrom.value,
    dateTo: batchDateTo.value
  })
  
  try {
    loadingBatches.value = true
    const response = await productionService.value.getBatchNumbers(
      currentComponent.value.Code,
      currentComponent.value.warehouse,
      batchDateFrom.value || null,
      batchDateTo.value || null
    )
    
    console.log('Batch API Response:', response)
    
    if (response && response.success && response.data) {
      batchNumbers.value = response.data
      console.log('Found batches:', response.data.length)
    } else {
      batchNumbers.value = []
      console.log('No batches found')
    }
  } catch (error) {
    console.error('Error fetching batches:', error)
    console.error('Error details:', error.response || error.message)
    batchNumbers.value = []
  } finally {
    loadingBatches.value = false
  }
}

const closeBatchModal = () => {
  showBatchModal.value = false
  batchNumbers.value = []
  selectedBatchesInModal.value = []
  currentComponent.value = null
  batchDateFrom.value = ''
  batchDateTo.value = ''
}

// Batch Date Item Lookup Functions
// Auto-fetch batch number for output when BOM is selected
const autoFetchOutputBatchNumber = async () => {
  if (!selectedBOM.value?.Code) {
    return
  }
  
  try {
    const today = new Date().toISOString().split('T')[0]
    const response = await productionService.value.getBatchNumbersFromBatchDateItem(
      selectedBOM.value.Code,
      today, // Only current date
      today  // Only current date
    )
    
    if (response && response.success && response.data && response.data.length > 0) {
      // Auto-select the first batch from current date
      const firstBatch = response.data[0]
      outputBatchNumber.value = firstBatch.batch_number
      
      // Auto-select warehouse based on plant prefix
      if (warehouses.value && warehouses.value.length > 0) {
        const prefix = getWarehousePrefix(plantId.value)
        const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
        if (selectedWarehouse) {
          outputWarehouse.value = selectedWarehouse
        } else if (firstBatch.warehouse) {
          outputWarehouse.value = firstBatch.warehouse
        }
      } else if (firstBatch.warehouse) {
        outputWarehouse.value = firstBatch.warehouse
      }
    } else {
      // Even if no batch found, auto-select warehouse based on plant prefix
      if (warehouses.value && warehouses.value.length > 0) {
        const prefix = getWarehousePrefix(plantId.value)
        const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
        if (selectedWarehouse) {
          outputWarehouse.value = selectedWarehouse
        }
      }
    }
  } catch (error) {
    console.error('Error auto-fetching batch number:', error)
    // Even on error, try to auto-select warehouse
    if (warehouses.value && warehouses.value.length > 0) {
      const prefix = getWarehousePrefix(plantId.value)
      const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
      if (selectedWarehouse) {
        outputWarehouse.value = selectedWarehouse
      }
    }
  }
}

// Auto-fetch batch numbers for byproducts when BOM is selected
const autoFetchByproductBatchNumbers = async () => {
  if (!byProducts.value || byProducts.value.length === 0) {
    return
  }
  
  const today = new Date().toISOString().split('T')[0]
  const prefix = getWarehousePrefix(plantId.value)
  
  // Fetch batch numbers for each byproduct
  for (const product of byProducts.value) {
    if (!product.Code) {
      continue
    }
    
    try {
      const response = await productionService.value.getBatchNumbersFromBatchDateItem(
        product.Code,
        today, // Only current date
        today  // Only current date
      )
      
      if (response && response.success && response.data && response.data.length > 0) {
        // Auto-select the first batch from current date
        const firstBatch = response.data[0]
        product.outputBatchNumber = firstBatch.batch_number
        
        // Auto-select warehouse based on plant prefix
        if (warehouses.value && warehouses.value.length > 0) {
          const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
          if (selectedWarehouse) {
            product.outputWarehouse = selectedWarehouse
          } else if (firstBatch.warehouse) {
            product.outputWarehouse = firstBatch.warehouse
          }
        } else if (firstBatch.warehouse) {
          product.outputWarehouse = firstBatch.warehouse
        }
      } else {
        // Even if no batch found, auto-select warehouse based on plant prefix
        if (warehouses.value && warehouses.value.length > 0) {
          const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
          if (selectedWarehouse) {
            product.outputWarehouse = selectedWarehouse
          }
        }
      }
    } catch (error) {
      console.error(`Error auto-fetching batch number for byproduct ${product.Code}:`, error)
      // Even on error, try to auto-select warehouse
      if (warehouses.value && warehouses.value.length > 0) {
        const selectedWarehouse = autoSelectWarehouse(warehouses.value, prefix)
        if (selectedWarehouse) {
          product.outputWarehouse = selectedWarehouse
        }
      }
    }
  }
}

const openOutputBatchLookup = async () => {
  if (!selectedBOM.value?.Code) {
    alert('Please select a BOM first')
    return
  }
  
  currentBatchLookupItem.value = {
    Code: selectedBOM.value.Code,
    item_code: selectedBOM.value.Code,
    ItemName: selectedBOM.value.Name || selectedBOM.value.ItemName
  }
  // Set both dates to current date by default - only show current date batches
  const today = new Date().toISOString().split('T')[0]
  batchDateItemLookupDateFrom.value = today
  batchDateItemLookupDateTo.value = today
  showBatchDateItemModal.value = true
  batchDateItemResults.value = []
  // Auto-search for current date batches when modal opens
  await searchBatchDateItems()
}

const openByproductBatchLookup = async (product) => {
  if (!product?.Code) {
    alert('Item code not available')
    return
  }
  
  currentBatchLookupItem.value = {
    Code: product.Code,
    item_code: product.Code,
    ItemName: product.ItemName
  }
  // Set both dates to current date by default - only show current date batches
  const today = new Date().toISOString().split('T')[0]
  batchDateItemLookupDateFrom.value = today
  batchDateItemLookupDateTo.value = today
  showBatchDateItemModal.value = true
  batchDateItemResults.value = []
  // Auto-search for current date batches when modal opens
  await searchBatchDateItems()
}

const searchBatchDateItems = async () => {
  if (!currentBatchLookupItem.value?.item_code && !currentBatchLookupItem.value?.Code) {
    return
  }
  
  const itemCode = currentBatchLookupItem.value.item_code || currentBatchLookupItem.value.Code
  const dateFrom = batchDateItemLookupDateFrom.value || null
  const dateTo = batchDateItemLookupDateTo.value || null
  
  try {
    loadingBatchDateItems.value = true
    const response = await productionService.value.getBatchNumbersFromBatchDateItem(itemCode, dateFrom, dateTo)
    
    if (response && response.success && response.data) {
      batchDateItemResults.value = response.data
    } else {
      batchDateItemResults.value = []
    }
  } catch (error) {
    console.error('Error fetching batch numbers from Batch Date Item:', error)
    batchDateItemResults.value = []
  } finally {
    loadingBatchDateItems.value = false
  }
}

const selectBatchDateItem = (batch) => {
  if (currentBatchLookupItem.value === null) return
  
  // Check if this is for Output or Byproduct
  const itemCode = currentBatchLookupItem.value.item_code || currentBatchLookupItem.value.Code
  
  // If it matches the selected BOM Code, update Output
  if (selectedBOM.value && itemCode === selectedBOM.value.Code) {
    outputBatchNumber.value = batch.batch_number
    // Use the batch date from the selected batch, or from date range
    outputBatchDate.value = batchDateItemLookupDateFrom.value || ''
    outputWarehouse.value = batch.warehouse || outputWarehouse.value
  }
  // Otherwise, find matching byproduct
  else {
    const byproduct = byProducts.value.find(p => p.Code === itemCode)
    if (byproduct) {
      byproduct.outputBatchNumber = batch.batch_number
      byproduct.batchDate = batchDateItemLookupDateFrom.value || ''
      byproduct.outputWarehouse = batch.warehouse || byproduct.outputWarehouse
    }
  }
  
  closeBatchDateItemModal()
}

const closeBatchDateItemModal = () => {
  showBatchDateItemModal.value = false
  batchDateItemResults.value = []
  currentBatchLookupItem.value = null
  batchDateItemLookupDateFrom.value = ''
  batchDateItemLookupDateTo.value = ''
}

// Approval Response Modal Functions
const closeApprovalResponseModal = () => {
  showApprovalResponseModal.value = false
  approvalResponseData.value = null
}

// Sidebar Functions
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
  if (showSidebar.value && productionOrders.value.length === 0) {
    fetchProductionOrders()
  }
}

// Production Orders Functions
const fetchProductionOrders = async (page = 1) => {
  try {
    loadingOrders.value = true
    // Build filters with date range if provided
    const filters = { ...currentDateFilters.value }
    
    const response = await productionService.value.getProductionOrdersList(filters, page, 20)
    
    if (response && response.success) {
      productionOrders.value = response.data || []
      ordersPagination.value = {
        page: response.page || page,
        page_size: response.page_size || 20,
        total_pages: response.total_pages || 1,
        total_count: response.total_count || 0
      }
    } else {
      console.error('Failed to fetch production orders:', response?.message)
      productionOrders.value = []
    }
  } catch (error) {
    console.error('Error fetching production orders:', error)
    productionOrders.value = []
  } finally {
    loadingOrders.value = false
  }
}

const applyDateFilter = () => {
  const filters = {}
  
  if (dateFilterFrom.value) {
    filters.date_from = dateFilterFrom.value
  }
  
  if (dateFilterTo.value) {
    filters.date_to = dateFilterTo.value
  }
  
  currentDateFilters.value = filters
  // Reset to first page when applying filter
  ordersPagination.value.page = 1
  fetchProductionOrders(1)
}

const clearDateFilter = () => {
  dateFilterFrom.value = ''
  dateFilterTo.value = ''
  currentDateFilters.value = {}
  // Reset to first page when clearing filter
  ordersPagination.value.page = 1
  fetchProductionOrders(1)
}

const loadOrdersPage = (page) => {
  if (page >= 1 && page <= ordersPagination.value.total_pages) {
    fetchProductionOrders(page)
  }
}

const viewProductionOrder = async (order) => {
  // Check if user wants to resume or just view
  // If order has sap_absoluteentry (production order created), offer to resume
  if (order.sap_absoluteentry) {
    const shouldResume = confirm(`Resume production order ${order.name}?\n\nThis will load the existing production order so you can continue with the next steps (Goods Issue, Goods Receipt, etc.).\n\nClick OK to resume, or Cancel to just view details.`)
    
    if (shouldResume) {
      await resumeProductionOrder(order.name)
      return
    }
  }
  
  // Otherwise, just show details modal
  selectedOrder.value = order
  showOrderDetailsModal.value = true
}

const resumeProductionOrder = async (productionKioskName) => {
  try {
    loading.value = true
    
    // Fetch full production order details
    const response = await productionService.value.getProductionOrderForResume(productionKioskName)
    
    if (!response || !response.success || !response.data) {
      alert(`Failed to load production order: ${response?.message || 'Unknown error'}`)
      return
    }
    
    const orderData = response.data
    const requestPayload = orderData.request_payload
    const responsePayload = orderData.response_payload
    
    if (!requestPayload) {
      alert('Cannot resume: Request payload not found for this production order')
      return
    }
    
    // Restore workflow state
    workflowState.value = orderData.workflow_step || 0
    workflowData.value = {
      productionOrderDocEntry: orderData.sap_absoluteentry ? parseInt(orderData.sap_absoluteentry) : null,
      productionOrderDocNum: orderData.sap_production_number ? parseInt(orderData.sap_production_number) : null,
      productionOrderStatus: orderData.production_order_status || null,
      goodsIssueDocEntry: orderData.issue_for_production_docentry ? parseInt(orderData.issue_for_production_docentry) : null,
      goodsIssueDocNum: null, // Not stored separately, would need to fetch from SAP
      goodsReceiptDocEntry: orderData.receipt_from_production_docentry ? parseInt(orderData.receipt_from_production_docentry) : null,
      goodsReceiptDocNum: null, // Not stored separately, would need to fetch from SAP
      closeDate: orderData.production_order_status === 'boposClosed' ? (orderData.workflow_state?.closeDate || new Date().toISOString().split('T')[0]) : null
    }
    
    // Restore BOM selection and components from request payload
    if (requestPayload.ItemNo) {
      // Search for the BOM to restore selection
      const bomResponse = await nandi_hillsProductionService.searchBOM(requestPayload.ItemNo)
      if (bomResponse.success && bomResponse.data && bomResponse.data.length > 0) {
        // Find exact match or use first result
        const bom = bomResponse.data.find(b => b.Code === requestPayload.ItemNo) || bomResponse.data[0]
        await selectBOM(bom)
        
        // Restore output quantity and warehouse
        if (requestPayload.PlannedQuantity) {
          outputQuantity.value = requestPayload.PlannedQuantity
        }
        if (requestPayload.Warehouse) {
          outputWarehouse.value = requestPayload.Warehouse
        }
        if (requestPayload.PostingDate) {
          outputBatchDate.value = requestPayload.PostingDate
        }
        if (requestPayload.outputBatchNumber) {
          outputBatchNumber.value = requestPayload.outputBatchNumber
        }
        
        // Wait a bit for ITT1 components to load
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // Restore production order lines (components)
        if (requestPayload.ProductionOrderLines && Array.isArray(requestPayload.ProductionOrderLines)) {
          // Map production order lines back to components
          requestPayload.ProductionOrderLines.forEach(line => {
            if (line.PlannedQuantity > 0) {
              // Input component
              const comp = itt1Components.value.find(c => c.Code === line.ItemNo)
              if (comp) {
                comp.inputQuantity = line.PlannedQuantity
                comp.warehouse = line.Warehouse || comp.warehouse
                
                // Restore batch numbers - prioritize selectedBatches
                if (line.selectedBatches && Array.isArray(line.selectedBatches) && line.selectedBatches.length > 0) {
                  comp.selectedBatches = line.selectedBatches
                  // Update batchNumber display
                  if (line.selectedBatches.length === 1) {
                    comp.batchNumber = line.selectedBatches[0].BatchNumber
                  } else {
                    comp.batchNumber = `${line.selectedBatches.length} batches selected`
                  }
                } else if (line.BatchNumber) {
                  comp.batchNumber = line.BatchNumber
                  // Try to create a selectedBatches entry for single batch
                  comp.selectedBatches = [{
                    BatchNumber: line.BatchNumber,
                    Warehouse: line.Warehouse || comp.warehouse,
                    AvailableQty: comp.inputQuantity,
                    inputQuantity: comp.inputQuantity
                  }]
                }
              }
            } else {
              // Byproduct (negative quantity)
              const byproduct = byProducts.value.find(p => p.Code === line.ItemNo)
              if (byproduct) {
                byproduct.outputQuantity = Math.abs(line.PlannedQuantity).toString()
                byproduct.outputWarehouse = line.Warehouse || byproduct.outputWarehouse
                if (line.outputBatchNumber || line.BatchNumber) {
                  byproduct.outputBatchNumber = line.outputBatchNumber || line.BatchNumber
                }
              }
            }
          })
        }
      }
    }
    
    // Close sidebar
    showSidebar.value = false
    
    // Show success message
    alert(`✅ Production order ${productionKioskName} loaded successfully!\n\nYou can now continue with the next steps.`)
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
    
  } catch (error) {
    console.error('Error resuming production order:', error)
    alert(`❌ Error loading production order: ${error.message || 'Unknown error'}`)
  } finally {
    loading.value = false
  }
}

const closeOrderDetailsModal = () => {
  showOrderDetailsModal.value = false
  selectedOrder.value = null
}

// Utility Functions
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    // Handle YYYY-MM-DD format (PostingDate from SAP)
    let date
    if (typeof dateString === 'string' && dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      // It's a date-only string, add time for proper parsing
      date = new Date(dateString + 'T00:00:00')
    } else {
      date = new Date(dateString)
    }
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return dateString
    }
    
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

const formatJSON = (jsonString) => {
  if (!jsonString) return 'N/A'
  try {
    const parsed = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString
    return JSON.stringify(parsed, null, 2)
  } catch (e) {
    return jsonString
  }
}

onMounted(() => {
  // Fetch warehouses when component mounts
  fetchWarehouses()
  // Optionally fetch production orders on mount
  // fetchProductionOrders()
})
</script>

<style scoped>
/* Additional styles if needed */
</style>
