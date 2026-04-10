<template>
  <section class="edit-drive-page">
    <header class="page-header">
      <h2>Edit Drive</h2>
      <button class="ghost" type="button" @click="goBack">Back to Drive</button>
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
          <input v-model="form.start_date" type="datetime-local" required :disabled="isStartDateLocked" />
          <small v-if="isStartDateLocked" class="field-note">Start date/time is locked after the drive starts.</small>
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
        <button class="primary" type="submit" :disabled="saving || loading">
          {{ saving ? 'Updating...' : 'Update Drive' }}
        </button>
        <button class="ghost" type="button" @click="resetForm" :disabled="loading">Reset</button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/api/client'
import { getDriveSummary, updateCompanyDrive } from '@/api/company'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const driveId = computed(() => Number(route.params.driveId))
const saving = ref(false)
const loading = ref(false)
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

const initialForm = ref(null)

const getErrorMessage = (error, fallback) => {
  const payload = error?.response?.data || {}
  return payload.error || payload.details || fallback
}

const isStartDateLocked = computed(() => {
  const start = initialForm.value?.start_date
  if (!start) return false
  const startDate = new Date(start)
  if (Number.isNaN(startDate.getTime())) return false
  return Date.now() >= startDate.getTime()
})

const toInputDateTime = (value) => {
  if (!value) return ''
  const text = String(value).trim().replace(' ', 'T')
  if (text.length >= 16) return text.slice(0, 16)

  const dt = new Date(value)
  if (Number.isNaN(dt.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`
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
  if (end.getFullYear() < currentYear) return 'Selected end year cannot be in the past.'
  if (!isStartDateLocked.value && start.getFullYear() < currentYear) {
    return 'Selected start year cannot be in the past.'
  }

  if (form.value.min_cgpa !== null && form.value.min_cgpa !== '' && (form.value.min_cgpa < 0 || form.value.min_cgpa > 10)) {
    return 'Min CGPA must be between 0 and 10.'
  }

  if (form.value.max_applications !== null && form.value.max_applications !== '' && Number(form.value.max_applications) < 1) {
    return 'Max applications must be at least 1.'
  }

  return null
}

const hydrateForm = (drive) => {
  const next = {
    title: drive?.title || '',
    description: drive?.description || '',
    start_date: toInputDateTime(drive?.start_date),
    end_date: toInputDateTime(drive?.end_date),
    work_mode: String(drive?.work_mode || '').toLowerCase(),
    min_cgpa: drive?.min_cgpa ?? null,
    max_applications: drive?.max_applications ?? null,
    allowed_branches: Array.isArray(drive?.allowed_branches) ? [...drive.allowed_branches] : [],
  }
  form.value = next
  initialForm.value = JSON.parse(JSON.stringify(next))
}

const buildPayload = () => {
  const payload = {
    title: form.value.title,
    description: form.value.description || null,
    end_date: toApiDateTime(form.value.end_date),
    work_mode: form.value.work_mode,
    min_cgpa: form.value.min_cgpa ?? null,
    max_applications: form.value.max_applications ?? null,
    allowed_branches: form.value.allowed_branches,
  }

  if (!isStartDateLocked.value) {
    payload.start_date = toApiDateTime(form.value.start_date)
  }

  return payload
}

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

const loadDrive = async () => {
  loading.value = true
  try {
    const res = await getDriveSummary(driveId.value)
    hydrateForm(res?.data?.drive || {})
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to load drive'))
  } finally {
    loading.value = false
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
    await updateCompanyDrive(driveId.value, buildPayload())
    toast.success('Drive updated')
    router.push({ name: 'company-drive-detail', params: { driveId: driveId.value } })
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to update drive'))
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  if (!initialForm.value) return
  form.value = JSON.parse(JSON.stringify(initialForm.value))
}

const goBack = () => {
  navigateBack(router, { name: 'company-drive-detail', params: { driveId: driveId.value } }, route.fullPath)
}

onMounted(async () => {
  await Promise.all([loadBranches(), loadDrive()])
})
</script>

<style scoped>
.edit-drive-page {
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

.field-note {
  font-size: 0.8rem;
  color: #5f6f8f;
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
