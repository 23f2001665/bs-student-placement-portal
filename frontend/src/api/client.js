import axios from "axios";
import router from "../router";
import { toast } from "vue3-toastify";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  if (config?.data instanceof FormData) {
    if (config.headers) {
      delete config.headers["Content-Type"];
      delete config.headers["content-type"];
    }
  }
  return config;
});

// Global error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (!err.response) {
      toast.error("Network error");
      return Promise.reject(err);
    }

    const status = err.response.status;
    const payload = err.response?.data || {};
    const errorCandidates = [payload.error, payload.details, payload.message];
    const errorMessage =
      errorCandidates.find((item) => typeof item === "string" && item.trim())?.trim() || null;

    if (status === 401) {
      const skipAuthHandling = Boolean(err.config?.skipAuthHandling)
      if (skipAuthHandling) {
        return Promise.reject(err)
      }

      const requestUrl = String(err.config?.url || '')
      const isLoginRequest = requestUrl.includes('/auth/login/')
      const hadAuthState = Boolean(localStorage.getItem('ppa_auth_user'))

      if (isLoginRequest) {
        return Promise.reject(err);
      }

      if (hadAuthState) {
        localStorage.removeItem('ppa_auth_user')
        window.dispatchEvent(new Event('ppa:force-logout'))
      }

      toast.error(errorMessage || (hadAuthState ? 'Session expired' : 'Authentication required'))

      if (hadAuthState || errorMessage === 'Authentication required') {
        router.push('/login')
      }
    } 
    else if (status === 403) {
      toast.warning(errorMessage || "Not allowed");
    } 
    else if (status >= 500) {
      toast.error(errorMessage || "Server error");
    }

    return Promise.reject(err);
  }
);

export default api;