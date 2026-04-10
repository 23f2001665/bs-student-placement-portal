<template>
  <section class="drives-page">
    <AdminPageHeader
      title="Drives"
      subtitle="Review, moderate, and track company drives from one place."
      :show-refresh="true"
      :refreshing="loading"
      :refresh-disabled="loading"
      @refresh="loadDrives"
    />

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search title, description, or company" />
      <select v-model="filters.approval_status">
        <option value="">All approvals</option>
        <option value="approved">Approved</option>
        <option value="pending">Pending</option>
        <option value="rejected">Rejected</option>
      </select>
      <select v-model="filters.status">
        <option value="">All status</option>
        <option value="upcoming">Upcoming</option>
        <option value="active">Active</option>
        <option value="closed">Closed</option>
        <option value="cancelled">Cancelled</option>
        <option value="pending">Pending</option>
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
            <span>Pending approvals on page</span>
            <strong>{{ pendingApprovalsOnPage }}</strong>
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

    <DriveListPanel
      :loading="loading"
      :drives="filteredDrives"
      :pagination="pagination"
      :sort-by="filters.sort_by"
      :sort-order="filters.sort_order"
      :action-busy-id="actionBusyId"
      :show-moderation="true"
      :show-company="true"
      :show-jump="true"
      empty-text="No drives found."
      @toggle-sort="toggleSort"
      @open-drive="openDrive"
      @drive-action="handleDriveAction"
      @go-page="goToPage"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { approveDrive, blockDrive, getAdminDrives, rejectDrive, unblockDrive } from '@/api/admin'
import DriveListPanel from '@/components/admin/DriveListPanel.vue'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'

const router = useRouter()
const loading = ref(false)
const actionBusyId = ref(null)
const drives = ref([])
const pageSize = 10

const filters = reactive({
  search: '',
  approval_status: '',
  status: '',
  work_mode: '',
  sort_by: 'start_date',
  sort_order: 'desc',
})

const pagination = reactive({
  page: 1,
  limit: pageSize,
  total: 0,
  total_pages: 1,
})

const filteredDrives = computed(() => drives.value)

const normalize = (value) => String(value || '').trim().toLowerCase()

const getErrorMessage = (error, fallback) => {
  const payload = error?.response?.data || {}
  return payload.error || payload.details || fallback
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

const loadDrives = async (nextPage = pagination.page) => {
  loading.value = true
  try {
    const params = {
      page: nextPage,
      limit: pageSize,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.approval_status ? { approval_status: filters.approval_status } : {}),
      ...(filters.status ? { status: filters.status } : {}),
      ...(filters.work_mode ? { work_mode: filters.work_mode } : {}),
    }
    const res = await getAdminDrives(params)
    drives.value = res?.data?.drives || []

    const meta = res?.data?.pagination || {}
    pagination.page = meta.page || nextPage
    pagination.limit = meta.limit || pageSize
    pagination.total = meta.total || drives.value.length
    pagination.total_pages = meta.total_pages || 1
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to load drives'))
  } finally {
    loading.value = false
  }
}

const updateDrive = async (driveId, action) => {
  actionBusyId.value = driveId
  try {
    if (action === 'approve') {
      await approveDrive(driveId)
      toast.success('Drive approved')
    } else if (action === 'reject') {
      await rejectDrive(driveId)
      toast.success('Drive rejected')
    } else if (action === 'block') {
      await blockDrive(driveId)
      toast.success('Drive blocked')
    } else {
      await unblockDrive(driveId)
      toast.success('Drive unblocked')
    }
    await loadDrives()
  } catch (error) {
    toast.error(getErrorMessage(error, `Unable to ${action} drive`))
  } finally {
    actionBusyId.value = null
  }
}

const applyFilters = async () => {
  await loadDrives(1)
}

const resetFilters = async () => {
  filters.search = ''
  filters.approval_status = ''
  filters.status = ''
  filters.work_mode = ''
  filters.sort_by = 'start_date'
  filters.sort_order = 'desc'
  await loadDrives(1)
}

const goToPage = async (nextPage) => {
  const safePage = Math.min(Math.max(1, nextPage), pagination.total_pages)
  await loadDrives(safePage)
}

const openDrive = (driveId) => {
  router.push({ name: 'admin-drive-detail', params: { driveId } })
}

const handleDriveAction = async ({ driveId, action }) => {
  await updateDrive(driveId, action)
}

const pageStatusCounts = computed(() => {
  const counts = {
    active: 0,
    upcoming: 0,
    closed: 0,
    pending: 0,
    cancelled: 0,
  }
  for (const drive of filteredDrives.value) {
    const status = normalize(drive?.status)
    if (Object.prototype.hasOwnProperty.call(counts, status)) {
      counts[status] += 1
    }
  }
  return counts
})

const pendingApprovalsOnPage = computed(() => {
  let count = 0
  for (const drive of filteredDrives.value) {
    if (normalize(drive?.approval_status) === 'pending') {
      count += 1
    }
  }
  return count
})

onMounted(async () => {
  await loadDrives()
})
</script>

<style scoped>
.drives-page {
  display: grid;
  gap: 14px;
}

.filters {
  display: grid;
  grid-template-columns: 1.3fr repeat(3, minmax(110px, 1fr)) auto auto;
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

.summary-card {
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

.ghost,
.text-btn {
  border-radius: 8px;
  padding: 8px 10px;
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
  border: none;
  background: transparent;
  color: #5b6783;
}

.state-text {
  margin: 0;
  color: #536a95;
}

button:disabled {
  opacity: 0.6;
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
}

@media (max-width: 760px) {
  .filters {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>

