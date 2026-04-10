<template>
  <section class="landing-page">
    <div class="landing-card">
      <p class="eyebrow">Welcome</p>
      <h2>Get Started</h2>

      <button id="login-btn" class="action-btn primary" @click="handleLogin">Login</button>
      <button id="register-btn" class="action-btn secondary" @click="handleRegister">Register</button>
      <button id="forgot-password-btn" class="action-btn subtle" @click="handleForgotPassword">Forgot Password</button>
    </div>
  </section>
</template>
<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleLogin = () => {
  router.push({ name: 'login' })
}

const handleRegister = () => {
  router.push({ name: 'register' })
}

const handleForgotPassword = () => {
  router.push({ name: 'forgot-password' })
}
</script>

<style scoped>
.landing-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
}

.landing-card {
  width: min(420px, 95vw);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-lg);
  padding: var(--space-6) var(--space-5);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.eyebrow {
  margin: 0;
  color: var(--color-text-subtle);
  font-weight: 600;
  font-size: var(--font-size-sm);
}

h2 {
  margin: 0 0 var(--space-1);
  color: var(--color-text-heading);
  font-size: var(--font-size-xl);
}

#login-btn,
#register-btn,
#forgot-password-btn {
  width: 100%;
  min-height: 44px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  font-size: var(--font-size-base);
  font-weight: 600;
  letter-spacing: 0.2px;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease;
}

#login-btn {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

#register-btn {
  color: var(--color-text-heading);
  background: var(--color-bg-card);
  border-color: var(--color-border-input);
}

#forgot-password-btn {
  color: var(--color-text-link);
  background: var(--color-primary-light);
  border-color: var(--color-border-nav);
}

#login-btn:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

#register-btn:hover,
#forgot-password-btn:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

#login-btn:focus-visible,
#register-btn:focus-visible,
#forgot-password-btn:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 1px;
}
</style>