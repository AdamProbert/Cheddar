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
  type: z.enum(['motor', 'servo', 'ping', 'stop', 'estop']),
  // 6-wheel drive control (preferred)
  motors: z.array(z.number().min(-1).max(1)).length(6).optional(),
  // 6-wheel steering control (preferred) - 90 degrees = straight ahead
  servos: z.array(z.number().int().min(0).max(180)).length(6).optional(),
  // Legacy simple control (deprecated)
  motor_left: z.number().min(-1).max(1).optional(),
  motor_right: z.number().min(-1).max(1).optional(),
  servo_pan: z.number().int().min(0).max(180).optional(),
  servo_tilt: z.number().int().min(0).max(180).optional(),
  timestamp: z.number(),
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

export const CameraSettingsSchema = z.object({
  enabled: z.boolean(),
  width: z.number(),
  height: z.number(),
  framerate: z.number(),
  flip_180: z.boolean(),
  is_noir: z.boolean(),
  awb_mode: z.string(),
  color_gains: z.tuple([z.number(), z.number()]),
})

// ---------------------------------------------------------------------------
// Debug tab (/ws/debug) message schemas
// ---------------------------------------------------------------------------
export const SerialEventSchema = z.object({
  dir: z.enum(['tx', 'rx']),
  line: z.string(),
  ts: z.number(),
})

export const LogRecordSchema = z.object({
  ts: z.number(),
  level: z.string(),
  name: z.string(),
  message: z.string(),
})

export const HeartbeatStatsSchema = z.object({
  available: z.boolean().optional(),
  connected: z.boolean().optional(),
  rtt_ms: z.number().nullable().optional(),
  last_pong_age_s: z.number().nullable().optional(),
  rate_hz: z.number().optional(),
  missed_60s: z.number().optional(),
  interval_ms: z.number().optional(),
  deadman_ms: z.number().optional(),
})

export const PowerFlagsSchema = z.object({
  undervoltage_now: z.boolean(),
  freq_capped_now: z.boolean(),
  throttled_now: z.boolean(),
  soft_temp_now: z.boolean(),
  undervoltage_occurred: z.boolean(),
  freq_capped_occurred: z.boolean(),
  throttled_occurred: z.boolean(),
  soft_temp_occurred: z.boolean(),
})

export const PowerSnapshotSchema = z.object({
  available: z.boolean(),
  raw: z.string().optional(),
  flags: PowerFlagsSchema.partial().optional(),
  history: z.array(z.object({ ts: z.number(), uv: z.boolean() })).optional(),
  events: z.number().optional(),
})

export type SerialEvent = z.infer<typeof SerialEventSchema>
export type LogRecord = z.infer<typeof LogRecordSchema>
export type HeartbeatStats = z.infer<typeof HeartbeatStatsSchema>
export type PowerFlags = z.infer<typeof PowerFlagsSchema>
export type PowerSnapshot = z.infer<typeof PowerSnapshotSchema>

// Type inference
export type SDPOffer = z.infer<typeof SDPOfferSchema>
export type SDPAnswer = z.infer<typeof SDPAnswerSchema>
export type HealthResponse = z.infer<typeof HealthResponseSchema>
export type ControlCommand = z.infer<typeof ControlCommandSchema>
export type SystemMetrics = z.infer<typeof SystemMetricsSchema>
export type ConfigResponse = z.infer<typeof ConfigResponseSchema>
export type CameraSettings = z.infer<typeof CameraSettingsSchema>
