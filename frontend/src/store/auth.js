import { defineStore } from 'pinia'
import { login as loginAPI, logout as logoutAPI } from '@/api/auth'
import { toast } from 'vue3-toastify'

const AUTH_USER_KEY = 'ppa_auth_user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    initialized: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    userRole: (state) => state.user?.user_type || null,
  },

  actions: {
    clearAuthState() {
      this.user = null
      this.initialized = true
      localStorage.removeItem(AUTH_USER_KEY)
    },

    initialize() {
      if (this.initialized) return

      try {
        const raw = localStorage.getItem(AUTH_USER_KEY)
        this.user = raw ? JSON.parse(raw) : null
      } catch (error) {
        this.user = null
      } finally {
        this.initialized = true
      }
    },

    async login(credentials) {
      const res = await loginAPI(credentials)

      if (!res.data.success) {
        throw new Error(res.data.message)
      }

      this.user = res.data.data
      this.initialized = true
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(this.user))

      return this.user
    },

    async logout() {
      let serverLogoutFailed = false

      try {
        await logoutAPI()
      } catch (error) {
        serverLogoutFailed = true
        // Proceed with local cleanup even if server session is already missing.
      } finally {
        this.clearAuthState()
      }

      if (serverLogoutFailed) {
        toast.warning('Logged out locally. Server session was already unavailable.')
        return
      }

      toast.success('Logged out successfully')
    }
  }
})