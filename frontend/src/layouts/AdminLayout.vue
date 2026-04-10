<template>
  <div class="dashboard-shell">
    <header class="shell-header">
      <div>
        <h1>Admin Portal</h1>
        <p>Manage students, companies, and placement drives.</p>
      </div>
      <button class="logout-btn" type="button" @click="handleLogout">Logout</button>
    </header>

    <nav class="shell-nav">
      <router-link to="/admin">Dashboard</router-link>
      <router-link to="/admin/students">Students</router-link>
      <router-link to="/admin/companies">Companies</router-link>
      <router-link to="/admin/drives">Drives</router-link>
      <router-link to="/admin/applications">Applications</router-link>
    </nav>

    <main class="shell-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const handleLogout = async () => {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.dashboard-shell {
  min-height: 100svh;
  background: var(--color-bg-page);
  padding: var(--space-5);
}

.shell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

h1 {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--color-text-heading);
}

p {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.shell-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.shell-nav a {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-primary);
  background: var(--color-primary-light);
  font-size: var(--font-size-sm);
  font-weight: 600;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.shell-nav a.router-link-exact-active {
  color: #fff;
  background: var(--color-primary);
}

.logout-btn {
  border: none;
  border-radius: var(--radius-md);
  height: 40px;
  padding: 0 var(--space-4);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease;
}

.logout-btn:hover {
  background: var(--color-primary-hover);
}

.shell-content {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}
</style>

