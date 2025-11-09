/**
 * Connection controls with Satisfactory-themed status indicators
 */
import { useState } from 'react'
import { useAppStore } from '@/store'
import { Button } from './ui/Button'
import { WebRTCManager, getApiUrl } from '@/utils/webrtc'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'
import { CameraSettingsSchema } from '@/types/schemas'

export function ConnectionControls() {
  const [isConnecting, setIsConnecting] = useState(false)
  const connectionState = useAppStore(state => state.connectionState)
  const setConnectionState = useAppStore(state => state.setConnectionState)
  const updateSystemMetrics = useAppStore(state => state.updateSystemMetrics)
  const setVideoStream = useAppStore(state => state.setVideoStream)
  const setCameraSettings = useAppStore(state => state.setCameraSettings)
  const webrtc = useAppStore(state => state.webrtc)
  const setWebRTC = useAppStore(state => state.setWebRTC)

  const handleConnect = async () => {
    try {
      setIsConnecting(true)
      setConnectionState('connecting')

      // Fetch camera settings to get the correct resolution
      try {
        const response = await fetch(getApiUrl('/api/camera/settings'))
        if (response.ok) {
          const data = await response.json()
          const settings = CameraSettingsSchema.parse(data)
          setCameraSettings(settings)
        }
      } catch (error) {
        console.error('Failed to fetch camera settings:', error)
      }

      // Create WebRTC manager
      const manager = new WebRTCManager({
        onConnectionStateChange: state => {
          console.log('Connection state changed:', state)
          if (state === 'connected') {
            setConnectionState('connected')
          } else if (state === 'failed' || state === 'closed') {
            setConnectionState('disconnected')
          }
        },
        onSystemMetrics: data => {
          updateSystemMetrics(data)
        },
        onTrack: track => {
          // Create MediaStream from track
          const stream = new MediaStream([track])
          setVideoStream(stream)
        },
      })

      await manager.connect()
      setWebRTC(manager) // Store in global state
    } catch (error) {
      console.error('Connection failed:', error)
      setConnectionState('failed')
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    if (webrtc) {
      await webrtc.disconnect()
      setWebRTC(null)
    }
    setVideoStream(null)
    setConnectionState('disconnected')
  }

  const isConnected = connectionState === 'connected'

  return (
    <div className="flex items-center gap-4">
      {/* Status indicator with industrial styling */}
      <div className="flex items-center gap-2 px-3 py-1 rounded bg-satisfactory-panel border border-satisfactory-panel-border">
        {connectionState === 'connecting' || isConnecting ? (
          <Loader2 className="w-5 h-5 animate-spin text-satisfactory-cyan" />
        ) : isConnected ? (
          <div className="relative">
            <Wifi className="w-5 h-5 text-green-500" />
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full status-online"></div>
          </div>
        ) : (
          <WifiOff className="w-5 h-5 text-gray-500" />
        )}
        <span className="text-sm font-bold uppercase tracking-wider">
          {connectionState === 'connecting' ? (
            <span className="text-satisfactory-cyan">Linking...</span>
          ) : isConnected ? (
            <span className="text-green-500">Online</span>
          ) : (
            <span className="text-gray-500">Offline</span>
          )}
        </span>
      </div>

      {/* Connect/Disconnect button */}
      {isConnected ? (
        <Button variant="destructive" onClick={handleDisconnect} size="sm">
          Disconnect
        </Button>
      ) : (
        <Button onClick={handleConnect} disabled={isConnecting || connectionState === 'connecting'} size="sm">
          {isConnecting || connectionState === 'connecting' ? 'Connecting...' : 'Connect'}
        </Button>
      )}
    </div>
  )
}

