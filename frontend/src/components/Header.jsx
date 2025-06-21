import { useState } from 'react'

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  VideoAI
                </h1>
                <p className="text-xs text-gray-500">URL to Video</p>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            <a href="#generator" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium transition-colors">
              Generator
            </a>
            <a href="#examples" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium transition-colors">
              Examples
            </a>
            <a href="#pricing" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium transition-colors">
              Pricing
            </a>
            <a href="#docs" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium transition-colors">
              API Docs
            </a>
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center space-x-4">
            <button className="btn btn-secondary">
              Sign In
            </button>
            <button className="btn btn-primary bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700">
              Try Free
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-600 hover:text-purple-600 p-2"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <div className="flex flex-col space-y-2">
              <a href="#generator" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium">
                Generator
              </a>
              <a href="#examples" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium">
                Examples
              </a>
              <a href="#pricing" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium">
                Pricing
              </a>
              <a href="#docs" className="text-gray-600 hover:text-purple-600 px-3 py-2 text-sm font-medium">
                API Docs
              </a>
              <div className="flex flex-col space-y-2 pt-2">
                <button className="btn btn-secondary w-full">
                  Sign In
                </button>
                <button className="btn btn-primary w-full bg-gradient-to-r from-purple-500 to-blue-600">
                  Try Free
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header 