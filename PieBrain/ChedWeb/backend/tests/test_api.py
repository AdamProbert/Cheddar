"""
Basic tests for API endpoints
"""

import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_get_config():
    """Test config endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "stun_server" in data
    assert "command_rate_limit_hz" in data


@pytest.mark.asyncio
async def test_signaling_offer():
    """Test signaling offer endpoint with valid SDP."""
    dummy_sdp = """v=0
o=- 123 123 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0
m=application 9 UDP/DTLS/SCTP webrtc-datachannel
c=IN IP4 0.0.0.0
a=ice-ufrag:test
a=ice-pwd:testpassword
a=fingerprint:sha-256 00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
a=setup:actpass
a=mid:0
a=sctp-port:5000
"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/signaling/offer", json={"sdp": dummy_sdp, "type": "offer"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "answer"
    assert "sdp" in data
