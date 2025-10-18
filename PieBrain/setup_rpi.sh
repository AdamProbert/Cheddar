#!/usr/bin/env bash
set -euo pipefail

# setup_rpi.sh
# Simplified Raspberry Pi setup script for Cheddar.
# Assumes Python 3.13 is already present (stock Raspberry Pi OS).
# Unconditionally installs and configures: apt updates, base packages, git (with provided name/email),
# pip (if missing), pipx + virtualenv tools, zsh + Oh My Zsh, SSH key, and clones the Cheddar repo + sets up virtualenv.

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

log "Setting default shell to zsh for $INVOKING_USER"
chsh -s /usr/bin/zsh "$INVOKING_USER" || err "Failed to change shell to zsh (continuing)."

log "Setup complete. Log out/in for new shell to apply."

cat <<EOF
Next steps:
- Add the printed SSH public key to GitHub (Settings → SSH and GPG keys).
- Activate your project environment:
  source ~/Cheddar/.venv/bin/activate
- Optionally set your default shell to zsh (already changed if chsh succeeded): chsh -s /usr/bin/zsh $INVOKING_USER
EOF

exit 0
