/**
 * Telemetry display with Satisfactory-style metrics
 */
import { useAppStore } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { formatLatency, formatBatteryVoltage } from '@/lib/utils'
import { Activity, Battery, Cpu, Wifi } from 'lucide-react'

export function TelemetryCard() {
  const telemetry = useAppStore(state => state.telemetry)
  const latency = useAppStore(state => state.latency)

  const latencyFormatted = formatLatency(latency)
  const batteryFormatted = formatBatteryVoltage(telemetry?.battery_voltage ?? null)

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-satisfactory-orange" />
          Telemetry Data
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {/* Latency */}
          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Latency</span>
            <span className={`text-2xl font-bold font-mono ${latencyFormatted.color}`}>
              {latencyFormatted.value}
            </span>
          </div>

          {/* Battery */}
          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <Battery className="w-3 h-3" />
              Battery
            </span>
            <span className={`text-2xl font-bold font-mono ${batteryFormatted.color}`}>
              {batteryFormatted.value}
            </span>
          </div>

          {/* CPU Temperature */}
          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <Cpu className="w-3 h-3" />
              CPU Temp
            </span>
            <span className="text-2xl font-bold font-mono text-satisfactory-cyan">
              {telemetry?.cpu_temp !== undefined && telemetry.cpu_temp !== null
                ? `${telemetry.cpu_temp.toFixed(1)}°C`
                : '--'}
            </span>
          </div>

          {/* Signal Strength */}
          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <Wifi className="w-3 h-3" />
              Signal
            </span>
            <span className="text-2xl font-bold font-mono text-foreground">
              {telemetry?.signal_strength !== undefined && telemetry.signal_strength !== null
                ? `${telemetry.signal_strength}%`
                : '--'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

