/**
 * WebSocket client for the Debug tab (/ws/debug).
 *
 * Independent of the WebRTC connection so the debug channel keeps working
 * during a brownout or a failed video negotiation. Auto-reconnects with a
 * short backoff.
 */
import {
  SerialEventSchema,
  LogRecordSchema,
  HeartbeatStatsSchema,
  PowerSnapshotSchema,
  type SerialEvent,
  type LogRecord,
  type HeartbeatStats,
  type PowerSnapshot,
} from '../types/schemas'

export interface DebugSnapshot {
  serial: SerialEvent[]
  logs: LogRecord[]
  heartbeat: HeartbeatStats
  power: PowerSnapshot
  config: {
    deadman_ms: number
    heartbeat_interval_ms: number
    serial_mock: boolean
  }
}

export interface DebugSocketCallbacks {
  onStatus?: (open: boolean) => void
  onSnapshot?: (snap: DebugSnapshot) => void
  onSerial?: (event: SerialEvent) => void
  onLog?: (record: LogRecord) => void
  onHeartbeat?: (stats: HeartbeatStats) => void
  onPower?: (power: PowerSnapshot) => void
  onArmed?: (armed: boolean) => void
  onError?: (detail: string) => void
}

/** Build the ws:// URL. In dev the Vite proxy forwards /ws to the backend. */
function getDebugWsUrl(): string {
  const path = '/ws/debug'
  if (import.meta.env.PROD) {
    return `ws://${window.location.hostname}:8000${path}`
  }
  return `ws://${window.location.host}${path}`
}

export class DebugSocket {
  private ws: WebSocket | null = null
  private callbacks: DebugSocketCallbacks
  private reconnectTimer: number | null = null
  private closedByUser = false

  constructor(callbacks: DebugSocketCallbacks = {}) {
    this.callbacks = callbacks
  }

  connect(): void {
    this.closedByUser = false
    this.open()
  }

  private open(): void {
    const ws = new WebSocket(getDebugWsUrl())
    this.ws = ws

    ws.onopen = () => this.callbacks.onStatus?.(true)

    ws.onclose = () => {
      this.callbacks.onStatus?.(false)
      if (!this.closedByUser) {
        this.reconnectTimer = window.setTimeout(() => this.open(), 1500)
      }
    }

    ws.onerror = () => ws.close()

    ws.onmessage = event => {
      let data: unknown
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }
      this.dispatch(data as { type?: string } & Record<string, unknown>)
    }
  }

  private dispatch(msg: { type?: string } & Record<string, unknown>): void {
    switch (msg.type) {
      case 'snapshot': {
        this.callbacks.onSnapshot?.({
          serial: SerialEventSchema.array().catch([]).parse(msg.serial ?? []),
          logs: LogRecordSchema.array().catch([]).parse(msg.logs ?? []),
          heartbeat: HeartbeatStatsSchema.parse(msg.heartbeat ?? {}),
          power: PowerSnapshotSchema.parse(msg.power ?? { available: false }),
          config: msg.config as DebugSnapshot['config'],
        })
        break
      }
      case 'serial': {
        const r = SerialEventSchema.safeParse(msg)
        if (r.success) this.callbacks.onSerial?.(r.data)
        break
      }
      case 'log': {
        const r = LogRecordSchema.safeParse(msg)
        if (r.success) this.callbacks.onLog?.(r.data)
        break
      }
      case 'heartbeat': {
        const r = HeartbeatStatsSchema.safeParse(msg)
        if (r.success) this.callbacks.onHeartbeat?.(r.data)
        break
      }
      case 'power': {
        const r = PowerSnapshotSchema.safeParse(msg)
        if (r.success) this.callbacks.onPower?.(r.data)
        break
      }
      case 'armed':
        this.callbacks.onArmed?.(Boolean(msg.value))
        break
      case 'error':
        this.callbacks.onError?.(String(msg.detail ?? 'Unknown error'))
        break
    }
  }

  private send(obj: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj))
    }
  }

  arm(value: boolean): void {
    this.send({ type: 'arm', value })
  }

  motor(index: number, direction: 'forward' | 'backward', speed: number): void {
    this.send({ type: 'motor', index, direction, speed })
  }

  motorStop(index: number | 'all'): void {
    this.send({ type: 'motor_stop', index })
  }

  servo(channel: number, pulse_us: number): void {
    this.send({ type: 'servo', channel, pulse_us })
  }

  estop(): void {
    this.send({ type: 'estop' })
  }

  raw(line: string): void {
    this.send({ type: 'raw', line })
  }

  get isOpen(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  disconnect(): void {
    this.closedByUser = true
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
