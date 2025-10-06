# MotionDriver

MotionDriver is the low-level firmware that bridges high-level commands from a Raspberry Pi via UART to the Cheddar robotic drivetrain and servos. It runs on a Freenove ESP32-WROOM board and exposes a simple UART command protocol for driving six DC motors through DRV8833 bridges and six hobby servos via a PCA9685 PWM expander.

## High-level components

- **`src/main.cpp`** – Initializes the UART command interface, servo bus, and motor drivers, then services command polling and servo sweep updates in the main loop.
- **`inputs/UARTCommandInput`** – Parses newline-delimited UART commands (`PING`, `S`, `SWEEP`, `MOTOR`, `LOG`, `HELP`) and routes them to the appropriate controllers. Error responses are emitted with the `ERR` prefix.
- **`outputs/ServoController`** – Owns the PCA9685 servo bus, clamps pulses, handles optional sweep motion, and can emit telemetry when enabled.
- **`outputs/MotorController`** – Configures LEDC PWM channels for the DRV8833 half-bridges, tracks enable/standby state, and provides helpers for per-motor or all-motor commands.
- **`include/pins.h`** – Central pin map for the ESP32, covering I²C, UART, DRV8833 inputs, standby, and PCA9685 output enable.

## Pinout summary

| Function | ESP32 pin | Notes |
| --- | --- | --- |
| I²C SDA (PCA9685) | 21 | Shared servo bus data line |
| I²C SCL (PCA9685) | 22 | Shared servo bus clock line |
| UART2 RX (from Pi) | 16 | HardwareSerial2 RX, 3.3 V logic |
| UART2 TX (to Pi) | 17 | HardwareSerial2 TX, 3.3 V logic |
| DRV8833 STBY | 27 | Shared standby enable for all motor drivers |
| PCA9685 OE | 5 | Active-low output enable for servo PWM board |
| M1 IN1 | 13 | DRV8833 AIN1 |
| M1 IN2 | 14 | DRV8833 AIN2 |
| M2 IN1 | 25 | DRV8833 BIN1 |
| M2 IN2 | 26 | DRV8833 BIN2 |
| M3 IN1 | 32 | DRV8833 AIN1 |
| M3 IN2 | 33 | DRV8833 AIN2 |
| M4 IN1 | 4 | DRV8833 BIN1 |
| M4 IN2 | 18 | DRV8833 BIN2 |
| M5 IN1 | 19 | DRV8833 AIN1 |
| M5 IN2 | 23 | DRV8833 AIN2 |
| M6 IN1 | 2 | Boot-sensitive pin; swap if needed |
| M6 IN2 | 15 | Boot-sensitive pin; swap if needed |

Refer to `include/pins.h` for the authoritative mapping and hardware notes.

## UART CLI reference

The canonical UART help text is stored in `docs/cli_help.txt`. Run the `HELP` command over the serial link to stream the same content from the firmware.

## Development notes

- The project is built with [PlatformIO](https://platformio.org/). Use `platformio run` to verify firmware builds locally.
- Keep the CLI documentation in `docs/cli_help.txt` in sync with the logic in `inputs/UARTCommandInput.cpp` when adding new commands or adjusting behavior.
