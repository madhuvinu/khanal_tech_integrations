<template>
  <div class="mallur-dashboard">
    <!-- Plant Header -->
    <div class="mb-8">
      <div class="flex items-center space-x-4 mb-4">
        <div class="h-16 w-16 bg-red-100 rounded-lg flex items-center justify-center">
          <span class="text-red-600 font-bold text-lg">ML</span>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Mallur Plant</h1>
          <p class="text-gray-600">Real-time production monitoring and analytics</p>
        </div>
      </div>
    </div>

    <!-- Key Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <MallurStatsCard
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
        <MallurChart
          :data="productionData"
          :type="'line'"
          :options="chartOptions.line"
        />
      </div>
      
      <div class="chart-container">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Efficiency by Line</h3>
        <MallurChart
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
import MallurStatsCard from './components/MallurStatsCard.vue'
import MallurChart from './components/MallurChart.vue'
import { mallurAPI } from './api/index.js'

export default {
  name: 'MallurDashboard',
  components: {
    MallurStatsCard,
    MallurChart
  },
  setup() {
    const keyMetrics = ref([
      {
        key: 'totalProduction',
        title: 'Total Production',
        value: '3,456 units',
        change: { percentage: 15.2, direction: 'up' },
        color: '#DC2626',
        icon: 'production'
      },
      {
        key: 'efficiency',
        title: 'Overall Efficiency',
        value: '89.7%',
        change: { percentage: 4.1, direction: 'up' },
        color: '#10B981',
        icon: 'efficiency'
      },
      {
        key: 'activeLines',
        title: 'Active Lines',
        value: '7/9',
        change: { percentage: 0, direction: 'neutral' },
        color: '#F59E0B',
        icon: 'lines'
      },
      {
        key: 'quality',
        title: 'Quality Score',
        value: '92.5%',
        change: { percentage: 2.3, direction: 'up' },
        color: '#8B5CF6',
        icon: 'quality'
      }
    ])

    const productionData = ref({
      labels: ['6 AM', '8 AM', '10 AM', '12 PM', '2 PM', '4 PM', '6 PM'],
      datasets: [{
        label: 'Production (units)',
        data: [200, 280, 350, 520, 400, 480, 420],
        borderColor: '#DC2626',
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        tension: 0.4
      }]
    })

    const efficiencyData = ref({
      labels: ['Line 1', 'Line 2', 'Line 3', 'Line 4', 'Line 5', 'Line 6', 'Line 7'],
      datasets: [{
        label: 'Efficiency %',
        data: [85, 92, 78, 88, 95, 82, 90],
        backgroundColor: ['#DC2626', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16']
      }]
    })

    const productionLines = ref([
      { id: 1, name: 'Line 1', status: 'active', output: 200, efficiency: 85 },
      { id: 2, name: 'Line 2', status: 'active', output: 215, efficiency: 92 },
      { id: 3, name: 'Line 3', status: 'maintenance', output: 0, efficiency: 78 },
      { id: 4, name: 'Line 4', status: 'active', output: 195, efficiency: 88 },
      { id: 5, name: 'Line 5', status: 'active', output: 220, efficiency: 95 },
      { id: 6, name: 'Line 6', status: 'active', output: 185, efficiency: 82 },
      { id: 7, name: 'Line 7', status: 'active', output: 210, efficiency: 90 }
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
        const data = await mallurAPI.getDashboardData()
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
.mallur-dashboard {
  /* Plant-specific styles */
}
</style>
