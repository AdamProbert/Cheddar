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
    import libcamera

    PICAMERA2_AVAILABLE = True
except ImportError:
    logger.warning("picamera2 not available - camera streaming will be disabled")
    PICAMERA2_AVAILABLE = False
    libcamera = None  # type: ignore


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
        flip_180: bool = False,
        use_mock: bool = False,
        is_noir: bool = True,
        awb_mode: str = "manual",
        color_gains: tuple[float, float] = (2.0, 1.2),
    ) -> None:
        """
        Initialize the Pi camera video track.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            framerate: Target framerate (FPS)
            flip_180: Flip camera 180 degrees (useful for upside-down mounting)
            use_mock: If True, use mock video source instead of real camera
            is_noir: If True, apply color correction for NoIR (No IR filter) camera
            awb_mode: Auto white balance mode (auto, greyworld, daylight, etc.)
            color_gains: Manual color gains (red, blue) - only used if awb_mode is None
        """
        super().__init__()
        self.width = width
        self.height = height
        self.framerate = framerate
        self.flip_180 = flip_180
        self.use_mock = use_mock or not PICAMERA2_AVAILABLE
        self.is_noir = is_noir
        self.awb_mode = awb_mode
        self.color_gains = color_gains

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
            logger.info(
                f"Initializing Pi camera: {self.width}x{self.height}@{self.framerate}fps, flip_180={self.flip_180}"
            )

            self.camera = Picamera2()

            # Build controls dictionary
            controls = {"FrameRate": self.framerate}

            if self.awb_mode and self.awb_mode.lower() != "manual":
                # AWB modes are set by index, not enum
                awb_mode_index = {
                    "auto": 0,
                    "incandescent": 1,
                    "tungsten": 2,
                    "fluorescent": 3,
                    "indoor": 4,
                    "daylight": 5,
                    "cloudy": 6,
                    "greyworld": 0,  # Use auto mode as fallback for greyworld
                }

                if self.awb_mode.lower() in awb_mode_index:
                    controls["AwbEnable"] = True
                    controls["AwbMode"] = awb_mode_index[self.awb_mode.lower()]
                    logger.info(
                        f"Using AWB mode: {self.awb_mode} (index {awb_mode_index[self.awb_mode.lower()]})"
                    )
                else:
                    logger.warning(f"Unknown AWB mode: {self.awb_mode}, using Auto")
                    controls["AwbEnable"] = True
                    controls["AwbMode"] = 0
            else:
                # Manual color gains
                controls["AwbEnable"] = False
                controls["ColourGains"] = self.color_gains
                logger.info(
                    f"Using manual color gains: {self.color_gains}"
                )  # Configure camera for video streaming
            video_config = self.camera.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls=controls,
            )

            # Flip camera 180 degrees if needed (for upside-down mounting)
            if self.flip_180:
                video_config["transform"] = libcamera.Transform(hflip=1, vflip=1)

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

                # Use BGR format directly - picamera2 RGB888 seems to output BGR order
                frame = VideoFrame.from_ndarray(array, format="bgr24")
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

    def update_settings(
        self,
        awb_mode: Optional[str] = None,
        color_gains: Optional[tuple[float, float]] = None,
        framerate: Optional[int] = None,
    ) -> None:
        """
        Update camera settings on the fly.

        Args:
            awb_mode: Auto white balance mode (auto, greyworld, daylight, etc.)
            color_gains: Manual color gains (red, blue)
            framerate: Target framerate (FPS)
        """
        # Always update internal state (will be used when camera initializes)
        if awb_mode is not None:
            self.awb_mode = awb_mode
            logger.info(f"Set AWB mode to: {self.awb_mode}")
        if color_gains is not None:
            self.color_gains = color_gains
            logger.info(f"Set color gains to: {self.color_gains}")
        if framerate is not None:
            self.framerate = framerate
            logger.info(f"Set framerate to: {framerate}")

        # If camera is running, apply settings immediately
        if self.camera and not self.use_mock:
            try:
                # Apply settings to camera
                controls = {}

                if self.awb_mode and self.awb_mode.lower() != "manual":
                    # AWB modes are set by index
                    awb_mode_index = {
                        "auto": 0,
                        "incandescent": 1,
                        "tungsten": 2,
                        "fluorescent": 3,
                        "indoor": 4,
                        "daylight": 5,
                        "cloudy": 6,
                        "greyworld": 0,  # Use auto mode as fallback
                    }
                    if self.awb_mode.lower() in awb_mode_index:
                        controls["AwbEnable"] = True
                        controls["AwbMode"] = awb_mode_index[self.awb_mode.lower()]
                else:
                    controls["AwbEnable"] = False
                    controls["ColourGains"] = self.color_gains

                if framerate is not None:
                    controls["FrameRate"] = framerate

                # Apply controls to running camera
                self.camera.set_controls(controls)
                logger.info("Applied settings to running camera")

            except Exception as e:
                logger.error(f"Failed to apply camera settings: {e}")
        else:
            logger.info("Settings saved - will be applied when camera starts")

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
        flip_180: bool = False,
        enabled: bool = True,
        is_noir: bool = True,
        awb_mode: str = "manual",
        color_gains: tuple[float, float] = (2.0, 1.2),
    ) -> None:
        """
        Initialize camera manager.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            framerate: Target framerate (FPS)
            flip_180: Flip camera 180 degrees (useful for upside-down mounting)
            enabled: Whether camera is enabled
            is_noir: Whether using NoIR camera (requires color correction)
            awb_mode: Auto white balance mode (use 'manual' for color gains)
            color_gains: Manual color gains (red, blue) - only active when awb_mode='manual'
        """
        self.width = width
        self.height = height
        self.framerate = framerate
        self.flip_180 = flip_180
        self.enabled = enabled
        self.is_noir = is_noir
        self.awb_mode = awb_mode
        self.color_gains = color_gains
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
            flip_180=self.flip_180,
            use_mock=not PICAMERA2_AVAILABLE,
            is_noir=self.is_noir,
            awb_mode=self.awb_mode,
            color_gains=self.color_gains,
        )

        return self.current_track

    def update_settings(
        self,
        awb_mode: Optional[str] = None,
        color_gains: Optional[tuple[float, float]] = None,
        framerate: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> dict:
        """
        Update camera settings on the fly.

        Args:
            awb_mode: Auto white balance mode
            color_gains: Manual color gains (red, blue)
            framerate: Target framerate (FPS)
            width: Video width (requires restart)
            height: Video height (requires restart)

        Returns:
            dict with update status and whether restart is needed
        """
        needs_restart = False

        # Update manager state
        if awb_mode is not None:
            self.awb_mode = awb_mode
        if color_gains is not None:
            self.color_gains = color_gains
        if framerate is not None:
            self.framerate = framerate

        # Resolution changes require full restart
        if width is not None and width != self.width:
            self.width = width
            needs_restart = True
        if height is not None and height != self.height:
            self.height = height
            needs_restart = True

        # Update running track if exists
        if self.current_track and not needs_restart:
            self.current_track.update_settings(
                awb_mode=awb_mode,
                color_gains=color_gains,
                framerate=framerate,
            )
            return {"success": True, "needs_restart": False}

        return {"success": True, "needs_restart": needs_restart}

    def cleanup(self) -> None:
        """Clean up camera resources."""
        if self.current_track:
            logger.info("Cleaning up camera manager")
            self.current_track.stop()
            self.current_track = None
