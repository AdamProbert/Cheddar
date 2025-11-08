# Rover Input Control System

This document describes the unified input system for controlling the Cheddar rover - a 6-wheel independent drive and steer platform.

## Overview

The Cheddar rover features **6 independently driven and steered wheels**, enabling advanced mobility modes:

- **Ackermann Steering** - Car-like steering with front wheels
- **Crab/Strafe** - All wheels point same direction for sideways movement  
- **Tank Drive** - Differential left/right for tight turns
- **Spin Turn** - Rotate in place around center
- **Point Turn** - Pivot around middle wheels

The input system converts user inputs (keyboard or Xbox controller) into drive mode-specific wheel commands transmitted via WebRTC DataChannel to the ESP32 MotionDriver.

## Architecture

```
┌─────────────────┐
│ Keyboard/Gamepad│
└────────┬────────┘
         │ Raw inputs
         v
  ┌──────────────┐
  │ InputManager │  Drive Mode Selection
  │ - Ackermann  │  + Kinematics Engine
  │ - Crab       │
  │ - Tank       │
  │ - Spin       │
  │ - Point Turn │
  └──────┬───────┘
         │ 6 motor speeds + 6 steering angles
         v
  ┌──────────────┐
  │ WebRTC DC    │  DataChannel
  └──────┬───────┘
         │
         v
  ┌──────────────┐
  │ PeerManager  │  Backend (Raspberry Pi)
  └──────┬───────┘
         │
         v
  ┌─────────────────────┐
  │ MotionDriverBridge  │
  └──────┬──────────────┘
         │ UART (115200 baud)
         v
  ┌──────────────┐
  │ ESP32        │
  │ PCA9685 (6x) │  Steering Servos (0-180°)
  │ DRV8833 (3x) │  Drive Motors (±255)
  └──────────────┘
         │
         v
  ┌─────────────────────────────┐
  │ 6 Wheels (Independent D/S) │
  │ FL  FR                      │
  │ ML  MR                      │
  │ RL  RR                      │
  └─────────────────────────────┘
```

## Command Schema

### ControlCommand Structure

```typescript
{
  type: 'motor' | 'servo' | 'ping' | 'stop' | 'estop',
  motors?: [number, number, number, number, number, number],  // -1.0 to 1.0
  servos?: [number, number, number, number, number, number],  // 0 to 180 (90=straight)
  timestamp: number  // milliseconds
}
```

### Wheel/Servo Mapping

The rover uses a unified indexing system for both drive motors and steering servos:

```
Index  Position      Motor (speed)    Servo (angle)
-----  ---------     -------------    -------------
  0    Front Left    Drive FL         Steer FL
  1    Front Right   Drive FR         Steer FR
  2    Middle Left   Drive ML         Steer ML
  3    Middle Right  Drive MR         Steer MR
  4    Rear Left     Drive RL         Steer RL
  5    Rear Right    Drive RR         Steer RR
```

- **Motor speeds:** `-1.0` (full reverse) to `1.0` (full forward)
- **Servo angles:** `0` to `180` degrees (`90` = straight ahead)

## Drive Modes

### 1. Ackermann Steering (Default)

Traditional car-like steering - front wheels steer, all wheels drive at same speed.

**Use cases:** Normal driving, efficient straight-line travel

```
Servos: [90±45°, 90±45°, 90, 90, 90, 90]
Motors: [speed, speed, speed, speed, speed, speed]
```

### 2. Crab/Strafe

All wheels point in the same direction, enabling sideways (strafe) movement.

**Use cases:** Parallel parking, precise positioning, moving through narrow gaps

```
All servos: Same angle based on joystick direction
All motors: Same speed
```

### 3. Tank Drive

All wheels point straight, differential speeds between left and right sides.

**Use cases:** Tight turns, simple control, maximum torque

```
Servos: [90, 90, 90, 90, 90, 90]
Motors: [L, R, L, R, L, R] (L/R differential)
```

### 4. Spin Turn

Wheels arranged in a circle around the rover center, enabling rotation in place.

**Use cases:** Precise orientation, zero-radius turning, confined spaces

```
FL: 135° (angled right-forward)
FR: 45°  (angled left-forward)
ML: 180° (pointing right)
MR: 0°   (pointing left)
RL: 45°  (angled left-back)
RR: 135° (angled right-back)
```

### 5. Point Turn

Front and rear wheels steer opposite directions, pivoting around middle wheels.

**Use cases:** Tight maneuvering, reduced turning radius

```
Front servos: 90±45° (based on turn input)
Middle servos: 90 (straight)
Rear servos: 90∓45° (opposite of front)
```

## Frontend Implementation

### InputManager (`frontend/src/utils/inputManager.ts`)

**Features:**

- Unified keyboard and gamepad input handling
- Automatic gamepad detection and reconnection
- Tank drive control scheme
- Configurable deadzone for analog sticks
- Continuous polling at 60Hz (requestAnimationFrame)

**Keyboard Controls:**

- `W` / `↑` - Forward
- `S` / `↓` - Backward
- `A` / `←` - Turn/steer left
- `D` / `→` - Turn/steer right
- `1` - Ackermann mode
- `2` - Crab mode
- `3` - Tank mode
- `4` - Spin mode
- `5` - Point turn mode
- `Space` / `Esc` - Emergency stop

**Xbox Controller Controls:**

