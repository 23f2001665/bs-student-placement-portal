<template>
  <section class="forgot-page">
    <div class="forgot-card">
      <p class="eyebrow">Account Recovery</p>
      <h2>Forgot Password</h2>

      <form class="forgot-form" @submit.prevent="handleResetPassword">
        <label for="email">Email</label>
        <input id="email" v-model.trim="email" type="email" placeholder="you@example.com" required />

        <button class="action-btn" type="button" :disabled="sendingOtp" @click="handleSendOtp">
          {{ sendingOtp ? 'Sending OTP...' : 'Send OTP' }}
        </button>

        <label for="otp">OTP</label>
        <input id="otp" v-model.trim="otp" type="text" inputmode="numeric" maxlength="6" placeholder="6-digit OTP" required />

        <label for="new-password">New Password</label>
        <div class="password-field">
          <input
            id="new-password"
            v-model="newPassword"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Enter new password"
            required
          />
          <button
            class="toggle-password-btn"
            type="button"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? 'Hide' : 'Show' }}
          </button>
        </div>

        <button class="action-btn" type="submit" :disabled="resettingPassword">
          {{ resettingPassword ? 'Resetting...' : 'Verify OTP and Reset Password' }}
        </button>
      </form>

      <div class="support-actions">
        <button class="text-btn" type="button" @click="goToLogin">Login</button>
        <span class="divider">|</span>
        <button class="text-btn" type="button" @click="goToRegister">Register</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { sendOtp, resetPassword } from '@/api/auth'

const router = useRouter()
const email = ref('')
const otp = ref('')
const newPassword = ref('')
const showPassword = ref(false)
const sendingOtp = ref(false)
const resettingPassword = ref(false)

const handleSendOtp = async () => {
  if (!email.value) {
    toast.error('Please enter your email first')
    return
  }

  try {
    sendingOtp.value = true
    await sendOtp({ email: email.value })
    toast.success('OTP sent to your email')
  } catch (error) {
    const message = error?.response?.data?.error || 'Failed to send OTP'
    toast.error(message)
  } finally {
    sendingOtp.value = false
  }
}

const handleResetPassword = async () => {
  if (!email.value || !otp.value || !newPassword.value) {
    toast.error('Email, OTP and new password are required')
    return
  }

  try {
    resettingPassword.value = true
    await resetPassword({
      email: email.value,
      otp: otp.value,
      password: newPassword.value,
    })

    toast.success('Password reset successful. Please login.')
    router.push({ name: 'login' })
  } catch (error) {
    const message = error?.response?.data?.error || 'Failed to reset password'
    toast.error(message)
  } finally {
    resettingPassword.value = false
  }
}

const goToLogin = () => {
  router.push({ name: 'login' })
}

const goToRegister = () => {
  router.push({ name: 'register' })
}
</script>

<style scoped>
.forgot-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
}

.forgot-card {
  width: min(420px, 95vw);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-5);
  box-shadow: var(--shadow-card);
}

.eyebrow {
  margin: 0;
  color: var(--color-text-subtle);
  font-weight: 600;
  font-size: var(--font-size-sm);
}

h2 {
  margin: var(--space-1) 0 var(--space-4);
  color: var(--color-text-heading);
  font-size: var(--font-size-xl);
}

.forgot-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

label {
  color: var(--color-text-base);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

input {
  height: 42px;
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-md);
  padding: 0 var(--space-3);
  outline: none;
  box-sizing: border-box;
  background: var(--color-bg-input);
  color: var(--color-text-heading);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input:focus {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.password-field {
  position: relative;
  width: 100%;
}

.password-field input {
  width: 100%;
  padding-right: 64px;
}

.toggle-password-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-link);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
}

.toggle-password-btn:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 1px;
}

.action-btn {
  height: 42px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease;
}

.action-btn:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

.action-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.text-btn {
  align-self: flex-start;
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-weight: 600;
  cursor: pointer;
  padding: 2px 0;
}

.support-actions {
  margin-top: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.support-actions .text-btn {
  align-self: center;
  font-size: var(--font-size-base);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.divider {
  color: var(--color-border-nav);
}
</style>

