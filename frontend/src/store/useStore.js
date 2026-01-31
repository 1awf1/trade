import { create } from 'zustand'

const useStore = create((set) => ({
  // Analysis state
  currentAnalysis: null,
  analysisHistory: [],
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  setAnalysisHistory: (history) => set({ analysisHistory: history }),
  
  // Portfolio state
  portfolio: null,
  setPortfolio: (portfolio) => set({ portfolio: portfolio }),
  
  // Alarms state
  alarms: [],
  setAlarms: (alarms) => set({ alarms: alarms }),
  
  // Backtesting state
  backtests: [],
  setBacktests: (backtests) => set({ backtests: backtests }),
  
  // UI state
  loading: false,
  error: null,
  setLoading: (loading) => set({ loading: loading }),
  setError: (error) => set({ error: error }),
  
  // Selected coin and timeframe
  selectedCoin: null,
  selectedTimeframe: '1h',
  setSelectedCoin: (coin) => set({ selectedCoin: coin }),
  setSelectedTimeframe: (timeframe) => set({ selectedTimeframe: timeframe }),
}))

export default useStore
