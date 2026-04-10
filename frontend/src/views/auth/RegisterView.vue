<template>
  <section class="register-page">
    <div class="register-card">
      <h1>Create Account</h1>

      <div class="user-type-row">
        <label>
          <input type="radio" value="student" v-model="userType" />
          Student
        </label>
        <label>
          <input type="radio" value="company" v-model="userType" />
          Company
        </label>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="grid">
          <div class="column">
            <h3>User Details</h3>

            <input v-model.trim="form.name" placeholder="Full Name" required />
            <input v-model.trim="form.email" type="email" placeholder="Email" required />

            <div class="password-field">
              <input
                :type="showPassword ? 'text' : 'password'"
                v-model="form.password"
                placeholder="Password"
                required
              />
              <button
                class="toggle-password-btn"
                type="button"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                @click="togglePassword"
              >
                {{ showPassword ? 'Hide' : 'Show' }}
              </button>
            </div>

            <input
              :type="showPassword ? 'text' : 'password'"
              v-model="form.confirmPassword"
              placeholder="Confirm Password"
              required
            />

            <button type="submit" class="submit-btn" :disabled="isSubmitting">
              {{ isSubmitting ? 'Registering...' : 'Register' }}
            </button>
          </div>

          <div class="column">
            <h3 v-if="userType === 'student'">Student Details</h3>
            <h3 v-else>Company Details</h3>

            <template v-if="userType === 'student'">

              <input v-model.trim="form.roll" placeholder="Roll Number" required />

              <select v-model="form.branch" required>
                <option value="">Select Branch</option>
                <option v-for="branch in branches" :key="branch.value" :value="branch.value">{{ branch.label }}</option>
              </select>

              <input v-model.number="form.currentLevel" type="number" min="1" placeholder="Current Level (Year)" required />

              <select v-model="form.gender">
                <option value="">Gender (Optional)</option>
                <option v-for="gender in genders" :key="gender.value" :value="gender.value">{{ gender.label }}</option>
              </select>

              <input v-model.number="form.cgpa" type="number" min="0" max="10" step="0.01" placeholder="CGPA (Optional)" />
              <label for="resume" class="file-label">Resume (PDF, max 1MB)</label>
              <input id="resume" type="file" accept="application/pdf,.pdf" @change="onResumeSelected"/>
            </template>


            <template v-else>
              <select v-model="form.industryType" required>
                <option value="">Industry Type</option>
                <option v-for="industry in industries" :key="industry.value" :value="industry.value">{{ industry.label }}</option>
              </select>
              <input v-model.trim="form.website" placeholder="Website" required />
              <textarea v-model.trim="form.description" rows="4" placeholder="Description (Optional)" />
            </template>
          </div>
        </div>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </form>

      <div class="support-actions">
        <span class="support-text">Already have an account?</span>
        <button class="text-btn" type="button" @click="goToLogin">Login</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import api from '@/api/client'

const userType = ref('student')
const showPassword = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')
const resumeFile = ref(null)
const router = useRouter()

const defaultBranches = [
  { value: 'cse', label: 'Computer Science and Engineering' },
  { value: 'ece', label: 'Electronics and Communication Engineering' },
  { value: 'me', label: 'Mechanical Engineering' },
  { value: 'ce', label: 'Civil Engineering' },
  { value: 'ee', label: 'Electrical Engineering' },
  { value: 'ds', label: 'Data Science' },
  { value: 'it', label: 'Information Technology' }
]

const defaultGenders = [
  { value: 'm', label: 'Male' },
  { value: 'f', label: 'Female' },
  { value: 'o', label: 'Other' }
]

const defaultIndustries = [
  { value: 'software', label: 'Software' },
  { value: 'finance', label: 'Finance' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail' },
  { value: 'energy', label: 'Energy' },
  { value: 'transportation', label: 'Transportation' },
  { value: 'entertainment', label: 'Entertainment' }
]

const branches = ref([...defaultBranches])
const genders = ref([...defaultGenders])
const industries = ref([...defaultIndustries])

const form = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: '',

  // student
  roll: '',
  branch: '',
  currentLevel: null,
  gender: '',
  cgpa: null,

  // company
  industryType: '',
  website: '',
  description: ''
})

