import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  base: '/assets/khanal_tech_integrations/production_kiosk_ui/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          charts: ['chart.js', 'vue-chartjs']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: process.env.VITE_API_TARGET ? {
      '/api': {
        target: process.env.VITE_API_TARGET,
        changeOrigin: true,
        secure: false
      }
    } : {}
  }
})
