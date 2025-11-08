/**
 * Camera settings control panel
 */
import { useState, useEffect } from 'react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'

interface CameraSettings {
  enabled: boolean
  width: number
  height: number
  framerate: number
  flip_180: boolean
  is_noir: boolean
  awb_mode: string
  color_gains: [number, number]
}

const AWB_MODES = [
  { value: 'manual', label: 'Manual (Use Color Gains)' },
  { value: 'auto', label: 'Auto' },
  { value: 'incandescent', label: 'Incandescent' },
  { value: 'tungsten', label: 'Tungsten' },
  { value: 'fluorescent', label: 'Fluorescent' },
  { value: 'indoor', label: 'Indoor' },
  { value: 'daylight', label: 'Daylight' },
  { value: 'cloudy', label: 'Cloudy' },
]

const RESOLUTIONS = [
  { width: 320, height: 240, label: '320x240' },
  { width: 640, height: 480, label: '640x480' },
  { width: 800, height: 600, label: '800x600' },
  { width: 1280, height: 720, label: '1280x720 (HD)' },
  { width: 1920, height: 1080, label: '1920x1080 (Full HD)' },
]

const FRAMERATES = [10, 15, 20, 24, 30, 60]

export function CameraControls() {
  const [settings, setSettings] = useState<CameraSettings | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [needsRestart, setNeedsRestart] = useState(false)

  // Temporary state for form inputs
  const [awbMode, setAwbMode] = useState<string>('manual')
  const [redGain, setRedGain] = useState<number>(1.5)
  const [blueGain, setBlueGain] = useState<number>(1.5)
  const [framerate, setFramerate] = useState<number>(30)
  const [resolution, setResolution] = useState<string>('640x480')

  // Fetch current settings on mount
  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/camera/settings')
      if (!response.ok) throw new Error('Failed to fetch camera settings')
      const data: CameraSettings = await response.json()
      setSettings(data)
      
      // Update form state
      setAwbMode(data.awb_mode)
      setRedGain(data.color_gains[0])
      setBlueGain(data.color_gains[1])
      setFramerate(data.framerate)
      setResolution(`${data.width}x${data.height}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings')
    }
  }

  const updateSettings = async () => {
    setLoading(true)
    setError(null)

    try {
      const [width, height] = resolution.split('x').map(Number)
      
      const response = await fetch('/api/camera/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          awb_mode: awbMode,
          color_gains: [redGain, blueGain],
          framerate,
          width,
          height,
        }),
      })

      if (!response.ok) throw new Error('Failed to update camera settings')
      
      const result = await response.json()
      setNeedsRestart(result.needs_restart)
      setSettings(result.current_settings)
      
      if (!result.needs_restart) {
        // Show success message
        setError(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update settings')
    } finally {
      setLoading(false)
    }
  }

  if (!settings) {
    return (
      <Card className="p-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-satisfactory-cyan rounded-full animate-pulse"></div>
          <span className="text-sm text-muted-foreground">Loading camera settings...</span>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-satisfactory-orange/20">
        <div className="w-1 h-6 bg-satisfactory-cyan"></div>
        <h3 className="text-lg font-bold uppercase tracking-wide">Camera Settings</h3>
      </div>

      <div className="space-y-4">
        {/* AWB Mode */}
        <div>
          <label className="block text-sm font-medium mb-2 text-satisfactory-cyan">
            White Balance Mode
          </label>
          <select
            value={awbMode}
            onChange={(e) => setAwbMode(e.target.value)}
            className="w-full bg-card border border-satisfactory-cyan/30 rounded px-3 py-2 text-sm focus:outline-none focus:border-satisfactory-orange transition-colors"
          >
            {AWB_MODES.map((mode) => (
              <option key={mode.value} value={mode.value}>
                {mode.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground mt-1">
            Set to "Manual" to use color gains below
          </p>
        </div>

        {/* Manual Color Gains */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium mb-2 text-satisfactory-orange">
              Red Gain
            </label>
            <input
              type="number"
              min="0.5"
              max="3.0"
              step="0.1"
              value={redGain}
              onChange={(e) => setRedGain(parseFloat(e.target.value))}
              disabled={awbMode !== 'manual'}
              className="w-full bg-card border border-satisfactory-orange/30 rounded px-3 py-2 text-sm focus:outline-none focus:border-satisfactory-orange transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2 text-satisfactory-orange">
              Blue Gain
            </label>
            <input
              type="number"
              min="0.5"
              max="3.0"
              step="0.1"
              value={blueGain}
              onChange={(e) => setBlueGain(parseFloat(e.target.value))}
              disabled={awbMode !== 'manual'}
              className="w-full bg-card border border-satisfactory-orange/30 rounded px-3 py-2 text-sm focus:outline-none focus:border-satisfactory-orange transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
        </div>
        <p className="text-xs text-muted-foreground -mt-2">
          {awbMode === 'manual' 
            ? 'Color gains active. Increase red to reduce purple/pink tint.'
            : 'Color gains disabled when AWB mode is active'}
        </p>

        {/* Resolution */}
        <div>
          <label className="block text-sm font-medium mb-2 text-satisfactory-cyan">
            Resolution
          </label>
          <select
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
            className="w-full bg-card border border-satisfactory-cyan/30 rounded px-3 py-2 text-sm focus:outline-none focus:border-satisfactory-orange transition-colors"
          >
            {RESOLUTIONS.map((res) => (
              <option key={res.label} value={`${res.width}x${res.height}`}>
                {res.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground mt-1">
            Resolution changes require reconnecting
          </p>
        </div>

        {/* Framerate */}
        <div>
          <label className="block text-sm font-medium mb-2 text-satisfactory-cyan">
            Framerate (FPS)
          </label>
          <select
            value={framerate}
            onChange={(e) => setFramerate(parseInt(e.target.value))}
            className="w-full bg-card border border-satisfactory-cyan/30 rounded px-3 py-2 text-sm focus:outline-none focus:border-satisfactory-orange transition-colors"
          >
            {FRAMERATES.map((fps) => (
              <option key={fps} value={fps}>
                {fps} FPS
              </option>
            ))}
          </select>
        </div>

        {/* Current Settings Display */}
        <div className="bg-satisfactory-panel/30 rounded p-3 border border-satisfactory-cyan/20">
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current:</span>
              <span className="text-satisfactory-cyan font-mono">
                {settings.width}x{settings.height}@{settings.framerate}fps
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">AWB:</span>
              <span className="text-satisfactory-cyan font-mono">{settings.awb_mode}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Gains:</span>
              <span className="text-satisfactory-orange font-mono">
                R:{settings.color_gains[0].toFixed(1)} B:{settings.color_gains[1].toFixed(1)}
              </span>
            </div>
          </div>
        </div>

        {/* Error/Warning Messages */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {needsRestart && (
          <div className="bg-satisfactory-orange/10 border border-satisfactory-orange/50 rounded p-3 text-sm text-satisfactory-orange">
            ⚠️ Resolution changed. Reconnect video to apply.
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <Button
            onClick={updateSettings}
            disabled={loading}
            className="flex-1 bg-satisfactory-orange hover:bg-satisfactory-orange/80"
          >
            {loading ? 'Applying...' : 'Apply Settings'}
          </Button>
          <Button
            onClick={fetchSettings}
            variant="outline"
            className="border-satisfactory-cyan/30 hover:border-satisfactory-cyan"
          >
            Refresh
          </Button>
        </div>
      </div>
    </Card>
  )
}
