#!/usr/bin/env bash
set -euo pipefail

# setup_rpi.sh
# Raspberry Pi setup script for Cheddar ChedWeb project.
# Assumes Python 3.13 is already present (stock Raspberry Pi OS).
# 
# This script:
# - Updates system packages
# - Installs base development tools and git
# - Installs camera/video streaming dependencies (picamera2, libcamera, codec libraries)
# - Installs Node.js LTS (if not present) for frontend development
# - Configures git with provided name/email
# - Sets up Python tooling (pip, pipx, virtualenv)
# - Installs zsh + Oh My Zsh
# - Generates SSH key
# - Clones Cheddar repository
# - Sets up ChedWeb backend virtualenv and dependencies
# - Sets up ChedWeb frontend dependencies (npm install)
# - Enables camera interface (if needed)
# - Adds user to video group for camera access

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() { echo "[setup_rpi] $*"; }
err() { echo "[setup_rpi] ERROR: $*" >&2; }

usage() {
  cat <<USAGE
Usage: sudo bash $0 --git-name "Full Name" --git-email "email@example.com"

Required arguments:
  --git-name    Git user.name to configure globally
  --git-email   Git user.email to configure globally

Example:
  sudo bash $0 --git-name "Ada Lovelace" --git-email "ada@example.com"
USAGE
}

GIT_NAME=""
GIT_EMAIL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --git-name)
      GIT_NAME="$2"; shift 2;;
    --git-email)
      GIT_EMAIL="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      err "Unknown argument: $1"; usage; exit 1;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  err "This script must be run with sudo or as root."; exit 1
fi

if [[ -z "$GIT_NAME" || -z "$GIT_EMAIL" ]]; then
  err "--git-name and --git-email are required."; usage; exit 1
fi

INVOKING_USER="${SUDO_USER:-${USER}}"

log "Starting Raspberry Pi setup (invoking user: $INVOKING_USER)"

log "Updating apt package lists and upgrading..."
apt update -y
apt upgrade -y

BASE_PACKAGES=(curl wget ca-certificates build-essential lsb-release gnupg2 git zsh)
log "Installing base packages: ${BASE_PACKAGES[*]}"
apt install -y "${BASE_PACKAGES[@]}"

# Camera and video streaming dependencies for ChedWeb
CAMERA_PACKAGES=(python3-picamera2 python3-libcamera python3-kms++ libcap-dev libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev)
log "Installing camera and video codec libraries: ${CAMERA_PACKAGES[*]}"
apt install -y "${CAMERA_PACKAGES[@]}"

log "Configuring global git user.name and user.email"
sudo -u "$INVOKING_USER" git config --global user.name "$GIT_NAME"
sudo -u "$INVOKING_USER" git config --global user.email "$GIT_EMAIL"

if command -v python3 >/dev/null 2>&1; then
  log "Found python interpreter: $(python3 -V) (assuming >= 3.13 is OK)"
else
  err "python3 not found. Raspberry Pi OS should include Python 3.13; install manually and re-run."; exit 2
fi

if python3 -m pip --version >/dev/null 2>&1; then
  log "pip already available: $(python3 -m pip --version)"
else
  log "Installing pip via apt (PEP 668 compliant)"
  apt install -y python3-pip python3-venv || err "Failed to install python3-pip; please 'apt install python3-pip' manually."
  if python3 -m pip --version >/dev/null 2>&1; then
    log "pip installed: $(python3 -m pip --version)"
  else
    err "pip still not available after apt install attempts."
  fi
fi

log "Setting up Python tooling (pipx, virtualenv, virtualenvwrapper) avoiding PEP 668 conflicts"
# Try apt packages first where available
APT_PY_TOOLS=(pipx virtualenvwrapper)
apt install -y "${APT_PY_TOOLS[@]}" 2>/dev/null || true

# Ensure pipx binary (some distros package as /usr/bin/pipx). If missing, create an isolated venv to host tools.
if ! command -v pipx >/dev/null 2>&1; then
  log "pipx not available via apt; creating isolated tools venv"
  TOOLS_VENV="/opt/cheddar-tools-venv"
  python3 -m venv "$TOOLS_VENV"
  "$TOOLS_VENV/bin/python" -m pip install --upgrade pip
  "$TOOLS_VENV/bin/pip" install pipx virtualenv virtualenvwrapper
  # Expose pipx by symlink
  ln -sf "$TOOLS_VENV/bin/pipx" /usr/local/bin/pipx || true
  log "Installed pipx and related tools in isolated venv: $TOOLS_VENV"
else
  log "pipx available: $(pipx --version || echo 'unknown version')"
  # Install/upgrade virtualenv + virtualenvwrapper via pipx (isolated) if pipx works
  pipx install virtualenv >/dev/null 2>&1 || pipx upgrade virtualenv || true
  pipx install virtualenvwrapper >/dev/null 2>&1 || pipx upgrade virtualenvwrapper || true
fi

log "Installing Oh My Zsh for $INVOKING_USER"
sudo -u "$INVOKING_USER" -H bash -c 'RUNZSH=no CHSH=no KEEP_ZSHRC=yes bash -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"' || log "Oh My Zsh install script encountered an issue (continuing)."


