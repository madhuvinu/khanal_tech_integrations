<template>
  <div class="login-container">
    <div class="login-form">
      <!-- Plant Header -->
      <div class="text-center mb-8">
        <div 
          class="h-16 w-16 mx-auto mb-4 rounded-lg flex items-center justify-center"
          :style="{ backgroundColor: plantData.color + '20' }"
        >
          <span 
            class="font-bold text-lg"
            :style="{ color: plantData.color }"
          >
            {{ plantData.name.charAt(0) }}{{ plantData.name.split(' ')[1]?.charAt(0) || '' }}
          </span>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
          {{ plantData.name }}
        </h1>
        <p class="text-gray-600">
          Enter your credentials to access production data
        </p>
      </div>

      <!-- Login Form -->
      <LoginForm
        :plant-name="plantName"
        :loading="loading"
        :error="error"
        @login="handleLogin"
        @back="goBack"
      />

      <!-- Footer -->
      <div class="mt-8 text-center text-sm text-gray-500">
        <p>Production Kiosk System</p>
        <p>Khanal Tech Integrations</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/index.js'
import { PLANT_ENDPOINTS } from '@/api/constants.js'
import LoginForm from '@/components/common/LoginForm.vue'

export default {
  name: 'LoginPage',
  components: {
    LoginForm
  },
  props: {
    plant: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()
    
    const loading = ref(false)
    const error = ref(null)
    
    const plantName = computed(() => props.plant || route.params.plant)
    const plantData = computed(() => PLANT_ENDPOINTS[plantName.value] || {})

    const handleLogin = async (credentials) => {
      loading.value = true
      error.value = null

      try {
        // Simulate login API call
        await new Promise(resolve => setTimeout(resolve, 1500))
        
        // In a real implementation, you would call the actual login API
        // const response = await authAPI.login(credentials.username, credentials.password)
        
        // For demo purposes, accept any non-empty credentials
        if (credentials.username && credentials.password) {
          const userData = {
            username: credentials.username,
            plant: plantName.value,
            loginTime: new Date().toISOString()
          }
          
          authStore.login(plantName.value, userData)
          router.push(`/plant/${plantName.value}`)
        } else {
          throw new Error('Please enter both username and password')
        }
      } catch (err) {
        error.value = err.message || 'Login failed. Please check your credentials.'
      } finally {
        loading.value = false
      }
    }

    const goBack = () => {
      router.push('/')
    }

    onMounted(() => {
      // Check if already logged in
      if (authStore.checkLogin(plantName.value)) {
        router.push(`/plant/${plantName.value}`)
      }
    })

    return {
      plantName,
      plantData,
      loading,
      error,
      handleLogin,
      goBack
    }
  }
}
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
