"""
Tests for the MotionDriver serial bridge
"""

import pytest
from motion_driver_bridge import (
    SERVO_MAX_PULSE_US,
    SERVO_MIN_PULSE_US,
    servo_angle_to_pulse_us,
)


def test_centre_angle_maps_to_centre_pulse():
    """90 degrees (straight ahead) must land on 1500us."""
    assert servo_angle_to_pulse_us(90) == 1500


def test_endpoints_map_to_firmware_clamp_range():
    """The 0-180 degree range must span exactly the firmware's pulse range."""
    assert servo_angle_to_pulse_us(0) == SERVO_MIN_PULSE_US
    assert servo_angle_to_pulse_us(180) == SERVO_MAX_PULSE_US


def test_out_of_range_angles_are_clamped():
    """Angles outside 0-180 clamp rather than producing wild pulse widths."""
    assert servo_angle_to_pulse_us(-30) == SERVO_MIN_PULSE_US
    assert servo_angle_to_pulse_us(400) == SERVO_MAX_PULSE_US


@pytest.mark.parametrize("angle", [0, 45, 90, 135, 180])
def test_all_angles_land_inside_firmware_clamp_range(angle):
    """Regression: degrees were once passed straight through as microseconds.

    Every angle then fell below the firmware's 1000us floor, so all six servos
    slammed hard over and steering looked dead -- 45 and 135 clamped identically.
    """
    assert SERVO_MIN_PULSE_US <= servo_angle_to_pulse_us(angle) <= SERVO_MAX_PULSE_US


def test_steering_extremes_are_distinguishable():
    """Ackermann's +/-45 degrees must produce distinct pulses either side of centre."""
    left = servo_angle_to_pulse_us(45)
    right = servo_angle_to_pulse_us(135)
    assert left < 1500 < right
