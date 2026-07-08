/**
 * Live ESP32 serial console: streams TX/RX lines and sends whitelisted raw
 * commands. Heartbeat PING/PONG chatter is hidden by default to keep the log
 * readable.
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import type { SerialEvent } from '@/types/schemas'
import { TerminalSquare } from 'lucide-react'

const ALLOWED_VERBS = ['PING', 'HELP', 'MOTOR', 'S', 'SWEEP', 'LOG']
const QUICK = ['PING', 'HELP', 'MOTOR ALL STOP', 'SWEEP ON 0-5', 'LOG ON']

interface Props {
  events: SerialEvent[]
  connected: boolean
  lastError: string | null
  onSend: (line: string) => void
}

function isHeartbeat(line: string): boolean {
  const u = line.trim().toUpperCase()
  return u === 'PING' || u === 'PONG'
}

function lineClass(evt: SerialEvent): string {
  const u = evt.line.toUpperCase()
  if (u.startsWith('ERR') || u.includes('FAILSAFE')) return 'text-destructive'
  if (evt.dir === 'tx') return 'text-satisfactory-yellow'
  if (u === 'OK' || u === 'PONG') return 'text-green-400'
  return 'text-muted-foreground'
}

function fmtTime(ts: number): string {
  const d = new Date(ts)
  return d.toLocaleTimeString('en-GB', { hour12: false }) + '.' + String(d.getMilliseconds()).padStart(3, '0')
}

export function SerialConsole({ events, connected, lastError, onSend }: Props) {
  const [input, setInput] = useState('')
  const [hideHeartbeat, setHideHeartbeat] = useState(true)
  const [localError, setLocalError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const visible = useMemo(
    () => (hideHeartbeat ? events.filter(e => !isHeartbeat(e.line)) : events),
    [events, hideHeartbeat]
  )

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [visible])

  const submit = (line: string) => {
    const trimmed = line.trim()
    if (!trimmed) return
    const verb = trimmed.split(/\s+/)[0].toUpperCase()
    if (!ALLOWED_VERBS.includes(verb)) {
      setLocalError(`'${verb}' not allowed. Try: ${ALLOWED_VERBS.join(', ')}`)
      return
    }
    setLocalError(null)
    onSend(trimmed)
    setInput('')
  }

  const error = localError ?? lastError

  return (
    <Card className="w-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base text-satisfactory-cyan">
          <TerminalSquare className="h-5 w-5" />
          ESP32 Serial Console
        </CardTitle>
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={hideHeartbeat}
            onChange={e => setHideHeartbeat(e.target.checked)}
            className="accent-satisfactory-cyan"
          />
          Hide heartbeat
        </label>
      </CardHeader>
      <CardContent className="space-y-3">
        <div
          ref={scrollRef}
          className="h-56 overflow-auto rounded border border-satisfactory-panel-border bg-background p-3 font-mono text-xs leading-relaxed"
        >
          {visible.length === 0 && (
            <div className="text-muted-foreground">
              {connected ? 'Waiting for serial traffic…' : 'Debug link offline.'}
            </div>
          )}
          {visible.map((evt, i) => (
            <div key={i} className="flex gap-2 whitespace-pre-wrap">
              <span className="shrink-0 text-muted-foreground/60">{fmtTime(evt.ts)}</span>
              <span className={`shrink-0 font-bold ${evt.dir === 'tx' ? 'text-satisfactory-orange' : 'text-satisfactory-cyan'}`}>
                {evt.dir === 'tx' ? '→' : '←'}
              </span>
              <span className={lineClass(evt)}>{evt.line}</span>
            </div>
          ))}
        </div>

        {error && (
          <div className="rounded border border-destructive/40 bg-destructive/10 px-3 py-1.5 text-xs text-destructive">
            {error}
          </div>
        )}

        <form
          onSubmit={e => {
            e.preventDefault()
            submit(input)
          }}
          className="flex gap-2"
        >
          <span className="self-center font-mono font-bold text-satisfactory-orange">›</span>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="MOTOR 2 FORWARD 0.6   ·   S 4 1500   ·   HELP"
            className="flex-1 rounded border border-satisfactory-panel-border bg-background px-3 py-2 font-mono text-sm text-foreground placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-satisfactory-orange"
          />
          <button
            type="submit"
            className="rounded bg-satisfactory-orange px-4 text-xs font-bold uppercase tracking-wider text-primary-foreground hover:bg-satisfactory-yellow"
          >
            Send
          </button>
        </form>

        <div className="flex flex-wrap gap-1.5">
          {QUICK.map(cmd => (
            <button
              key={cmd}
              onClick={() => submit(cmd)}
              className="rounded-full border border-satisfactory-cyan/30 bg-satisfactory-cyan/10 px-2.5 py-0.5 font-mono text-[11px] text-satisfactory-cyan hover:bg-satisfactory-cyan/20"
            >
              {cmd}
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
