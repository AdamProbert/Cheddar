"""
Tests for peer manager (unit tests, WebRTC mocked)
"""

import pytest
from peer_manager import PeerManager


def test_peer_manager_init():
    """Test peer manager initialization."""
    manager = PeerManager(ice_servers=[{"urls": ["stun:stun.l.google.com:19302"]}])
    assert manager.pc is None
    assert manager.control_channel is None


@pytest.mark.asyncio
async def test_handle_offer_creates_peer_connection():
    """Test that handle_offer creates a peer connection."""
    manager = PeerManager(ice_servers=[{"urls": ["stun:stun.l.google.com:19302"]}])
    
    # Create a minimal valid SDP offer
    minimal_offer = """v=0
o=- 0 0 IN IP4 127.0.0.1
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
    
    answer_sdp = await manager.handle_offer(minimal_offer)
    assert answer_sdp is not None
    assert manager.pc is not None
    assert "v=0" in answer_sdp  # Basic SDP validation
    
    await manager.close()


# TODO: Add more comprehensive tests with mocked WebRTC components
# TODO: Test DataChannel message handling
# TODO: Test command callbacks
