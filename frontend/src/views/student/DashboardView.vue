<template>
  <section class="dashboard-page">
    <header class="head">
      <div>
        <h2>Welcome {{ student?.name || 'Student' }}</h2>
        <p>Quick view of opportunities and your progress.</p>
      </div>
      <div class="head-actions">
        <button class="ghost" type="button" :disabled="dashboardLoading || exportBusy" @click="loadDashboard">
          {{ dashboardLoading ? 'Refreshing...' : 'Refresh' }}
        </button>
        <button class="ghost" type="button" :disabled="exportBusy || dashboardLoading" @click="triggerExport">
          {{ exportBusy ? 'Preparing Export...' : 'Export Applications CSV' }}
        </button>
      </div>
    </header>

    <div class="stats">
      <article>
        <h3>{{ drives.length }}</h3>
        <p>Available Drives</p>
      </article>
      <article>
        <h3>{{ applications.length }}</h3>
        <p>Total Applications</p>
      </article>
      <article>
        <h3>{{ shortListedCount }}</h3>
        <p>Shortlisted</p>
      </article>
      <article>
        <h3>{{ selectedCount }}</h3>
        <p>Selected</p>
      </article>
    </div>

    <section class="charts-grid">
      <article class="chart-card">
        <h3>Applications Breakdown</h3>
        <p>Applied vs shortlisted vs rejected.</p>
        <div class="chart-body">
          <div class="pie" :style="applicationPieStyle" aria-label="Applications pie chart"></div>
          <ul class="legend">
            <li>
              <span class="dot dot-applied"></span>
              <span>Applied</span>
              <strong>{{ applicationCounts.applied }}</strong>
            </li>
            <li>
              <span class="dot dot-shortlisted"></span>
              <span>Shortlisted</span>
              <strong>{{ applicationCounts.shortlisted }}</strong>
            </li>
            <li>
              <span class="dot dot-rejected"></span>
              <span>Rejected</span>
              <strong>{{ applicationCounts.rejected }}</strong>
            </li>
          </ul>
        </div>
      </article>

      <article class="chart-card">
        <h3>Eligible Drives Breakdown</h3>
        <p>Active vs upcoming vs closed among eligible drives.</p>
        <div class="chart-body">
          <div class="pie" :style="eligibleDrivePieStyle" aria-label="Eligible drives pie chart"></div>
          <ul class="legend">
            <li>
              <span class="dot dot-active"></span>
              <span>Active</span>
              <strong>{{ eligibleDriveStatusCounts.active }}</strong>
            </li>
            <li>
              <span class="dot dot-upcoming"></span>
              <span>Upcoming</span>
              <strong>{{ eligibleDriveStatusCounts.upcoming }}</strong>
            </li>
            <li>
              <span class="dot dot-closed"></span>
              <span>Closed</span>
              <strong>{{ eligibleDriveStatusCounts.closed }}</strong>
            </li>
          </ul>
        </div>
      </article>
    </section>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { toast } from 'vue3-toastify'
import {
  downloadStudentApplicationsExport,
  getStudentApplications,
  getStudentApplicationsExportStatus,
  getStudentDrives,
  getStudentProfile,
  startStudentApplicationsExport,
} from '@/api/student'

const drives = ref([])
const applications = ref([])
const student = ref(null)
const dashboardLoading = ref(false)
const exportBusy = ref(false)
const exportTaskId = ref('')
const exportPoller = ref(null)
const exportStartedAt = ref(0)
const exportCompleted = ref(false)
const exportStatusCheckInProgress = ref(false)
const EXPORT_POLL_INTERVAL_MS = 2500
const EXPORT_MAX_WAIT_MS = 120000
const DRIVES_BATCH_LIMIT = 50

const normalizedStatus = (status) => String(status || '').toLowerCase()
const shortListedCount = computed(() =>
  applications.value.filter((a) => normalizedStatus(a.status) === 'shortlisted').length
)
const selectedCount = computed(() =>
  applications.value.filter((a) => normalizedStatus(a.status) === 'selected').length
)

