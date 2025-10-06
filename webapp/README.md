# Local web control (FastAPI)

A lightweight FastAPI application in `webapp/` exposes the serial CLI over HTTP for quick debugging without a terminal. It wraps the same commands (`PING`, `S`, `SWEEP`, `MOTOR`, `LOG`) and serves a static dashboard for servo and motor control.

## Prerequisites

- Python 3.9 or newer (Raspberry Pi OS Bullseye/Bookworm and macOS already include this via `python3`).
- USB/UART connection to the MotionDriver (e.g. `/dev/ttyUSB0` on Linux/Pi or `/dev/cu.usbserial-XXXX` on macOS).

## Install dependencies

```bash
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure the serial link

Set the target serial port via environment variable before launching the app:

```bash
export MOTIONDRIVER_SERIAL_PORT=/dev/cu.usbserial-11220  # adjust for your setup
export MOTIONDRIVER_SERIAL_BAUDRATE=115200               # optional (defaults to 115200)
```

Additional toggles:

- `MOTIONDRIVER_DRY_RUN=1` — use an in-memory stub instead of a real serial device (handy for UI demos).
- `MOTIONDRIVER_LOG_TRAFFIC=0` — silence the command/response logs.

## Run the web server

```bash
uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in a browser to access the dashboard. All API routes are namespaced under `/api/*` and respond with JSON.

## Test the web app

```bash
pytest webapp/tests
```

Consider using `systemd --user`, `tmux`, or `screen` on the Raspberry Pi if you want the server to run continuously without blocking a login shell.
