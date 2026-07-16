# Cheddar Project - AI Agent Instructions

This document provides AI coding assistants with comprehensive context about the Cheddar robotics platform. Use this information to understand the project structure, make informed decisions, and provide accurate assistance.

## 🤖 Project Overview

**Cheddar** is an experimental robotics platform designed for exploration, stair climbing, and general terrain traversal. It serves as a test bed for autonomous navigation, robotic arms, and other experimental features. The architecture is split across microcontrollers (low-level motor/servo control) and a Raspberry Pi (high-level control, video streaming, web interface).

### Core Philosophy

- **Modular design** for easy expansion and experimentation
- **Hardware acceleration** where available (H.264 encoding, PWM controllers)
- **Type-safe** interfaces with schema validation (Pydantic backend, Zod frontend)
- **Real-time control** via WebRTC DataChannel
- **Developer-friendly** with mock modes, comprehensive testing, and clear documentation

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Raspberry Pi 3B                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ChedWeb (WebRTC Control Interface)                  │   │
│  │  - FastAPI Backend (Python)                          │   │
│  │  - React Frontend (TypeScript)                       │   │
│  │  - Camera Streaming (picamera2 + H.264)             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Legacy WebApp (FastAPI Serial Bridge)              │   │
│  │  - HTTP REST API for debugging                       │   │
│  │  - Static dashboard                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │ USB Serial (CH340 → /dev/ttyUSB0 @ 115200)
┌─────────────────▼───────────────────────────────────────────┐
│              ESP32-WROOM (MotionDriver)                      │
│  - UART Command Interface                                   │
│  - ServoController (PCA9685 I²C)                            │
│  - MotorController (DRV8833 via LEDC PWM)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│  PCA9685      │   │  3x DRV8833   │
│  (6 Servos)   │   │  (6 DC Motors)│
└───────────────┘   └───────────────┘
```

## 📁 Project Structure & Components

### Root Level

- **README.md** - Project overview
- **HARDWARE.md** - **Authoritative hardware reference** (BOM, wiring, pin map, known issues)
- **PieBrain/** - Raspberry Pi software and setup
- **MotionDriver/** - ESP32 firmware (PlatformIO project) — the active motion controller
- **webapp/** - Legacy FastAPI serial bridge
- **BlinkRGB/** - ESP32 LED test firmware
- **ServoMotorDriver/** - Historical Arduino servo sketches (not part of the current build)

### PieBrain (`PieBrain/`)

High-level control software running on Raspberry Pi.

**Key Files:**

- `setup_rpi.sh` - Automated Raspberry Pi setup script
- `README.md` - Pi setup documentation

**What the setup script does:**

- Updates apt packages and installs dependencies (curl, wget, git, zsh, build tools)
- Configures global git identity
- Installs Python tooling (pipx, virtualenv, virtualenvwrapper) in PEP 668-compliant way
- Installs Oh My Zsh
- Generates SSH key if missing
- Clones Cheddar repository to `~/Cheddar`
- Creates `.venv` and installs dependencies if `requirements.txt` exists

**Usage:**

```bash
sudo bash ./setup_rpi.sh --git-name "Adam Probert" --git-email "adamprobert@live.co.uk"
```

### ChedWeb (`PieBrain/ChedWeb/`)

Modern WebRTC-based rover control system with ultra-low latency video streaming.

**Architecture:**

- **Backend:** FastAPI + aiortc + picamera2
- **Frontend:** React + TypeScript + Vite + Tailwind + shadcn/ui
- **Communication:** WebRTC DataChannel for commands/telemetry, video track for streaming
- **State Management:** Zustand (frontend)
- **Schema Validation:** Pydantic (backend), Zod (frontend)

**Key Features:**

- ✅ Hardware-accelerated H.264 video streaming
- ✅ Real-time command/telemetry via DataChannel
- ✅ Gamepad support (Browser Gamepad API)
- ✅ Mock mode with test pattern fallback
- ✅ Type-safe schemas across stack

**Backend Structure (`backend/`):**

- `main.py` - FastAPI application and endpoints
- `peer_manager.py` - WebRTC peer connection manager
- `camera.py` - Camera video streaming (picamera2 integration)
- `models.py` - Pydantic models for type safety
- `config.py` - Settings management
- `requirements.txt` - Python dependencies
- `setup.sh` - Automated backend setup
- `backend.service` - systemd service configuration

**Frontend Structure (`frontend/`):**

```
src/
├── components/
│   ├── ConnectionControls.tsx - WebRTC connection UI
│   ├── TelemetryCard.tsx - Real-time telemetry display
│   ├── VideoFeed.tsx - Camera video component
│   └── ui/ - shadcn/ui components (Button, Card)
├── utils/
│   └── webrtc.ts - WebRTC connection logic
├── types/
│   └── schemas.ts - Zod schemas (match Pydantic models)
├── App.tsx - Main application component
├── store.ts - Zustand state management
└── main.tsx - Entry point
```

**API Endpoints:**

- `GET /healthz` - Health check
- `POST /signaling/offer` - WebRTC SDP offer/answer exchange
- `WS /ws/debug` - WebSocket echo for testing
- `GET /api/config` - Public configuration

**Camera Configuration (`.env`):**

```bash
CAMERA_ENABLED=true              # Enable/disable camera
CAMERA_WIDTH=640                 # Resolution width
CAMERA_HEIGHT=480                # Resolution height
CAMERA_FRAMERATE=30              # Target framerate
CAMERA_ROTATION=0                # Rotation (0, 90, 180, 270)
```

**Development Commands:**

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py  # Runs on http://0.0.0.0:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
npm run test  # Run vitest tests
npm run build  # Production build
```

