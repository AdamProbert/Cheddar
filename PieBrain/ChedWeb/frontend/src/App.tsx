/**
 * Main App component with Satisfactory-themed design
 */
import { ConnectionControls } from './components/ConnectionControls'
import { VideoFeed } from './components/VideoFeed'
import { SystemMetricsCard } from './components/SystemMetricsCard'
import { CameraControls } from './components/CameraControls'
import { RoverControls } from './components/RoverControls'
import { DebugView } from './components/DebugView'
import { useAppStore, type ActiveTab } from './store'
import { Gamepad2, Wrench } from 'lucide-react'

const TABS: { id: ActiveTab; label: string; icon: typeof Gamepad2 }[] = [
  { id: 'control', label: 'Control', icon: Gamepad2 },
  { id: 'debug', label: 'Debug', icon: Wrench },
]

function App() {
  const activeTab = useAppStore(state => state.activeTab)
  const setActiveTab = useAppStore(state => state.setActiveTab)

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

      {/* Tab navigation */}
      <nav className="border-b border-satisfactory-panel-border bg-card/40">
        <div className="container mx-auto flex gap-8 px-4">
          {TABS.map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                aria-selected={active}
                className={`flex items-center gap-2 border-b-2 py-3 text-sm font-bold uppercase tracking-widest transition-colors ${
                  active
                    ? 'border-satisfactory-orange text-satisfactory-orange'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {activeTab === 'control' ? (
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
        ) : (
          <div className="animate-slide-in">
            <DebugView />
          </div>
        )}
      </main>
    </div>
  )
}

export default App
