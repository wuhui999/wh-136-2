import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'trenches',
        name: 'Trenches',
        component: () => import('../views/Trenches.vue'),
        meta: { title: '探方管理' }
      },
      {
        path: 'strata',
        name: 'Strata',
        component: () => import('../views/Strata.vue'),
        meta: { title: '地层管理' }
      },
      {
        path: 'artifacts',
        name: 'Artifacts',
        component: () => import('../views/Artifacts.vue'),
        meta: { title: '出土物管理' }
      },
      {
        path: 'relations',
        name: 'Relations',
        component: () => import('../views/Relations.vue'),
        meta: { title: '关联图' }
      },
      {
        path: 'audits',
        name: 'Audits',
        component: () => import('../views/Audits.vue'),
        meta: { title: '审核中心', roles: ['expert', 'admin'] }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { title: '用户管理', roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    next()
  } else if (!auth.isLoggedIn) {
    next('/login')
  } else if (to.meta.roles && !to.meta.roles.includes(auth.userRole)) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
