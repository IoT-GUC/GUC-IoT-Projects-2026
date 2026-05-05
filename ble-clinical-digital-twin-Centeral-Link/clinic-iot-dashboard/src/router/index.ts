import { createRouter, createWebHistory } from 'vue-router'
import AuthView from '@/views/AuthView.vue'
import DashboardView from '@/views/DashboardView.vue'
import RouterManagmentView from '@/views/RouterManagmentView.vue'
import DeviceManagmentView from '@/views/DeviceManagmentView.vue'
import PatientTrackingView from '@/views/PatientTrackingView.vue'
import AnalyticsView from '@/views/AnalyticsView.vue'
import SettingsView from '@/views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/auth',
      name: 'auth',
      component: AuthView,
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
    },
    {
      path: '/router-managment',
      name: 'router-managment',
      component: RouterManagmentView
    },
    {
      path: '/device-managment',
      name: 'device-managment',
      component: DeviceManagmentView
    },
    {
      path: '/patient-tracking',
      name: 'patient-tracking',
      component: PatientTrackingView
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: AnalyticsView
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView
    },
  ],
})


const isAuthenticated = () => {
  return localStorage.getItem('token') !== null
}

router.beforeEach((to, from, next) => {
  if (to.name !== 'auth' && !isAuthenticated()) {
    next({ name: 'auth' })
  } else {
    next()
  }
})


export default router
