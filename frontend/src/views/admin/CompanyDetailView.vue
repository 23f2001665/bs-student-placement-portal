<template>
  <section class="company-detail-page">
    <AdminPageHeader
      :title="company?.name || `Company #${companyId}`"
      :show-refresh="true"
      :show-back="true"
      :refreshing="loadingCompany || loadingDrives"
      :refresh-disabled="loadingCompany || loadingDrives"
      @refresh="refreshAll"
      @back="goBack"
    />

    <p v-if="loadingCompany" class="card">Loading company context...</p>
    <p v-else-if="!company" class="card">Company not found.</p>

    <article v-else class="card company-card">
      <div class="card-header">
        <h3>Company Details</h3>
        <div class="actions-group">
          <button
            v-if="isCompanyPending(company)"
            class="primary"
            type="button"
            :disabled="actionBusy"
            @click="updateCompany('approve')"
          >
            Approve
          </button>
          <button
            v-if="isCompanyPending(company)"
            class="danger"
            type="button"
            :disabled="actionBusy"
            @click="updateCompany('reject')"
          >
            Reject
          </button>
          <button
            v-if="isCompanyApproved(company) && company.is_active"
            class="danger ghost-danger"
            type="button"
            :disabled="actionBusy"
            @click="updateCompany('block')"
          >
            Block
          </button>
          <button
            v-if="isCompanyApproved(company) && !company.is_active"
            class="ghost"
            type="button"
            :disabled="actionBusy"
            @click="updateCompany('unblock')"
          >
            Unblock
          </button>
          <button
            v-if="isCompanyRejected(company)"
            class="primary"
            type="button"
            :disabled="actionBusy"
            @click="updateCompany('approve')"
          >
            Approve
          </button>
        </div>
      </div>
      <ul>
        <li><span>ID</span><strong>{{ company.id }}</strong></li>
        <li><span>Name</span><strong>{{ company.name || '-' }}</strong></li>
        <li><span>Email</span><strong class="wrap">{{ company.email || '-' }}</strong></li>
        <li><span>Website</span><strong class="wrap">{{ company.website || '-' }}</strong></li>
        <li><span>Industry</span><strong>{{ company.industry_type || '-' }}</strong></li>
        <li><span>Approved</span><strong>{{ company.is_approved ? 'Yes' : 'No' }}</strong></li>
        <li><span>Active</span><strong>{{ company.is_active ? 'Yes' : 'No' }}</strong></li>
      </ul>
    </article>

    <section v-if="company" class="drives-panel">
      <header class="drives-header">
        <h3>Drives</h3>
        <form class="drives-filters" @submit.prevent="applyDriveFilters">
          <input v-model="driveFilters.search" type="search" placeholder="Search drive title or description" />
          <select v-model="driveFilters.approval_status">
            <option value="">All approvals</option>
            <option value="approved">Approved</option>
            <option value="pending">Pending</option>
            <option value="rejected">Rejected</option>
          </select>
          <select v-model="driveFilters.status">
            <option value="">All status</option>
            <option value="active">Active</option>
            <option value="upcoming">Upcoming</option>
            <option value="closed">Closed</option>
            <option value="cancelled">Cancelled</option>
            <option value="pending">Pending</option>
          </select>
          <button class="ghost" type="submit">Apply</button>
          <button class="text-btn" type="button" @click="resetDriveFilters">Reset</button>
        </form>
      </header>

      <DriveListPanel
        :loading="loadingDrives"
        :drives="drives"
        :pagination="pagination"
        sort-by="start_date"
        sort-order="desc"
        :show-moderation="false"
        :show-company="false"
        :show-jump="false"
        empty-text="No drives found for this company."
        @open-drive="openDrive"
        @go-page="goToPage"
      />
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import {
  approveCompany,
  blockCompany,
  getAdminCompanies,
  getAdminDrives,
  rejectCompany,
  unblockCompany,
} from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import DriveListPanel from '@/components/admin/DriveListPanel.vue'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const companyId = computed(() => Number(route.params.companyId))
const company = ref(null)
const loadingCompany = ref(false)
const actionBusy = ref(false)

const loadingDrives = ref(false)
const drives = ref([])
const pageSize = 10
const pagination = reactive({
  page: 1,
  limit: pageSize,
  total: 0,
  total_pages: 1,
})

const driveFilters = reactive({
  search: '',
  status: '',
  approval_status: '',
})

