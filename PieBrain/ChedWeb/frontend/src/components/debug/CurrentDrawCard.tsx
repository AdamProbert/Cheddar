/**
 * Current draw - placeholder until a current/power sensor is on the bus.
 * Phase 2: add an INA226/INA260 on the I2C line (shared with the PCA9685).
 */
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Gauge } from 'lucide-react'

export function CurrentDrawCard() {
  return (
    <Card className="w-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Gauge className="h-5 w-5 text-satisfactory-orange" />
          Current Draw
        </CardTitle>
        <span className="rounded-full border border-satisfactory-panel-border bg-background px-2.5 py-0.5 font-mono text-[11px] font-bold uppercase text-muted-foreground">
          Sensor Needed
        </span>
      </CardHeader>
      <CardContent>
        <div
          className="rounded border border-dashed border-satisfactory-panel-border p-4 text-center"
          style={{
            background:
              'repeating-linear-gradient(135deg, transparent, transparent 8px, rgba(255,255,255,0.012) 8px, rgba(255,255,255,0.012) 16px)',
          }}
        >
          <div className="font-mono text-2xl font-bold text-muted-foreground">— · — A</div>
          <p className="mt-2 text-xs text-muted-foreground">
            No current sensor on the bus yet. Add an <span className="font-mono text-satisfactory-cyan">INA226/INA260</span>{' '}
            on the I²C line (shared with the PCA9685) to stream live amps for the Pi 5V and motor rails.
          </p>
        </div>
        <p className="mt-2 text-xs text-muted-foreground/70">Phase 2 — everything above works with today's hardware.</p>
      </CardContent>
    </Card>
  )
}
