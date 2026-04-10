<template>
  <section class="application-detail-page">
    <AdminPageHeader
      :title="`Application #${application?.id || route.params.applicationId}`"
      subtitle="Detailed application view for review and auditing."
      :show-refresh="true"
      :show-back="true"
      :refreshing="loading"
      :refresh-disabled="loading"
      @refresh="loadApplication"
      @back="goBack"
    />

    <div v-if="loading && !payload" class="card">Loading application detail...</div>

    <template v-else-if="payload">
      <section class="detail-grid">
        <article class="card">
          <h4>Application</h4>
          <ul>
            <li><span>Application ID</span><strong>{{ application?.id ?? '-' }}</strong></li>
            <li><span>Status</span><strong>{{ application?.status || '-' }}</strong></li>
            <li><span>Applied On</span><strong>{{ formatDateTime(application?.application_date) }}</strong></li>
            <li><span>Student ID</span><strong>{{ application?.student_id ?? '-' }}</strong></li>
            <li><span>Drive ID</span><strong>{{ application?.drive_id ?? '-' }}</strong></li>
            <li>
              <span>Resume Link</span>
              <strong class="wrap">
                <a
                  v-if="resumeHref"
                  :href="resumeHref"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open Resume
                </a>
                <template v-else>-</template>
              </strong>
            </li>
            <li><span>Resume Note</span><strong class="wrap">{{ application?.resume_note || '-' }}</strong></li>
          </ul>
        </article>

        <article class="card">
          <h4>Student</h4>
          <ul>
            <li><span>Name</span><strong>{{ student?.name || '-' }}</strong></li>
            <li><span>Email</span><strong class="wrap">{{ student?.email || '-' }}</strong></li>
            <li><span>Roll</span><strong>{{ student?.roll || '-' }}</strong></li>
            <li><span>Branch</span><strong class="wrap">{{ student?.branch || '-' }}</strong></li>
            <li><span>Current Level</span><strong>{{ student?.current_level ?? '-' }}</strong></li>
            <li><span>CGPA</span><strong>{{ student?.cgpa ?? '-' }}</strong></li>
            
          </ul>
        </article>

        <article class="card">
          <h4>Drive</h4>
          <ul>
            <li><span>Title</span><strong class="wrap">{{ drive?.title || '-' }}</strong></li>
            <li><span>Status</span><strong>{{ drive?.status || '-' }}</strong></li>
            <li><span>Approval</span><strong>{{ drive?.approval_status || '-' }}</strong></li>
            <li><span>Work Mode</span><strong>{{ drive?.work_mode || '-' }}</strong></li>
            <li><span>Start Date</span><strong>{{ formatDateTime(drive?.start_date) }}</strong></li>
            <li><span>End Date</span><strong>{{ formatDateTime(drive?.end_date) }}</strong></li>
            <li><span>Min CGPA</span><strong>{{ drive?.min_cgpa ?? '-' }}</strong></li>
            <li>
              <span>Allowed Branches</span>
              <strong class="wrap">{{ formatBranches(drive?.allowed_branches) }}</strong>
            </li>
            <li><span>Max Applications</span><strong>{{ drive?.max_applications ?? '-' }}</strong></li>
          </ul>
        </article>

        <article class="card">
          <h4>Company</h4>
          <ul>
            <li><span>Name</span><strong>{{ company?.name || '-' }}</strong></li>
            <li><span>Email</span><strong class="wrap">{{ company?.email || '-' }}</strong></li>
            <li>
              <span>Website</span>
              <strong class="wrap">
                <a v-if="company?.website" :href="company.website" target="_blank" rel="noopener noreferrer">
                  {{ company.website }}
                </a>
                <template v-else>-</template>
              </strong>
            </li>
            <li><span>Industry</span><strong>{{ company?.industry_type || '-' }}</strong></li>
          </ul>
        </article>

        <article class="card interview-card">
          <h4>Interview</h4>
          <ul>
            <li><span>Interview Date</span><strong>{{ application?.interview?.interview_date || '-' }}</strong></li>
            <li><span>Interview Time</span><strong>{{ application?.interview?.interview_time || '-' }}</strong></li>
            <li><span>Details</span><strong class="wrap">{{ application?.interview?.details || '-' }}</strong></li>
          </ul>
        </article>
      </section>
    </template>

    <p v-else class="card">Application details are unavailable.</p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { getAdminApplicationDetail } from '@/api/admin'
import AdminPageHeader from '@/components/admin/AdminPageHeader.vue'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const payload = ref(null)

const applicationId = computed(() => Number(route.params.applicationId))
const application = computed(() => payload.value?.application || null)
const student = computed(() => payload.value?.student || null)
const drive = computed(() => payload.value?.drive || null)
const company = computed(() => payload.value?.company || null)
const resumeHref = computed(() => {
  const hasAppliedResume = Boolean(application.value?.resume_link)
  const hasCurrentResume = Boolean(student.value?.resume_path)
  if (!hasAppliedResume && !hasCurrentResume) return ''

  const source = hasAppliedResume ? 'applied' : 'current'
  const base = String(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
  return `${base}/admin/applications/${applicationId.value}/resume/?source=${source}`
})

const formatDateTime = (value) => {
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

const formatBranches = (value) => {
  if (!Array.isArray(value) || value.length === 0) return '-'
  return value.join(', ')
}

const loadApplication = async () => {
  if (!Number.isFinite(applicationId.value) || applicationId.value <= 0) {
    toast.error('Invalid application id')
    return
  }

  loading.value = true
  try {
    const res = await getAdminApplicationDetail(applicationId.value)
    payload.value = res?.data || null
  } catch (error) {
    toast.error(error?.response?.data?.error || 'Failed to load application detail')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  navigateBack(router, { name: 'admin-applications' }, route.fullPath)
}

onMounted(async () => {
  await loadApplication()
})
</script>

<style scoped>
.application-detail-page {
  display: grid;
  gap: 14px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.interview-card {
  grid-column: 1 / -1;
}

.card {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.card h4 {
  margin: 0 0 10px;
}

.card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.card li {
  display: grid;
  grid-template-columns: 145px 1fr;
  gap: 8px;
  align-items: flex-start;
}

.card li span {
  color: #4e5f81;
  font-size: 0.9rem;
}

.card li strong {
  color: #1f2d46;
}

.wrap {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

a {
  color: #175cd3;
  text-decoration: underline;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .card li {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
