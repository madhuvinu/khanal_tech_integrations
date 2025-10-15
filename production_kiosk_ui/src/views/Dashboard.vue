<template>
  <div class="kiosk-container">
    <!-- Header -->
    <header class="kiosk-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="text-blue-600 font-bold text-sm">KT</span>
          </div>
          <h1 class="text-2xl font-bold">Production Kiosk</h1>
        </div>
        <div class="text-sm opacity-90">
          Select a plant to view production data
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="kiosk-main">
      <div class="max-w-7xl mx-auto">
        <!-- Welcome Section -->
        <div class="text-center mb-12">
          <h2 class="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Production Kiosk
          </h2>
          <p class="text-xl text-gray-600 max-w-2xl mx-auto">
            Select a plant below to access real-time production data, reports, and analytics
          </p>
        </div>

        <!-- Plants Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <PlantCard
            v-for="(plant, key) in plants"
            :key="key"
            :plant-key="key"
            :plant-data="plant"
            @select-plant="selectPlant"
          />
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="loading-spinner"></div>
          <span class="ml-3 text-gray-600">Loading plants...</span>
        </div>

        <!-- Error State -->
        <div v-if="error" class="text-center py-12">
          <div class="text-red-600 text-lg mb-4">
            {{ error }}
          </div>
          <button 
            @click="loadPlants"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PLANT_ENDPOINTS } from '@/api/constants.js'
import PlantCard from '@/components/common/PlantCard.vue'

export default {
  name: 'Dashboard',
  components: {
    PlantCard
  },
  setup() {
    const router = useRouter()
    const plants = ref(PLANT_ENDPOINTS)
    const loading = ref(false)
    const error = ref(null)

    const selectPlant = (plantKey) => {
      // Navigate to login page for the selected plant
      router.push(`/login/${plantKey}`)
    }

    const loadPlants = async () => {
      loading.value = true
      error.value = null
      
      try {
        // In a real implementation, you might fetch plant status from API
        // For now, we'll use the static plant data
        await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate API call
        loading.value = false
      } catch (err) {
        error.value = 'Failed to load plants. Please try again.'
        loading.value = false
      }
    }

    onMounted(() => {
      loadPlants()
    })

    return {
      plants,
      loading,
      error,
      selectPlant,
      loadPlants
    }
  }
}
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
