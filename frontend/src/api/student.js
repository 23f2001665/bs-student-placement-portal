import client from './client'

export const getStudentProfile = () => client.get('/student/profile/')
export const updateStudentProfile = (payload) => client.put('/student/profile/update/', payload)

export const getStudentDrives = (params = {}) => client.get('/student/drives/', { params })
export const getStudentDrive = (driveId) => client.get(`/student/drives/${driveId}/`)
export const getStudentCompanyDetail = (companyId) => client.get(`/student/companies/${companyId}/`)
export const applyToDrive = (driveId, payload = {}) => client.post(`/student/drives/${driveId}/apply/`, payload)

export const getStudentApplications = (params = {}) => client.get('/student/applications/', { params })
export const getStudentApplicationDetail = (applicationId) => client.get(`/student/applications/${applicationId}/`)
export const startStudentApplicationsExport = () => client.post('/student/applications/export/')
export const getStudentApplicationsExportStatus = (taskId) =>
	client.get(`/student/applications/export/${taskId}/status`)

const parseDownloadFilename = (contentDisposition, fallbackName) => {
	if (!contentDisposition) return fallbackName

	const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
	if (utf8Match?.[1]) {
		return decodeURIComponent(utf8Match[1])
	}

	const asciiMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
	if (asciiMatch?.[1]) {
		return asciiMatch[1]
	}

	return fallbackName
}

export const downloadStudentApplicationsExport = async (taskId) => {
	const response = await client.get(
		`/student/applications/export/${taskId}/download`,
		{ responseType: 'blob' }
	)

	const contentType = String(response?.headers?.['content-type'] || '').toLowerCase()
	if (contentType.includes('application/json')) {
		const bodyText = await response.data.text()
		let payload = {}
		try {
			payload = JSON.parse(bodyText)
		} catch {
			payload = {}
		}
		throw new Error(payload.error || payload.details || 'Export download failed')
	}

	const fallbackName = `applications_${taskId}.csv`
	const filename = parseDownloadFilename(response?.headers?.['content-disposition'], fallbackName)
	const blob = response.data instanceof Blob ? response.data : new Blob([response.data], { type: 'text/csv' })
	const objectUrl = window.URL.createObjectURL(blob)

	const link = document.createElement('a')
	link.href = objectUrl
	link.download = filename
	link.style.display = 'none'
	document.body.appendChild(link)
	link.click()
	link.remove()

	window.URL.revokeObjectURL(objectUrl)
}

