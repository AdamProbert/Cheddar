/**
 * Pi power & brownout panel, sourced from `vcgencmd get_throttled`.
 *
 * Reads at a glance: a headline health state, live vs since-boot flags in plain
 * language, and a timeline that overlays under-voltage against motor commands so
 * a motor-induced brownout is obvious.
 */
import { useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Zap, ZapOff, AlertTriangle, ThermometerSun } from 'lucide-react'
import type { PowerSnapshot, PowerFlags } from '@/types/schemas'
import type { MotorEvent } from '../DebugView'

interface Props {
  power: PowerSnapshot
  motorEvents: MotorEvent[]
}

const WINDOW_MS = 60_000

const NOW_FLAGS: { key: keyof PowerFlags; label: string; tip: string }[] = [
  { key: 'undervoltage_now', label: 'Under-volt', tip: '5V rail below threshold right now (bit0)' },
  { key: 'throttled_now', label: 'Throttled', tip: 'CPU throttled right now (bit2)' },
  { key: 'freq_capped_now', label: 'Freq cap', tip: 'ARM frequency capped right now (bit1)' },
  { key: 'soft_temp_now', label: 'Soft temp', tip: 'Soft temperature limit active right now (bit3)' },
]

const BOOT_FLAGS: { key: keyof PowerFlags; label: string; tip: string }[] = [
  { key: 'undervoltage_occurred', label: 'Under-volt', tip: 'Under-voltage has happened since boot (bit16)' },
  { key: 'throttled_occurred', label: 'Throttled', tip: 'Throttling has happened since boot (bit18)' },
  { key: 'freq_capped_occurred', label: 'Freq cap', tip: 'Frequency capping has happened since boot (bit17)' },
  { key: 'soft_temp_occurred', label: 'Soft temp', tip: 'Soft temperature limit has happened since boot (bit19)' },
]

function headline(flags: Partial<PowerFlags>) {
  if (flags.undervoltage_now)
    return { label: 'Under-voltage', tone: 'crit' as const, Icon: ZapOff, note: 'The 5V rail is sagging right now.' }
  if (flags.throttled_now)
    return { label: 'Throttling', tone: 'crit' as const, Icon: AlertTriangle, note: 'CPU is being throttled right now.' }
  if (flags.freq_capped_now)
    return { label: 'Frequency capped', tone: 'warn' as const, Icon: AlertTriangle, note: 'ARM clock is capped right now.' }
  if (flags.soft_temp_now)
    return { label: 'Soft temp limit', tone: 'warn' as const, Icon: ThermometerSun, note: 'Soft temperature limit is active.' }
  return { label: 'Power OK', tone: 'ok' as const, Icon: Zap, note: 'Rail nominal, no active throttling.' }
}

