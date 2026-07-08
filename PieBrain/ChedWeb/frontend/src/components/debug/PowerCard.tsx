/**
 * Pi power & brownout panel, sourced from `vcgencmd get_throttled`. A spike
 * here that lines up with a motor command is the brownout smoking gun.
 */
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Zap } from 'lucide-react'
import type { PowerSnapshot, PowerFlags } from '@/types/schemas'

interface Props {
  power: PowerSnapshot
}

const FLAG_ROWS: { key: keyof PowerFlags; label: string; bit: string; danger: boolean }[] = [
  { key: 'undervoltage_now', label: 'Under-voltage now', bit: 'bit0', danger: true },
  { key: 'undervoltage_occurred', label: 'Under-voltage occurred', bit: 'bit16', danger: false },
  { key: 'throttled_occurred', label: 'Throttling occurred', bit: 'bit18', danger: false },
  { key: 'freq_capped_now', label: 'Freq capped now', bit: 'bit1', danger: true },
]

export function PowerCard({ power }: Props) {
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

  const flags: Partial<PowerFlags> = power.flags ?? {}
  const history = power.history ?? []
  const events = power.events ?? 0

  return (
    <Card className="w-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Zap className="h-5 w-5 text-satisfactory-orange" />
          Power & Brownouts
        </CardTitle>
        <span
          className={`rounded-full border px-2.5 py-0.5 font-mono text-[11px] font-bold uppercase ${
            events > 0
              ? 'border-satisfactory-yellow/40 bg-satisfactory-yellow/10 text-satisfactory-yellow'
              : 'border-green-500/40 bg-green-500/10 text-green-400'
          }`}
        >
          {events} {events === 1 ? 'Event' : 'Events'}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          {FLAG_ROWS.map(row => {
            const on = Boolean(flags[row.key])
            const color = !on ? 'bg-green-500' : row.danger ? 'bg-destructive' : 'bg-satisfactory-yellow'
            return (
              <div
                key={row.key}
                className="flex items-center gap-2.5 rounded border border-satisfactory-panel-border bg-background px-2.5 py-2 text-xs"
              >
                <span className={`h-2 w-2 shrink-0 rounded-full ${color}`} />
                <span className="flex-1">{row.label}</span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {row.bit} · {on ? 1 : 0}
                </span>
              </div>
            )
          })}
        </div>

        <div>
          <div className="mb-1 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Under-voltage · recent
          </div>
          <div className="flex h-11 items-end gap-0.5">
            {history.length === 0 && <div className="text-[11px] text-muted-foreground">No samples yet</div>}
            {history.map((h, i) => (
              <div
                key={i}
                title={new Date(h.ts).toLocaleTimeString()}
                className={`flex-1 rounded-sm ${h.uv ? 'bg-destructive' : 'bg-muted'}`}
                style={{ height: h.uv ? '100%' : '18%' }}
              />
            ))}
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Source: <span className="font-mono text-satisfactory-cyan">vcgencmd get_throttled</span>
          {power.raw && <span className="font-mono"> · {power.raw}</span>}
        </p>
      </CardContent>
    </Card>
  )
}
