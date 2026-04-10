<template>
  <section class="drives-page">
    <header class="page-header">
      <div>
        <h2>Drives</h2>
        <p class="subtext">Browse approved drives and apply directly.</p>
      </div>
      <button class="ghost" type="button" :disabled="loadingDrives" @click="refreshPage">
        {{ loadingDrives ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search title or description" />
      <select v-model="filters.status">
        <option value="">All status</option>
        <option value="upcoming">Upcoming</option>
        <option value="active">Active</option>
        <option value="closed">Closed</option>
      </select>
      <select v-model="filters.work_mode">
        <option value="">All modes</option>
        <option value="onsite">Onsite</option>
        <option value="hybrid">Hybrid</option>
        <option value="remote">Remote</option>
      </select>
      <select v-model="filters.application_filter">
        <option value="">All candidates</option>
        <option value="applied">Applied</option>
        <option value="not_applied_but_eligible">Not Applied but Eligible</option>
        <option value="not_eligible">Not Eligible</option>
      </select>
      <button class="ghost" type="submit">Apply</button>
      <button class="text-btn" type="button" @click="resetFilters">Reset</button>
    </form>

    <section class="summary-grid">
      <article class="summary-card">
        <h4>Result Summary</h4>
        <ul>
          <li>
            <span>Total matching</span>
            <strong>{{ pagination.total }}</strong>
          </li>
          <li>
            <span>On this page</span>
            <strong>{{ filteredDrives.length }}</strong>
          </li>
          <li>
            <span>Applied (overall)</span>
            <strong>{{ applications.length }}</strong>
          </li>
        </ul>
      </article>
      <article class="summary-card">
        <h4>Status of this Page</h4>
        <ul>
          <li v-for="(count, key) in pageStatusCounts" :key="`status-${key}`">
            <span>{{ key }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
    </section>

    <div v-if="loadingDrives" class="box">Loading drives...</div>
    <p v-else-if="filteredDrives.length === 0">No approved drives available right now.</p>

    <div v-else class="table-wrap">
      <table>
        <colgroup>
          <col class="col-drive-id" />
          <col class="col-drive-name" />
          <col class="col-created-on" />
          <col class="col-start-date" />
          <col class="col-end-date" />
          <col class="col-status" />
          <col class="col-eligibility" />
          <col class="col-mode" />
          <col class="col-action" />
        </colgroup>
        <thead>
          <tr>
            <th>
              <button class="sort-btn" :class="{ 'is-active': filters.sort_by === 'id' }" type="button" @click="toggleSort('id')">
                <u>Drive ID</u> {{ sortMark('id') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': filters.sort_by === 'title' }" type="button" @click="toggleSort('title')">
                <u>Drive Name</u> {{ sortMark('title') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': filters.sort_by === 'create_date' }" type="button" @click="toggleSort('create_date')">
                <u>Created</u> {{ sortMark('create_date') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': filters.sort_by === 'start_date' }" type="button" @click="toggleSort('start_date')">
                <u>Start</u> {{ sortMark('start_date') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': filters.sort_by === 'end_date' }" type="button" @click="toggleSort('end_date')">
                <u>End</u> {{ sortMark('end_date') }}
              </button>
            </th>
            <th>Drive Status</th>
            <th>Eligibility</th>
            <th>Mode</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="drive in filteredDrives"
            :key="drive.id"
            :class="[
              driveRowClass(drive),
              {
                'row-ineligible': !isEligibleForApply(drive),
                'row-priority': isPriorityDrive(drive),
              },
            ]"
            :title="ineligibleReasonText(drive)"
          >
            <td>
              <router-link class="drive-link" :to="{ name: 'student-drive-detail', params: { driveId: drive.id } }">
                <strong>#{{ drive.id }}</strong>
              </router-link>
            </td>
            <td>
              <router-link class="drive-link" :to="{ name: 'student-drive-detail', params: { driveId: drive.id } }">
                <strong>{{ drive.title }}</strong>
              </router-link>
            </td>
            <td>{{ formatDate(drive.create_date) }}</td>
            <td>{{ formatDate(drive.start_date) }}</td>
            <td>{{ formatDate(drive.end_date) }}</td>
            <td>
              <span class="status-pill" :class="driveStatusPillClass(getDriveStatus(drive))">{{ formatDriveStatus(getDriveStatus(drive)) }}</span>
            </td>
            <td>
              <span class="status-pill" :class="isEligibleForApply(drive) ? 'pill-eligible' : 'pill-not-eligible'">
                {{ isEligibleForApply(drive) ? 'Eligible' : 'Not Eligible' }}
              </span>
            </td>
            <td>
              <span class="mode-pill">{{ drive.work_mode }}</span>
            </td>
            <td class="action-cell">
                <button
                  class="ghost"
                  type="button"
                  @click="openDriveDetail(drive.id)"
                >
                  Detail
                </button>
                <span v-if="isApplied(drive)" class="status-pill applied-mini">Applied</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer v-if="!loadingDrives && pagination.total_pages > 1" class="pagination">
      <button class="ghost" type="button" :disabled="pagination.page === 1" @click="goToPage(pagination.page - 1)">
        Previous
      </button>
      <span>Page {{ pagination.page }} / {{ pagination.total_pages }}</span>
      <div class="pagination-jump">
        <label for="drives-page-jump">Jump to</label>
        <input
          id="drives-page-jump"
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
import { getStudentApplications, getStudentDrives } from '@/api/student'

const router = useRouter()
const loadingDrives = ref(false)
const drives = ref([])
const applications = ref([])
const jumpToPageInput = ref(1)
const pageSize = 10

const filters = reactive({
  search: '',
  status: '',
  work_mode: '',
  application_filter: '',
  sort_by: 'priority',
  sort_order: 'asc',
})

const pagination = reactive({
  page: 1,
  limit: pageSize,
  total: 0,
  total_pages: 1,
})

const appliedDriveIds = computed(() => {
  const ids = new Set()
  for (const app of applications.value) {
    if (app.drive_id != null) ids.add(app.drive_id)
  }
  return ids
})

const isApplied = (drive) => {
  if (drive && typeof drive === 'object') {
    if (drive.already_applied === true) return true
    return appliedDriveIds.value.has(drive.id)
  }
  return appliedDriveIds.value.has(drive)
}
const isEligibleForApply = (drive) => Boolean(drive?.eligible_for_apply)

const filteredDrives = computed(() => drives.value)

const getErrorMessage = (error, fallback) => {
  const payload = error?.response?.data || {}
  return payload.error || payload.details || fallback
}

const ineligibleReasonText = (drive) => {
  if (isEligibleForApply(drive)) return ''
  const reasons = drive?.eligibility_reasons || []
  return reasons.length ? reasons.join(' | ') : 'Not eligible for this drive'
}

const toggleSort = async (key) => {
  if (filters.sort_by === key) {
    filters.sort_order = filters.sort_order === 'asc' ? 'desc' : 'asc'
  } else {
    filters.sort_by = key
    filters.sort_order = 'asc'
  }
  await loadDrives(1)
}

const sortMark = (key) => {
  if (filters.sort_by !== key) return ''
  return filters.sort_order === 'asc' ? '^' : 'v'
}

const loadDrives = async (page = pagination.page) => {
  loadingDrives.value = true
  try {
    const params = {
      page,
      limit: pageSize,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.work_mode ? { work_mode: filters.work_mode } : {}),
      ...(filters.application_filter ? { application_filter: filters.application_filter } : {}),
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    }
    const res = await getStudentDrives(params)
    drives.value = res.data.drives || []

    const meta = res.data.pagination || {}
    pagination.page = meta.page || page
    pagination.limit = meta.limit || pageSize
    pagination.total = meta.total || drives.value.length
    pagination.total_pages = meta.total_pages || 1
    jumpToPageInput.value = pagination.page
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to load drives'))
  } finally {
    loadingDrives.value = false
  }
}

const loadApplications = async () => {
  try {
    const res = await getStudentApplications()
    applications.value = res.data.applications || []
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to load applications'))
  }
}

const refreshPage = async () => {
  await Promise.all([loadDrives(pagination.page), loadApplications()])
}

const applyFilters = async () => {
  await loadDrives(1)
}

const resetFilters = async () => {
  filters.search = ''
  filters.status = ''
  filters.work_mode = ''
  filters.application_filter = ''
  filters.sort_by = 'priority'
  filters.sort_order = 'asc'
  await loadDrives(1)
}

const goToPage = async (page) => {
  const nextPage = Math.min(Math.max(1, page), pagination.total_pages)
  await loadDrives(nextPage)
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

const openDriveDetail = (driveId) => {
  router.push({ name: 'student-drive-detail', params: { driveId } })
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

const getDriveStatus = (drive) => drive?.drive_status || drive?.status || 'unknown'
const isPriorityDrive = (drive) => {
  const status = normalize(getDriveStatus(drive))
  return isEligibleForApply(drive) && !isApplied(drive) && status === 'active'
}

const formatDriveStatus = (status) => {
  const s = normalize(status)
  if (!s) return 'unknown'
  return s
}

const driveStatusPillClass = (status) => {
  const s = normalize(status)
  if (s === 'active') return 'pill-active'
  if (s === 'upcoming') return 'pill-pending'
  if (s === 'pending') return 'pill-pending'
  if (s === 'closed' || s === 'cancelled') return 'pill-inactive'
  return 'pill-neutral'
}

const driveRowClass = (drive) => {
  const status = normalize(getDriveStatus(drive))
  if (status === 'active') return 'row-active'
  if (status === 'upcoming') return 'row-upcoming'
  if (status === 'pending') return 'row-pending'
  if (status === 'closed') return 'row-closed'
  return 'row-neutral'
}

const pageStatusCounts = computed(() => {
  const counts = {
    active: 0,
    upcoming: 0,
    closed: 0,
    pending: 0,
  }
  for (const drive of filteredDrives.value) {
    const key = formatDriveStatus(getDriveStatus(drive))
    if (Object.prototype.hasOwnProperty.call(counts, key)) {
      counts[key] += 1
    }
  }
  return counts
})

onMounted(async () => {
  await Promise.all([loadDrives(), loadApplications()])
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

.filters {
  display: grid;
  grid-template-columns: 1.25fr repeat(3, minmax(120px, 1fr)) auto auto;
  align-items: end;
  gap: 6px;
}

.filters input,
.filters select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 8px 10px;
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
  min-width: 920px;
}

.col-drive-id {
  width: 5%;
}

.col-drive-name {
  width: 15%;
}

.col-created-on {
  width: 10%;
}

.col-start-date {
  width: 10%;
}

.col-end-date {
  width: 10%;
}

.col-status {
  width: 8%;
}

.col-eligibility {
  width: 7%;
}

.col-mode {
  width: 8%;
}

.col-action {
  width: 10%;
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
  padding: 0 0 2px;
  border-bottom: 2px solid transparent;
}

.sort-btn.is-active {
  border-bottom-color: #2f66db;
}

.mode-pill {
  color: #1d4f91;
  background: #e6f0ff;
  border-radius: 999px;
  padding: 2px 8px;
  font-weight: 600;
}

.drive-link {
  color: inherit;
  text-decoration: none;
}

.drive-link:hover {
  text-decoration: underline;
}

.status-pill {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
}

.row-active {
  background: #f4fbf7;
}

.row-upcoming {
  background: #f2f7ff;
}

.row-pending {
  background: #fff9ec;
}

.row-closed {
  background: #f3f4f6;
}

.row-neutral {
  background: #ffffff;
}

.row-priority td {
  background: #e9f9ee;
}

.row-ineligible td {
  color: #4f5f7a;
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

.pill-eligible {
  color: #067647;
  background: #e7f6ee;
}

.pill-not-eligible {
  color: #8a2d2d;
  background: #fbe6e6;
}

.primary,
.ghost,
.text-btn {
  border-radius: 8px;
  padding: 8px 10px;
  font-weight: 600;
  cursor: pointer;
}

.action-cell {
  white-space: normal;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  overflow: visible;
  text-overflow: clip;
  gap: 8px;
}

.applied-mini {
  color: #175cd3;
  background: #e8f1ff;
  font-size: 10px;
  padding: 1px 7px;
}

.primary {
  border: none;
  background: #2f66db;
  color: #fff;
  white-space: nowrap;
}

.ghost {
  border: none;
  background: #edf2ff;
  color: #2f66db;
}

.text-btn {
  border: none;
  background: transparent;
  color: #5b6783;
}

.primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination > span {
  white-space: nowrap;
}

.pagination-jump {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
}

.pagination-jump label {
  color: #4f5f7a;
  font-size: 0.9rem;
  white-space: nowrap;
}

.pagination-jump input {
  width: 64px;
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 6px 8px;
  font: inherit;
}

.ghost:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 980px) {
  .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filters .ghost,
  .filters .text-btn {
    width: 100%;
  }

  table {
    min-width: 840px;
  }

  th,
  td {
    padding: 8px;
  }
}

@media (max-width: 760px) {
  .filters {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  table {
    min-width: 760px;
  }

  .pagination {
    justify-content: flex-start;
  }
}
</style>
