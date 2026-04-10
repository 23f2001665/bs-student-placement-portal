import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

import AuthLayout from '@/layouts/AuthLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import MainLayout from '@/layouts/MainLayout.vue'
import LandingView from '@/views/auth/Landing.vue'
import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'
import ForgotPasswordView from '@/views/auth/ForgotPasswordView.vue'
import StudentDashboardView from '@/views/student/DashboardView.vue'
import StudentProfileView from '@/views/student/ProfileView.vue'
import StudentDrivesView from '@/views/student/DrivesView.vue'
import StudentDriveDetailView from '@/views/student/DriveDetailView.vue'
import StudentCompanyDetailView from '@/views/student/CompanyDetailView.vue'
import StudentApplicationsView from '@/views/student/ApplicationsView.vue'
import StudentApplicationDetailView from '@/views/student/ApplicationDetailView.vue'
import CompanyDashboardView from '@/views/company/DashboardView.vue'
import CompanyProfileView from '@/views/company/ProfileView.vue'
import CompanyDrivesView from '@/views/company/DrivesView.vue'
import CompanyCreateDriveView from '@/views/company/CreateDriveView.vue'
import CompanyEditDriveView from '@/views/company/EditDriveView.vue'
import CompanyPendingApprovalView from '@/views/company/PendingApprovalView.vue'
import CompanyDriveDetailView from '@/views/company/DriveDetailView.vue'
import CompanyApplicationDetailView from '@/views/company/ApplicationDetailView.vue'
import CompanyApplicationsView from '@/views/company/ApplicationsView.vue'
import AdminDashboardView from '@/views/admin/DashboardView.vue'
import AdminCompaniesView from '@/views/admin/CompaniesView.vue'
import AdminStudentsView from '@/views/admin/StudentsView.vue'
import AdminDrivesView from '@/views/admin/ApplicationsView.vue'
import AdminApplicationsView from '@/views/admin/AllApplicationsView.vue'
import AdminDriveDetailView from '@/views/admin/DriveDetailView.vue'
import AdminApplicationDetailView from '@/views/admin/ApplicationDetailView.vue'
import AdminCompanyDetailView from '@/views/admin/CompanyDetailView.vue'

const getHomeByRole = (role) => {
  if (role === 'admin') return '/admin'
  if (role === 'company') return '/company'
  if (role === 'student') return '/student'
  return '/'
}

const routes = [
  {
    path: '/',
    component: AuthLayout,
    meta: { guestOnly: true },
    children: [
      { path: '', name: 'landing', component: LandingView },
      { path: 'login', name: 'login', component: LoginView },
      { path: 'register', name: 'register', component: RegisterView },
      { path: 'forgot-password', name: 'forgot-password', component: ForgotPasswordView }
    ]
  },

  {
    path: '/student',
    component: MainLayout,
    meta: { requiresAuth: true, role: 'student' },
    children: [
      { path: '', name: 'student-dashboard', component: StudentDashboardView },
      { path: 'profile', name: 'student-profile', component: StudentProfileView },
      { path: 'drives', name: 'student-drives', component: StudentDrivesView },
      { path: 'drives/:driveId', name: 'student-drive-detail', component: StudentDriveDetailView },
      { path: 'companies/:companyId', name: 'student-company-detail', component: StudentCompanyDetailView },
      { path: 'applications', name: 'student-applications', component: StudentApplicationsView },
      { path: 'applications/:applicationId', name: 'student-application-detail', component: StudentApplicationDetailView }
    ]
  },

  {
    path: '/company',
    component: MainLayout,
    meta: { requiresAuth: true, role: 'company' },
    children: [
      { path: '', name: 'company-dashboard', component: CompanyDashboardView },
      { path: 'pending-approval', name: 'company-pending-approval', component: CompanyPendingApprovalView },
      { path: 'profile', name: 'company-profile', component: CompanyProfileView },
      { path: 'drives', name: 'company-drives', component: CompanyDrivesView },
      { path: 'drives/create', name: 'company-drive-create', component: CompanyCreateDriveView },
      { path: 'drives/:driveId/edit', name: 'company-drive-edit', component: CompanyEditDriveView },
      { path: 'drives/:driveId', name: 'company-drive-detail', component: CompanyDriveDetailView },
      { path: 'applications', name: 'company-applications', component: CompanyApplicationsView },
      { path: 'applications/:applicationId', name: 'company-application-detail', component: CompanyApplicationDetailView }
    ]
  },

  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', name: 'admin-dashboard', component: AdminDashboardView },
      { path: 'companies', name: 'admin-companies', component: AdminCompaniesView },
      { path: 'companies/:companyId', name: 'admin-company-detail', component: AdminCompanyDetailView },
      { path: 'students', name: 'admin-students', component: AdminStudentsView },
      { path: 'drives', name: 'admin-drives', component: AdminDrivesView },
      { path: 'drives/:driveId', name: 'admin-drive-detail', component: AdminDriveDetailView },
      { path: 'applications', name: 'admin-applications', component: AdminApplicationsView },
      { path: 'applications/:applicationId', name: 'admin-application-detail', component: AdminApplicationDetailView }
    ]
  },

  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  auth.initialize()

  const currentRole = auth.userRole

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return next(getHomeByRole(currentRole))
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }

  if (to.meta.role) {
    if (!currentRole) {
      return next('/login')
    }

    if (currentRole !== to.meta.role) {
      return next(getHomeByRole(currentRole))
    }
  }

  // Unapproved companies can only access the pending-approval page.
  if (currentRole === 'company') {
    const isApproved = auth.user?.is_approved
    const isPendingPage = to.name === 'company-pending-approval'

    if (isApproved === false && !isPendingPage) {
      return next('/company/pending-approval')
    }

    if (isApproved === true && isPendingPage) {
      return next('/company')
    }
  }

  next()
})

export default router