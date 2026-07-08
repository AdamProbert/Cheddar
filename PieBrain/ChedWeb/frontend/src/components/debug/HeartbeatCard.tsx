/**
 * Link heartbeat: PING -> PONG round-trip latency, rate, and time since the
 * last PONG against the firmware deadman window.
 */
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { LineChart, Line, YAxis, ResponsiveContainer } from 'recharts'
import { Activity } from 'lucide-react'
import type { HeartbeatStats } from '@/types/schemas'
import type { RttPoint } from '../DebugView'

interface Props {
  heartbeat: HeartbeatStats
  rttHistory: RttPoint[]
  connected: boolean
}

export function HeartbeatCard({ heartbeat, rttHistory, connected }: Props) {
  const age = heartbeat.last_pong_age_s
  const healthy = connected && age !== null && age !== undefined && age < 1.0
  const deadmanMs = heartbeat.deadman_ms ?? 1000
  const deadmanFrac = age !== null && age !== undefined ? Math.min((age * 1000) / deadmanMs, 1) : 0

  const rtt = heartbeat.rtt_ms

  return (
    <Card className="w-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base text-satisfactory-cyan">
          <Activity className="h-5 w-5" />
          Link Heartbeat
        </CardTitle>
        <span
          className={`rounded-full border px-2.5 py-0.5 font-mono text-[11px] font-bold uppercase ${
            healthy
              ? 'border-green-500/40 bg-green-500/10 text-green-400'
              : 'border-destructive/40 bg-destructive/10 text-destructive'
          }`}
        >
          {healthy ? 'Healthy' : 'No Link'}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline justify-between">
          <div className="font-mono text-3xl font-bold text-green-400">
            {rtt !== null && rtt !== undefined ? rtt.toFixed(1) : '--'}
            <span className="ml-1 text-sm font-semibold text-muted-foreground">ms rtt</span>
          </div>
          <div className="text-right">
            <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Ping → Pong</div>
            <div className="font-mono font-bold text-satisfactory-cyan">
              {(heartbeat.rate_hz ?? 0).toFixed(1)} Hz
            </div>
          </div>
        </div>

        <div className="h-14">
          {rttHistory.length > 1 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rttHistory} margin={{ top: 4, right: 2, left: 2, bottom: 0 }}>
                <YAxis domain={[0, 'dataMax + 5']} hide />
                <Line
                  type="monotone"
                  dataKey="rtt"
                  stroke="hsl(var(--satisfactory-cyan))"
                  strokeWidth={1.8}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-[11px] uppercase tracking-widest text-muted-foreground">
              Collecting…
            </div>
          )}
        </div>

        <div className="space-y-0">
          <Row label="Last PONG" value={age !== null && age !== undefined ? `${age.toFixed(2)} s ago` : '--'} good={healthy} />
          <Row label="Missed beats (60s)" value={String(heartbeat.missed_60s ?? 0)} />
          <Row label="Deadman window" value={`${deadmanMs} ms`} />
        </div>

        <div className="relative h-2 overflow-hidden rounded bg-muted">
          <div
            className="absolute inset-y-0 left-0 rounded"
            style={{
              width: `${Math.max(deadmanFrac * 100, 3)}%`,
              background:
                deadmanFrac > 0.7
                  ? 'hsl(var(--destructive))'
                  : 'linear-gradient(90deg, hsl(var(--satisfactory-cyan)), #34d17f)',
            }}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Bar shows silence vs the {deadmanMs} ms firmware deadman. Backend PINGs keep it well left.
        </p>
      </CardContent>
    </Card>
  )
}

function Row({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <div className="flex justify-between border-b border-satisfactory-panel-border py-1.5 text-xs last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-mono font-bold ${good ? 'text-green-400' : 'text-foreground'}`}>{value}</span>
    </div>
  )
}
