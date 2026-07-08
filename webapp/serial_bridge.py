from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Optional, Protocol

from config import SerialConfig

try:
    import serial  # type: ignore
except ImportError:  # pragma: no cover - handled in tests
    serial = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


class CommandError(RuntimeError):
    """Raised when the MotionDriver returns an error response."""


class SerialTransport(Protocol):
    """Transport interface for sending commands over a serial-like link."""

    def write_line(self, line: str) -> None: ...

    def readline(self, timeout: float) -> Optional[str]: ...

    def close(self) -> None: ...


class PySerialTransport:
    """Transport backed by pyserial.Serial."""

    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        if serial is None:  # pragma: no cover - import fallback
            raise RuntimeError("pyserial is required but not installed")
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    def write_line(self, line: str) -> None:
        payload = (line.rstrip("\r\n") + "\n").encode("utf-8")
        self._serial.write(payload)
        self._serial.flush()

    def readline(self, timeout: float) -> Optional[str]:
        original_timeout = self._serial.timeout
        try:
            self._serial.timeout = timeout
            raw = self._serial.readline()
        finally:
            self._serial.timeout = original_timeout
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace").strip()

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()


@dataclass
class DummyTransport:
    """A fake transport for tests and dry-run mode."""

    last_line: Optional[str] = None
    canned_response: str = "OK"

    def write_line(self, line: str) -> None:
        self.last_line = line.rstrip("\r\n")
        _LOGGER.debug("DummyTransport wrote line: %s", self.last_line)

    def readline(
        self, timeout: float
    ) -> Optional[str]:  # noqa: ARG002 - interface requirement
        _LOGGER.debug(
            "DummyTransport returning canned response: %s", self.canned_response
        )
        return self.canned_response

    def close(self) -> None:  # pragma: no cover - nothing to do
        _LOGGER.debug("DummyTransport close() called")


class SerialBridge:
    """High-level helper that wraps MotionDriver CLI commands."""

    def __init__(
        self, config: SerialConfig, transport: Optional[SerialTransport] = None
    ) -> None:
        self._config = config
        self._transport = transport
        self._lock = threading.Lock()

    def _ensure_transport(self) -> SerialTransport:
        if self._transport is not None:
            return self._transport

        if self._config.dry_run:
            self._transport = DummyTransport()
            return self._transport

        port = self._config.effective_port()
        if port is None:
            raise RuntimeError(
                "Serial port not specified. Set MOTIONDRIVER_SERIAL_PORT."
            )

        _LOGGER.info(
            "Opening MotionDriver serial port %s @ %sbps (timeout=%.2fs)",
            port,
            self._config.baudrate,
            self._config.timeout,
        )
        self._transport = PySerialTransport(
            port, self._config.baudrate, self._config.timeout
        )
        return self._transport

    def close(self) -> None:
        with self._lock:
            if self._transport is not None:
                _LOGGER.debug("Closing serial transport")
                self._transport.close()
                self._transport = None

    def send_command(
        self,
        command: str,
        expect_response: bool = True,
        timeout: Optional[float] = None,
        quiet: bool = False,
    ) -> Optional[str]:
        timeout = timeout if timeout is not None else self._config.timeout
        log = self._config.log_traffic and not quiet
        with self._lock:
            transport = self._ensure_transport()
            if log:
                _LOGGER.info("-> %s", command)
            transport.write_line(command)
            if not expect_response:
                return None
            response = transport.readline(timeout)
            if response is None:
                raise TimeoutError(
                    f"No response received for command '{command}' within {timeout}s"
                )
            response = response.strip()
            if log:
                _LOGGER.info("<- %s", response)
            if response.upper().startswith("ERR"):
                raise CommandError(response)
            return response

    def ping(self, quiet: bool = False) -> str:
        return self.send_command("PING", quiet=quiet) or ""

    def set_servo(self, channel: int, pulse_us: int) -> str:
        self._validate_channel(channel)
        if pulse_us <= 0:
            raise ValueError("pulse_us must be positive")
        return self._expect_ok(self.send_command(f"S {channel} {pulse_us}"))

    def set_sweep(self, enabled: bool, sweep_range: Optional[str] = None) -> str:
        state = "ON" if enabled else "OFF"
        command = f"SWEEP {state}"
        if sweep_range:
            command += f" {sweep_range}"
        return self._expect_ok(self.send_command(command))

    def set_log(self, enabled: bool) -> str:
        state = "ON" if enabled else "OFF"
        return self._expect_ok(self.send_command(f"LOG {state}"))

    def motor_run(
        self, target: str, direction: str, speed: Optional[float] = None
    ) -> str:
        tgt = self._normalize_target(target)
        dir_upper = self._normalize_direction(direction)
        command = f"MOTOR {tgt} {dir_upper}"
        if speed is not None:
            if not 0.0 <= speed <= 1.0:
                raise ValueError("speed must be between 0.0 and 1.0")
            command += f" {speed:.2f}"
        return self._expect_ok(self.send_command(command))

    def motor_start(self, target: str) -> str:
        tgt = self._normalize_target(target)
        return self._expect_ok(self.send_command(f"MOTOR {tgt} START"))

    def motor_stop(self, target: str) -> str:
        tgt = self._normalize_target(target)
        return self._expect_ok(self.send_command(f"MOTOR {tgt} STOP"))

    @staticmethod
    def _expect_ok(response: Optional[str]) -> str:
        if response is None:
            return ""
        if response.upper() != "OK":
            raise CommandError(response)
        return response

    @staticmethod
    def _validate_channel(channel: int) -> None:
        if channel < 0 or channel > 15:
            raise ValueError("channel must be between 0 and 15 (inclusive)")

    @staticmethod
    def _normalize_target(target: str) -> str:
        target = str(target).strip().upper()
        if target in {"ALL", "[ALL]"}:
            return "ALL"
        if not target.isdigit():
            raise ValueError("target must be an integer string 0-5 or 'ALL'")
        index = int(target)
        if not 0 <= index <= 5:
            raise ValueError("motor index must be between 0 and 5")
        return str(index)

    @staticmethod
    def _normalize_direction(direction: str) -> str:
        upper = direction.strip().upper()
        if upper not in {"FORWARD", "BACKWARD"}:
            raise ValueError("direction must be FORWARD or BACKWARD")
        return upper


