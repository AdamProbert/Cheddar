from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Optional, Protocol

from .config import SerialConfig

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
    ) -> Optional[str]:
        timeout = timeout if timeout is not None else self._config.timeout
        with self._lock:
            transport = self._ensure_transport()
            if self._config.log_traffic:
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
            if self._config.log_traffic:
                _LOGGER.info("<- %s", response)
            if response.upper().startswith("ERR"):
                raise CommandError(response)
            return response

    def ping(self) -> str:
        return self.send_command("PING") or ""

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


def create_bridge(
    config: Optional[SerialConfig] = None, transport: Optional[SerialTransport] = None
) -> SerialBridge:
    config = config or SerialConfig()
    return SerialBridge(config=config, transport=transport)
