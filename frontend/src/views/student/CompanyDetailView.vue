<template>
  <section class="student-company-page">
    <header class="head">
      <div>
        <h2>{{ company?.name || 'Company Detail' }}</h2>
        <p>Public company profile and approved drives.</p>
      </div>
      <button class="ghost" type="button" @click="goBack">Back</button>
    </header>

    <div v-if="loading" class="box">Loading company detail...</div>
    <p v-else-if="!company">Company not found.</p>

    <div v-else class="content">
      <article class="panel">
        <h3>Public Details</h3>
        <ul>
          <li><span>Name</span><strong>{{ company.name || '-' }}</strong></li>
          <li><span>Industry</span><strong>{{ company.industry_type || '-' }}</strong></li>
          <li><span>Website</span><strong class="wrap">{{ company.website || '-' }}</strong></li>
        </ul>
        <p class="description">{{ company.description || 'No description provided.' }}</p>
      </article>

      <article class="panel">
        <h3>Approved Drives ({{ drives.length }})</h3>

        <p v-if="!drives.length" class="muted">No approved drives published by this company yet.</p>

        <ul v-else class="drive-list">
          <li v-for="drive in drives" :key="drive.id">
            <div class="drive-top">
              <button class="link-btn" type="button" @click="openDrive(drive.id)">
                {{ drive.title || `Drive #${drive.id}` }}
              </button>
              <span class="pill">{{ formatStatus(drive.drive_status || drive.status) }}</span>
            </div>
            <div class="drive-meta">
              <span>Start: {{ formatDate(drive.start_date) }}</span>
              <span>End: {{ formatDate(drive.end_date) }}</span>
            </div>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { getStudentCompanyDetail } from '@/api/student'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const company = ref(null)
const drives = ref([])

const loadCompany = async () => {
  loading.value = true
  try {
    const res = await getStudentCompanyDetail(route.params.companyId)
    company.value = res?.data?.company || null
    drives.value = Array.isArray(res?.data?.drives) ? res.data.drives : []
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load company detail')
    company.value = null
    drives.value = []
  } finally {
    loading.value = false
  }
}

const openDrive = (driveId) => {
  router.push({ name: 'student-drive-detail', params: { driveId } })
}

const goBack = () => {
  navigateBack(router, { name: 'student-drives' }, route.fullPath)
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
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

const formatStatus = (status) => {
  const token = String(status || '').trim().toLowerCase()
  return token || '-'
}

onMounted(async () => {
  await loadCompany()
})
</script>

<style scoped>
.student-company-page {
  display: grid;
  gap: 12px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.head h2 {
  margin: 0;
}

.head p {
  margin: 4px 0 0;
  color: #607094;
}

.box,
.panel {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.panel {
  min-width: 0;
}

.panel h3 {
  margin: 0 0 8px;
}

.panel ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.panel li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.description,
.wrap {
  color: #44516a;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.description {
  margin-top: 12px;
}

.muted {
  color: #5f6f8f;
}

.drive-list {
  gap: 10px;
}

.drive-list li {
  display: grid;
  gap: 6px;
  border: 1px solid #dfe6f7;
  border-radius: 10px;
  padding: 10px;
}

.drive-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.link-btn {
  border: none;
  background: transparent;
  color: #155eef;
  padding: 0;
  text-align: left;
  cursor: pointer;
  font-weight: 600;
}

.drive-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: #4f5f80;
  font-size: 13px;
}

.pill {
  background: #edf2ff;
  color: #2f66db;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  text-transform: capitalize;
}

.ghost {
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
  background: #edf2ff;
  color: #2f66db;
}

@media (max-width: 980px) {
  .content {
    grid-template-columns: 1fr;
  }

  .head {
    flex-direction: column;
    align-items: stretch;
  }

  .panel li {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
