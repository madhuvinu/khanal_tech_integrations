import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('./views/Dashboard.vue')
  },
  {
    path: '/kiosk',
    name: 'KioskDashboard',
    component: () => import('./views/Dashboard.vue')
  },
  {
    path: '/login/:plant',
    name: 'Login',
    component: () => import('./views/LoginPage.vue'),
    props: true
  },
  {
    path: '/plant/:plantName',
    name: 'PlantDashboard',
    component: () => import('./views/PlantDashboard.vue'),
    props: true,
    beforeEnter: (to, from, next) => {
      // Check if user is logged in for this plant
      const plantName = to.params.plantName
      const isLoggedIn = localStorage.getItem(`kiosk_${plantName}_logged_in`)
      if (isLoggedIn) {
        next()
      } else {
        next(`/login/${plantName}`)
      }
    }
  },
  // Plant-specific routes
  {
    path: '/plant/NandhiHills/dashboard',
    name: 'NandhiHillsDashboard',
    component: () => import('./modules/NandhiHills/Dashboard.vue'),
    beforeEnter: (to, from, next) => {
      const isLoggedIn = localStorage.getItem('kiosk_NandhiHills_logged_in')
      if (isLoggedIn) {
        next()
      } else {
        next('/login/NandhiHills')
      }
    }
  },
  {
    path: '/plant/Dogsee/dashboard',
    name: 'DogseeDashboard',
    component: () => import('./modules/Dogsee/Dashboard.vue'),
    beforeEnter: (to, from, next) => {
      const isLoggedIn = localStorage.getItem('kiosk_Dogsee_logged_in')
      if (isLoggedIn) {
        next()
      } else {
        next('/login/Dogsee')
      }
    }
  },
  {
    path: '/plant/Mallur/dashboard',
    name: 'MallurDashboard',
    component: () => import('./modules/Mallur/Dashboard.vue'),
    beforeEnter: (to, from, next) => {
      const isLoggedIn = localStorage.getItem('kiosk_Mallur_logged_in')
      if (isLoggedIn) {
        next()
      } else {
        next('/login/Mallur')
      }
    }
  },
  {
    path: '/plant/Champawath/dashboard',
    name: 'ChampawathDashboard',
    component: () => import('./modules/Champawath/Dashboard.vue'),
    beforeEnter: (to, from, next) => {
      const isLoggedIn = localStorage.getItem('kiosk_Champawath_logged_in')
      if (isLoggedIn) {
        next()
      } else {
        next('/login/Champawath')
      }
    }
  },
  {
    path: '/plant/Krishnagiri/dashboard',
    name: 'KrishnagiriDashboard',
    component: () => import('./modules/Krishnagiri/Dashboard.vue'),
    beforeEnter: (to, from, next) => {
      const isLoggedIn = localStorage.getItem('kiosk_Krishnagiri_logged_in')
      if (isLoggedIn) {
        next()
      } else {
        next('/login/Krishnagiri')
      }
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
