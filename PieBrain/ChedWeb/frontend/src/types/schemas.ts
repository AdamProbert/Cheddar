/**
 * Zod schemas for API types - mirrors backend Pydantic models
 */
import { z } from 'zod'

export const SDPOfferSchema = z.object({
  sdp: z.string(),
  type: z.literal('offer'),
})

export const SDPAnswerSchema = z.object({
  sdp: z.string(),
  type: z.literal('answer'),
})

export const HealthResponseSchema = z.object({
  status: z.string(),
  timestamp: z.string(),
  version: z.string(),
})

export const ControlCommandSchema = z.object({
  type: z.enum(['motor', 'servo', 'ping', 'stop']),
  motor_left: z.number().min(-1).max(1).optional(),
  motor_right: z.number().min(-1).max(1).optional(),
  servo_pan: z.number().int().min(0).max(180).optional(),
  servo_tilt: z.number().int().min(0).max(180).optional(),
  timestamp: z.number(),
})

export const TelemetryDataSchema = z.object({
  type: z.enum(['telemetry', 'pong']),
  battery_voltage: z.number().nullable().optional(),
  current_draw: z.number().nullable().optional(),
  cpu_temp: z.number().nullable().optional(),
  signal_strength: z.number().int().min(0).max(100).nullable().optional(),
  timestamp: z.number(),
  latency_ms: z.number().optional(),
})

export const SystemMetricsSchema = z.object({
  type: z.literal('metrics'),
  cpu_percent: z.number(),
  memory_percent: z.number(),
  cpu_temp: z.number().nullable().optional(),
  disk_percent: z.number().nullable().optional(),
  timestamp: z.number(),
})

export const ConfigResponseSchema = z.object({
  version: z.string(),
  stun_server: z.string(),
  command_rate_limit_hz: z.number(),
  deadman_timeout_ms: z.number(),
})

// Type inference
export type SDPOffer = z.infer<typeof SDPOfferSchema>
export type SDPAnswer = z.infer<typeof SDPAnswerSchema>
export type HealthResponse = z.infer<typeof HealthResponseSchema>
export type ControlCommand = z.infer<typeof ControlCommandSchema>
export type TelemetryData = z.infer<typeof TelemetryDataSchema>
export type SystemMetrics = z.infer<typeof SystemMetricsSchema>
export type ConfigResponse = z.infer<typeof ConfigResponseSchema>
