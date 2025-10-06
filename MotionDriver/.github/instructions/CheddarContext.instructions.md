---
applyTo: "**"
---

Project Context for gpt-5-codex (Cheddar)

Summary
• Project: Cheddar — modular mobile robotics testbed (future: autonomy, arm, treat dispenser).
• MCU: Freenove ESP32-WROOM (FNK0091 breakout).
• Logic: 3.3 V GPIO.
• Actuators: 6× DC motors (≈1 A peak each) via 3× DRV8833; 6× hobby servos (≈1 A peak each) via PCA9685 (I²C).
• Battery: 2S LiPo (7.4 V nominal; 8.4 V full).
• Comms: UART2 (GPIO16 RX2 / GPIO17 TX2) to Raspberry Pi 3 (high-level commands).
• I²C: SDA=GPIO21 / SCL=GPIO22 (PCA9685).
• DRV8833 STBY: Shared single pin from ESP32.
• Grounding: One common ground for ESP32, drivers, PCA9685, Pi, and battery.

⚠️ Voltage note: Fully-charged 2S = 8.4 V. If your motors/servos are “6 V” parts, add a buck to ~6.0–6.5 V or use HV servos/motors rated for 8.4 V. Add bulk caps (≥1000 µF per rail).

Pin Plan (ESP32)

Reserved
• I²C: GPIO21 (SDA), GPIO22 (SCL)
• UART2 (Pi link): GPIO16 (RX2), GPIO17 (TX2)
• DRV8833 STBY (shared): GPIO27 (any free output is fine)

Motors (3× DRV8833 = 6 motors; 2 inputs per motor)
• Driver A (Motors M1–M2):
• M1: GPIO13 (IN1), GPIO14 (IN2)
• M2: GPIO25 (IN3), GPIO26 (IN4)
• Driver B (Motors M3–M4):
• M3: GPIO32 (IN1), GPIO33 (IN2)
• M4: GPIO4 (IN3), GPIO18 (IN4)
• Driver C (Motors M5–M6):
• M5: GPIO19 (IN1), GPIO23 (IN2)
• M6: GPIO2 (IN3), GPIO15 (IN4)

If you want to be ultra-safe with bootstraps, swap GPIO2/15 for GPIO5 and GPIO12 only if you know your board’s strapping tolerances. Otherwise leave as-is; don’t hold 0/2/12/15 low at boot.

Servos
• Via PCA9685 channels 0–5 (signal from PCA9685; power from servo rail).

Avoid
• GPIO34–39 are input-only (don’t use for motor inputs).
• Be mindful of boot pins 0/2/12/15 during power-up.

Power & Wiring Rules
• Star ground at a single distribution point; run separate returns for motors, servos, logic back to that star.
• Servo & motor rail from battery (or buck). Place big electrolytics near each DRV8833 and PCA9685 (e.g., 470–1000 µF).
• Use inline fuse on battery lead sized for expected peak (e.g., 15–20 A slow-blow for headroom).
• Keep motor leads twisted/short; route away from I²C and UART.
• Wire order for servo headers: GND – V+ – Sig (match PCA9685 boards).

Software Conventions
• Platform: Arduino (ESP32 core).
• Libs: Adafruit_PWMServoDriver for PCA9685. DRV8833 controlled with GPIO/LEDC PWM (no heavy libs).
• Structure:
• src/hal/ — pin map, motor + servo HAL
• src/control/ — high-level commands, mixing, safety
• src/proto/ — UART parser
• src/main.cpp
• Coding style: constants in kSCREAMING_SNAKE_CASE, classes for actuators, no dynamic alloc in loop, non-blocking code.
• PWM: Use ESP32 LEDC. 10–15 kHz for motors (quieter), 50 Hz for servos (handled by PCA9685).
• Safety on boot: set DRV8833 STBY low, set all motor inputs low, init I²C, then raise STBY.

Command Schema (UART2)

Plaintext, one per line, \n terminated:
• M n dir pwm → set motor n∈[1..6], dir∈{-1,0,1}, pwm∈[0..255]
• S n us → set servo n∈[0..5] to microseconds (e.g., 1500)
• ALLSTOP → brake all motors (both inputs HIGH) and neutral servos
• PING → respond PONG

Responses: OK, ERR <code>, or telemetry lines prefixed T:.

Helper Class Stubs (what the agent should assume)
• Motor(int in1, int in2) with setRaw(int dir, uint8_t pwm), brake(), coast()
• ServoBus(PCA9685&) with writeUS(ch, us) and clamping
• CommandRouter that parses lines and calls HAL

“Do / Don’t”
• ✅ Do centralize pin map in one header.
• ✅ Do keep STBY low until init complete.
• ✅ Do clamp servo pulses (e.g., 1000–2000 µs unless configured).
• ❌ Don’t block in loops; avoid delay() except tiny debounces.
• ❌ Don’t drive motors before verifying supply > 6.0 V and brownout won’t occur.

⸻

Ready-Made Pin Map (drop-in header)

// pins.h — Freenove ESP32-WROOM (FNK0091)
#pragma once

// I2C (PCA9685)
constexpr int PIN_I2C_SDA = 21;
constexpr int PIN_I2C_SCL = 22;

// UART2 to Raspberry Pi
constexpr int PIN_UART2_RX = 16; // ESP32 RX2
constexpr int PIN_UART2_TX = 17; // ESP32 TX2

// DRV8833 STBY (shared)
constexpr int PIN_DRV_STBY = 27;

// Driver A (M1, M2)
constexpr int PIN_M1_IN1 = 13;
constexpr int PIN_M1_IN2 = 14;
constexpr int PIN_M2_IN1 = 25;
constexpr int PIN_M2_IN2 = 26;

// Driver B (M3, M4)
constexpr int PIN_M3_IN1 = 32;
constexpr int PIN_M3_IN2 = 33;
constexpr int PIN_M4_IN1 = 4;
constexpr int PIN_M4_IN2 = 18;

// Driver C (M5, M6)
constexpr int PIN_M5_IN1 = 19;
constexpr int PIN_M5_IN2 = 23;
constexpr int PIN_M6_IN1 = 2; // swap if boot issues
constexpr int PIN_M6_IN2 = 15; // swap if boot issues

⸻

Minimal Motor Behavior Contract (for the agent)
• Forward: IN1=PWM, IN2=LOW
• Reverse: IN1=LOW, IN2=PWM
• Coast: IN1=LOW, IN2=LOW
• Brake: IN1=HIGH, IN2=HIGH
• STBY: LOW disables outputs; HIGH enables after init.
