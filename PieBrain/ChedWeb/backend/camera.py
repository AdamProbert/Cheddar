"""Camera video streaming module using picamera2 and aiortc."""

import asyncio
import time
from typing import Optional

import av
import numpy as np
from aiortc import VideoStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame
from loguru import logger

try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except ImportError:
    logger.warning("picamera2 not available - camera streaming will be disabled")
    PICAMERA2_AVAILABLE = False


class PiCameraVideoTrack(VideoStreamTrack):
    """
    VideoStreamTrack implementation using Raspberry Pi camera (picamera2).

    Captures H.264 video from the Pi camera and streams it via WebRTC.
    Uses hardware encoding for optimal performance on Raspberry Pi 3B.
    """

    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        framerate: int = 30,
        rotation: int = 0,
        use_mock: bool = False,
    ) -> None:
        """
        Initialize the Pi camera video track.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            framerate: Target framerate (FPS)
            rotation: Camera rotation in degrees (0, 90, 180, 270)
            use_mock: If True, use mock video source instead of real camera
        """
        super().__init__()
        self.width = width
        self.height = height
        self.framerate = framerate
        self.rotation = rotation
        self.use_mock = use_mock or not PICAMERA2_AVAILABLE

        self.camera: Optional[Picamera2] = None
        self._frame_count = 0
        self._start_time = time.time()
        self._is_running = False

    def _init_camera(self) -> None:
        """Initialize the Picamera2 instance with configuration."""
        if self.use_mock:
            logger.info("Using mock video source (camera not available)")
            return

        if not PICAMERA2_AVAILABLE:
            logger.error("Cannot initialize camera - picamera2 not installed")
            raise ImportError("picamera2 is required for camera streaming")

        try:
            logger.info(f"Initializing Pi camera: {self.width}x{self.height}@{self.framerate}fps")

            self.camera = Picamera2()

            # Configure camera for video streaming
            video_config = self.camera.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": self.framerate},
            )

            # Apply rotation if specified
            if self.rotation != 0:
                video_config["transform"] = {"rotation": self.rotation}

            self.camera.configure(video_config)
            self.camera.start()

            logger.info("Pi camera initialized successfully")
            self._is_running = True

        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.use_mock = True
            logger.info("Falling back to mock video source")

    def _generate_mock_frame(self) -> VideoFrame:
        """Generate a test pattern frame for mock mode."""
        # Create a simple test pattern with timestamp
        frame_data = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Add color bars
        bar_width = self.width // 8
        colors = [
            (255, 255, 255),  # White
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
            (0, 255, 0),  # Green
            (255, 0, 255),  # Magenta
            (255, 0, 0),  # Red
            (0, 0, 255),  # Blue
            (0, 0, 0),  # Black
        ]

        for i, color in enumerate(colors):
            x_start = i * bar_width
            x_end = min((i + 1) * bar_width, self.width)
            frame_data[:, x_start:x_end] = color

        # Add frame counter text area (simplified - just a white box)
        counter_height = 40
        frame_data[:counter_height, :200] = (50, 50, 50)

        # Convert numpy array to av.VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_data, format="rgb24")
        video_frame.pts = self._frame_count
        video_frame.time_base = av.Rational(1, self.framerate)

        return video_frame

    async def recv(self) -> VideoFrame:
        """
        Receive the next video frame.

        This method is called by aiortc to get frames for the video stream.
        """
        if not self._is_running:
            self._init_camera()

        pts, time_base = await self.next_timestamp()

        if self.use_mock:
            # Generate mock frame
            frame = self._generate_mock_frame()
            self._frame_count += 1

            # Simulate framerate delay
            await asyncio.sleep(1.0 / self.framerate)

        else:
            # Capture real frame from camera
            try:
                # Capture frame from picamera2
                array = self.camera.capture_array()

                # Convert to av.VideoFrame
                frame = VideoFrame.from_ndarray(array, format="rgb24")
                frame.pts = pts
                frame.time_base = time_base

                self._frame_count += 1

            except Exception as e:
                logger.error(f"Error capturing frame: {e}")
                raise MediaStreamError(f"Camera capture failed: {e}")

        # Log framerate periodically
        if self._frame_count % (self.framerate * 10) == 0:
            elapsed = time.time() - self._start_time
            actual_fps = self._frame_count / elapsed
            logger.debug(f"Camera stats - Frames: {self._frame_count}, FPS: {actual_fps:.1f}")

        return frame

    def stop(self) -> None:
        """Stop the camera and clean up resources."""
        super().stop()
        self._is_running = False

        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                logger.info("Pi camera stopped and cleaned up")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")
            finally:
                self.camera = None


class CameraManager:
    """
    Manages camera lifecycle and provides video tracks for WebRTC.

    Singleton-style manager to ensure only one camera instance exists.
    """

    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        framerate: int = 30,
        rotation: int = 0,
        enabled: bool = True,
    ) -> None:
        """
        Initialize camera manager.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            framerate: Target framerate (FPS)
            rotation: Camera rotation in degrees (0, 90, 180, 270)
            enabled: Whether camera is enabled
        """
        self.width = width
        self.height = height
        self.framerate = framerate
        self.rotation = rotation
        self.enabled = enabled
        self.current_track: Optional[PiCameraVideoTrack] = None

    def create_video_track(self) -> Optional[PiCameraVideoTrack]:
        """
        Create a new video track for WebRTC streaming.

        Returns:
            PiCameraVideoTrack instance or None if camera is disabled
        """
        if not self.enabled:
            logger.info("Camera is disabled - no video track will be created")
            return None

        # Stop existing track if any
        if self.current_track:
            logger.info("Stopping existing video track")
            self.current_track.stop()

        # Create new track
        logger.info("Creating new camera video track")
        self.current_track = PiCameraVideoTrack(
            width=self.width,
            height=self.height,
            framerate=self.framerate,
            rotation=self.rotation,
            use_mock=not PICAMERA2_AVAILABLE,
        )

        return self.current_track

    def cleanup(self) -> None:
        """Clean up camera resources."""
        if self.current_track:
            logger.info("Cleaning up camera manager")
            self.current_track.stop()
            self.current_track = None