const clamp = (value) => (Number.isFinite(value) && value > 0 ? value : 0)

const pieStyleFromSegments = (segments) => {
  const total = segments.reduce((acc, s) => acc + clamp(s.value), 0)
  if (total <= 0) {
    return {
      background: 'conic-gradient(#e4e8f2 0 360deg)',
    }
  }

  let cursor = 0
  const slices = segments
    .map((segment) => {
      const portion = (clamp(segment.value) / total) * 360
      const start = cursor
      const end = cursor + portion
      cursor = end
      return `${segment.color} ${start}deg ${end}deg`
    })
    .join(', ')

  return {
    background: `conic-gradient(${slices})`,
  }
}

const applicationCounts = computed(() => {
  const counts = {
    applied: 0,
    shortlisted: 0,
    rejected: 0,
  }

  for (const app of applications.value) {
    const status = normalizedStatus(app?.status)
    if (status === 'applied') counts.applied += 1
    if (status === 'shortlisted') counts.shortlisted += 1
    if (status === 'rejected') counts.rejected += 1
  }

  return counts
})

const applicationPieStyle = computed(() =>
  pieStyleFromSegments([
    { value: applicationCounts.value.applied, color: '#f59e0b' },
    { value: applicationCounts.value.shortlisted, color: '#2563eb' },
    { value: applicationCounts.value.rejected, color: '#6b7280' },
  ])
)

const eligibleDriveStatusCounts = computed(() => {
  const counts = {
    active: 0,
    upcoming: 0,
    closed: 0,
  }

  for (const drive of drives.value) {
    if (!drive?.eligible_for_apply) continue
    const status = normalizedStatus(drive?.drive_status || drive?.status)
    if (status === 'active') counts.active += 1
    else if (status === 'upcoming') counts.upcoming += 1
    else if (status === 'closed') counts.closed += 1
  }

  return counts
})

const eligibleDrivePieStyle = computed(() =>
  pieStyleFromSegments([
    { value: eligibleDriveStatusCounts.value.active, color: '#16a34a' },
    { value: eligibleDriveStatusCounts.value.upcoming, color: '#0ea5e9' },
    { value: eligibleDriveStatusCounts.value.closed, color: '#6b7280' },
  ])
)

const fetchAllStudentDrives = async () => {
  const firstRes = await getStudentDrives({ page: 1, limit: DRIVES_BATCH_LIMIT })
  const firstDrives = firstRes?.data?.drives || []
  const meta = firstRes?.data?.pagination || {}
  const totalPages = Number(meta.total_pages || 1)

  if (totalPages <= 1) return firstDrives

  const requests = []
  for (let page = 2; page <= totalPages; page += 1) {
    requests.push(getStudentDrives({ page, limit: DRIVES_BATCH_LIMIT }))
  }
  const rest = await Promise.all(requests)
  const extra = rest.flatMap((res) => res?.data?.drives || [])
  return [...firstDrives, ...extra]
}

const clearExportPoller = () => {
  if (exportPoller.value) {
    clearInterval(exportPoller.value)
    exportPoller.value = null
  }
}

const handleExportStatus = async () => {
  if (!exportTaskId.value || exportCompleted.value) return
  if (exportStatusCheckInProgress.value) return
  exportStatusCheckInProgress.value = true

  if (Date.now() - exportStartedAt.value > EXPORT_MAX_WAIT_MS) {
    clearExportPoller()
    exportBusy.value = false
    exportStatusCheckInProgress.value = false
    toast.warning('Export is taking longer than expected. Please try again in a moment.')
    return
  }

  try {
    const res = await getStudentApplicationsExportStatus(exportTaskId.value)
    const data = res?.data || {}
    const state = String(data.state || '').toLowerCase()

    if (state === 'success' && data.ready) {
      clearExportPoller()
      exportBusy.value = false
      exportCompleted.value = true
      await downloadStudentApplicationsExport(exportTaskId.value)
      toast.success(`Export ready (${data.row_count || 0} rows). Download started.`)
    } else if (state === 'failure' || state === 'revoked') {
      clearExportPoller()
      exportBusy.value = false
      exportCompleted.value = true
      toast.error(data.error || 'Export failed')
    }
  } catch (error) {
    clearExportPoller()
    exportBusy.value = false
    exportCompleted.value = true
    toast.error(error?.message || error?.response?.data?.error || 'Failed to download export')
  } finally {
    exportStatusCheckInProgress.value = false
  }
}

