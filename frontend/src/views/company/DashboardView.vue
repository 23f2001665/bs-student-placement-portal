<template>
  <section class="dashboard-page">
    <header class="page-header">
      <h2>Company Dashboard</h2>
      <button class="ghost" type="button" :disabled="loading" @click="loadDashboard">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <div class="stats">
      <article>
        <h3>{{ totals.drives }}</h3>
        <p>Total Drives</p>
      </article>
      <article>
        <h3>{{ totals.active_drives }}</h3>
        <p>Active</p>
      </article>
      <article>
        <h3>{{ totals.applications }}</h3>
        <p>Total Applications</p>
      </article>
      <article>
        <h3>{{ selectedCount }}</h3>
        <p>Selected</p>
      </article>
    </div>

    <div class="charts">
      <article class="chart-card">
        <h4>Drives Status (Approval)</h4>
        <div class="svg-chart-wrap">
          <svg class="svg-chart" viewBox="0 0 360 170" role="img" aria-label="Drive approval chart">
            <line x1="36" y1="12" x2="36" y2="146" class="axis" />
            <line x1="36" y1="146" x2="350" y2="146" class="axis" />
            <g v-for="bar in approvalBars" :key="`approval-${bar.key}`">
              <rect :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" class="bar-approval" />
              <text :x="bar.x + bar.width / 2" y="160" class="label" text-anchor="middle">{{ prettyLabel(bar.key) }}</text>
              <text :x="bar.x + bar.width / 2" :y="bar.y - 3" class="value" text-anchor="middle">{{ bar.value }}</text>
            </g>
          </svg>
        </div>
        <p class="chart-note">Shows how your drives are distributed across approval states.</p>
      </article>

      <article class="chart-card">
        <h4>Application Status</h4>
        <div class="svg-chart-wrap">
          <svg class="svg-chart" viewBox="0 0 360 170" role="img" aria-label="Application status chart">
            <line x1="36" y1="12" x2="36" y2="146" class="axis" />
            <line x1="36" y1="146" x2="350" y2="146" class="axis" />
            <g v-for="bar in applicationBars" :key="`application-${bar.key}`">
              <rect :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" class="bar-app" />
              <text :x="bar.x + bar.width / 2" y="160" class="label" text-anchor="middle">{{ prettyLabel(bar.key) }}</text>
              <text :x="bar.x + bar.width / 2" :y="bar.y - 3" class="value" text-anchor="middle">{{ bar.value }}</text>
            </g>
          </svg>
        </div>
        <p class="chart-note">Shows application volume split by application status.</p>
      </article>

      <article class="chart-card">
        <h4>Drive Branch (Allowed vs Applied)</h4>
        <div class="branch-chart">
          <div v-for="row in branchRows" :key="row.key" class="branch-row">
            <div class="branch-head">
              <span>{{ prettyLabel(row.key) }}</span>
              <span>Max Allowed {{ row.allowed }} | applied {{ row.applied }}</span>
            </div>
            <div class="branch-track">
              <div class="branch-fill allowed" :style="{ width: `${row.allowedWidth}%` }"></div>
              <div class="branch-fill applied" :style="{ width: `${row.appliedWidth}%` }"></div>
            </div>
          </div>
        </div>
        <p class="chart-note">Compares how often each branch was allowed versus actually applied.</p>
      </article>

      <article class="chart-card">
        <h4>Current Month: Application Status</h4>
        <p class="month-caption">{{ currentMonthLabel }}</p>
        <div class="current-month-chart" role="img" aria-label="Current month pie chart for application statuses">
          <svg class="pie-chart" viewBox="0 0 180 180">
            <circle cx="90" cy="90" :r="pieRadius" class="pie-base" />
            <g transform="translate(90, 90) rotate(-90)">
              <circle
                v-for="slice in pieSlices"
                :key="`slice-${slice.key}`"
                cx="0"
                cy="0"
                :r="pieRadius"
                fill="none"
                :stroke-dasharray="`${slice.length} ${pieCircumference}`"
                :stroke-dashoffset="slice.offset"
                :class="`segment-stroke-${slice.key}`"
                class="pie-slice"
              />
            </g>
            <text x="90" y="86" class="pie-total" text-anchor="middle">{{ currentMonthTotal }}</text>
            <text x="90" y="104" class="pie-sub" text-anchor="middle">Total</text>
          </svg>
          <p v-if="currentMonthTotal === 0" class="empty-month">No applications this month yet.</p>
          <ul v-else class="pie-legend">
            <li v-for="segment in currentMonthSegments" :key="`legend-${segment.key}`">
              <span class="legend-dot" :class="`dot-${segment.key}`"></span>
              <span>{{ segment.label }}</span>
              <strong>{{ segment.count }}</strong>
              <span>{{ segment.percent }}%</span>
            </li>
          </ul>
        </div>
        <p class="chart-note">Shows current month distribution of applied, shortlisted, selected, and rejected.</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { toast } from 'vue3-toastify'
