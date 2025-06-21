import React from 'react'
import VideoGenerator from './VideoGenerator'

const Hero = ({ onGetStarted }) => {
  return (
    <section className="relative bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="flex items-center space-x-2 bg-white rounded-full px-4 py-2 shadow-sm border">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-sm text-gray-600">AI-Powered Video Generation</span>
            </div>
          </div>
          
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
            Transform Any
            <span className="block bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Product URL into Video Ads
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Paste any e-commerce URL and watch our AI create compelling 15-second video advertisements 
            with professional voiceover, animations, and persuasive scripts.
          </p>
          
          <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-12">
            <button 
              onClick={onGetStarted}
              className="btn btn-primary text-lg px-8 py-4 bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h1m4 0h1m-6 4h1m4 0h1M9 10h1m4 0h1m-6 4h1m4 0h1" />
              </svg>
              Create Video Now - Free
            </button>
            <button className="btn btn-secondary text-lg px-8 py-4 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h1m4 0h1m-6 4h1m4 0h1M9 10h1m4 0h1m-6 4h1m4 0h1" />
              </svg>
              Watch Demo
            </button>
          </div>

          {/* Feature badges */}
          <div className="flex flex-wrap justify-center items-center gap-6 text-sm text-gray-600 mb-12">
            <div className="flex items-center space-x-2 bg-white rounded-lg px-3 py-2 shadow-sm">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                </svg>
              </div>
              <span className="font-medium">eBay & Shopify</span>
            </div>
            <div className="flex items-center space-x-2 bg-white rounded-lg px-3 py-2 shadow-sm">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <span className="font-medium">AI Voiceover</span>
            </div>
            <div className="flex items-center space-x-2 bg-white rounded-lg px-3 py-2 shadow-sm">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <span className="font-medium">15-Second Ads</span>
            </div>
            <div className="flex items-center space-x-2 bg-white rounded-lg px-3 py-2 shadow-sm">
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <span className="font-medium">Multiple Formats</span>
            </div>
          </div>

          {/* Sample URL Examples */}
          <div className="bg-white rounded-2xl p-8 shadow-lg max-w-4xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Try with these sample URLs:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="text-left">
                <p className="text-sm font-medium text-gray-700 mb-2">eBay Products:</p>
                <div className="space-y-2">
                  <code className="block text-xs bg-gray-100 p-2 rounded text-gray-600 break-all">
                    https://www.ebay.com/itm/146412308093?_trkparms=5373%3A0%7C5374%3AFeatured
                  </code>
                  <code className="block text-xs bg-gray-100 p-2 rounded text-gray-600 break-all">
                    https://www.ebay.com/itm/167017920229?_trkparms=5373%3A0%7C5374%3AFeatured%7C5079%3A6000007364
                  </code>
                </div>
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-700 mb-2">eBay Categories:</p>
                <div className="space-y-2">
                  <code className="block text-xs bg-gray-100 p-2 rounded text-gray-600 break-all">
                    https://www.ebay.com/b/Jordan-1-Retro-OG-High-UNC-Toe/15709/bn_7119139207
                  </code>
                </div>
              </div>
            </div>
          </div>

          {/* Video Generator Component */}
          <div className="mt-12">
            <VideoGenerator />
          </div>
        </div>
      </div>

      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-200 rounded-full opacity-20"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-200 rounded-full opacity-20"></div>
        <div className="absolute top-20 left-20 w-32 h-32 bg-indigo-200 rounded-full opacity-10"></div>
      </div>
    </section>
  )
}

export default Hero 