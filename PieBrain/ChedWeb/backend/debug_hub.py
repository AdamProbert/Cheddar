"""Shared plumbing for the Debug tab: event fan-out, power monitoring,
log capture, and command whitelisting.

Everything here is hardware-agnostic so it can run against the mock bridge in
dev. The WebSocket handler in ``main.py`` wires these together.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Iterable

from loguru import logger


# ---------------------------------------------------------------------------
# Broadcaster: a ring buffer + set of subscriber queues.
# ---------------------------------------------------------------------------
class Broadcaster:
    """Fan-out of JSON-serialisable events to any number of subscribers.

    Keeps a bounded backlog so a freshly-connected client can be seeded with
    recent history before it starts receiving live events.
    """

    def __init__(self, history: int = 300, queue_size: int = 1000) -> None:
        self._buffer: deque[dict[str, Any]] = deque(maxlen=history)
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._queue_size = queue_size

    def emit(self, event: dict[str, Any]) -> dict[str, Any]:
        """Record an event and push it to every live subscriber.

        Slow subscribers silently drop events rather than blocking the
        producer (serial/heartbeat traffic must never stall on a stuck WS).
        """
        self._buffer.append(event)
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass
        return event

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def recent(self) -> list[dict[str, Any]]:
        return list(self._buffer)


# ---------------------------------------------------------------------------
# Log capture: a loguru sink that mirrors records into a Broadcaster.
# ---------------------------------------------------------------------------
log_broadcaster = Broadcaster(history=200)


def _log_sink(message: Any) -> None:
    """loguru sink -> broadcaster. ``message`` is a loguru Message with a
    ``.record`` mapping we flatten into a small JSON payload."""
    record = message.record
    log_broadcaster.emit(
        {
            "ts": record["time"].timestamp() * 1000,
            "level": record["level"].name,
            "name": record["name"],
            "message": record["message"],
        }
    )


def install_log_capture(level: str = "DEBUG") -> None:
    """Attach the capture sink to loguru. Safe to call once at startup."""
    logger.add(_log_sink, level=level, format="{message}", enqueue=False)


# ---------------------------------------------------------------------------
# Power monitor: polls `vcgencmd get_throttled` on the Pi.
# ---------------------------------------------------------------------------
# Bit meanings from the Raspberry Pi firmware. Low bits = happening now,
# high bits (>>16) = has happened since boot.
_FLAG_BITS = {
    "undervoltage_now": 0,
    "freq_capped_now": 1,
    "throttled_now": 2,
    "soft_temp_now": 3,
    "undervoltage_occurred": 16,
    "freq_capped_occurred": 17,
    "throttled_occurred": 18,
    "soft_temp_occurred": 19,
}


class PowerMonitor:
    """Background poller for the Pi's under-voltage / throttling flags.

    Degrades gracefully anywhere ``vcgencmd`` is missing (dev laptops, CI):
    ``available`` goes False and the Debug tab shows the panel as unavailable.
    """

    def __init__(self, poll_interval: float = 2.0, history: int = 60) -> None:
        self.poll_interval = poll_interval
        self._available: bool | None = None
        self._raw: str | None = None
        self._value: int = 0
        self._history: deque[dict[str, Any]] = deque(maxlen=history)
        self._events = 0
        self._prev_uv = False
        self._task: asyncio.Task | None = None
        self._closing = False

    async def start(self) -> None:
        self._closing = False
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._closing = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while not self._closing:
            await self._poll_once()
            if self._available is False:
                # vcgencmd isn't here; stop hammering a missing binary.
                return
            await asyncio.sleep(self.poll_interval)

    async def _poll_once(self) -> None:
        try:
            proc = await asyncio.create_subprocess_exec(
                "vcgencmd",
                "get_throttled",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
        except FileNotFoundError:
            self._available = False
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug(f"vcgencmd poll failed: {exc}")
            self._available = False
            return

        text = stdout.decode("utf-8", errors="ignore").strip()
        # Expected: "throttled=0x50000"
        if "=" not in text:
            self._available = False
            return
        try:
            self._value = int(text.split("=", 1)[1], 16)
        except ValueError:
            self._available = False
            return

        self._available = True
        self._raw = text.split("=", 1)[1]
        uv_now = bool(self._value & (1 << _FLAG_BITS["undervoltage_now"]))
        # Count a fresh event on the rising edge of under-voltage.
        if uv_now and not self._prev_uv:
            self._events += 1
        self._prev_uv = uv_now
        self._history.append({"ts": time.time() * 1000, "uv": uv_now})

    def snapshot(self) -> dict[str, Any]:
        if not self._available:
            return {"available": False, "history": [], "events": 0, "flags": {}}
        flags = {name: bool(self._value & (1 << bit)) for name, bit in _FLAG_BITS.items()}
        return {
            "available": True,
            "raw": self._raw,
            "flags": flags,
            "history": list(self._history),
            "events": self._events,
        }


# ---------------------------------------------------------------------------
# Command whitelist for the raw console.
# ---------------------------------------------------------------------------
# Only these verbs may reach the firmware from the debug console.
ALLOWED_VERBS = {"PING", "HELP", "MOTOR", "S", "SWEEP", "LOG"}
# MOTOR sub-commands that actually spin a motor (gated behind "arm").
_MOTION_MODES = {"FORWARD", "BACKWARD", "START"}


def validate_raw_command(line: str) -> tuple[bool, str]:
    """Return (ok, reason). ``reason`` is empty when ok."""
    stripped = line.strip()
    if not stripped:
        return False, "empty command"
    verb = stripped.split()[0].upper()
    if verb not in ALLOWED_VERBS:
        allowed = ", ".join(sorted(ALLOWED_VERBS))
        return False, f"'{verb}' is not allowed. Permitted verbs: {allowed}"
    return True, ""


def is_motion_command(line: str) -> bool:
    """True if the line would drive a motor (needs the motors armed).

    Firmware syntax is ``MOTOR <target> FORWARD|BACKWARD|START [speed]`` so the
    mode follows the target token; scan everything after the verb so ``ALL`` and
    numeric targets are both handled.
    """
    tokens = line.strip().upper().split()
    return len(tokens) >= 3 and tokens[0] == "MOTOR" and any(t in _MOTION_MODES for t in tokens[1:])


def iter_recent(broadcasters: Iterable[Broadcaster]) -> list[dict[str, Any]]:  # pragma: no cover - helper
    out: list[dict[str, Any]] = []
    for b in broadcasters:
        out.extend(b.recent())
    return out
