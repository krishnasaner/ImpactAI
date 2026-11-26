import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'X-CSRF-Token';

const getCsrfToken = () => {
  if (typeof document === 'undefined') {
    return null;
  }

  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${CSRF_COOKIE_NAME}=`));

  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : null;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers = config.headers || {};
      config.headers[CSRF_HEADER_NAME] = csrfToken;
    }
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: () => void; reject: (error: unknown) => void }> = [];

const processQueue = (error: unknown = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve();
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const isAuthRoute =
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/signup') ||
        originalRequest.url?.includes('/auth/refresh') ||
        originalRequest.url?.includes('/auth/logout');

      if (isAuthRoute) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise<void>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => api(originalRequest))
          .catch((refreshError) => Promise.reject(refreshError));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await api.post('/auth/refresh', {});
        isRefreshing = false;
        processQueue();
        return api(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        processQueue(refreshError);
        window.dispatchEvent(new CustomEvent('auth-logout'));
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ── Strongly-Typed Backend Feature Services ──────────────────────────────────

export const userService = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data: any) => api.put('/users/profile', data),
  getPreferences: () => api.get('/users/preferences'),
  updatePreferences: (data: any) => api.put('/users/preferences', data),
  exportData: () => api.get('/users/export'),
  deleteAccount: () => api.delete('/users/account'),
};

export const journalService = {
  list: (limit = 20, offset = 0, tag?: string) =>
    api.get('/journal', { params: { limit, offset, tag } }),
  get: (id: number) => api.get(`/journal/${id}`),
  create: (data: { title: string; content: string; mood_score?: number; tags?: string[]; is_pinned?: boolean }) =>
    api.post('/journal', data),
  update: (id: number, data: any) => api.put(`/journal/${id}`, data),
  delete: (id: number) => api.delete(`/journal/${id}`),
  search: (q: string) => api.get('/journal/search', { params: { q } }),
};

export const wellnessService = {
  getPlans: (status?: string) => api.get('/wellness/plans', { params: { status } }),
  getPlan: (id: number) => api.get(`/wellness/plans/${id}`),
  createPlan: (data: any) => api.post('/wellness/plans', data),
  updatePlan: (id: number, data: any) => api.put(`/wellness/plans/${id}`, data),
  deletePlan: (id: number) => api.delete(`/wellness/plans/${id}`),
  addActivity: (planId: number, data: any) => api.post(`/wellness/plans/${planId}/activities`, data),
  updateProgress: (actId: number, data: { progress?: number; completed?: boolean }) =>
    api.patch(`/wellness/activities/${actId}/progress`, data),
  generatePlan: (category = 'wellness') => api.post('/wellness/generate-plan', { category }),
};

export const resourceService = {
  list: (params?: { category?: string; content_type?: string; search?: string; limit?: number }) =>
    api.get('/resources', { params }),
  get: (id: number) => api.get(`/resources/${id}`),
  getCategories: () => api.get('/resources/categories'),
  getBookmarks: () => api.get('/resources/bookmarks'),
  toggleBookmark: (id: number) => api.post(`/resources/${id}/bookmark`),
};

export const appointmentService = {
  getCounsellors: () => api.get('/counsellors'),
  getAvailability: (id: number) => api.get(`/counsellors/${id}/availability`),
  getAppointments: () => api.get('/appointments'),
  bookAppointment: (data: { counsellor_id: number; appointment_date: string; duration_minutes?: number; meeting_type?: string; notes?: string }) =>
    api.post('/appointments', data),
  updateAppointment: (id: number, data: { status?: string; counsellor_notes?: string }) =>
    api.patch(`/appointments/${id}`, data),
  cancelAppointment: (id: number) => api.delete(`/appointments/${id}`),
};

export const notificationService = {
  list: (limit = 20) => api.get('/notifications', { params: { limit } }),
  markRead: (id: number) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/mark-all-read'),
};

export const adminService = {
  getDashboard: () => api.get('/admin/dashboard'),
  getUsers: (params?: { role?: string; limit?: number; offset?: number }) =>
    api.get('/admin/users', { params }),
  getSystemHealth: () => api.get('/admin/system-health'),
  getAuditLogs: (limit = 50, offset = 0) =>
    api.get('/admin/audit-logs', { params: { limit, offset } }),
};

export const chatService = {
  sendMessage: (message: string, sessionId?: string) =>
    api.post('/chat', { message, session_id: sessionId }, { timeout: 45000 }),
  getSessions: () => api.get('/chat/sessions'),
  getSessionMessages: (sessionId: string, limit = 50, offset = 0) =>
    api.get(`/chat/sessions/${sessionId}/messages`, { params: { limit, offset } }),
  renameSession: (sessionId: string, title: string) =>
    api.patch(`/chat/sessions/${sessionId}`, { title }),
  deleteSession: (sessionId: string) =>
    api.delete(`/chat/session/${sessionId}`),
  submitFeedback: (messageId: number, rating: 1 | -1, comment?: string) =>
    api.post(`/chat/messages/${messageId}/feedback`, { rating, comment }),
  regenerateMessage: (messageId: number) =>
    api.post(`/chat/messages/${messageId}/regenerate`),
};

