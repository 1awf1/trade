import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, TrendingDown, CheckCircle, XCircle, Eye } from 'lucide-react'
import { analysisAPI } from '../services/api'

const AnalysisHistoryPage = () => {
  const navigate = useNavigate()
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedAnalyses, setSelectedAnalyses] = useState([])
  const [comparisonResult, setComparisonResult] = useState(null)
  const [accuracyStats, setAccuracyStats] = useState(null)
  
  useEffect(() => {
    loadHistory()
  }, [])
  
  const loadHistory = async () => {
    try {
      const response = await analysisAPI.getHistory()
      setAnalyses(response.data.analyses || [])
      
      // Calculate accuracy stats
      const completed = response.data.analyses?.filter(a => a.actual_outcome) || []
      const correct = completed.filter(a => a.actual_outcome === 'correct').length
      const total = completed.length
      
      setAccuracyStats({
        total: response.data.analyses?.length || 0,
        evaluated: total,
        correct: correct,
        incorrect: total - correct,
        accuracy: total > 0 ? (correct / total) * 100 : 0,
      })
    } catch (error) {
      console.error('Geçmiş yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSelectAnalysis = (id) => {
    setSelectedAnalyses(prev => {
      if (prev.includes(id)) {
        return prev.filter(i => i !== id)
      } else if (prev.length < 3) {
        return [...prev, id]
      }
      return prev
    })
  }
  
  const handleCompare = async () => {
    if (selectedAnalyses.length < 2) {
      alert('Karşılaştırma için en az 2 analiz seçin')
      return
    }
    
    try {
      const response = await analysisAPI.compare(selectedAnalyses)
      setComparisonResult(response.data)
    } catch (error) {
      console.error('Karşılaştırma yapılamadı:', error)
    }
  }
  
  const getSignalColor = (signal) => {
    const signalLower = signal?.toLowerCase() || ''
    if (signalLower.includes('strong_buy')) return 'text-green-600'
    if (signalLower.includes('buy')) return 'text-green-500'
    if (signalLower.includes('strong_sell')) return 'text-red-600'
    if (signalLower.includes('sell')) return 'text-red-500'
    if (signalLower.includes('neutral')) return 'text-gray-500'
    return 'text-yellow-500'
  }
  
  const getSignalText = (signal) => {
    const signalLower = signal?.toLowerCase() || ''
    if (signalLower.includes('strong_buy')) return 'Güçlü Al'
    if (signalLower.includes('buy')) return 'Al'
    if (signalLower.includes('strong_sell')) return 'Güçlü Sat'
    if (signalLower.includes('sell')) return 'Sat'
    if (signalLower.includes('neutral')) return 'Nötr'
    return 'Belirsiz'
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
          Analiz Geçmişi
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Geçmiş analizlerinizi görüntüleyin ve karşılaştırın
        </p>
      </div>
      
      {/* Accuracy Stats */}
      {accuracyStats && (
        <div className="grid md:grid-cols-5 gap-4">
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Toplam Analiz</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {accuracyStats.total}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Değerlendirilen</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {accuracyStats.evaluated}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Doğru</p>
            <p className="text-2xl font-bold text-green-600">
              {accuracyStats.correct}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Yanlış</p>
            <p className="text-2xl font-bold text-red-600">
              {accuracyStats.incorrect}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Doğruluk Oranı</p>
            <p className="text-2xl font-bold text-primary-600">
              {accuracyStats.accuracy.toFixed(1)}%
            </p>
          </div>
        </div>
      )}
      
      {/* Comparison Controls */}
      {selectedAnalyses.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-gray-700 dark:text-gray-300">
              {selectedAnalyses.length} analiz seçildi
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setSelectedAnalyses([])}
                className="btn-secondary"
              >
                Seçimi Temizle
              </button>
              <button
                onClick={handleCompare}
                disabled={selectedAnalyses.length < 2}
                className="btn-primary disabled:opacity-50"
              >
                Karşılaştır
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Comparison Result */}
      {comparisonResult && (
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Karşılaştırma Sonuçları
          </h3>
          <div className="space-y-4">
            {comparisonResult.analyses?.map((analysis, index) => (
              <div key={index} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {analysis.coin} - {new Date(analysis.timestamp).toLocaleDateString('tr-TR')}
                  </h4>
                  <span className={`font-bold ${getSignalColor(analysis.signal?.signal_type)}`}>
                    {getSignalText(analysis.signal?.signal_type)}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Başarı İhtimali: {analysis.signal?.success_probability?.toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Analyses List */}
      <div className="card">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Tüm Analizler
        </h3>
        {analyses.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      className="rounded"
                      disabled
                    />
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Tarih
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Coin
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Zaman Aralığı
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Sinyal
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Başarı İhtimali
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Sonuç
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    İşlem
                  </th>
                </tr>
              </thead>
              <tbody>
                {analyses.map((analysis) => (
                  <tr
                    key={analysis.id}
                    className={`border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 ${
                      selectedAnalyses.includes(analysis.id) ? 'bg-primary-50 dark:bg-primary-900' : ''
                    }`}
                  >
                    <td className="py-3 px-4">
                      <input
                        type="checkbox"
                        checked={selectedAnalyses.includes(analysis.id)}
                        onChange={() => handleSelectAnalysis(analysis.id)}
                        className="rounded"
                      />
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(analysis.timestamp).toLocaleString('tr-TR')}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-gray-900 dark:text-white">
                      {analysis.coin}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {analysis.timeframe}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`text-sm font-medium ${getSignalColor(analysis.signal?.signal_type)}`}>
                        {getSignalText(analysis.signal?.signal_type)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                      {analysis.signal?.success_probability?.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center">
                      {analysis.actual_outcome === 'correct' && (
                        <CheckCircle className="w-5 h-5 text-green-600 mx-auto" />
                      )}
                      {analysis.actual_outcome === 'incorrect' && (
                        <XCircle className="w-5 h-5 text-red-600 mx-auto" />
                      )}
                      {!analysis.actual_outcome && (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => navigate(`/analysis/${analysis.id}`)}
                        className="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            Henüz analiz geçmişiniz bulunmuyor.
          </p>
        )}
      </div>
    </div>
  )
}

export default AnalysisHistoryPage
