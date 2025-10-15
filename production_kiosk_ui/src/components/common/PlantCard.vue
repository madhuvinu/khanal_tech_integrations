<template>
  <div 
    class="plant-card"
    :class="`plant-${plantKey.toLowerCase()}`"
    @click="$emit('select-plant', plantKey)"
  >
    <div class="p-6">
      <!-- Plant Logo -->
      <div class="flex items-center justify-center mb-4">
        <div 
          class="h-16 w-16 rounded-lg flex items-center justify-center"
          :style="{ backgroundColor: plantData.color + '20' }"
        >
          <span 
            class="font-bold text-lg"
            :style="{ color: plantData.color }"
          >
            {{ plantData.name.charAt(0) }}{{ plantData.name.split(' ')[1]?.charAt(0) || '' }}
          </span>
        </div>
      </div>

      <!-- Plant Name -->
      <h3 class="text-xl font-semibold text-gray-900 text-center mb-2">
        {{ plantData.name }}
      </h3>

      <!-- Plant Status -->
      <div class="flex items-center justify-center mb-4">
        <div 
          class="w-3 h-3 rounded-full mr-2"
          :style="{ backgroundColor: plantData.color }"
        ></div>
        <span class="text-sm text-gray-600">Online</span>
      </div>

      <!-- Plant Info -->
      <div class="space-y-2 text-sm text-gray-600">
        <div class="flex justify-between">
          <span>Status:</span>
          <span class="font-medium text-green-600">Active</span>
        </div>
        <div class="flex justify-between">
          <span>Last Update:</span>
          <span class="font-medium">2 min ago</span>
        </div>
      </div>

      <!-- Action Button -->
      <div class="mt-6">
        <button 
          class="w-full py-2 px-4 rounded-lg font-medium transition-colors"
          :style="{
            backgroundColor: plantData.color,
            color: 'white'
          }"
          @click.stop="$emit('select-plant', plantKey)"
        >
          Access Dashboard
        </button>
      </div>
    </div>

    <!-- Hover Effect Overlay -->
    <div class="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-5 transition-all duration-300 rounded-lg"></div>
  </div>
</template>

<script>
export default {
  name: 'PlantCard',
  props: {
    plantKey: {
      type: String,
      required: true
    },
    plantData: {
      type: Object,
      required: true
    }
  },
  emits: ['select-plant']
}
</script>

<style scoped>
.plant-card {
  position: relative;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.plant-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

/* Plant-specific styling */
.plant-nandhihills {
  border-top: 4px solid #4F46E5;
}

.plant-dogsee {
  border-top: 4px solid #059669;
}

.plant-mallur {
  border-top: 4px solid #DC2626;
}

.plant-champawath {
  border-top: 4px solid #7C3AED;
}

.plant-krishnagiri {
  border-top: 4px solid #EA580C;
}
</style>
