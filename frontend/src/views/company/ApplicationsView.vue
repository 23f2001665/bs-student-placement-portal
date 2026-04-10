<template>
  <section class="applications-page">
    <header class="page-header">
      <h2>Applications</h2>
      <button class="ghost" type="button" :disabled="loading" @click="loadApplications()">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search by student name, roll, or drive title" />
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

    <section v-if="summary" class="summary-card">
      <h4>Status Distribution</h4>
      <ul>
        <li v-for="(count, key) in summary.status_distribution" :key="key">
          <span>{{ key }}</span>
          <strong>{{ count }}</strong>
        </li>
      </ul>
    </section>

    <div v-if="loading" class="box">Loading applications...</div>
    <p v-else-if="items.length === 0">No applications found.</p>

    <ul v-else class="list">
      <li
        v-for="item in items"
        :key="item.application.id"
        class="card"
        :class="applicationCardClass(item.application.status)"
      >
        <div>
          <h4>Application #{{ item.application.id }}</h4>
          <p>
            {{ item.student?.name || 'Student' }}
            <span v-if="item.student?.roll">({{ item.student.roll }})</span>
            applied to {{ item.drive?.title || 'Unknown drive' }}
          </p>
          <small class="meta-line">
            <span class="status-pill" :class="applicationPillClass(item.application.status)">
              {{ item.application.status }}
            </span>
            <span>{{ formatDate(item.application.application_date) }}</span>
          </small>
          <small class="meta-line" v-if="item.application.resume_link">
            Resume: {{ item.application.resume_link }}
          </small>
          <small class="meta-line" v-if="item.application.resume_note">
            Note: {{ item.application.resume_note }}
          </small>
        </div>
        <button class="primary" type="button" @click="openDetail(item.application.id)">View Detail</button>
      </li>
    </ul>

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
import { getCompanyApplications } from '@/api/company'

const router = useRouter()
const loading = ref(false)
const items = ref([])
const summary = ref(null)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 10

const filters = reactive({
  search: '',
  status: '',
})

const loadApplications = async (page = currentPage.value) => {
  loading.value = true
  try {
    const params = {
      page,
      limit: pageSize,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.status ? { status: filters.status } : {}),
    }
    const res = await getCompanyApplications(params)
    items.value = res.data.items || []
    summary.value = res.data.summary || null

    const meta = res.data.pagination || {}
    currentPage.value = meta.page || page
    totalPages.value = meta.total_pages || 1
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
  await loadApplications(1)
}

const goToPage = (page) => {
  const nextPage = Math.min(Math.max(1, page), totalPages.value)
  loadApplications(nextPage)
}

const openDetail = (applicationId) => {
  router.push({ name: 'company-application-detail', params: { applicationId } })
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

const normalize = (value) => String(value || '').toLowerCase().trim()

const applicationCardClass = (status) => {
  const s = normalize(status)
  if (s === 'selected') return 'application-selected'
  if (s === 'shortlisted') return 'application-shortlisted'
  if (s === 'rejected') return 'application-rejected'
  if (s === 'applied') return 'application-applied'
  return ''
}

const applicationPillClass = (status) => {
  const s = normalize(status)
  if (s === 'selected') return 'pill-selected'
  if (s === 'shortlisted') return 'pill-shortlisted'
  if (s === 'rejected') return 'pill-rejected'
  if (s === 'applied') return 'pill-applied'
  return 'pill-neutral'
}

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

.filters {
  display: grid;
  grid-template-columns: 1.5fr 180px auto auto;
  gap: 8px;
}

.filters input,
.filters select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 9px 10px;
  font: inherit;
}

.summary-card,
.box,
.card {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
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

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.card.application-selected {
  background: #f2fbf6;
  border-color: #cdebd8;
}

.card.application-shortlisted {
  background: #f3f8ff;
  border-color: #d7e5ff;
}

.card.application-applied {
  background: #fffdf5;
  border-color: #eee1bf;
}

.card.application-rejected {
  background: #f3f4f6;
  border-color: #dadde3;
}

.meta-line {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
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

.pill-applied {
  color: #9a5d00;
  background: #fff0d8;
}

.pill-rejected {
  color: #5a6373;
  background: #e9ecf1;
}

.pill-neutral {
  color: #44516a;
  background: #eaf0fa;
}

.primary,
.ghost,
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
    grid-template-columns: 1fr;
  }

  .card {
    flex-direction: column;
  }
}
</style>
