"""FastAPI application for rover control backend."""

import sys
import traceback
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import asyncio

from config import settings
from models import (
    SDPOffer,
    SDPAnswer,
    HealthResponse,
    ControlCommand,
    ErrorResponse,
    CameraSettings,
    CameraSettingsResponse,
)
from peer_manager import PeerManager
from camera import CameraManager
from motion_driver_bridge import MotionDriverBridge, MockMotionDriverBridge
import metrics
import debug_hub
from debug_hub import PowerMonitor


# Configure structured logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)

# Global manager instances
peer_manager: PeerManager | None = None
camera_manager: CameraManager | None = None
motion_driver: MotionDriverBridge | MockMotionDriverBridge | None = None
power_monitor: PowerMonitor | None = None


async def update_metrics_periodically():
    """Background task to update system metrics periodically."""
    while True:
        try:
            metrics.update_process_metrics()
            await asyncio.sleep(15)  # Update every 15 seconds
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    global peer_manager, camera_manager, motion_driver, power_monitor
    logger.info("Starting ChedWeb backend...")
    # Mirror application logs into the Debug tab's live log stream.
    debug_hub.install_log_capture(level=settings.log_level)
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"ICE servers: {settings.ice_servers}")
    logger.info(f"Camera enabled: {settings.camera_enabled}")
    logger.info(f"Serial port: {settings.serial_port}")
    logger.info(f"Serial mock mode: {settings.serial_mock}")

    # Initialize camera manager
    camera_manager = CameraManager(
        width=settings.camera_width,
        height=settings.camera_height,
        framerate=settings.camera_framerate,
        flip_180=settings.camera_flip_180,
        enabled=settings.camera_enabled,
        is_noir=True,  # Set to True for NoIR cameras
        awb_mode="auto",  # Auto white balance by default
        color_gains=(2.0, 1.2),  # Higher red gain to reduce purple tint on NoIR
    )

    # Initialize MotionDriver serial bridge
    if settings.serial_mock:
        logger.info("Using MOCK MotionDriver bridge (no hardware)")
        motion_driver = MockMotionDriverBridge(
            port=settings.serial_port,
            baudrate=settings.serial_baudrate,
        )
    else:
        logger.info(f"Initializing MotionDriver on {settings.serial_port}")
        motion_driver = MotionDriverBridge(
            port=settings.serial_port,
            baudrate=settings.serial_baudrate,
            heartbeat_interval=settings.serial_heartbeat_interval,
            reconnect_interval=settings.serial_reconnect_interval,
        )

    try:
        await motion_driver.connect()
    except Exception as e:
        # The bridge supervisor keeps retrying in the background, so keep the
        # instance around rather than dropping to None.
        logger.error(f"MotionDriver initial connect error: {e}")
        logger.warning("MotionDriver will keep retrying to connect in the background")

    # Initialize peer manager with motion driver
    peer_manager = PeerManager(
        ice_servers=settings.ice_servers,
        motion_driver=motion_driver,
    )

    # Initialize metrics
    metrics.camera_enabled.set(1 if settings.camera_enabled else 0)
    metrics.motion_driver_connected.set(
        1 if (motion_driver and motion_driver.is_connected()) else 0
    )
    if camera_manager:
        metrics.camera_resolution.info(
            {
                "width": str(camera_manager.width),
                "height": str(camera_manager.height),
                "framerate": str(camera_manager.framerate),
            }
        )

    # Start background metrics update task
    metrics_task = asyncio.create_task(update_metrics_periodically())

    # Start Pi power/brownout monitor (no-op off real Pi hardware)
    power_monitor = PowerMonitor()
    await power_monitor.start()

    yield

    # Cleanup
    logger.info("Shutting down ChedWeb backend...")
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass

    if power_monitor:
        await power_monitor.stop()
    if peer_manager:
        await peer_manager.close()
    if camera_manager:
        camera_manager.cleanup()
    if motion_driver:
        await motion_driver.disconnect()


