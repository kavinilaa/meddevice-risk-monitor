import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
        window.location.href = '/login?expired=1';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  signup: (userData) => api.post('/api/auth/signup', userData),
  logout: () => api.post('/api/auth/logout'),
};

export const userApi = {
  getProfile: () => api.get('/api/users/me'),
  updateProfile: (data) => api.put('/api/users/me', data),
  changePassword: (data) => api.put('/api/users/me/password', data),
};

export const metadataApi = {
  getOptions: () => api.get('/api/metadata/options'),
  getEventTypes: () => api.get('/api/metadata/event-types'),
  getStatuses: () => api.get('/api/metadata/statuses'),
  getClassifications: () => api.get('/api/metadata/classifications'),
  getRiskClasses: () => api.get('/api/metadata/risk-classes'),
  getImplantStatuses: () => api.get('/api/metadata/implant-statuses'),
  getCountries: () => api.get('/api/metadata/countries'),
  searchManufacturers: (search, page = 1, limit = 20) =>
    api.get('/api/metadata/manufacturers', { params: { search, page, limit } }),
  getHistoricalCounts: (params) => api.get('/api/metadata/historical-counts', { params }),
  getDatasetStats: () => api.get('/api/metadata/dataset-stats'),
};

export const predictionApi = {
  create: (data) => api.post('/api/predictions', data),
  getAll: (params) => api.get('/api/predictions', { params }),
  getById: (id) => api.get(`/api/predictions/${id}`),
};

export const adminApi = {
  getDashboardStats: () => api.get('/api/admin/dashboard'),
  getUsers: (params) => api.get('/api/admin/users', { params }),
  updateUserStatus: (userId, isActive) => api.put(`/api/admin/users/${userId}/status`, { is_active: isActive }),
  getPredictions: (params) => api.get('/api/admin/predictions', { params }),
  getLogs: (params) => api.get('/api/admin/logs', { params }),
};

export default api;
