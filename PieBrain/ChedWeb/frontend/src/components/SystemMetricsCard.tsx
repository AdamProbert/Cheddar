/**
 * System metrics display with Satisfactory-themed graphs
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
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-satisfactory-orange" />
          System Performance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current values */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <Cpu className="w-3 h-3" />
              CPU
            </span>
            <span className="text-2xl font-bold font-mono text-satisfactory-orange">
              {systemMetrics?.cpu_percent !== undefined ? `${systemMetrics.cpu_percent.toFixed(1)}%` : '--'}
            </span>
          </div>

          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <HardDrive className="w-3 h-3" />
              Memory
            </span>
            <span className="text-2xl font-bold font-mono text-satisfactory-cyan">
              {systemMetrics?.memory_percent !== undefined
                ? `${systemMetrics.memory_percent.toFixed(1)}%`
                : '--'}
            </span>
          </div>

          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <Thermometer className="w-3 h-3" />
              Temp
            </span>
            <span className="text-2xl font-bold font-mono text-red-400">
              {systemMetrics?.cpu_temp !== undefined && systemMetrics.cpu_temp !== null
                ? `${systemMetrics.cpu_temp.toFixed(1)}°C`
                : '--'}
            </span>
          </div>

          <div className="flex flex-col bg-satisfactory-panel p-3 rounded border border-satisfactory-panel-border">
            <span className="text-xs text-muted-foreground flex items-center gap-1 uppercase tracking-wider mb-1">
              <HardDrive className="w-3 h-3" />
              Disk
            </span>
            <span className="text-2xl font-bold font-mono text-foreground">
              {systemMetrics?.disk_percent !== undefined && systemMetrics.disk_percent !== null
                ? `${systemMetrics.disk_percent.toFixed(1)}%`
                : '--'}
            </span>
          </div>
        </div>

        {/* CPU & Memory Graph */}
        {chartData.length > 1 && (
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">CPU & Memory Usage</h3>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--satisfactory-panel-border))" opacity={0.3} />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                  tickFormatter={val => `${val}s`}
                  stroke="hsl(var(--satisfactory-panel-border))"
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                  tickFormatter={val => `${val}%`}
                  stroke="hsl(var(--satisfactory-panel-border))"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--satisfactory-panel))',
                    border: '2px solid hsl(var(--satisfactory-panel-border))',
                    borderRadius: '4px',
                    color: 'hsl(var(--foreground))',
                  }}
                  formatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="hsl(var(--satisfactory-orange))"
                  name="CPU"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="hsl(var(--satisfactory-cyan))"
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
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">CPU Temperature</h3>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--satisfactory-panel-border))" opacity={0.3} />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                  tickFormatter={val => `${val}s`}
                  stroke="hsl(var(--satisfactory-panel-border))"
                />
                <YAxis
                  domain={[0, 'auto']}
                  tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                  tickFormatter={val => `${val}°C`}
                  stroke="hsl(var(--satisfactory-panel-border))"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--satisfactory-panel))',
                    border: '2px solid hsl(var(--satisfactory-panel-border))',
                    borderRadius: '4px',
                    color: 'hsl(var(--foreground))',
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
          <div className="text-xs text-muted-foreground text-center py-4 uppercase tracking-wider">
            [ Initializing Metrics... ]
          </div>
        )}
      </CardContent>
    </Card>
  )
}