log "Creating SSH key for $INVOKING_USER if absent"
SSH_HOME="/home/${INVOKING_USER}"
[[ "$INVOKING_USER" == "root" ]] && SSH_HOME="/root"
SSH_KEY_PATH="${SSH_HOME}/.ssh/id_ed25519"
sudo -u "$INVOKING_USER" mkdir -p "${SSH_HOME}/.ssh"
if [[ ! -f "${SSH_KEY_PATH}.pub" ]]; then
  sudo -u "$INVOKING_USER" ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$SSH_KEY_PATH" -N ""
else
  log "SSH key already exists at ${SSH_KEY_PATH}.pub"
fi

PUB_KEY_CONTENT="$(sudo -u "$INVOKING_USER" cat "${SSH_KEY_PATH}.pub" 2>/dev/null || true)"
if [[ -n "$PUB_KEY_CONTENT" ]]; then
  echo
  echo "=== BEGIN PUBLIC SSH KEY (${SSH_KEY_PATH}.pub) ==="
  echo "$PUB_KEY_CONTENT"
  echo "=== END PUBLIC SSH KEY ==="
  echo
else
  err "Could not read public key ${SSH_KEY_PATH}.pub"
fi

REPO_URL="https://github.com/AdamProbert/Cheddar.git"
CLONE_DIR="/home/${INVOKING_USER}/Cheddar"
[[ "$INVOKING_USER" == "root" ]] && CLONE_DIR="/root/Cheddar"
log "Cloning (or updating) Cheddar repo at ${CLONE_DIR}"
if [[ -d "${CLONE_DIR}/.git" ]]; then
  sudo -u "$INVOKING_USER" git -C "$CLONE_DIR" pull || log "Repo pull encountered an issue (continuing)."
else
  sudo -u "$INVOKING_USER" git clone "$REPO_URL" "$CLONE_DIR"
fi

if [[ -f "${CLONE_DIR}/requirements.txt" ]]; then
  log "Creating virtualenv (.venv) inside repo and installing requirements"
  sudo -u "$INVOKING_USER" python3 -m venv "${CLONE_DIR}/.venv"
  sudo -u "$INVOKING_USER" bash -lc "source '${CLONE_DIR}/.venv/bin/activate' && pip install --upgrade pip && pip install -r '${CLONE_DIR}/requirements.txt'"
else
  log "No requirements.txt found in repo; skipping dependency install"
fi

# Setup ChedWeb backend environment
CHEDWEB_BACKEND="${CLONE_DIR}/PieBrain/ChedWeb/backend"
if [[ -d "$CHEDWEB_BACKEND" ]]; then
  log "Setting up ChedWeb backend environment"
  
  # Create virtualenv for ChedWeb backend with system site packages (needed for picamera2)
  sudo -u "$INVOKING_USER" python3 -m venv "${CHEDWEB_BACKEND}/.venv" --system-site-packages
  
  # Install backend dependencies
  if [[ -f "${CHEDWEB_BACKEND}/requirements.txt" ]]; then
    log "Installing ChedWeb backend dependencies (including picamera2, av, numpy)"
    sudo -u "$INVOKING_USER" bash -lc "source '${CHEDWEB_BACKEND}/.venv/bin/activate' && pip install --upgrade pip && pip install -r '${CHEDWEB_BACKEND}/requirements.txt'"
  fi
  
  # Create .env file from .env.example if it doesn't exist
  if [[ -f "${CHEDWEB_BACKEND}/.env.example" ]] && [[ ! -f "${CHEDWEB_BACKEND}/.env" ]]; then
    log "Creating ChedWeb backend .env file from .env.example"
    sudo -u "$INVOKING_USER" cp "${CHEDWEB_BACKEND}/.env.example" "${CHEDWEB_BACKEND}/.env"
    log "Backend configuration created at ${CHEDWEB_BACKEND}/.env"
  fi
else
  log "ChedWeb backend directory not found; skipping ChedWeb-specific setup"
fi

# Setup ChedWeb frontend environment
CHEDWEB_FRONTEND="${CLONE_DIR}/PieBrain/ChedWeb/frontend"
if [[ -d "$CHEDWEB_FRONTEND" ]]; then
  log "Setting up ChedWeb frontend environment"
  
  # Check if Node.js and npm are available
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    log "Node.js $(node -v) and npm $(npm -v) detected"
  else
    log "Node.js/npm not found. Installing Node.js LTS..."
    
    # Install Node.js from NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt install -y nodejs
    
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
      log "Node.js $(node -v) and npm $(npm -v) installed successfully"
    else
      log "WARNING: Node.js installation may have failed. Frontend setup will be skipped."
    fi
  fi
  
  # Install frontend dependencies if Node.js is available
  if command -v npm >/dev/null 2>&1; then
    if [[ -f "${CHEDWEB_FRONTEND}/package.json" ]]; then
      log "Installing ChedWeb frontend dependencies"
      sudo -u "$INVOKING_USER" bash -lc "cd '${CHEDWEB_FRONTEND}' && npm install"
    fi
  fi
