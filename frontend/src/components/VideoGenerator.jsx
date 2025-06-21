import { useState, useEffect } from 'react'
import { useToast } from './ToastProvider'
import { videoAPI } from '../config/api'
import UrlInput from './UrlInput'
import VideoSettings from './VideoSettings'
import GenerationProgress from './GenerationProgress'
import ProductPreview from './ProductPreview'
import ScriptPreview from './ScriptPreview'
import VideoPreview from './VideoPreview'

const VideoGenerator = () => {
  const { showToast } = useToast()
  const [currentStep, setCurrentStep] = useState('input') // input, settings, generating, results
  const [url, setUrl] = useState('')
  const [settings, setSettings] = useState({
    aspectRatio: '16:9',
    template: 'modern',
    voiceTone: 'professional',
    enableKaraoke: true,
    includeVoiceover: true,
    includeMusic: true,
    backgroundMusic: 'corporate'
  })
  const [generationData, setGenerationData] = useState({
    sessionId: null,
    productData: null,
    adScript: null,
    videoPath: null,
    progress: 0,
    status: 'idle', // idle, scraping, scraped, generating_script, script_generated, creating_video, completed, error
    error: null,
    currentOperation: ''
  })

  const handleUrlSubmit = async (submittedUrl) => {
    console.log('🔗 Starting URL submission:', submittedUrl)
    setUrl(submittedUrl)
    
    // Start scraping immediately
    try {
      setGenerationData({
        sessionId: null,
        productData: null,
        adScript: null,
        videoPath: null,
        progress: 10,
        status: 'scraping',
        error: null,
        currentOperation: 'Scraping product data...'
      })
      setCurrentStep('generating')

      console.log('📡 Calling videoAPI.scrapeProduct...')
      const result = await videoAPI.scrapeProduct(submittedUrl)
      console.log('📡 Scrape result:', result)
      
      if (result.success && result.session_id) {
        console.log('✅ Scraping successful, session_id:', result.session_id)
        
        setGenerationData(prev => ({
          ...prev,
          sessionId: result.session_id,  // Make sure this is set
          productData: result.product_data,
          status: 'scraped',
          progress: 25,
          currentOperation: 'Product data scraped successfully!'
        }))
        
        // Auto-advance to settings after a short delay to show success
        setTimeout(() => {
          setCurrentStep('settings')
        }, 1500)
        
        showToast('Product data scraped successfully!', 'success')
      } else {
        console.error('❌ Scraping failed - no session_id in response:', result)
        throw new Error(result.error || 'Failed to scrape product data - no session ID returned')
      }
    } catch (error) {
      console.error('❌ Scraping error:', error)
      setGenerationData(prev => ({
        ...prev,
        status: 'error',
        error: error.message,
        currentOperation: 'Scraping failed'
      }))
      showToast(`Scraping failed: ${error.message}`, 'error')
    }
  }

  const handleSettingsConfirm = async (confirmedSettings) => {
    console.log('⚙️ Settings confirmed:', confirmedSettings)
    console.log('🔍 Current sessionId:', generationData.sessionId)
    
    // Check if we have a session ID
    if (!generationData.sessionId) {
      console.error('❌ No session ID available for settings confirmation')
      setGenerationData(prev => ({
        ...prev,
        status: 'error',
        error: 'No session ID available. Please try again.',
        currentOperation: 'Session error'
      }))
      showToast('Session error: No session ID available. Please try again.', 'error')
      return
    }
    
    setSettings(confirmedSettings)
    setCurrentStep('generating')
    
    try {
      // Step 1: Generate Script
      console.log('📝 Generating script for session:', generationData.sessionId)
      setGenerationData(prev => ({
        ...prev,
        status: 'generating_script',
        progress: 35,
        currentOperation: 'Generating AI script...',
        error: null
      }))

      const scriptResult = await videoAPI.generateScript(
        generationData.sessionId, 
        confirmedSettings.voiceTone
      )
      
      console.log('📝 Script generation result:', scriptResult)
      
      if (!scriptResult.success) {
        throw new Error(scriptResult.error || 'Failed to generate script')
      }

      setGenerationData(prev => ({
        ...prev,
        adScript: scriptResult.ad_script,
        status: 'script_generated',
        progress: 50,
        currentOperation: 'AI script generated successfully!'
      }))

      // Step 2: Create Video
      setTimeout(async () => {
        try {
          console.log('🎬 Creating video for session:', generationData.sessionId)
          setGenerationData(prev => ({
            ...prev,
            status: 'creating_video',
            progress: 60,
            currentOperation: 'Creating video with AI...'
          }))

          const videoResult = await videoAPI.createVideo(generationData.sessionId, confirmedSettings)
          console.log('🎬 Video creation result:', videoResult)
          
          if (videoResult.success) {
            setGenerationData(prev => ({
              ...prev,
              videoPath: videoResult.video_path,
              status: 'completed',
              progress: 100,
              currentOperation: 'Video created successfully!'
            }))
            
            setCurrentStep('results')
            showToast('Video generated successfully!', 'success')
          } else {
            throw new Error(videoResult.error || 'Failed to create video')
          }
        } catch (videoError) {
          console.error('❌ Video creation error:', videoError)
          setGenerationData(prev => ({
            ...prev,
            status: 'error',
            error: videoError.message,
            currentOperation: 'Video creation failed'
          }))
          showToast(`Video creation failed: ${videoError.message}`, 'error')
        }
      }, 1000)

    } catch (error) {
      console.error('❌ Script generation error:', error)
      setGenerationData(prev => ({
        ...prev,
        status: 'error',
        error: error.message,
        currentOperation: 'Script generation failed'
      }))
      showToast(`Script generation failed: ${error.message}`, 'error')
    }
  }

  const handleReset = () => {
    console.log('🔄 Resetting video generator')
    setCurrentStep('input')
    setUrl('')
    setGenerationData({
      sessionId: null,
      productData: null,
      adScript: null,
      videoPath: null,
      progress: 0,
      status: 'idle',
      error: null,
      currentOperation: ''
    })
  }

  const handleDownload = async () => {
    console.log('⬇️ Download requested for session:', generationData.sessionId)
    
    if (!generationData.sessionId) {
      console.error('❌ No session ID available for download')
      showToast('Download failed: No session ID available', 'error')
      return
    }
    
    try {
      const downloadUrl = `/api/download/${generationData.sessionId}`
      console.log('⬇️ Download URL:', downloadUrl)
      
      // Create a temporary anchor element to trigger download
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `ad_video_${generationData.sessionId}.mp4`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      showToast('Download started!', 'success')
    } catch (error) {
      console.error('❌ Download error:', error)
      showToast('Download failed. Please try again.', 'error')
    }
  }

  // Auto-refresh session data when in results step
  useEffect(() => {
    if (currentStep === 'results' && generationData.sessionId) {
      console.log('🔄 Refreshing session data for:', generationData.sessionId)
      
      const refreshSessionData = async () => {
        try {
          const sessionData = await videoAPI.getSessionData(generationData.sessionId)
          console.log('🔄 Session data refreshed:', sessionData)
          
          setGenerationData(prev => ({
            ...prev,
            productData: sessionData.product_data,
            adScript: sessionData.ad_script,
            videoPath: sessionData.video_path,
            status: sessionData.status
          }))
        } catch (error) {
          console.error('❌ Failed to refresh session data:', error)
        }
      }
      
      refreshSessionData()
    }
  }, [currentStep, generationData.sessionId])

  // Debug logging for session changes
  useEffect(() => {
    console.log('🔍 Session state changed:', {
      sessionId: generationData.sessionId,
      status: generationData.status,
      currentStep: currentStep
    })
  }, [generationData.sessionId, generationData.status, currentStep])

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            AI Video Generator
          </h1>
          <p className="text-gray-600">
            Transform any product URL into a compelling video advertisement
          </p>
          {/* Debug info - remove in production */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-2 text-xs text-gray-500">
              Debug: Session ID = {generationData.sessionId || 'null'} | Status = {generationData.status}
            </div>
          )}
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex justify-center">
            <div className="flex items-center space-x-4">
              {[
                { key: 'input', label: 'URL Input', icon: '🔗' },
                { key: 'settings', label: 'Settings', icon: '⚙️' },
                { key: 'generating', label: 'Generating', icon: '🎬' },
                { key: 'results', label: 'Results', icon: '✅' }
              ].map((step, index) => (
                <div key={step.key} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    currentStep === step.key ? 'bg-purple-500 border-purple-500 text-white' :
                    ['settings', 'generating', 'results'].slice(0, ['input', 'settings', 'generating', 'results'].indexOf(currentStep)).includes(step.key) ?
                    'bg-green-500 border-green-500 text-white' :
                    'bg-gray-200 border-gray-300 text-gray-500'
                  }`}>
                    <span className="text-sm">{step.icon}</span>
                  </div>
                  <span className={`ml-2 text-sm font-medium ${
                    currentStep === step.key ? 'text-purple-600' : 'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                  {index < 3 && (
                    <svg className="w-5 h-5 text-gray-300 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {currentStep === 'input' && (
            <UrlInput onSubmit={handleUrlSubmit} />
          )}
          
          {currentStep === 'settings' && (
            <VideoSettings
              url={url}
              settings={settings}
              onSettingsChange={setSettings}
              onConfirm={handleSettingsConfirm}
              onBack={() => setCurrentStep('input')}
              productData={generationData.productData}
            />
          )}
          
          {currentStep === 'generating' && (
            <GenerationProgress
              status={generationData.status}
              progress={generationData.progress}
              error={generationData.error}
              currentOperation={generationData.currentOperation}
              onReset={handleReset}
            />
          )}
          
          {currentStep === 'results' && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  🎉 Your Video is Ready!
                </h2>
                <div className="flex space-x-3">
                  <button
                    onClick={handleDownload}
                    className="btn btn-primary bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download Video
                  </button>
                  <button
                    onClick={handleReset}
                    className="btn btn-secondary"
                  >
                    Create Another
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <VideoPreview
                    sessionId={generationData.sessionId}
                    videoPath={generationData.videoPath}
                  />
                </div>
                <div className="space-y-6">
                  <ProductPreview productData={generationData.productData} />
                  <ScriptPreview adScript={generationData.adScript} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default VideoGenerator 