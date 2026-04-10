<template>
  <section class="drive-detail-page">
    <header class="head">
      <div>
        <h2>{{ drive?.title || 'Drive Detail' }}</h2>
        <p>
          <router-link
            v-if="drive?.company?.id"
            class="company-link"
            :to="{ name: 'student-company-detail', params: { companyId: drive.company.id } }"
          >
            {{ drive?.company?.name || '-' }}
          </router-link>
          <span v-else>{{ drive?.company?.name || '-' }}</span>
        </p>
      </div>
      <button class="ghost" type="button" @click="goBack">Back to Drives</button>
    </header>

    <div v-if="loading" class="box">Loading drive detail...</div>
    <p v-else-if="!drive">The drive is either cancelled or removed.</p>

    <div v-else class="content">
      <article class="panel">
        <h3>Overview</h3>
        <ul>
          <li><span>Status</span><strong>{{ formatDriveStatus(drive.drive_status || drive.status) }}</strong></li>
          <li><span>Approval</span><strong>{{ drive.approval_status || '-' }}</strong></li>
          <li><span>Work Mode</span><strong>{{ drive.work_mode || '-' }}</strong></li>
          <li><span>Min CGPA</span><strong>{{ drive.min_cgpa ?? '-' }}</strong></li>
          <li><span>Start</span><strong>{{ formatDate(drive.start_date) }}</strong></li>
          <li><span>End</span><strong>{{ formatDate(drive.end_date) }}</strong></li>
        </ul>
      </article>

      <article class="panel">
        <h3>Description</h3>
        <p class="description-text">{{ drive.description || 'No description' }}</p>
      </article>

      <article class="panel">
        <h3>Eligibility</h3>
        <p><strong>Eligible branches:</strong> {{ eligibleBranchesLabel }}</p>
        <div v-if="hasApplied" class="applied">
          <p>You have already applied to this drive.</p>
          <p v-if="applicationStatusLabel">Application status: {{ applicationStatusLabel }}</p>
        </div>
        <p v-else-if="!isDriveOpenForApply" class="upcoming">Applications are not open for this drive yet.</p>
        <p v-else-if="isEligible" class="ok">You are eligible to apply for this drive.</p>
        <ul v-else class="reasons">
          <li v-for="reason in reasons" :key="reason">{{ reason }}</li>
        </ul>
        <div v-if="!hasApplied" class="resume-note">
          <label for="resume_note">Resume note (optional)</label>
          <textarea
            id="resume_note"
            v-model="resumeNote"
            rows="4"
            maxlength="1000"
            placeholder="Add a short note about your resume, projects, or relevant experience."
          />
        </div>
        <button
          v-if="!hasApplied"
          class="primary"
          type="button"
          :disabled="!isEligible || !isDriveOpenForApply || applying"
          @click="applyNow"
        >
          {{
            !isDriveOpenForApply
              ? 'Not Open'
              : isEligible
                ? (applying ? 'Applying...' : 'Apply Now')
                : 'Not Eligible'
          }}
        </button>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { applyToDrive, getStudentDrive } from '@/api/student'
import { navigateBack } from '@/utils/navigation'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const applying = ref(false)
const drive = ref(null)
const resumeNote = ref('')

const isEligible = computed(() => Boolean(drive.value?.eligible_for_apply))
const reasons = computed(() => drive.value?.eligibility_reasons || [])
const eligibleBranchesLabel = computed(() => {
  const branches = Array.isArray(drive.value?.allowed_branches) ? drive.value.allowed_branches : []
  if (!branches.length) return 'All branches'
  return branches.join(', ')
})
const hasApplied = computed(() => Boolean(drive.value?.already_applied))
const applicationStatusLabel = computed(() => {
  const s = String(drive.value?.application_status || '').toLowerCase().trim()
  if (!s) return ''
  if (s === 'shortlisted' || s === 'short_listed') return 'shortlisted'
  return s
})
const isDriveOpenForApply = computed(() => {
  const status = String(drive.value?.drive_status || drive.value?.status || '').toLowerCase().trim()
  return status === 'active'
})

const getErrorMessage = (error, fallback) => {
  const payload = error?.response?.data || {}
  return payload.error || payload.details || fallback
}

const formatDriveStatus = (status) => {
  const s = String(status || '').toLowerCase().trim()
  if (!s) return '-'
  return s
}

const loadDrive = async () => {
  loading.value = true
  try {
    const res = await getStudentDrive(route.params.driveId)
    drive.value = res?.data?.drive || null
  } catch (error) {
    if (error.response?.status === 404) {
      toast.error('This drive is either cancelled or removed')
    } else {
      toast.error(getErrorMessage(error, 'Failed to load drive detail'))
    }
    drive.value = null
  } finally {
    loading.value = false
  }
}

const applyNow = async () => {
  if (!drive.value?.id || !isEligible.value || applying.value) return
  if (!isDriveOpenForApply.value) {
    toast.error('Drive is not accepting applications right now')
    return
  }
  applying.value = true
  try {
    await applyToDrive(drive.value.id, { resume_note: resumeNote.value })
    toast.success('Application submitted successfully')
    router.push('/student/applications')
  } catch (error) {
    toast.error(getErrorMessage(error, 'Failed to apply to drive'))
  } finally {
    applying.value = false
  }
}

const goBack = () => {
  navigateBack(router, '/student/drives', route.fullPath)
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

onMounted(async () => {
  await loadDrive()
})
</script>

<style scoped>
.drive-detail-page {
  display: grid;
  gap: 12px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.head h2 {
  margin: 0;
}

.head p {
  margin: 4px 0 0;
  color: #607094;
}

.company-link {
  color: #155eef;
  text-decoration: none;
  font-weight: 600;
}

.company-link:hover {
  text-decoration: underline;
}

.box,
.panel {
  border: 1px solid #e2e6f1;
  border-radius: 12px;
  background: #fff;
  padding: 12px;
}

.content {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.panel h3 {
  margin: 0 0 8px;
}

.panel {
  min-width: 0;
}

.panel ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

.panel li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.panel p {
  margin: 0;
  color: #44516a;
}

.description-text {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.ok {
  color: #067647;
  font-weight: 600;
}

.applied {
  color: #155eef;
  background: #e8f1ff;
  border: 1px solid #bfd4ff;
  border-radius: 8px;
  padding: 8px 10px;
  font-weight: 600;
}

.upcoming {
  color: #9a5d00;
  background: #fff0d8;
  border: 1px solid #f8d8a6;
  border-radius: 8px;
  padding: 8px 10px;
  font-weight: 600;
}

.reasons {
  list-style: disc;
  margin: 0 0 10px 16px;
  padding: 0;
}

.reasons li {
  display: list-item;
  color: #6e4b00;
}

.resume-note {
  display: grid;
  gap: 6px;
  margin: 10px 0;
}

.resume-note label {
  font-size: 13px;
  color: #44516a;
}

.resume-note textarea {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  display: block;
  border: 1px solid #cfd8ea;
  border-radius: 8px;
  padding: 10px;
  font: inherit;
  resize: vertical;
}

.primary,
.ghost {
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

.primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.ghost {
  background: #edf2ff;
  color: #2f66db;
}

@media (max-width: 980px) {
  .content {
    grid-template-columns: 1fr;
  }

  .head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
