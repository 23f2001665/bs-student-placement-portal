import { createApp } from 'vue'
import App from './App.vue'

// Global design theme (Poppins + CSS variables + base reset)
import './assets/theme.css'

// router + store
import router from '@/router'
import { createPinia } from 'pinia'
import { useAuthStore } from '@/store/auth'

// toast
import Vue3Toastify from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Vue3Toastify)

window.addEventListener('ppa:force-logout', () => {
	const auth = useAuthStore(pinia)
	auth.clearAuthState()
})

app.mount('#app')