"""Serial bridge for communicating with ESP32 MotionDriver via UART."""

import asyncio
import time
from collections import deque
from typing import Any, Optional

import serial_asyncio
from loguru import logger

from debug_hub import Broadcaster
from models import ControlCommand


def _now_ms() -> float:
    return time.time() * 1000


class MotionDriverBridge:
    """Asynchronous serial bridge to ESP32 MotionDriver.

    Converts high-level ControlCommand messages into UART protocol
    commands that the ESP32 understands.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        heartbeat_interval: float = 0.2,
        reconnect_interval: float = 2.0,
    ) -> None:
        """Initialize serial bridge.

        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0', '/dev/serial0')
            baudrate: Serial baud rate (default: 115200)
            heartbeat_interval: Seconds between PING heartbeats. Must stay well
                under the ESP32 firmware deadman window so a healthy link keeps
                the motors enabled.
            reconnect_interval: Seconds between reconnection attempts after the
                serial link drops.
        """
        self.port = port
        self.baudrate = baudrate
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self._closing = False
        self._supervisor_task: Optional[asyncio.Task] = None
        self._write_lock = asyncio.Lock()

        # Debug/telemetry: fan-out of every TX/RX line to the Debug tab, plus
        # heartbeat round-trip tracking derived from the PING/PONG traffic.
        self.events = Broadcaster(history=300)
        self._awaiting_pong = False
        self._last_ping_mono: float | None = None
        self._last_pong_mono: float | None = None
        self._last_rtt_ms: float | None = None
        self._pong_times: deque[float] = deque(maxlen=64)
        self._miss_times: deque[float] = deque(maxlen=64)

    def _on_tx(self, line: str) -> None:
        """Record an outbound line and track heartbeat timing."""
        self.events.emit({"dir": "tx", "line": line, "ts": _now_ms()})
        if line.strip().upper() == "PING":
            now = time.monotonic()
            # A new PING before the previous PONG arrived = a missed beat.
            if self._awaiting_pong:
                self._miss_times.append(now)
            self._awaiting_pong = True
            self._last_ping_mono = now

    def _on_rx(self, line: str) -> None:
        """Record an inbound line and close out heartbeat timing on PONG."""
        self.events.emit({"dir": "rx", "line": line, "ts": _now_ms()})
        if "PONG" in line.upper():
            now = time.monotonic()
            if self._last_ping_mono is not None:
                self._last_rtt_ms = (now - self._last_ping_mono) * 1000
            self._last_pong_mono = now
            self._awaiting_pong = False
            self._pong_times.append(now)

    def heartbeat_stats(self) -> dict[str, Any]:
        """Snapshot of link-heartbeat health for the Debug tab."""
        now = time.monotonic()
        rate = len([t for t in self._pong_times if now - t <= 3.0]) / 3.0
        missed = len([t for t in self._miss_times if now - t <= 60.0])
        age = (now - self._last_pong_mono) if self._last_pong_mono is not None else None
        return {
            "connected": self.connected,
            "rtt_ms": self._last_rtt_ms,
            "last_pong_age_s": age,
            "rate_hz": rate,
            "missed_60s": missed,
            "interval_ms": self.heartbeat_interval * 1000,
        }

    async def connect(self) -> None:
        """Open the serial link and start the background supervisor.

        The supervisor keeps the link alive with periodic heartbeats and
        automatically reconnects if it drops (e.g. the ESP32 resets or the USB
        adapter re-enumerates). This does not raise on an initial failure - the
        supervisor keeps retrying in the background.
        """
        self._closing = False
        try:
            await self._open()
        except Exception as e:
            logger.error(f"Initial MotionDriver connect failed: {e}; will keep retrying")
            await self._cleanup_transport()
            self.connected = False
        if self._supervisor_task is None:
            self._supervisor_task = asyncio.create_task(self._supervise())

    async def _open(self) -> None:
        """Open the serial connection and verify it with a PING/PONG handshake."""
        logger.info(f"Connecting to MotionDriver on {self.port} @ {self.baudrate} baud")
        self.reader, self.writer = await serial_asyncio.open_serial_connection(
            url=self.port, baudrate=self.baudrate
        )
        self.connected = True
        logger.info("MotionDriver connected")

        # Send ping to verify connection
        await self.send_raw("PING\n")
        response = await self.read_line(timeout=2.0)
        if response and "PONG" in response:
            logger.success("MotionDriver responded to PING")
        else:
            logger.warning(f"Unexpected response to PING: {response}")

    async def _cleanup_transport(self) -> None:
        """Close and discard the current serial transport, if any."""
        writer = self.writer
        self.reader = None
        self.writer = None
        if writer is not None:
            try:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
            except Exception:
                pass

    async def _supervise(self) -> None:
        """Keep the link alive: heartbeat while connected, reconnect when not."""
        while not self._closing:
            if not self.connected:
                try:
                    await self._open()
                except Exception as e:
                    logger.warning(
                        f"MotionDriver reconnect failed: {e}; retrying in {self.reconnect_interval}s"
                    )
                    await self._cleanup_transport()
                    self.connected = False
                    await asyncio.sleep(self.reconnect_interval)
                    continue

            # Connected: drain replies and heartbeat until the link drops. A
            # failed read/write flips self.connected to False and breaks out.
            reader_task = asyncio.create_task(self._reader_loop())
            try:
                while not self._closing and self.connected:
                    await self.send_raw("PING\n")
                    await asyncio.sleep(self.heartbeat_interval)
            finally:
                reader_task.cancel()
                try:
                    await reader_task
                except asyncio.CancelledError:
                    pass

            if not self.connected and not self._closing:
                logger.warning("MotionDriver link lost; attempting to reconnect")
                await self._cleanup_transport()
                await asyncio.sleep(self.reconnect_interval)

    async def _reader_loop(self) -> None:
        """Continuously read and discard incoming lines.

        The ESP32 replies to every command and heartbeat, so something has to
        drain the buffer; this also detects a dropped link via EOF.
        """
        while not self._closing and self.connected:
            await self.read_line(timeout=1.0)

    async def disconnect(self) -> None:
        """Stop the supervisor and close the serial connection."""
        self._closing = True
        if self._supervisor_task is not None:
            self._supervisor_task.cancel()
            try:
                await self._supervisor_task
            except asyncio.CancelledError:
                pass
            self._supervisor_task = None
        await self._cleanup_transport()
        self.connected = False
        logger.info("MotionDriver disconnected")

    async def send_raw(self, command: str) -> None:
        """Send raw command to MotionDriver.

        Args:
            command: Command string (should include newline if required)
        """
        if not self.writer or not self.connected:
            logger.warning("Cannot send command - not connected")
            return

        try:
            async with self._write_lock:
                self.writer.write(command.encode("utf-8"))
                await self.writer.drain()
            logger.debug(f"Sent: {command.strip()}")
            self._on_tx(command.strip())
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            self.connected = False

    async def read_line(self, timeout: float = 1.0) -> Optional[str]:
        """Read a line from serial port with timeout.

        Args:
            timeout: Read timeout in seconds

        Returns:
            Line string (without newline) or None on timeout
        """
        if not self.reader or not self.connected:
            return None

        try:
            line_bytes = await asyncio.wait_for(self.reader.readline(), timeout=timeout)
            if line_bytes == b"":
                # EOF - the serial device went away
                logger.warning("MotionDriver serial reached EOF (device disconnected)")
                self.connected = False
                return None
            line = line_bytes.decode("utf-8", errors="ignore").strip()
            logger.debug(f"Received: {line}")
            if line:
                self._on_rx(line)
            return line
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Failed to read from serial: {e}")
            self.connected = False
            return None

    async def send_command(self, cmd: ControlCommand) -> None:
        """Convert ControlCommand to UART protocol and send to ESP32.

        Args:
            cmd: High-level control command from frontend
        """
        if not self.connected:
            logger.warning("MotionDriver not connected, command ignored")
            return

        try:
            if cmd.type == "estop" or cmd.type == "stop":
                # Emergency stop: stop all motors using proper protocol
                await self.send_raw("MOTOR ALL STOP\n")
                logger.warning("Emergency stop executed")
                return

            # Motor control - use FORWARD/BACKWARD commands with speed 0.0-1.0
            if cmd.motors:
                for motor_id, speed in enumerate(cmd.motors):
                    if speed == 0:
                        await self.send_raw(f"MOTOR {motor_id} STOP\n")
                    else:
                        # Determine direction and magnitude
                        direction = "FORWARD" if speed > 0 else "BACKWARD"
                        speed_magnitude = abs(speed)  # 0.0 to 1.0
                        await self.send_raw(f"MOTOR {motor_id} {direction} {speed_magnitude}\n")

            # Servo control - ESP32 expects pulse width in microseconds
            if cmd.servos:
                for servo_id, pulse_us in enumerate(cmd.servos):
                    await self.send_raw(f"S {servo_id} {pulse_us}\n")

            # Legacy command support (backwards compatibility)
            if cmd.motor_left is not None or cmd.motor_right is not None:
                left = cmd.motor_left or 0.0
                right = cmd.motor_right or 0.0

                # Map to 6-motor layout (3 left, 3 right)
                for motor_id in [0, 1, 2]:  # Left side
                    if left == 0:
                        await self.send_raw(f"MOTOR {motor_id} STOP\n")
                    else:
                        direction = "FORWARD" if left > 0 else "BACKWARD"
                        await self.send_raw(f"MOTOR {motor_id} {direction} {abs(left)}\n")

                for motor_id in [3, 4, 5]:  # Right side
                    if right == 0:
                        await self.send_raw(f"MOTOR {motor_id} STOP\n")
                    else:
                        direction = "FORWARD" if right > 0 else "BACKWARD"
                        await self.send_raw(f"MOTOR {motor_id} {direction} {abs(right)}\n")

            if cmd.servo_pan is not None:
                # Servo expects pulse width in microseconds (e.g., 1000-2000)
                await self.send_raw(f"S 0 {cmd.servo_pan}\n")
            if cmd.servo_tilt is not None:
                # Servo expects pulse width in microseconds (e.g., 1000-2000)
                await self.send_raw(f"S 1 {cmd.servo_tilt}\n")

        except Exception as e:
            logger.error(f"Error processing command: {e}")

    def is_connected(self) -> bool:
        """Check if serial connection is active."""
        return self.connected


class MockMotionDriverBridge:
    """Mock bridge for testing without hardware.

    Emits synthetic PING/PONG heartbeat traffic and echoes OK replies so the
    Debug tab is fully exercisable in dev mode with ``serial_mock=True``.
    """

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        logger.info(f"[MOCK] MotionDriver bridge initialized (port={port})")
        self.connected = False
        self.heartbeat_interval = 0.2
        self.events = Broadcaster(history=300)
        self._hb_task: Optional[asyncio.Task] = None
        self._rtt_ms = 7.0
        self._last_pong_mono: float | None = None

    async def connect(self) -> None:
        logger.info("[MOCK] MotionDriver connected")
        self.connected = True
        self.events.emit({"dir": "rx", "line": "boot: MotionDriver ready (MOCK)", "ts": _now_ms()})
        if self._hb_task is None:
            self._hb_task = asyncio.create_task(self._fake_heartbeat())

    async def disconnect(self) -> None:
        logger.info("[MOCK] MotionDriver disconnected")
        self.connected = False
        if self._hb_task is not None:
            self._hb_task.cancel()
            try:
                await self._hb_task
            except asyncio.CancelledError:
                pass
            self._hb_task = None

    async def _fake_heartbeat(self) -> None:
        import random

        while self.connected:
            self.events.emit({"dir": "tx", "line": "PING", "ts": _now_ms()})
            await asyncio.sleep(0.01)
            self._rtt_ms = round(random.uniform(5.0, 12.0), 1)
            self._last_pong_mono = time.monotonic()
            self.events.emit({"dir": "rx", "line": "PONG", "ts": _now_ms()})
            await asyncio.sleep(self.heartbeat_interval)

    async def send_raw(self, command: str) -> None:
        line = command.strip()
        logger.debug(f"[MOCK] Send: {line}")
        self.events.emit({"dir": "tx", "line": line, "ts": _now_ms()})
        if line.upper() != "PING":
            reply = "PONG" if line.upper() == "PING" else "OK"
            self.events.emit({"dir": "rx", "line": reply, "ts": _now_ms()})

    async def read_line(self, timeout: float = 1.0) -> Optional[str]:
        await asyncio.sleep(0.01)  # Simulate I/O
        return "OK"

    async def send_command(self, cmd: ControlCommand) -> None:
        logger.info(f"[MOCK] Command: {cmd.type} | motors={cmd.motors} | servos={cmd.servos}")

    def heartbeat_stats(self) -> dict[str, Any]:
        now = time.monotonic()
        age = (now - self._last_pong_mono) if self._last_pong_mono is not None else None
        return {
            "connected": self.connected,
            "rtt_ms": self._rtt_ms if self.connected else None,
            "last_pong_age_s": age,
            "rate_hz": (1.0 / self.heartbeat_interval) if self.connected else 0.0,
            "missed_60s": 0,
            "interval_ms": self.heartbeat_interval * 1000,
        }

    def is_connected(self) -> bool:
        return self.connected
