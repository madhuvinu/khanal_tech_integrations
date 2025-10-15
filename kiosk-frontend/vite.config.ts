import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/kiosk/',
  plugins: [
    vue({
      script: {
        propsDestructure: true,
      },
    }),
    vueJsx(),
    VitePWA({
      registerType: "autoUpdate",
      devOptions: {
        enabled: true,
      },
      manifest: {
        display: "fullscreen",
        name: "Khanal Foods Kiosk",
        short_name: "KFL Kiosk",
        start_url: "/kiosk",
        description: "Production Kiosk Tool for Khanal Foods",
        orientation: "landscape",
        theme_color: "#1f2937",
        background_color: "#ffffff",
        icons: [
          {
            src: "/assets/khanal_tech_integrations/assets/img/favicons/android-chrome-192x192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/assets/khanal_tech_integrations/assets/img/favicons/android-chrome-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/assets/khanal_tech_integrations/assets/img/favicons/apple-touch-icon.png",
            sizes: "180x180",
            type: "image/png",
            purpose: "any",
          }
        ],
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 3000000, // 3MB
        globPatterns: [
          '**/*.{js,css,html,ico,png,jpg,jpeg,svg,woff,woff2}'
        ]
      }
    }),
    {
      name: "transform-index.html",
      transformIndexHtml(html, context) {
        if (!context.server) {
          return html.replace(
            /<\/body>/,
            `
            <script>
                {% for key in boot %}
                window["{{ key }}"] = {{ boot[key] | tojson }};
                {% endfor %}
            </script>
            </body>
            `
          );
        }
        return html;
      },
    },
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: "../khanal_tech_integrations/www/kiosk",
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['lucide-vue-next'],
          'axios-vendor': ['axios']
        }
      }
    },
    cssCodeSplit: true,
    // Optimize CSS
    cssMinify: 'esbuild',
    // Improve build performance
    chunkSizeWarningLimit: 1000,
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
  },
  optimizeDeps: {
    include: [
      "feather-icons",
      "tailwind.config.js",
      "engine.io-client",
      "qrcode",
      "axios",
    ],
  },
  server: {
    port: 8081,
    host: true, // Listen on all addresses
    cors: true,
    hmr: {
      overlay: false
    }
  },
  preview: {
    port: 8081,
    host: true, // Listen on all addresses
  },
})