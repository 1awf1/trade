import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, TrendingUp } from 'lucide-react'
import useStore from '../store/useStore'
import { coinsAPI, analysisAPI } from '../services/api'

const TIMEFRAMES = [
  { value: '15m', label: '15 Dakika' },
  { value: '1h', label: '1 Saat' },
  { value: '4h', label: '4 Saat' },
  { value: '8h', label: '8 Saat' },
  { value: '12h', label: '12 Saat' },
  { value: '24h', label: '24 Saat' },
  { value: '1w', label: '1 Hafta' },
  { value: '15d', label: '15 Gün' },
  { value: '1M', label: '1 Ay' },
]

const HomePage = () => {
  const navigate = useNavigate()
  const { setLoading, setError, setCurrentAnalysis } = useStore()
  
  const [coins, setCoins] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCoin, setSelectedCoin] = useState('')
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  
  useEffect(() => {
    loadCoins()
  }, [])
  
  const loadCoins = async () => {
    try {
      const response = await coinsAPI.list()
      setCoins(response.data.coins || [])
    } catch (error) {
      console.error('Coinler yüklenemedi:', error)
      setError('Coinler yüklenemedi')
    }
  }
  
  const filteredCoins = coins.filter(coin =>
    coin.toLowerCase().includes(searchTerm.toLowerCase())
  )
  
  const handleStartAnalysis = async () => {
    if (!selectedCoin) {
      setError('Lütfen bir coin seçin')
      return
    }
    
    setIsAnalyzing(true)
    setLoading(true)
    setError(null)
    
    try {
      const response = await analysisAPI.start(selectedCoin, selectedTimeframe)
      const analysisId = response.data.analysis_id
      
      // Poll for results
      const checkAnalysis = async () => {
        try {
          const result = await analysisAPI.get(analysisId)
          if (result.data.status === 'completed') {
            setCurrentAnalysis(result.data)
            navigate(`/analysis/${analysisId}`)
          } else if (result.data.status === 'failed') {
            setError('Analiz başarısız oldu')
            setIsAnalyzing(false)
            setLoading(false)
          } else {
            setTimeout(checkAnalysis, 2000)
          }
        } catch (error) {
          setError('Analiz sonucu alınamadı')
          setIsAnalyzing(false)
          setLoading(false)
        }
      }
      
      checkAnalysis()
    } catch (error) {
      setError(error.response?.data?.detail || 'Analiz başlatılamadı')
      setIsAnalyzing(false)
      setLoading(false)
    }
  }
  
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Kripto Para Analiz Sistemi
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Teknik ve temel analiz ile yapay zeka destekli al/sat sinyalleri
        </p>
      </div>
      
      {/* Analysis Form */}
      <div className="card max-w-2xl mx-auto">
        <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
          Yeni Analiz Başlat
        </h3>
        
        <div className="space-y-6">
          {/* Coin Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Kripto Para Seçin
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Coin ara (örn: BTC, ETH)"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
            
            {searchTerm && (
              <div className="mt-2 max-h-48 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg">
                {filteredCoins.length > 0 ? (
                  filteredCoins.map((coin) => (
                    <button
                      key={coin}
                      onClick={() => {
                        setSelectedCoin(coin)
                        setSearchTerm('')
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <span className="font-medium text-gray-900 dark:text-white">
                        {coin}
                      </span>
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-2 text-gray-500 dark:text-gray-400">
                    Coin bulunamadı
                  </div>
                )}
              </div>
            )}
            
            {selectedCoin && (
              <div className="mt-2 inline-flex items-center px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded-full">
                <TrendingUp className="w-4 h-4 mr-2" />
                <span className="font-medium">{selectedCoin}</span>
                <button
                  onClick={() => setSelectedCoin('')}
                  className="ml-2 text-primary-600 hover:text-primary-800"
                >
                  ×
                </button>
              </div>
            )}
          </div>
          
          {/* Timeframe Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Zaman Aralığı
            </label>
            <div className="grid grid-cols-3 gap-2">
              {TIMEFRAMES.map((tf) => (
                <button
                  key={tf.value}
                  onClick={() => setSelectedTimeframe(tf.value)}
                  className={`py-2 px-4 rounded-lg border-2 transition-colors ${
                    selectedTimeframe === tf.value
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-200'
                      : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Start Button */}
          <button
            onClick={handleStartAnalysis}
            disabled={!selectedCoin || isAnalyzing}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? 'Analiz Yapılıyor...' : 'Analizi Başlat'}
          </button>
        </div>
      </div>
      
      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-6 h-6 text-primary-600" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Teknik Analiz
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            RSI, MACD, Bollinger Bands ve daha fazlası
          </p>
        </div>
        
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-6 h-6 text-primary-600" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Temel Analiz
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            Sosyal medya ve haber duygu analizi
          </p>
        </div>
        
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-6 h-6 text-primary-600" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            AI Yorumlama
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            Yapay zeka destekli anlaşılır açıklamalar
          </p>
        </div>
      </div>
    </div>
  )
}

export default HomePage
