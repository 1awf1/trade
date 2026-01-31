import { useState, useEffect } from 'react'
import { Play, TrendingUp, TrendingDown } from 'lucide-react'
import { backtestingAPI } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const TIMEFRAMES = [
  { value: '15m', label: '15 Dakika' },
  { value: '1h', label: '1 Saat' },
  { value: '4h', label: '4 Saat' },
  { value: '1d', label: '1 Gün' },
]

const BacktestingPage = () => {
  const [backtests, setBacktests] = useState([])
  const [currentBacktest, setCurrentBacktest] = useState(null)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    coin: '',
    timeframe: '1h',
    start_date: '',
    end_date: '',
    initial_capital: 10000,
  })
  
  useEffect(() => {
    // Set default dates (1 year ago to today)
    const endDate = new Date()
    const startDate = new Date()
    startDate.setFullYear(startDate.getFullYear() - 1)
    
    setFormData(prev => ({
      ...prev,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
    }))
  }, [])
  
  const handleStartBacktest = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await backtestingAPI.start(formData)
      const backtestId = response.data.backtest_id
      
      // Poll for results
      const checkBacktest = async () => {
        try {
          const result = await backtestingAPI.get(backtestId)
          if (result.data.status === 'completed') {
            setCurrentBacktest(result.data)
            setBacktests(prev => [result.data, ...prev])
            setLoading(false)
          } else if (result.data.status === 'failed') {
            alert('Backtesting başarısız oldu')
            setLoading(false)
          } else {
            setTimeout(checkBacktest, 2000)
          }
        } catch (error) {
          console.error('Backtest sonucu alınamadı:', error)
          setLoading(false)
        }
      }
      
      checkBacktest()
    } catch (error) {
      console.error('Backtest başlatılamadı:', error)
      setLoading(false)
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
          Backtesting
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Stratejinizi geçmiş veriler üzerinde test edin
        </p>
      </div>
      
      {/* Backtest Form */}
      <div className="card">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Yeni Backtest Başlat
        </h3>
        <form onSubmit={handleStartBacktest} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Coin
              </label>
              <input
                type="text"
                value={formData.coin}
                onChange={(e) => setFormData({ ...formData, coin: e.target.value })}
                className="input"
                placeholder="BTC"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Zaman Aralığı
              </label>
              <select
                value={formData.timeframe}
                onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
                className="input"
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf.value} value={tf.value}>
                    {tf.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Başlangıç Tarihi
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="input"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Bitiş Tarihi
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="input"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Başlangıç Sermayesi ($)
              </label>
              <input
                type="number"
                value={formData.initial_capital}
                onChange={(e) => setFormData({ ...formData, initial_capital: parseFloat(e.target.value) })}
                className="input"
                required
              />
            </div>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50"
          >
            <Play className="w-5 h-5" />
            <span>{loading ? 'Backtest Çalışıyor...' : 'Backtest Başlat'}</span>
          </button>
        </form>
      </div>
      
      {/* Current Backtest Results */}
      {currentBacktest && (
        <div className="space-y-6">
          {/* Metrics Summary */}
          <div className="grid md:grid-cols-4 gap-4">
            <div className="card">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Toplam Kar/Zarar</p>
              <p className={`text-2xl font-bold ${
                (currentBacktest.metrics?.total_profit_loss || 0) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}>
                ${currentBacktest.metrics?.total_profit_loss?.toFixed(2) || '0.00'}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Başarı Oranı</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {(currentBacktest.metrics?.win_rate * 100)?.toFixed(1) || '0.0'}%
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Toplam İşlem</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {currentBacktest.metrics?.total_trades || 0}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Max Düşüş</p>
              <p className="text-2xl font-bold text-red-600">
                {currentBacktest.metrics?.max_drawdown_percent?.toFixed(2) || '0.00'}%
              </p>
            </div>
          </div>
          
          {/* Equity Curve */}
          {currentBacktest.equity_curve && currentBacktest.equity_curve.length > 0 && (
            <div className="card">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Equity Curve
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={currentBacktest.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          
          {/* Detailed Metrics */}
          <div className="card">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Detaylı Metrikler
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Kazanan İşlemler</span>
                  <TrendingUp className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-2xl font-bold text-green-600">
                  {currentBacktest.metrics?.winning_trades || 0}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Kaybeden İşlemler</span>
                  <TrendingDown className="w-5 h-5 text-red-600" />
                </div>
                <p className="text-2xl font-bold text-red-600">
                  {currentBacktest.metrics?.losing_trades || 0}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {currentBacktest.metrics?.sharpe_ratio?.toFixed(2) || 'N/A'}
                </p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Profit Factor</span>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {currentBacktest.metrics?.profit_factor?.toFixed(2) || 'N/A'}
                </p>
              </div>
            </div>
          </div>
          
          {/* Trades List */}
          {currentBacktest.trades && currentBacktest.trades.length > 0 && (
            <div className="card">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                İşlem Geçmişi
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Giriş Tarihi
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Giriş Fiyatı
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Çıkış Tarihi
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Çıkış Fiyatı
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Kar/Zarar
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentBacktest.trades.slice(0, 10).map((trade, index) => (
                      <tr
                        key={index}
                        className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                          {new Date(trade.entry_date).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                          ${trade.entry_price?.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                          {new Date(trade.exit_date).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                          ${trade.exit_price?.toFixed(2)}
                        </td>
                        <td className={`py-3 px-4 text-sm text-right font-medium ${
                          (trade.profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          ${trade.profit_loss?.toFixed(2)} ({trade.profit_loss_percent?.toFixed(2)}%)
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default BacktestingPage
