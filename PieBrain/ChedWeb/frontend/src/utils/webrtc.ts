/**
 * WebRTC peer connection and DataChannel management
 */
import axios from 'axios'
import type { SDPOffer, SDPAnswer, ControlCommand, TelemetryData, SystemMetrics } from '../types/schemas'
import { TelemetryDataSchema, SystemMetricsSchema } from '../types/schemas'

// Use relative URL to go through Vite proxy in dev, or same origin in production
const API_BASE = ''

export interface WebRTCCallbacks {
  onConnectionStateChange?: (state: RTCPeerConnectionState) => void
  onTelemetry?: (data: TelemetryData) => void
  onSystemMetrics?: (data: SystemMetrics) => void
  onTrack?: (track: MediaStreamTrack) => void
}

export class WebRTCManager {
  private pc: RTCPeerConnection | null = null
  private dataChannel: RTCDataChannel | null = null
  private callbacks: WebRTCCallbacks

  constructor(callbacks: WebRTCCallbacks = {}) {
    this.callbacks = callbacks
  }

  async connect(): Promise<void> {
    // Create peer connection
    this.pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    })

    // Connection state monitoring
    this.pc.onconnectionstatechange = () => {
      if (this.pc) {
        console.log('Connection state:', this.pc.connectionState)
        this.callbacks.onConnectionStateChange?.(this.pc.connectionState)
      }
    }

    // Track handling (for video stream)
    this.pc.ontrack = event => {
      console.log('Received track:', event.track.kind)
      this.callbacks.onTrack?.(event.track)
    }

    // Add transceiver for receiving video from server (one-way video)
    this.pc.addTransceiver('video', { direction: 'recvonly' })

    // Create DataChannel for control commands
    this.dataChannel = this.pc.createDataChannel('control', {
      ordered: true,
    })

    this.setupDataChannel()

    // Create and send offer
    const offer = await this.pc.createOffer()
    await this.pc.setLocalDescription(offer)

    // Send offer to backend and get answer
    const sdpOffer: SDPOffer = {
      sdp: offer.sdp!,
      type: 'offer',
    }

    const response = await axios.post<SDPAnswer>(`${API_BASE}/signaling/offer`, sdpOffer)
    const answer = response.data

    // Set remote description
    await this.pc.setRemoteDescription({
      type: 'answer',
      sdp: answer.sdp,
    })

    console.log('WebRTC connection established')
  }

  private setupDataChannel(): void {
    if (!this.dataChannel) return

    this.dataChannel.onopen = () => {
      console.log('DataChannel opened')
      // Send initial ping to measure latency
      this.sendPing()
    }

    this.dataChannel.onmessage = event => {
      try {
        const data = JSON.parse(event.data)
        
        // Try to parse as system metrics first
        const metricsResult = SystemMetricsSchema.safeParse(data)
        if (metricsResult.success) {
          this.callbacks.onSystemMetrics?.(metricsResult.data)
          return
        }

        // Otherwise parse as telemetry
        const telemetry = TelemetryDataSchema.parse(data)
        this.callbacks.onTelemetry?.(telemetry)
      } catch (error) {
        console.error('Failed to parse DataChannel message:', error)
      }
    }

    this.dataChannel.onerror = error => {
      console.error('DataChannel error:', error)
    }

    this.dataChannel.onclose = () => {
      console.log('DataChannel closed')
      // TODO: Implement deadman switch / reconnection logic
    }
  }

  sendCommand(command: Omit<ControlCommand, 'timestamp'>): void {
    if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
      console.warn('DataChannel not ready, command not sent')
      return
    }

    const fullCommand: ControlCommand = {
      ...command,
      timestamp: Date.now(),
    }

    this.dataChannel.send(JSON.stringify(fullCommand))
  }

  sendPing(): void {
    if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
      return
    }

    this.dataChannel.send(
      JSON.stringify({
        type: 'ping',
        timestamp: Date.now(),
      })
    )
  }

  async disconnect(): Promise<void> {
    if (this.dataChannel) {
      this.dataChannel.close()
      this.dataChannel = null
    }

    if (this.pc) {
      this.pc.close()
      this.pc = null
    }

    console.log('WebRTC connection closed')
  }

  get connectionState(): RTCPeerConnectionState | null {
    return this.pc?.connectionState ?? null
  }

  get isConnected(): boolean {
    return this.pc?.connectionState === 'connected'
  }
}

// TODO: Add automatic reconnection logic
// TODO: Add bandwidth stats monitoring
// TODO: Add ICE candidate trickling if needed
