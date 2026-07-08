#!/usr/bin/env python3
"""Detect the rover's serial port and write it to webapp/.env.

Usage:
    python scripts/detect_port.py            # auto-detect
    python scripts/detect_port.py COM5       # set explicitly

Exits non-zero (with an error message) if no serial port is connected, or if
the port is ambiguous and must be chosen by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

from serial.tools import list_ports

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
ENV_EXAMPLE_PATH = ENV_PATH.with_name(".env.example")
ENV_KEY = "MOTIONDRIVER_SERIAL_PORT"

# USB-UART bridges commonly found on ESP32 dev boards (VID -> chip family):
#   0x10C4 Silicon Labs CP210x, 0x1A86 QinHeng CH340/CH9102,
#   0x0403 FTDI, 0x303A Espressif native USB.
KNOWN_VIDS = {0x10C4, 0x1A86, 0x0403, 0x303A}
KNOWN_HINTS = (
    "cp210",
    "ch340",
    "ch910",
    "ftdi",
    "silicon labs",
    "wch",
    "usb-serial",
    "espressif",
)


def is_candidate(port) -> bool:
    if port.vid in KNOWN_VIDS:
        return True
    text = " ".join(
        filter(None, [port.description, port.manufacturer, port.product])
    ).lower()
    return any(hint in text for hint in KNOWN_HINTS)


def update_env(device: str) -> None:
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text().splitlines()
    elif ENV_EXAMPLE_PATH.exists():
        # Seed from the example so we keep the other defaults, not just the port.
        lines = ENV_EXAMPLE_PATH.read_text().splitlines()
    else:
        lines = []
    out, found = [], False
    for line in lines:
        if line.strip().startswith(f"{ENV_KEY}="):
            out.append(f"{ENV_KEY}={device}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{ENV_KEY}={device}")
    ENV_PATH.write_text("\n".join(out) + "\n")


def main() -> int:
    ports = list(list_ports.comports())
    explicit = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None

    if explicit:
        device = explicit
        known = {p.device for p in ports}
        if ports and device not in known:
            print(
                f"warning: {device} is not among the detected ports "
                f"({', '.join(sorted(known))})",
                file=sys.stderr,
            )
    else:
        if not ports:
            print(
                "error: no serial/COM ports found. Connect the rover over USB "
                "and try again.",
                file=sys.stderr,
            )
            return 1
        candidates = [p for p in ports if is_candidate(p)]
        pool = candidates or ports
        if len(pool) > 1:
            print(
                "error: multiple serial ports found; pass one explicitly, e.g. "
                f"`just port {pool[0].device}`:",
                file=sys.stderr,
            )
            for p in pool:
                print(f"  {p.device}  {p.description}", file=sys.stderr)
            return 1
        device = pool[0].device

    update_env(device)
    print(f"Set {ENV_KEY}={device} in {ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
