<template>
  <section class="create-drive-page">
    <header class="page-header">
      <h2>Create New Drive</h2>
      <button class="ghost" type="button" @click="goBack">Back to Drives</button>
    </header>

    <form class="drive-form" @submit.prevent="handleSubmit">
      <div class="grid">
        <label>
          Title
          <input v-model.trim="form.title" required />
        </label>

        <label>
          Work Mode
          <select v-model="form.work_mode" required>
            <option value="">Select</option>
            <option value="onsite">Onsite</option>
            <option value="remote">Remote</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </label>

        <label>
          Start Date
          <input v-model="form.start_date" type="datetime-local" required />
        </label>

        <label>
          End Date
          <input v-model="form.end_date" type="datetime-local" required />
        </label>

        <label>
          Min CGPA
          <input v-model.number="form.min_cgpa" type="number" min="0" max="10" step="0.01" />
        </label>

        <label>
          Max Applications
          <input v-model.number="form.max_applications" type="number" min="1" />
        </label>
      </div>

      <label>
        Description
        <textarea v-model="form.description" rows="3" />
      </label>

      <fieldset class="branch-group">
        <legend>Allowed Branches</legend>
        <label v-for="branch in branches" :key="branch.value" class="checkbox-item">
          <input
            :checked="form.allowed_branches.includes(branch.value)"
            type="checkbox"
            @change="toggleBranch(branch.value)"
          />
          <span>{{ branch.label }}</span>
        </label>
      </fieldset>

      <div class="actions">
        <button class="primary" type="submit" :disabled="saving">
          {{ saving ? 'Creating...' : 'Create Drive' }}
        </button>
        <button class="ghost" type="button" @click="resetForm">Clear</button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/api/client'
import { createCompanyDrive } from '@/api/company'
import { navigateBack } from '@/utils/navigation'

const router = useRouter()
const saving = ref(false)
const branches = ref([])

const form = ref({
  title: '',
  description: '',
  start_date: '',
  end_date: '',
  work_mode: '',
  min_cgpa: null,
  max_applications: null,
  allowed_branches: [],
})

const getErrorMessage = (error, fallback) => {
  const payload = error?.response?.data || {}
  return payload.error || payload.details || fallback
}

const toApiDateTime = (value) => {
  if (!value) return null
  const text = String(value).trim()
  if (!text) return null
  // Keep local wall-clock value from datetime-local input (no UTC conversion).
  return text.length === 16 ? `${text}:00` : text
}

const validateForm = () => {
  if (!form.value.title?.trim()) return 'Title is required.'
  if (!form.value.work_mode) return 'Work mode is required.'
  if (!form.value.start_date || !form.value.end_date) return 'Start and end dates are required.'

  const start = new Date(form.value.start_date)
  const end = new Date(form.value.end_date)
  const now = new Date()
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 'Please provide valid start and end dates.'
  if (end < start) return 'End date must be on or after start date.'
  if (end < now) return 'End date/time cannot be in the past.'

  const currentYear = now.getFullYear()
  if (start.getFullYear() < currentYear || end.getFullYear() < currentYear) {
    return 'Selected year cannot be in the past.'
  }

  if (form.value.min_cgpa !== null && form.value.min_cgpa !== '' && (form.value.min_cgpa < 0 || form.value.min_cgpa > 10)) {
    return 'Min CGPA must be between 0 and 10.'
  }

  if (form.value.max_applications !== null && form.value.max_applications !== '' && Number(form.value.max_applications) < 1) {
    return 'Max applications must be at least 1.'
  }

  return null
}

const buildPayload = () => ({
  title: form.value.title,
  description: form.value.description || null,
  start_date: toApiDateTime(form.value.start_date),
  end_date: toApiDateTime(form.value.end_date),
  work_mode: form.value.work_mode,
  min_cgpa: form.value.min_cgpa ?? null,
  max_applications: form.value.max_applications ?? null,
  allowed_branches: form.value.allowed_branches,
})

const toggleBranch = (branchValue) => {
  const selected = form.value.allowed_branches
  const idx = selected.indexOf(branchValue)
  if (idx >= 0) {
    selected.splice(idx, 1)
    return
  }
  selected.push(branchValue)
}

const loadBranches = async () => {
  try {
    const res = await api.get('/branches')
    branches.value = res.data.branches || []
  } catch (error) {
    branches.value = []
    toast.error('Failed to load branches')
  }
}

const handleSubmit = async () => {
  const validationError = validateForm()
  if (validationError) {
    toast.error(validationError)
    return
  }

  saving.value = true
  try {
    await createCompanyDrive(buildPayload())
    toast.success('Drive created')
    router.push('/company/drives')
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to create drive'))
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  form.value = {
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    work_mode: '',
    min_cgpa: null,
    max_applications: null,
    allowed_branches: [],
  }
}

const goBack = () => {
  navigateBack(router, '/company/drives')
}

onMounted(loadBranches)
</script>

<style scoped>
.create-drive-page {
  display: grid;
  gap: 14px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drive-form {
  border: 1px solid #e3e7ef;
  border-radius: 12px;
  background: #fff;
  padding: 14px;
  display: grid;
  gap: 10px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
}

input,
select,
textarea {
  border: 1px solid #cfd6e3;
  border-radius: 8px;
  padding: 8px 10px;
  font: inherit;
}

.branch-group {
  border: 1px solid #d6dbe8;
  border-radius: 10px;
  padding: 10px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.branch-group legend {
  padding: 0 6px;
  font-size: 0.9rem;
  color: #3f4b66;
}

.checkbox-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
}

.checkbox-item input {
  margin: 0;
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.primary,
.ghost {
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}

.primary {
  background: #2f66db;
  color: #fff;
}

.ghost {
  background: #edf2ff;
  color: #2f66db;
}

@media (max-width: 760px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .branch-group {
    grid-template-columns: 1fr;
  }

  .page-header {
    align-items: stretch;
    gap: 8px;
  }
}
</style>
