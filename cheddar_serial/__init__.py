"""Shared serial link utilities for Cheddar MotionDriver.

Exports:
- SerialConfig: Runtime configuration (env-aware)
- SerialBridge: High-level command helper
- create_bridge: Factory
- CommandError: Error raised when device returns ERR
"""
from .config import SerialConfig  # noqa: F401
from .serial_bridge import (  # noqa: F401
	SerialBridge,
	create_bridge,
	CommandError,
	DummyTransport,
)