# Create FastAPI application
app = FastAPI(
    title="ChedWeb Rover Control API",
    description="Raspberry Pi-based rover control with WebRTC video and DataChannel commands",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins in development
# TODO: Restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Metrics middleware to track HTTP requests
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track HTTP request metrics."""
    method = request.method
    endpoint = request.url.path

    # Skip metrics endpoint itself to avoid recursion
    if endpoint == "/metrics":
        return await call_next(request)

    # Track in-progress requests
    metrics.http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    start_time = time.time()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        logger.error(f"Error in request {method} {endpoint}: {e}")
        metrics.errors_total.labels(error_type="http_exception", component="api").inc()
        raise
    finally:
        # Track request completion
        duration = time.time() - start_time
        metrics.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code,
        ).inc()
        metrics.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)
        metrics.http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


# Add validation exception handler for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url}")
    logger.error(f"Errors: {exc.errors()}")
    logger.error(f"Body: {exc.body}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/healthz", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.get("/metrics", tags=["System"])
async def get_metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Exposes application and system metrics in Prometheus format
    for scraping by Grafana Alloy or other Prometheus-compatible collectors.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/signaling/offer", response_model=SDPAnswer, tags=["WebRTC"])
async def handle_signaling_offer(offer: SDPOffer) -> SDPAnswer:
    """
    Handle WebRTC signaling offer and return answer.

    This endpoint receives an SDP offer from the client, creates a peer connection,
    and returns an SDP answer to complete the WebRTC negotiation.
    """
    logger.info(f"Received request at /signaling/offer")
    logger.debug(f"Offer payload: {offer}")

    if not peer_manager:
        raise HTTPException(status_code=500, detail="Peer manager not initialized")

    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")

    try:
        logger.info("Received SDP offer from client")

        # Close any existing peer connection before creating a new one
        if peer_manager.pc:
            logger.info("Closing existing peer connection")
            await peer_manager.close()
            metrics.webrtc_connections_active.dec()

        # Create a new video track for this connection
        video_track = camera_manager.create_video_track()
        if video_track:
            logger.info("Video track created successfully")
        else:
            logger.warning("No video track created - camera may be disabled")

        # Update peer manager with the video track before handling offer
        peer_manager.video_track = video_track

        # Process the offer and create answer (this will create peer connection with video track)
        answer_sdp = await peer_manager.handle_offer(offer.sdp)

        # Track successful WebRTC connection
        metrics.webrtc_connections_total.labels(status="success").inc()
        metrics.webrtc_connections_active.inc()

        logger.info("Returning SDP answer to client")
        return SDPAnswer(sdp=answer_sdp, type="answer")
    except Exception as e:
        logger.error(f"Error handling signaling offer: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Track failed WebRTC connection
        metrics.webrtc_connections_total.labels(status="failed").inc()
        metrics.errors_total.labels(error_type="webrtc_offer", component="webrtc").inc()

        raise HTTPException(status_code=500, detail=str(e))


def _heartbeat_snapshot() -> dict:
    """Heartbeat stats for the Debug tab, plus the deadman window for context."""
    if not motion_driver:
        return {"available": False, "deadman_ms": settings.deadman_timeout_ms}
    stats = motion_driver.heartbeat_stats()
    stats["available"] = True
    stats["deadman_ms"] = settings.deadman_timeout_ms
    return stats


async def _handle_debug_command(data: dict, armed: dict, out: asyncio.Queue) -> None:
    """Apply a single inbound debug command. Motion is gated behind ``armed``."""
    if not motion_driver:
        out.put_nowait({"type": "error", "detail": "MotionDriver not initialised"})
        return

    cmd_type = data.get("type")

    # Arm / disarm the motor drive controls.
    if cmd_type == "arm":
        armed["value"] = bool(data.get("value"))
        if not armed["value"]:
            await motion_driver.send_raw("MOTOR ALL STOP\n")
        out.put_nowait({"type": "armed", "value": armed["value"]})
        return

    # Emergency + plain stop are always allowed and clear the armed state.
    if cmd_type in ("estop", "stop"):
        await motion_driver.send_raw("MOTOR ALL STOP\n")
        armed["value"] = False
        out.put_nowait({"type": "armed", "value": False})
        return

    # Stop a single motor (or all) — never gated.
    if cmd_type == "motor_stop":
        target = data.get("index", "all")
        target = "ALL" if str(target).lower() == "all" else int(target)
        await motion_driver.send_raw(f"MOTOR {target} STOP\n")
        return

    # Drive a single motor — requires the motors to be armed.
    if cmd_type == "motor":
        if not armed["value"]:
            out.put_nowait({"type": "error", "detail": "Motors are disarmed"})
            return
        index = int(data.get("index", -1))
        direction = str(data.get("direction", "")).upper()
        speed = float(data.get("speed", 0.0))
        if not 0 <= index <= 5 or direction not in ("FORWARD", "BACKWARD"):
            out.put_nowait({"type": "error", "detail": "Invalid motor command"})
            return
        speed = max(0.0, min(1.0, speed))
        if speed == 0.0:
            await motion_driver.send_raw(f"MOTOR {index} STOP\n")
        else:
            await motion_driver.send_raw(f"MOTOR {index} {direction} {speed:.2f}\n")
        return

    # Steering servo — pulse width in microseconds. Not gated (servos hold).
    if cmd_type == "servo":
        channel = int(data.get("channel", -1))
        pulse_us = int(data.get("pulse_us", 0))
        if not 0 <= channel <= 5 or not 500 <= pulse_us <= 2500:
            out.put_nowait({"type": "error", "detail": "Invalid servo command"})
            return
        await motion_driver.send_raw(f"S {channel} {pulse_us}\n")
        return

    # Raw console line — whitelisted verbs only, motion gated behind arm.
    if cmd_type == "raw":
        line = str(data.get("line", ""))
        ok, reason = debug_hub.validate_raw_command(line)
        if not ok:
            out.put_nowait({"type": "error", "detail": reason})
            return
        if debug_hub.is_motion_command(line) and not armed["value"]:
            out.put_nowait({"type": "error", "detail": "Motors are disarmed"})
            return
        await motion_driver.send_raw(line.strip() + "\n")
        return

    out.put_nowait({"type": "error", "detail": f"Unknown command type: {cmd_type}"})


@app.websocket("/ws/debug")
async def websocket_debug(websocket: WebSocket) -> None:
    """Live debug channel: streams serial TX/RX, heartbeat, power flags and
    logs to the browser, and accepts whitelisted actuator/console commands.

    Independent of the WebRTC connection so it keeps working during a brownout
    or a failed video negotiation — exactly when you need to debug.
    """
    await websocket.accept()
    logger.info("Debug WebSocket connected")

    armed = {"value": False}
    out: asyncio.Queue = asyncio.Queue(maxsize=2000)
    serial_q = motion_driver.events.subscribe() if motion_driver else None
    log_q = debug_hub.log_broadcaster.subscribe()

    # Seed the client with recent history and current state.
    await websocket.send_json(
        {
            "type": "snapshot",
            "serial": motion_driver.events.recent() if motion_driver else [],
            "logs": debug_hub.log_broadcaster.recent(),
            "heartbeat": _heartbeat_snapshot(),
            "power": power_monitor.snapshot() if power_monitor else {"available": False},
            "config": {
                "deadman_ms": settings.deadman_timeout_ms,
                "heartbeat_interval_ms": settings.serial_heartbeat_interval * 1000,
                "serial_mock": settings.serial_mock,
            },
        }
    )

    async def relay(queue: asyncio.Queue, kind: str) -> None:
        while True:
            event = await queue.get()
            try:
                out.put_nowait({"type": kind, **event})
            except asyncio.QueueFull:
                pass

    async def periodic() -> None:
        while True:
            await asyncio.sleep(0.5)
            try:
                out.put_nowait({"type": "heartbeat", **_heartbeat_snapshot()})
                if power_monitor:
                    out.put_nowait({"type": "power", **power_monitor.snapshot()})
            except asyncio.QueueFull:
                pass

    async def sender() -> None:
        while True:
            msg = await out.get()
            await websocket.send_json(msg)

    async def receiver() -> None:
        while True:
            data = await websocket.receive_json()
            try:
                await _handle_debug_command(data, armed, out)
            except Exception as exc:
                logger.error(f"Debug command error: {exc}")
                out.put_nowait({"type": "error", "detail": str(exc)})

    tasks = [asyncio.create_task(sender()), asyncio.create_task(periodic()), asyncio.create_task(receiver())]
    if serial_q is not None:
        tasks.append(asyncio.create_task(relay(serial_q, "serial")))
    tasks.append(asyncio.create_task(relay(log_q, "log")))

    try:
        # Finish as soon as any task ends (receiver on disconnect, or an error).
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except WebSocketDisconnect:
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if motion_driver and serial_q is not None:
            motion_driver.events.unsubscribe(serial_q)
        debug_hub.log_broadcaster.unsubscribe(log_q)
        # Safety: a debug session may have left a motor running. Stop on exit.
        if motion_driver:
            try:
                await motion_driver.send_raw("MOTOR ALL STOP\n")
            except Exception:
                pass
        logger.info("Debug WebSocket closed")


@app.get("/api/config", tags=["Configuration"])
async def get_config() -> dict[str, str | int]:
    """
    Get public configuration for client.

    Returns non-sensitive configuration values needed by the frontend.
    """
    return {
        "version": "0.1.0",
        "stun_server": settings.stun_server,
        "command_rate_limit_hz": settings.command_rate_limit_hz,
        "deadman_timeout_ms": settings.deadman_timeout_ms,
    }


@app.get("/api/camera/settings", tags=["Camera"])
async def get_camera_settings() -> dict:
    """Get current camera settings."""
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not initialized")

    return {
        "enabled": camera_manager.enabled,
        "width": camera_manager.width,
        "height": camera_manager.height,
        "framerate": camera_manager.framerate,
        "flip_180": camera_manager.flip_180,
        "is_noir": camera_manager.is_noir,
        "awb_mode": camera_manager.awb_mode,
        "color_gains": camera_manager.color_gains,
    }


@app.post("/api/camera/settings", response_model=CameraSettingsResponse, tags=["Camera"])
async def update_camera_settings(settings: CameraSettings) -> CameraSettingsResponse:
    """
    Update camera settings on the fly.

    Note: Changes to width/height require reconnecting the video stream.
    Other settings (AWB, color gains, framerate) apply immediately.
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not initialized")

    # Track which settings changed
    if settings.awb_mode is not None:
        metrics.camera_settings_changes_total.labels(setting="awb_mode").inc()
    if settings.color_gains is not None:
        metrics.camera_settings_changes_total.labels(setting="color_gains").inc()
    if settings.framerate is not None:
        metrics.camera_settings_changes_total.labels(setting="framerate").inc()
    if settings.width is not None or settings.height is not None:
        metrics.camera_settings_changes_total.labels(setting="resolution").inc()

    result = camera_manager.update_settings(
        awb_mode=settings.awb_mode,
        color_gains=settings.color_gains,
        framerate=settings.framerate,
        width=settings.width,
        height=settings.height,
    )

    current_settings = {
        "enabled": camera_manager.enabled,
        "width": camera_manager.width,
        "height": camera_manager.height,
        "framerate": camera_manager.framerate,
        "flip_180": camera_manager.flip_180,
        "is_noir": camera_manager.is_noir,
        "awb_mode": camera_manager.awb_mode,
        "color_gains": camera_manager.color_gains,
    }

    # Update camera resolution metric if changed
    if settings.width is not None or settings.height is not None or settings.framerate is not None:
        metrics.camera_resolution.info(
            {
                "width": str(camera_manager.width),
                "height": str(camera_manager.height),
                "framerate": str(camera_manager.framerate),
            }
        )

    return CameraSettingsResponse(
        success=result["success"],
        needs_restart=result["needs_restart"],
        current_settings=current_settings,
    )


# TODO: Add endpoints for configuration updates, stats, etc.
# @app.post("/api/config/update")
# @app.get("/api/stats")
# @app.post("/api/emergency-stop")


def handle_control_command(command: ControlCommand) -> None:
    """
    Callback for handling control commands from DataChannel.

    TODO: Implement actual command forwarding to UART/ESP32.
    """
    logger.info(f"Handling control command: {command}")
    # Stub: In production, forward to serial bridge
    # serial_bridge.send_command(command)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
