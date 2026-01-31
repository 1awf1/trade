import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const IndicatorsTable = ({ indicators }) => {
  if (!indicators) return null
  
  const getSignalIcon = (signal) => {
    if (!signal) return <Minus className="w-5 h-5 text-gray-400" />
    
    const signalLower = signal.toLowerCase()
    if (signalLower.includes('bullish') || signalLower.includes('buy') || signalLower.includes('oversold')) {
      return <TrendingUp className="w-5 h-5 text-green-500" />
    } else if (signalLower.includes('bearish') || signalLower.includes('sell') || signalLower.includes('overbought')) {
      return <TrendingDown className="w-5 h-5 text-red-500" />
    }
    return <Minus className="w-5 h-5 text-gray-400" />
  }
  
  const indicatorRows = [
    { name: 'RSI', value: indicators.rsi?.toFixed(2), signal: indicators.rsi_signal },
    { name: 'MACD', value: indicators.macd?.value?.toFixed(2), signal: indicators.macd_signal },
    { name: 'Bollinger Bands', value: indicators.bollinger?.middle?.toFixed(2), signal: indicators.bollinger_signal },
    { name: 'EMA 50', value: indicators.ema_50?.toFixed(2), signal: indicators.ma_signal },
    { name: 'EMA 200', value: indicators.ema_200?.toFixed(2), signal: indicators.ema_200_trend_filter },
    { name: 'Stochastic', value: indicators.stochastic?.k?.toFixed(2), signal: indicators.stochastic_signal },
    { name: 'ATR', value: indicators.atr?.value?.toFixed(2), signal: null },
    { name: 'VWAP', value: indicators.vwap?.toFixed(2), signal: indicators.vwap_signal },
    { name: 'OBV', value: indicators.obv?.toFixed(0), signal: indicators.obv_signal },
  ]
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
              İndikatör
            </th>
            <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
              Değer
            </th>
            <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
              Sinyal
            </th>
          </tr>
        </thead>
        <tbody>
          {indicatorRows.map((row, index) => (
            <tr
              key={index}
              className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <td className="py-3 px-4 text-sm text-gray-900 dark:text-white font-medium">
                {row.name}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 text-right">
                {row.value || 'N/A'}
              </td>
              <td className="py-3 px-4 text-center">
                <div className="flex items-center justify-center space-x-2">
                  {getSignalIcon(row.signal)}
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {row.signal || 'Nötr'}
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Confluence Score */}
      {indicators.confluence_score !== undefined && (
        <div className="mt-4 p-4 bg-primary-50 dark:bg-primary-900 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-primary-900 dark:text-primary-100">
              İndikatör Uyumu (Confluence)
            </span>
            <span className="text-lg font-bold text-primary-700 dark:text-primary-300">
              {(indicators.confluence_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}
      
      {/* Special Signals */}
      <div className="mt-4 space-y-2">
        {indicators.golden_death_cross && (
          <div className={`p-3 rounded-lg ${
            indicators.golden_death_cross === 'golden_cross'
              ? 'bg-green-50 dark:bg-green-900'
              : 'bg-red-50 dark:bg-red-900'
          }`}>
            <p className="text-sm font-medium">
              {indicators.golden_death_cross === 'golden_cross' ? '🟢 Golden Cross' : '🔴 Death Cross'}
            </p>
          </div>
        )}
        
        {indicators.rsi_divergence && (
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900 rounded-lg">
            <p className="text-sm font-medium">
              ⚠️ RSI Divergence: {indicators.rsi_divergence}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default IndicatorsTable
