import api from '@/api/client'

export const getCompanyDrives = (params) => api.get('/company/drives/', { params })
export const getCompanyDriveSummaries = (params) => api.get('/company/drives/summary/', { params })
export const getCompanySummary = () => api.get('/company/summary/')
export const createCompanyDrive = (payload) => api.post('/company/drives/create/', payload)
export const updateCompanyDrive = (driveId, payload) => api.put(`/company/drives/${driveId}/update/`, payload)
export const deleteCompanyDrive = (driveId) => api.delete(`/company/drives/${driveId}/delete/`)
export const getDriveApplications = (driveId, params) => api.get(`/company/drives/${driveId}/`, { params })
export const getDriveSummary = (driveId) => api.get(`/company/drives/${driveId}/summary/`)
export const getCompanyApplications = (params) => api.get('/company/applications/', { params })
export const getApplicationDetail = (applicationId) => api.get(`/company/applications/${applicationId}/`)
export const updateApplicationStatus = (applicationId, payload) =>
	api.put(`/company/applications/${applicationId}/status/`, payload)
export const getCompanyProfile = () => api.get('/company/profile/')
export const updateCompanyProfile = (payload) => api.put('/company/profile/update/', payload)

