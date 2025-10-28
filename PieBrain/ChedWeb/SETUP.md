# ChedWeb - Quick Start Guide

Complete setup instructions for getting ChedWeb running on your Raspberry Pi 3B.

## 📋 Prerequisites

### Hardware

- Raspberry Pi 3B (or newer)
- MicroSD card (16GB+ recommended)
- Power supply
- Network connection (WiFi or Ethernet)

### Software

- Raspberry Pi OS (Bullseye or newer)
- Python 3.9+ (3.11 recommended)
- Node.js 18+ and npm

## 🚀 Installation

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install system dependencies for aiortc
sudo apt install -y \
  libavformat-dev libavcodec-dev libavdevice-dev \
  libavutil-dev libswscale-dev libswresample-dev libavfilter-dev \
  libopus-dev libvpx-dev pkg-config
```

### Step 2: Clone/Copy Project

```bash
# Navigate to your projects directory
cd ~
mkdir -p projects
cd projects

# If using git:
git clone <your-repo-url> ChedWeb
cd ChedWeb/PieBrain/ChedWeb

# Or copy the ChedWeb folder to your Pi
```

### Step 3: Backend Setup

```bash
cd backend

# Run setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Step 4: Frontend Setup

```bash
cd ../frontend

# Run setup script
chmod +x setup.sh
./setup.sh

# Or manually:
npm install
```

## 🏃 Running

### Development Mode

**Terminal 1 - Backend:**

```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

**Access the app:**

- From Pi: `http://localhost:5173`
- From network: `http://<pi-ip>:5173`

### Production Mode

#### Option 1: Manual

**Backend:**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend (build and serve):**

```bash
cd frontend
npm run build

# Serve with a simple HTTP server
npx serve -s dist -l 80
```

#### Option 2: Systemd Service (Recommended)

**Backend service:**

```bash
# Edit paths in backend.service if needed
sudo cp backend/backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable backend
sudo systemctl start backend

# Check status
sudo systemctl status backend
```

**Frontend (nginx):**

```bash
# Install nginx
sudo apt install -y nginx

# Build frontend
cd frontend
npm run build

# Copy build to nginx
sudo cp -r dist/* /var/www/html/

# Create nginx config
sudo nano /etc/nginx/sites-available/chedweb
```

Add this config:

```nginx
server {
    listen 80;
    server_name _;
    
    root /var/www/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /signaling {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/chedweb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## ✅ Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Quick Connection Test

1. Start backend: `python main.py`
2. Check health: `curl http://localhost:8000/healthz`
3. Start frontend: `npm run dev`
4. Open browser to `http://localhost:5173`
5. Click "Connect" button
6. Check browser console for WebRTC logs

## 🐛 Troubleshooting

### Backend won't start

**Check Python version:**

```bash
python3 --version  # Should be 3.9+
```

**Check dependencies:**

```bash
source venv/bin/activate
pip list
```

**Check logs:**

```bash
# If using systemd
sudo journalctl -u backend -f
```

### Frontend won't build

**Clear cache:**

```bash
rm -rf node_modules package-lock.json
npm install
```

**Check Node version:**

```bash
node --version  # Should be 18+
```

### WebRTC connection fails

**Check STUN server:**

- Default is `stun:stun.l.google.com:19302`
- Try alternative: `stun:stun.stunprotocol.org:3478`

**Check firewall:**

```bash
sudo ufw allow 8000
sudo ufw allow 5173
sudo ufw allow 80
```

**Check ICE candidates in browser console:**

- Look for "ICE connection state" logs
- Should see "connected" state

### Video not showing

This is expected! Camera integration is not yet implemented. See README.md "Next Steps" section.

## 🔒 Security Notes

**For production deployment:**

1. **Change default ports** in `.env`
2. **Enable HTTPS** with Let's Encrypt:

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Restrict CORS** in `backend/main.py`
4. **Add authentication** (OAuth2, JWT, etc.)
5. **Configure TURN server** for NAT traversal
6. **Set strong credentials** in `.env`

## 📚 Next Steps

See the main [README.md](README.md) for:

- Adding H.264 video track
- UART/Serial bridge to ESP32
- Gamepad integration
- Safety features (deadman timer, rate limiting)

## 🆘 Getting Help

- Check logs in browser console (F12)
- Check backend logs: `sudo journalctl -u backend -f`
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Review [README.md](README.md) for architecture details

---

**Status**: This is a scaffold with minimal "hello world" functionality. Camera and UART integration are next steps.
