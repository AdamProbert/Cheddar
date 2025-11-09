#!/usr/bin/env bash
# diagnose_uart.sh
# Diagnostic script for UART/serial connection issues between RPi and ESP32

set -euo pipefail

echo "=========================================="
echo "  UART Diagnostic Script"
echo "=========================================="
echo

# Check boot config
echo "1. Checking boot configuration..."
BOOT_CONFIG="/boot/firmware/config.txt"
[[ ! -f "$BOOT_CONFIG" ]] && BOOT_CONFIG="/boot/config.txt"

if [[ -f "$BOOT_CONFIG" ]]; then
  echo "   Boot config: $BOOT_CONFIG"
  
  if grep -q "^enable_uart=1" "$BOOT_CONFIG"; then
    echo "   ✓ UART is enabled"
  else
    echo "   ✗ UART NOT enabled (add 'enable_uart=1' to $BOOT_CONFIG)"
  fi
  
  if grep -q "^dtoverlay=disable-bt" "$BOOT_CONFIG"; then
    echo "   ✓ Bluetooth disabled (primary UART freed)"
  else
    echo "   ⚠ Bluetooth NOT disabled (primary UART may be in use)"
    echo "     Add 'dtoverlay=disable-bt' to $BOOT_CONFIG"
  fi
else
  echo "   ✗ Boot config not found at $BOOT_CONFIG"
fi
echo

# Check serial devices
echo "2. Checking serial devices..."
if ls /dev/serial* >/dev/null 2>&1; then
  echo "   Available serial devices:"
  ls -l /dev/serial* | sed 's/^/   /'
else
  echo "   ✗ No /dev/serial* devices found"
  echo "     UART may not be enabled or reboot required"
fi
echo

if ls /dev/ttyAMA* >/dev/null 2>&1; then
  echo "   Hardware UART devices:"
  ls -l /dev/ttyAMA* | sed 's/^/   /'
else
  echo "   ✗ No /dev/ttyAMA* devices found"
fi
echo

if ls /dev/ttyUSB* >/dev/null 2>&1; then
  echo "   USB serial devices:"
  ls -l /dev/ttyUSB* | sed 's/^/   /'
else
  echo "   No USB serial devices (expected - using GPIO UART)"
fi
echo

# Check user permissions
echo "3. Checking user permissions..."
CURRENT_USER="${SUDO_USER:-$USER}"
if groups "$CURRENT_USER" | grep -q dialout; then
  echo "   ✓ User '$CURRENT_USER' is in 'dialout' group"
else
  echo "   ✗ User '$CURRENT_USER' NOT in 'dialout' group"
  echo "     Run: sudo usermod -a -G dialout $CURRENT_USER"
  echo "     Then log out and back in"
fi
echo

# GPIO pin status
echo "4. GPIO pin status (14=TX, 15=RX)..."
if command -v raspi-gpio >/dev/null 2>&1; then
  echo "   GPIO 14 (TX):"
  raspi-gpio get 14 | sed 's/^/   /'
  echo "   GPIO 15 (RX):"
  raspi-gpio get 15 | sed 's/^/   /'
else
  echo "   'raspi-gpio' command not available"
  echo "   Install with: sudo apt install raspi-gpio"
fi
echo

# Test serial port
echo "5. Testing serial port access..."
SERIAL_DEVICE="/dev/serial0"
if [[ -e "$SERIAL_DEVICE" ]]; then
  echo "   Device: $SERIAL_DEVICE"
  
  # Check if we can open it
  if timeout 1 cat "$SERIAL_DEVICE" >/dev/null 2>&1; then
    echo "   ✓ Can read from $SERIAL_DEVICE"
  else
    if [[ $? -eq 124 ]]; then
      echo "   ✓ Can access $SERIAL_DEVICE (timeout is expected)"
    else
      echo "   ✗ Cannot access $SERIAL_DEVICE"
      echo "     Check permissions or add user to dialout group"
    fi
  fi
else
  echo "   ✗ $SERIAL_DEVICE does not exist"
  echo "     UART may not be enabled - reboot required"
fi
echo

# Check ChedWeb backend config
echo "6. Checking ChedWeb backend configuration..."
BACKEND_DIR="$HOME/Cheddar/PieBrain/ChedWeb/backend"
if [[ -f "$BACKEND_DIR/.env" ]]; then
  echo "   Found .env file"
  if grep -q "^SERIAL_PORT=" "$BACKEND_DIR/.env"; then
    CONFIGURED_PORT=$(grep "^SERIAL_PORT=" "$BACKEND_DIR/.env" | cut -d= -f2 | tr -d '"' | tr -d "'")
    echo "   Configured port: $CONFIGURED_PORT"
    if [[ "$CONFIGURED_PORT" == "/dev/serial0" ]]; then
      echo "   ✓ Using correct device (/dev/serial0)"
    else
      echo "   ⚠ Should use /dev/serial0 instead of $CONFIGURED_PORT"
    fi
  else
    echo "   Using default from config.py"
  fi
else
  echo "   No .env file found - using defaults from config.py"
  if grep -q 'serial_port.*=.*"/dev/ttyUSB0"' "$BACKEND_DIR/config.py" 2>/dev/null; then
    echo "   ⚠ Default is /dev/ttyUSB0 - should be /dev/serial0 for GPIO UART"
  fi
fi
echo

# Summary
echo "=========================================="
echo "  Diagnostic Summary"
echo "=========================================="
echo
echo "WIRING CHECKLIST (physical connections):"
echo "  ESP32 GPIO 16 (RX2) → RPi GPIO 14 (Pin 8) [TX]"
echo "  ESP32 GPIO 17 (TX2) → RPi GPIO 15 (Pin 10) [RX]"
echo "  ESP32 GND → RPi GND (e.g., Pin 6, 9, 14, 20, 25, 30, 34, 39)"
echo
echo "RASPBERRY PI CONFIGURATION:"
echo "  1. Ensure UART is enabled in boot config"
echo "  2. Ensure Bluetooth is disabled (frees primary UART)"
echo "  3. REBOOT after changing boot config"
echo "  4. Add user to 'dialout' group for serial access"
echo "  5. Use /dev/serial0 for serial device"
echo
echo "ESP32 TESTING:"
echo "  - Arduino Serial Monitor connects to UART0 (USB), not UART2"
echo "  - Cannot send Pi commands through Serial Monitor"
echo "  - Add Serial2.println() debug output to see Pi commands"
echo
echo "TESTING PROCEDURE:"
echo "  1. Fix wiring if incorrect"
echo "  2. On RPi, run: screen /dev/serial0 115200"
echo "  3. Type: PING (should see PONG from ESP32)"
echo "  4. Try other commands: HELP, S 0 1500, etc."
echo "  5. Press Ctrl+A then K to exit screen"
echo
echo "=========================================="
