<template>
  <section class="applications-page">
    <header class="page-header">
      <div>
        <h2>Applications</h2>
        <p class="subtext">Track current and historical applications with quick filters.</p>
      </div>
      <button class="ghost" type="button" :disabled="loadingApplications" @click="loadApplications()">
        {{ loadingApplications ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search drive title or description" />
      <select v-model="filters.status">
        <option value="">All status</option>
        <option value="applied">Applied</option>
        <option value="short_listed">Shortlisted</option>
        <option value="rejected">Rejected</option>
        <option value="selected">Selected</option>
      </select>
      <button class="ghost" type="submit">Apply</button>
      <button class="text-btn" type="button" @click="resetFilters">Reset</button>
    </form>

    <section class="summary-grid">
      <article class="summary-card">
        <h4>Result Summary</h4>
        <ul>
          <li>
            <span>Total Applications</span>
            <strong>{{ pagination.total }}</strong>
          </li>
          <li>
            <span>Currently In Progress</span>
            <strong>{{ currentCount }}</strong>
          </li>
          <li>
            <span>Completed Applications</span>
            <strong>{{ historyCount }}</strong>
          </li>
        </ul>
      </article>
      <article class="summary-card">
        <h4>Status on this Page</h4>
        <ul>
          <li v-for="(count, key) in statusDistribution" :key="key">
            <span>{{ key }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
    </section>

    <div v-if="loadingApplications" class="box">Loading applications...</div>
    <p v-else-if="applications.length === 0">No applications found for current filters.</p>

    <div v-else class="table-wrap">
      <table>
        <colgroup>
          <col class="col-drive-id" />
          <col class="col-drive-name" />
          <col class="col-company-name" />
          <col class="col-status" />
          <col class="col-applied-on" />
          <col class="col-action" />
        </colgroup>
        <thead>
          <tr>
            <th><button class="sort-btn" type="button" @click="toggleSort('drive_id')"><u>Drive ID</u> {{ sortMark('drive_id') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('drive_title')"><u>Drive Name</u> {{ sortMark('drive_title') }}</button></th>
            <th>Company</th>
            <th><button class="sort-btn" type="button" @click="toggleSort('status')">Status {{ sortMark('status') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('application_date')">Applied On {{ sortMark('application_date') }}</button></th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody v-for="app in applications" :key="`app-${app.id}`">
          <tr :class="historyItemClass(app.status)">
            <td>
              <router-link v-if="app.drive?.id" class="drive-link" :to="{ name: 'student-drive-detail', params: { driveId: app.drive.id } }">
                <strong>#{{ app.drive.id }}</strong>
              </router-link>
              <strong v-else>-</strong>
            </td>
            <td>
              <router-link v-if="app.drive?.id" class="drive-link" :to="{ name: 'student-drive-detail', params: { driveId: app.drive.id } }">
                <strong>{{ app.drive?.title || 'Deleted drive' }}</strong>
              </router-link>
              <strong v-else>{{ app.drive?.title || 'Deleted drive' }}</strong>
            </td>
            <td>{{ app.company?.name || 'Deleted company' }}</td>
            <td>
              <span class="status-pill" :class="applicationPillClass(app.status)">{{ app.status }}</span>
            </td>
            <td>{{ formatDate(app.application_date) }}</td>
            <td>
              <button class="ghost" type="button" @click="openApplicationDetail(app.id)">View Details</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer v-if="!loadingApplications && pagination.total_pages > 1" class="pagination">
      <button class="ghost" type="button" :disabled="pagination.page === 1" @click="goToPage(pagination.page - 1)">
        Previous
      </button>
      <span>Page {{ pagination.page }} / {{ pagination.total_pages }}</span>
      <div class="pagination-jump">
        <label for="applications-page-jump">Jump to</label>
        <input
          id="applications-page-jump"
          v-model.number="jumpToPageInput"
          type="number"
          min="1"
          :max="pagination.total_pages"
          @keyup.enter="submitPageJump"
        />
        <button class="ghost" type="button" @click="submitPageJump">Go</button>
      </div>
      <button
        class="ghost"
        type="button"
        :disabled="pagination.page === pagination.total_pages"
        @click="goToPage(pagination.page + 1)"
      >
        Next
      </button>
    </footer>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { getStudentApplications } from '@/api/student'

const router = useRouter()
const loadingApplications = ref(false)
const applications = ref([])
const jumpToPageInput = ref(1)
const pageSize = 10
const summary = reactive({
  current: 0,
  history: 0,
})

const filters = reactive({
  search: '',
  status: '',
  sort_by: 'application_date',
  sort_order: 'desc',
})

const pagination = reactive({
  page: 1,
  limit: pageSize,
  total: 0,
  total_pages: 1,
})

const normalize = (value) => String(value || '').toLowerCase().replace(/[_\s]/g, '').trim()

const isHistoryStatus = (status) => {
  const s = normalize(status)
  return s === 'selected' || s === 'rejected'
}

const currentCount = computed(() => summary.current)
const historyCount = computed(() => summary.history)

const toggleSort = async (key) => {
  if (filters.sort_by === key) {
    filters.sort_order = filters.sort_order === 'asc' ? 'desc' : 'asc'
  } else {
    filters.sort_by = key
    filters.sort_order = 'asc'
  }
  await loadApplications(1)
}

const sortMark = (key) => {
  if (filters.sort_by !== key) return ''
  return filters.sort_order === 'asc' ? '^' : 'v'
}

const openApplicationDetail = (applicationId) => {
  router.push({ name: 'student-application-detail', params: { applicationId } })
}

const loadApplications = async (page = pagination.page) => {
  loadingApplications.value = true
  try {
    const params = {
      page,
      limit: pageSize,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    }
    const res = await getStudentApplications(params)
    applications.value = res.data.applications || []

    const meta = res.data.pagination || {}
    pagination.page = meta.page || page
    pagination.limit = meta.limit || pageSize
    pagination.total = meta.total || applications.value.length
    pagination.total_pages = meta.total_pages || 1
    jumpToPageInput.value = pagination.page

    const serverSummary = res.data.summary || {}
    if (typeof serverSummary.current === 'number') {
      summary.current = serverSummary.current
    } else {
      summary.current = applications.value.filter((app) => !isHistoryStatus(app.status)).length
    }

    if (typeof serverSummary.history === 'number') {
      summary.history = serverSummary.history
    } else {
      summary.history = applications.value.filter((app) => isHistoryStatus(app.status)).length
    }
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load applications')
  } finally {
    loadingApplications.value = false
  }
}

const applyFilters = async () => {
  await loadApplications(1)
}

const resetFilters = async () => {
  filters.search = ''
  filters.status = ''
  filters.sort_by = 'application_date'
  filters.sort_order = 'desc'
  await loadApplications(1)
}

const goToPage = async (page) => {
  const nextPage = Math.min(Math.max(1, page), pagination.total_pages)
  await loadApplications(nextPage)
}

const submitPageJump = async () => {
  const requestedPage = Number(jumpToPageInput.value)
  if (!Number.isFinite(requestedPage)) {
    jumpToPageInput.value = pagination.page
    return
  }
  const nextPage = Math.min(Math.max(1, Math.trunc(requestedPage)), pagination.total_pages)
  jumpToPageInput.value = nextPage
  if (nextPage !== pagination.page) {
    await goToPage(nextPage)
  }
}

const formatDate = (value) => {
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

const historyItemClass = (status) => {
  const s = normalize(status)
  if (s === 'selected') return 'app-selected'
  if (s === 'shortlisted') return 'app-shortlisted'
  if (s === 'rejected') return 'app-rejected'
  if (s === 'applied') return 'app-applied'
  return ''
}

const applicationPillClass = (status) => {
  const s = normalize(status)
  if (s === 'selected') return 'pill-selected'
  if (s === 'shortlisted') return 'pill-shortlisted'
  if (s === 'rejected') return 'pill-inactive'
  if (s === 'applied') return 'pill-pending'
  return 'pill-neutral'
}

const statusDistribution = computed(() => {
  const counts = {
    applied: 0,
    shortlisted: 0,
    selected: 0,
    rejected: 0,
  }
  for (const app of applications.value) {
    const key = normalize(app.status || 'unknown') || 'unknown'
    if (Object.prototype.hasOwnProperty.call(counts, key)) {
      counts[key] += 1
    }
  }
  return counts
})

onMounted(async () => {
  await loadApplications()
})
</script>

<style scoped>
.applications-page {
  display: grid;
  gap: 14px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.page-header h2 {
  margin: 0;
}

.subtext {
  margin: 4px 0 0;
  color: #607094;
}

.drive-link {
  color: inherit;
  text-decoration: underline;
}

.filters {
  display: grid;
  grid-template-columns: 1.6fr minmax(160px, 1fr) auto auto;
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-card,
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
  margin: 0;
  padding: 0;
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
  table-layout: fixed;
  min-width: 760px;
}

.col-drive-id {
  width: 8%;
}

.col-drive-name {
  width: 25%;
}

.col-company-name {
  width: 17%;
}

.col-status {
  width: 10%;
}

.col-applied-on {
  width: 25%;
}

.col-action {
  width: 15%;
}

th,
td {
  padding: 10px;
  border-bottom: 1px solid #e9eef8;
  text-align: left;
  vertical-align: middle;
}

td {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

th {
  background: #f3f7ff;
  color: #2f4676;
  font-size: 0.88rem;
}

.sort-btn {
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

tbody tr.app-selected {
  background: #f2fbf6;
}

tbody tr.app-shortlisted {
  background: #f3f8ff;
}

tbody tr.app-applied {
  background: #fffdf5;
}

tbody tr.app-rejected {
  background: #f3f4f6;
}

.status-pill {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.pill-active,
.pill-selected {
  color: #067647;
  background: #e7f6ee;
}

.pill-upcoming,
.pill-shortlisted {
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

.ghost,
.text-btn {
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}

.ghost {
  background: #edf2ff;
  color: #2f66db;
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

.pagination-jump {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.pagination-jump label {
  color: #4f5f7a;
  font-size: 0.9rem;
}

.pagination-jump input {
  width: 70px;
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 6px 8px;
  font: inherit;
}

.ghost:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 760px) {
  .filters {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  table {
    min-width: 680px;
  }
}
</style>

