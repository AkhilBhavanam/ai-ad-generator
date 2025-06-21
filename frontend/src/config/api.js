// API Configuration
const isDevelopment = import.meta.env.DEV
const API_BASE_URL = isDevelopment ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:8000')

export const API_ENDPOINTS = {
  // Separated endpoints for step-by-step process
  SCRAPE: `${API_BASE_URL}/api/scrape-product`,
  GENERATE_SCRIPT: `${API_BASE_URL}/api/generate-script`,
  CREATE_VIDEO: `${API_BASE_URL}/api/create-video`,
  
  // Session management
  STATUS: (sessionId) => `${API_BASE_URL}/api/status/${sessionId}`,
  SESSION_DATA: (sessionId) => `${API_BASE_URL}/api/session/${sessionId}`,
  DOWNLOAD: (sessionId) => `${API_BASE_URL}/api/download/${sessionId}`,
  CLEANUP: (sessionId) => `${API_BASE_URL}/api/session/${sessionId}`,
  
  // Legacy endpoints (keep for compatibility)
  GENERATE_VIDEO: `${API_BASE_URL}/api/generate-video`,
  DEBUG_SCRAPE: `${API_BASE_URL}/api/debug-scrape`
}

// API utility functions
export const apiRequest = async (url, options = {}) => {
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  // Remove Content-Type for FormData
  if (options.body instanceof FormData) {
    delete defaultOptions.headers['Content-Type']
  }

  console.log('🌐 API Request:', { url, options: defaultOptions })

  try {
    const response = await fetch(url, defaultOptions)
    
    console.log('🌐 API Response status:', response.status, response.statusText)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.log('🌐 API Error response:', errorText)
      
      let errorMessage
      
      try {
        const errorJson = JSON.parse(errorText)
        errorMessage = errorJson.detail || errorJson.message || `HTTP ${response.status}`
      } catch {
        errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`
      }
      
      throw new Error(errorMessage)
    }
    
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      const jsonData = await response.json()
      console.log('🌐 API Response data:', jsonData)
      return jsonData
    }
    
    return response
  } catch (error) {
    // Enhanced error logging for debugging
    console.error('🌐 API Request failed:', {
      url,
      error: error.message,
      options
    })
    
    // Handle network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to the backend. Please make sure the server is running on port 8000.')
    }
    
    throw error
  }
}

// Specialized API functions for the video generation workflow
export const videoAPI = {
  // Step 1: Scrape product data
  scrapeProduct: async (url) => {
    console.log('🔍 API: Starting product scrape for URL:', url)
    
    const formData = new FormData()
    formData.append('url', url)
    
    console.log('🔍 API: FormData created:', { url })
    
    try {
      const result = await apiRequest(API_ENDPOINTS.SCRAPE, {
        method: 'POST',
        body: formData
      })
      
      console.log('🔍 API: Scrape result received:', result)
      
      // Validate the response structure
      if (!result) {
        throw new Error('Empty response from scrape endpoint')
      }
      
      if (!result.session_id && !result.sessionId) {
        console.error('🔍 API: Response missing session_id:', result)
        throw new Error('Backend did not return a session ID')
      }
      
      // Normalize session_id field (handle both snake_case and camelCase)
      if (result.session_id && !result.sessionId) {
        result.sessionId = result.session_id
      }
      
      return result
    } catch (error) {
      console.error('🔍 API: Scrape error:', error)
      throw error
    }
  },
  
  // Step 2: Generate script
  generateScript: async (sessionId, tone = 'exciting') => {
    console.log('📝 API: Generating script for session:', sessionId, 'with tone:', tone)
    
    if (!sessionId) {
      throw new Error('Session ID is required for script generation')
    }
    
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('tone', tone)
    
    try {
      const result = await apiRequest(API_ENDPOINTS.GENERATE_SCRIPT, {
        method: 'POST',
        body: formData
      })
      
      console.log('📝 API: Script generation result:', result)
      return result
    } catch (error) {
      console.error('📝 API: Script generation error:', error)
      throw error
    }
  },
  
  // Step 3: Create video
  createVideo: async (sessionId, settings) => {
    console.log('🎬 API: Creating video for session:', sessionId, 'with settings:', settings)
    
    if (!sessionId) {
      throw new Error('Session ID is required for video creation')
    }
    
    const formData = new FormData()
    formData.append('session_id', sessionId)
    formData.append('aspect_ratio', settings.aspectRatio || '16:9')
    formData.append('template', settings.template || 'modern')
    formData.append('voice_tone', settings.voiceTone || 'professional')
    formData.append('enable_karaoke', settings.enableKaraoke ? 'true' : 'false')
    formData.append('include_voiceover', settings.includeVoiceover ? 'true' : 'false')
    formData.append('background_music', settings.backgroundMusic || 'corporate')
    formData.append('include_music', settings.includeMusic ? 'true' : 'false')
    
    try {
      const result = await apiRequest(API_ENDPOINTS.CREATE_VIDEO, {
        method: 'POST',
        body: formData
      })
      
      console.log('🎬 API: Video creation result:', result)
      return result
    } catch (error) {
      console.error('🎬 API: Video creation error:', error)
      throw error
    }
  },
  
  // Get session status
  getStatus: async (sessionId) => {
    console.log('📊 API: Getting status for session:', sessionId)
    
    if (!sessionId) {
      throw new Error('Session ID is required for status check')
    }
    
    try {
      const result = await apiRequest(API_ENDPOINTS.STATUS(sessionId))
      console.log('📊 API: Status result:', result)
      return result
    } catch (error) {
      console.error('📊 API: Status check error:', error)
      throw error
    }
  },
  
  // Get complete session data
  getSessionData: async (sessionId) => {
    console.log('🗂️ API: Getting session data for:', sessionId)
    
    if (!sessionId) {
      throw new Error('Session ID is required for session data')
    }
    
    try {
      const result = await apiRequest(API_ENDPOINTS.SESSION_DATA(sessionId))
      console.log('🗂️ API: Session data result:', result)
      return result
    } catch (error) {
      console.error('🗂️ API: Session data error:', error)
      throw error
    }
  },
  
  // Poll status with timeout
  pollStatus: async (sessionId, timeoutMs = 60000, intervalMs = 2000) => {
    console.log('⏳ API: Starting status polling for session:', sessionId)
    
    const startTime = Date.now()
    
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          if (Date.now() - startTime > timeoutMs) {
            reject(new Error('Status polling timeout'))
            return
          }
          
          const status = await videoAPI.getStatus(sessionId)
          
          if (status.status === 'completed') {
            console.log('⏳ API: Polling completed successfully')
            resolve(status)
          } else if (status.status === 'error') {
            console.log('⏳ API: Polling detected error:', status.error)
            reject(new Error(status.error || 'Generation failed'))
          } else {
            console.log('⏳ API: Polling continues, current status:', status.status)
            // Continue polling
            setTimeout(poll, intervalMs)
          }
        } catch (error) {
          console.error('⏳ API: Polling error:', error)
          reject(error)
        }
      }
      
      poll()
    })
  }
}

export default API_ENDPOINTS 