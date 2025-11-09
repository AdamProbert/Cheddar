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
    global peer_manager, camera_manager, motion_driver
    logger.info("Starting ChedWeb backend...")
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
        awb_mode="manual",  # Use manual mode to allow color gain adjustments
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
        )

    try:
        await motion_driver.connect()
    except Exception as e:
        logger.error(f"Failed to connect to MotionDriver: {e}")
        logger.warning("Continuing without MotionDriver - commands will be ignored")
        motion_driver = None

    # Initialize peer manager with motion driver
    peer_manager = PeerManager(
        ice_servers=settings.ice_servers,
        motion_driver=motion_driver,
    )

    # Initialize metrics
    metrics.camera_enabled.set(1 if settings.camera_enabled else 0)
    metrics.motion_driver_connected.set(1 if motion_driver else 0)
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

    yield

    # Cleanup
    logger.info("Shutting down ChedWeb backend...")
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass

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


@app.websocket("/ws/debug")
async def websocket_debug(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for debugging and testing.

    Echoes back any JSON messages received. Useful for quick connectivity tests.
    """
    await websocket.accept()
    logger.info("WebSocket debug connection established")

    try:
        while True:
            # Receive and echo JSON messages
            data = await websocket.receive_json()
            logger.debug(f"WebSocket received: {data}")
            await websocket.send_json({"echo": data, "timestamp": __import__("time").time()})
    except WebSocketDisconnect:
        logger.info("WebSocket debug connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


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
