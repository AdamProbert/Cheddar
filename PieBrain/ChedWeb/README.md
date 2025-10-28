# ChedWeb - Raspberry Pi Rover Control

A low-latency WebRTC-based rover control system designed for Raspberry Pi 3B. Control your robot remotely with real-time video streaming and gamepad input.

## 🎯 Features

- **WebRTC Video**: Ultra-low latency H.264 video streaming (ready for camera integration)
- **DataChannel Control**: Real-time command/telemetry via WebRTC DataChannel
- **REST API**: Configuration and non-realtime operations
- **Modern UI**: React + TypeScript + Tailwind + shadcn/ui
- **Gamepad Support**: Browser Gamepad API ready (Xbox controller)
- **Type-Safe**: Zod schemas (frontend) match Pydantic models (backend)

## 📁 Project Structure

```
ChedWeb/
├── backend/              # Python FastAPI + aiortc
│   ├── main.py          # FastAPI application
│   ├── peer_manager.py  # WebRTC peer connection manager
│   ├── models.py        # Pydantic models
│   ├── config.py        # Settings management
│   └── requirements.txt
├── frontend/            # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── utils/       # WebRTC, gamepad utilities
│   │   ├── types/       # Zod schemas
│   │   ├── App.tsx
│   │   └── store.ts     # Zustand state management
│   └── package.json
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Raspberry Pi 3B** (or similar) running Raspberry Pi OS
- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** and npm

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
python main.py
```

The backend will start on `http://0.0.0.0:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start on `http://localhost:5173` with proxy to backend.

### Access the App

1. Open browser to `http://localhost:5173`
2. Click **Connect** button
3. WebRTC connection establishes with DataChannel
4. Video feed placeholder displays (ready for camera integration)
5. Telemetry updates in real-time

## 🔌 API Endpoints

### Backend

- `GET /healthz` - Health check
- `POST /signaling/offer` - WebRTC SDP offer/answer exchange
- `WS /ws/debug` - WebSocket echo for testing
- `GET /api/config` - Public configuration

### WebRTC DataChannel

Once connected, the `control` DataChannel handles:

- **Client → Server**: Control commands (motor, servo, ping)
- **Server → Client**: Telemetry data (battery, latency, sensors)

Example control command:

```json
{
  "type": "motor",
  "motor_left": 0.5,
  "motor_right": 0.5,
  "timestamp": 1698508800000
}
```

Example telemetry:

```json
{
  "type": "telemetry",
  "battery_voltage": 7.4,
  "cpu_temp": 45.2,
  "signal_strength": 85,
  "timestamp": 1698508800000
}
```

## 🛠️ Development

### Backend

```bash
# Lint and format
ruff check .
black .

# Run tests
pytest

# Type checking
mypy .
```

### Frontend

```bash
# Lint
npm run lint

# Format
npm run format

# Run tests
npm test

# Build production
npm run build
```

## 📋 Next Steps & TODOs

### 1. Camera Integration (H.264 Video Track)

The video track is **not yet implemented**. To add it:

**Backend (`peer_manager.py`):**

- Add `libcamera` or `picamera2` for camera capture
- Use `aiortc.VideoStreamTrack` to create H.264 stream
- Add track to peer connection: `pc.addTrack(video_track)`
- Consider using hardware encoding on Pi 3B

**Resources:**

- [aiortc VideoStreamTrack docs](https://aiortc.readthedocs.io/en/latest/api.html#videostreamtrack)
- [picamera2 examples](https://github.com/raspberrypi/picamera2)

### 2. UART/Serial Bridge to ESP32

Currently stubbed. To forward commands:

**Backend:**

- Create `serial_bridge.py` module
- Use `pyserial` to communicate with ESP32
- Register callback: `peer_manager.set_command_callback(serial_bridge.send_command)`
- Implement protocol (JSON, binary, etc.)

**ESP32:**

- Listen on UART (e.g., 115200 baud)
- Parse commands and drive motors/servos
- Send sensor data back to Pi

### 3. Safety Features

**Deadman Timer:**

- Client sends periodic pings
- Backend monitors last command timestamp
- Stop motors if timeout exceeds `DEADMAN_TIMEOUT_MS`

**Rate Limiting:**

- Limit command frequency to `COMMAND_RATE_LIMIT_HZ`
- Prevent command spam

**Emergency Stop:**

- Add `/api/emergency-stop` endpoint
- Dedicated UI button

### 4. Gamepad Integration

**Frontend (`utils/gamepad.ts`):**

- Wire up `GamepadManager` to send commands
- Map left stick → motor control
- Map right stick → servo control
- Add deadzone and curve configuration

**UI:**

- Add gamepad status indicator
- Show button mapping
- Allow rebinding

### 5. Additional Features

- [ ] Bandwidth monitoring and adaptive quality
- [ ] ICE candidate trickling for faster connection
- [ ] Reconnection logic on disconnect
- [ ] Recording/playback of video/telemetry
- [ ] Multi-client support (observer mode)
- [ ] HTTPS/WSS for production
- [ ] Authentication and authorization

## 🔧 Configuration

### Backend (`.env`)

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# WebRTC
STUN_SERVER=stun:stun.l.google.com:19302
# TURN_SERVER=turn:turn.example.com:3478

# Serial (for ESP32)
SERIAL_PORT=/dev/ttyUSB0
SERIAL_BAUDRATE=115200

# Safety
DEADMAN_TIMEOUT_MS=500
COMMAND_RATE_LIMIT_HZ=50
```

### Frontend

Vite proxy is configured in `vite.config.ts` to forward:

- `/api/*` → `http://localhost:8000`
- `/signaling/*` → `http://localhost:8000`
- `/ws/*` → `ws://localhost:8000`

## 🌐 Production Deployment

### On Raspberry Pi

1. **Backend** (systemd service):

```bash
sudo cp backend.service /etc/systemd/system/
sudo systemctl enable backend
sudo systemctl start backend
```

2. **Frontend** (static files):

```bash
cd frontend
npm run build
# Serve dist/ with nginx or serve via FastAPI static files
```

3. **HTTPS** (Let's Encrypt + nginx):

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d rover.example.com
```

### Environment Variables (Production)

- Set `DEBUG=false`
- Configure TURN server for NAT traversal
- Set strong secrets/credentials
- Restrict CORS origins

## 📚 Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **aiortc** - WebRTC implementation
- **Pydantic** - Data validation
- **Loguru** - Structured logging
- **uvicorn** - ASGI server

### Frontend

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component primitives
- **Zustand** - State management
- **Zod** - Runtime validation
- **Axios** - HTTP client

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please open issues/PRs.

---

**Current Status**: ✅ Scaffold complete, ready for camera and UART integration.
