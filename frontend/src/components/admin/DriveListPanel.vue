<template>
  <div>
    <div v-if="loading" class="box">Loading drives...</div>
    <p v-else-if="drives.length === 0" class="state-text">{{ emptyText }}</p>

    <div v-else class="table-wrap">
      <table>
        <colgroup>
          <col class="col-drive-id" />
          <col class="col-drive-name" />
          <col v-if="showCompany" class="col-company" />
          <col class="col-created-on" />
          <col class="col-start-date" />
          <col class="col-end-date" />
          <col class="col-approval" />
          <col class="col-status" />
          <col class="col-mode" />
          <col class="col-action" />
        </colgroup>
        <thead>
          <tr>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'id' }" type="button" @click="toggleSort('id')">
                <u>Drive ID</u> {{ sortMark('id') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'title' }" type="button" @click="toggleSort('title')">
                <u>Drive Name</u> {{ sortMark('title') }}
              </button>
            </th>
            <th v-if="showCompany">Company</th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'create_date' }" type="button" @click="toggleSort('create_date')">
                <u>Created</u> {{ sortMark('create_date') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'start_date' }" type="button" @click="toggleSort('start_date')">
                <u>Start</u> {{ sortMark('start_date') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'end_date' }" type="button" @click="toggleSort('end_date')">
                <u>End</u> {{ sortMark('end_date') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'approval_status' }" type="button" @click="toggleSort('approval_status')">
                <u>Approval</u> {{ sortMark('approval_status') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'status' }" type="button" @click="toggleSort('status')">
                <u>Status</u> {{ sortMark('status') }}
              </button>
            </th>
            <th>
              <button class="sort-btn" :class="{ 'is-active': sortBy === 'work_mode' }" type="button" @click="toggleSort('work_mode')">
                <u>Mode</u> {{ sortMark('work_mode') }}
              </button>
            </th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="drive in drives" :key="drive.id" :class="driveRowClass(drive)">
            <td>
              <button class="drive-link" type="button" @click="openDrive(drive.id)">
                <strong>#{{ drive.id }}</strong>
              </button>
            </td>
            <td>
              <button class="drive-link" type="button" @click="openDrive(drive.id)">
                <strong>{{ drive.title }}</strong>
              </button>
            </td>
            <td v-if="showCompany">{{ drive.company_name || '-' }}</td>
            <td>{{ formatDate(drive.create_date) }}</td>
            <td>{{ formatDate(drive.start_date) }}</td>
            <td>{{ formatDate(drive.end_date) }}</td>
            <td>
              <span class="status-pill" :class="approvalPillClass(drive.approval_status)">{{ drive.approval_status }}</span>
            </td>
            <td>
              <span class="status-pill" :class="driveStatusPillClass(drive.status)">{{ drive.status }}</span>
            </td>
            <td>
              <span class="mode-pill">{{ drive.work_mode || '-' }}</span>
            </td>
            <td class="action-cell">
              <button v-if="showModeration && isDrivePending(drive)" class="primary" type="button" :disabled="actionBusyId === drive.id" @click="emitAction(drive.id, 'approve')">
                Approve
              </button>
              <button v-if="showModeration && isDrivePending(drive)" class="danger" type="button" :disabled="actionBusyId === drive.id" @click="emitAction(drive.id, 'reject')">
                Reject
              </button>
              <button v-if="showModeration && isDriveApproved(drive) && drive.is_active" class="danger ghost-danger" type="button" :disabled="actionBusyId === drive.id" @click="emitAction(drive.id, 'block')">
                Block
              </button>
              <button v-if="showModeration && isDriveApproved(drive) && !drive.is_active" class="ghost" type="button" :disabled="actionBusyId === drive.id" @click="emitAction(drive.id, 'unblock')">
                Unblock
              </button>
              <button v-if="showModeration && isDriveRejected(drive)" class="primary" type="button" :disabled="actionBusyId === drive.id" @click="emitAction(drive.id, 'approve')">
                Approve
              </button>
              <button class="ghost" type="button" @click="openDrive(drive.id)">View Details</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination
      :page="pagination.page"
      :total-pages="pagination.total_pages"
      :disabled="loading"
      :show-jump="showJump"
      input-id="drives-page-jump"
      @go="goToPage"
    />
  </div>
</template>

<script setup>
import AdminPagination from '@/components/admin/AdminPagination.vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  drives: { type: Array, default: () => [] },
  pagination: {
    type: Object,
    default: () => ({ page: 1, total_pages: 1 }),
  },
  sortBy: { type: String, default: 'start_date' },
  sortOrder: { type: String, default: 'desc' },
  actionBusyId: { type: [Number, String, null], default: null },
  showModeration: { type: Boolean, default: false },
  showCompany: { type: Boolean, default: true },
  showJump: { type: Boolean, default: false },
  emptyText: { type: String, default: 'No drives found.' },
})

const emit = defineEmits(['toggle-sort', 'open-drive', 'drive-action', 'go-page'])

const normalize = (value) => String(value || '').trim().toLowerCase()

const sortMark = (key) => {
  if (props.sortBy !== key) return ''
  return props.sortOrder === 'asc' ? '^' : 'v'
}

const toggleSort = (key) => {
  emit('toggle-sort', key)
}

const openDrive = (driveId) => {
  emit('open-drive', driveId)
}

const emitAction = (driveId, action) => {
  emit('drive-action', { driveId, action })
}

const goToPage = (page) => {
  emit('go-page', page)
}

const isDriveApproved = (drive) => normalize(drive?.approval_status) === 'approved'
const isDrivePending = (drive) => normalize(drive?.approval_status) === 'pending'
const isDriveRejected = (drive) => normalize(drive?.approval_status) === 'rejected'

const approvalPillClass = (value) => {
  const key = normalize(value)
  if (key === 'approved') return 'pill-approved'
  if (key === 'rejected') return 'pill-rejected'
  if (key === 'pending') return 'pill-pending'
  return 'pill-neutral'
}

const driveStatusPillClass = (value) => {
  const key = normalize(value)
  if (key === 'active') return 'pill-active'
  if (key === 'upcoming') return 'pill-upcoming'
  if (key === 'closed') return 'pill-closed'
  if (key === 'cancelled') return 'pill-rejected'
  if (key === 'pending') return 'pill-pending'
  return 'pill-neutral'
}

const driveRowClass = (drive) => {
  const key = normalize(drive?.status)
  if (key === 'active') return 'row-active'
  if (key === 'upcoming') return 'row-upcoming'
  if (key === 'pending') return 'row-pending'
  if (key === 'closed') return 'row-closed'
  return 'row-neutral'
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
</script>

<style scoped>
.box {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
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

.col-drive-id {
  width: 6%;
}

.col-drive-name {
  width: 15%;
}

.col-company {
  width: 13%;
}

.col-created-on,
.col-start-date,
.col-end-date {
  width: 10%;
}

.col-approval,
.col-status,
.col-mode {
  width: 8%;
}

.col-action {
  width: 12%;
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
  border: none;
  background: transparent;
  color: inherit;
  padding: 0;
  font: inherit;
  cursor: pointer;
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

.pill-approved {
  color: #067647;
  background: #e7f6ee;
}

.pill-active,
.pill-upcoming {
  color: #175cd3;
  background: #e8f1ff;
}

.pill-pending {
  color: #9a5d00;
  background: #fff0d8;
}

.pill-rejected {
  color: #8f2e2e;
  background: #fde9e9;
}

.pill-closed,
.pill-neutral {
  color: #596278;
  background: #edf0f5;
}

.primary,
.danger,
.ghost {
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

.primary {
  border: none;
  background: #2f66db;
  color: #fff;
  white-space: nowrap;
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
  height: 34px;
  border-radius: 8px;
  padding: 0 12px;
  border: 1px solid #cfd9ee;
  background: #fff;
  color: #2f4b80;
  font-weight: 600;
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
  table {
    min-width: 900px;
  }
}
</style>
