<template>
  <section class="profile-page">
    <h2>Company Profile</h2>
    <div class="profile-card readonly-card">
    
      <div class="row">
        <span>Mail ID</span>
        <strong>{{ company.email || '-' }}</strong>
      </div>
      
      <div class="row">
        <span>Industry Type</span>
        <strong>{{ company.industry_type || '-' }}</strong>
      </div>
    </div>
    
    <form class="profile-card" @submit.prevent="saveProfile">
      <h3>Edit Details</h3>

      <label>
        Name
        <input v-model.trim="form.name" required />
      </label>


      <label>
        Website
        <input v-model.trim="form.website" type="url" required />
      </label>

      <label>
        Description
        <textarea v-model="form.description" rows="4" />
      </label>

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
import { getCompanyProfile, updateCompanyProfile } from '@/api/company'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const industries = ref([])

const company = ref({
  id: null,
  email: '',
  is_active: false,
  is_approved: false,
  user_type: 'company',
})

const form = ref({
  name: '',
  industry_type: '',
  website: '',
  description: '',
})

const applyCompany = (payload) => {
  company.value = payload || {}
  form.value = {
    name: payload?.name || '',
    industry_type: payload?.industry_type || '',
    website: payload?.website || '',
    description: payload?.description || '',
  }
}

const loadIndustries = async () => {
  try {
    const res = await api.get('/industries')
    industries.value = res.data.industries || []
  } catch (error) {
    industries.value = []
  }
}

const loadProfile = async () => {
  loading.value = true
  try {
    const res = await getCompanyProfile()
    applyCompany(res.data.company)
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load profile')
  } finally {
    loading.value = false
  }
}

const saveProfile = async () => {
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      industry_type: form.value.industry_type,
      website: form.value.website,
      description: form.value.description || null,
    }
    const res = await updateCompanyProfile(payload)
    const updated = res.data.company
    applyCompany(updated)

    // Keep auth store user in sync for layout/header usage.
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
  await Promise.all([loadIndustries(), loadProfile()])
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
select,
textarea {
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
</style>

