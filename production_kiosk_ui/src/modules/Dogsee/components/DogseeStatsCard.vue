<template>
  <div class="stats-card dogsee-stats">
    <div class="flex items-center justify-between">
      <div class="flex-1">
        <p class="text-sm font-medium text-gray-600 mb-1">{{ title }}</p>
        <p class="text-2xl font-bold text-gray-900 mb-2">{{ value }}</p>
        <div v-if="change" class="flex items-center">
          <span 
            :class="[
              'text-sm font-medium',
              change.direction === 'up' ? 'text-green-600' : 
              change.direction === 'down' ? 'text-red-600' : 'text-gray-600'
            ]"
          >
            <span v-if="change.direction === 'up'">↗</span>
            <span v-else-if="change.direction === 'down'">↘</span>
            <span v-else>→</span>
            {{ change.percentage }}%
          </span>
          <span class="text-sm text-gray-500 ml-1">vs last period</span>
        </div>
      </div>
      <div 
        class="p-3 rounded-full flex-shrink-0"
        :style="{ backgroundColor: color + '20' }"
      >
        <div 
          class="w-6 h-6 rounded-full flex items-center justify-center"
          :style="{ backgroundColor: color }"
        >
          <span class="text-white text-xs font-bold">{{ icon.charAt(0).toUpperCase() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DogseeStatsCard',
  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: String,
      required: true
    },
    change: {
      type: Object,
      default: null
    },
    color: {
      type: String,
      default: '#059669'
    },
    icon: {
      type: String,
      default: 'metric'
    }
  }
}
</script>

<style scoped>
.stats-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.dogsee-stats {
  border-left: 4px solid #059669;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
</style>
