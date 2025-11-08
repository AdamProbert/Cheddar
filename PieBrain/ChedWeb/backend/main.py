"""FastAPI application for rover control backend."""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from models import SDPOffer, SDPAnswer, HealthResponse, ControlCommand, ErrorResponse
from peer_manager import PeerManager
from camera import CameraManager


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    global peer_manager, camera_manager
    logger.info("Starting ChedWeb backend...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"ICE servers: {settings.ice_servers}")
    logger.info(f"Camera enabled: {settings.camera_enabled}")

    # Initialize camera manager
    camera_manager = CameraManager(
        width=settings.camera_width,
        height=settings.camera_height,
        framerate=settings.camera_framerate,
        rotation=settings.camera_rotation,
        enabled=settings.camera_enabled,
    )

    # Initialize peer manager
    peer_manager = PeerManager(ice_servers=settings.ice_servers)

    # TODO: Initialize serial bridge for UART communication
    # serial_bridge = SerialBridge(settings.serial_port, settings.serial_baudrate)
    # await serial_bridge.connect()
    # peer_manager.set_command_callback(serial_bridge.send_command)

    yield

    # Cleanup
    logger.info("Shutting down ChedWeb backend...")
    if peer_manager:
        await peer_manager.close()
    if camera_manager:
        camera_manager.cleanup()
    # if serial_bridge:
    #     await serial_bridge.disconnect()


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


@app.get("/healthz", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.post("/signaling/offer", response_model=SDPAnswer, tags=["WebRTC"])
async def handle_signaling_offer(offer: SDPOffer) -> SDPAnswer:
    """
    Handle WebRTC signaling offer and return answer.

    This endpoint receives an SDP offer from the client, creates a peer connection,
    and returns an SDP answer to complete the WebRTC negotiation.
    """
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
        logger.info("Returning SDP answer to client")
        return SDPAnswer(sdp=answer_sdp, type="answer")
    except Exception as e:
        logger.error(f"Error handling signaling offer: {e}")
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
