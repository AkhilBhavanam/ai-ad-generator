import { useState } from 'react'

const VideoSettings = ({ url, settings, onSettingsChange, onConfirm, onBack, productData }) => {
  const [localSettings, setLocalSettings] = useState(settings)

  const handleChange = (key, value) => {
    const newSettings = { ...localSettings, [key]: value }
    setLocalSettings(newSettings)
    onSettingsChange(newSettings)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onConfirm(localSettings)
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Video Settings</h2>
            <p className="text-gray-600">Configure how your video will be generated</p>
          </div>
          <button
            onClick={onBack}
            className="text-gray-500 hover:text-gray-700 text-sm flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to URL Input
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Product Preview (if available) */}
          {productData && (
            <div className="lg:col-span-1">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <span className="text-green-500 mr-2">✅</span>
                  Product Data Scraped
                </h3>
                
                {productData.primary_image && (
                  <div className="mb-4">
                    <img
                      src={productData.primary_image}
                      alt={productData.title}
                      className="w-full h-32 object-cover rounded-lg"
                      onError={(e) => {
                        e.target.style.display = 'none'
                      }}
                    />
                  </div>
                )}
                
                <div className="space-y-3">
                  <div>
                    <h4 className="font-medium text-gray-900 text-sm">Product Title</h4>
                    <p className="text-gray-600 text-sm line-clamp-2">
                      {productData.title || 'Title not available'}
                    </p>
                  </div>
                  
                  {productData.price && (
                    <div>
                      <h4 className="font-medium text-gray-900 text-sm">Price</h4>
                      <p className="text-green-600 font-semibold">
                        {productData.price}
                      </p>
                    </div>
                  )}
                  
                  {productData.rating && (
                    <div>
                      <h4 className="font-medium text-gray-900 text-sm">Rating</h4>
                      <p className="text-yellow-600">
                        ⭐ {productData.rating} 
                        {productData.review_count && ` (${productData.review_count} reviews)`}
                      </p>
                    </div>
                  )}

                  {productData.description && (
                    <div>
                      <h4 className="font-medium text-gray-900 text-sm">Description</h4>
                      <p className="text-gray-600 text-xs line-clamp-3">
                        {productData.description}
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <p className="text-green-700 text-xs">
                    🎯 This data will be used to create your personalized video advertisement
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Settings Form */}
          <div className={productData ? "lg:col-span-2" : "lg:col-span-3"}>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Current URL Display */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Product URL
                </label>
                <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                  <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <span className="text-sm text-gray-600 truncate flex-1">{url}</span>
                </div>
              </div>

              {/* Aspect Ratio */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Video Aspect Ratio
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: '16:9', label: 'Landscape (16:9)', desc: 'YouTube, Facebook' },
                    { value: '9:16', label: 'Portrait (9:16)', desc: 'TikTok, Instagram Stories' },
                    { value: '1:1', label: 'Square (1:1)', desc: 'Instagram Feed' }
                  ].map((option) => (
                    <label key={option.value} className="cursor-pointer">
                      <input
                        type="radio"
                        name="aspectRatio"
                        value={option.value}
                        checked={localSettings.aspectRatio === option.value}
                        onChange={(e) => handleChange('aspectRatio', e.target.value)}
                        className="sr-only"
                      />
                      <div className={`p-4 border-2 rounded-lg text-center transition-all ${
                        localSettings.aspectRatio === option.value
                          ? 'border-purple-500 bg-purple-50 text-purple-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                        <div className={`mx-auto mb-2 ${
                          option.value === '16:9' ? 'w-8 h-5' :
                          option.value === '9:16' ? 'w-5 h-8' :
                          'w-6 h-6'
                        } bg-current opacity-20 rounded`}></div>
                        <div className="font-medium text-sm">{option.label}</div>
                        <div className="text-xs text-gray-500 mt-1">{option.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Template Style */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Video Template
                </label>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { value: 'modern', label: 'Modern', desc: 'Clean animations, gradient backgrounds' },
                    { value: 'classic', label: 'Classic', desc: 'Traditional style, professional look' },
                    { value: 'dynamic', label: 'Dynamic', desc: 'High energy, bold transitions' },
                    { value: 'minimal', label: 'Minimal', desc: 'Simple, focused on content' }
                  ].map((template) => (
                    <label key={template.value} className="cursor-pointer">
                      <input
                        type="radio"
                        name="template"
                        value={template.value}
                        checked={localSettings.template === template.value}
                        onChange={(e) => handleChange('template', e.target.value)}
                        className="sr-only"
                      />
                      <div className={`p-4 border-2 rounded-lg transition-all ${
                        localSettings.template === template.value
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                        <div className="font-medium text-sm mb-1">{template.label}</div>
                        <div className="text-xs text-gray-500">{template.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Voice & Audio Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Voice & Audio</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Voice Tone
                  </label>
                  <select
                    value={localSettings.voiceTone}
                    onChange={(e) => handleChange('voiceTone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="exciting">Exciting</option>
                    <option value="calm">Calm</option>
                    <option value="authoritative">Authoritative</option>
                  </select>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localSettings.includeVoiceover}
                      onChange={(e) => handleChange('includeVoiceover', e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Include AI Voiceover
                      <span className="text-gray-500 block text-xs">Professional voice narration for your video</span>
                    </span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localSettings.enableKaraoke}
                      onChange={(e) => handleChange('enableKaraoke', e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Enable Karaoke Text
                      <span className="text-gray-500 block text-xs">Highlight words as they're spoken</span>
                    </span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localSettings.includeMusic}
                      onChange={(e) => handleChange('includeMusic', e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Include Background Music
                      <span className="text-gray-500 block text-xs">Add professional background music to your video</span>
                    </span>
                  </label>

                  {localSettings.includeMusic && (
                    <div className="ml-6 mt-3">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Music Style
                      </label>
                      <select
                        value={localSettings.backgroundMusic}
                        onChange={(e) => handleChange('backgroundMusic', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="corporate">Corporate - Professional business music</option>
                        <option value="energetic">Energetic - High-energy, upbeat music</option>
                        <option value="relaxed">Relaxed - Calm, soothing music</option>
                        <option value="modern">Modern - Contemporary, trendy music</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onBack}
                  className="btn btn-secondary"
                >
                  ← Back to URL
                </button>
                <button
                  type="submit"
                  className="btn btn-primary bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700"
                >
                  Generate Video →
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VideoSettings 