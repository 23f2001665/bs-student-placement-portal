<template>
  <section class="applications-page">
    <AdminPageHeader
      title="Applications"
      subtitle="Browse applications across all students with quick filtering and sorting."
      :show-refresh="true"
      :refreshing="loading"
      :refresh-disabled="loading"
      @refresh="loadApplications"
    />

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search student, drive, company, or roll" />
      <select v-model="filters.status">
        <option value="">All status</option>
        <option value="applied">Applied</option>
        <option value="short_listed">Shortlisted</option>
        <option value="selected">Selected</option>
        <option value="rejected">Rejected</option>
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
            <strong>{{ summary.current }}</strong>
          </li>
          <li>
            <span>Completed Applications</span>
            <strong>{{ summary.history }}</strong>
          </li>
        </ul>
      </article>
      <article class="summary-card">
        <h4>Status on this Page</h4>
        <ul>
          <li v-for="(count, key) in pageStatusDistribution" :key="key">
            <span>{{ key }}</span>
            <strong>{{ count }}</strong>
          </li>
        </ul>
      </article>
    </section>

    <div v-if="loading" class="box">Loading applications...</div>
    <p v-else-if="applications.length === 0">No applications found for current filters.</p>

    <div v-else class="table-wrap">
      <table>
        <colgroup>
          <col class="col-app-id" />
          <col class="col-student" />
          <col class="col-drive" />
          <col class="col-company" />
          <col class="col-status" />
          <col class="col-applied-on" />
          <col class="col-action" />
        </colgroup>
        <thead>
          <tr>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('id')">
                <u>Application ID</u> {{ sortMark('id') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('student_name')">
                Student {{ sortMark('student_name') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('drive_title')">
                Drive {{ sortMark('drive_title') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('company_name')">
                Company {{ sortMark('company_name') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('status')">
                Status {{ sortMark('status') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('application_date')">
                Applied On {{ sortMark('application_date') }}
              </button>
            </th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody v-for="item in applications" :key="`admin-app-${item.application.id}`">
          <tr :class="historyItemClass(item.application.status)">
            <td><strong>#{{ item.application.id }}</strong></td>
            <td>
              <strong>{{ item.student?.name || '-' }}</strong>
              <p class="sub-line">{{ item.student?.roll || '-' }}</p>
            </td>
            <td>
              <strong>{{ item.drive?.title || 'Deleted drive' }}</strong>
              <p class="sub-line">#{{ item.drive?.id ?? '-' }}</p>
            </td>
            <td>{{ item.company?.name || 'Deleted company' }}</td>
            <td>
              <span class="status-pill" :class="applicationPillClass(item.application.status)">
                {{ item.application.status }}
              </span>
            </td>
            <td>{{ formatDate(item.application.application_date) }}</td>
            <td>
              <button class="ghost" type="button" @click="openDetail(item.application.id)">View Details</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination
      :page="pagination.page"
      :total-pages="pagination.total_pages"
      :disabled="loading"
      :show-jump="true"
      input-id="admin-applications-page-jump"
      @go="goToPage"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { getAdminApplications } from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminPagination from '@/components/admin/AdminPagination.vue'

const router = useRouter()
const loading = ref(false)
const applications = ref([])
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

const openDetail = (applicationId) => {
  router.push({ name: 'admin-application-detail', params: { applicationId } })
}

const loadApplications = async (page = pagination.page) => {
  loading.value = true
  try {
    const params = {
      page,
      limit: pageSize,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    }
    const res = await getAdminApplications(params)
    applications.value = res?.data?.applications || []

    const meta = res?.data?.pagination || {}
    pagination.page = meta.page || page
    pagination.limit = meta.limit || pageSize
    pagination.total = meta.total || applications.value.length
    pagination.total_pages = meta.total_pages || 1

    const serverSummary = res?.data?.summary || {}
    summary.current = typeof serverSummary.current === 'number' ? serverSummary.current : 0
    summary.history = typeof serverSummary.history === 'number' ? serverSummary.history : 0
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load applications')
  } finally {
    loading.value = false
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

const pageStatusDistribution = computed(() => {
  const counts = {
    applied: 0,
    shortlisted: 0,
    selected: 0,
    rejected: 0,
  }
  for (const item of applications.value) {
    const key = normalize(item?.application?.status || 'unknown')
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
  min-width: 980px;
}

.col-app-id {
  width: 10%;
}

.col-student {
  width: 18%;
}

.col-drive {
  width: 20%;
}

.col-company {
  width: 14%;
}

.col-status {
  width: 10%;
}

.col-applied-on {
  width: 18%;
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
  padding: 0;
}

.sub-line {
  margin: 3px 0 0;
  color: #5f7197;
  font-size: 0.85rem;
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

.pill-selected {
  color: #067647;
  background: #e7f6ee;
}

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

@media (max-width: 900px) {
  .filters {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  table {
    min-width: 860px;
  }
}
</style>
