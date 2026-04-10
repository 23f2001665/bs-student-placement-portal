<template>
  <section class="login-page">
    <div class="login-card">
      <p class="eyebrow">Welcome Back</p>
      <h1>Sign In</h1>
      <p class="subtitle">Use your account credentials to continue.</p>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="input-row">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            autocomplete="email"
            :pattern="emailPattern"
            title="Enter a valid email address (example@domain.com)."
            required
          />
        </div>

        <div class="input-row">
          <label for="password">Password</label>
          <div class="password-field">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter your password"
              autocomplete="current-password"
              :pattern="passwordPattern"
              title="Password must be at least 8 characters and include uppercase, lowercase, and a number."
              required
            />
            <button
              class="toggle-password-btn"
              type="button"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="togglePasswordVisibility"
            >
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <p v-if="validationError" class="validation-error">{{ validationError }}</p>

        <button class="primary-btn" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Signing in...' : 'Login' }}
        </button>
      </form>

      <div class="support-actions">
        <div class="support-row">
          <span class="support-text">Don't have an account?</span>
          <button id="register-btn" class="text-btn" type="button" @click="handleRegister">
            Create new account
          </button>
        </div>
        <div class="support-row">
          <span class="support-text">Forgot your password?</span>
          <button id="forgot-password-btn" class="text-btn" type="button" @click="handleForgotPassword">
            Reset password
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'

const email = ref('')
const password = ref('')
const isSubmitting = ref(false)
const showPassword = ref(false)
const validationError = ref('')

const emailPattern = '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$'
const passwordPattern = '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}$'

const auth = useAuthStore()
const router = useRouter()

const handleLogin = async () => {
  const isEmailValid = new RegExp(emailPattern).test(email.value.trim())
  const isPasswordValid = new RegExp(passwordPattern).test(password.value)

  if (!isEmailValid) {
    validationError.value = 'Please enter a valid email address.'
    return
  }

  if (!isPasswordValid) {
    validationError.value = 'Password must be at least 8 characters and include uppercase, lowercase, and a number.'
    return
  }

  validationError.value = ''
  isSubmitting.value = true

  try {
    const user = await auth.login({
      email: email.value,
      password: password.value
    })

    toast.success("Login successful")

    // role-based redirect
    if (user.user_type === 'admin') {
      router.push('/admin')
    } else if (user.user_type === 'student') {
      router.push('/student')
    } else if (user.user_type === 'company' && user.is_approved === false) {
      router.push('/company/pending-approval')
    } else {
      router.push('/company')
    }

  } catch (err) {
    const message = err?.response?.data?.message || err?.response?.data?.error || 'Invalid credentials'
    toast.error(message)
  } finally {
    isSubmitting.value = false
  }
}

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

const handleRegister = () => {
  router.push({ name: 'register' })
}

const handleForgotPassword = () => {
  router.push({ name: 'forgot-password' })
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
}

.login-card {
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

h1 {
  margin: var(--space-1) 0 var(--space-1);
  font-size: var(--font-size-2xl);
  color: var(--color-text-heading);
}

.subtitle {
  margin: 0 0 var(--space-4);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.input-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  width: 100%;
}

label {
  color: var(--color-text-base);
  font-weight: 600;
  font-size: var(--font-size-sm);
}

input {
  box-sizing: border-box;
  width: 100%;
  height: 42px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-input);
  background: var(--color-bg-input);
  color: var(--color-text-heading);
  font-size: var(--font-size-base);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.password-field {
  position: relative;
  width: 100%;
}

.password-field input {
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

.validation-error {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.primary-btn {
  height: 44px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  font-size: var(--font-size-base);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease;
}

.primary-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.primary-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.support-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.support-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.support-text {
  color: var(--color-text-support);
  font-size: var(--font-size-sm);
}

.text-btn {
  border: none;
  padding: 0;
  width: fit-content;
  background: transparent;
  color: var(--color-text-link);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.text-btn:hover {
  color: var(--color-primary-hover);
}
</style>