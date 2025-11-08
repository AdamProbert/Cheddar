"""WebRTC peer connection manager with DataChannel support."""

import asyncio
import json
import time
from typing import Callable, Optional

import psutil
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
from loguru import logger

from models import ControlCommand, TelemetryData, SystemMetrics
from camera import PiCameraVideoTrack


class PeerManager:
    """Manages a WebRTC peer connection with DataChannel for control/telemetry."""

    def __init__(
        self,
        ice_servers: list[dict[str, str | list[str]]],
        video_track: Optional[PiCameraVideoTrack] = None,
    ) -> None:
        """Initialize peer manager with ICE server configuration."""
        self.ice_servers = ice_servers
        self.video_track = video_track
        self.pc: RTCPeerConnection | None = None
        self.control_channel: RTCDataChannel | None = None
        self.on_command_callback: Callable[[ControlCommand], None] | None = None
        self.metrics_task: asyncio.Task | None = None

    def _setup_datachannel(self, channel: RTCDataChannel) -> None:
        """Set up message handlers for the control DataChannel."""

        @channel.on("open")
        def on_open() -> None:
            logger.info(f"DataChannel '{channel.label}' opened")
            # Send initial telemetry to confirm connection
            self._send_telemetry(
                TelemetryData(
                    type="telemetry",
                    timestamp=time.time() * 1000,
                    battery_voltage=None,  # TODO: Read from sensors
                    current_draw=None,
                    cpu_temp=None,
                    signal_strength=None,
                )
            )
            # Start system metrics loop
            asyncio.create_task(self._start_metrics_loop())

        @channel.on("message")
        def on_message(message: str) -> None:
            """Handle incoming control commands."""
            try:
                data = json.loads(message)
                logger.debug(f"Received message: {data}")

                # Handle ping/pong for latency measurement
                if data.get("type") == "ping":
                    client_timestamp = data.get("timestamp", 0)
                    self._send_pong(client_timestamp)
                    return

                # Parse and validate control command
                command = ControlCommand(**data)
                logger.info(f"Control command: {command}")

                # TODO: Forward command to UART/ESP32 serial bridge
                if self.on_command_callback:
                    self.on_command_callback(command)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

        @channel.on("close")
        def on_close() -> None:
            logger.info(f"DataChannel '{channel.label}' closed")
            # TODO: Implement deadman switch - stop all motors on disconnect

    def _send_pong(self, client_timestamp: float) -> None:
        """Send pong response for latency measurement."""
        if not self.control_channel or self.control_channel.readyState != "open":
            return

        pong = TelemetryData(
            type="pong",
            timestamp=time.time() * 1000,
            latency_ms=time.time() * 1000 - client_timestamp,
        )
        self.control_channel.send(pong.model_dump_json())

    def _send_telemetry(self, telemetry: TelemetryData) -> None:
        """Send telemetry data to client."""
        if not self.control_channel or self.control_channel.readyState != "open":
            return

        try:
            self.control_channel.send(telemetry.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send telemetry: {e}")

    def _send_metrics(self, metrics: SystemMetrics) -> None:
        """Send system metrics data to client."""
        if not self.control_channel or self.control_channel.readyState != "open":
            return

        try:
            self.control_channel.send(metrics.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send metrics: {e}")

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics using psutil."""
        # Get CPU temperature (Raspberry Pi specific)
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            if temps and "cpu_thermal" in temps:
                cpu_temp = temps["cpu_thermal"][0].current
        except Exception as e:
            logger.debug(f"Could not read CPU temperature: {e}")

        # Get disk usage for root partition
        disk_percent = None
        try:
            disk_percent = psutil.disk_usage("/").percent
        except Exception as e:
            logger.debug(f"Could not read disk usage: {e}")

        return SystemMetrics(
            type="metrics",
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            cpu_temp=cpu_temp,
            disk_percent=disk_percent,
            timestamp=time.time() * 1000,
        )

    async def _start_metrics_loop(self, interval_seconds: float = 1.0) -> None:
        """Send system metrics at regular intervals via DataChannel."""
        logger.info(f"Starting system metrics loop (interval={interval_seconds}s)")
        try:
            while self.control_channel and self.control_channel.readyState == "open":
                metrics = self._collect_system_metrics()
                self._send_metrics(metrics)
                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Metrics loop cancelled")
        except Exception as e:
            logger.error(f"Error in metrics loop: {e}")

    async def handle_offer(self, offer_sdp: str) -> str:
        """Handle SDP offer and return SDP answer."""
        if not self.pc:
            # Create peer connection
            self.pc = RTCPeerConnection()

            @self.pc.on("connectionstatechange")
            async def on_connectionstatechange() -> None:
                logger.info(f"Connection state: {self.pc.connectionState}")
                if self.pc.connectionState == "failed":
                    await self.close()

            @self.pc.on("datachannel")
            def on_datachannel(channel: RTCDataChannel) -> None:
                logger.info(f"DataChannel created: {channel.label}")
                if channel.label == "control":
                    self.control_channel = channel
                    self._setup_datachannel(channel)

            # Add video track before processing offer so it's included in negotiation
            if self.video_track:
                logger.info("Adding video track to peer connection")
                self.pc.addTrack(self.video_track)
            else:
                logger.warning("No video track available - video streaming disabled")

        # Set remote description
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self.pc.setRemoteDescription(offer)

        # Create answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        logger.info("SDP offer/answer exchange completed")
        return self.pc.localDescription.sdp

    async def close(self) -> None:
        """Close the peer connection and clean up resources."""
        if self.metrics_task and not self.metrics_task.done():
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass

        if self.control_channel:
            self.control_channel.close()
            self.control_channel = None

        if self.pc:
            await self.pc.close()
            self.pc = None

        logger.info("Peer connection closed")

    def set_command_callback(self, callback: Callable[[ControlCommand], None]) -> None:
        """Register callback for received control commands."""
        self.on_command_callback = callback

    # TODO: Add periodic telemetry sender
    async def start_telemetry_loop(self, interval_ms: int = 100) -> None:
        """Send telemetry data at regular intervals (placeholder for future)."""
        while self.control_channel and self.control_channel.readyState == "open":
            # TODO: Read actual sensor data
            telemetry = TelemetryData(
                type="telemetry",
                timestamp=time.time() * 1000,
                battery_voltage=None,
                current_draw=None,
                cpu_temp=None,
                signal_strength=None,
            )
            self._send_telemetry(telemetry)
            await asyncio.sleep(interval_ms / 1000.0)
