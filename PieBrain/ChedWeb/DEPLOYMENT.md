# ChedWeb Deployment Guide

This guide covers deploying ChedWeb as systemd services on the Raspberry Pi for automatic startup and restart management.

## 🚀 Quick Start

```bash
cd ~/Cheddar/PieBrain/ChedWeb
sudo ./install_services.sh
```

This will:

- Install both backend and frontend systemd services
- Enable them to start on boot
- Start them immediately
- Configure automatic restart on failure (up to 5 attempts within 10 minutes)

## 📦 What Gets Installed

### Backend Service (`cheddar-backend.service`)

- **Port:** 8000
- **Working Directory:** `/home/adamprobert/Cheddar/PieBrain/ChedWeb/backend`
- **Process:** uvicorn serving FastAPI app
- **Auto-update:** Pulls from `main` branch on every restart
- **Logs:** `journalctl -u cheddar-backend`

### Frontend Service (`cheddar-frontend.service`)

- **Port:** 3000
- **Working Directory:** `/home/adamprobert/Cheddar/PieBrain/ChedWeb/frontend`
- **Process:** Production build served via `npx serve`
- **Auto-update:** Pulls from `main` branch, runs `npm install` and `npm run build` on every restart
- **Logs:** `journalctl -u cheddar-frontend`
- **Dependencies:** Waits for backend to be ready before starting

## 🔧 Service Management

### View Service Status

```bash
sudo systemctl status cheddar-backend
sudo systemctl status cheddar-frontend
```

### Start Services

```bash
sudo systemctl start cheddar-backend
sudo systemctl start cheddar-frontend
```

### Stop Services

```bash
sudo systemctl stop cheddar-backend
sudo systemctl stop cheddar-frontend
```

### Restart Services

```bash
sudo systemctl restart cheddar-backend
sudo systemctl restart cheddar-frontend
```

### Enable/Disable Auto-Start on Boot

```bash
# Enable (already done by install script)
sudo systemctl enable cheddar-backend
sudo systemctl enable cheddar-frontend

# Disable
sudo systemctl disable cheddar-backend
sudo systemctl disable cheddar-frontend
```

## 📝 Viewing Logs

### Real-time Log Streaming

```bash
# Backend logs
journalctl -u cheddar-backend -f

# Frontend logs
journalctl -u cheddar-frontend -f

# Both services
journalctl -u cheddar-backend -u cheddar-frontend -f
```

### View Recent Logs

```bash
# Last 50 lines
journalctl -u cheddar-backend -n 50

# Since boot
journalctl -u cheddar-backend -b

# Since specific time
journalctl -u cheddar-backend --since "1 hour ago"
```

### Filter by Log Level

```bash
# Only errors
journalctl -u cheddar-backend -p err

# Warnings and above
journalctl -u cheddar-backend -p warning
```

## 🔄 Auto-Update Workflow

Both services automatically sync code on startup:

1. **Git checkout main** - Ensures we're on the main branch
2. **Git reset --hard HEAD** - Discards any local changes
3. **Git pull** - Fetches latest code from remote
4. **Service starts** - Launches with fresh code

To deploy new changes:

```bash
# Push to GitHub from your dev machine
git push origin main

# On the Pi, restart services to pull updates
sudo systemctl restart cheddar-backend
sudo systemctl restart cheddar-frontend
```

## 🛡️ Restart Policy

Both services are configured with:

- **Restart on failure:** Automatically restarts if process crashes
- **Restart attempts:** Up to 5 restarts within 10 minutes
- **Restart delay:** 10 seconds between attempts
- **Behavior after limit:** Service stops and requires manual restart

## 🌐 Access Points

Once services are running:

- **Backend API:** `http://<raspberry-pi-ip>:8000`
- **Frontend UI:** `http://<raspberry-pi-ip>:3000`
- **API Documentation:** `http://<raspberry-pi-ip>:8000/docs`

Find your Pi's IP:

```bash
hostname -I
```

## 🔍 Troubleshooting

### Service won't start

```bash
# Check service status for errors
sudo systemctl status cheddar-backend

# View full logs
journalctl -u cheddar-backend -n 100

# Check if ports are already in use
sudo lsof -i :8000
sudo lsof -i :3000
```

### Git sync fails

Ensure the Pi has SSH keys configured for GitHub:

```bash
# Check if SSH key exists
ls -la ~/.ssh/id_*.pub

# If not, generate one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy and paste to https://github.com/settings/keys
```

### Backend can't find camera

Check camera is enabled:

```bash
rpicam-hello --version
```

If needed, enable via raspi-config:

```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### Frontend build fails

Ensure Node.js is installed:

```bash
node --version  # Should be 18+
npm --version
```

If not installed:

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Python dependencies missing

The backend virtual environment should be created by the setup script. If missing:

```bash
cd ~/Cheddar/PieBrain/ChedWeb/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🗑️ Uninstalling Services

```bash
# Stop services
sudo systemctl stop cheddar-backend cheddar-frontend

# Disable auto-start
sudo systemctl disable cheddar-backend cheddar-frontend

# Remove service files
sudo rm /etc/systemd/system/cheddar-backend.service
sudo rm /etc/systemd/system/cheddar-frontend.service

# Reload systemd
sudo systemctl daemon-reload
```

## 📚 Additional Resources

- **Main Setup Guide:** `SETUP.md`
- **Camera Configuration:** `CAMERA_SETUP.md`
- **Input System:** `INPUT_SYSTEM.md`
- **Telemetry Details:** `TELEMETRY_IMPLEMENTATION.md`

## 🐛 Common Issues

### "Failed to start cheddar-frontend.service: Unit cheddar-backend.service not found"

The frontend depends on the backend. Ensure both service files are installed:

```bash
ls -l /etc/systemd/system/cheddar-*.service
```

### "git pull" fails with authentication error

Set up SSH keys (see Git sync fails section above) or configure git credentials.

### Services restart constantly

Check logs for the root cause:

```bash
journalctl -u cheddar-backend -n 200
```

If code has bugs, fix them locally, push to main, then restart services.

---

**Last Updated:** 2025-11-09  
**Maintainer:** Adam Probert