import { getCompanySummary } from '@/api/company'

const totals = ref({ drives: 0, active_drives: 0, applications: 0 })
const loading = ref(false)
const distribution = ref({
  drive_status: {},
  drive_approval: {},
  applications: {},
  work_mode: {},
  branches: { allowed: {}, applied: {} },
  monthly_applications: [],
})
const driveApplication = ref({ total: 0 })

const driveApplicationBars = computed(() => {
  const data = { ...driveApplication.value }
  delete data.total
  return data
})

const selectedCount = computed(() => {
  const entries = Object.entries(driveApplication.value || {})
  const row = entries.find(([key]) => String(key).toLowerCase() === 'selected')
  return Number(row?.[1] || 0)
})

const BRANCH_NAMES = {
  ce: 'Civil Engineering',
  cse: 'Computer Science and Engineering',
  ds: 'Data Science',
  ee: 'Electrical Engineering',
  ece: 'Electronics and Communication Engineering',
  it: 'Information Technology',
  me: 'Mechanical Engineering',
}

const ALL_BRANCHES = Object.values(BRANCH_NAMES)

const normalizeBranchKey = (key) => {
  const raw = String(key || '').trim()
  if (!raw) return ''

  const lower = raw.toLowerCase()
  if (BRANCH_NAMES[lower]) return BRANCH_NAMES[lower]

  const fullMatch = Object.values(BRANCH_NAMES).find((name) => name.toLowerCase() === lower)
  if (fullMatch) return fullMatch

  if (lower === 'all') return 'All Branches'
  return prettyLabel(raw)
}

const normalizedBranches = computed(() => {
  const allowedRaw = distribution.value.branches?.allowed || {}
  const appliedRaw = distribution.value.branches?.applied || {}
  const result = {}

  Object.entries(allowedRaw).forEach(([key, value]) => {
    const normalized = normalizeBranchKey(key)
    if (!normalized) return
    if (!result[normalized]) result[normalized] = { allowed: 0, applied: 0 }
    result[normalized].allowed += Number(value || 0)
  })

  Object.entries(appliedRaw).forEach(([key, value]) => {
    const normalized = normalizeBranchKey(key)
    if (!normalized) return
    if (!result[normalized]) result[normalized] = { allowed: 0, applied: 0 }
    result[normalized].applied += Number(value || 0)
  })

  return result
})

const branchKeys = computed(() => {
  const present = new Set(Object.keys(normalizedBranches.value))
  ALL_BRANCHES.forEach((branch) => present.add(branch))
  if (present.has('All Branches')) {
    const withoutAll = [...present].filter((key) => key !== 'All Branches').sort()
    return [...withoutAll, 'All Branches']
  }
  return [...present].sort()
})

const monthlyApplications = computed(() => distribution.value.monthly_applications || [])
const MONTHLY_STATUS_KEYS = ['applied', 'shortlisted', 'selected', 'rejected']

const prettyLabel = (key) => {
  return String(key || '')
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim()
    .replace(/^./, (m) => m.toUpperCase())
}

const toBars = (raw) => {
  const obj = raw || {}
  const max = Math.max(1, ...Object.values(obj).map((v) => Number(v || 0)))
  return Object.entries(obj).map(([key, value]) => ({
    key,
    value: Number(value || 0),
    width: Math.max(4, Math.round((Number(value || 0) / max) * 100)),
  }))
}

