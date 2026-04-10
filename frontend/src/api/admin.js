import client from './client'

export const getAdminDashboard = () => client.get('/admin/dashboard/')
export const getAdminStudents = (params) => client.get('/admin/students/', { params })
export const blockStudent = (studentId) => client.put(`/admin/students/${studentId}/block/`)
export const unblockStudent = (studentId) => client.put(`/admin/students/${studentId}/unblock/`)

export const getAdminCompanies = (params) => client.get('/admin/companies/', { params })
export const approveCompany = (companyId) => client.put(`/admin/companies/${companyId}/approve/`)
export const rejectCompany = (companyId) => client.put(`/admin/companies/${companyId}/reject/`)
export const blockCompany = (companyId) => client.put(`/admin/companies/${companyId}/block/`)
export const unblockCompany = (companyId) => client.put(`/admin/companies/${companyId}/unblock/`)

export const getAdminDrives = (params) => client.get('/admin/drives/', { params })
export const getAdminDriveDetail = (driveId) => client.get(`/admin/drives/${driveId}/`)
export const approveDrive = (driveId) => client.put(`/admin/drives/${driveId}/approve/`)
export const rejectDrive = (driveId) => client.put(`/admin/drives/${driveId}/reject/`)
export const blockDrive = (driveId) => client.put(`/admin/drives/${driveId}/block/`)
export const unblockDrive = (driveId) => client.put(`/admin/drives/${driveId}/unblock/`)

export const getAdminApplications = (params) => client.get('/admin/applications/', { params })
export const getAdminApplicationDetail = (applicationId) => client.get(`/admin/applications/${applicationId}/`)

