<template>
  <section class="admin-table-page">
    <AdminPageHeader
      title="Students"
      :show-refresh="true"
      :refreshing="loading"
      :refresh-disabled="loading"
      @refresh="loadStudents"
    />

    <form class="filters" @submit.prevent="applyFilters">
      <input v-model="filters.search" type="search" placeholder="Search by name, email, roll" />
      <select v-model="filters.branch">
        <option value="">All branches</option>
        <option v-for="branch in branches" :key="branch.value" :value="branch.value">{{ branch.label }}</option>
      </select>
      <select v-model="filters.current_level">
        <option value="">All years</option>
        <option v-for="year in yearOptions" :key="year" :value="year">Year {{ year }}</option>
      </select>
      <input v-model.number="filters.cgpa_min" type="number" min="0" max="10" step="0.01" placeholder="CGPA min" />
      <input v-model.number="filters.cgpa_max" type="number" min="0" max="10" step="0.01" placeholder="CGPA max" />
      <select v-model="filters.active">
        <option value="">All status</option>
        <option value="true">Active</option>
        <option value="false">Blocked</option>
      </select>
      <button class="ghost" type="submit">Apply</button>
      <button class="text-btn" type="button" @click="resetFilters">Reset</button>
    </form>

    <p v-if="loading" class="state-text">Loading students...</p>
    <p v-else-if="students.length === 0" class="state-text">No students found.</p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th><button class="sort-btn" type="button" @click="toggleSort('name')">Name {{ sortMark('name') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('roll')">Roll {{ sortMark('roll') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('branch')">Branch {{ sortMark('branch') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('current_level')">Year {{ sortMark('current_level') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('cgpa')">CGPA {{ sortMark('cgpa') }}</button></th>
            <th><button class="sort-btn" type="button" @click="toggleSort('is_active')">Status {{ sortMark('is_active') }}</button></th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.id">
            <td>
              <strong>{{ student.name }}</strong>
              <p class="sub-line">{{ student.email }}</p>
            </td>
            <td>{{ student.roll || '-' }}</td>
            <td>{{ student.branch || '-' }}</td>
            <td>{{ student.current_level || '-' }}</td>
            <td>{{ student.cgpa ?? '-' }}</td>
            <td>
              <span class="status-pill" :class="student.is_active ? 'pill-active' : 'pill-blocked'">
                {{ student.is_active ? 'Active' : 'Blocked' }}
              </span>
            </td>
            <td class="actions-cell">
              <button
                v-if="student.is_active"
                class="danger ghost-danger"
                type="button"
                :disabled="actionBusyId === student.id"
                @click="updateStudentStatus(student, 'block')"
              >
                Block
              </button>
              <button
                v-else
                class="primary"
                type="button"
                :disabled="actionBusyId === student.id"
                @click="updateStudentStatus(student, 'unblock')"
              >
                Unblock
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
import { toast } from 'vue3-toastify'
import api from '@/api/client'
import { blockStudent, getAdminStudents, unblockStudent } from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import AdminPagination from '@/components/admin/AdminPagination.vue'

const loading = ref(false)
const actionBusyId = ref(null)
const students = ref([])
const branches = ref([])
const yearOptions = [1, 2, 3, 4, 5]
const filters = reactive({
  search: '',
  branch: '',
  current_level: '',
  cgpa_min: null,
  cgpa_max: null,
  active: '',
})
const page = ref(1)
const limit = ref(10)
const totalPages = ref(1)
const sort = ref({ key: 'name', direction: 'asc' })

const toggleSort = (key) => {
  if (sort.value.key === key) {
    sort.value.direction = sort.value.direction === 'asc' ? 'desc' : 'asc'
  } else {
    sort.value = { key, direction: 'asc' }
  }
  loadStudents(1)
}

const sortMark = (key) => {
  if (sort.value.key !== key) return ''
  return sort.value.direction === 'asc' ? '^' : 'v'
}

const loadStudents = async (nextPage = page.value) => {
  loading.value = true
  try {
    const params = {
      page: nextPage,
      limit: limit.value,
      sort_by: sort.value.key,
      sort_order: sort.value.direction,
      ...(filters.search ? { search: filters.search } : {}),
      ...(filters.branch ? { branch: filters.branch } : {}),
      ...(filters.current_level ? { current_level: filters.current_level } : {}),
      ...(filters.cgpa_min !== null && filters.cgpa_min !== '' ? { cgpa_min: filters.cgpa_min } : {}),
      ...(filters.cgpa_max !== null && filters.cgpa_max !== '' ? { cgpa_max: filters.cgpa_max } : {}),
      ...(filters.active ? { active: filters.active } : {}),
    }
    const res = await getAdminStudents(params)
    students.value = res?.data?.students || []
    page.value = res?.data?.pagination?.page || nextPage
    totalPages.value = res?.data?.pagination?.total_pages || 1
  } catch (err) {
    toast.error(err?.response?.data?.error || 'Failed to load students')
  } finally {
    loading.value = false
  }
}

const loadBranchOptions = async () => {
  try {
    const res = await api.get('/branches')
    branches.value = res?.data?.branches || []
  } catch {
    branches.value = []
  }
}

const updateStudentStatus = async (student, action) => {
  actionBusyId.value = student.id
  try {
    if (action === 'block') {
      await blockStudent(student.id)
      toast.success('Student blocked')
    } else {
      await unblockStudent(student.id)
      toast.success('Student unblocked')
    }
    await loadStudents()
  } catch (err) {
    toast.error(err?.response?.data?.error || `Unable to ${action} student`)
  } finally {
    actionBusyId.value = null
  }
}

const applyFilters = async () => {
  await loadStudents(1)
}

const resetFilters = async () => {
  filters.search = ''
  filters.branch = ''
  filters.current_level = ''
  filters.cgpa_min = null
  filters.cgpa_max = null
  filters.active = ''
  await loadStudents(1)
}

const goToPage = async (nextPage) => {
  const safe = Math.min(Math.max(1, nextPage), totalPages.value)
  await loadStudents(safe)
}

onMounted(async () => {
  await Promise.all([loadBranchOptions(), loadStudents()])
})
</script>

<style scoped>
.admin-table-page {
  display: grid;
  gap: 12px;
}

.filters {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) 140px 90px 110px 110px 160px auto auto;
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
  min-width: 860px;
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

.sub-line {
  margin: 3px 0 0;
  color: #5f7197;
  font-size: 0.82rem;
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

.pill-active {
  background: #e8f8ef;
  color: #1f7a4f;
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

.ghost-danger {
  background: transparent;
  color: #b63838;
  border: 1px solid #e5bcbc;
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

@media (max-width: 780px) {
  .filters {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

