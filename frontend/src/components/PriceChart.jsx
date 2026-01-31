import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import { coinsAPI } from '../services/api'

const PriceChart = ({ coin, timeframe }) => {
  const chartContainerRef = useRef()
  const chartRef = useRef()
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    if (!chartContainerRef.current) return
    
    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1f2937' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#374151' },
        horzLines: { color: '#374151' },
      },
    })
    
    chartRef.current = chart
    
    // Load data
    loadChartData(chart)
    
    // Handle resize
    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current.clientWidth,
      })
    }
    
    window.addEventListener('resize', handleResize)
    
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [coin, timeframe])
  
  const loadChartData = async (chart) => {
    try {
      // In a real implementation, fetch OHLCV data from the API
      // For now, create sample data
      const candlestickSeries = chart.addCandlestickSeries()
      
      const sampleData = generateSampleData()
      candlestickSeries.setData(sampleData)
      
      setLoading(false)
    } catch (error) {
      console.error('Chart data load error:', error)
      setLoading(false)
    }
  }
  
  const generateSampleData = () => {
    const data = []
    const basePrice = 50000
    let currentPrice = basePrice
    const now = Math.floor(Date.now() / 1000)
    
    for (let i = 100; i >= 0; i--) {
      const time = now - i * 3600
      const change = (Math.random() - 0.5) * 1000
      currentPrice += change
      
      const open = currentPrice
      const close = currentPrice + (Math.random() - 0.5) * 500
      const high = Math.max(open, close) + Math.random() * 300
      const low = Math.min(open, close) - Math.random() * 300
      
      data.push({
        time,
        open,
        high,
        low,
        close,
      })
    }
    
    return data
  }
  
  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-800 rounded-lg">
        <p className="text-gray-400">Grafik yükleniyor...</p>
      </div>
    )
  }
  
  return <div ref={chartContainerRef} className="rounded-lg overflow-hidden" />
}

export default PriceChart