**Important Notes for Agents:**

- Camera requires `python3-picamera2`, `python3-libcamera`, `python3-kms++` system packages
- Video codecs need `libavformat-dev`, `libavcodec-dev`, `libavdevice-dev`, etc.
- Mock mode activates automatically when camera unavailable
- Always match Pydantic and Zod schemas when modifying data models
- WebRTC connection flow: offer → answer → ICE candidates → DataChannel ready

### MotionDriver (`MotionDriver/`)

Low-level ESP32 firmware that bridges UART commands to motors and servos.

**Technology:** PlatformIO, ESP32-WROOM, C++

**Key Components:**

- `src/main.cpp` - Initializes UART, servo bus, motor drivers; main loop
- `inputs/UARTCommandInput.cpp/.h` - Parses UART commands and routes to controllers
- `outputs/ServoController.cpp/.h` - PCA9685 servo bus control with sweep motion
- `outputs/MotorController.cpp/.h` - LEDC PWM channels for DRV8833 H-bridges
- `include/pins.h` - **Central pin map** (authoritative source)

**Hardware Connections:** see [HARDWARE.md](../../HARDWARE.md#esp32-pin-map) for the pin map, or
`include/pins.h` for the authoritative values.

**UART Command Protocol:**

Commands are newline-delimited. Error responses prefixed with `ERR`.

- `PING` - Connection test, responds with `PONG`
- `S <servo> <angle>` - Set servo position (servo: 0-5, angle: 0-180)
- `SWEEP <servo> <start> <end> <step> <delay>` - Sweep servo motion
- `MOTOR <motor> <speed>` - Control motor (motor: 0-5, speed: -255 to 255)
- `LOG <enable>` - Enable/disable telemetry logging
- `HELP` - Display CLI help (from `docs/cli_help.txt`)

**Development Commands:**

```bash
cd MotionDriver
platformio run  # Build firmware
platformio upload  # Flash to ESP32
platformio device monitor  # Serial monitor
```

**Important Notes for Agents:**

- Refer to `include/pins.h` for authoritative pin mapping
- Keep `docs/cli_help.txt` in sync with command implementations
- Pins 2 and 15 are boot-sensitive; swap if boot issues occur
- All commands must be newline-terminated
- Error responses start with `ERR` prefix

### Legacy WebApp (`webapp/`)

FastAPI-based HTTP wrapper around MotionDriver serial CLI for debugging.

**Technology:** FastAPI, pyserial, Python 3.9+

**Structure:**

- `main.py` - FastAPI application
- `serial_bridge.py` - Serial communication wrapper
- `config.py` - Configuration management
- `static/` - HTML/CSS/JS dashboard
- `tests/` - pytest test suite

**Configuration (Environment Variables):**

```bash
MOTIONDRIVER_SERIAL_PORT=/dev/ttyUSB0  # Serial device
MOTIONDRIVER_SERIAL_BAUDRATE=115200     # Baud rate
MOTIONDRIVER_DRY_RUN=1                  # Use in-memory stub
MOTIONDRIVER_LOG_TRAFFIC=0              # Silence command logs
```

**API Routes:**

- All routes namespaced under `/api/*`
- Wraps UART commands: `PING`, `S`, `SWEEP`, `MOTOR`, `LOG`
- Returns JSON responses

**Development Commands:**

```bash
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MOTIONDRIVER_SERIAL_PORT=/dev/cu.usbserial-11220
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Testing:**

```bash
pytest webapp/tests
```

**Important Notes for Agents:**

- This is a **legacy** component; ChedWeb is the modern replacement
- Useful for quick debugging without WebRTC complexity
- Can run in dry-run mode for UI testing without hardware
- Consider using systemd, tmux, or screen for persistent Pi deployment

## 🔧 Hardware Specifications

**→ See [HARDWARE.md](../../HARDWARE.md) for the authoritative hardware reference:** bill of
materials, wiring diagram, pin map, wheel indexing, and known issues. Do not restate hardware
details in this file — link to it instead.

Quick orientation for agents:

- **MCU:** Freenove ESP32-WROOM (`board = esp32dev`). *Not* an Arduino Mega, *not* a C3 SuperMini —
  both were evaluated and dropped. Older docs claiming otherwise are stale.
- **Pi ↔ ESP32:** USB serial via CH340 bridge, `/dev/ttyUSB0` @ 115200. **Not** GPIO UART —
  `PIN_UART2_RX/TX` in `pins.h` are vestigial and unused.
- **Actuation:** 6 DC motors via 3× DRV8833; 6 servos via PCA9685 on I²C.
- **Power:** single 2S LiPo (7.4 V nom / 8.4 V full). Pi runs off the ESP32 breakout's 5 V buck,
  which is why motor inrush can brown out the Pi.

### High-Level Processing

- **Board:** Raspberry Pi 3B, hostname `cheddarpi`
- **OS:** Debian 13 (trixie)
- **Python:** 3.9+ (3.13 on the Pi)
- **Node.js:** 18+ required for frontend development

## 🛠️ Development Workflows

### Working with ChedWeb

**Local Development (on Mac/PC):**

```bash
# Terminal 1 - Backend with mock camera
cd PieBrain/ChedWeb/backend
source .venv/bin/activate
export CAMERA_ENABLED=false  # Use test pattern
python main.py

# Terminal 2 - Frontend
cd PieBrain/ChedWeb/frontend
npm run dev
```

**On Raspberry Pi:**

```bash
# Setup (one-time)
sudo bash ~/Cheddar/PieBrain/setup_rpi.sh --git-name "Name" --git-email "email"
sudo reboot

# Development
cd ~/Cheddar/PieBrain/ChedWeb/backend
source .venv/bin/activate
python main.py  # Camera enabled by default
```

**Production Deployment:**

```bash
# Install as systemd service
sudo cp ~/Cheddar/PieBrain/ChedWeb/backend/backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable backend.service
sudo systemctl start backend.service
```

### Working with MotionDriver

**Building Firmware:**

```bash
cd MotionDriver
platformio run  # Verify build
platformio upload  # Flash to ESP32
```

**Testing Commands:**

```bash
# Via serial monitor
platformio device monitor
# Then type commands:
PING
S 0 90
MOTOR 0 100
HELP
```

**Via WebApp:**

```bash
cd webapp
export MOTIONDRIVER_SERIAL_PORT=/dev/ttyUSB0
uvicorn main:app --reload
# Open http://localhost:8000
```

### Schema Synchronization

When modifying data models, keep schemas in sync:

1. **Backend:** Update `backend/models.py` (Pydantic models)
2. **Frontend:** Update `frontend/src/types/schemas.ts` (Zod schemas)
3. **Test:** Verify with type checking and runtime validation

Example:

```python
# backend/models.py
class TelemetryData(BaseModel):
    timestamp: float
    battery_voltage: float
    new_field: int  # Added
```

```typescript
// frontend/src/types/schemas.ts
export const telemetryDataSchema = z.object({
  timestamp: z.number(),
  battery_voltage: z.number(),
  new_field: z.number(),  // Added - must match!
});
```

## 🧪 Testing

### Frontend Tests

```bash
cd PieBrain/ChedWeb/frontend
npm run test  # Run vitest
npm run test:ui  # Interactive UI
```

### Backend Tests

```bash
cd PieBrain/ChedWeb/backend
source .venv/bin/activate
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/test_api.py::test_healthz  # Specific test
```

### WebApp Tests

```bash
cd webapp
source .venv/bin/activate
pytest tests/
```

## 📝 Code Style Guidelines

### Python

- **Formatting:** Follow PEP 8
- **Type hints:** Use type annotations consistently
- **Models:** Pydantic for validation
- **Async:** Use async/await for I/O operations (FastAPI endpoints, WebRTC)
- **Config:** Environment variables via `.env`, validated in `config.py`

### TypeScript/React

- **Formatting:** Prettier with default config
- **Components:** Functional components with hooks
- **State:** Zustand for global state
- **Validation:** Zod schemas for runtime validation
- **Styling:** Tailwind CSS utility classes
- **UI:** shadcn/ui components

### C++ (MotionDriver)

- **Style:** Google C++ Style Guide
- **Naming:** CamelCase for classes, camelCase for methods
- **Headers:** Include guards, clear documentation
- **Pin definitions:** Central in `include/pins.h`

## 🚨 Common Issues & Solutions

### Camera Not Working

1. Check camera enabled: `rpicam-hello --version`
2. Enable via raspi-config if needed
3. Verify system packages installed (see `CAMERA_SETUP.md`)
4. Check `.env` has `CAMERA_ENABLED=true`
5. Look for mock mode fallback in logs

### UART Communication Issues

1. Verify serial port: `ls /dev/tty*`
2. Check baud rate matches (115200)
3. Ensure proper power and ground connections
4. Test with `PING` command
5. Check pin mapping in `include/pins.h`

### WebRTC Connection Fails

1. Check backend running and accessible
2. Verify frontend proxy configuration
3. Look for CORS issues in browser console
4. Check signaling endpoint `/signaling/offer`
5. Inspect browser WebRTC internals: `chrome://webrtc-internals`

### Motor/Servo Not Responding

1. Check power supply and voltage levels
2. Verify DRV8833 STBY pin is HIGH (pin 27)
3. Check PCA9685 OE pin is LOW (pin 5)
4. Test with simple command: `S 0 90` or `MOTOR 0 100`
5. Verify pin connections against `include/pins.h`

## 🎯 Agent Decision-Making Guidelines

### When to Use ChedWeb vs WebApp

- **ChedWeb:** Real-time control, video streaming, gamepad input, production use
- **WebApp:** Quick debugging, testing serial commands, simple HTTP API needs

### When to Modify Schemas

- **Always** update both Pydantic (backend) and Zod (frontend) together
- **Test** with actual data flow after changes
- **Document** new fields in code comments

### When to Update Pin Mappings

- **Never** hardcode pins in source files
- **Always** update `include/pins.h` first
- **Document** hardware reasons for pin choices
- **Test** thoroughly after pin changes (boot behavior, conflicts)

### When to Add New UART Commands

1. Add command parsing in `UARTCommandInput.cpp`
2. Update `docs/cli_help.txt`
3. Test via serial monitor
4. Optionally add WebApp endpoint if useful for debugging

### When Working with Video Streaming

- **Prefer** hardware acceleration (picamera2 H.264 encoder)
- **Test** with mock mode first (`CAMERA_ENABLED=false`)
- **Monitor** performance (CPU, bandwidth, latency)
- **Configure** resolution/framerate based on Pi model and network

## 📚 Additional Documentation

- **ChedWeb Setup:** `PieBrain/ChedWeb/SETUP.md`
- **Camera Setup:** `PieBrain/ChedWeb/CAMERA_SETUP.md`
- **UART CLI Help:** `MotionDriver/docs/cli_help.txt`
- **Pi Setup:** `PieBrain/README.md`

## 💡 Tips for AI Agents

1. **Always check pinout** in `include/pins.h` before suggesting hardware changes
2. **Keep schemas in sync** when modifying data models between frontend/backend
3. **Use mock modes** for testing without hardware (camera, serial)
4. **Follow type safety** - leverage Pydantic and Zod for validation
5. **Test incrementally** - verify each component works before integration
6. **Respect boot pins** - pins 2, 15 on ESP32 affect boot behavior
7. **Check documentation** in respective README files before making assumptions
8. **Consider power** - verify voltage levels and current requirements
9. **Monitor resources** - Pi 3 has limited CPU/memory for video encoding
10. **Version compatibility** - Python 3.9+ required, Node.js 18+ required

---

**Last Updated:** 2025-11-08  
**Primary Maintainer:** Adam Probert  
**Repository:** github.com/AdamProbert/Cheddar
