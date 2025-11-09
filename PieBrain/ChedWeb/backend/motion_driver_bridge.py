"""Serial bridge for communicating with ESP32 MotionDriver via UART."""

import asyncio
from typing import Optional

import serial_asyncio
from loguru import logger

from models import ControlCommand


class MotionDriverBridge:
    """Asynchronous serial bridge to ESP32 MotionDriver.

    Converts high-level ControlCommand messages into UART protocol
    commands that the ESP32 understands.
    """

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        """Initialize serial bridge.

        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0', '/dev/serial0')
            baudrate: Serial baud rate (default: 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False

    async def connect(self) -> None:
        """Open serial connection to MotionDriver."""
        try:
            logger.info(f"Connecting to MotionDriver on {self.port} @ {self.baudrate} baud")
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port, baudrate=self.baudrate
            )
            self.connected = True
            logger.info("MotionDriver connected")

            # Send ping to verify connection
            await self.send_raw("PING\n")
            response = await self.read_line(timeout=2.0)
            if response and "PONG" in response:
                logger.success("MotionDriver responded to PING")
            else:
                logger.warning(f"Unexpected response to PING: {response}")
        except Exception as e:
            logger.error(f"Failed to connect to MotionDriver: {e}")
            self.connected = False
            raise

    async def disconnect(self) -> None:
        """Close serial connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False
        logger.info("MotionDriver disconnected")

    async def send_raw(self, command: str) -> None:
        """Send raw command to MotionDriver.

        Args:
            command: Command string (should include newline if required)
        """
        if not self.writer or not self.connected:
            logger.warning("Cannot send command - not connected")
            return

        try:
            self.writer.write(command.encode("utf-8"))
            await self.writer.drain()
            logger.debug(f"Sent: {command.strip()}")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            self.connected = False

    async def read_line(self, timeout: float = 1.0) -> Optional[str]:
        """Read a line from serial port with timeout.

        Args:
            timeout: Read timeout in seconds

        Returns:
            Line string (without newline) or None on timeout
        """
        if not self.reader or not self.connected:
            return None

        try:
            line_bytes = await asyncio.wait_for(self.reader.readline(), timeout=timeout)
            line = line_bytes.decode("utf-8", errors="ignore").strip()
            logger.debug(f"Received: {line}")
            return line
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Failed to read from serial: {e}")
            self.connected = False
            return None

    async def send_command(self, cmd: ControlCommand) -> None:
        """Convert ControlCommand to UART protocol and send to ESP32.

        Args:
            cmd: High-level control command from frontend
        """
        if not self.connected:
            logger.warning("MotionDriver not connected, command ignored")
            return

        try:
            if cmd.type == "estop" or cmd.type == "stop":
                # Emergency stop: stop all motors using proper protocol
                await self.send_raw("MOTOR ALL STOP\n")
                logger.warning("Emergency stop executed")
                return

            # Motor control - use FORWARD/BACKWARD commands with speed 0.0-1.0
            if cmd.motors:
                for motor_id, speed in enumerate(cmd.motors):
                    if speed == 0:
                        await self.send_raw(f"MOTOR {motor_id} STOP\n")
                    else:
                        # Determine direction and magnitude
                        direction = "FORWARD" if speed > 0 else "BACKWARD"
                        speed_magnitude = abs(speed)  # 0.0 to 1.0
                        await self.send_raw(f"MOTOR {motor_id} {direction} {speed_magnitude}\n")

            # Servo control - ESP32 expects pulse width in microseconds
            if cmd.servos:
                for servo_id, pulse_us in enumerate(cmd.servos):
                    await self.send_raw(f"S {servo_id} {pulse_us}\n")

            # Legacy command support (backwards compatibility)
            if cmd.motor_left is not None or cmd.motor_right is not None:
                left = cmd.motor_left or 0.0
                right = cmd.motor_right or 0.0

                # Map to 6-motor layout (3 left, 3 right)
                for motor_id in [0, 1, 2]:  # Left side
                    if left == 0:
                        await self.send_raw(f"MOTOR {motor_id} STOP\n")
                    else:
                        direction = "FORWARD" if left > 0 else "BACKWARD"
                        await self.send_raw(f"MOTOR {motor_id} {direction} {abs(left)}\n")

                for motor_id in [3, 4, 5]:  # Right side
                    if right == 0:
                        await self.send_raw(f"MOTOR {motor_id} STOP\n")
                    else:
                        direction = "FORWARD" if right > 0 else "BACKWARD"
                        await self.send_raw(f"MOTOR {motor_id} {direction} {abs(right)}\n")

            if cmd.servo_pan is not None:
                # Servo expects pulse width in microseconds (e.g., 1000-2000)
                await self.send_raw(f"S 0 {cmd.servo_pan}\n")
            if cmd.servo_tilt is not None:
                # Servo expects pulse width in microseconds (e.g., 1000-2000)
                await self.send_raw(f"S 1 {cmd.servo_tilt}\n")

        except Exception as e:
            logger.error(f"Error processing command: {e}")

    def is_connected(self) -> bool:
        """Check if serial connection is active."""
        return self.connected


class MockMotionDriverBridge:
    """Mock bridge for testing without hardware."""

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        logger.info(f"[MOCK] MotionDriver bridge initialized (port={port})")
        self.connected = False

    async def connect(self) -> None:
        logger.info("[MOCK] MotionDriver connected")
        self.connected = True

    async def disconnect(self) -> None:
        logger.info("[MOCK] MotionDriver disconnected")
        self.connected = False

    async def send_raw(self, command: str) -> None:
        logger.debug(f"[MOCK] Send: {command.strip()}")

    async def read_line(self, timeout: float = 1.0) -> Optional[str]:
        await asyncio.sleep(0.01)  # Simulate I/O
        return "OK"

    async def send_command(self, cmd: ControlCommand) -> None:
        logger.info(f"[MOCK] Command: {cmd.type} | motors={cmd.motors} | servos={cmd.servos}")

    def is_connected(self) -> bool:
        return self.connected
