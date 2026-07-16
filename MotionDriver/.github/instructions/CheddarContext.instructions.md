---
applyTo: "**"
---

# Cheddar — MotionDriver agent context

Cheddar is a modular mobile robotics testbed (future: autonomy, arm, treat dispenser).
MotionDriver is the ESP32 firmware that turns serial commands into motor and servo motion.

## Hardware

**Do not restate hardware facts here — they go stale.** The authoritative sources are:

- **[HARDWARE.md](../../../HARDWARE.md)** — bill of materials, wiring diagram, power tree, known issues
- **[`include/pins.h`](../../include/pins.h)** — pin numbers, outranks all prose
- **[MotionDriver/README.md](../../README.md)** — pinout summary and CLI reference

Minimum you need to know: Freenove **ESP32-WROOM** (`board = esp32dev`), 3.3 V logic, 6 DC motors
via 3× DRV8833, 6 servos via PCA9685 on I²C, single 2S LiPo. The Pi connects over **USB serial**
(`/dev/ttyUSB0` @ 115200) — the `PIN_UART2_*` constants in `pins.h` are vestigial and unused.

## Command protocol

Canonical help text lives in [`docs/cli_help.txt`](../../docs/cli_help.txt); the `HELP` command
streams the same content. Commands are newline-delimited; errors are prefixed `ERR`.

Keep `docs/cli_help.txt` in sync with `inputs/UARTCommandInput.cpp` when changing commands.

## Software conventions

- **Platform:** Arduino framework on ESP32 core, built with PlatformIO (`platformio run`).
- **Libraries:** `Adafruit_PWMServoDriver` for the PCA9685. DRV8833 is driven directly with
  GPIO/LEDC PWM — no heavy libraries.
- **Structure:**
  - `src/inputs/` — serial command parsing
  - `src/outputs/` — motor + servo controllers
  - `include/pins.h` — central pin map
  - `src/main.cpp` — init and main loop
- **Style:** constants in `kSCREAMING_SNAKE_CASE`, classes for actuators, no dynamic allocation in
  the main loop, non-blocking throughout.
- **PWM:** ESP32 LEDC. 10–15 kHz for motors (above audible range); servos are 50 Hz via the PCA9685.
- **Boot safety:** hold DRV8833 STBY low, set all motor inputs low, init I²C, *then* raise STBY.

## Do / Don't

- ✅ Centralize pin numbers in `include/pins.h` — never hardcode in source.
- ✅ Keep STBY low until init completes.
- ✅ Clamp servo pulses (1000–2000 µs unless configured otherwise).
- ❌ Don't block in loops; avoid `delay()` except tiny debounces.
- ❌ Don't hold GPIO 0/2/12/15 low at boot — they are strapping pins (M6 uses 2 and 15).
- ❌ Don't use GPIO 34–39 as outputs — input-only on the WROOM.
- ❌ Don't drive motors without checking the supply rail; see the brownout issue in HARDWARE.md.
