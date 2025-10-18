import pytest

from cheddar_serial import SerialConfig, CommandError, DummyTransport, SerialBridge


def make_bridge(response: str = "OK") -> tuple[SerialBridge, DummyTransport]:
    transport = DummyTransport(canned_response=response)
    config = SerialConfig(
        port="dummy", baudrate=115200, timeout=0.1, dry_run=False, log_traffic=False
    )
    bridge = SerialBridge(config=config, transport=transport)
    return bridge, transport


def test_set_servo_sends_command() -> None:
    bridge, transport = make_bridge()
    bridge.set_servo(2, 1500)
    assert transport.last_line == "S 2 1500"


def test_motor_run_with_speed() -> None:
    bridge, transport = make_bridge()
    bridge.motor_run("ALL", "forward", 0.5)
    assert transport.last_line == "MOTOR ALL FORWARD 0.50"


def test_motor_run_rejects_invalid_target() -> None:
    bridge, _ = make_bridge()
    with pytest.raises(ValueError):
        bridge.motor_run("foo", "forward", 0.2)


def test_error_response_raises_command_error() -> None:
    bridge, _ = make_bridge("ERR Servo channel")
    with pytest.raises(CommandError):
        bridge.set_servo(0, 1200)


def test_ping_returns_response() -> None:
    bridge, _ = make_bridge("PONG")
    assert bridge.ping() == "PONG"
