from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import SerialConfig
from serial_bridge import CommandError, SerialBridge, create_bridge

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
_LOGGER = logging.getLogger("motiondriver.webapp")

app = FastAPI(title="MotionDriver Control", version="0.1.0")

_static_dir = Path(__file__).parent / "static"
if not _static_dir.exists():  # pragma: no cover - guards against missing assets
    _LOGGER.warning("Static directory %s not found", _static_dir)

app.mount("/static", StaticFiles(directory=_static_dir), name="static")

_bridge = create_bridge(SerialConfig())


class ServoCommand(BaseModel):
    channel: int = Field(..., ge=0, le=5, description="Servo channel (0-5)")
    pulse_us: int = Field(
        ..., ge=500, le=2500, description="Pulse width in microseconds"
    )


class MotorRunRequest(BaseModel):
    target: str = Field(..., description="Motor index 0-5 or 'ALL'")
    direction: str = Field(..., pattern="^(?i)(forward|backward)$")
    speed: Optional[float] = Field(1.0, ge=0.0, le=1.0)


class MotorToggleRequest(BaseModel):
    target: str = Field(..., description="Motor index 0-5 or 'ALL'")


class SweepRequest(BaseModel):
    enabled: bool
    sweep_range: Optional[str] = Field(
        None,
        description="Optional sweep range token (e.g. '0-5', 'ALL', '2')",
        pattern=r"^(?i)(all|\[all\]|\d+-\d+|\d+)$",
    )


class LogRequest(BaseModel):
    enabled: bool


@app.exception_handler(CommandError)
async def handle_command_error(_: Request, exc: CommandError) -> JSONResponse:
    return JSONResponse(
        status_code=400, content={"status": "error", "detail": str(exc)}
    )


@app.exception_handler(ValueError)
async def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"status": "error", "detail": str(exc)}
    )


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    if not _static_dir.exists():
        raise HTTPException(status_code=500, detail="Web assets missing")
    index_path = _static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="index.html not found")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/api/ping")
async def api_ping() -> JSONResponse:
    response = _bridge.ping()
    return JSONResponse({"status": "ok", "response": response})


@app.post("/api/servo")
async def api_servo(command: ServoCommand) -> JSONResponse:
    response = _bridge.set_servo(command.channel, command.pulse_us)
    return JSONResponse({"status": "ok", "response": response})


@app.post("/api/motor/run")
async def api_motor_run(command: MotorRunRequest) -> JSONResponse:
    response = _bridge.motor_run(command.target, command.direction, command.speed)
    return JSONResponse({"status": "ok", "response": response})


@app.post("/api/motor/start")
async def api_motor_start(command: MotorToggleRequest) -> JSONResponse:
    response = _bridge.motor_start(command.target)
    return JSONResponse({"status": "ok", "response": response})


@app.post("/api/motor/stop")
async def api_motor_stop(command: MotorToggleRequest) -> JSONResponse:
    response = _bridge.motor_stop(command.target)
    return JSONResponse({"status": "ok", "response": response})


@app.post("/api/sweep")
async def api_sweep(command: SweepRequest) -> JSONResponse:
    response = _bridge.set_sweep(command.enabled, command.sweep_range)
    return JSONResponse({"status": "ok", "response": response})


@app.post("/api/log")
async def api_log(command: LogRequest) -> JSONResponse:
    response = _bridge.set_log(command.enabled)
    return JSONResponse({"status": "ok", "response": response})


@app.on_event("shutdown")
def shutdown_event() -> None:
    _LOGGER.info("Shutting down serial bridge")
    _bridge.close()
