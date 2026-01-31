import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react'

const SignalCard = ({ signal }) => {
  if (!signal) return null
  
  const getSignalColor = (type) => {
    const typeLower = type?.toLowerCase() || ''
    if (typeLower.includes('strong_buy')) return 'bg-green-600'
    if (typeLower.includes('buy')) return 'bg-green-500'
    if (typeLower.includes('strong_sell')) return 'bg-red-600'
    if (typeLower.includes('sell')) return 'bg-red-500'
    if (typeLower.includes('neutral')) return 'bg-gray-500'
    return 'bg-yellow-500'
  }
  
  const getSignalIcon = (type) => {
    const typeLower = type?.toLowerCase() || ''
    if (typeLower.includes('buy')) return <TrendingUp className="w-8 h-8" />
    if (typeLower.includes('sell')) return <TrendingDown className="w-8 h-8" />
    if (typeLower.includes('neutral')) return <Minus className="w-8 h-8" />
    return <AlertTriangle className="w-8 h-8" />
  }
  
  const getSignalText = (type) => {
    const typeLower = type?.toLowerCase() || ''
    if (typeLower.includes('strong_buy')) return 'Güçlü Al'
    if (typeLower.includes('buy')) return 'Al'
    if (typeLower.includes('strong_sell')) return 'Güçlü Sat'
    if (typeLower.includes('sell')) return 'Sat'
    if (typeLower.includes('neutral')) return 'Nötr'
    return 'Belirsiz'
  }
  
  const signalColor = getSignalColor(signal.signal_type)
  const signalIcon = getSignalIcon(signal.signal_type)
  const signalText = getSignalText(signal.signal_type)
  
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`${signalColor} text-white p-4 rounded-full`}>
            {signalIcon}
          </div>
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {signalText}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Başarı İhtimali: {signal.success_probability?.toFixed(1)}%
            </p>
          </div>
        </div>
        
        <div className="text-right">
          {signal.stop_loss && (
            <div className="mb-2">
              <p className="text-sm text-gray-500 dark:text-gray-400">Stop Loss</p>
              <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                ${signal.stop_loss?.toFixed(2)}
              </p>
            </div>
          )}
          {signal.take_profit && (
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Take Profit</p>
              <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                ${signal.take_profit?.toFixed(2)}
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Signal Details */}
      <div className="mt-6 grid md:grid-cols-2 gap-4">
        {signal.supporting_indicators && signal.supporting_indicators.length > 0 && (
          <div className="p-4 bg-green-50 dark:bg-green-900 rounded-lg">
            <h4 className="text-sm font-semibold text-green-900 dark:text-green-100 mb-2">
              Destekleyen İndikatörler
            </h4>
            <ul className="space-y-1">
              {signal.supporting_indicators.map((indicator, index) => (
                <li key={index} className="text-sm text-green-700 dark:text-green-300">
                  • {indicator}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {signal.conflicting_indicators && signal.conflicting_indicators.length > 0 && (
          <div className="p-4 bg-red-50 dark:bg-red-900 rounded-lg">
            <h4 className="text-sm font-semibold text-red-900 dark:text-red-100 mb-2">
              Çelişen İndikatörler
            </h4>
            <ul className="space-y-1">
              {signal.conflicting_indicators.map((indicator, index) => (
                <li key={index} className="text-sm text-red-700 dark:text-red-300">
                  • {indicator}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Risk Factors */}
      {signal.risk_factors && signal.risk_factors.length > 0 && (
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900 rounded-lg">
          <h4 className="text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
            Risk Faktörleri
          </h4>
          <ul className="space-y-1">
            {signal.risk_factors.map((factor, index) => (
              <li key={index} className="text-sm text-yellow-700 dark:text-yellow-300">
                • {factor}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default SignalCard
