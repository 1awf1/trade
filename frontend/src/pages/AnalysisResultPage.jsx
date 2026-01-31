import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'
import useStore from '../store/useStore'
import { analysisAPI } from '../services/api'
import PriceChart from '../components/PriceChart'
import IndicatorsTable from '../components/IndicatorsTable'
import SignalCard from '../components/SignalCard'
import AIReport from '../components/AIReport'

const AnalysisResultPage = () => {
  const { id } = useParams()
  const { currentAnalysis, setCurrentAnalysis } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    if (!currentAnalysis || currentAnalysis.id !== id) {
      loadAnalysis()
    }
  }, [id])
  
  const loadAnalysis = async () => {
    setLoading(true)
    try {
      const response = await analysisAPI.get(id)
      setCurrentAnalysis(response.data)
    } catch (error) {
      setError('Analiz yüklenemedi')
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Analiz yükleniyor...</p>
        </div>
      </div>
    )
  }
  
  if (error || !currentAnalysis) {
    return (
      <div className="card text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600 dark:text-red-400">{error || 'Analiz bulunamadı'}</p>
      </div>
    )
  }
  
  const { coin, timeframe, signal, technical_data, fundamental_data, ai_report } = currentAnalysis
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              {coin} Analiz Sonuçları
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Zaman Aralığı: {timeframe}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {new Date(currentAnalysis.timestamp).toLocaleString('tr-TR')}
            </p>
          </div>
        </div>
      </div>
      
      {/* Signal Card */}
      <SignalCard signal={signal} />
      
      {/* Price Chart */}
      <div className="card">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Fiyat Grafiği
        </h3>
        <PriceChart coin={coin} timeframe={timeframe} />
      </div>
      
      {/* Technical Indicators */}
      <div className="card">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Teknik İndikatörler
        </h3>
        <IndicatorsTable indicators={technical_data} />
      </div>
      
      {/* Fundamental Analysis */}
      {fundamental_data && (
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Temel Analiz
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Genel Duygu</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {fundamental_data.overall_sentiment?.classification || 'N/A'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Duygu Skoru</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {fundamental_data.overall_sentiment?.overall_score?.toFixed(2) || 'N/A'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Trend</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {fundamental_data.overall_sentiment?.trend || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* AI Report */}
      {ai_report && (
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            AI Yorumu
          </h3>
          <AIReport report={ai_report} />
        </div>
      )}
    </div>
  )
}

export default AnalysisResultPage
