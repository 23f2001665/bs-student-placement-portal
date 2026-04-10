import api from '@/api/client'

export const login = (payload) => api.post('/auth/login/', payload)
export const register = (payload) => api.post('/auth/register/', payload)
export const sendOtp = (payload) => api.post('/auth/send-otp/', payload)
export const resetPassword = (payload) => api.post('/auth/reset-password/', payload)
export const logout = () => api.post('/auth/logout/')