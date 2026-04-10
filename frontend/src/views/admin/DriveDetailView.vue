<template>
  <section class="drive-detail-page">
    <AdminPageHeader
      title="Drive Detail"
      subtitle="Detailed information about the selected drive."
      :show-refresh="true"
      :show-back="true"
      :refreshing="loading || applicationsLoading"
      :refresh-disabled="loading || applicationsLoading || Boolean(actionBusy)"
      @refresh="refreshPage"
      @back="goBack"
    />

    <div v-if="loading" class="box">Loading drive details...</div>
    <div v-else-if="!drive" class="box error-box">Drive not found.</div>

    <template v-else>
      <section class="action-card">
        <h3>Admin Actions</h3>
        <div class="action-row">
          <button
            v-if="isDrivePending"
            class="primary"
            type="button"
            :disabled="Boolean(actionBusy)"
            @click="runAction('approve')"
          >
            Approve
          </button>
          <button
            v-if="isDrivePending"
            class="danger"
            type="button"
            :disabled="Boolean(actionBusy)"
            @click="runAction('reject')"
          >
            Reject
          </button>
          <button
            v-if="isDriveApproved && drive.is_active"
            class="danger ghost-danger"
            type="button"
            :disabled="Boolean(actionBusy)"
            @click="runAction('block')"
          >
            Block
          </button>
          <button
            v-if="isDriveApproved && !drive.is_active"
            class="ghost"
            type="button"
            :disabled="Boolean(actionBusy)"
            @click="runAction('unblock')"
          >
            Unblock
          </button>
          <button
            v-if="isDriveRejected"
            class="primary"
            type="button"
            :disabled="Boolean(actionBusy)"
            @click="runAction('approve')"
          >
            Approve
          </button>
        </div>
      </section>

      <section class="card-grid">
        <article class="detail-card">
          <h3>Drive Snapshot</h3>
          <ul>
            <li><span>Drive ID</span><strong>#{{ drive.id }}</strong></li>
            <li><span>Title</span><strong>{{ drive.title || '-' }}</strong></li>
            <li><span>Status</span><strong>{{ drive.status || '-' }}</strong></li>
            <li><span>Approval</span><strong>{{ drive.approval_status || '-' }}</strong></li>
            <li><span>Work Mode</span><strong>{{ drive.work_mode || '-' }}</strong></li>
            <li><span>Min CGPA</span><strong>{{ drive.min_cgpa ?? '-' }}</strong></li>
            <li><span>Allowed Branches</span><strong>{{ allowedBranchesText }}</strong></li>
            <li><span>Max Applications</span><strong>{{ drive.max_applications ?? '-' }}</strong></li>
            <li><span>Applications Received</span><strong>{{ drive.applications_count ?? 0 }}</strong></li>
            <li><span>Active</span><strong>{{ drive.is_active ? 'Yes' : 'No' }}</strong></li>
          </ul>
        </article>

        <article class="detail-card">
          <h3>Schedule</h3>
          <ul>
            <li><span>Created On</span><strong>{{ formatDate(drive.create_date) }}</strong></li>
            <li><span>Start Date</span><strong>{{ formatDate(drive.start_date) }}</strong></li>
            <li><span>End Date</span><strong>{{ formatDate(drive.end_date) }}</strong></li>
          </ul>
        </article>

        <article class="detail-card">
          <h3>Company</h3>
          <ul>
            <li><span>Company ID</span><strong>{{ drive.company?.id ?? '-' }}</strong></li>
            <li><span>Name</span><strong>{{ drive.company?.name || '-' }}</strong></li>
            <li><span>Email</span><strong>{{ drive.company?.email || '-' }}</strong></li>
            <li><span>Website</span><strong>{{ drive.company?.website || '-' }}</strong></li>
            <li><span>Industry</span><strong>{{ drive.company?.industry_type || '-' }}</strong></li>
          </ul>
        </article>
      </section>

      <section class="description-card">
        <h3>Description</h3>
        <p>{{ drive.description || 'No description provided.' }}</p>
      </section>

      <section class="applications-panel">
        <header class="applications-header">
          <h3>Applications for this Drive</h3>
          <form class="applications-filters" @submit.prevent="applyApplicationFilters">
            <input
              v-model="applicationFilters.search"
              type="search"
              placeholder="Search student, company, email, or roll"
            />
            <select v-model="applicationFilters.status">
              <option value="">All status</option>
              <option value="applied">Applied</option>
              <option value="short_listed">Shortlisted</option>
              <option value="selected">Selected</option>
              <option value="rejected">Rejected</option>
            </select>
            <button class="ghost" type="submit">Apply</button>
            <button class="text-btn" type="button" @click="resetApplicationFilters">Reset</button>
          </form>
        </header>

        <div v-if="applicationsLoading" class="box">Loading applications...</div>
        <p v-else-if="applications.length === 0" class="state-text">No applications found for this drive.</p>

        <div v-else class="table-wrap">
          <table>
            <colgroup>
              <col class="col-app-id" />
              <col class="col-student" />
              <col class="col-company" />
              <col class="col-status" />
              <col class="col-applied-on" />
              <col class="col-action" />
            </colgroup>
            <thead>
              <tr>
                <th>
                  <button class="sort-btn" type="button" @click="toggleApplicationSort('id')">
                    <u>Application ID</u> {{ applicationSortMark('id') }}
                  </button>
                </th>
                <th>
                  <button class="sort-btn" type="button" @click="toggleApplicationSort('student_name')">
                    Student {{ applicationSortMark('student_name') }}
                  </button>
                </th>
                <th>
                  <button class="sort-btn" type="button" @click="toggleApplicationSort('company_name')">
                    Company {{ applicationSortMark('company_name') }}
                  </button>
                </th>
                <th>
                  <button class="sort-btn" type="button" @click="toggleApplicationSort('status')">
                    Status {{ applicationSortMark('status') }}
                  </button>
                </th>
                <th>
                  <button class="sort-btn" type="button" @click="toggleApplicationSort('application_date')">
                    Applied On {{ applicationSortMark('application_date') }}
                  </button>
                </th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in applications"
                :key="`drive-application-${item.application.id}`"
                :class="applicationRowClass(item.application.status)"
              >
                <td><strong>#{{ item.application.id }}</strong></td>
                <td>
                  <strong>{{ item.student?.name || '-' }}</strong>
                  <p class="sub-line">{{ item.student?.roll || '-' }}</p>
                </td>
                <td>{{ item.company?.name || '-' }}</td>
                <td>
                  <span class="status-pill" :class="applicationPillClass(item.application.status)">
                    {{ formatStatusLabel(item.application.status) }}
                  </span>
                </td>
                <td>{{ formatDate(item.application.application_date) }}</td>
                <td>
                  <button class="ghost" type="button" @click="openApplication(item.application.id)">View Details</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <AdminPagination
          :page="applicationPagination.page"
          :total-pages="applicationPagination.total_pages"
          :disabled="applicationsLoading"
          :show-jump="true"
          input-id="drive-applications-page-jump"
          @go="goToApplicationsPage"
        />
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { approveDrive, blockDrive, getAdminApplications, getAdminDriveDetail, rejectDrive, unblockDrive } from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminPagination from '@/components/admin/AdminPagination.vue'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const drive = ref(null)
const actionBusy = ref('')
const driveId = computed(() => Number(route.params.driveId))

