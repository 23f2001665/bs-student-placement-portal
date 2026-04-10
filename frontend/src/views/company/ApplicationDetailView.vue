<template>
  <section class="application-detail-page">
    <header class="page-header">
      <h2>Application #{{ application?.id || route.params.applicationId }}</h2>
      <button class="ghost" type="button" @click="goBack">Back</button>
    </header>

    <div v-if="!application" class="card">Loading application...</div>

    <template v-else>
      <section class="detail-grid">
        <article class="card">
          <h4>Application</h4>
          <ul>
            <li><span>Status</span><strong>{{ application.status }}</strong></li>
            <li><span>Applied</span><strong>{{ formatDate(application.application_date) }}</strong></li>
            <li><span>Student ID</span><strong>{{ application.student_id }}</strong></li>
            <li><span>Drive ID</span><strong>{{ application.drive_id }}</strong></li>
            <li>
              <span>Resume</span>
              <strong>
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
            <li><span>Resume Note</span><strong>{{ application.resume_note || '-' }}</strong></li>
            <template v-if="isTerminalCurrentStatus">
              <li><span>Message</span><strong>{{ application?.interview?.details || '-' }}</strong></li>
            </template>
            <template v-else>
              <li><span>Interview Date</span><strong>{{ application?.interview?.interview_date || '-' }}</strong></li>
              <li><span>Interview Time</span><strong>{{ application?.interview?.interview_time || '-' }}</strong></li>
              <li><span>Interview Details</span><strong>{{ application?.interview?.details || '-' }}</strong></li>
            </template>
          </ul>
        </article>

        <article class="card">
          <h4>Student Public Profile</h4>
          <ul>
            <li><span>Name</span><strong>{{ student?.name || '-' }}</strong></li>
            <li><span>Roll</span><strong>{{ student?.roll || '-' }}</strong></li>
            <li><span>Branch</span><strong>{{ student?.branch || '-' }}</strong></li>
            <li><span>Current level</span><strong>{{ student?.current_level || '-' }}</strong></li>
            <li><span>CGPA</span><strong>{{ student?.cgpa ?? '-' }}</strong></li>
          </ul>
        </article>

        <article class="card">
          <h4>Drive</h4>
          <ul>
            <li><span>Title</span><strong>{{ drive?.title || '-' }}</strong></li>
            <li><span>Status</span><strong>{{ drive?.status || '-' }}</strong></li>
            <li><span>Approval</span><strong>{{ drive?.approval_status || '-' }}</strong></li>
            <li><span>Work mode</span><strong>{{ drive?.work_mode || '-' }}</strong></li>
          </ul>
          <button class="text-btn" type="button" @click="openDrive">Open Drive Detail</button>
        </article>
      </section>

      <form class="action-bar" @submit.prevent="applyStatus">
        <template v-if="!isTerminalCurrentStatus">
          <label for="status">Update status</label>
          <select id="status" v-model="nextStatus">
            <option v-for="status in allowedStatuses" :key="status" :value="status">{{ status }}</option>
          </select>
        </template>
        <template v-else>
          <label>Current status</label>
          <strong>{{ application?.status }}</strong>
        </template>
        <section id="interview-section" v-if="isShortlisted || isSelectedOrRejected" class="interview-info">
          <p v-if="isShortlisted">
            Required interview date, time, and message.
          </p>

          <template v-if="isShortlisted">
            <label for="interviewDate">Interview Date</label>
            <input
              id="interviewDate"
              v-model="interviewDate"
              type="date"
              :min="todayDate"
              aria-label="Interview date"
              required
            />

            <label for="interviewTime">Interview Time</label>
            <input
              id="interviewTime"
              v-model="interviewTime"
              type="time"
              :min="minInterviewTime"
              aria-label="Interview time"
              required
            />
          </template>

          <label for="interviewDetails">Message*</label>
          <textarea
            v-model="interviewDetails"
            id="interviewDetails"
            placeholder="Enter message"
            required
          ></textarea>
        </section>
        <button class="primary" type="submit" :disabled="saving">{{ saving ? 'Updating...' : actionLabel }}</button>
      </form>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { getApplicationDetail, updateApplicationStatus } from '@/api/company'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const payload = ref(null)
const saving = ref(false)
const nextStatus = ref('')
const interviewDate = ref('')
const interviewTime = ref('')
const interviewDetails = ref('')

const getErrorMessage = (error, fallback) => {
  const payload = error?.response?.data || {}
  return payload.error || payload.details || fallback
}

const STATUS_VALUE_TO_KEY = {
  Applied: 'applied',
  ShortListed: 'short_listed',
  Selected: 'selected',
  Rejected: 'rejected',
}

