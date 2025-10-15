<template>
  <div class="side-panel">
    <!-- Panel Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
      <p v-if="subtitle" class="text-sm text-gray-600 mt-1">{{ subtitle }}</p>
    </div>

    <!-- Panel Content -->
    <div class="p-6">
      <slot>
        <!-- Default content if no slot provided -->
        <div class="text-center text-gray-500 py-8">
          <p>No content available</p>
        </div>
      </slot>
    </div>

    <!-- Panel Footer (optional) -->
    <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-200 bg-gray-50">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SidePanel',
  props: {
    title: {
      type: String,
      required: true
    },
    subtitle: {
      type: String,
      default: null
    }
  }
}
</script>

<style scoped>
.side-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
</style>
