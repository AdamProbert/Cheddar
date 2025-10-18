"""Backward compatibility shim.

The webapp previously hosted SerialBridge and SerialConfig. These have been
refactored into the shared `cheddar_serial` package. Import and re-export
symbols here so existing import paths keep working.
"""

from cheddar_serial import (  # noqa: F401
    SerialBridge,
    SerialConfig,
    CommandError,
    create_bridge,
    DummyTransport,
)
