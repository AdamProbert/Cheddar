/**
 * Zustand store for application state management
 */
import { create } from 'zustand'
import type { TelemetryData, ConfigResponse } from './types/schemas'

export type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'failed'
  | 'closed'

interface AppState {
  // Connection
  connectionState: ConnectionState
  setConnectionState: (state: ConnectionState) => void

  // Telemetry
  telemetry: TelemetryData | null
  updateTelemetry: (data: TelemetryData) => void
  latency: number | null
  setLatency: (latency: number) => void

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
    set(state => {
      // Calculate latency if this is a pong response
      if (data.type === 'pong' && data.latency_ms !== undefined) {
        return { telemetry: data, latency: data.latency_ms }
      }
      return { telemetry: data }
    }),
  latency: null,
  setLatency: latency => set({ latency }),

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
