"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SDPOffer(BaseModel):
    """WebRTC SDP offer from client."""

    sdp: str = Field(..., description="Session Description Protocol offer")
    type: Literal["offer"] = Field(default="offer", description="SDP type")


class SDPAnswer(BaseModel):
    """WebRTC SDP answer from server."""

    sdp: str = Field(..., description="Session Description Protocol answer")
    type: Literal["answer"] = Field(default="answer", description="SDP type")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    version: str = Field(default="0.1.0", description="API version")


class ControlCommand(BaseModel):
    """Robot control command sent via DataChannel."""

    type: Literal["motor", "servo", "ping", "stop"] = Field(..., description="Command type")
    motor_left: float | None = Field(None, ge=-1.0, le=1.0, description="Left motor speed")
    motor_right: float | None = Field(None, ge=-1.0, le=1.0, description="Right motor speed")
    servo_pan: int | None = Field(None, ge=0, le=180, description="Pan servo angle")
    servo_tilt: int | None = Field(None, ge=0, le=180, description="Tilt servo angle")
    timestamp: float = Field(..., description="Client timestamp in milliseconds")


class TelemetryData(BaseModel):
    """Telemetry data sent to client via DataChannel."""

    type: Literal["telemetry", "pong"] = Field(default="telemetry", description="Message type")
    battery_voltage: float | None = Field(None, description="Battery voltage in volts")
    current_draw: float | None = Field(None, description="Current draw in amps")
    cpu_temp: float | None = Field(None, description="CPU temperature in Celsius")
    signal_strength: int | None = Field(None, ge=0, le=100, description="WiFi signal strength %")
    timestamp: float = Field(..., description="Server timestamp in milliseconds")
    latency_ms: float | None = Field(None, description="Round-trip latency if pong")


class SystemMetrics(BaseModel):
    """System metrics data sent via DataChannel."""

    type: Literal["metrics"] = Field(default="metrics", description="Message type")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    cpu_temp: float | None = Field(None, description="CPU temperature in Celsius")
    disk_percent: float | None = Field(None, description="Disk usage percentage")
    timestamp: float = Field(..., description="Server timestamp in milliseconds")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
