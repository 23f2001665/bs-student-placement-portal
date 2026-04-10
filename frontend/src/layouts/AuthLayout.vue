<template>
  <div class="auth-container">
    <header class="auth-header">
      <h1 class="app-title">Placement Portal</h1>
      <p class="app-subtitle">Campus recruitment portal</p>
    </header>

    <div class="auth-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100svh;
  padding: var(--space-5) var(--space-4);
  background: var(--color-bg-page);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-2);
}

.app-title {
  margin: 0;
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--color-text-heading);
  letter-spacing: -0.5px;
}

.app-subtitle {
  margin: var(--space-1) 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
}

.auth-content {
  width: min(900px, 100%);
}
</style>

