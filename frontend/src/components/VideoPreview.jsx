import { useState, useEffect } from 'react'
import { API_ENDPOINTS } from '../config/api'

const VideoPreview = ({ sessionId, videoPath }) => {
  const [videoUrl, setVideoUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isDownloading, setIsDownloading] = useState(false)

  useEffect(() => {
    if (sessionId) {
      // Construct video URL for preview
      const previewUrl = `${API_ENDPOINTS.DOWNLOAD(sessionId)}?preview=true`
      setVideoUrl(previewUrl)
      setLoading(false)
    } else if (videoPath) {
      // Fallback: use video path directly if available
      setVideoUrl(videoPath)
      setLoading(false)
    } else {
      setError('No video available')
      setLoading(false)
    }
  }, [sessionId, videoPath])

  const handleDownload = async () => {
    if (!sessionId) {
      setError('Download not available - no session ID')
      return
    }

    try {
      setIsDownloading(true)
      
      // Create download link
      const downloadUrl = API_ENDPOINTS.DOWNLOAD(sessionId)
      
      // Method 1: Try direct download link
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `ad_video_${sessionId}.mp4`
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Method 2: If that doesn't work, try fetch and blob
      setTimeout(async () => {
        try {
          const response = await fetch(downloadUrl)
          if (response.ok) {
            const blob = await response.blob()
            const blobUrl = window.URL.createObjectURL(blob)
            const blobLink = document.createElement('a')
            blobLink.href = blobUrl
            blobLink.download = `ad_video_${sessionId}.mp4`
            document.body.appendChild(blobLink)
            blobLink.click()
            document.body.removeChild(blobLink)
            window.URL.revokeObjectURL(blobUrl)
          }
        } catch (fetchError) {
          console.warn('Fetch download failed:', fetchError)
          // Direct link method should have worked
        }
      }, 1000)
      
    } catch (error) {
      console.error('Download error:', error)
      setError('Download failed. Please try again.')
    } finally {
      setIsDownloading(false)
    }
  }

  const handleShare = async () => {
    if (navigator.share && videoUrl) {
      try {
        await navigator.share({
          title: 'Check out my AI-generated video ad!',
          text: 'I created this awesome product video using AI',
          url: window.location.href
        })
      } catch (error) {
        // Fallback to copying link to clipboard
        handleCopyLink()
      }
    } else {
      handleCopyLink()
    }
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      // You could show a toast notification here
      alert('Link copied to clipboard!')
    } catch (error) {
      console.error('Failed to copy link:', error)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading video...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Video Error</h3>
            <p className="text-gray-600 text-sm">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Video Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            🎬 Your AI-Generated Video
          </h3>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
              Ready
            </span>
          </div>
        </div>
      </div>

      {/* Video Player */}
      <div className="p-6">
        <div className="relative bg-gray-900 rounded-lg overflow-hidden">
          {videoUrl ? (
            <video
              key={videoUrl} // Force re-render when URL changes
              className="w-full h-auto max-h-96"
              controls
              poster="" // You could set a poster image here
              onError={(e) => {
                console.error('Video load error:', e)
                setError('Failed to load video. The file may still be processing.')
              }}
              onCanPlay={() => {
                setError(null) // Clear any previous errors
              }}
            >
              <source src={videoUrl} type="video/mp4" />
              <p className="text-white p-4">
                Your browser doesn't support video playback. 
                <button 
                  onClick={handleDownload}
                  className="text-blue-400 underline ml-2"
                >
                  Download the video instead
                </button>
              </p>
            </video>
          ) : (
            <div className="flex items-center justify-center h-48">
              <p className="text-gray-400">Video not available</p>
            </div>
          )}
        </div>

        {/* Video Info */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Format:</span>
              <div className="font-medium">MP4</div>
            </div>
            <div>
              <span className="text-gray-600">Quality:</span>
              <div className="font-medium">HD</div>
            </div>
            <div>
              <span className="text-gray-600">Features:</span>
              <div className="font-medium">AI Voice + Text</div>
            </div>
            <div>
              <span className="text-gray-600">Duration:</span>
              <div className="font-medium">~30s</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 mt-6">
          <button
            onClick={handleDownload}
            disabled={isDownloading || !sessionId}
            className="flex-1 btn btn-primary bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Downloading...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Video
              </>
            )}
          </button>
          
          <button
            onClick={handleShare}
            className="flex-1 btn btn-secondary"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            Share
          </button>
        </div>

        {/* Tips */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">💡 Tips for best results:</h4>
          <ul className="text-blue-800 text-sm space-y-1">
            <li>• Download the video for best quality playback</li>
            <li>• Use downloaded video for social media uploads</li>
            <li>• Share the link to let others see your creation process</li>
            <li>• Video works best on platforms that support MP4 format</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default VideoPreview 