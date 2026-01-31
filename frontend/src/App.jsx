import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import AnalysisResultPage from './pages/AnalysisResultPage'
import PortfolioPage from './pages/PortfolioPage'
import AlarmsPage from './pages/AlarmsPage'
import BacktestingPage from './pages/BacktestingPage'
import AnalysisHistoryPage from './pages/AnalysisHistoryPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="analysis/:id" element={<AnalysisResultPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="alarms" element={<AlarmsPage />} />
        <Route path="backtesting" element={<BacktestingPage />} />
        <Route path="history" element={<AnalysisHistoryPage />} />
      </Route>
    </Routes>
  )
}

export default App
