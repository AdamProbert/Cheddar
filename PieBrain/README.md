# PieBrain - Raspberry Pi setup

This directory contains the Raspberry Pi side of the Cheddar project and includes a simplified
setup script to bootstrap a freshly flashed Pi. It assumes Raspberry Pi OS already ships with
Python 3.13 and does not attempt to install or modify Python. The setup script now directly
clones the Cheddar repository and creates a virtual environment.

## Script

`setup_rpi.sh` — updates apt, installs base packages (curl, wget, build tools, git, zsh), sets global git name/email (arguments), ensures pip, installs Python tooling (pipx / virtualenv / virtualenvwrapper) in a PEP 668–friendly way, installs Oh My Zsh, creates an SSH key (`~/.ssh/id_ed25519`) if missing and prints it, clones the Cheddar repo into `~/Cheddar` (or `/root/Cheddar`) and, if `requirements.txt` exists, creates `.venv` and installs dependencies.

## Quick start

1. Copy or clone this repository onto your Pi (or transfer `setup_rpi.sh` into this folder).
2. Run the setup script providing your git identity:

```bash
sudo bash ./setup_rpi.sh --git-name "Adam Probert" --git-email "adamprobert@live.co.uk"
```

## What the script does

- Apt update & upgrade
- Installs: curl, wget, ca-certificates, build-essential, lsb-release, gnupg2, git, zsh
- Configures global git user.name and user.email
- Ensures `pip` for the system `python3` (assumed 3.13)
- Installs Python tooling (pipx, virtualenv, virtualenvwrapper) via apt when available; if not, creates an isolated venv at `/opt/cheddar-tools-venv` to avoid PEP 668 (externally managed environment) conflicts
- Installs Oh My Zsh for the invoking user (without auto-launching zsh)
- Generates an Ed25519 SSH key if absent and prints the public key
- Clones the Cheddar repository and sets up `.venv` if `requirements.txt` exists

## Notes

- The script automatically sets your default shell to zsh; log out/in for it to take effect.
- Add the printed SSH public key to GitHub under Settings → SSH and GPG keys.
- If a USB Bluetooth dongle is detected during setup, the script appends `dtoverlay=disable-bt` to the active boot config (`/boot/firmware/config.txt` or `/boot/config.txt`) so that on next reboot the onboard UART Bluetooth is disabled and the dongle becomes the primary adapter.

### Bluetooth Dongle Auto-Setup

When you run `setup_rpi.sh`, it scans `lsusb` for a USB Bluetooth adapter (matches common vendor strings like TP-Link, Realtek, Intel). If found:

1. It appends `dtoverlay=disable-bt` to your boot config (unless already present).
2. On the next reboot the onboard Broadcom Bluetooth (UART hci0) is disabled.
3. The USB adapter will then appear as `hci0` (or the only controller) to BlueZ, reducing interference with Wi‑Fi on Pi 3 models.

To verify after reboot:

```bash
bluetoothctl list
hciconfig -a
```

Reverting (re-enable onboard Bluetooth):

```bash
sudo sed -i '/^dtoverlay=disable-bt$/d' /boot/firmware/config.txt 2>/dev/null || \
sudo sed -i '/^dtoverlay=disable-bt$/d' /boot/config.txt
sudo reboot
```

If you plug in a dongle after running the script (and want to disable onboard BT later), simply add the overlay manually:

```bash
echo 'dtoverlay=disable-bt' | sudo tee -a /boot/firmware/config.txt 2>/dev/null || \
echo 'dtoverlay=disable-bt' | sudo tee -a /boot/config.txt
sudo reboot
```

## Xbox Controller Teleoperation

An Xbox One (or Series) Bluetooth controller can be paired with the Raspberry Pi and used to drive the robot. The script `xbox_control.py` converts stick motions into per‑motor `MOTOR <index> <FORWARD|BACKWARD> <speed>` serial commands consumed by the MotionDriver firmware on the ESP32.

### Pair the Controller (Bluetooth)

1. Put the controller in pairing mode (hold the sync button until Xbox logo flashes rapidly).
2. On the Pi:

```bash
bluetoothctl
scan on         # wait until controller appears (e.g., 'Xbox Wireless Controller')
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
quit
```


### Install Dependencies (virtual environment recommended)

Inside the repo root (or `PieBrain/`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r PieBrain/requirements.txt  # installs evdev
pip install -r webapp/requirements.txt    # if you also need the FastAPI app
```

On some Raspberry Pi kernels you may need udev permissions (or run with sudo) to read the event device. Prefer creating a udev rule instead of running as root.

### Run the Teleop Script

Determine the controller event device path (often `/dev/input/eventX`, or use the auto-detect helper below). Then run:

```bash
python -m PieBrain.xbox_control --device /dev/input/event4 --port /dev/ttyS0 --baud 115200
```

Flags:

- `--device`  Required evdev path.
- `--port`    Serial port to the ESP32 (falls back to `MOTIONDRIVER_SERIAL_PORT`).
- `--baud`    Baud rate (default 115200).
- `--deadzone` Axis deadzone (default 0.08).
- `--rate`    Max command send rate Hz (default 20).
- `--log`     Enable serial traffic logging.
- `--dry-run` No serial; print / log only.

Buttons:

- A (BTN_SOUTH): Immediate ALL STOP.
- B (BTN_EAST): Exit program (also sends STOP).

Axes:

- Left stick Y (forward/back) => throttle (forward = push up).
- Right stick X => turn (left/right yaw).

Motor Mapping (current assumption): indices 0–2 = left side, 3–5 = right side. Each command is sent independently; firmware sums or handles as needed.

### Safety Notes

- Script sends `MOTOR ALL STOP` at start and on exit.
- If the controller disconnects, press Ctrl+C; a final STOP is still attempted.
- Consider adding a physical E‑stop that cuts motor power.

### Auto-Detect Helper

Run:

```bash
python -m PieBrain.device_detect --xbox
```

The script prints the most likely event device path for the Xbox controller (prioritises names containing "Xbox" and joystick capability). Use that path for `--device`.

### Future Enhancements

- Use triggers for variable speed scaling.
- Add servo pan/tilt mapping.
- Integrate directly with FastAPI REST for remote teleop.
