/**
 * Zustand store for application state management
 */
import { create } from 'zustand'
import type { ConfigResponse, SystemMetrics, CameraSettings } from './types/schemas'
import { WebRTCManager } from './utils/webrtc'

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

  // WebRTC Manager
  webrtc: WebRTCManager | null
  setWebRTC: (manager: WebRTCManager | null) => void

  // System Metrics
  systemMetrics: SystemMetrics | null
  metricsHistory: MetricsHistoryPoint[]
  updateSystemMetrics: (data: SystemMetrics) => void

  // Video
  videoStream: MediaStream | null
  setVideoStream: (stream: MediaStream | null) => void

  // Camera
  cameraSettings: CameraSettings | null
  setCameraSettings: (settings: CameraSettings) => void

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

  // WebRTC Manager
  webrtc: null,
  setWebRTC: manager => set({ webrtc: manager }),

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

  // Camera
  cameraSettings: null,
  setCameraSettings: settings => set({ cameraSettings: settings }),

  // Config
  config: null,
  setConfig: config => set({ config }),

  // Gamepad
  gamepadConnected: false,
  setGamepadConnected: connected => set({ gamepadConnected: connected }),
}))