const applicationsLoading = ref(false)
const applications = ref([])
const applicationPageSize = 10
const applicationFilters = reactive({
  search: '',
  status: '',
  sort_by: 'application_date',
  sort_order: 'desc',
})
const applicationPagination = reactive({
  page: 1,
  limit: applicationPageSize,
  total: 0,
  total_pages: 1,
})

const normalize = (value) => String(value || '').trim().toLowerCase()
const isDriveApproved = computed(() => normalize(drive.value?.approval_status) === 'approved')
const isDrivePending = computed(() => normalize(drive.value?.approval_status) === 'pending')
const isDriveRejected = computed(() => normalize(drive.value?.approval_status) === 'rejected')

const allowedBranchesText = computed(() => {
  const branches = drive.value?.allowed_branches
  if (!Array.isArray(branches) || branches.length === 0) {
    return 'All branches'
  }
  return branches.join(', ')
})

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

const loadDetail = async () => {
  if (!Number.isFinite(driveId.value) || driveId.value <= 0) {
    toast.error('Invalid drive id')
    return
  }

  loading.value = true
  try {
    const res = await getAdminDriveDetail(driveId.value)
    drive.value = res?.data?.drive || null
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load drive detail')
    drive.value = null
  } finally {
    loading.value = false
  }
}

const loadDriveApplications = async (page = applicationPagination.page) => {
  if (!Number.isFinite(driveId.value) || driveId.value <= 0) {
    applications.value = []
    return
  }

  applicationsLoading.value = true
  try {
    const params = {
      drive_id: driveId.value,
      page,
      limit: applicationPageSize,
      sort_by: applicationFilters.sort_by,
      sort_order: applicationFilters.sort_order,
      ...(applicationFilters.search ? { search: applicationFilters.search } : {}),
      ...(applicationFilters.status ? { status: applicationFilters.status } : {}),
    }
    const res = await getAdminApplications(params)
    applications.value = res?.data?.applications || []

    const meta = res?.data?.pagination || {}
    applicationPagination.page = meta.page || page
    applicationPagination.limit = meta.limit || applicationPageSize
    applicationPagination.total = meta.total || applications.value.length
    applicationPagination.total_pages = meta.total_pages || 1
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load drive applications')
    applications.value = []
  } finally {
    applicationsLoading.value = false
  }
}