- **Left Stick Y** - Forward/backward
- **Right Stick X** - Turn/steer
- **D-Pad Up** - Ackermann mode
- **D-Pad Left** - Crab mode
- **D-Pad Down** - Tank mode
- **D-Pad Right** - Spin mode
- **B Button** - Emergency stop

### RoverControls Component (`frontend/src/components/RoverControls.tsx`)

**Features:**

- Real-time display of motor speeds (6 motors)
- Real-time display of servo angles (6 servos)
- Gamepad connection status indicator
- Emergency stop and stop all buttons
- Context-sensitive control help

## Backend Implementation

### MotionDriverBridge (`backend/motion_driver_bridge.py`)

**Features:**

- Asynchronous serial communication via `pyserial-asyncio`
- Command translation from high-level to UART protocol
- Mock mode for testing without hardware
- Connection health monitoring (PING/PONG)

**UART Protocol Translation:**

| Frontend Command | UART Command(s) |
|-----------------|----------------|
| `motors: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]` | `MOTOR 0 127`, `MOTOR 1 127`, ... |
| `servos: [90, 90, 90, 90, 90, 90]` | `S 0 90`, `S 1 90`, ... |
| `type: 'estop'` | `MOTOR 0 0`, `MOTOR 1 0`, ... (all motors) |

Speed conversion: `uart_speed = int(frontend_speed * 255)`

### PeerManager Integration

The `PeerManager` receives commands from the WebRTC DataChannel and forwards them to the `MotionDriverBridge`:

```python
# In peer_manager.py
if self.motion_driver:
    loop = asyncio.get_event_loop()
    loop.create_task(self.motion_driver.send_command(command))
```

## Configuration

### Backend (.env)

```bash
# Serial port (ESP32 connection)
SERIAL_PORT=/dev/ttyUSB0      # USB-to-serial adapter
# Or for Pi GPIO UART:
# SERIAL_PORT=/dev/serial0

SERIAL_BAUDRATE=115200
SERIAL_MOCK=false             # Set true for testing without hardware
```

### Frontend

No configuration needed - the input system auto-detects gamepads and falls back to keyboard.

## Usage

### Development (Mock Mode)

Test the full input system without hardware:

```bash
# Backend
cd PieBrain/ChedWeb/backend
export SERIAL_MOCK=true
export CAMERA_ENABLED=false
python main.py

# Frontend (separate terminal)
cd PieBrain/ChedWeb/frontend
npm run dev
```

1. Open <http://localhost:5173>
2. Click "Connect"
3. Use keyboard or plug in Xbox controller
4. Watch motor/servo values update in real-time
5. Backend logs will show `[MOCK]` commands

### Production (Raspberry Pi)

With ESP32 MotionDriver connected via UART:

```bash
# On Raspberry Pi
cd ~/Cheddar/PieBrain/ChedWeb/backend

# Create .env
cp .env.example .env
# Edit .env and set:
#   SERIAL_PORT=/dev/ttyUSB0  (or /dev/serial0)
#   SERIAL_MOCK=false
#   CAMERA_ENABLED=true

# Run backend
python main.py
```

Frontend can be accessed from any device on the network at `http://<pi-ip>:8000`.

## Testing

### Frontend Tests

```bash
cd frontend
npm run test
```

### Backend Tests

```bash
cd backend
pytest tests/
```

### Manual Testing Checklist

- [ ] Keyboard inputs control motors smoothly
- [ ] Gamepad connects automatically when plugged in
- [ ] Emergency stop zeroes all motors immediately
- [ ] Servo controls respond to keyboard/gamepad
- [ ] Motor values display correctly in UI
- [ ] Backend receives and logs commands
- [ ] UART commands sent to ESP32 (check `platformio device monitor`)
- [ ] Physical motors/servos respond to commands

## Troubleshooting

### Gamepad Not Detected

1. Check browser gamepad support: <https://gamepad-tester.com/>
2. Press any button on the gamepad to wake it
3. Check browser console for connection logs
4. Try reconnecting via USB or Bluetooth

### No Motor Response

1. Check backend logs for command reception
2. Verify serial connection: `ls -l /dev/ttyUSB*` or `ls -l /dev/serial*`
3. Test ESP32 directly: `platformio device monitor` and send `PING`
4. Check DRV8833 STBY pin is HIGH (GPIO 27)
5. Verify power supply to motors

### Servo Not Moving

1. Check PCA9685 OE pin is LOW (GPIO 5)
2. Verify I2C connection: `i2cdetect -y 1` (should show 0x40)
3. Check servo power supply (separate from logic)
4. Test with simple command: `S 0 90`

### Serial Permission Denied

```bash
# Add user to dialout group (Raspberry Pi)
sudo usermod -a -G dialout $USER
# Log out and back in
```

## Future Enhancements

- [ ] Add rate limiting to prevent command flooding
- [ ] Implement deadman switch (auto-stop on connection loss)
- [ ] Add configurable control sensitivity
- [ ] Support custom button mappings
- [ ] Add haptic feedback for gamepad
- [ ] Implement smooth servo interpolation
- [ ] Add telemetry feedback (motor current, servo position)
- [ ] Record and replay command sequences

## Related Documentation

- [AGENTS.md](../../.github/instructions/AGENTS.md) - Full project overview
- [MotionDriver CLI Help](../../../MotionDriver/docs/cli_help.txt) - UART command reference
- [MotionDriver pins.h](../../../MotionDriver/include/pins.h) - Hardware pin mapping
