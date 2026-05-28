import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/login', { email, password }).then((r) => r.data);

export const register = (email: string, password: string, display_name?: string) =>
  api.post('/auth/register', { email, password, display_name }).then((r) => r.data);

export const getMe = () => api.get('/auth/me').then((r) => r.data);

// Frameworks
export const getFrameworks = () => api.get('/frameworks').then((r) => r.data);

export const getFramework = (id: string) => api.get(`/frameworks/${id}`).then((r) => r.data);

// Controls
export const getControls = (frameworkId?: string) =>
  api.get('/controls', { params: { framework_id: frameworkId } }).then((r) => r.data);

export const getControl = (id: string) => api.get(`/controls/${id}`).then((r) => r.data);

export const triggerCheck = (id: string) =>
  api.post(`/controls/${id}/check`).then((r) => r.data);

// Evidence
export const getEvidence = (id: string) => api.get(`/evidence/${id}`).then((r) => r.data);

export const getRawEvidence = (id: string) =>
  api.get(`/evidence/${id}/raw`).then((r) => r.data);

// Dashboard
export const getDashboardSummary = () =>
  api.get('/dashboard/summary').then((r) => r.data);

export const getDashboardHeatmap = () =>
  api.get('/dashboard/heatmap').then((r) => r.data);

// Risk
export const getRiskMatrix = () => api.get('/risk/matrix').then((r) => r.data);

export const updateRiskMatrix = (data: any) =>
  api.put('/risk/matrix', data).then((r) => r.data);

export const createRiskAssessment = (data: any) =>
  api.post('/risk/assess', data).then((r) => r.data);

// Collectors
export const getCollectors = () => api.get('/collectors').then((r) => r.data);

export const saveCollectorConfig = (type: string, config: any) =>
  api.post(`/collectors/${type}/config`, { config }).then((r) => r.data);

export default api;
