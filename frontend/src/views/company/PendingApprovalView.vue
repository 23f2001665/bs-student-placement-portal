<template>
  <section class="pending-page">
    <div class="pending-card">
      <p class="eyebrow">Company Verification</p>
      <h1>Approval Pending</h1>
      <p class="message">
        Your company account has been created, but it is waiting for admin approval.
        You will be able to access dashboard features once approved.
      </p>
      <p class="message small">
        If approval takes too long, please contact the placement cell administrator.
      </p>

      <div class="actions">
        <button class="primary-btn" type="button" @click="refreshProfile">Check Status</button>
        <button class="ghost-btn" type="button" @click="logout">Logout</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/api/client'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const refreshProfile = async () => {
  try {
    const res = await api.get('/company/profile/', { skipAuthHandling: true })
    const company = res?.data?.company

    if (company?.is_approved) {
      const nextUser = { ...(auth.user || {}), is_approved: true }
      auth.user = nextUser
      localStorage.setItem('ppa_auth_user', JSON.stringify(nextUser))
      toast.success('Your account is approved. You can continue now.')
      router.push('/company')
      return
    }

    toast.info('Your account is still pending approval.')
  } catch (error) {
    const message = error?.response?.data?.error || 'Your account is still pending approval.'
    toast.info(message)
  }
}

const logout = async () => {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.pending-page {
  min-height: calc(100vh - 120px);
  display: grid;
  place-items: center;
  padding: 16px;
}

.pending-card {
  width: min(560px, 100%);
  border: 1px solid #d8e0f0;
  border-radius: 14px;
  padding: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
  box-shadow: 0 10px 26px rgba(30, 60, 120, 0.08);
}

.eyebrow {
  margin: 0;
  color: #4d6290;
  font-weight: 600;
  font-size: 0.9rem;
}

h1 {
  margin: 6px 0 12px;
  color: #1d2f53;
}

.message {
  margin: 0;
  color: #384f79;
  line-height: 1.45;
}

.message.small {
  margin-top: 10px;
  color: #5c6f94;
  font-size: 0.92rem;
}

.actions {
  margin-top: 18px;
  display: flex;
  gap: 10px;
}

.primary-btn,
.ghost-btn {
  height: 40px;
  border-radius: 8px;
  padding: 0 14px;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn {
  border: none;
  background: #2f66db;
  color: #fff;
}

.primary-btn:hover {
  background: #2457c7;
}

.ghost-btn {
  border: 1px solid #c7d3ec;
  background: #fff;
  color: #2e4677;
}

.ghost-btn:hover {
  background: #f3f7ff;
}
</style>