const applicationId = computed(() => Number(route.params.applicationId))
const application = computed(() => payload.value?.application || null)
const student = computed(() => payload.value?.student || null)
const drive = computed(() => payload.value?.drive || null)
const allowedStatuses = computed(() => payload.value?.actions?.allowed_status_updates || [])
const currentStatusNormalized = computed(() => normalizeStatus(application.value?.status))
const isTerminalCurrentStatus = computed(() => ['selected', 'rejected'].includes(currentStatusNormalized.value))
const isShortlisted = computed(() => String(nextStatus.value || '').toLowerCase() === 'short_listed')
const isSelectedOrRejected = computed(() => ['selected', 'rejected'].includes(String(nextStatus.value || '').toLowerCase()))
const resumeHref = computed(() => {
  if (application.value?.resume_link) return resumeUrl('applied')
  if (student.value?.resume_path) return resumeUrl('current')
  return ''
})
const actionLabel = computed(() => {
  if (isTerminalCurrentStatus.value) return 'Send Message'
  return 'Update'
})
const todayDate = computed(() => {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
})
const minInterviewTime = computed(() => {
  if (interviewDate.value !== todayDate.value) return ''
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
})

const normalizeStatus = (status) => {
  if (!status) return ''
  const raw = String(status).trim()
  const lower = raw.toLowerCase()
  if (allowedStatuses.value.includes(lower)) return lower
  return STATUS_VALUE_TO_KEY[raw] || lower
}

const resumeUrl = (source) => {
  const base = String(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
  return `${base}/company/applications/${applicationId.value}/resume/?source=${encodeURIComponent(source)}`
}

const loadApplication = async () => {
  try {
    const res = await getApplicationDetail(applicationId.value)
    payload.value = res.data
    nextStatus.value = normalizeStatus(res.data.application?.status) || allowedStatuses.value[0] || ''

    const interview = res.data.application?.interview
    interviewDate.value = interview?.interview_date || ''
    interviewTime.value = interview?.interview_time ? String(interview.interview_time).slice(0, 5) : ''
    interviewDetails.value = interview?.details || ''

    if (isTerminalCurrentStatus.value) {
      nextStatus.value = currentStatusNormalized.value
    }
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to load application detail'))
  }
}

const applyStatus = async () => {
  if (!nextStatus.value) return
  if (isShortlisted.value && (!interviewDate.value || !interviewTime.value)) {
    toast.error('Interview date and time are required for shortlisted status')
    return
  }
  if (isShortlisted.value) {
    const scheduledAt = new Date(`${interviewDate.value}T${interviewTime.value}:00`)
    if (Number.isNaN(scheduledAt.getTime()) || scheduledAt.getTime() < Date.now()) {
      toast.error('Interview date/time cannot be in the past')
      return
    }
  }
  if ((isShortlisted.value || isSelectedOrRejected.value) && !String(interviewDetails.value || '').trim()) {
    toast.error('Message is required for this status')
    return
  }

  const updatePayload = {
    status: nextStatus.value,
    interview_details: String(interviewDetails.value || '').trim() || null,
  }

  if (isShortlisted.value) {
    updatePayload.interview_date = interviewDate.value
    updatePayload.interview_time = interviewTime.value
  }

  saving.value = true
  try {
    const res = await updateApplicationStatus(applicationId.value, updatePayload)
    payload.value = {
      ...payload.value,
      application: res.data.application,
    }
    nextStatus.value = normalizeStatus(res.data.application?.status) || nextStatus.value

    const interview = res.data.application?.interview
    interviewDate.value = interview?.interview_date || interviewDate.value
    interviewTime.value = interview?.interview_time ? String(interview.interview_time).slice(0, 5) : interviewTime.value
    interviewDetails.value = isTerminalCurrentStatus.value ? '' : (interview?.details || interviewDetails.value)
    toast.success(isTerminalCurrentStatus.value ? 'Message sent to student' : 'Application status updated')
    const targetDriveId = res.data.application?.drive_id || drive.value?.id
    if (targetDriveId) {
      router.push({ name: 'company-drive-detail', params: { driveId: targetDriveId } })
    } else {
      router.push('/company/drives')
    }
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to update application status'))
  } finally {
    saving.value = false
  }
}

const openDrive = () => {
  if (!drive.value?.id) return
  router.push({ name: 'company-drive-detail', params: { driveId: drive.value.id } })
}

const openCompanyProfile = () => {
  router.push({ name: 'company-profile' })
}

const goBack = () => {
  const fallbackTarget = drive.value?.id
    ? { name: 'company-drive-detail', params: { driveId: drive.value.id } }
    : '/company/drives'
  navigateBack(router, fallbackTarget, route.fullPath)
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

onMounted(async () => {
  await loadApplication()
})
</script>

<style scoped>
.application-detail-page {
  display: grid;
  gap: 14px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.card {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

.card li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.action-bar {
  border: 1px solid #dce3f5;
  border-radius: 12px;
  background: #f7f9ff;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-bar select {
  border: 1px solid #d6dbe8;
  border-radius: 8px;
  padding: 8px 10px;
}

.interview-info {
  display: grid;
  gap: 8px;
  width: min(420px, 100%);
}

.interview-info p {
  margin: 0;
  color: #4d5f86;
  font-size: 0.88rem;
}

.interview-info label {
  font-size: 0.82rem;
  color: #3e4d6f;
  font-weight: 600;
}

.interview-info input,
.interview-info textarea {
  border: 1px solid #cfd8ea;
  border-radius: 8px;
  padding: 8px 10px;
  font: inherit;
  color: #1f2e4d;
  background: #fff;
}

.interview-info textarea {
  min-height: 92px;
  resize: vertical;
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
  margin-top: 10px;
  background: transparent;
  color: #2f66db;
  padding-left: 0;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .page-header,
  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
