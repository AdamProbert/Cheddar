# MotionDriver

MotionDriver is the low-level firmware that bridges high-level commands from a Raspberry Pi to the Cheddar robotic drivetrain and servos. It runs on a Freenove ESP32-WROOM board and exposes a simple serial command protocol for driving six DC motors through DRV8833 bridges and six hobby servos via a PCA9685 PWM expander.

The Pi connects over **USB** (CH340 bridge, `/dev/ttyUSB0` @ 115200); the firmware binds its command parser to `Serial` (UART0). For the full wiring picture, power tree, and known issues see [HARDWARE.md](../HARDWARE.md).

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

> **Note:** `pins.h` also defines `PIN_UART2_RX` (16) and `PIN_UART2_TX` (17). These are vestigial
> from an earlier GPIO-UART plan and are **never opened** — the Pi link is USB/UART0. They are
> listed here only so nobody wires to them expecting a working link.

## UART CLI reference

The canonical UART help text is stored in `docs/cli_help.txt`. Run the `HELP` command over the serial link to stream the same content from the firmware.

## Flashing from the Pi

The ESP32 lives on the rover's USB, so it is flashed **from `cheddarpi`** — no need to tether the
rover to the dev PC. Build on the PC (the Pi has no PlatformIO), copy the images over, and flash
with the Pi's `esptool` (installed by `PieBrain/setup_rpi.sh`):

```bash
# On the PC, from MotionDriver/
pio run
scp .pio/build/esp32dev/{bootloader,partitions,firmware}.bin \
    ~/.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin \
    adamprobert@cheddarpi:~/fw/

# On the Pi — stop the backend first, see below
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z \
  --flash_mode dio --flash_freq 40m --flash_size detect \
  0x1000 ~/fw/bootloader.bin 0x8000 ~/fw/partitions.bin \
  0xe000 ~/fw/boot_app0.bin 0x10000 ~/fw/firmware.bin
```

> ⚠️ **Stop the ChedWeb backend before flashing.** The backend holds `/dev/ttyUSB0` open, and
> esptool cannot share it. The symptom is misleading — esptool fails with
> `A fatal error occurred: Packet content transfer stopped`, or connects and reads the chip ID and
> *then* dies uploading the stub, which looks like a baud-rate or cable fault and sends you chasing
> the wrong thing. Check `sudo fuser -v /dev/ttyUSB0` **first**; `systemctl is-active` is not
> enough, since the backend is often started by hand and won't show up as a service.

Flashing resets the ESP32, and on reset all GPIOs go high-impedance — see the brownout runaway risk
in [HARDWARE.md](../HARDWARE.md). **The wheels can twitch mid-flash.** Chock the rover or cut the
motor rail if that matters.

## Development notes

- The project is built with [PlatformIO](https://platformio.org/). Use `platformio run` to verify firmware builds locally.
- Keep the CLI documentation in `docs/cli_help.txt` in sync with the logic in `inputs/UARTCommandInput.cpp` when adding new commands or adjusting behavior.
- Wheel index → motor pins is **not** `M(n+1)`; the loom is wired in side-blocks and every motor's
  leads are reversed. The mapping table lives in `outputs/MotorController.cpp` — see the wheel
  indexing section of [HARDWARE.md](../HARDWARE.md) before trusting any index-to-motor assumption.
