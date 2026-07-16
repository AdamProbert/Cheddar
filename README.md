# Cheddar  

Cheddar is an experimental robotics platform designed for exploration, stair climbing, and general terrain traversal. It serves as a **test bed for future additions** such as autonomous navigation, robotic arms, and even fun extras like a dog treat dispenser. The project combines low-level motor/servo control with high-level navigation and control logic, split across microcontrollers and a Raspberry Pi.  

## Hardware Overview  

A Raspberry Pi 3B handles high-level control and video; a Freenove ESP32-WROOM drives 6 DC motors
(3× DRV8833) and 6 steering servos (PCA9685) from commands sent over USB serial. Powered by a
single 2S LiPo.

📖 **See [HARDWARE.md](HARDWARE.md) for the full bill of materials, wiring diagram, pin map, and
known issues.** That file is the single source of truth — don't restate hardware details here.

## Software Overview  

- **[MotionDriver/](MotionDriver/)** – ESP32 firmware (PlatformIO) for motor and servo control
- **[PieBrain/ChedWeb/](PieBrain/ChedWeb/)** – Pi-side WebRTC control interface (FastAPI + React)
- **[webapp/](webapp/)** – legacy FastAPI serial bridge, useful for quick debugging
- High-level commands issued from the Pi to the ESP32 over USB serial (`/dev/ttyUSB0`, 115200)
- Modular design for expansion into autonomy, manipulation, and other experimental features  

## Current Status  

- Motor and servo control functional; Pi ↔ ESP32 serial link working over USB
- ChedWeb WebRTC control and video streaming operational
- **Open issue:** motor inrush browns out the shared rail and can freeze the Pi — see
  [HARDWARE.md](HARDWARE.md#-known-issue--brownouts)
- Perfboard layout and wiring in progress  
