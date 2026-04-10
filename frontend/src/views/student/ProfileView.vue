<template>
  <section class="profile-page">
    <h2>Student Profile</h2>

    <div class="profile-card readonly-card">
      <div class="row">
        <span>Mail ID</span>
        <strong>{{ student.email || '-' }}</strong>
      </div>
      <div class="row">
        <span>Roll Number</span>
        <strong>{{ student.roll || '-' }}</strong>
      </div>
      <div class="row">
        <span>Branch</span>
        <strong>{{ student.branch || '-' }}</strong>
      </div>
    </div>

    <form class="profile-card" @submit.prevent="saveProfile">
      <h3>Edit Details</h3>

      <label>
        Name
        <input v-model.trim="form.name" required />
      </label>

      <label>
        Gender
        <select v-model="form.gender">
          <option value="">Select gender</option>
          <option v-for="g in genders" :key="g.value" :value="g.value">{{ g.label }}</option>
        </select>
      </label>

      <label>
        Current Level
        <input v-model.number="form.current_level" type="number" min="1" required />
      </label>

      <label>
        CGPA
        <input v-model.number="form.cgpa" type="number" min="0" max="10" step="0.01" />
      </label>

      <label>
        Resume (PDF, max 1MB)
        <input type="file" accept="application/pdf,.pdf" @change="onResumeFileChange" />
      </label>

      <p v-if="form.resume_path" class="resume-path">
        <a :href="resumeOpenUrl" target="_blank" rel="noopener noreferrer">Open current resume</a>
      </p>

      <div class="actions">
        <button class="primary" type="submit" :disabled="saving || loading">
          {{ saving ? 'Saving...' : 'Save Profile' }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '@/api/client'
import { toast } from 'vue3-toastify'
import { getStudentProfile, updateStudentProfile } from '@/api/student'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const genders = ref([])

const student = ref({
  id: null,
  email: '',
  roll: '',
  branch: '',
})

const form = ref({
  name: '',
  gender: '',
  current_level: 1,
  cgpa: null,
  resume_path: '',
})
const resumeFile = ref(null)
const resumeOpenUrl = `${String(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')}/student/profile/resume/`

const normalizeGender = (value) => {
  if (!value) return ''

  const raw = String(value).trim().toLowerCase()
  const matchByKey = genders.value.find((item) => String(item.value).toLowerCase() === raw)
  if (matchByKey) return matchByKey.value

  const matchByLabel = genders.value.find((item) => String(item.label).toLowerCase() === raw)
  if (matchByLabel) return matchByLabel.value

  return ''
}

const applyStudent = (payload) => {
  student.value = payload || {}
  form.value = {
    name: payload?.name || '',
    gender: normalizeGender(payload?.gender || ''),
    current_level: payload?.current_level || 1,
    cgpa: payload?.cgpa ?? null,
    resume_path: payload?.resume_path || '',
  }
}

const loadGenders = async () => {
  try {
    const res = await api.get('/genders')
    genders.value = res.data.genders || []
  } catch (error) {
    genders.value = []
  }
}

const loadProfile = async () => {
  loading.value = true
  try {
    const res = await getStudentProfile()
    applyStudent(res.data.student)
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load profile')
  } finally {
    loading.value = false
  }
}

const onResumeFileChange = (event) => {
  const file = event?.target?.files?.[0] || null
  resumeFile.value = file
}

const saveProfile = async () => {
  saving.value = true
  try {
    const payload = new FormData()
    payload.append('name', form.value.name || '')
    payload.append('gender', form.value.gender || '')
    payload.append('current_level', String(form.value.current_level ?? ''))
    payload.append('cgpa', form.value.cgpa === '' || form.value.cgpa == null ? '' : String(form.value.cgpa))
    payload.append('resume_path', form.value.resume_path || '')
    if (resumeFile.value) {
      payload.append('resume', resumeFile.value)
    }

    const res = await updateStudentProfile(payload)
    const updated = res.data.student
    applyStudent(updated)
    resumeFile.value = null

    auth.user = {
      ...(auth.user || {}),
      ...updated,
    }
    localStorage.setItem('ppa_auth_user', JSON.stringify(auth.user))

    toast.success('Profile updated successfully')
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to update profile')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadGenders()
  await loadProfile()
})
</script>

<style scoped>
.profile-page {
  display: grid;
  gap: 14px;
}

h2 {
  margin: 0;
}

h3 {
  margin: 0;
}

.profile-card {
  background: #fff;
  border: 1px solid #e3e7ef;
  border-radius: 10px;
  padding: 14px;
  display: grid;
  gap: 10px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.9rem;
}

input,
select {
  border: 1px solid #cfd6e3;
  border-radius: 8px;
  padding: 8px 10px;
  font: inherit;
}

.actions {
  display: flex;
  gap: 8px;
}

.primary {
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
  background: #2f66db;
  color: #fff;
}

.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.readonly-card {
  gap: 8px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid #eef2f8;
  padding-bottom: 8px;
}

.row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

span {
  color: #607094;
}

strong {
  color: #1b2a4b;
}

.resume-path {
  margin: 0;
  color: #5a6886;
  font-size: 0.88rem;
}
</style>

