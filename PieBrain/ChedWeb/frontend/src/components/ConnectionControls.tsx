/**
 * Connection controls and status display
 */
import { useState } from 'react'
import { useAppStore } from '@/store'
import { Button } from './ui/Button'
import { WebRTCManager } from '@/utils/webrtc'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'

let webrtcManager: WebRTCManager | null = null

export function ConnectionControls() {
  const [isConnecting, setIsConnecting] = useState(false)
  const connectionState = useAppStore(state => state.connectionState)
  const setConnectionState = useAppStore(state => state.setConnectionState)
  const updateTelemetry = useAppStore(state => state.updateTelemetry)
  const updateSystemMetrics = useAppStore(state => state.updateSystemMetrics)
  const setVideoStream = useAppStore(state => state.setVideoStream)

  const handleConnect = async () => {
    try {
      setIsConnecting(true)
      setConnectionState('connecting')

      // Create WebRTC manager
      webrtcManager = new WebRTCManager({
        onConnectionStateChange: state => {
          console.log('Connection state changed:', state)
          if (state === 'connected') {
            setConnectionState('connected')
          } else if (state === 'failed' || state === 'closed') {
            setConnectionState('disconnected')
          }
        },
        onTelemetry: data => {
          updateTelemetry(data)
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

      await webrtcManager.connect()
    } catch (error) {
      console.error('Connection failed:', error)
      setConnectionState('failed')
    } finally {
      setIsConnecting(false)
    }
  }

  const handleDisconnect = async () => {
    if (webrtcManager) {
      await webrtcManager.disconnect()
      webrtcManager = null
    }
    setVideoStream(null)
    setConnectionState('disconnected')
  }

  const isConnected = connectionState === 'connected'

  return (
    <div className="flex items-center gap-4">
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        {connectionState === 'connecting' || isConnecting ? (
          <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
        ) : isConnected ? (
          <Wifi className="w-5 h-5 text-green-500" />
        ) : (
          <WifiOff className="w-5 h-5 text-gray-400" />
        )}
        <span className="text-sm font-medium capitalize">{connectionState}</span>
      </div>

      {/* Connect/Disconnect button */}
      {isConnected ? (
        <Button variant="destructive" onClick={handleDisconnect}>
          Disconnect
        </Button>
      ) : (
        <Button onClick={handleConnect} disabled={isConnecting || connectionState === 'connecting'}>
          {isConnecting || connectionState === 'connecting' ? 'Connecting...' : 'Connect'}
        </Button>
      )}
    </div>
  )
}
