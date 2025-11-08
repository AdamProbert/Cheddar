/**
 * Zustand store for application state management
 */
import { create } from 'zustand'
import type { TelemetryData, ConfigResponse, SystemMetrics } from './types/schemas'

export type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'failed'
  | 'closed'

// Historical metrics data point (for time-series charts)
export interface MetricsHistoryPoint {
  timestamp: number
  cpu_percent: number
  memory_percent: number
  cpu_temp: number | null
  disk_percent: number | null
}

// Keep last N data points (60 points = 1 minute at 1Hz)
const MAX_HISTORY_POINTS = 60

interface AppState {
  // Connection
  connectionState: ConnectionState
  setConnectionState: (state: ConnectionState) => void

  // Telemetry
  telemetry: TelemetryData | null
  updateTelemetry: (data: TelemetryData) => void
  latency: number | null
  setLatency: (latency: number) => void

  // System Metrics
  systemMetrics: SystemMetrics | null
  metricsHistory: MetricsHistoryPoint[]
  updateSystemMetrics: (data: SystemMetrics) => void

  // Video
  videoStream: MediaStream | null
  setVideoStream: (stream: MediaStream | null) => void

  // Config
  config: ConfigResponse | null
  setConfig: (config: ConfigResponse) => void

  // Gamepad
  gamepadConnected: boolean
  setGamepadConnected: (connected: boolean) => void
}

export const useAppStore = create<AppState>(set => ({
  // Connection
  connectionState: 'disconnected',
  setConnectionState: state => set({ connectionState: state }),

  // Telemetry
  telemetry: null,
  updateTelemetry: data =>
    set(_state => {
      // Calculate latency if this is a pong response
      if (data.type === 'pong' && data.latency_ms !== undefined) {
        return { telemetry: data, latency: data.latency_ms }
      }
      return { telemetry: data }
    }),
  latency: null,
  setLatency: latency => set({ latency }),

  // System Metrics
  systemMetrics: null,
  metricsHistory: [],
  updateSystemMetrics: data =>
    set(state => {
      // Create new history point
      const newPoint: MetricsHistoryPoint = {
        timestamp: data.timestamp,
        cpu_percent: data.cpu_percent,
        memory_percent: data.memory_percent,
        cpu_temp: data.cpu_temp ?? null,
        disk_percent: data.disk_percent ?? null,
      }

      // Add to history and keep only last MAX_HISTORY_POINTS
      const newHistory = [...state.metricsHistory, newPoint].slice(-MAX_HISTORY_POINTS)

      return {
        systemMetrics: data,
        metricsHistory: newHistory,
      }
    }),

  // Video
  videoStream: null,
  setVideoStream: stream => set({ videoStream: stream }),

  // Config
  config: null,
  setConfig: config => set({ config }),

  // Gamepad
  gamepadConnected: false,
  setGamepadConnected: connected => set({ gamepadConnected: connected }),
}))
