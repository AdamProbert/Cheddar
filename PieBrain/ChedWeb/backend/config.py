"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # WebRTC
    stun_server: str = "stun:stun.l.google.com:19302"
    turn_server: str | None = None
    turn_username: str | None = None
    turn_password: str | None = None

    # Serial/UART (for ESP32 MotionDriver communication)
    # Use /dev/serial0 for GPIO UART on Raspberry Pi (GPIO 14/15)
    serial_port: str = "/dev/serial0"
    serial_baudrate: int = 115200
    serial_timeout: float = 1.0
    serial_mock: bool = False  # Use mock bridge for testing without hardware

    # Camera settings
    camera_enabled: bool = True
    camera_width: int = 640
    camera_height: int = 480
    camera_framerate: int = 30
    camera_flip_180: bool = False  # Flip camera 180 degrees (hflip + vflip)

    # Safety (placeholders)
    deadman_timeout_ms: int = 500
    command_rate_limit_hz: int = 50

    @property
    def ice_servers(self) -> list[dict[str, str | list[str]]]:
        """Build ICE server configuration for WebRTC."""
        servers = [{"urls": [self.stun_server]}]
        if self.turn_server and self.turn_username and self.turn_password:
            servers.append(
                {
                    "urls": [self.turn_server],
                    "username": self.turn_username,
                    "credential": self.turn_password,
                }
            )
        return servers


# Global settings instance
settings = Settings()
