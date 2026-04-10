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

<script setup>  
</script>

<style scoped>
.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100svh;
  padding: 20px 16px;
  background: #f3f5f9;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.auth-header {
  text-align: center;
  margin-bottom: 10px;
}

.app-title {
  margin: 0;
  font-size: 2rem;
  color: #1b2a4b;
}

.app-subtitle {
  margin: 4px 0 0;
  color: #607094;
  font-size: 0.95rem;
}

.auth-content {
  width: min(900px, 100%);
}
</style>