"""Controller input mapping utilities.

We treat the robot as a differential (left/right) drive of 6 motors arranged
in two sets (e.g., 3 left + 3 right). The MotionDriver firmware currently
accepts commands per motor index 0-5 or ALL. We send per-side speeds by
issuing individual MOTOR commands for each index.

Input axes (Xbox One over Linux evdev typical mapping):
- LX (ABS_X): strafe/unused (future)
- LY (ABS_Y): forward/backward (negative = forward on many controllers)
- RX (ABS_RX): yaw/turn (left = negative)
- RT (ABS_RZ) / LT (ABS_Z): analog triggers 0-255 (optional for speed scaling)

We combine LY (throttle) and RX (turn) into left/right motor scalar outputs
in the range [-1.0, 1.0]. A simple differential mix:
    left  = clamp(throttle + turn)
    right = clamp(throttle - turn)

Deadzone is applied to each centered axis before mixing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


def apply_deadzone(value: float, deadzone: float) -> float:
    """Apply a symmetric deadzone to a normalized axis value [-1,1]."""
    if abs(value) < deadzone:
        return 0.0
    # Re-scale so that value just outside the deadzone maps proportionally.
    sign = 1.0 if value > 0 else -1.0
    adjusted = (abs(value) - deadzone) / (1.0 - deadzone)
    return max(0.0, min(1.0, adjusted)) * sign


def differential_mix(throttle: float, turn: float) -> Tuple[float, float]:
    """Return (left, right) motor normalized outputs in [-1,1]."""
    left = throttle + turn
    right = throttle - turn
    return (max(-1.0, min(1.0, left)), max(-1.0, min(1.0, right)))


@dataclass
class DriveCommand:
    left: float  # -1..1
    right: float  # -1..1

    def scaled(self, scale: float) -> "DriveCommand":
        return DriveCommand(
            left=max(-1.0, min(1.0, self.left * scale)),
            right=max(-1.0, min(1.0, self.right * scale)),
        )

    def as_direction_speed(self):
        """Return tuple for each side: (dir, speed) with dir in {FORWARD,BACKWARD}.

        speed returned 0..1.
        """
        def part(v: float):
            if v == 0:
                return ("FORWARD", 0.0)  # direction arbitrary when stopped
            return ("FORWARD" if v > 0 else "BACKWARD", abs(v))

        return part(self.left), part(self.right)


def compute_drive(throttle: float, turn: float, deadzone: float = 0.08) -> DriveCommand:
    """Full pipeline: deadzone, mix."""
    throttle = apply_deadzone(throttle, deadzone)
    turn = apply_deadzone(turn, deadzone)
    l, r = differential_mix(throttle, turn)
    return DriveCommand(l, r)
