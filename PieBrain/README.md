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
