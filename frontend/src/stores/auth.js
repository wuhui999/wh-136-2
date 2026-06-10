import { defineStore } from 'pinia'
import api from '../utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    userRole: (state) => state.user?.role || '',
    isAdmin: (state) => state.user?.role === 'admin',
    isExpert: (state) => state.user?.role === 'expert' || state.user?.role === 'admin',
    isCurator: (state) => state.user?.role === 'curator' || state.user?.role === 'admin',
    isExcavator: (state) => state.user?.role === 'excavator' || state.user?.role === 'admin'
  },
  actions: {
    async login(username, password) {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      const data = await api.post('/auth/login', formData)
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      return data
    },
    async getCurrentUser() {
      const data = await api.get('/auth/me')
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
