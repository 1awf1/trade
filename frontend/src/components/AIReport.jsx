const AIReport = ({ report }) => {
  if (!report) return null
  
  // Split report into paragraphs
  const paragraphs = report.split('\n').filter(p => p.trim())
  
  return (
    <div className="prose dark:prose-invert max-w-none">
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900 dark:to-blue-900 p-6 rounded-lg">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold">AI</span>
            </div>
          </div>
          <div className="flex-1">
            {paragraphs.map((paragraph, index) => (
              <p
                key={index}
                className="text-gray-800 dark:text-gray-200 mb-3 last:mb-0 leading-relaxed"
              >
                {paragraph}
              </p>
            ))}
          </div>
        </div>
      </div>
      
      <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <p className="text-xs text-gray-500 dark:text-gray-400 italic">
          Bu yorum yapay zeka tarafından üretilmiştir ve yatırım tavsiyesi niteliği taşımaz.
          Yatırım kararlarınızı verirken kendi araştırmanızı yapın ve gerekirse profesyonel
          danışmanlık alın.
        </p>
      </div>
    </div>
  )
}

export default AIReport
