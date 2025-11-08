"""
Tests for Pydantic models
"""

import pytest
from pydantic import ValidationError
from models import ControlCommand, TelemetryData, SDPOffer, SDPAnswer


def test_control_command_valid():
    """Test valid control command."""
    cmd = ControlCommand(type="motor", motor_left=0.5, motor_right=0.5, timestamp=1234567890.0)
    assert cmd.type == "motor"
    assert cmd.motor_left == 0.5


def test_control_command_bounds():
    """Test motor value bounds checking."""
    with pytest.raises(ValidationError):
        ControlCommand(
            type="motor", motor_left=1.5, motor_right=0.5, timestamp=1234567890.0  # Invalid: > 1.0
        )


def test_telemetry_data():
    """Test telemetry data model."""
    telem = TelemetryData(
        type="telemetry",
        battery_voltage=7.4,
        cpu_temp=45.2,
        signal_strength=85,
        timestamp=1234567890.0,
    )
    assert telem.battery_voltage == 7.4
    assert telem.signal_strength == 85


def test_sdp_offer():
    """Test SDP offer model."""
    offer = SDPOffer(sdp="dummy sdp", type="offer")
    assert offer.type == "offer"
    assert offer.sdp == "dummy sdp"
