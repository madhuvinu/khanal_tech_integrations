/**
 * Main Router Configuration
 * Handles plant-specific routing with authentication guards
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from './core/stores/session.js'
import { APP_CONFIG } from '@/config/constants.js'

// Import pages
import Login from './app/pages/Login.vue'
import NotFound from './app/pages/NotFound.vue'
import Unauthorized from './app/pages/Unauthorized.vue'
import PlantFeature from './app/pages/PlantFeature.vue'
import ResetPassword from './app/pages/ResetPassword.vue'

// Plant-specific layouts (lazy loaded)
const MahadevpuraLayout = () => import('./plants/mahadevpura/layouts/PlantLayout.vue')
const NandiHillsLayout = () => import('./plants/nandi-hills/layouts/PlantLayout.vue')
const MalurLayout = () => import('./plants/malur/layouts/PlantLayout.vue')
const KrishnagiriLayout = () => import('./plants/krishnagiri/layouts/PlantLayout.vue')
const ChampavathLayout = () => import('./plants/champavath/layouts/PlantLayout.vue')

// Plant-specific pages (lazy loaded)
const MahadevpuraDashboard = () => import('./plants/mahadevpura/pages/Dashboard.vue')
const MahadevpuraGRN = () => import('./plants/mahadevpura/pages/GRN.vue')
const MahadevpuraProductionOrder = () => import('./plants/mahadevpura/pages/ProductionOrder.vue')
const MahadevpuraQuality = () => import('./plants/mahadevpura/pages/Quality.vue')
const MahadevpuraInventoryTransfer = () => import('./plants/mahadevpura/pages/InventoryTransfer.vue')

const NandiHillsDashboard = () => import('./plants/nandi-hills/pages/Dashboard.vue')
const NandiHillsGRN = () => import('./plants/nandi-hills/pages/GRN.vue')
const NandiHillsProductionOrder = () => import('./plants/nandi-hills/pages/ProductionOrder.vue')
const NandiHillsQuality = () => import('./plants/nandi-hills/pages/Quality.vue')
const NandiHillsInventoryTransfer = () => import('./plants/nandi-hills/pages/InventoryTransfer.vue')
const NandiHillsDisassembly = () => import('./plants/nandi-hills/pages/Disassembly.vue')

const MalurDashboard = () => import('./plants/malur/pages/Dashboard.vue')
const MalurGRN = () => import('./plants/malur/pages/GRN.vue')
const MalurProductionOrder = () => import('./plants/malur/pages/ProductionOrder.vue')
const MalurInventoryTransfer = () => import('./plants/malur/pages/InventoryTransfer.vue')

const KrishnagiriDashboard = () => import('./plants/krishnagiri/pages/Dashboard.vue')
const KrishnagiriGRN = () => import('./plants/krishnagiri/pages/GRN.vue')
const KrishnagiriProductionOrder = () => import('./plants/krishnagiri/pages/ProductionOrder.vue')
const KrishnagiriQuality = () => import('./plants/krishnagiri/pages/Quality.vue')
const KrishnagiriInventoryTransfer = () => import('./plants/krishnagiri/pages/InventoryTransfer.vue')

const ChampavathDashboard = () => import('./plants/champavath/pages/Dashboard.vue')
const ChampavathGRN = () => import('./plants/champavath/pages/GRN.vue')
const ChampavathProductionOrder = () => import('./plants/champavath/pages/ProductionOrder.vue')
const ChampavathInventoryTransfer = () => import('./plants/champavath/pages/InventoryTransfer.vue')

const routes = [
  // Root redirect
  {
    path: '/',
    redirect: '/login',
    name: 'Root'
  },


  // Plant-specific Login
  {
    path: '/login/:plantId',
    name: 'Login',
    component: Login,
    meta: {
      title: 'Login',
      requiresAuth: false,
      layout: 'public'
    }
  },

  // Generic Login (with plant dropdown)
  {
    path: '/login',
    name: 'LoginGeneric',
    component: Login,
    meta: {
      title: 'Login',
      requiresAuth: false,
      layout: 'public'
    }
  },

  // Reset Password (public)
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPassword,
    meta: {
      title: 'Reset Password',
      requiresAuth: false,
      layout: 'public'
    }
  },


  // Mahadevpura Plant Routes
  {
    path: '/plant/mahadevpura',
    component: MahadevpuraLayout,
    meta: {
      requiresAuth: true,
      requiresPlant: 'mahadevpura'
    },
    children: [
      {
        path: '',
        redirect: 'dashboard',
        name: 'MahadevpuraRoot'
      },
      {
        path: 'dashboard',
        name: 'MahadevpuraDashboard',
        component: MahadevpuraDashboard,
        meta: {
          title: 'Dashboard - Mahadevpura'
        }
      },
      {
        path: 'grn',
        name: 'MahadevpuraGRN',
        component: MahadevpuraGRN,
        meta: {
          title: 'GRN - Mahadevpura'
        }
      },
      {
        path: 'production-order',
        name: 'MahadevpuraProductionOrder',
        component: MahadevpuraProductionOrder,
        meta: {
          title: 'Production Order - Mahadevpura'
        }
      },
      {
        path: 'quality',
        name: 'MahadevpuraQuality',
        component: MahadevpuraQuality,
        meta: {
          title: 'Quality - Mahadevpura'
        }
      },
      {
        path: 'inventory-transfer',
        name: 'MahadevpuraInventoryTransfer',
        component: MahadevpuraInventoryTransfer,
        meta: {
          title: 'Inventory Transfer - Mahadevpura'
        }
      },
    ]
  },

  // Nandi Hills Plant Routes (accepts both nandihills and nandi-hills)
  {
    path: '/plant/:nandiPlantId(nandihills|nandi-hills)',
    component: NandiHillsLayout,
    meta: {
      requiresAuth: true,
      requiresPlant: 'nandihills'  // Must match normalized plant ID from database
    },
    children: [
      {
        path: '',
        redirect: 'dashboard',
        name: 'NandiHillsRoot'
      },
      {
        path: 'dashboard',
        name: 'NandiHillsDashboard',
        component: NandiHillsDashboard,
        meta: {
          title: 'Dashboard - Nandi Hills'
        }
      },
      {
        path: 'grn',
        name: 'NandiHillsGRN',
        component: NandiHillsGRN,
        meta: {
          title: 'GRN - Nandi Hills'
        }
      },
      {
        path: 'production-order',
        name: 'NandiHillsProductionOrder',
        component: NandiHillsProductionOrder,
        meta: {
          title: 'Production Order - Nandi Hills'
        }
      },
      {
        path: 'quality',
        name: 'NandiHillsQuality',
        component: NandiHillsQuality,
        meta: {
          title: 'Quality - Nandi Hills'
        }
      },
      {
        path: 'inventory-transfer',
        name: 'NandiHillsInventoryTransfer',
        component: NandiHillsInventoryTransfer,
        meta: {
          title: 'Inventory Transfer - Nandi Hills'
        }
      },
      {
        path: 'disassembly',
        name: 'NandiHillsDisassembly',
        component: NandiHillsDisassembly,
        meta: {
          title: 'Disassembly Report - Nandi Hills'
        }
      },
    ]
  },

  // Malur Plant Routes
  {
    path: '/plant/malur',
    component: MalurLayout,
    meta: {
      requiresAuth: true,
      requiresPlant: 'malur'
    },
    children: [
      {
        path: '',
        redirect: 'dashboard',
        name: 'MalurRoot'
      },
      {
        path: 'dashboard',
        name: 'MalurDashboard',
        component: MalurDashboard,
        meta: {
          title: 'Dashboard - Malur'
        }
      },
      {
        path: 'grn',
        name: 'MalurGRN',
        component: MalurGRN,
        meta: {
          title: 'GRN - Malur'
        }
      },
      {
        path: 'production-order',
        name: 'MalurProductionOrder',
        component: MalurProductionOrder,
        meta: {
          title: 'Production Order - Malur'
        }
      },
      {
        path: 'inventory-transfer',
        name: 'MalurInventoryTransfer',
        component: MalurInventoryTransfer,
        meta: {
          title: 'Inventory Transfer - Malur'
        }
      },
    ]
  },

  // Krishnagiri Plant Routes
  {
    path: '/plant/krishnagiri',
    component: KrishnagiriLayout,
    meta: {
      requiresAuth: true,
      requiresPlant: 'krishnagiri'
    },
    children: [
      {
        path: '',
        redirect: 'dashboard',
        name: 'KrishnagiriRoot'
      },
      {
        path: 'dashboard',
        name: 'KrishnagiriDashboard',
        component: KrishnagiriDashboard,
        meta: {
          title: 'Dashboard - Krishnagiri'
        }
      },
      {
        path: 'grn',
        name: 'KrishnagiriGRN',
        component: KrishnagiriGRN,
        meta: {
          title: 'GRN - Krishnagiri'
        }
      },
      {
        path: 'production-order',
        name: 'KrishnagiriProductionOrder',
        component: KrishnagiriProductionOrder,
        meta: {
          title: 'Production Order - Krishnagiri'
        }
      },
      {
        path: 'quality',
        name: 'KrishnagiriQuality',
        component: KrishnagiriQuality,
        meta: {
          title: 'Quality - Krishnagiri'
        }
      },
      {
        path: 'inventory-transfer',
        name: 'KrishnagiriInventoryTransfer',
        component: KrishnagiriInventoryTransfer,
        meta: {
          title: 'Inventory Transfer - Krishnagiri'
        }
      },
    ]
  },

  // Champavath Plant Routes
  {
    path: '/plant/champavath',
    component: ChampavathLayout,
    meta: {
      requiresAuth: true,
      requiresPlant: 'champavath'
    },
    children: [
      {
        path: '',
        redirect: 'dashboard',
        name: 'ChampavathRoot'
      },
      {
        path: 'dashboard',
        name: 'ChampavathDashboard',
        component: ChampavathDashboard,
        meta: {
          title: 'Dashboard - Champavath'
        }
      },
      {
        path: 'grn',
        name: 'ChampavathGRN',
        component: ChampavathGRN,
        meta: {
          title: 'GRN - Champavath'
        }
      },
      {
        path: 'production-order',
        name: 'ChampavathProductionOrder',
        component: ChampavathProductionOrder,
        meta: {
          title: 'Production Order - Champavath'
        }
      },
      {
        path: 'inventory-transfer',
        name: 'ChampavathInventoryTransfer',
        component: ChampavathInventoryTransfer,
        meta: {
          title: 'Inventory Transfer - Champavath'
        }
      },
    ]
  },

  // Dynamic plant feature routes
  {
    path: '/plant/:plantId/:feature',
    name: 'PlantFeature',
    component: () => import('./app/pages/PlantFeature.vue'),
    meta: {
      title: 'Plant Feature',
      requiresAuth: true,
      requiresPlant: true,
      layout: 'plant'
    }
  },

  // Admin dashboard
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('./admin/pages/AdminDashboard.vue'),
    meta: {
      title: 'Admin Dashboard',
      requiresAuth: true,
      requiresAdmin: true,
      layout: 'admin'
    }
  },

  // Error pages
  {
    path: '/unauthorized',
    name: 'Unauthorized',
    component: Unauthorized,
    meta: {
      title: 'Access Denied',
      requiresAuth: false,
      layout: 'public'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: 'Page Not Found',
      requiresAuth: false,
      layout: 'public'
    }
  }
]

const router = createRouter({
  history: createWebHistory(APP_CONFIG.BASE_PATH + '/'),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top for kiosk
    return { top: 0, left: 0 }
  }
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const sessionStore = useSessionStore()

  // Update page title
  if (to.meta.title) {
    document.title = `${to.meta.title} - Khanal Foods Kiosk`
  }

  // Check authentication
  if (to.meta.requiresAuth) {
    try {
      // Initialize session from storage if not already done
      if (!sessionStore.isAuthenticated) {
        const hasValidSession = sessionStore.initializeFromStorage()
        if (!hasValidSession) {
          // no valid session
          return next({ name: 'LoginGeneric' })
        }
      }

      // Verify session is still valid (isSessionValid is a computed property, not a function)
      if (!sessionStore.isSessionValid) {
        // session expired
        sessionStore.clearSession()
        return next({ name: 'LoginGeneric' })
      }
    } catch (error) {
      // Handle any errors during session initialization (e.g., decryption errors)
      console.error('Error during session initialization:', error)
      sessionStore.clearSession()
      return next({ name: 'LoginGeneric' })
    }
  }

  // Admin-only routes
  if (to.meta.requiresAdmin) {
    try {
      const session = sessionStore.getSession()
      if (!session || !session.user || !session.plant) {
        return next({ name: 'LoginGeneric' })
      }
      // Admin if has 'admin' permission for current plant, or role present
      const hasAdminPerm = Array.isArray(session?.plant?.permissions) && session.plant.permissions.includes('admin')
      const hasAdminRole = Array.isArray(session?.user?.roles) && session.user.roles.includes('System Administrator')
      if (!hasAdminPerm && !hasAdminRole) {
        return next({ name: 'Unauthorized' })
      }
    } catch (error) {
      // Handle any errors during admin check
      console.error('Error during admin access check:', error)
      return next({ name: 'LoginGeneric' })
    }
  }

  // Check plant-specific access
  if (to.meta.requiresPlant) {
    try {
      const session = sessionStore.getSession()

      if (!session || !session.plant || !session.plant.id) {
        // no session or invalid plant data
        return next({ name: 'LoginGeneric' })
      }

      // Check specific plant requirement
      if (typeof to.meta.requiresPlant === 'string') {
        if (session.plant.id !== to.meta.requiresPlant) {
          // wrong plant
          sessionStore.clearSession()
          return next({ name: 'LoginGeneric' })
        }
      }

      // Check plant access from URL params
      if (to.params.plantId && session.plant.id !== to.params.plantId) {
        // plant mismatch
        sessionStore.clearSession()
        return next({ name: 'LoginGeneric' })
      }
    } catch (error) {
      // Handle any errors during plant access check
      console.error('Error during plant access check:', error)
      sessionStore.clearSession()
      return next({ name: 'LoginGeneric' })
    }
  }

  next()
})

// After navigation
router.afterEach((to, from) => {
  const sessionStore = useSessionStore()

  // Update activity
  sessionStore.updateActivity()
})

export default router