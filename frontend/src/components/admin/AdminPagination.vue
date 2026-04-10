<template>
  <footer v-if="totalPages > 1" class="pagination">
    <button class="ghost" type="button" :disabled="disabled || page <= 1" @click="go(page - 1)">
      Previous
    </button>
    <span>Page {{ page }} / {{ totalPages }}</span>
    <div v-if="showJump" class="pagination-jump">
      <label :for="inputId">{{ jumpLabel }}</label>
      <input
        :id="inputId"
        v-model.number="jumpToPageInput"
        type="number"
        min="1"
        :max="totalPages"
        @keyup.enter="submitJump"
      />
      <button class="ghost" type="button" :disabled="disabled" @click="submitJump">Go</button>
    </div>
    <button class="ghost" type="button" :disabled="disabled || page >= totalPages" @click="go(page + 1)">
      Next
    </button>
  </footer>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  showJump: { type: Boolean, default: false },
  jumpLabel: { type: String, default: 'Jump to' },
  inputId: { type: String, default: 'pagination-jump' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['go'])

const jumpToPageInput = ref(1)

watch(
  () => props.page,
  (value) => {
    jumpToPageInput.value = Number(value || 1)
  },
  { immediate: true }
)

const go = (page) => {
  emit('go', page)
}

const submitJump = () => {
  const requestedPage = Number(jumpToPageInput.value)
  if (!Number.isFinite(requestedPage)) {
    jumpToPageInput.value = props.page
    return
  }
  const nextPage = Math.min(Math.max(1, Math.trunc(requestedPage)), props.totalPages)
  jumpToPageInput.value = nextPage
  if (nextPage !== props.page) {
    go(nextPage)
  }
}
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination > span {
  white-space: nowrap;
}

.pagination-jump {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
}

.pagination-jump label {
  color: #4f5f7a;
  font-size: 0.9rem;
  white-space: nowrap;
}

.pagination-jump input {
  width: 64px;
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 6px 8px;
  font: inherit;
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
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
