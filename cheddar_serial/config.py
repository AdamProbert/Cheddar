import os
from dataclasses import dataclass
from typing import Optional


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SerialConfig:
    """Runtime configuration for the MotionDriver serial link."""

    port: str = os.getenv("MOTIONDRIVER_SERIAL_PORT", "auto")
    baudrate: int = int(os.getenv("MOTIONDRIVER_SERIAL_BAUDRATE", "115200"))
    timeout: float = float(os.getenv("MOTIONDRIVER_SERIAL_TIMEOUT", "1.0"))
    dry_run: bool = _as_bool(os.getenv("MOTIONDRIVER_DRY_RUN"), default=False)
    log_traffic: bool = _as_bool(os.getenv("MOTIONDRIVER_LOG_TRAFFIC"), default=True)

    def effective_port(self) -> Optional[str]:
        """Return the port string, resolving the "auto" sentinel to None."""
        port = self.port.strip()
        if port.lower() in {"", "auto", "detect"}:
            return None
        return port
