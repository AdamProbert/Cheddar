/**
 * Rover control panel - displays input status and manual controls
 */
import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { Button } from './ui/Button'
import { useAppStore } from '../store'
import { InputManager, type RoverInputState, type DriveMode } from '../utils/inputManager'
import { Gamepad2 } from 'lucide-react'

const DRIVE_MODE_LABELS: Record<DriveMode, string> = {
  ackermann: 'Ackermann',
  crab: 'Crab/Strafe',
  tank: 'Tank',
  spin: 'Spin Turn',
  'point-turn': 'Point Turn',
}

const DRIVE_MODE_DESCRIPTIONS: Record<DriveMode, string> = {
  ackermann: 'Car-like: front wheels steer',
  crab: 'Strafe: all wheels same angle',
  tank: 'Differential: left vs right',
  spin: 'Rotate: spin around center',
  'point-turn': 'Pivot: around middle wheels',
}

export function RoverControls() {
  const [inputState, setInputState] = useState<RoverInputState | null>(null)
  const [gamepadConnected, setGamepadConnected] = useState(false)
  const [inputManager] = useState(() => new InputManager())
  const { webrtc, connectionState } = useAppStore()
  
  const isConnected = connectionState === 'connected'
  
  useEffect(() => {
    if (!isConnected || !webrtc) return
    
    console.log('[RoverControls] Starting input manager...')
    
    // Start input manager
    inputManager.start((state) => {
      setInputState(state)
      
      // Send command via WebRTC
      if (state.emergencyStop) {
        webrtc.sendCommand({ type: 'estop' })
      } else {
        webrtc.sendCommand({
          type: 'motor',
          motors: [...state.motors],
          servos: [...state.servos],
        })
      }
    })
    
    // Poll gamepad connection status
    const interval = setInterval(() => {
      const connected = inputManager.isGamepadConnected()
      setGamepadConnected(prevConnected => {
        if (connected !== prevConnected) {
          console.log('[RoverControls] Gamepad connection changed:', connected)
        }
        return connected
      })
    }, 500)
    
    return () => {
      inputManager.stop()
      clearInterval(interval)
    }
  }, [isConnected, webrtc, inputManager])
  
  const handleEmergencyStop = () => {
    if (!webrtc) return
    webrtc.sendCommand({ type: 'estop' })
  }
  
  const handleStopAll = () => {
    if (!webrtc) return
    webrtc.sendCommand({ type: 'stop' })
  }
  
  const handleDriveModeChange = (mode: DriveMode) => {
    inputManager.setDriveMode(mode)
  }
  
  // Format motor speed for display
  const formatSpeed = (speed: number): string => {
    const percent = Math.round(speed * 100)
    return percent >= 0 ? `+${percent}%` : `${percent}%`
  }
  
  // Format servo angle for display
  const formatAngle = (angle: number): string => {
    return `${Math.round(angle)}°`
  }
  
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Gamepad2 className="w-5 h-5 text-satisfactory-orange" />
            Rover Controls
          </div>
          {gamepadConnected && (
            <div className="flex items-center gap-2 text-sm text-satisfactory-cyan font-normal">
              <div className="w-2 h-2 bg-satisfactory-cyan rounded-full animate-pulse-glow"></div>
              Gamepad
            </div>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        
        {!isConnected && (
          <div className="text-sm text-muted-foreground">
            Connect to rover to enable controls
          </div>
        )}
        
        {isConnected && (
          <>
            {/* Drive Mode Selection */}
            {inputState && (
              <div className="p-3 bg-satisfactory-panel/50 rounded border border-satisfactory-cyan/30">
                <div className="text-sm font-semibold text-satisfactory-cyan mb-2 uppercase">
                  Drive Mode: {DRIVE_MODE_LABELS[inputState.driveMode]}
                </div>
                <div className="text-xs text-muted-foreground mb-3">
                  {DRIVE_MODE_DESCRIPTIONS[inputState.driveMode]}
                </div>
                <div className="grid grid-cols-3 gap-1">
                  {(Object.keys(DRIVE_MODE_LABELS) as DriveMode[]).map((mode) => (
                    <Button
                      key={mode}
                      size="sm"
                      variant={inputState.driveMode === mode ? 'default' : 'outline'}
                      onClick={() => handleDriveModeChange(mode)}
                      className="text-xs h-8"
                    >
                      {DRIVE_MODE_LABELS[mode]}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Emergency Controls */}
            <div className="grid grid-cols-2 gap-2">
              <Button
                onClick={handleEmergencyStop}
                variant="destructive"
                className="bg-red-600 hover:bg-red-700 font-bold"
              >
                E-STOP
              </Button>
              <Button
                onClick={handleStopAll}
                variant="outline"
              >
                Stop All
              </Button>
            </div>
            
            {/* Motor & Servo Status */}
            {inputState && (
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-semibold text-satisfactory-cyan mb-2 uppercase">
                    Wheel Status
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                    {/* Left Side */}
                    <div className="space-y-1">
                      <div className="text-muted-foreground font-bold">Left Side</div>
                      <div className="flex justify-between">
                        <span>FL:</span>
                        <span className={inputState.motors[0] !== 0 ? 'text-satisfactory-cyan' : ''}>
                          {formatSpeed(inputState.motors[0])} @ {formatAngle(inputState.servos[0])}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>ML:</span>
                        <span className={inputState.motors[2] !== 0 ? 'text-satisfactory-cyan' : ''}>
                          {formatSpeed(inputState.motors[2])} @ {formatAngle(inputState.servos[2])}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>RL:</span>
                        <span className={inputState.motors[4] !== 0 ? 'text-satisfactory-cyan' : ''}>
                          {formatSpeed(inputState.motors[4])} @ {formatAngle(inputState.servos[4])}
                        </span>
                      </div>
                    </div>
                    {/* Right Side */}
                    <div className="space-y-1">
                      <div className="text-muted-foreground font-bold">Right Side</div>
                      <div className="flex justify-between">
                        <span>FR:</span>
                        <span className={inputState.motors[1] !== 0 ? 'text-satisfactory-cyan' : ''}>
                          {formatSpeed(inputState.motors[1])} @ {formatAngle(inputState.servos[1])}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>MR:</span>
                        <span className={inputState.motors[3] !== 0 ? 'text-satisfactory-cyan' : ''}>
                          {formatSpeed(inputState.motors[3])} @ {formatAngle(inputState.servos[3])}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>RR:</span>
                        <span className={inputState.motors[5] !== 0 ? 'text-satisfactory-cyan' : ''}>
                          {formatSpeed(inputState.motors[5])} @ {formatAngle(inputState.servos[5])}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Control Help */}
            <div className="mt-4 p-3 bg-muted/10 rounded border border-muted/30 text-xs space-y-2">
              <div className="font-semibold text-satisfactory-orange">Controls:</div>
              <div className="space-y-1 text-muted-foreground">
                {gamepadConnected ? (
                  <>
                    <div><strong>Left Stick:</strong> Forward/Backward</div>
                    <div><strong>Right Stick X:</strong> Turn/Steer</div>
                    <div><strong>D-Pad:</strong> Change Drive Mode</div>
                    <div><strong>B Button:</strong> Emergency Stop</div>
                  </>
                ) : (
                  <>
                    <div><strong>W/S or ↑/↓:</strong> Forward/Backward</div>
                    <div><strong>A/D or ←/→:</strong> Turn/Steer</div>
                    <div><strong>1-5:</strong> Drive Modes (Ackermann/Crab/Tank/Spin/Point)</div>
                    <div><strong>Space/Esc:</strong> Emergency Stop</div>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
