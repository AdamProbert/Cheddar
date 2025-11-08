/**
 * System metrics display with time-series graphs
 */
import { useAppStore } from '@/store'
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Activity, Cpu, HardDrive, Thermometer } from 'lucide-react'

export function SystemMetricsCard() {
  const systemMetrics = useAppStore(state => state.systemMetrics)
  const metricsHistory = useAppStore(state => state.metricsHistory)

  // Format data for Recharts (convert timestamps to relative seconds)
  const chartData = metricsHistory.map((point, index) => ({
    time: index, // Simple index-based time axis (0, 1, 2, ...)
    cpu: point.cpu_percent,
    memory: point.memory_percent,
    temp: point.cpu_temp,
  }))

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="w-5 h-5" />
          System Metrics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current values */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <Cpu className="w-4 h-4" />
              CPU
            </span>
            <span className="text-2xl font-bold text-foreground">
              {systemMetrics?.cpu_percent !== undefined ? `${systemMetrics.cpu_percent.toFixed(1)}%` : '--'}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <HardDrive className="w-4 h-4" />
              Memory
            </span>
            <span className="text-2xl font-bold text-foreground">
              {systemMetrics?.memory_percent !== undefined
                ? `${systemMetrics.memory_percent.toFixed(1)}%`
                : '--'}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <Thermometer className="w-4 h-4" />
              Temp
            </span>
            <span className="text-2xl font-bold text-foreground">
              {systemMetrics?.cpu_temp !== undefined && systemMetrics.cpu_temp !== null
                ? `${systemMetrics.cpu_temp.toFixed(1)}°C`
                : '--'}
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-sm text-muted-foreground flex items-center gap-1">
              <HardDrive className="w-4 h-4" />
              Disk
            </span>
            <span className="text-2xl font-bold text-foreground">
              {systemMetrics?.disk_percent !== undefined && systemMetrics.disk_percent !== null
                ? `${systemMetrics.disk_percent.toFixed(1)}%`
                : '--'}
            </span>
          </div>
        </div>

        {/* CPU & Memory Graph */}
        {chartData.length > 1 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">CPU & Memory Usage</h3>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  tickFormatter={val => `${val}s`}
                  className="text-muted-foreground"
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  tickFormatter={val => `${val}%`}
                  className="text-muted-foreground"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3b82f6"
                  name="CPU"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#10b981"
                  name="Memory"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Temperature Graph */}
        {chartData.length > 1 && chartData.some(d => d.temp !== null) && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">CPU Temperature</h3>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  tickFormatter={val => `${val}s`}
                  className="text-muted-foreground"
                />
                <YAxis
                  domain={[0, 'auto']}
                  tick={{ fontSize: 12 }}
                  tickFormatter={val => `${val}°C`}
                  className="text-muted-foreground"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  formatter={(value: any) =>
                    value !== null && typeof value === 'number' ? `${value.toFixed(1)}°C` : 'N/A'
                  }
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#ef4444"
                  name="Temperature"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {chartData.length <= 1 && (
          <div className="text-sm text-muted-foreground text-center py-4">
            Waiting for metrics data...
          </div>
        )}
      </CardContent>
    </Card>
  )
}