const loadEnumOptions = async () => {
  try {
    const [branchesRes, industriesRes, gendersRes] = await Promise.all([
      api.get('/branches'),
      api.get('/industries'),
      api.get('/genders')
    ])

    if (Array.isArray(branchesRes?.data?.branches) && branchesRes.data.branches.length > 0) {
      branches.value = branchesRes.data.branches
    }

    if (Array.isArray(industriesRes?.data?.industries) && industriesRes.data.industries.length > 0) {
      industries.value = industriesRes.data.industries
    }

    if (Array.isArray(gendersRes?.data?.genders) && gendersRes.data.genders.length > 0) {
      genders.value = gendersRes.data.genders
    }
  } catch (err) {
    // Fall back to local defaults so form remains usable even if enum APIs fail.
    branches.value = [...defaultBranches]
    industries.value = [...defaultIndustries]
    genders.value = [...defaultGenders]
  }
}

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const onResumeSelected = (event) => {
  const file = event.target.files?.[0] || null

  if (!file) {
    resumeFile.value = null
    return
  }

  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    errorMessage.value = 'Resume must be a PDF file.'
    event.target.value = ''
    resumeFile.value = null
    return
  }

  if (file.size > 1024 * 1024) {
    errorMessage.value = 'Resume file must be 1MB or smaller.'
    event.target.value = ''
    resumeFile.value = null
    return
  }

  errorMessage.value = ''
  resumeFile.value = file
}

const buildPayload = () => {
  if (userType.value === 'student') {
    const payload = new FormData()
    payload.append('name', form.name)
    payload.append('email', form.email)
    payload.append('password', form.password)
    payload.append('roll', form.roll)
    payload.append('branch', form.branch)
    payload.append('current_level', String(form.currentLevel))

    if (form.gender) {
      payload.append('gender', form.gender)
    }

    if (form.cgpa !== null && form.cgpa !== '') {
      payload.append('cgpa', String(form.cgpa))
    }

    if (resumeFile.value) {
      payload.append('resume', resumeFile.value)
    }

    return payload
  }

  return {
    name: form.name,
    email: form.email,
    password: form.password,
    industry_type: form.industryType || null,
    website: form.website || null,
    description: form.description || null
  }
}

const handleSubmit = async () => {
  errorMessage.value = ''

  if (form.password !== form.confirmPassword) {
    errorMessage.value = 'Password and confirm password do not match.'
    return
  }

  if (userType.value === 'student' && !form.roll) {
    errorMessage.value = 'Roll number is required for student registration.'
    return
  }

  if (userType.value === 'student' && !resumeFile.value) {
    errorMessage.value = 'Resume PDF is required for student registration.'
    return
  }

  const payload = buildPayload()
  const endpoint = userType.value === 'student' ? '/auth/register/student/' : '/auth/register/company/'

  isSubmitting.value = true

  try {
    if (userType.value === 'student') {
      await api.post(endpoint, payload, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    } else {
      await api.post(endpoint, payload)
    }

    toast.success('Registration successful. Please login.')
    router.push({ name: 'login' })
  } catch (err) {
    errorMessage.value = err?.response?.data?.error || 'Registration failed. Please check your details.'
  } finally {
    isSubmitting.value = false
  }
}

const goToLogin = () => {
  router.push({ name: 'login' })
}

onMounted(() => {
  loadEnumOptions()
})

</script>

<style scoped>
.register-page {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
}

.register-card {
  width: min(820px, 96vw);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-card);
}

h1 {
  margin: 0 0 var(--space-2);
  color: var(--color-text-heading);
}

.user-type-row {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

h3 {
  margin: 0 0 var(--space-1);
  font-size: var(--font-size-md);
  color: var(--color-text-base);
}

.file-label {
  color: var(--color-text-base);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

input {
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: 10px var(--space-3);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-md);
  background: var(--color-bg-input);
  color: var(--color-text-heading);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

select,
textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 10px var(--space-3);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-md);
  background: var(--color-bg-input);
  color: var(--color-text-heading);
}

select:focus,
textarea:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

.password-field {
  width: 100%;
  position: relative;
  display: flex;
}

.password-field input {
  padding-right: 72px;
}

.toggle-password-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-link);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
}

.toggle-password-btn:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 1px;
}

.error {
  margin: var(--space-3) 0 0;
  color: var(--color-danger);
  font-size: var(--font-size-sm);
}

.submit-btn {
  margin-top: 10px;
  width: min(260px, 100%);
  align-self: center;
  height: 48px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  font-size: var(--font-size-md);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.18s ease;
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.support-actions {
  margin-top: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

.support-text {
  color: var(--color-text-support);
  font-size: var(--font-size-sm);
}

.text-btn {
  border: none;
  padding: 0;
  background: transparent;
  color: var(--color-text-link);
  font-size: var(--font-size-base);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.text-btn:hover {
  color: var(--color-primary-hover);
}

@media (max-width: 760px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>