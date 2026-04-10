<template>
  <section class="admin-table-page">
    <AdminPageHeader
      title="Companies"
      :show-refresh="true"
      :refreshing="loading"
      :refresh-disabled="loading"
      @refresh="loadCompanies"
    />

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search by name, email, website" />
      <select v-model="filters.approved">
        <option value="">All approvals</option>
        <option value="true">Approved</option>
        <option value="false">Pending/Rejected</option>
      </select>
      <select v-model="filters.active">
        <option value="">All activity</option>
        <option value="true">Active</option>
        <option value="false">Blocked</option>
      </select>
      <button class="ghost" type="submit">Apply</button>
      <button class="text-btn" type="button" @click="resetFilters">Reset</button>
    </form>

    <p v-if="loading" class="state-text">Loading companies...</p>
    <p v-else-if="companies.length === 0" class="state-text">No companies found.</p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('name')">
                <u>Company</u> {{ sortMark('name') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('industry_type')">
                <u>Industry</u> {{ sortMark('industry_type') }}
              </button>
            </th>
            <th>Website</th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('is_approved')">
                <u>Approval</u> {{ sortMark('is_approved') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" type="button" @click="toggleSort('is_active')">
                <u>Account</u> {{ sortMark('is_active') }}
              </button>
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="company in companies" :key="company.id">
            <td>
                <div class="company-link-stack">
                  <button class="link-btn" type="button" @click="openCompanyDetail(company.id)">
                    <strong>{{ company.name }}</strong>
                  </button>
                  <button class="link-id-btn" type="button" @click="openCompanyDetail(company.id)">
                    #{{ company.id }}
                  </button>
                </div>
              <p class="sub-line">{{ company.email }}</p>
            </td>
            <td>{{ company.industry_type || '-' }}</td>
            <td>
              <a :href="company.website" target="_blank" rel="noopener noreferrer">{{ company.website }}</a>
            </td>
            <td>
              <span class="status-pill" :class="approvalPillClass(company)">
                {{ approvalLabel(company) }}
              </span>
            </td>
            <td>
              <span class="status-pill" :class="company.is_active ? 'pill-active' : 'pill-blocked'">
                {{ company.is_active ? 'Active' : 'Blocked' }}
              </span>
            </td>
            <td class="actions-cell">
              <button
                v-if="isCompanyPending(company)"
                class="primary"
                type="button"
                :disabled="actionBusyId === company.id"
                @click="updateCompany(company.id, 'approve')"
              >
                Approve
              </button>
              <button
                v-if="isCompanyPending(company)"
                class="danger"
                type="button"
                :disabled="actionBusyId === company.id"
                @click="updateCompany(company.id, 'reject')"
              >
                Reject
              </button>
              <button
                v-if="isCompanyApproved(company) && company.is_active"
                class="danger ghost-danger"
                type="button"
                :disabled="actionBusyId === company.id"
                @click="updateCompany(company.id, 'block')"
              >
                Block
              </button>
              <button
                v-if="isCompanyApproved(company) && !company.is_active"
                class="ghost"
                type="button"
                :disabled="actionBusyId === company.id"
                @click="updateCompany(company.id, 'unblock')"
              >
                Unblock
              </button>
              <button
                v-if="isCompanyRejected(company)"
                class="primary"
                type="button"
                :disabled="actionBusyId === company.id"
                @click="updateCompany(company.id, 'approve')"
              >
                Approve
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination :page="page" :total-pages="totalPages" :disabled="loading" @go="goToPage" />
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import {
  approveCompany,
  blockCompany,
  getAdminCompanies,
  rejectCompany,
  unblockCompany,
} from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminPagination from '@/components/admin/AdminPagination.vue'

const router = useRouter()
const loading = ref(false)
const actionBusyId = ref(null)
const companies = ref([])
const filters = reactive({ search: '', approved: '', active: '' })
const page = ref(1)
const limit = ref(10)
const totalPages = ref(1)
const sort = ref({ key: 'is_approved', direction: 'desc' })

const isCompanyApproved = (company) => Boolean(company?.is_approved)
const isCompanyPending = (company) => !company?.is_approved && Boolean(company?.is_active)
const isCompanyRejected = (company) => !company?.is_approved && !company?.is_active

const approvalLabel = (company) => {
  if (isCompanyApproved(company)) return 'Approved'
  if (isCompanyRejected(company)) return 'Rejected'
  return 'Pending'
}

const approvalPillClass = (company) => {
  if (isCompanyApproved(company)) return 'pill-approved'
  if (isCompanyRejected(company)) return 'pill-blocked'
  return 'pill-pending'
}

const openCompanyDetail = (companyId) => {
  router.push({ name: 'admin-company-detail', params: { companyId } })
}

const toggleSort = (key) => {
  if (sort.value.key === key) {
    sort.value.direction = sort.value.direction === 'asc' ? 'desc' : 'asc'
  } else {
    sort.value = { key, direction: 'asc' }
  }
  loadCompanies(1)
}

const sortMark = (key) => {
  if (sort.value.key !== key) return ''
  return sort.value.direction === 'asc' ? '^' : 'v'
}

const loadCompanies = async (nextPage = page.value) => {
  loading.value = true
  try {
    const params = {
      page: nextPage,
      limit: limit.value,
      sort_by: sort.value.key,
      sort_order: sort.value.direction,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.approved ? { approved: filters.approved } : {}),
      ...(filters.active ? { active: filters.active } : {}),
    }
    const res = await getAdminCompanies(params)
    companies.value = res?.data?.companies || []
    page.value = res?.data?.pagination?.page || nextPage
    totalPages.value = res?.data?.pagination?.total_pages || 1
  } catch (err) {
    toast.error(err?.response?.data?.error || 'Failed to load companies')
  } finally {
    loading.value = false
  }
}

const updateCompany = async (companyId, action) => {
  actionBusyId.value = companyId
  try {
    if (action === 'approve') {
      await approveCompany(companyId)
      toast.success('Company approved')
    } else if (action === 'reject') {
      await rejectCompany(companyId)
      toast.success('Company rejected')
    } else if (action === 'block') {
      await blockCompany(companyId)
      toast.success('Company blocked')
    } else {
      await unblockCompany(companyId)
      toast.success('Company unblocked')
    }
    await loadCompanies()
  } catch (err) {
    toast.error(err?.response?.data?.error || `Unable to ${action} company`)
  } finally {
    actionBusyId.value = null
  }
}

const applyFilters = async () => {
  await loadCompanies(1)
}

const resetFilters = async () => {
  filters.search = ''
  filters.approved = ''
  filters.active = ''
  await loadCompanies(1)
}

const goToPage = async (nextPage) => {
  const safe = Math.min(Math.max(1, nextPage), totalPages.value)
  await loadCompanies(safe)
}

onMounted(loadCompanies)
</script>

<style scoped>
.admin-table-page {
  display: grid;
  gap: 12px;
}

.filters {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 180px 160px auto auto;
  gap: 8px;
}

.filters input,
.filters select {
  border: 1px solid #d6ddec;
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
  min-width: 900px;
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

.sort-btn {
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

a {
  color: #2f66db;
}

.sub-line {
  margin: 3px 0 0;
  color: #5f7197;
  font-size: 0.82rem;
}

.link-btn {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  color: #0d0d0f;
  cursor: pointer;
  text-decoration: underline;
  font: inherit;
}

  .company-link-stack {
    display: inline-flex;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
  }

  .link-id-btn {
    border: none;
    background: transparent;
    padding: 0;
    margin: 0;
    color: #0e0e0e;
    cursor: pointer;
    text-decoration: underline;
    font: inherit;
    font-size: 0.86rem;
  }

.actions-cell {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.78rem;
  font-weight: 700;
}

.pill-approved {
  background: #e8f8ef;
  color: #1f7a4f;
}

.pill-pending {
  background: #fff4dd;
  color: #8f6518;
}

.pill-active {
  background: #eaf1ff;
  color: #335cb7;
}

.pill-blocked {
  background: #fde9e9;
  color: #8f2e2e;
}

.state-text {
  margin: 0;
  color: #536a95;
}

.primary,
.danger,
.ghost,
.text-btn {
  height: 36px;
  border-radius: 8px;
  padding: 0 12px;
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
  color: #3a5da6;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 860px) {
  .filters {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

