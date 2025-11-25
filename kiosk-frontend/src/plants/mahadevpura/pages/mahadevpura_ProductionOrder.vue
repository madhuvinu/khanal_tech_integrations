<!--
  Mahadevpura Plant-Specific Production Order Component
  
  This component can be used to add plant-specific customizations.
  Currently, it just uses the shared component.
  
  To add customizations:
  1. Copy the template from @/app/pages/ProductionOrder.vue
  2. Modify sections as needed for Mahadevpura
  3. Add plant-specific logic in the script section
  
  If you don't need any customizations, you can delete this file and the router
  will automatically use the shared component from @/app/pages/ProductionOrder.vue
-->

<script setup>
// Import the shared ProductionOrder component
import SharedProductionOrder from '@/app/pages/ProductionOrder.vue'

// You can add plant-specific logic here
// For example:
// - Custom validation rules
// - Additional fields
// - Plant-specific API calls
// - Custom UI elements
// - Override methods from shared component
</script>

<template>
  <!-- Use the shared component directly -->
  <SharedProductionOrder />
  
  <!-- 
    To add plant-specific UI, you can:
    1. Copy the entire template from SharedProductionOrder
    2. Modify specific sections
    3. Add new sections below
  -->
  
  <!-- Example: Plant-specific section (uncomment to use) -->
  <!--
  <div class="mahadevpura-specific-section mt-6 p-4 bg-blue-50 rounded-lg">
    <h2 class="text-xl font-bold text-blue-700 mb-2">Mahadevpura Specific Features</h2>
    <p>Add plant-specific content here</p>
  </div>
  -->
</template>

<style scoped>
/* Add plant-specific styles here if needed */
.mahadevpura-specific-section {
  /* Custom styles for Mahadevpura */
}
</style>
