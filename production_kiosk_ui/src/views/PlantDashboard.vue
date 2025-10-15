<template>
  <div class="kiosk-container">
    <!-- Header -->
    <header class="kiosk-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div 
            class="h-12 w-12 rounded-lg flex items-center justify-center"
            :style="{ backgroundColor: plantData.color + '20' }"
          >
            <span 
              class="font-bold text-sm"
              :style="{ color: plantData.color }"
            >
              {{ plantData.name.charAt(0) }}{{ plantData.name.split(' ')[1]?.charAt(0) || '' }}
            </span>
          </div>
          <div>
            <h1 class="text-2xl font-bold">{{ plantData.name }}</h1>
            <p class="text-sm opacity-90">Production Dashboard</p>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="text-sm">
            <span class="opacity-90">Welcome,</span>
            <span class="font-semibold ml-1">{{ user?.username || 'User' }}</span>
          </div>
          <button
            @click="logout"
            class="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="kiosk-main">
      <div class="max-w-7xl mx-auto">
        <!-- Navigation Tabs -->
        <div class="mb-8">
          <nav class="flex space-x-8 border-b border-gray-200">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              :class="[
                'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              {{ tab.label }}
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- Dashboard Tab -->
          <div v-if="activeTab === 'dashboard'" class="space-y-8">
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div
                v-for="stat in stats"
                :key="stat.key"
                class="stats-card"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-600">{{ stat.label }}</p>
                    <p class="text-3xl font-bold text-gray-900">{{ stat.value }}</p>
                    <p 
                      v-if="stat.change"
                      :class="[
                        'text-sm',
                        stat.change.direction === 'up' ? 'text-green-600' : 
                        stat.change.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                      ]"
                    >
                      {{ stat.change.direction === 'up' ? '↗' : stat.change.direction === 'down' ? '↘' : '→' }}
                      {{ stat.change.percentage }}% from last period
                    </p>
                  </div>
                  <div 
                    class="p-3 rounded-full"
                    :style="{ backgroundColor: stat.color + '20' }"
                  >
                    <component 
                      :is="stat.icon" 
                      class="h-6 w-6"
                      :style="{ color: stat.color }"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Charts Row -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div class="chart-container">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Production Trend</h3>
                <div class="h-64 flex items-center justify-center text-gray-500">
                  <p>Chart component will be loaded here</p>
                </div>
              </div>
              
              <div class="chart-container">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Efficiency Metrics</h3>
                <div class="h-64 flex items-center justify-center text-gray-500">
                  <p>Chart component will be loaded here</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Production Tab -->
          <div v-if="activeTab === 'production'" class="space-y-8">
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Production Details</h3>
              <div class="text-gray-500">
                <p>Production page content will be loaded here</p>
              </div>
            </div>
          </div>

          <!-- Reports Tab -->
          <div v-if="activeTab === 'reports'" class="space-y-8">
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Reports</h3>
              <div class="text-gray-500">
                <p>Reports page content will be loaded here</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="loading-spinner"></div>
          <span class="ml-3 text-gray-600">Loading data...</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/index.js'
import { PLANT_ENDPOINTS } from '@/api/constants.js'
import { getPlantColorScheme } from '@/utils/helpers.js'

export default {
  name: 'PlantDashboard',
  props: {
    plantName: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()
    
    const loading = ref(false)
    const activeTab = ref('dashboard')
    
    const plantName = computed(() => props.plantName || route.params.plantName)
    const plantData = computed(() => PLANT_ENDPOINTS[plantName.value] || {})
    const user = computed(() => authStore.user)
    const colorScheme = computed(() => getPlantColorScheme(plantName.value))

    const tabs = [
      { key: 'dashboard', label: 'Dashboard' },
      { key: 'production', label: 'Production' },
      { key: 'reports', label: 'Reports' }
    ]

    const stats = ref([
      {
        key: 'totalProduction',
        label: 'Total Production',
        value: '1,234',
        change: { percentage: 12.5, direction: 'up' },
        color: colorScheme.value.primary,
        icon: 'div' // Placeholder for icon component
      },
      {
        key: 'efficiency',
        label: 'Efficiency',
        value: '87.3%',
        change: { percentage: 2.1, direction: 'up' },
        color: '#10B981',
        icon: 'div'
      },
      {
        key: 'activeLines',
        label: 'Active Lines',
        value: '8/10',
        change: { percentage: 0, direction: 'neutral' },
        color: '#F59E0B',
        icon: 'div'
      },
      {
        key: 'quality',
        label: 'Quality Score',
        value: '94.2%',
        change: { percentage: 1.8, direction: 'up' },
        color: '#8B5CF6',
        icon: 'div'
      }
    ])

    const logout = () => {
      authStore.logout()
      router.push('/')
    }

    const loadData = async () => {
      loading.value = true
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        loading.value = false
      } catch (error) {
        console.error('Failed to load data:', error)
        loading.value = false
      }
    }

    onMounted(() => {
      // Check if user is logged in
      if (!authStore.checkLogin(plantName.value)) {
        router.push(`/login/${plantName.value}`)
        return
      }
      
      loadData()
    })

    return {
      plantData,
      user,
      loading,
      activeTab,
      tabs,
      stats,
      logout
    }
  }
}
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
