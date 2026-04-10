<template>
  <section class="drives-page">
    <header class="page-header">
      <h2>Drive Management</h2>
      <div class="header-actions">
        <button class="ghost" type="button" :disabled="loading" @click="loadDrives(currentPage)">
          {{ loading ? 'Refreshing...' : 'Refresh' }}
        </button>
        <button class="primary" type="button" @click="goToCreateDrive">New Drive</button>
      </div>
    </header>

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search title or description" />
      <select v-model="filters.status">
        <option value="">All status</option>
        <option value="pending">Pending</option>
        <option value="active">Active</option>
        <option value="closed">Closed</option>
        <option value="cancelled">Cancelled</option>
      </select>
      <select v-model="filters.approval_status">
        <option value="">All approvals</option>
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
      </select>
      <select v-model="filters.work_mode">
        <option value="">All modes</option>
        <option value="onsite">Onsite</option>
        <option value="hybrid">Hybrid</option>
        <option value="remote">Remote</option>
      </select>
      <button class="ghost" type="submit">Apply</button>
      <button class="text-btn" type="button" @click="resetFilters">Reset</button>
    </form>

    <section v-if="chartSummary" class="summary-grid">
      <article class="summary-card">
        <h4>Drive Status</h4>
        <ul>
          <li v-for="(count, key) in chartSummary.drive_status_distribution" :key="`ds-${key}`">
            <span>{{ formatDriveStatus(key) }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
      <article class="summary-card">
        <h4>Approval Status</h4>
        <ul>
          <li v-for="(count, key) in chartSummary.drive_approval_distribution" :key="`da-${key}`">
            <span>{{ formatDriveStatus(key) }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
      <article class="summary-card">
        <h4>Applications</h4>
        <ul>
          <li v-for="(count, key) in chartSummary.application_status_distribution" :key="`app-${key}`">
            <span>{{ formatDriveStatus(key) }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
    </section>

    <div v-if="loading" class="box">Loading drives...</div>
    <p v-else-if="drives.length === 0">No drives found for current filters.</p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Drive Status</th>
            <th>Approval</th>
            <th>Mode</th>
            <th>Applications</th>
            <th>Timeline</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in drives" :key="item.drive.id">
            <td>{{ item.drive.title }}</td>
            <td>
              <span class="status-pill" :class="statusPillClass(item.drive.status)">{{ formatDriveStatus(item.drive.status) }}</span>
            </td>
            <td>
              <span class="status-pill" :class="approvalPillClass(item.drive.approval_status)">{{ item.drive.approval_status }}</span>
            </td>
            <td>
              <span class="mode-pill">{{ item.drive.work_mode }}</span>
            </td>
            <td>{{ item.summary.application_total }}</td>
            <td>{{ formatDate(item.drive.start_date) }} to {{ formatDate(item.drive.end_date) }}</td>
            <td>
              <div class="row-actions">
                <button class="ghost" type="button" @click="openDrive(item.drive.id)">Detail</button>
                <button class="ghost" type="button" @click="editDrive(item.drive.id)">Edit</button>
                <button class="danger" type="button" @click="removeDrive(item.drive.id)">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer v-if="!loading && totalPages > 1" class="pagination">
      <button class="ghost" type="button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
        Previous
      </button>
      <span>Page {{ currentPage }} / {{ totalPages }}</span>
      <button class="ghost" type="button" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
        Next
      </button>
    </footer>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { deleteCompanyDrive, getCompanyDriveSummaries } from '@/api/company'

const router = useRouter()
const loading = ref(false)
const drives = ref([])
const chartSummary = ref(null)
const currentPage = ref(1)
const pageSize = 10
const totalPages = ref(1)

const filters = reactive({
  search: '',
  status: '',
  approval_status: '',
  work_mode: '',
})

const loadDrives = async (page = currentPage.value) => {
  loading.value = true
  try {
    const params = {
      page,
      limit: pageSize,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.approval_status ? { approval_status: filters.approval_status } : {}),
      ...(filters.work_mode ? { work_mode: filters.work_mode } : {}),
    }
    const res = await getCompanyDriveSummaries(params)
    drives.value = res.data.items || []
    chartSummary.value = res.data.chart_summary || null

    const meta = res.data.pagination || {}
    currentPage.value = meta.page || page
    totalPages.value = meta.total_pages || 1
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load drive summaries')
  } finally {
    loading.value = false
  }
}

const applyFilters = async () => {
  await loadDrives(1)
}

const resetFilters = async () => {
  filters.search = ''
  filters.status = ''
  filters.approval_status = ''
  filters.work_mode = ''
  await loadDrives(1)
}

const removeDrive = async (driveId) => {
  try {
    await deleteCompanyDrive(driveId)
    toast.success('Drive deleted')
    await loadDrives(currentPage.value)
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to delete drive')
  }
}

const openDrive = (driveId) => {
  router.push({ name: 'company-drive-detail', params: { driveId } })
}

const editDrive = (driveId) => {
  router.push({ name: 'company-drive-edit', params: { driveId } })
}

const goToPage = (page) => {
  const nextPage = Math.min(Math.max(1, page), totalPages.value)
  loadDrives(nextPage)
}

const goToCreateDrive = () => {
  router.push('/company/drives/create')
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
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
  if (s === 'closed') return 'pill-closed'
  if (s === 'cancelled') return 'pill-inactive'
  return 'pill-neutral'
}

const approvalPillClass = (status) => {
  const s = normalize(status)
  if (s === 'approved') return 'pill-approved'
  if (s === 'pending') return 'pill-pending'
  if (s === 'rejected') return 'pill-inactive'
  return 'pill-neutral'
}

onMounted(async () => {
  await loadDrives()
})
</script>

<style scoped>
.drives-page {
  display: grid;
  gap: 14px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filters {
  display: grid;
  grid-template-columns: 1.3fr repeat(3, minmax(120px, 1fr)) auto auto;
  gap: 8px;
}

.filters input,
.filters select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 9px 10px;
  font: inherit;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.summary-card {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.box {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.summary-card h4 {
  margin: 0 0 8px;
}

.summary-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 6px;
}

.summary-card li {
  display: flex;
  justify-content: space-between;
}

.table-wrap {
  overflow: auto;
  border: 1px solid #dde4f2;
  border-radius: 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 920px;
}

th,
td {
  padding: 10px;
  border-bottom: 1px solid #e9eef8;
  text-align: left;
  vertical-align: middle;
}

th {
  background: #f3f7ff;
  color: #2f4676;
  font-size: 0.88rem;
}

.status-pill,
.mode-pill {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
}

.mode-pill,
.pill-neutral {
  color: #44516a;
  background: #eaf0fa;
}

.pill-active,
.pill-approved {
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

.pill-closed {
  color: #475467;
  background: #e4e7ec;
}

.pill-inactive {
  color: #5a6373;
  background: #e9ecf1;
}

.row-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.primary,
.ghost,
.danger,
.text-btn {
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

.danger {
  background: #fee4e2;
  color: #b42318;
}

.text-btn {
  background: transparent;
  color: #5b6783;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

@media (max-width: 900px) {
  .filters {
    grid-template-columns: 1fr 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>

