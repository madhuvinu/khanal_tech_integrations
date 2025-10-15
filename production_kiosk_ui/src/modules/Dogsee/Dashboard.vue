<template>
  <div class="dogsee-dashboard">
    <!-- Plant Header -->
    <div class="mb-8">
      <div class="flex items-center space-x-4 mb-4">
        <div class="h-16 w-16 bg-green-100 rounded-lg flex items-center justify-center">
          <span class="text-green-600 font-bold text-lg">DS</span>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Dogsee Plant</h1>
          <p class="text-gray-600">Real-time production monitoring and analytics</p>
        </div>
      </div>
    </div>

    <!-- Key Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <DogseeStatsCard
        v-for="stat in keyMetrics"
        :key="stat.key"
        :title="stat.title"
        :value="stat.value"
        :change="stat.change"
        :color="stat.color"
        :icon="stat.icon"
      />
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
      <div class="chart-container">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Production Trend</h3>
        <DogseeChart
          :data="productionData"
          :type="'line'"
          :options="chartOptions.line"
        />
      </div>
      
      <div class="chart-container">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Efficiency by Line</h3>
        <DogseeChart
          :data="efficiencyData"
          :type="'bar'"
          :options="chartOptions.bar"
        />
      </div>
    </div>

    <!-- Production Lines Status -->
    <div class="chart-container">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Production Lines Status</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="line in productionLines"
          :key="line.id"
          class="p-4 border border-gray-200 rounded-lg"
        >
          <div class="flex items-center justify-between mb-2">
            <h4 class="font-medium text-gray-900">{{ line.name }}</h4>
            <span 
              :class="[
                'px-2 py-1 text-xs font-medium rounded-full',
                line.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              ]"
            >
              {{ line.status }}
            </span>
          </div>
          <div class="text-sm text-gray-600">
            <p>Output: {{ line.output }} units/hr</p>
            <p>Efficiency: {{ line.efficiency }}%</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import DogseeStatsCard from './components/DogseeStatsCard.vue'
import DogseeChart from './components/DogseeChart.vue'
import { dogseeAPI } from './api/index.js'

export default {
  name: 'DogseeDashboard',
  components: {
    DogseeStatsCard,
    DogseeChart
  },
  setup() {
    const keyMetrics = ref([
      {
        key: 'totalProduction',
        title: 'Total Production',
        value: '2,156 units',
        change: { percentage: 8.3, direction: 'up' },
        color: '#059669',
        icon: 'production'
      },
      {
        key: 'efficiency',
        title: 'Overall Efficiency',
        value: '91.2%',
        change: { percentage: 3.4, direction: 'up' },
        color: '#10B981',
        icon: 'efficiency'
      },
      {
        key: 'activeLines',
        title: 'Active Lines',
        value: '6/8',
        change: { percentage: 0, direction: 'neutral' },
        color: '#F59E0B',
        icon: 'lines'
      },
      {
        key: 'quality',
        title: 'Quality Score',
        value: '96.8%',
        change: { percentage: 0.5, direction: 'up' },
        color: '#8B5CF6',
        icon: 'quality'
      }
    ])

    const productionData = ref({
      labels: ['6 AM', '8 AM', '10 AM', '12 PM', '2 PM', '4 PM', '6 PM'],
      datasets: [{
        label: 'Production (units)',
        data: [180, 250, 320, 480, 350, 420, 380],
        borderColor: '#059669',
        backgroundColor: 'rgba(5, 150, 105, 0.1)',
        tension: 0.4
      }]
    })

    const efficiencyData = ref({
      labels: ['Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5', 'Line 6'],
      datasets: [{
        label: 'Efficiency %',
        data: [88, 94, 85, 92, 89, 96],
        backgroundColor: ['#059669', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
      }]
    })

    const productionLines = ref([
      { id: 1, name: 'Line 1', status: 'active', output: 180, efficiency: 88 },
      { id: 2, name: 'Line 2', status: 'active', output: 195, efficiency: 94 },
      { id: 3, name: 'Line 3', status: 'active', output: 165, efficiency: 85 },
      { id: 4, name: 'Line 4', status: 'maintenance', output: 0, efficiency: 92 },
      { id: 5, name: 'Line 5', status: 'active', output: 175, efficiency: 89 },
      { id: 6, name: 'Line 6', status: 'active', output: 200, efficiency: 96 }
    ])

    const chartOptions = {
      line: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        }
      },
      bar: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        }
      }
    }

    const loadData = async () => {
      try {
        const data = await dogseeAPI.getDashboardData()
        // Update reactive data with API response
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      }
    }

    onMounted(() => {
      loadData()
    })

    return {
      keyMetrics,
      productionData,
      efficiencyData,
      productionLines,
      chartOptions
    }
  }
}
</script>

<style scoped>
.dogsee-dashboard {
  /* Plant-specific styles */
}
</style>
