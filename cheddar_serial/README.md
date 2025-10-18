# cheddar_serial

Shared Python package providing the serial transport and high-level command helper for Cheddar's MotionDriver (ESP32) firmware.

## Provided Components

- `SerialConfig`: Environment-aware runtime config (port autodetect sentinel, baud, timeouts, logging).
- `SerialBridge`: Thread-safe helper sending commands and validating OK/ERR responses.
- `create_bridge()`: Convenience factory.
- `CommandError`: Raised when device returns a line beginning with `ERR`.
- `DummyTransport`: Test/dry-run transport capturing last line.

## Usage

```python
from cheddar_serial import SerialConfig, create_bridge

bridge = create_bridge(SerialConfig(port="/dev/ttyS0", baudrate=115200))
bridge.motor_run("ALL", "FORWARD", 0.5)
bridge.motor_stop("ALL")
```

## Notes

Originally these utilities lived inside the webapp package; they were extracted to `cheddar_serial` so both the web API and Raspberry Pi teleoperation scripts can share one implementation.

## Environment Variables

- `MOTIONDRIVER_SERIAL_PORT` ("auto" to defer opening until explicitly set)
- `MOTIONDRIVER_SERIAL_BAUDRATE` (default 115200)
- `MOTIONDRIVER_SERIAL_TIMEOUT` (default 1.0 seconds)
- `MOTIONDRIVER_DRY_RUN` (true/false) for DummyTransport
- `MOTIONDRIVER_LOG_TRAFFIC` (true/false)
