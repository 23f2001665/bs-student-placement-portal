<template>
  <header class="admin-page-header">
    <div>
      <h2>{{ title }}</h2>
      <p v-if="subtitle" class="subtext">{{ subtitle }}</p>
    </div>

    <div class="header-actions">
      <button
        v-if="showRefresh"
        class="ghost"
        type="button"
        :disabled="refreshDisabled"
        @click="$emit('refresh')"
      >
        {{ refreshing ? refreshingLabel : refreshLabel }}
      </button>
      <button
        v-if="showBack"
        class="ghost"
        type="button"
        :disabled="backDisabled"
        @click="$emit('back')"
      >
        {{ backLabel }}
      </button>
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  showRefresh: { type: Boolean, default: false },
  refreshing: { type: Boolean, default: false },
  refreshDisabled: { type: Boolean, default: false },
  refreshLabel: { type: String, default: 'Refresh' },
  refreshingLabel: { type: String, default: 'Refreshing...' },
  showBack: { type: Boolean, default: false },
  backLabel: { type: String, default: 'Back' },
  backDisabled: { type: Boolean, default: false },
})

defineEmits(['refresh', 'back'])
</script>

<style scoped>
.admin-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.admin-page-header h2 {
  margin: 0;
}

.subtext {
  margin: 4px 0 0;
  color: #607094;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ghost {
  height: 34px;
  border-radius: 8px;
  padding: 0 12px;
  border: 1px solid #cfd9ee;
  background: #fff;
  color: #2f4b80;
  font-weight: 600;
  cursor: pointer;
}

.ghost:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
</style>
