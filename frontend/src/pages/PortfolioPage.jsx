import { useState, useEffect } from 'react'
import { Plus, TrendingUp, TrendingDown, Trash2 } from 'lucide-react'
import { portfolioAPI } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const PortfolioPage = () => {
  const [portfolio, setPortfolio] = useState(null)
  const [performance, setPerformance] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    coin: '',
    amount: '',
    purchase_price: '',
    purchase_date: new Date().toISOString().split('T')[0],
  })
  
  useEffect(() => {
    loadPortfolio()
    loadPerformance()
  }, [])
  
  const loadPortfolio = async () => {
    try {
      const response = await portfolioAPI.get()
      setPortfolio(response.data)
    } catch (error) {
      console.error('Portföy yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadPerformance = async () => {
    try {
      const response = await portfolioAPI.getPerformance()
      setPerformance(response.data.performance || [])
    } catch (error) {
      console.error('Performans verisi yüklenemedi:', error)
    }
  }
  
  const handleAddCoin = async (e) => {
    e.preventDefault()
    try {
      await portfolioAPI.add(formData)
      setShowAddForm(false)
      setFormData({
        coin: '',
        amount: '',
        purchase_price: '',
        purchase_date: new Date().toISOString().split('T')[0],
      })
      loadPortfolio()
      loadPerformance()
    } catch (error) {
      console.error('Coin eklenemedi:', error)
    }
  }
  
  const handleRemoveCoin = async (holdingId) => {
    if (!confirm('Bu coin\'i portföyden çıkarmak istediğinize emin misiniz?')) return
    
    try {
      await portfolioAPI.remove(holdingId)
      loadPortfolio()
      loadPerformance()
    } catch (error) {
      console.error('Coin çıkarılamadı:', error)
    }
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
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
          Portföy Yönetimi
        </h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Coin Ekle</span>
        </button>
      </div>
      
      {/* Add Coin Form */}
      {showAddForm && (
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Yeni Coin Ekle
          </h3>
          <form onSubmit={handleAddCoin} className="space-y-4">
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
                  Miktar
                </label>
                <input
                  type="number"
                  step="any"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="input"
                  placeholder="0.5"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Alış Fiyatı ($)
                </label>
                <input
                  type="number"
                  step="any"
                  value={formData.purchase_price}
                  onChange={(e) => setFormData({ ...formData, purchase_price: e.target.value })}
                  className="input"
                  placeholder="50000"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Alış Tarihi
                </label>
                <input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                  className="input"
                  required
                />
              </div>
            </div>
            <div className="flex space-x-3">
              <button type="submit" className="btn-primary">
                Ekle
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="btn-secondary"
              >
                İptal
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Portfolio Summary */}
      {portfolio && (
        <div className="grid md:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Toplam Değer</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              ${portfolio.total_value?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Yatırılan</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              ${portfolio.total_invested?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Kar/Zarar</p>
            <p className={`text-2xl font-bold ${
              (portfolio.total_profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              ${portfolio.total_profit_loss?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Kar/Zarar %</p>
            <div className="flex items-center space-x-2">
              {(portfolio.total_profit_loss_percent || 0) >= 0 ? (
                <TrendingUp className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600" />
              )}
              <p className={`text-2xl font-bold ${
                (portfolio.total_profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {portfolio.total_profit_loss_percent?.toFixed(2) || '0.00'}%
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Performance Chart */}
      {performance.length > 0 && (
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Performans Grafiği
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      
      {/* Holdings List */}
      <div className="card">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Varlıklar
        </h3>
        {portfolio?.holdings && portfolio.holdings.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Coin
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Miktar
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Alış Fiyatı
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Güncel Fiyat
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Değer
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Kar/Zarar
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    İşlem
                  </th>
                </tr>
              </thead>
              <tbody>
                {portfolio.holdings.map((holding) => (
                  <tr
                    key={holding.id}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <td className="py-3 px-4 text-sm font-medium text-gray-900 dark:text-white">
                      {holding.coin}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                      {holding.amount}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                      ${holding.purchase_price?.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                      ${holding.current_price?.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                      ${holding.current_value?.toFixed(2)}
                    </td>
                    <td className={`py-3 px-4 text-sm text-right font-medium ${
                      (holding.profit_loss_percent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {holding.profit_loss_percent?.toFixed(2)}%
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleRemoveCoin(holding.id)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            Portföyünüzde henüz coin bulunmuyor. Yukarıdaki butonu kullanarak coin ekleyin.
          </p>
        )}
      </div>
    </div>
  )
}

export default PortfolioPage
