from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from .. import main as main_module
from cheddar_serial import SerialConfig, DummyTransport, SerialBridge


@pytest.fixture(name="transport")
def transport_fixture() -> Generator[DummyTransport, None, None]:
    transport = DummyTransport()
    bridge = SerialBridge(
        SerialConfig(port="dummy", dry_run=False, log_traffic=False),
        transport=transport,
    )
    original_bridge = main_module._bridge
    main_module._bridge = bridge
    yield transport
    main_module._bridge = original_bridge


@pytest.fixture(name="client")
def client_fixture(
    transport: DummyTransport,
) -> TestClient:  # noqa: ARG001 - force fixture ordering
    return TestClient(main_module.app)


def test_servo_endpoint(client: TestClient, transport: DummyTransport) -> None:
    response = client.post("/api/servo", json={"channel": 2, "pulse_us": 1400})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert transport.last_line == "S 2 1400"


def test_motor_run_endpoint(client: TestClient, transport: DummyTransport) -> None:
    response = client.post(
        "/api/motor/run",
        json={"target": "ALL", "direction": "FORWARD", "speed": 0.75},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert transport.last_line == "MOTOR ALL FORWARD 0.75"


def test_ping_endpoint_returns_response(
    client: TestClient, transport: DummyTransport
) -> None:
    transport.canned_response = "PONG"
    response = client.post("/api/ping")
    assert response.status_code == 200
    assert response.json()["response"] == "PONG"


def test_error_from_device_returns_400(
    client: TestClient, transport: DummyTransport
) -> None:
    transport.canned_response = "ERR Servo channel"
    response = client.post("/api/servo", json={"channel": 2, "pulse_us": 1200})
    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/api/servo", json={"channel": -1, "pulse_us": 200})
    assert response.status_code == 422
