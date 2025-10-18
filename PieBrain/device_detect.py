"""Helper utilities to auto-detect input event devices for controllers.

Currently focused on detecting an Xbox Wireless Controller connected via
Bluetooth (or USB) on a Raspberry Pi. Falls back gracefully if none found.

Usage (module):
    python -m PieBrain.device_detect --xbox

Returned path printed to stdout for easy shell capture.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional

XBOX_NAME_PATTERNS = [
    re.compile(r"xbox", re.IGNORECASE),
    re.compile(r"xbox\s+wireless", re.IGNORECASE),
]

@dataclass
class InputDevice:
    path: str
    name: str
    is_joystick: bool
    score: int = 0

    def compute_score(self) -> int:
        score = 0
        for pat in XBOX_NAME_PATTERNS:
            if pat.search(self.name):
                score += 10
        if self.is_joystick:
            score += 5
        # Prefer event devices over js devices for evdev usage
        if self.path.startswith('/dev/input/event'):
            score += 2
        self.score = score
        return score


def _udev_props(path: str) -> str:
    try:
        return subprocess.run(
            ["udevadm", "info", "-q", "property", "-n", path],
            capture_output=True,
            text=True,
            timeout=1.0,
        ).stdout
    except Exception:
        return ""


def _extract_name(props: str) -> str:
    for line in props.splitlines():
        if line.startswith("NAME="):
            return line.split("=", 1)[1].strip().strip("\"")
    return ""


def _is_joystick(props: str) -> bool:
    # ID_INPUT_JOYSTICK=1 is a strong indicator
    for line in props.splitlines():
        if line.startswith("ID_INPUT_JOYSTICK=") and line.endswith("1"):
            return True
    return False


def find_xbox_controller() -> Optional[InputDevice]:
    base = "/dev/input"
    if not os.path.isdir(base):
        return None
    devices: List[InputDevice] = []
    for entry in sorted(os.listdir(base)):
        if not (entry.startswith("event") or entry.startswith("js")):
            continue
        path = os.path.join(base, entry)
        props = _udev_props(path)
        name = _extract_name(props)
        is_js = _is_joystick(props)
        if not name:
            continue  # skip unnamed devices
        dev = InputDevice(path=path, name=name, is_joystick=is_js)
        dev.compute_score()
        devices.append(dev)

    if not devices:
        return None
    # Filter to those matching Xbox pattern first
    xbox_like = [d for d in devices if any(pat.search(d.name) for pat in XBOX_NAME_PATTERNS)]
    candidates = xbox_like or devices
    # Sort descending by score
    candidates.sort(key=lambda d: d.score, reverse=True)
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-detect controller input devices")
    parser.add_argument("--xbox", action="store_true", help="Detect Xbox Wireless Controller event device")
    args = parser.parse_args()

    if args.xbox:
        dev = find_xbox_controller()
        if dev:
            print(dev.path)
            return 0
        print("No Xbox controller detected", flush=True)
        return 1
    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
