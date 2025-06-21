const ScriptPreview = ({ adScript }) => {
  if (!adScript) return null

  const scriptSections = [
    { key: 'hook', label: 'Hook', icon: '🎣', color: 'text-purple-600' },
    { key: 'problem', label: 'Problem', icon: '⚠️', color: 'text-orange-600' },
    { key: 'solution', label: 'Solution', icon: '💡', color: 'text-blue-600' },
    { key: 'call_to_action', label: 'Call to Action', icon: '🚀', color: 'text-green-600' }
  ]

  const getToneColor = (tone) => {
    switch (tone) {
      case 'exciting': return 'bg-red-100 text-red-800'
      case 'professional': return 'bg-blue-100 text-blue-800'
      case 'friendly': return 'bg-green-100 text-green-800'
      case 'calm': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          AI-Generated Script
        </h3>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getToneColor(adScript.tone)}`}>
            {adScript.tone}
          </span>
          <span className="text-xs text-gray-500">
            ~{adScript.duration_seconds || 15}s
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {scriptSections.map((section) => {
          const content = adScript[section.key]
          if (!content) return null

          return (
            <div key={section.key} className="border-l-4 border-gray-200 pl-4">
              <div className="flex items-center mb-2">
                <span className="text-lg mr-2">{section.icon}</span>
                <h4 className={`font-medium ${section.color}`}>
                  {section.label}
                </h4>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">
                "{content}"
              </p>
            </div>
          )
        })}

        {adScript.benefits && adScript.benefits.length > 0 && (
          <div className="border-l-4 border-gray-200 pl-4">
            <div className="flex items-center mb-2">
              <span className="text-lg mr-2">⭐</span>
              <h4 className="font-medium text-yellow-600">Key Benefits</h4>
            </div>
            <ul className="text-sm text-gray-700 space-y-1">
              {adScript.benefits.map((benefit, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span>"{benefit}"</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Script Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
          <div>
            <span className="font-medium">Target Audience:</span>
            <div className="capitalize">{adScript.target_audience || 'General'}</div>
          </div>
          <div>
            <span className="font-medium">Word Count:</span>
            <div>
              {[adScript.hook, adScript.problem, adScript.solution, adScript.call_to_action]
                .filter(Boolean)
                .join(' ')
                .split(' ').length} words
            </div>
          </div>
        </div>
      </div>

      {/* Full Script Preview */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <h5 className="text-xs font-medium text-gray-900 mb-2">Full Script:</h5>
        <p className="text-xs text-gray-700 leading-relaxed italic">
          "{[adScript.hook, adScript.problem, adScript.solution, adScript.call_to_action]
            .filter(Boolean)
            .join(' ')}"
        </p>
      </div>
    </div>
  )
}

export default ScriptPreview 