const runAction = async (action) => {
  if (!drive.value?.id) return

  actionBusy.value = action
  try {
    if (action === 'approve') {
      await approveDrive(drive.value.id)
      toast.success('Drive approved')
    } else if (action === 'reject') {
      await rejectDrive(drive.value.id)
      toast.success('Drive rejected')
    } else if (action === 'block') {
      await blockDrive(drive.value.id)
      toast.success('Drive blocked')
    } else if (action === 'unblock') {
      await unblockDrive(drive.value.id)
      toast.success('Drive unblocked')
    }
    await loadDetail()
  } catch (error) {
    toast.error(error?.response?.data?.error || `Failed to ${action} drive`)
  } finally {
    actionBusy.value = ''
  }
}

const goBack = () => {
  navigateBack(router, { name: 'admin-drives' }, route.fullPath)
}

const refreshPage = async () => {
  await Promise.all([loadDetail(), loadDriveApplications(applicationPagination.page)])
}

const toggleApplicationSort = async (key) => {
  if (applicationFilters.sort_by === key) {
    applicationFilters.sort_order = applicationFilters.sort_order === 'asc' ? 'desc' : 'asc'
  } else {
    applicationFilters.sort_by = key
    applicationFilters.sort_order = 'asc'
  }
  await loadDriveApplications(1)
}

const applicationSortMark = (key) => {
  if (applicationFilters.sort_by !== key) return ''
  return applicationFilters.sort_order === 'asc' ? '^' : 'v'
}

const applyApplicationFilters = async () => {
  await loadDriveApplications(1)
}

const resetApplicationFilters = async () => {
  applicationFilters.search = ''
  applicationFilters.status = ''
  applicationFilters.sort_by = 'application_date'
  applicationFilters.sort_order = 'desc'
  await loadDriveApplications(1)
}

const goToApplicationsPage = async (page) => {
  const nextPage = Math.min(Math.max(1, page), applicationPagination.total_pages)
  await loadDriveApplications(nextPage)
}

const formatStatusLabel = (value) => {
  const clean = String(value || '').trim()
  if (!clean) return '-'
  return clean.replace(/_/g, ' ')
}

const applicationRowClass = (status) => {
  const normalized = normalize(status).replace(/[_\s]/g, '')
  if (normalized === 'selected') return 'app-selected'
  if (normalized === 'shortlisted') return 'app-shortlisted'
  if (normalized === 'rejected') return 'app-rejected'
  if (normalized === 'applied') return 'app-applied'
  return ''
}

const applicationPillClass = (status) => {
  const normalized = normalize(status).replace(/[_\s]/g, '')
  if (normalized === 'selected') return 'pill-selected'
  if (normalized === 'shortlisted') return 'pill-shortlisted'
  if (normalized === 'rejected') return 'pill-inactive'
  if (normalized === 'applied') return 'pill-pending'
  return 'pill-neutral'
}

const openApplication = (applicationId) => {
  router.push({ name: 'admin-application-detail', params: { applicationId } })
}

onMounted(async () => {
  await Promise.all([loadDetail(), loadDriveApplications(1)])
})
</script>

<style scoped>
.drive-detail-page {
  display: grid;
  gap: 14px;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.detail-card,
.description-card,
.action-card,
.box {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.detail-card h3,
.description-card h3,
.action-card h3 {
  margin: 0 0 10px;
  color: #1f2f52;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.detail-card li {
  display: grid;
  grid-template-columns: 130px minmax(0, 1fr);
  align-items: start;
  gap: 10px;
}

.detail-card li span {
  color: #5c6d92;
}

.detail-card li strong {
  color: #203259;
  text-align: left;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.description-card p {
  margin: 0;
  color: #334155;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.applications-panel {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
  display: grid;
  gap: 10px;
}

.applications-header {
  display: grid;
  gap: 10px;
}

.applications-header h3 {
  margin: 0;
  color: #1f2f52;
}

.applications-filters {
  display: grid;
  grid-template-columns: 1.6fr minmax(160px, 1fr) auto auto;
  gap: 8px;
}

.applications-filters input,
.applications-filters select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 9px 10px;
  font: inherit;
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
  min-width: 860px;
}

.col-app-id {
  width: 13%;
}

.col-student {
  width: 24%;
}

.col-company {
  width: 18%;
}

.col-status {
  width: 15%;
}

.col-applied-on {
  width: 20%;
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

.state-text {
  margin: 0;
  color: #536a95;
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

.error-box {
  color: #8f2e2e;
  background: #fff3f3;
}

.primary,
.danger,
.ghost {
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}

.primary {
  border: none;
  background: #2f66db;
  color: #fff;
}

.danger {
  border: none;
  background: #c94747;
  color: #fff;
}

.danger.ghost-danger {
  background: #fff;
  border: 1px solid #d9b9b9;
  color: #a34545;
}

.ghost {
  border: 1px solid #cfd9ee;
  background: #fff;
  color: #2f4b80;
}

.text-btn {
  border: none;
  background: transparent;
  color: #5b6783;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 980px) {
  .card-grid {
    grid-template-columns: 1fr;
  }

  .detail-card li {
    grid-template-columns: 110px minmax(0, 1fr);
  }

  .applications-filters {
    grid-template-columns: 1fr;
  }

  table {
    min-width: 760px;
  }
}
</style>
