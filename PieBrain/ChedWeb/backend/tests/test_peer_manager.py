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
async def test_create_peer_connection():
    """Test peer connection creation."""
    manager = PeerManager(ice_servers=[{"urls": ["stun:stun.l.google.com:19302"]}])
    pc = await manager.create_peer_connection()
    assert pc is not None
    assert manager.pc == pc
    await manager.close()


# TODO: Add more comprehensive tests with mocked WebRTC components
# TODO: Test DataChannel message handling
# TODO: Test command callbacks
