/**
 * Main App component with Satisfactory-themed design
 */
import { ConnectionControls } from './components/ConnectionControls'
import { VideoFeed } from './components/VideoFeed'
import { SystemMetricsCard } from './components/SystemMetricsCard'
import { CameraControls } from './components/CameraControls'
import { RoverControls } from './components/RoverControls'

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header with industrial aesthetic */}
      <header className="border-b-2 border-satisfactory-orange bg-gradient-to-r from-satisfactory-panel via-card to-satisfactory-panel shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-8 bg-satisfactory-orange animate-pulse-glow"></div>
              <h1 className="text-2xl font-bold tracking-wider uppercase">
                <span className="text-satisfactory-orange">Ched</span>
                <span className="text-satisfactory-cyan">Web</span>
                <span className="text-muted-foreground ml-2">// Rover Control</span>
              </h1>
            </div>
            <ConnectionControls />
          </div>
        </div>
      </header>

      {/* Main Content with grid layout */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Video and Rover Controls */}
          <div className="lg:col-span-2 space-y-6">
            <div className="animate-slide-in">
              <VideoFeed />
            </div>
            <div className="animate-slide-in" style={{ animationDelay: '0.1s' }}>
              <RoverControls />
            </div>
          </div>

          {/* Right sidebar - System info and camera controls */}
          <div className="space-y-6">
            <div className="animate-slide-in" style={{ animationDelay: '0.2s' }}>
              <SystemMetricsCard />
            </div>
            <div className="animate-slide-in" style={{ animationDelay: '0.3s' }}>
              <CameraControls />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