class Heartbeat:
    """Background thread that keeps the firmware deadman fed with PINGs.

    The ESP32 MotionDriver stops all motors if it sees no serial traffic for
    ~1s (deadman failsafe). This webapp only sends one-shot commands, so without
    a heartbeat a `MOTOR ... FORWARD` would be stopped ~1s later. This thread
    sends a quiet PING every ``interval`` seconds while the server runs, so a
    motor keeps running until an explicit STOP. If the backend dies or the link
    drops, the PINGs stop and the firmware deadman correctly stops the motors.
    """

    def __init__(self, bridge: SerialBridge, interval: float = 0.2) -> None:
        self._bridge = bridge
        self._interval = interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._healthy: Optional[bool] = None

    def start(self) -> None:
        if self._interval <= 0:
            _LOGGER.info("Heartbeat disabled (interval <= 0)")
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="motiondriver-heartbeat", daemon=True
        )
        self._thread.start()
        _LOGGER.info("Heartbeat started (every %.0fms)", self._interval * 1000)

    def _run(self) -> None:
        # Event.wait returns True once stop() is called; False on each timeout.
        while not self._stop.wait(self._interval):
            try:
                self._bridge.ping(quiet=True)
                if self._healthy is not True:
                    if self._healthy is False:
                        _LOGGER.info("Heartbeat link recovered")
                    self._healthy = True
            except Exception as exc:  # keep the heartbeat alive through any error
                if self._healthy is not False:
                    _LOGGER.warning("Heartbeat ping failing: %s", exc)
                    self._healthy = False

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=1.0)
            self._thread = None
        _LOGGER.info("Heartbeat stopped")


def create_bridge(
    config: Optional[SerialConfig] = None, transport: Optional[SerialTransport] = None
) -> SerialBridge:
    config = config or SerialConfig()
    return SerialBridge(config=config, transport=transport)
