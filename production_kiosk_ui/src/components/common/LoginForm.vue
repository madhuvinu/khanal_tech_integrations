<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <!-- Username Field -->
    <div>
      <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
        Username
      </label>
      <input
        id="username"
        v-model="form.username"
        type="text"
        required
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        placeholder="Enter your username"
        :disabled="loading"
      />
    </div>

    <!-- Password Field -->
    <div>
      <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
        Password
      </label>
      <div class="relative">
        <input
          id="password"
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          required
          class="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter your password"
          :disabled="loading"
        />
        <button
          type="button"
          @click="togglePasswordVisibility"
          class="absolute inset-y-0 right-0 pr-3 flex items-center"
          :disabled="loading"
        >
          <svg
            v-if="showPassword"
            class="h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
            />
          </svg>
          <svg
            v-else
            class="h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Remember Me -->
    <div class="flex items-center">
      <input
        id="remember"
        v-model="form.remember"
        type="checkbox"
        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        :disabled="loading"
      />
      <label for="remember" class="ml-2 block text-sm text-gray-700">
        Remember me
      </label>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex">
        <svg class="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div class="ml-3">
          <p class="text-sm text-red-800">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Submit Button -->
    <button
      type="submit"
      :disabled="loading || !form.username || !form.password"
      class="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <span v-if="loading" class="flex items-center">
        <div class="loading-spinner mr-2"></div>
        Signing in...
      </span>
      <span v-else>Sign In</span>
    </button>

    <!-- Back Button -->
    <button
      type="button"
      @click="$emit('back')"
      :disabled="loading"
      class="w-full py-2 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      ← Back to Plant Selection
    </button>
  </form>
</template>

<script>
import { ref, reactive } from 'vue'

export default {
  name: 'LoginForm',
  props: {
    plantName: {
      type: String,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  emits: ['login', 'back'],
  setup(props, { emit }) {
    const showPassword = ref(false)
    
    const form = reactive({
      username: '',
      password: '',
      remember: false
    })

    const togglePasswordVisibility = () => {
      showPassword.value = !showPassword.value
    }

    const handleSubmit = () => {
      if (!form.username || !form.password) {
        return
      }
      
      emit('login', {
        username: form.username,
        password: form.password,
        remember: form.remember,
        plant: props.plantName
      })
    }

    return {
      form,
      showPassword,
      togglePasswordVisibility,
      handleSubmit
    }
  }
}
</script>

<style scoped>
/* Additional component-specific styles if needed */
</style>
