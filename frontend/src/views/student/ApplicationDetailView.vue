<template>
  <section class="application-detail-page">
    <header class="page-header">
      <div>
        <h2>Application #{{ application?.id || route.params.applicationId }}</h2>
        <p class="subtext">Track application status, interview info, and linked drive/company.</p>
      </div>
      <div class="header-actions">
        <button class="ghost" type="button" :disabled="loading" @click="loadDetail">
          {{ loading ? 'Refreshing...' : 'Refresh' }}
        </button>
        <button class="ghost" type="button" @click="goBack">Back</button>
      </div>
    </header>

    <div v-if="loading && !payload" class="card">Loading application detail...</div>

    <template v-else-if="payload">
      <section class="detail-grid">
        <article class="card">
          <h3>Application</h3>
          <ul>
            <li><span>Status</span><strong>{{ application?.status || '-' }}</strong></li>
            <li><span>Applied On</span><strong>{{ formatDateTime(application?.application_date) }}</strong></li>
            <li><span>Application ID</span><strong>#{{ application?.id ?? '-' }}</strong></li>
            <li><span>Drive ID</span><strong>#{{ application?.drive_id ?? '-' }}</strong></li>
            <li><span>Resume Note</span><strong class="wrap">{{ application?.resume_note || '-' }}</strong></li>
            <li><span>Interview Date</span><strong>{{ application?.interview?.interview_date || '-' }}</strong></li>
            <li><span>Interview Time</span><strong>{{ application?.interview?.interview_time || '-' }}</strong></li>
            <li><span>Interview Details</span><strong class="wrap">{{ application?.interview?.details || '-' }}</strong></li>
          </ul>
        </article>

        <article class="card">
          <h3>Drive</h3>
          <ul>
            <li><span>Title</span><strong class="wrap">{{ drive?.title || '-' }}</strong></li>
            <li><span>Status</span><strong>{{ drive?.status || '-' }}</strong></li>
            <li><span>Approval</span><strong>{{ drive?.approval_status || '-' }}</strong></li>
            <li><span>Work Mode</span><strong>{{ drive?.work_mode || '-' }}</strong></li>
            <li><span>Start Date</span><strong>{{ formatDateTime(drive?.start_date) }}</strong></li>
            <li><span>End Date</span><strong>{{ formatDateTime(drive?.end_date) }}</strong></li>
          </ul>
          <button v-if="drive?.id" class="text-btn" type="button" @click="openDrive">Open Drive Detail</button>
        </article>

        <article class="card">
          <h3>Company</h3>
          <ul>
            <li><span>Name</span><strong>{{ company?.name || '-' }}</strong></li>
            <li><span>Email</span><strong class="wrap">{{ company?.email || '-' }}</strong></li>
            <li><span>Website</span><strong class="wrap">{{ company?.website || '-' }}</strong></li>
            <li><span>Approved</span><strong>{{ company?.is_approved ? 'Yes' : 'No' }}</strong></li>
            <li><span>Active</span><strong>{{ company?.is_active ? 'Yes' : 'No' }}</strong></li>
          </ul>
          <button v-if="company?.id" class="text-btn" type="button" @click="openCompany">Open Company Detail</button>
        </article>
      </section>
    </template>

    <p v-else class="card">Application details are unavailable.</p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { getStudentApplicationDetail } from '@/api/student'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const payload = ref(null)

const applicationId = computed(() => Number(route.params.applicationId))
const application = computed(() => payload.value?.application || null)
const drive = computed(() => payload.value?.drive || null)
const company = computed(() => payload.value?.company || null)

const formatDateTime = (value) => {
  if (!value) return '-'
  const raw = String(value).trim().replace(' ', 'T')
  const normalized = /[zZ]|[+-]\d{2}:\d{2}$/.test(raw) ? raw : `${raw}Z`
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

const loadDetail = async () => {
  if (!Number.isFinite(applicationId.value) || applicationId.value <= 0) {
    toast.error('Invalid application id')
    return
  }

  loading.value = true
  try {
    const res = await getStudentApplicationDetail(applicationId.value)
    payload.value = res?.data || null
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load application detail')
    payload.value = null
  } finally {
    loading.value = false
  }
}

const openDrive = () => {
  if (!drive.value?.id) return
  router.push({ name: 'student-drive-detail', params: { driveId: drive.value.id } })
}

const openCompany = () => {
  if (!company.value?.id) return
  router.push({ name: 'student-company-detail', params: { companyId: company.value.id } })
}

const goBack = () => {
  navigateBack(router, { name: 'student-applications' }, route.fullPath)
}

onMounted(async () => {
  await loadDetail()
})
</script>

<style scoped>
.application-detail-page {
  display: grid;
  gap: 14px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.page-header h2 {
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
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.card {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.card h3 {
  margin: 0 0 10px;
}

.card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.card li {
  display: grid;
  grid-template-columns: 130px 1fr;
  align-items: start;
  gap: 10px;
}

.card li span {
  color: #4e5f81;
}

.wrap {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.ghost,
.text-btn {
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}

.ghost {
  height: 34px;
  border-radius: 8px;
  padding: 0 12px;
  border: 1px solid #cfd9ee;
  background: #fff;
  color: #2f4b80;
  font-weight: 600;
}

.text-btn {
  background: transparent;
  color: #5b6783;
}

.ghost:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 980px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .card li {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