else
  log "ChedWeb frontend directory not found; skipping frontend setup"
fi

# Verify camera hardware is detected
log "Checking for camera hardware..."
CAMERA_DETECTED=false
if vcgencmd get_camera 2>/dev/null | grep -q "detected=1"; then
  log "Camera hardware detected via vcgencmd"
  CAMERA_DETECTED=true
elif ls /dev/video* >/dev/null 2>&1; then
  log "Video device(s) found: $(ls /dev/video* 2>/dev/null | tr '\n' ' ')"
  CAMERA_DETECTED=true
elif command -v rpicam-hello >/dev/null 2>&1 && timeout 2 rpicam-hello --list-cameras 2>&1 | grep -q "Available cameras"; then
  log "Camera detected via rpicam"
  CAMERA_DETECTED=true
else
  log "WARNING: No camera hardware detected. Ensure camera is properly connected."
  log "The system will still be configured, but camera may not work until hardware is connected."
fi

# Note: Modern Raspberry Pi OS has camera enabled by default
# Only enable if camera is detected but camera test fails
if [ "$CAMERA_DETECTED" = true ]; then
  CAMERA_WORKING=false
  if command -v rpicam-hello >/dev/null 2>&1; then
    timeout 2 rpicam-hello --version >/dev/null 2>&1 && CAMERA_WORKING=true
  fi
  
  if [ "$CAMERA_WORKING" = false ]; then
    log "Camera detected but not responding. Attempting to enable camera interface..."
    raspi-config nonint do_camera 0 || log "Camera enable command may have failed (continuing)"
    log "Camera interface enabled. A reboot is required."
  else
    log "Camera interface is already enabled and working"
  fi
else
  log "Skipping camera interface configuration (no camera detected)"
fi

# Add user to video group for camera access
log "Adding $INVOKING_USER to 'video' group for camera permissions"
usermod -a -G video "$INVOKING_USER" || log "Failed to add user to video group (continuing)"

log "Setting default shell to zsh for $INVOKING_USER"
chsh -s /usr/bin/zsh "$INVOKING_USER" || err "Failed to change shell to zsh (continuing)."

# Determine if reboot is needed
REBOOT_NEEDED=false
if [ "$CAMERA_DETECTED" = true ] && [ "$CAMERA_WORKING" = false ]; then
  REBOOT_NEEDED=true
  log "Setup complete. REBOOT REQUIRED for camera interface changes."
else
  log "Setup complete."
fi

echo
echo "=========================================="
echo "  Raspberry Pi Setup Summary"
echo "=========================================="
echo "✓ System packages updated"
echo "✓ Camera libraries installed (picamera2, libcamera, video codecs)"
echo "✓ Git configured (user: $GIT_NAME, email: $GIT_EMAIL)"
echo "✓ Python $(python3 -V 2>&1 | cut -d' ' -f2) with pip"
echo "✓ SSH key generated"
echo "✓ Cheddar repository cloned/updated"
echo "✓ ChedWeb backend environment configured"
command -v node >/dev/null 2>&1 && echo "✓ Node.js $(node -v) and npm $(npm -v) installed"
[[ -d "$CHEDWEB_FRONTEND" ]] && command -v npm >/dev/null 2>&1 && echo "✓ ChedWeb frontend dependencies installed"
[ "$CAMERA_DETECTED" = true ] && echo "✓ Camera hardware detected"
[ "$REBOOT_NEEDED" = true ] && echo "✓ Camera interface configured (reboot required)" || echo "✓ Camera ready to use"
echo "✓ User added to video group"
echo "✓ Default shell set to zsh"
echo "=========================================="
echo

cat <<EOF
Next steps:
- Add the printed SSH public key to GitHub (Settings → SSH and GPG keys).

EOF

if [ "$REBOOT_NEEDED" = true ]; then
cat <<EOF
- REBOOT the Raspberry Pi to apply camera interface changes:
  sudo reboot

EOF
fi

cat <<EOF

- Verify camera is working (after reboot if required):
  rpicam-hello                       # Should show camera preview
  rpicam-still --list-cameras        # List detected cameras
  rpicam-jpeg -o test.jpg            # Capture a test image

- Test picamera2 (used by ChedWeb):
  python3 -c "from picamera2 import Picamera2; cam = Picamera2(); cam.start(); print('Camera OK'); cam.stop()"

- Start ChedWeb backend (Terminal 1):
  cd ~/Cheddar/PieBrain/ChedWeb/backend
  source .venv/bin/activate
  python main.py

- Start ChedWeb frontend (Terminal 2 - if Node.js is installed):
  cd ~/Cheddar/PieBrain/ChedWeb/frontend
  npm run dev

- Access the web interface:
  http://<raspberry-pi-ip>:5173

- Camera configuration can be adjusted in:
  ~/Cheddar/PieBrain/ChedWeb/backend/.env

- For detailed camera setup, testing, and troubleshooting:
  ~/Cheddar/PieBrain/ChedWeb/CAMERA_SETUP.md

ChedWeb Backend:  ${CHEDWEB_BACKEND}
ChedWeb Frontend: ${CHEDWEB_FRONTEND}
EOF

exit 0
