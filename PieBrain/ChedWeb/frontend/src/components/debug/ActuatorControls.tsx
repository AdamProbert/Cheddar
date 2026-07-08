/**
 * Per-actuator control: 6 drive motors and 6 steering servos, each driven
 * individually. Motor drive is gated behind the arm toggle; servos are always
 * live (they only hold a position).
 */
import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Cog } from 'lucide-react'

const WHEELS = [
  { tag: 'FL', idx: 0 },
  { tag: 'FR', idx: 1 },
  { tag: 'ML', idx: 2 },
  { tag: 'MR', idx: 3 },
  { tag: 'RL', idx: 4 },
  { tag: 'RR', idx: 5 },
]

const DEFAULT_ALL_SPEED = 30 // percent
const SERVO_MIN = 500
const SERVO_MAX = 2500
const SERVO_CENTER = 1500

type Dir = 'forward' | 'backward'
interface MotorState {
  dir: Dir
  speed: number // 0-100
}

interface Props {
  armed: boolean
  connected: boolean
  onMotor: (index: number, dir: Dir, speed: number) => void
  onMotorStop: (index: number | 'all') => void
  onServo: (channel: number, pulseUs: number) => void
}

export function ActuatorControls({ armed, connected, onMotor, onMotorStop, onServo }: Props) {
  const [tab, setTab] = useState<'motors' | 'servos'>('motors')
  const [motors, setMotors] = useState<MotorState[]>(WHEELS.map(() => ({ dir: 'forward', speed: 0 })))
  const [servos, setServos] = useState<number[]>(WHEELS.map(() => SERVO_CENTER))

  const setMotor = (i: number, next: MotorState) => {
    setMotors(prev => prev.map((m, idx) => (idx === i ? next : m)))
    if (!armed) return
    if (next.speed <= 0) onMotorStop(i)
    else onMotor(i, next.dir, next.speed / 100)
  }

  const allMotors = (dir: Dir) => {
    const next = WHEELS.map(() => ({ dir, speed: DEFAULT_ALL_SPEED }))
    setMotors(next)
    if (!armed) return
    WHEELS.forEach((_, i) => onMotor(i, dir, DEFAULT_ALL_SPEED / 100))
  }

  const stopAllMotors = () => {
    setMotors(prev => prev.map(m => ({ ...m, speed: 0 })))
    onMotorStop('all')
  }

  const setServo = (i: number, us: number) => {
    setServos(prev => prev.map((s, idx) => (idx === i ? us : s)))
    onServo(i, us)
  }

  return (
    <Card className="w-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-base">
          <Cog className="h-5 w-5 text-satisfactory-orange" />
          Individual Actuators
        </CardTitle>
        <div className="flex overflow-hidden rounded border border-satisfactory-panel-border">
          {(['motors', 'servos'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              aria-pressed={tab === t}
              className={`px-4 py-1.5 text-xs font-bold uppercase tracking-wider transition-colors ${
                tab === t ? 'bg-satisfactory-orange/15 text-satisfactory-orange' : 'text-muted-foreground'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {!connected && (
          <div className="rounded border border-satisfactory-panel-border bg-satisfactory-panel/50 p-2 text-center text-xs text-muted-foreground">
            Debug link offline — reconnecting…
          </div>
        )}

        {tab === 'motors' && (
          <>
            {!armed && (
              <div className="mb-1 rounded border border-satisfactory-yellow/30 bg-satisfactory-yellow/10 p-2 text-xs text-satisfactory-yellow">
                Motors disarmed — arm above to drive. Sliders preview only.
              </div>
            )}
            <div className="space-y-2">
              {WHEELS.map((w, i) => {
                const m = motors[i]
                const active = m.speed > 0 && armed
                return (
                  <div key={w.tag} className="grid grid-cols-[52px_112px_1fr_46px_52px] items-center gap-3">
                    <div className="rounded border border-satisfactory-panel-border bg-background py-1.5 text-center font-mono text-sm font-bold">
                      {w.tag}
                      <span className="block text-[10px] leading-none text-muted-foreground">M{w.idx}</span>
                    </div>

                    <div className="flex overflow-hidden rounded border border-satisfactory-panel-border">
                      {(['forward', 'backward'] as const).map(d => (
                        <button
                          key={d}
                          disabled={!armed}
                          onClick={() => setMotor(i, { ...m, dir: d })}
                          aria-pressed={m.dir === d}
                          className={`w-14 py-1.5 text-[10px] font-extrabold uppercase transition-colors disabled:opacity-40 ${
                            m.dir === d
                              ? d === 'forward'
                                ? 'bg-satisfactory-cyan/15 text-satisfactory-cyan'
                                : 'bg-satisfactory-orange/15 text-satisfactory-orange'
                              : 'text-muted-foreground'
                          }`}
                        >
                          {d === 'forward' ? 'FWD' : 'BWD'}
                        </button>
                      ))}
                    </div>

                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={m.speed}
                      disabled={!armed}
                      onChange={e => setMotor(i, { ...m, speed: Number(e.target.value) })}
                      className="h-1.5 w-full cursor-pointer appearance-none rounded bg-muted accent-satisfactory-orange disabled:opacity-40"
                    />
                    <span
                      className={`text-right font-mono text-sm font-bold ${
                        active ? 'text-satisfactory-orange' : 'text-muted-foreground'
                      }`}
                    >
                      {m.speed}%
                    </span>
                    <button
                      onClick={() => setMotor(i, { ...m, speed: 0 })}
                      className="rounded border border-satisfactory-panel-border bg-background py-1.5 text-[10px] font-bold uppercase text-muted-foreground hover:text-satisfactory-orange"
                    >
                      Stop
                    </button>
                  </div>
                )
              })}
            </div>

            <div className="mt-3 flex gap-2 border-t border-dashed border-satisfactory-panel-border pt-3">
              <button
                disabled={!armed}
                onClick={() => allMotors('forward')}
                className="flex-1 rounded border border-satisfactory-panel-border bg-background py-2 text-xs font-bold uppercase text-muted-foreground hover:text-satisfactory-cyan disabled:opacity-40"
              >
                All Forward
              </button>
              <button
                disabled={!armed}
                onClick={() => allMotors('backward')}
                className="flex-1 rounded border border-satisfactory-panel-border bg-background py-2 text-xs font-bold uppercase text-muted-foreground hover:text-satisfactory-orange disabled:opacity-40"
              >
                All Backward
              </button>
              <button
                onClick={stopAllMotors}
                className="flex-1 rounded border border-destructive/50 bg-destructive/10 py-2 text-xs font-bold uppercase text-destructive"
              >
                Stop All
              </button>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Emits <span className="font-mono text-satisfactory-cyan">MOTOR &lt;n&gt; FORWARD 0.30</span> per change.
            </p>
          </>
        )}

        {tab === 'servos' && (
          <div className="space-y-2">
            {WHEELS.map((w, i) => (
              <div key={w.tag} className="grid grid-cols-[52px_1fr_72px_60px] items-center gap-3">
                <div className="rounded border border-satisfactory-panel-border bg-background py-1.5 text-center font-mono text-sm font-bold">
                  {w.tag}
                  <span className="block text-[10px] leading-none text-muted-foreground">S{w.idx}</span>
                </div>
                <input
                  type="range"
                  min={SERVO_MIN}
                  max={SERVO_MAX}
                  step={10}
                  value={servos[i]}
                  onChange={e => setServo(i, Number(e.target.value))}
                  className="h-1.5 w-full cursor-pointer appearance-none rounded bg-muted accent-satisfactory-cyan"
                />
                <span className="text-right font-mono text-sm font-bold text-satisfactory-cyan">
                  {servos[i]}µs
                </span>
                <button
                  onClick={() => setServo(i, SERVO_CENTER)}
                  className="rounded border border-satisfactory-panel-border bg-background py-1.5 text-[10px] font-bold uppercase text-muted-foreground hover:text-satisfactory-cyan"
                >
                  Center
                </button>
              </div>
            ))}
            <p className="mt-1 text-xs text-muted-foreground">
              Emits <span className="font-mono text-satisfactory-cyan">S &lt;ch&gt; &lt;µs&gt;</span> ({SERVO_MIN}–
              {SERVO_MAX}, center {SERVO_CENTER}).
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