const loadDashboard = async () => {
  dashboardLoading.value = true
  try {
    const [profileResult, drivesResult, appsResult] = await Promise.allSettled([
      getStudentProfile(),
      fetchAllStudentDrives(),
      getStudentApplications(),
    ])

    if (profileResult.status === 'fulfilled') {
      const profileRes = profileResult.value
      student.value = profileRes.data.student || null
    }

    if (drivesResult.status === 'fulfilled') {
      const allDrives = drivesResult.value
      drives.value = allDrives || []
    }

    if (appsResult.status === 'fulfilled') {
      const appsRes = appsResult.value
      applications.value = appsRes.data.applications || []
    }

    if (profileResult.status === 'rejected' || drivesResult.status === 'rejected' || appsResult.status === 'rejected') {
      toast.error('Failed to load dashboard data')
    }
  } finally {
    dashboardLoading.value = false
  }
}

const triggerExport = async () => {
  if (exportBusy.value) return
  exportBusy.value = true
  exportCompleted.value = false
  try {
    const res = await startStudentApplicationsExport()
    exportTaskId.value = res?.data?.task_id || ''
    if (!exportTaskId.value) {
      throw new Error('missing task id')
    }

    toast.info('Export started. You will be alerted when CSV is ready.')
    exportStartedAt.value = Date.now()
    clearExportPoller()
    exportPoller.value = setInterval(handleExportStatus, EXPORT_POLL_INTERVAL_MS)
    await handleExportStatus()
  } catch (error) {
    exportBusy.value = false
    clearExportPoller()
    toast.error(error?.response?.data?.error || 'Failed to start export')
  }
}

onMounted(async () => {
  await loadDashboard()
})

onBeforeUnmount(() => {
  clearExportPoller()
})
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 12px;
}

.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.head-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

h2 {
  margin: 0;
}

p {
  margin: 0;
  color: #607094;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

article {
  background: #fff;
  border: 1px solid #e3e7ef;
  border-radius: 10px;
  padding: 12px;
}

h3 {
  margin: 0;
  color: #1b2a4b;
  font-size: 1.4rem;
}

article p {
  margin-top: 4px;
  font-size: 0.85rem;
}

.chart-card h3 {
  font-size: 1rem;
}

.chart-body {
  margin-top: 10px;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 14px;
}

.pie {
  width: 118px;
  height: 118px;
  border-radius: 999px;
  border: 1px solid #dbe3f2;
  position: relative;
}

.pie::after {
  content: '';
  position: absolute;
  inset: 24px;
  background: #fff;
  border-radius: 999px;
  border: 1px solid #e5ebf8;
}

.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.dot-applied {
  background: #f59e0b;
}

.dot-shortlisted {
  background: #2563eb;
}

.dot-rejected {
  background: #6b7280;
}

.dot-active {
  background: #16a34a;
}

.dot-upcoming {
  background: #0ea5e9;
}

.dot-closed {
  background: #6b7280;
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

.ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .stats {
    grid-template-columns: 1fr 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-body {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .legend {
    width: 100%;
  }
}

@media (max-width: 760px) {
  .head {
    flex-direction: column;
    align-items: stretch;
  }

  .stats {
    grid-template-columns: 1fr 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-body {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .legend {
    width: 100%;
  }
}
</style>

