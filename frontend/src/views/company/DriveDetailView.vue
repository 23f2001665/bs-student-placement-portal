<template>
  <section class="drive-detail-page">
    <header class="page-header">
      <div>
        <h2>{{ drive?.title || 'Drive Detail' }}</h2>
        <p v-if="drive">{{ drive.description || 'No description' }}</p>
      </div>
      <div class="header-actions">
        <button class="ghost" type="button" @click="editDrive">Edit Drive</button>
        <button class="danger" type="button" @click="deleteDrive">Delete Drive</button>
        <button class="ghost" type="button" @click="goBack">Back to Drives</button>
      </div>
    </header>

    <section v-if="drive" class="meta-grid">
      <article class="meta-card">
        <h4>Drive Info</h4>
        <ul>
          <li>
            <span>Status</span>
            <strong><span class="status-pill" :class="statusPillClass(drive.status)">{{ formatDriveStatus(drive.status) }}</span></strong>
          </li>
          <li>
            <span>Approval</span>
            <strong><span class="status-pill" :class="approvalPillClass(drive.approval_status)">{{ drive.approval_status }}</span></strong>
          </li>
          <li><span>Work mode</span><strong>{{ drive.work_mode }}</strong></li>
          <li><span>Start</span><strong>{{ formatDate(drive.start_date) }}</strong></li>
          <li><span>End</span><strong>{{ formatDate(drive.end_date) }}</strong></li>
          <li><span>Min CGPA</span><strong>{{ drive.min_cgpa ?? '-' }}</strong></li>
          <li><span>Max applications</span><strong>{{ drive.max_applications ?? '-' }}</strong></li>
        </ul>
      </article>
      <article class="meta-card" v-if="summary">
        <h4>Application Summary</h4>
        <ul>
          <li><span>Total</span><strong>{{ summary.application_total }}</strong></li>
          <li
            v-for="(count, status) in summary.application_status_distribution"
            :key="status"
          >
            <span>{{ status }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
    </section>

    <form class="status-filter" @submit.prevent="loadApplications">
      <label for="status">Application status</label>
      <select id="status" v-model="statusFilter">
        <option value="">All</option>
        <option value="applied">Applied</option>
        <option value="shortlisted">Shortlisted</option>
        <option value="rejected">Rejected</option>
        <option value="selected">Selected</option>
      </select>
      <button class="ghost" type="submit">Apply</button>
    </form>

    <div v-if="loadingApps" class="box">Loading applications...</div>
    <div v-else-if="applications.length === 0" class="box">No applications for current filter.</div>
    <ul v-else class="app-list">
      <li v-for="app in applications" :key="app.id" class="app-card" :class="applicationCardClass(app.status)">
        <div>
          <h4>Application #{{ app.id }}</h4>
          <p>
            {{ app.student?.name || 'Student' }}
            <span v-if="app.student?.roll">({{ app.student.roll }})</span>
          </p>
          <small class="meta-line">
            <span class="status-pill" :class="applicationPillClass(app.status)">{{ app.status }}</span>
            <span>{{ app.student?.branch || '-' }}</span>
            <span>{{ app.student?.cgpa ?? '-' }} CGPA</span>
          </small>
        </div>
        <button class="primary" type="button" @click="openApplication(app.id)">View Detail</button>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { deleteCompanyDrive, getDriveApplications, getDriveSummary } from '@/api/company'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const loadingApps = ref(false)
const driveData = ref(null)
const applications = ref([])
const statusFilter = ref('')

const driveId = computed(() => Number(route.params.driveId))
const drive = computed(() => driveData.value?.drive || null)
const summary = computed(() => driveData.value?.summary || null)

const loadSummary = async () => {
  try {
    const res = await getDriveSummary(driveId.value)
    driveData.value = res.data
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load drive summary')
  }
}

const loadApplications = async () => {
  loadingApps.value = true
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : undefined
    const res = await getDriveApplications(driveId.value, params)
    applications.value = res.data.applications || []
  } catch (error) {
    applications.value = []
    toast.error(error?.response?.data?.error || 'Failed to load applications')
  } finally {
    loadingApps.value = false
  }
}

const openApplication = (applicationId) => {
  router.push({ name: 'company-application-detail', params: { applicationId } })
}

const editDrive = () => {
  router.push({ name: 'company-drive-edit', params: { driveId: driveId.value } })
}

const deleteDrive = async () => {
  try {
    await deleteCompanyDrive(driveId.value)
    toast.success('Drive deleted')
    router.push('/company/drives')
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to delete drive')
  }
}

const goBack = () => {
  navigateBack(router, '/company/drives', route.fullPath)
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

const normalize = (value) => String(value || '').toLowerCase().trim()

const formatDriveStatus = (status) => {
  const s = normalize(status)
  if (!s) return 'unknown'
  return s
}

const statusPillClass = (status) => {
  const s = normalize(status)
  if (s === 'active') return 'pill-active'
  if (s === 'upcoming') return 'pill-pending'
  if (s === 'pending') return 'pill-pending'
  if (s === 'closed' || s === 'cancelled') return 'pill-inactive'
  return 'pill-neutral'
}

const approvalPillClass = (status) => {
  const s = normalize(status)
  if (s === 'approved') return 'pill-active'
  if (s === 'pending') return 'pill-pending'
  if (s === 'rejected') return 'pill-inactive'
  return 'pill-neutral'
}

const applicationCardClass = (status) => {
  const s = normalize(status)
  if (s === 'selected') return 'app-selected'
  if (s === 'shortlisted') return 'app-shortlisted'
  if (s === 'applied') return 'app-applied'
  if (s === 'rejected') return 'app-rejected'
  return ''
}

const applicationPillClass = (status) => {
  const s = normalize(status)
  if (s === 'selected') return 'pill-active'
  if (s === 'shortlisted') return 'pill-upcoming'
  if (s === 'applied') return 'pill-pending'
  if (s === 'rejected') return 'pill-inactive'
  return 'pill-neutral'
}

onMounted(async () => {
  await loadSummary()
  await loadApplications()
})
</script>

<style scoped>
.drive-detail-page {
  display: grid;
  gap: 14px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.meta-card,
.box,
.app-card {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.meta-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 6px;
}

.meta-card li {
  display: flex;
  justify-content: space-between;
}

.readonly-note {
  margin: 4px 0 10px;
  font-size: 0.83rem;
  color: #5f6f8f;
}

.status-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-filter select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 8px 10px;
}

.app-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.app-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.app-card.app-selected {
  background: #f2fbf6;
  border-color: #cdebd8;
}

.app-card.app-shortlisted {
  background: #f3f8ff;
  border-color: #d7e5ff;
}

.app-card.app-applied {
  background: #fffdf5;
  border-color: #eee1bf;
}

.app-card.app-rejected {
  background: #f3f4f6;
  border-color: #dadde3;
}

.meta-line {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.status-pill {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.pill-active {
  color: #067647;
  background: #e7f6ee;
}

.pill-upcoming {
  color: #175cd3;
  background: #e8f1ff;
}

.pill-pending {
  color: #9a5d00;
  background: #fff0d8;
}

.pill-inactive {
  color: #5a6373;
  background: #e9ecf1;
}

.pill-neutral {
  color: #44516a;
  background: #eaf0fa;
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

@media (max-width: 900px) {
  .meta-grid {
    grid-template-columns: 1fr;
  }

  .app-card,
  .page-header {
    flex-direction: column;
  }
}
</style>
