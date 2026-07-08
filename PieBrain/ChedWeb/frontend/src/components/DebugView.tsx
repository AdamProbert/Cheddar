/**
 * Debug tab - direct actuator control + live link/power/serial diagnostics.
 * Owns the /ws/debug connection and fans state out to the panels.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { DebugSocket } from '@/utils/debugSocket'
import type { SerialEvent, LogRecord, HeartbeatStats, PowerSnapshot } from '@/types/schemas'
import { ActuatorControls } from './debug/ActuatorControls'
import { SerialConsole } from './debug/SerialConsole'
import { HeartbeatCard } from './debug/HeartbeatCard'
import { PowerCard } from './debug/PowerCard'
import { CurrentDrawCard } from './debug/CurrentDrawCard'
import { ShieldAlert, ShieldCheck, Square } from 'lucide-react'

const MAX_SERIAL = 400
const MAX_RTT = 60

export interface RttPoint {
  i: number
  rtt: number
}

export function DebugView() {
  const socketRef = useRef<DebugSocket | null>(null)
  const [wsOpen, setWsOpen] = useState(false)
  const [armed, setArmed] = useState(false)
  const [serial, setSerial] = useState<SerialEvent[]>([])
  const [, setLogs] = useState<LogRecord[]>([])
  const [heartbeat, setHeartbeat] = useState<HeartbeatStats>({})
  const [power, setPower] = useState<PowerSnapshot>({ available: false })
  const [rttHistory, setRttHistory] = useState<RttPoint[]>([])
  const [lastError, setLastError] = useState<string | null>(null)
  const rttCounter = useRef(0)

  const pushRtt = useCallback((rtt: number | null | undefined) => {
    if (rtt === null || rtt === undefined) return
    setRttHistory(prev => {
      const next = [...prev, { i: rttCounter.current++, rtt }]
      return next.slice(-MAX_RTT)
    })
  }, [])

  useEffect(() => {
    const socket = new DebugSocket({
      onStatus: setWsOpen,
      onSnapshot: snap => {
        setSerial(snap.serial.slice(-MAX_SERIAL))
        setLogs(snap.logs)
        setHeartbeat(snap.heartbeat)
        setPower(snap.power)
        pushRtt(snap.heartbeat.rtt_ms)
      },
      onSerial: evt => setSerial(prev => [...prev, evt].slice(-MAX_SERIAL)),
      onLog: rec => setLogs(prev => [...prev, rec].slice(-300)),
      onHeartbeat: hb => {
        setHeartbeat(hb)
        pushRtt(hb.rtt_ms)
      },
      onPower: setPower,
      onArmed: setArmed,
      onError: detail => setLastError(detail),
    })
    socketRef.current = socket
    socket.connect()
    return () => socket.disconnect()
  }, [pushRtt])

  const socket = socketRef.current

  return (
    <div className="space-y-6">
      {/* Safety strip */}
      <div
        className="flex flex-wrap items-center gap-4 rounded border border-destructive/40 bg-gradient-to-r from-destructive/10 to-transparent p-3"
        style={{ borderLeftWidth: 3, borderLeftColor: 'hsl(var(--destructive))' }}
      >
        <button
          onClick={() => socket?.estop()}
          className="inline-flex items-center gap-2 rounded bg-destructive px-6 py-3 font-black uppercase tracking-widest text-white shadow-lg transition-transform active:scale-95"
        >
          <Square className="h-4 w-4 fill-current" />
          E-Stop
        </button>

        <button
          onClick={() => socket?.arm(!armed)}
          className={`inline-flex items-center gap-3 rounded border px-3 py-2 transition-colors ${
            armed
              ? 'border-satisfactory-cyan/50 bg-satisfactory-cyan/10'
              : 'border-satisfactory-panel-border bg-satisfactory-panel'
          }`}
        >
          {armed ? (
            <ShieldCheck className="h-5 w-5 text-satisfactory-cyan" />
          ) : (
            <ShieldAlert className="h-5 w-5 text-satisfactory-yellow" />
          )}
          <span className="text-left">
            <span
              className={`block text-xs font-bold uppercase tracking-widest ${
                armed ? 'text-satisfactory-cyan' : 'text-satisfactory-yellow'
              }`}
            >
              {armed ? 'Motors Armed' : 'Motors Disarmed'}
            </span>
            <span className="block text-xs text-muted-foreground">
              {armed ? 'Direct motor drive enabled' : 'Arm to enable direct motor drive'}
            </span>
          </span>
        </button>

        <div className="flex-1" />
        <p className="max-w-sm text-xs text-muted-foreground">
          Direct commands bypass drive-mode mixing. Servos hold position; motors auto-stop after{' '}
          {(heartbeat.deadman_ms ?? 1000) / 1000}s of silence (firmware deadman).
        </p>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ActuatorControls
            armed={armed}
            connected={wsOpen}
            onMotor={(i, dir, speed) => socket?.motor(i, dir, speed)}
            onMotorStop={i => socket?.motorStop(i)}
            onServo={(ch, us) => socket?.servo(ch, us)}
          />
          <SerialConsole
            events={serial}
            connected={wsOpen}
            lastError={lastError}
            onSend={line => {
              setLastError(null)
              socket?.raw(line)
            }}
          />
        </div>

        <div className="space-y-6">
          <HeartbeatCard heartbeat={heartbeat} rttHistory={rttHistory} connected={wsOpen} />
          <PowerCard power={power} />
          <CurrentDrawCard />
        </div>
      </div>
    </div>
  )
}
