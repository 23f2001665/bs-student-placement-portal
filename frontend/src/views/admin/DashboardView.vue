<template>
  <section class="admin-dashboard">
    <AdminPageHeader
      title="Dashboard Summary"
      :show-refresh="true"
      :refreshing="loading"
      :refresh-disabled="loading"
      @refresh="loadDashboard"
    />

    <p v-if="loading" class="state-text">Loading dashboard data...</p>
    <p v-else-if="error" class="state-text error">{{ error }}</p>

    <template v-else>
      <section class="stats">
        <article>
          <h3>{{ dashboard.totals?.students ?? 0 }}</h3>
          <p>Total Students</p>
        </article>
        <article>
          <h3>{{ dashboard.totals?.companies ?? 0 }}</h3>
          <p>Total Companies</p>
        </article>
        <article>
          <h3>{{ dashboard.totals?.drives ?? 0 }}</h3>
          <p>Total Drives</p>
        </article>
        <article>
          <h3>{{ dashboard.totals?.applications ?? 0 }}</h3>
          <p>Total Applications</p>
        </article>
      </section>

      <section class="dashboard-main">
        <article class="chart-card summary-table-card">
          <h3>Summary Table</h3>
          <div class="summary-table-wrap">
            <table class="summary-table">
              <thead>
                <tr>
                  <th>Entity</th>
                  <th>Total</th>
                  <th>Breakdown</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in summaryRows" :key="`sum-${row.entity}`">
                  <td>{{ row.entity }}</td>
                  <td>{{ row.total }}</td>
                  <td class="metric-list-cell">
                    <ul class="metric-list">
                      <li v-for="metric in row.metrics" :key="`${row.entity}-${metric.label}`" class="metric-item">
                        <span class="metric-label">{{ metric.label }}</span>
                        <strong v-if="metric.value !== null">{{ metric.value }}</strong>
                        <span v-else class="metric-empty">-</span>
                      </li>
                    </ul>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="chart-card pie-card">
          <h3>Application Status Mix</h3>
          <div class="pie-wrap">
            <svg class="pie-chart" viewBox="0 0 180 180" role="img" aria-label="Application status pie chart">
              <circle cx="90" cy="90" :r="pieRadius" class="pie-base" />
              <g transform="translate(90, 90) rotate(-90)">
                <circle
                  v-for="slice in pieSlices"
                  :key="`app-slice-${slice.key}`"
                  cx="0"
                  cy="0"
                  :r="pieRadius"
                  fill="none"
                  :stroke-dasharray="`${slice.length} ${pieCircumference}`"
                  :stroke-dashoffset="slice.offset"
                  :class="`segment-${slice.css}`"
                  class="pie-slice"
                />
              </g>
              <text x="90" y="86" class="pie-total" text-anchor="middle">{{ applicationsTotal }}</text>
              <text x="90" y="104" class="pie-sub" text-anchor="middle">Total</text>
            </svg>

            <ul v-if="applicationSegments.length" class="pie-legend">
              <li v-for="segment in applicationSegments" :key="`legend-${segment.key}`">
                <span class="legend-dot" :class="`dot-${segment.css}`"></span>
                <span>{{ segment.label }}</span>
                <strong>{{ segment.count }}</strong>
                <span>{{ segment.percent }}%</span>
              </li>
            </ul>
            <p v-else class="state-text">No application distribution data available yet.</p>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { toast } from 'vue3-toastify'
import { getAdminDashboard } from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'

const loading = ref(false)
const error = ref('')

const createEmptyDashboard = () => ({
  totals: { students: 0, companies: 0, drives: 0, applications: 0 },
  active: { students: 0, companies: 0, drives: 0 },
  pending: { companies: 0, drives: 0 },
  rejected: { companies: 0, drives: 0, applications: 0 },
  summary: {
    students: { total: 0, active: 0, inactive: 0 },
    companies: { total: 0, approved_active: 0, pending_approval: 0, rejected_or_blocked: 0, approved_inactive: 0 },
    drives: { total: 0, approved_active: 0, pending_approval: 0, rejected_approval: 0, approved_inactive: 0 },
    applications: { total: 0, applied: 0, short_listed: 0, selected: 0, rejected: 0 },
  },
  applications: { total: 0, status_distribution: {} },
  distribution: { applications: {} },
})

const dashboard = ref(createEmptyDashboard())

const normalizeLabel = (value) =>
  String(value || '')
    .replace(/_/g, ' ')
    .replace(/^./, (m) => m.toUpperCase())

const normalizeStatusKey = (value) => String(value || '').toLowerCase().replace(/[_\s]/g, '')

