#!/usr/bin/env python3
"""Xbox One controller to MotionDriver serial bridge.

Usage (run on Raspberry Pi):
    python -m PieBrain.xbox_control --device /dev/input/event4 --port /dev/ttyS0

Find controller device:
    ls /dev/input/by-id/  # look for *Xbox* event device

This script reads evdev events, constructs normalized throttle/turn axes,
performs differential drive mixing, and issues MOTOR commands to the MotionDriver
firmware via the existing webapp.serial_bridge.SerialBridge abstraction.

Mapping assumptions (may vary slightly by kernel/driver):
- ABS_Y  (value -32768..32767) left stick vertical => throttle (forward negative)
- ABS_RX (value -32768..32767) right stick horizontal => turn (left negative)
- BTN_SOUTH (A) acts as an ALL STOP when tapped.
- BTN_EAST  (B) exits program.

Safety:
- On start sends MOTOR ALL STOP to ensure a known state.
- On exit sends MOTOR ALL STOP.
- Rate-limits command sending to --rate Hz (default 20).
- Deadzone default 0.08.

Environment variable MOTIONDRIVER_SERIAL_PORT can replace --port.
"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from typing import Dict, Optional

from cheddar_serial import SerialConfig, SerialBridge, create_bridge
from .controller_mapping import compute_drive

try:
    from evdev import InputDevice, ecodes  # type: ignore
except Exception as exc:  # pragma: no cover - hardware dependency
    print("evdev import failed:", exc, file=sys.stderr)
    raise

# (No manual path manipulation required; using shared cheddar_serial package)

_LOGGER = logging.getLogger("xbox_control")


@dataclass
class AxisState:
    value: float = 0.0  # normalized -1..1


class XboxController:
    """Wrap an evdev InputDevice to maintain axis/button state."""

    AXIS_NORMALIZERS = {
        ecodes.ABS_Y: lambda v: -(v / 32767.0),  # invert so forward is +
        ecodes.ABS_RX: lambda v: v / 32767.0,
    }

    def __init__(self, device_path: str, deadzone: float) -> None:
        self.dev = InputDevice(device_path)
        self.deadzone = deadzone
        self.axes: Dict[int, AxisState] = {code: AxisState() for code in self.AXIS_NORMALIZERS}
        self.btn_allstop = ecodes.BTN_SOUTH  # A button
        self.btn_exit = ecodes.BTN_EAST      # B button
        _LOGGER.info("Opened controller %s (%s)", self.dev.path, self.dev.name)

    def read_events(self):  # pragma: no cover - live loop
        for event in self.dev.read_loop():
            yield event

    def update(self, event) -> Optional[str]:  # pragma: no cover - live loop
        if event.type == ecodes.EV_ABS and event.code in self.AXIS_NORMALIZERS:
            norm = self.AXIS_NORMALIZERS[event.code](event.value)
            norm = max(-1.0, min(1.0, norm))
            self.axes[event.code].value = norm
        elif event.type == ecodes.EV_KEY:
            if event.code == self.btn_allstop and event.value == 1:  # press
                return "ALLSTOP"
            if event.code == self.btn_exit and event.value == 1:
                return "EXIT"
        return None

    def throttle_turn(self) -> tuple[float, float]:
        return (self.axes[ecodes.ABS_Y].value, self.axes[ecodes.ABS_RX].value)


def send_drive(bridge: SerialBridge, drive, last_sent, rate_hz: float) -> float:
    """Send MOTOR commands for left/right if enough time elapsed."""
    interval = 1.0 / rate_hz
    now = time.time()
    if now - last_sent < interval:
        return last_sent
    (left_dir, left_speed), (right_dir, right_speed) = drive.as_direction_speed()

    # Map sides to motor indices: assume 0,1,2 = left; 3,4,5 = right
    for idx, (dir_, speed) in zip((0,1,2), [(left_dir, left_speed)]*3):
        bridge.motor_run(str(idx), dir_, speed)
    for idx, (dir_, speed) in zip((3,4,5), [(right_dir, right_speed)]*3):
        bridge.motor_run(str(idx), dir_, speed)
    return now


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Xbox controller teleop for Cheddar")
    parser.add_argument("--device", required=True, help="/dev/input/event* path for Xbox controller")
    parser.add_argument("--port", default=os.getenv("MOTIONDRIVER_SERIAL_PORT", "auto"), help="Serial port for MotionDriver (or 'auto')")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--deadzone", type=float, default=0.08, help="Axis deadzone")
    parser.add_argument("--rate", type=float, default=20.0, help="Command send rate (Hz)")
    parser.add_argument("--log", action="store_true", help="Enable traffic logging")
    parser.add_argument("--dry-run", action="store_true", help="Don't open serial; print instead")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")

    config = SerialConfig(port=args.port, baudrate=args.baud, timeout=0.2, dry_run=args.dry_run, log_traffic=args.log)
    bridge = create_bridge(config)

    controller = XboxController(args.device, args.deadzone)

    stopping = False

    def handle_sigint(sig, frame):  # noqa: D401, ANN001 - simple handler
        nonlocal stopping
        _LOGGER.info("SIGINT received, stopping...")
        stopping = True

    signal.signal(signal.SIGINT, handle_sigint)

    last_sent = 0.0
    try:
        _LOGGER.info("Sending initial STOP")
        bridge.motor_stop("ALL")
        for ev in controller.read_events():
            action = controller.update(ev)
            if action == "ALLSTOP":
                _LOGGER.info("ALLSTOP button pressed")
                bridge.motor_stop("ALL")
                continue
            if action == "EXIT":
                _LOGGER.info("Exit button pressed")
                break
            throttle, turn = controller.throttle_turn()
            drive = compute_drive(throttle, turn, args.deadzone)
            last_sent = send_drive(bridge, drive, last_sent, args.rate)
            if stopping:
                break
    finally:
        _LOGGER.info("Final STOP and closing")
        try:
            bridge.motor_stop("ALL")
        except Exception:  # pragma: no cover - best effort
            pass
        bridge.close()
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
