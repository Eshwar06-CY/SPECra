import axios from 'axios';

const getEnvBaseUrl = (): string => {
  try {
    if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
      return import.meta.env.VITE_API_BASE_URL;
    }
  } catch {
    // Fallback if import.meta is not evaluated
  }
  const globalProc = (globalThis as any).process;
  if (globalProc?.env?.VITE_API_BASE_URL) {
    return globalProc.env.VITE_API_BASE_URL;
  }
  return 'http://127.0.0.1:8001';
};

const rawBaseUrl = getEnvBaseUrl();
const baseURL = rawBaseUrl ? `${rawBaseUrl}/api/v1` : '/api/v1';

export const apiClient = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Authorization Bearer header from localStorage session token if present
apiClient.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('specra_auth_token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {}
  return config;
});

// Generic error normalizer for enterprise user feedback
export const formatErrorMessage = (error: any): string => {
  if (error?.response?.status === 503 || error?.error_type === 'provider_unavailable' || error?.message?.includes('503') || error?.message?.includes('UNAVAILABLE')) {
    return 'Gemini is temporarily unavailable. Please retry.';
  }
  if (error?.response?.status === 429 || error?.error_type === 'rate_limited' || error?.message?.includes('429') || error?.message?.includes('RESOURCE_EXHAUSTED')) {
    return 'Gemini quota/rate limit reached. Please retry later.';
  }
  if (error?.code === 'ECONNABORTED' || error?.error_type === 'timeout' || error?.message?.includes('timeout') || error?.message?.includes('timed out')) {
    return 'AI processing timed out. Please retry.';
  }
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object' && detail.error) return detail.error;
    return JSON.stringify(detail);
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred. Please try again.';
};
