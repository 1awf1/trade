import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Analysis endpoints
export const analysisAPI = {
  start: (coin, timeframe) => api.post('/analysis/start', { coin, timeframe }),
  get: (id) => api.get(`/analysis/${id}`),
  getHistory: () => api.get('/analysis/history'),
  compare: (ids) => api.post('/analysis/compare', { analysis_ids: ids }),
}

// Portfolio endpoints
export const portfolioAPI = {
  get: () => api.get('/portfolio'),
  add: (data) => api.post('/portfolio/add', data),
  remove: (coinId) => api.delete(`/portfolio/${coinId}`),
  getPerformance: () => api.get('/portfolio/performance'),
}

// Alarms endpoints
export const alarmsAPI = {
  list: () => api.get('/alarms'),
  create: (data) => api.post('/alarms', data),
  update: (id, data) => api.put(`/alarms/${id}`, data),
  delete: (id) => api.delete(`/alarms/${id}`),
}

// Backtesting endpoints
export const backtestingAPI = {
  start: (data) => api.post('/backtest/start', data),
  get: (id) => api.get(`/backtest/${id}`),
  compare: (ids) => api.post('/backtest/compare', { backtest_ids: ids }),
}

// Coins endpoints
export const coinsAPI = {
  list: () => api.get('/coins'),
  getPrice: (symbol) => api.get(`/coins/${symbol}/price`),
}

export default api