const summaryRows = computed(() => {
  const totals = dashboard.value.totals || {}
  const active = dashboard.value.active || {}
  const pending = dashboard.value.pending || {}
  const rejected = dashboard.value.rejected || {}
  const summary = dashboard.value.summary || {}

  return [
    {
      entity: 'Students',
      total: Number(summary.students?.total ?? totals.students ?? 0),
      metrics: [
        { label: 'Active', value: Number(summary.students?.active ?? active.students ?? 0) },
        {
          label: 'Inactive',
          value: Number(summary.students?.inactive ?? Math.max(0, Number(totals.students || 0) - Number(active.students || 0))),
        },
      ],
    },
    {
      entity: 'Companies',
      total: Number(summary.companies?.total ?? totals.companies ?? 0),
      metrics: [
        { label: 'Approved + Active', value: Number(summary.companies?.approved_active ?? 0) },
        { label: 'Pending Approval', value: Number(summary.companies?.pending_approval ?? pending.companies ?? 0) },
        { label: 'Rejected/Blocked', value: Number(summary.companies?.rejected_or_blocked ?? rejected.companies ?? 0) },
        { label: 'Approved + Inactive', value: Number(summary.companies?.approved_inactive ?? 0) },
      ],
    },
    {
      entity: 'Drives',
      total: Number(summary.drives?.total ?? totals.drives ?? 0),
      metrics: [
        { label: 'Approved + Active', value: Number(summary.drives?.approved_active ?? 0) },
        { label: 'Pending Approval', value: Number(summary.drives?.pending_approval ?? pending.drives ?? 0) },
        { label: 'Rejected Approval', value: Number(summary.drives?.rejected_approval ?? rejected.drives ?? 0) },
        { label: 'Approved + Inactive', value: Number(summary.drives?.approved_inactive ?? 0) },
      ],
    },
    {
      entity: 'Applications',
      total: Number(summary.applications?.total ?? totals.applications ?? 0),
      metrics: [
        { label: 'Applied', value: Number(summary.applications?.applied ?? 0) },
        { label: 'ShortListed', value: Number(summary.applications?.short_listed ?? 0) },
        { label: 'Selected', value: Number(summary.applications?.selected ?? 0) },
        { label: 'Rejected', value: Number(summary.applications?.rejected ?? 0) },
      ],
    },
  ]
})

const readDistributionCount = (distribution, key) => {
  const target = normalizeStatusKey(key)
  for (const [status, count] of Object.entries(distribution || {})) {
    if (normalizeStatusKey(status) === target) {
      return Number(count || 0)
    }
  }
  return 0
}

const applicationCounts = computed(() => {
  const distribution =
    dashboard.value.applications?.status_distribution ||
    dashboard.value.distribution?.applications ||
    {}
  const summaryApps = dashboard.value.summary?.applications || {}

  return {
    applied: readDistributionCount(distribution, 'applied') || Number(summaryApps.applied || 0),
    short_listed: readDistributionCount(distribution, 'short_listed') || Number(summaryApps.short_listed || 0),
    selected: readDistributionCount(distribution, 'selected') || Number(summaryApps.selected || 0),
    rejected: readDistributionCount(distribution, 'rejected') || Number(summaryApps.rejected || 0),
  }
})

const applicationsTotal = computed(() => {
  const totalFromApi = Number(dashboard.value.applications?.total || 0)
  if (totalFromApi > 0) return totalFromApi
  const counts = applicationCounts.value
  return Number(counts.applied + counts.short_listed + counts.selected + counts.rejected)
})

const pieRadius = 42
const pieCircumference = 2 * Math.PI * pieRadius

const applicationSegments = computed(() => {
  const counts = applicationCounts.value
  const total = applicationsTotal.value

  const rows = [
    { key: 'applied', css: 'applied', label: normalizeLabel('applied'), count: counts.applied },
    { key: 'short_listed', css: 'shortlisted', label: normalizeLabel('short_listed'), count: counts.short_listed },
    { key: 'selected', css: 'selected', label: normalizeLabel('selected'), count: counts.selected },
    { key: 'rejected', css: 'rejected', label: normalizeLabel('rejected'), count: counts.rejected },
  ]

  return rows
    .filter((item) => item.count > 0)
    .map((item) => ({
      ...item,
      percent: total > 0 ? Math.round((item.count / total) * 100) : 0,
    }))
})

const pieSlices = computed(() => {
  let offset = 0
  return applicationSegments.value.map((segment) => {
    const length = applicationsTotal.value > 0 ? (segment.count / applicationsTotal.value) * pieCircumference : 0
    const slice = { ...segment, length, offset: -offset }
    offset += length
    return slice
  })
})