const isCompanyApproved = (c) => Boolean(c?.is_approved)
const isCompanyPending = (c) => !c?.is_approved && Boolean(c?.is_active)
const isCompanyRejected = (c) => !c?.is_approved && !c?.is_active

const loadCompany = async () => {
  if (!Number.isFinite(companyId.value) || companyId.value <= 0) {
    toast.error('Invalid company id')
    return
  }

  loadingCompany.value = true
  try {
    const res = await getAdminCompanies({ company_id: companyId.value, page: 1, limit: 1 })
    const item = res?.data?.companies?.[0] || null
    company.value = item
    if (!item) {
      toast.error('Company not found')
    }
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load company detail')
    company.value = null
  } finally {
    loadingCompany.value = false
  }
}

const loadDrives = async (page = pagination.page) => {
  if (!Number.isFinite(companyId.value) || companyId.value <= 0) {
    return
  }

  loadingDrives.value = true
  try {
    const params = {
      company_id: companyId.value,
      page,
      limit: pageSize,
      sort_by: 'start_date',
      sort_order: 'desc',
      ...(driveFilters.search ? { search: driveFilters.search } : {}),
      ...(driveFilters.status ? { status: driveFilters.status } : {}),
      ...(driveFilters.approval_status ? { approval_status: driveFilters.approval_status } : {}),
    }
    const res = await getAdminDrives(params)
    drives.value = res?.data?.drives || []

    const meta = res?.data?.pagination || {}
    pagination.page = meta.page || page
    pagination.limit = meta.limit || pageSize
    pagination.total = meta.total || drives.value.length
    pagination.total_pages = meta.total_pages || 1
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load company drives')
    drives.value = []
  } finally {
    loadingDrives.value = false
  }
}

const applyDriveFilters = async () => {
  await loadDrives(1)
}

const resetDriveFilters = async () => {
  driveFilters.search = ''
  driveFilters.status = ''
  driveFilters.approval_status = ''
  await loadDrives(1)
}

const goToPage = async (page) => {
  const nextPage = Math.min(Math.max(1, page), pagination.total_pages)
  await loadDrives(nextPage)
}

const updateCompany = async (action) => {
  if (!company.value?.id) return
  actionBusy.value = true
  try {
    if (action === 'approve') {
      await approveCompany(company.value.id)
      toast.success('Company approved')
    } else if (action === 'reject') {
      await rejectCompany(company.value.id)
      toast.success('Company rejected')
    } else if (action === 'block') {
      await blockCompany(company.value.id)
      toast.success('Company blocked')
    } else if (action === 'unblock') {
      await unblockCompany(company.value.id)
      toast.success('Company unblocked')
    }
    await loadCompany()
  } catch (err) {
    toast.error(err?.response?.data?.error || `Unable to ${action} company`)
  } finally {
    actionBusy.value = false
  }
}

const refreshAll = async () => {
  await Promise.all([loadCompany(), loadDrives(pagination.page)])
}

const openDrive = (driveId) => {
  router.push({ name: 'admin-drive-detail', params: { driveId } })
}

const goBack = () => {
  navigateBack(router, { name: 'admin-companies' }, route.fullPath)
}

onMounted(async () => {
  await Promise.all([loadCompany(), loadDrives(1)])
})
</script>

<style scoped>
.company-detail-page {
  display: grid;
  gap: 14px;
}

.card,
.drives-panel {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.card-header h3 {
  margin: 0;
  flex: 1;
}

.actions-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.company-card h3 {
  margin: 0;
}

.company-card ul {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.company-card li {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 10px;
  align-items: start;
}

.wrap {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.drives-header h3 {
  margin: 0;
}

.drives-header {
  display: grid;
  gap: 10px;
  margin-bottom: 5px;
}

.drives-filters {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) 170px 170px auto auto;
  gap: 8px;
}

.drives-filters input,
.drives-filters select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 9px 10px;
  font: inherit;
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

.primary {
  height: 34px;
  padding: 0 12px;
  border: none;
  border-radius: 8px;
  background: #2f66db;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.danger {
  height: 34px;
  padding: 0 12px;
  border: none;
  border-radius: 8px;
  background: #e8364f;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.danger:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.ghost-danger {
  background: #fff;
  border: 1px solid #e8364f;
  color: #e8364f;
}

@media (max-width: 900px) {
  .company-card li {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .drives-filters {
    grid-template-columns: 1fr;
  }
}
</style>
