import { useState, useEffect } from 'react'
import { Plus, Bell, BellOff, Trash2, Edit } from 'lucide-react'
import { alarmsAPI } from '../services/api'

const ALARM_TYPES = [
  { value: 'price', label: 'Fiyat' },
  { value: 'signal', label: 'Sinyal' },
  { value: 'success_probability', label: 'Başarı İhtimali' },
]

const CONDITIONS = [
  { value: 'above', label: 'Üzerinde' },
  { value: 'below', label: 'Altında' },
  { value: 'equals', label: 'Eşit' },
]

const AlarmsPage = () => {
  const [alarms, setAlarms] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingAlarm, setEditingAlarm] = useState(null)
  const [formData, setFormData] = useState({
    coin: '',
    type: 'price',
    condition: 'above',
    threshold: '',
    notification_channels: ['email'],
    auto_disable: true,
  })
  
  useEffect(() => {
    loadAlarms()
  }, [])
  
  const loadAlarms = async () => {
    try {
      const response = await alarmsAPI.list()
      setAlarms(response.data.alarms || [])
    } catch (error) {
      console.error('Alarmlar yüklenemedi:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editingAlarm) {
        await alarmsAPI.update(editingAlarm.id, formData)
      } else {
        await alarmsAPI.create(formData)
      }
      setShowForm(false)
      setEditingAlarm(null)
      setFormData({
        coin: '',
        type: 'price',
        condition: 'above',
        threshold: '',
        notification_channels: ['email'],
        auto_disable: true,
      })
      loadAlarms()
    } catch (error) {
      console.error('Alarm kaydedilemedi:', error)
    }
  }
  
  const handleEdit = (alarm) => {
    setEditingAlarm(alarm)
    setFormData({
      coin: alarm.coin,
      type: alarm.type,
      condition: alarm.condition,
      threshold: alarm.threshold,
      notification_channels: alarm.notification_channels || ['email'],
      auto_disable: alarm.auto_disable,
    })
    setShowForm(true)
  }
  
  const handleDelete = async (id) => {
    if (!confirm('Bu alarmı silmek istediğinize emin misiniz?')) return
    
    try {
      await alarmsAPI.delete(id)
      loadAlarms()
    } catch (error) {
      console.error('Alarm silinemedi:', error)
    }
  }
  
  const handleToggleActive = async (alarm) => {
    try {
      await alarmsAPI.update(alarm.id, { active: !alarm.active })
      loadAlarms()
    } catch (error) {
      console.error('Alarm durumu değiştirilemedi:', error)
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
          Alarm Yönetimi
        </h2>
        <button
          onClick={() => {
            setShowForm(!showForm)
            setEditingAlarm(null)
            setFormData({
              coin: '',
              type: 'price',
              condition: 'above',
              threshold: '',
              notification_channels: ['email'],
              auto_disable: true,
            })
          }}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Yeni Alarm</span>
        </button>
      </div>
      
      {/* Alarm Form */}
      {showForm && (
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {editingAlarm ? 'Alarm Düzenle' : 'Yeni Alarm Oluştur'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
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
                  Alarm Türü
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="input"
                >
                  {ALARM_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Koşul
                </label>
                <select
                  value={formData.condition}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  className="input"
                >
                  {CONDITIONS.map((cond) => (
                    <option key={cond.value} value={cond.value}>
                      {cond.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Eşik Değeri
                </label>
                <input
                  type="number"
                  step="any"
                  value={formData.threshold}
                  onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
                  className="input"
                  placeholder={formData.type === 'price' ? '50000' : '80'}
                  required
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.auto_disable}
                  onChange={(e) => setFormData({ ...formData, auto_disable: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Tetiklendiğinde otomatik devre dışı bırak
                </span>
              </label>
            </div>
            
            <div className="flex space-x-3">
              <button type="submit" className="btn-primary">
                {editingAlarm ? 'Güncelle' : 'Oluştur'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setEditingAlarm(null)
                }}
                className="btn-secondary"
              >
                İptal
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Alarms List */}
      <div className="card">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Alarmlar
        </h3>
        {alarms.length > 0 ? (
          <div className="space-y-4">
            {alarms.map((alarm) => (
              <div
                key={alarm.id}
                className={`p-4 border-2 rounded-lg transition-colors ${
                  alarm.active
                    ? 'border-primary-300 dark:border-primary-700 bg-primary-50 dark:bg-primary-900'
                    : 'border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => handleToggleActive(alarm)}
                      className={`p-2 rounded-full ${
                        alarm.active
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-400 text-white'
                      }`}
                    >
                      {alarm.active ? (
                        <Bell className="w-5 h-5" />
                      ) : (
                        <BellOff className="w-5 h-5" />
                      )}
                    </button>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">
                        {alarm.coin} - {ALARM_TYPES.find(t => t.value === alarm.type)?.label}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {CONDITIONS.find(c => c.value === alarm.condition)?.label} {alarm.threshold}
                      </p>
                      {alarm.last_triggered && (
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Son tetiklenme: {new Date(alarm.last_triggered).toLocaleString('tr-TR')}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleEdit(alarm)}
                      className="p-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(alarm.id)}
                      className="p-2 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            Henüz alarm oluşturmadınız. Yukarıdaki butonu kullanarak yeni alarm ekleyin.
          </p>
        )}
      </div>
    </div>
  )
}

export default AlarmsPage