const loadDashboard = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getAdminDashboard()
    const payload = res?.data || {}
    const empty = createEmptyDashboard()
    dashboard.value = {
      ...empty,
      ...payload,
      totals: { ...empty.totals, ...(payload.totals || {}) },
      active: { ...empty.active, ...(payload.active || {}) },
      pending: { ...empty.pending, ...(payload.pending || {}) },
      rejected: { ...empty.rejected, ...(payload.rejected || {}) },
      summary: {
        ...empty.summary,
        ...(payload.summary || {}),
        students: { ...empty.summary.students, ...(payload.summary?.students || {}) },
        companies: { ...empty.summary.companies, ...(payload.summary?.companies || {}) },
        drives: { ...empty.summary.drives, ...(payload.summary?.drives || {}) },
        applications: { ...empty.summary.applications, ...(payload.summary?.applications || {}) },
      },
      applications: {
        ...empty.applications,
        ...(payload.applications || {}),
        status_distribution: {
          ...empty.applications.status_distribution,
          ...(payload.applications?.status_distribution || {}),
        },
      },
      distribution: {
        ...empty.distribution,
        ...(payload.distribution || {}),
        applications: {
          ...empty.distribution.applications,
          ...(payload.distribution?.applications || {}),
        },
      },
    }
  } catch (err) {
    error.value = err?.response?.data?.error || 'Unable to load dashboard summary.'
    toast.error('Failed to load dashboard data')
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.admin-dashboard {
  display: grid;
  gap: 10px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.stats article {
  border: 1px solid #e0e7f4;
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}

.stats h3 {
  margin: 0;
  color: #1f3158;
  font-size: 1.2rem;
}

.stats p {
  margin: 4px 0 0;
  color: #607094;
  font-size: 0.84rem;
}

.dashboard-main {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 1fr);
  gap: 10px;
  align-items: start;
}

.chart-card {
  border: 1px solid #e0e7f4;
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}

.chart-card h3 {
  margin: 0 0 8px;
  color: #1f3158;
}

.summary-table-card {
  display: grid;
  align-content: start;
  max-height: 430px;
  overflow: hidden;
}

.summary-table-wrap {
  max-height: 374px;
  overflow: auto;
}

.summary-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
  color: #3d4f76;
}

.summary-table th,
.summary-table td {
  border-bottom: 1px solid #e6edf9;
  padding: 6px;
  text-align: right;
  white-space: nowrap;
}

.summary-table th:first-child,
.summary-table td:first-child {
  text-align: left;
  font-weight: 700;
}

.summary-table thead th {
  font-size: 0.72rem;
  color: #5c7099;
  background: #f7faff;
}

.summary-table th:nth-child(3),
.summary-table td:nth-child(3) {
  text-align: left;
}

.metric-list-cell {
  white-space: normal;
  min-width: 210px;
}

.metric-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 4px;
}

.metric-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: baseline;
}

.metric-label {
  display: block;
  font-size: 0.7rem;
  color: #5f739e;
  line-height: 1.2;
}

.metric-item strong {
  display: block;
  font-size: 0.8rem;
  color: #2a3f6d;
  line-height: 1.2;
}

.metric-empty {
  display: block;
  color: #99a8c7;
  font-size: 0.8rem;
}

.pie-wrap {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  justify-items: center;
}

.pie-chart {
  width: 190px;
  height: 190px;
}

.pie-base {
  fill: none;
  stroke: #edf1f8;
  stroke-width: 18;
}

.pie-slice {
  stroke-width: 18;
  stroke-linecap: butt;
}

.segment-applied {
  stroke: #4f86f1;
}

.segment-shortlisted {
  stroke: #59b4ff;
}

.segment-selected {
  stroke: #34a66a;
}

.segment-rejected {
  stroke: #d45959;
}

.segment-neutral {
  stroke: #8b9ab8;
}

.pie-total {
  fill: #223b70;
  font-size: 14px;
  font-weight: 700;
}

.pie-sub {
  fill: #5c7099;
  font-size: 10px;
}

.pie-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
  width: 100%;
  max-width: 360px;
}

.pie-legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto auto;
  gap: 6px;
  align-items: center;
  color: #4a618d;
  font-size: 0.8rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-applied {
  background: #4f86f1;
}

.dot-shortlisted {
  background: #59b4ff;
}

.dot-selected {
  background: #34a66a;
}

.dot-rejected {
  background: #d45959;
}

.dot-neutral {
  background: #8b9ab8;
}

.state-text {
  margin: 0;
  color: #4b6088;
}

.state-text.error {
  color: #9b2f2f;
}

@media (max-width: 1080px) {
  .dashboard-main {
    grid-template-columns: 1fr;
  }

  .summary-table-card {
    max-height: none;
    overflow: visible;
  }

  .summary-table-wrap {
    max-height: none;
  }
}

@media (max-width: 760px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metric-list-cell {
    min-width: 160px;
  }
}

@media (max-width: 520px) {
  .stats {
    grid-template-columns: 1fr;
  }
}

@media (max-height: 920px) {
  .admin-dashboard {
    gap: 8px;
  }

  .stats article,
  .chart-card {
    padding: 8px;
  }

  .stats h3 {
    font-size: 1.08rem;
  }

  .summary-table {
    font-size: 0.72rem;
  }

  .summary-table th,
  .summary-table td {
    padding: 5px 4px;
  }

  .chart-card h3 {
    margin-bottom: 6px;
    font-size: 1.08rem;
  }

  .pie-chart {
    width: 168px;
    height: 168px;
  }

  .pie-legend li {
    font-size: 0.74rem;
  }
}
</style>
