const GenerationProgress = ({ status, progress, error, currentOperation, onReset }) => {
  const steps = [
    { key: 'scraping', label: 'Scraping Product Data', icon: '🔍', description: 'Extracting product information from URL' },
    { key: 'scraped', label: 'Data Retrieved', icon: '✅', description: 'Product data successfully extracted' },
    { key: 'generating_script', label: 'Generating AI Script', icon: '✍️', description: 'Creating compelling ad copy with AI' },
    { key: 'script_generated', label: 'Script Created', icon: '📝', description: 'AI script generation completed' },
    { key: 'creating_video', label: 'Creating Video', icon: '🎬', description: 'Rendering video with animations and voiceover' },
    { key: 'completed', label: 'Completed', icon: '🎉', description: 'Your video is ready!' }
  ]

  const getStepStatus = (stepKey) => {
    const stepIndex = steps.findIndex(step => step.key === stepKey)
    const currentIndex = steps.findIndex(step => step.key === status)
    
    if (status === 'error') {
      return stepIndex <= currentIndex ? 'error' : 'pending'
    }
    
    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Generation Failed
          </h2>
          <p className="text-gray-600 mb-4">
            {error}
          </p>
          {currentOperation && (
            <p className="text-sm text-gray-500 mb-6">
              Failed during: {currentOperation}
            </p>
          )}
          <div className="flex justify-center space-x-4">
            <button
              onClick={onReset}
              className="btn btn-primary bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Generating Your Video
          </h2>
          <p className="text-gray-600">
            Our AI is working through each step to create your perfect video advertisement
          </p>
          {currentOperation && (
            <p className="text-purple-600 font-medium mt-2">
              {currentOperation}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>Overall Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-purple-500 to-blue-600 h-3 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const stepStatus = getStepStatus(step.key)
            
            return (
              <div key={step.key} className="flex items-center space-x-4">
                <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                  stepStatus === 'completed' ? 'bg-green-500 border-green-500 text-white' :
                  stepStatus === 'active' ? 'bg-purple-500 border-purple-500 text-white animate-pulse' :
                  stepStatus === 'error' ? 'bg-red-500 border-red-500 text-white' :
                  'bg-gray-200 border-gray-300 text-gray-500'
                }`}>
                  {stepStatus === 'completed' ? (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : stepStatus === 'active' ? (
                    <div className="animate-spin">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </div>
                  ) : stepStatus === 'error' ? (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : (
                    <span className="text-xl">{step.icon}</span>
                  )}
                </div>
                
                <div className="flex-1">
                  <h3 className={`font-semibold transition-colors duration-300 ${
                    stepStatus === 'active' ? 'text-purple-600' :
                    stepStatus === 'completed' ? 'text-green-600' :
                    stepStatus === 'error' ? 'text-red-600' :
                    'text-gray-500'
                  }`}>
                    {step.label}
                    {stepStatus === 'active' && (
                      <span className="ml-2 text-sm">
                        <span className="animate-pulse">●</span>
                        <span className="animate-pulse animation-delay-200">●</span>
                        <span className="animate-pulse animation-delay-400">●</span>
                      </span>
                    )}
                  </h3>
                  <p className="text-sm text-gray-600">{step.description}</p>
                  {stepStatus === 'active' && currentOperation && (
                    <p className="text-xs text-purple-600 mt-1 font-medium">{currentOperation}</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Enhanced Info Box */}
        <div className="mt-8 p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-2">💡 What's happening now?</h4>
          <div className="text-sm text-gray-600">
            {status === 'scraping' && (
              <p>Analyzing the product page to extract title, price, images, and key features...</p>
            )}
            {status === 'scraped' && (
              <p>Product data successfully extracted! Moving to script generation...</p>
            )}
            {status === 'generating_script' && (
              <p>AI is creating a compelling advertisement script with hook, problem, solution, and call-to-action...</p>
            )}
            {status === 'script_generated' && (
              <p>Perfect script created! Now rendering the video with animations and voiceover...</p>
            )}
            {status === 'creating_video' && (
              <p>Creating high-quality video with product images, text animations, and AI-generated voiceover...</p>
            )}
            {(!status || status === 'idle') && (
              <p>Video ads perform 50% better than static images and can increase conversion rates by up to 80%!</p>
            )}
          </div>
        </div>

        {/* Cancel Button */}
        <div className="text-center mt-8">
          <button
            onClick={onReset}
            className="text-gray-500 hover:text-gray-700 text-sm underline transition-colors"
          >
            Cancel Generation
          </button>
        </div>
      </div>
    </div>
  )
}

export default GenerationProgress 