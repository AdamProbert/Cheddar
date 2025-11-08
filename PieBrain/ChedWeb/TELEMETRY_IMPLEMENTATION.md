# System Telemetry Implementation (Option 3: DataChannel)

## Overview
Implemented real-time system metrics monitoring sent via WebRTC DataChannel with time-series graphs.

## What Was Added

### Backend Changes

1. **New Model** (`models.py`)
   - `SystemMetrics` - Contains CPU, memory, temperature, and disk usage data

2. **Dependencies** (`requirements.txt`)
   - Added `psutil>=5.9.0` for system monitoring

3. **PeerManager Updates** (`peer_manager.py`)
   - `_collect_system_metrics()` - Collects CPU, memory, temperature, disk stats using psutil
   - `_send_metrics()` - Sends metrics via DataChannel
   - `_start_metrics_loop()` - Automatic metrics collection every 1 second
   - Automatically starts when DataChannel opens
   - Properly cleans up metrics task on disconnect

### Frontend Changes

1. **Type Definitions** (`types/schemas.ts`)
   - `SystemMetricsSchema` - Zod schema matching backend model
   - `SystemMetrics` TypeScript type

2. **State Management** (`store.ts`)
   - `systemMetrics` - Current metrics snapshot
   - `metricsHistory` - Rolling buffer of last 60 data points (1 minute)
   - `updateSystemMetrics()` - Handles incoming metrics and maintains history

3. **WebRTC Updates** (`utils/webrtc.ts`)
   - Added `onSystemMetrics` callback
   - DataChannel message handler distinguishes between telemetry and metrics

4. **Connection Controls** (`components/ConnectionControls.tsx`)
   - Wired up `updateSystemMetrics` callback to WebRTC manager

5. **New Component** (`components/SystemMetricsCard.tsx`)
   - Displays current values: CPU, Memory, Temperature, Disk usage
   - Line chart for CPU & Memory over time (Recharts)
   - Separate line chart for CPU temperature
   - Auto-updates as metrics stream in

6. **App Integration** (`App.tsx`)
   - Added SystemMetricsCard to sidebar below TelemetryCard

7. **Dependencies** (`package.json`)
   - Added `recharts` for time-series graphs

## How It Works

1. **WebRTC DataChannel established** → Backend starts metrics loop
2. **Every 1 second**: Backend collects system stats via `psutil` and sends via DataChannel
3. **Frontend receives** → Stores in Zustand state with rolling history (max 60 points)
4. **UI auto-updates** → Current values + graphs display real-time data

## Installation Steps

### Backend (on Raspberry Pi)
```bash
cd /Users/adamprobert/projects/Cheddar/PieBrain/ChedWeb/backend
source .venv/bin/activate  # or create venv if needed
pip install -r requirements.txt
```

### Frontend (already done)
```bash
cd /Users/adamprobert/projects/Cheddar/PieBrain/ChedWeb/frontend
npm install  # recharts already installed
```

## Testing

1. Start backend: `python main.py` (or uvicorn)
2. Start frontend: `npm run dev`
3. Click "Connect" button
4. Watch SystemMetricsCard populate with graphs after a few seconds

## Metrics Collected

- **CPU Usage** (%) - Overall CPU utilization
- **Memory Usage** (%) - RAM usage percentage
- **CPU Temperature** (°C) - Raspberry Pi CPU thermal sensor
- **Disk Usage** (%) - Root filesystem usage

## Features

✅ Real-time updates (1 second interval)
✅ Low overhead (uses existing WebRTC DataChannel)
✅ Time-series graphs showing last 60 seconds
✅ Separate graphs for CPU/Memory and Temperature
✅ Works offline (no external services needed)
✅ Encrypted by default (DTLS via WebRTC)
✅ Automatic cleanup on disconnect

## Future Improvements

- [ ] Configurable metrics interval
- [ ] Add network I/O stats
- [ ] Add process-level metrics
- [ ] Export metrics history to CSV
- [ ] Alert thresholds (high CPU/temp warnings)
- [ ] Longer history with time range selector
