import { Outlet, Link, useLocation } from 'react-router-dom'
import { Home, TrendingUp, Briefcase, Bell, BarChart3, History } from 'lucide-react'

const Layout = () => {
  const location = useLocation()
  
  const navItems = [
    { path: '/', icon: Home, label: 'Ana Sayfa' },
    { path: '/portfolio', icon: Briefcase, label: 'Portföy' },
    { path: '/alarms', icon: Bell, label: 'Alarmlar' },
    { path: '/backtesting', icon: BarChart3, label: 'Backtesting' },
    { path: '/history', icon: History, label: 'Geçmiş' },
  ]
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Kripto Analiz
              </h1>
            </div>
          </div>
        </div>
      </header>
      
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                    isActive
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
