<template>
  <div class="chart-wrapper">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js'

// Register Chart.js components
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

export default {
  name: 'PlantChart',
  props: {
    data: {
      type: Object,
      required: true
    },
    type: {
      type: String,
      default: 'line',
      validator: (value) => ['line', 'bar', 'doughnut', 'pie'].includes(value)
    },
    options: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const chartCanvas = ref(null)
    let chartInstance = null

    const createChart = () => {
      if (!chartCanvas.value) return

      const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            enabled: true
          }
        },
        scales: props.type === 'line' || props.type === 'bar' ? {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          },
          x: {
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          }
        } : {}
      }

      const mergedOptions = {
        ...defaultOptions,
        ...props.options
      }

      chartInstance = new Chart(chartCanvas.value, {
        type: props.type,
        data: props.data,
        options: mergedOptions
      })
    }

    const updateChart = () => {
      if (chartInstance) {
        chartInstance.data = props.data
        chartInstance.update()
      }
    }

    const destroyChart = () => {
      if (chartInstance) {
        chartInstance.destroy()
        chartInstance = null
      }
    }

    onMounted(() => {
      createChart()
    })

    onUnmounted(() => {
      destroyChart()
    })

    watch(() => props.data, updateChart, { deep: true })
    watch(() => props.type, () => {
      destroyChart()
      createChart()
    })

    return {
      chartCanvas
    }
  }
}
</script>

<style scoped>
.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}
</style>
