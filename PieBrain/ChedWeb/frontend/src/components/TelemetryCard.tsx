/**
 * Telemetry display component
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
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Telemetry
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {/* Latency */}
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground">Latency</span>
            <span className={`text-2xl font-bold ${latencyFormatted.color}`}>
              {latencyFormatted.value}
            </span>
          </div>

          {/* Battery */}
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <Battery className="w-4 h-4" />
              Battery
            </span>
            <span className={`text-2xl font-bold ${batteryFormatted.color}`}>
              {batteryFormatted.value}
            </span>
          </div>

          {/* CPU Temperature */}
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <Cpu className="w-4 h-4" />
              CPU Temp
            </span>
            <span className="text-2xl font-bold text-foreground">
              {telemetry?.cpu_temp !== undefined && telemetry.cpu_temp !== null
                ? `${telemetry.cpu_temp.toFixed(1)}°C`
                : '--'}
            </span>
          </div>

          {/* Signal Strength */}
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <Wifi className="w-4 h-4" />
              Signal
            </span>
            <span className="text-2xl font-bold text-foreground">
              {telemetry?.signal_strength !== undefined && telemetry.signal_strength !== null
                ? `${telemetry.signal_strength}%`
                : '--'}
            </span>
          </div>
        </div>

        {/* TODO: Add current draw and other metrics */}
      </CardContent>
    </Card>
  )
}
