/**
 * Main App component
 */
import { ConnectionControls } from './components/ConnectionControls'
import { VideoFeed } from './components/VideoFeed'
import { TelemetryCard } from './components/TelemetryCard'

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">ChedWeb Rover Control</h1>
            <ConnectionControls />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Feed - takes 2 columns on large screens */}
          <div className="lg:col-span-2">
            <VideoFeed />
          </div>

          {/* Sidebar - telemetry and controls */}
          <div className="space-y-6">
            <TelemetryCard />

            {/* TODO: Add gamepad status card */}
            {/* TODO: Add manual control buttons as fallback */}
            {/* TODO: Add settings/config panel */}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