const toSvgBars = (raw, chartWidth = 314, chartHeight = 132, maxBars = 6, chartBottom = 146) => {
  const source = toBars(raw).slice(0, maxBars)
  const max = Math.max(1, ...source.map((s) => s.value))
  const slot = chartWidth / Math.max(1, source.length)
  const width = Math.max(14, slot - 10)
  return source.map((item, index) => {
    const height = Math.round((item.value / max) * (chartHeight - 12))
    const x = 36 + Math.round(index * slot + (slot - width) / 2)
    const y = chartBottom - height
    return { ...item, x, y, width, height }
  })
}

const approvalBars = computed(() => toSvgBars(distribution.value.drive_approval))
const applicationBars = computed(() => toSvgBars(driveApplicationBars.value))

const branchRows = computed(() => {
  const keys = branchKeys.value
  const max = Math.max(
    1,
    ...keys.map((key) => {
      const row = normalizedBranches.value[key] || { allowed: 0, applied: 0 }
      return Math.max(Number(row.allowed || 0), Number(row.applied || 0))
    }),
  )
  return keys.map((key) => {
    const row = normalizedBranches.value[key] || { allowed: 0, applied: 0 }
    const allowed = Number(row.allowed || 0)
    const applied = Number(row.applied || 0)
    return {
      key,
      allowed,
      applied,
      allowedWidth: Math.max(0, Math.round((allowed / max) * 100)),
      appliedWidth: Math.max(0, Math.round((applied / max) * 100)),
    }
  })
})

const monthlyApplicationStatus = computed(() => {
  const rows = distribution.value.monthly_application_status || []
  if (rows.length) {
    return [...rows].sort((a, b) => String(a.month || '').localeCompare(String(b.month || '')))
  }

  return monthlyApplications.value.map((row) => ({
    month: row.month,
    applied: Number(row.count || 0),
    shortlisted: 0,
    selected: 0,
    rejected: 0,
  }))
})

const currentMonthKey = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
})

const currentMonthRow = computed(() => {
  const found = monthlyApplicationStatus.value.find((row) => String(row.month) === currentMonthKey.value)
  if (found) return found

  return {
    month: currentMonthKey.value,
    applied: 0,
    shortlisted: 0,
    selected: 0,
    rejected: 0,
  }
})

const currentMonthTotal = computed(() => {
  return MONTHLY_STATUS_KEYS.reduce((sum, key) => sum + Number(currentMonthRow.value[key] || 0), 0)
})

const currentMonthSegments = computed(() => {
  const total = currentMonthTotal.value
  return MONTHLY_STATUS_KEYS.map((key) => {
    const count = Number(currentMonthRow.value[key] || 0)
    const ratio = total ? count / total : 0
    const percent = Math.round(ratio * 100)
    return {
      key,
      label: prettyLabel(key),
      count,
      percent,
      ratio,
    }
  })
})

const pieRadius = 52
const pieCircumference = 2 * Math.PI * pieRadius

const pieSlices = computed(() => {
  if (!currentMonthTotal.value) return []

  let acc = 0
  return currentMonthSegments.value
    .filter((segment) => segment.count > 0)
    .map((segment) => {
      const length = Math.max(0, segment.ratio * pieCircumference)
      const slice = {
        key: segment.key,
        length,
        offset: -acc,
      }
      acc += length
      return slice
    })
})

const currentMonthLabel = computed(() => {
  const [year, month] = String(currentMonthRow.value.month || currentMonthKey.value).split('-')
  const date = new Date(Number(year), Number(month || 1) - 1, 1)
  return Number.isNaN(date.getTime())
    ? String(currentMonthRow.value.month || currentMonthKey.value)
    : date.toLocaleString(undefined, { month: 'long', year: 'numeric' })
})

const loadDashboard = async () => {
  loading.value = true
  try {
    const res = await getCompanySummary()
    totals.value = res.data.totals || totals.value
    distribution.value = res.data.distribution || distribution.value
    driveApplication.value = res.data.drive_application || driveApplication.value
  } catch (error) {
    toast.error('Failed to load dashboard data')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadDashboard()
})
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

h2 {
  margin: 0;
}

p {
  margin: 0;
  color: #607094;
}

.ghost {
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
  background: #edf2ff;
  color: #2f66db;
}

.ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.stats article,
.chart-card {
  background: #fff;
  border: 1px solid #e3e7ef;
  border-radius: 10px;
  padding: 10px;
}

h3 {
  margin: 0;
  color: #1b2a4b;
  font-size: 1.25rem;
}

.stats article p {
  margin-top: 4px;
  font-size: 0.8rem;
}

.charts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.chart-card h4 {
  margin: 0 0 8px;
}

.chart-note {
  margin-top: 6px;
  font-size: 0.76rem;
  color: #607094;
}

.svg-chart-wrap {
  overflow-x: auto;
}

.svg-chart {
  width: 100%;
  min-width: 320px;
  height: 168px;
}

.axis {
  stroke: #cfd7eb;
  stroke-width: 1;
}

.bar-approval {
  fill: #2f66db;
}

.bar-app {
  fill: #2d9f75;
}

.label {
  font-size: 9px;
  fill: #596680;
}

.value {
  font-size: 9px;
  fill: #202b42;
  font-weight: 600;
}

.month-caption {
  font-size: 0.82rem;
  color: #4f5f80;
  margin-bottom: 8px;
}

.current-month-chart {
  display: grid;
  gap: 8px;
}

.pie-chart {
  width: 146px;
  height: 146px;
}

.pie-base {
  fill: none;
  stroke: #e8edf6;
  stroke-width: 20;
}

.pie-slice {
  stroke-width: 20;
}

.segment-stroke-applied {
  stroke: #2f66db;
}

.segment-stroke-shortlisted {
  stroke: #2d9f75;
}

.segment-stroke-selected {
  stroke: #a15cd1;
}

.segment-stroke-rejected {
  stroke: #e68538;
}

.pie-total {
  fill: #1b2a4b;
  font-size: 18px;
  font-weight: 700;
}

.pie-sub {
  fill: #607094;
  font-size: 11px;
}

.pie-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

.pie-legend li {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 8px;
  align-items: center;
  font-size: 11px;
  color: #3f4b66;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-applied {
  background: #2f66db;
}

.dot-shortlisted {
  background: #2d9f75;
}

.dot-selected {
  background: #a15cd1;
}

.dot-rejected {
  background: #e68538;
}

.empty-month {
  font-size: 0.85rem;
  color: #607094;
}

.branch-chart {
  display: grid;
  gap: 6px;
}

.branch-row {
  display: grid;
  gap: 4px;
}

.branch-head {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #43506a;
}

.branch-track {
  display: grid;
  gap: 3px;
}

.branch-fill {
  height: 6px;
  border-radius: 999px;
}

.branch-fill.allowed {
  background: #2f66db;
}

.branch-fill.applied {
  background: #e68538;
}

.bar-list,
.paired-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.bar-list,
.paired-list,
.bar-head,
.bar-track,
.bar-fill,
.branch-name,
.pill,
.pill.allowed,
.pill.applied {
  display: none;
}

.bar-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #3f4b66;
}

.bar-track {
  height: 7px;
  border-radius: 999px;
  background: #e8edf9;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #2f66db;
}

.paired-list li {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 6px;
  align-items: center;
}

.branch-name {
  color: #3f4b66;
  font-size: 13px;
}

.pill {
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 600;
}

.pill.allowed {
  color: #155eef;
  background: #eaf0ff;
}

.pill.applied {
  color: #7a2e0e;
  background: #ffe7d5;
}

@media (max-width: 760px) {
  .stats {
    grid-template-columns: 1fr 1fr;
  }

  .charts {
    grid-template-columns: 1fr;
  }
}

@media (max-height: 920px) {
  .dashboard-page {
    gap: 6px;
  }

  .stats article,
  .chart-card {
    padding: 8px;
  }

  .chart-card h4 {
    margin-bottom: 6px;
    font-size: 1rem;
  }

  .chart-note {
    display: none;
  }

  .svg-chart {
    min-width: 300px;
    height: 152px;
  }

  .pie-chart {
    width: 132px;
    height: 132px;
  }

  .pie-legend li {
    font-size: 10px;
    gap: 6px;
  }

  .month-caption {
    margin-bottom: 6px;
    font-size: 0.76rem;
  }
}
</style>

