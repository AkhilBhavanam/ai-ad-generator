import { useState } from 'react'
import Header from './components/Header'
import Hero from './components/Hero'
import VideoGenerator from './components/VideoGenerator'
import Footer from './components/Footer'
import { ToastProvider } from './components/ToastProvider'

function App() {
  const [showGenerator, setShowGenerator] = useState(false)

  return (
    <ToastProvider>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main>
          {!showGenerator ? (
            <Hero onGetStarted={() => setShowGenerator(true)} />
          ) : (
            <VideoGenerator />
          )}
        </main>
        <Footer />
      </div>
    </ToastProvider>
  )
}

export default App 