const TONE = {
  ok: { text: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/40', dot: 'bg-green-500' },
  warn: {
    text: 'text-satisfactory-yellow',
    bg: 'bg-satisfactory-yellow/10',
    border: 'border-satisfactory-yellow/40',
    dot: 'bg-satisfactory-yellow',
  },
  crit: { text: 'text-destructive', bg: 'bg-destructive/10', border: 'border-destructive/40', dot: 'bg-destructive' },
}

/** Count rising edges (false -> true) of under-voltage inside the window. */
function eventsInWindow(history: { ts: number; uv: boolean }[], now: number): number {
  let count = 0
  let prev = false
  for (const h of history) {
    if (h.uv && !prev && now - h.ts <= WINDOW_MS) count++
    prev = h.uv
  }
  return count
}

export function PowerCard({ power, motorEvents }: Props) {
  const flags: Partial<PowerFlags> = power.flags ?? {}
  const history = power.history ?? []

  // Use the latest server timestamp as "now" so serial + power stay aligned
  // regardless of client-clock skew.
  const nowRef = useMemo(() => {
    const hist = power.history ?? []
    const lastHist = hist.length ? hist[hist.length - 1].ts : 0
    const lastMotor = motorEvents.length ? motorEvents[motorEvents.length - 1].ts : 0
    return Math.max(lastHist, lastMotor, Date.now())
  }, [power.history, motorEvents])

  if (!power.available) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="h-5 w-5 text-satisfactory-orange" />
            Power & Brownouts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            <span className="font-mono text-satisfactory-cyan">vcgencmd</span> not available on this host — power
            flags only appear when the backend runs on the Pi.
          </p>
        </CardContent>
      </Card>
    )
  }

  const h = headline(flags)
  const tone = TONE[h.tone]
  const events = power.events ?? 0
  const last60 = eventsInWindow(history, nowRef)
  const lastAgo =
    power.last_event_ts != null ? Math.max(0, (nowRef - power.last_event_ts) / 1000) : null

  const uvPoints = history.filter(p => p.uv && nowRef - p.ts <= WINDOW_MS)
  const motorPoints = motorEvents.filter(m => nowRef - m.ts <= WINDOW_MS)
  const xPct = (ts: number) => Math.min(100, Math.max(0, ((ts - (nowRef - WINDOW_MS)) / WINDOW_MS) * 100))

  return (
    <Card className="w-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="h-5 w-5 text-satisfactory-orange" />
          Power & Brownouts
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 1. Headline state */}
        <div className={`flex items-center gap-3 rounded border ${tone.border} ${tone.bg} px-3 py-2.5`}>
          <h.Icon className={`h-6 w-6 shrink-0 ${tone.text}`} />
          <div className="min-w-0">
            <div className={`text-sm font-bold uppercase tracking-wide ${tone.text}`}>{h.label}</div>
            <div className="text-xs text-muted-foreground">{h.note}</div>
          </div>
        </div>

        {/* 2 + 3. Live vs since-boot flags, plain language */}
        <div className="grid grid-cols-2 gap-3">
          <FlagGroup title="Right now" flags={flags} rows={NOW_FLAGS} activeTone="crit" />
          <FlagGroup title="Since boot" flags={flags} rows={BOOT_FLAGS} activeTone="warn" />
        </div>

        {/* 4. Event counters with timeframe */}
        <div className="grid grid-cols-3 gap-2">
          <Stat label="Events (session)" value={String(events)} tone={events > 0 ? 'warn' : 'ok'} />
          <Stat label="Last 60s" value={String(last60)} tone={last60 > 0 ? 'crit' : 'ok'} />
          <Stat
            label="Last event"
            value={lastAgo == null ? 'never' : lastAgo < 1 ? 'now' : `${Math.round(lastAgo)}s ago`}
            tone={lastAgo != null && lastAgo < 3 ? 'crit' : 'ok'}
          />
        </div>

        {/* 5 + 6. Correlation timeline */}
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              Brownout vs motor commands
            </span>
            <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
              <Legend swatch="bg-destructive" label="Under-volt" />
              <Legend swatch="bg-satisfactory-orange" label="Motor drive" />
              <Legend swatch="bg-muted-foreground/50" label="Motor stop" />
            </div>
          </div>

          <div className="rounded border border-satisfactory-panel-border bg-background px-2 py-1.5">
            <Lane label="Power" empty={uvPoints.length === 0} emptyText="no dips">
              {uvPoints.map((p, i) => (
                <span
                  key={i}
                  title={`Under-voltage · ${new Date(p.ts).toLocaleTimeString()}`}
                  className="absolute top-0 h-full w-[3px] -translate-x-1/2 rounded bg-destructive"
                  style={{ left: `${xPct(p.ts)}%` }}
                />
              ))}
            </Lane>
            <Lane label="Motors" empty={motorPoints.length === 0} emptyText="idle">
              {motorPoints.map((m, i) => (
                <span
                  key={i}
                  title={`${m.line} · ${new Date(m.ts).toLocaleTimeString()}`}
                  className={`absolute top-0 h-full w-[3px] -translate-x-1/2 rounded ${
                    m.motion ? 'bg-satisfactory-orange' : 'bg-muted-foreground/50'
                  }`}
                  style={{ left: `${xPct(m.ts)}%` }}
                />
              ))}
            </Lane>
            <div className="flex justify-between pl-12 pt-0.5 text-[10px] text-muted-foreground">
              <span>−60s</span>
              <span>now</span>
            </div>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            An under-voltage tick right after a motor tick means the drive current is sagging the shared rail. Source:{' '}
            <span className="font-mono text-satisfactory-cyan">vcgencmd get_throttled</span>
            {power.raw && <span className="font-mono"> · {power.raw}</span>}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

function FlagGroup({
  title,
  flags,
  rows,
  activeTone,
}: {
  title: string
  flags: Partial<PowerFlags>
  rows: { key: keyof PowerFlags; label: string; tip: string }[]
  activeTone: 'warn' | 'crit'
}) {
  return (
    <div>
      <div className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{title}</div>
      <div className="space-y-1">
        {rows.map(row => {
          const on = Boolean(flags[row.key])
          const dot = !on ? 'bg-green-500' : activeTone === 'crit' ? 'bg-destructive' : 'bg-satisfactory-yellow'
          return (
            <div
              key={row.key}
              title={row.tip}
              className={`flex items-center gap-2 rounded border border-satisfactory-panel-border bg-background px-2 py-1.5 text-xs ${
                on ? '' : 'opacity-70'
              }`}
            >
              <span className={`h-2 w-2 shrink-0 rounded-full ${dot}`} />
              <span className="flex-1 truncate">{row.label}</span>
              <span className="font-mono text-[10px] text-muted-foreground">{on ? 'yes' : 'no'}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function Stat({ label, value, tone }: { label: string; value: string; tone: 'ok' | 'warn' | 'crit' }) {
  const color = tone === 'crit' ? 'text-destructive' : tone === 'warn' ? 'text-satisfactory-yellow' : 'text-foreground'
  return (
    <div className="rounded border border-satisfactory-panel-border bg-background px-2 py-1.5 text-center">
      <div className={`font-mono text-lg font-bold ${color}`}>{value}</div>
      <div className="text-[9px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  )
}

function Lane({
  label,
  empty,
  emptyText,
  children,
}: {
  label: string
  empty: boolean
  emptyText: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="w-10 shrink-0 text-right text-[9px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <div className="relative h-4 flex-1 overflow-hidden rounded-sm bg-muted/40">
        {empty ? (
          <span className="absolute inset-0 flex items-center pl-2 text-[9px] italic text-muted-foreground/60">
            {emptyText}
          </span>
        ) : (
          children
        )}
      </div>
    </div>
  )
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className={`h-2 w-2 rounded-sm ${swatch}`} />
      {label}
    </span>
  )
}
