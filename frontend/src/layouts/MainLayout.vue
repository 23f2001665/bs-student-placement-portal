<template>
  <div class="dashboard-shell">
    <header class="shell-header">
      <div>
        <h1>{{ sectionTitle }}</h1>
        <p>{{ sectionSubtitle }}</p>
      </div>
      <button class="logout-btn" type="button" @click="handleLogout">Logout</button>
    </header>

    <nav class="shell-nav">
      <template v-if="isStudent">
        <router-link to="/student">Dashboard</router-link>
        <router-link to="/student/profile">Profile</router-link>
        <router-link to="/student/drives">Drives</router-link>
        <router-link to="/student/applications">Applications</router-link>
      </template>
      <template v-else>
        <router-link to="/company">Dashboard</router-link>
        <router-link to="/company/profile">Profile</router-link>
        <router-link to="/company/drives">Drives</router-link>
        <router-link to="/company/applications">Applications</router-link>
      </template>
    </nav>

    <main class="shell-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isStudent = computed(() => route.path.startsWith('/student'))

const sectionTitle = computed(() => (isStudent.value ? 'Student Portal' : 'Company Portal'))
const sectionSubtitle = computed(() =>
  isStudent.value
    ? 'Track profile, drives, and applications.'
    : 'Manage drives, applications, and company profile.'
)

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

