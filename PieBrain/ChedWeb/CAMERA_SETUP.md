# Camera Video Streaming Setup Guide

This guide covers the setup and testing of the newly implemented camera video streaming feature for ChedWeb.

## ✨ What's New

Video streaming has been implemented with the following features:

- **Hardware-Accelerated H.264 Encoding**: Uses Raspberry Pi's native camera interface (picamera2)
- **WebRTC Video Track**: Real-time video streaming with ultra-low latency
- **Configurable Settings**: Resolution, framerate, and flip can be configured via environment variables
- **Mock Mode**: Automatic fallback to test pattern when camera is unavailable
- **Graceful Degradation**: System works without camera if disabled or unavailable

## 📦 Installation

### Automated Setup (Recommended)

The easiest way to set up the Raspberry Pi with all camera dependencies is to use the automated setup script:

```bash
# On your Raspberry Pi, run:
sudo bash ~/Cheddar/PieBrain/setup_rpi.sh --git-name "Your Name" --git-email "your@email.com"
```

This script automatically:

- Installs all camera and video codec system dependencies
- Enables the camera interface
- Creates the ChedWeb backend virtual environment
- Installs all Python dependencies
- Creates the `.env` configuration file

After running the script, **reboot** and proceed to [Testing](#-testing).

### Manual Setup

If you prefer to set up manually or need to troubleshoot:

#### On Raspberry Pi (with Camera)

1. **Install System Dependencies**

   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Install camera libraries
   sudo apt install -y python3-picamera2 python3-libcamera python3-kms++
   
   # Install video codec libraries and build dependencies
   sudo apt install -y libcap-dev libavformat-dev libavcodec-dev libavdevice-dev \
                        libavutil-dev libswscale-dev libswresample-dev libavfilter-dev
   ```

2. **Enable Camera Interface** (if needed)

   Modern Raspberry Pi OS has the camera enabled by default. You can verify with:

   ```bash
   # Check if camera is detected
   rpicam-hello --version
   ```

   If the camera is not working, you may need to enable it manually:

   ```bash
   sudo raspi-config
   # Navigate to: Interface Options -> Camera -> Enable
   
   # Reboot
   sudo reboot
   ```

3. **Install Python Dependencies**

   ```bash
   cd /path/to/ChedWeb/backend
   
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install requirements
   pip install -r requirements.txt
   ```

4. **Configure Camera Settings**

   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

   Important camera settings in `.env`:

   ```bash
   # Camera configuration
   CAMERA_ENABLED=true        # Enable/disable camera
   CAMERA_WIDTH=640           # Video width (320, 640, 1280, 1920)
   CAMERA_HEIGHT=480          # Video height (240, 480, 720, 1080)
   CAMERA_FRAMERATE=30        # Target FPS (15, 30, 60)
   CAMERA_FLIP_180=false      # Flip camera 180° (for upside-down mounting)
   ```

   **Performance Recommendations for Pi 3B:**
   - **Low latency**: 640x480 @ 30fps (recommended)
   - **Higher quality**: 1280x720 @ 30fps
   - **Lower bandwidth**: 320x240 @ 30fps

### On Development Machine (without Camera)

The system automatically uses a mock video source (color bar test pattern) when the camera is unavailable.

```bash
cd /path/to/ChedWeb/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements (picamera2 will be skipped on non-Pi systems)
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set CAMERA_ENABLED=true to see mock video
```

## 🧪 Testing

### 1. Backend Startup Test

```bash
cd backend
source .venv/bin/activate
python main.py
```

Expected output:

```
2024-11-08 10:00:00 | INFO     | main:lifespan:35 - Starting ChedWeb backend...
2024-11-08 10:00:00 | INFO     | main:lifespan:38 - Camera enabled: True
2024-11-08 10:00:00 | INFO     | camera:create_video_track:237 - Creating new camera video track
2024-11-08 10:00:00 | INFO     | camera:_init_camera:83 - Initializing Pi camera: 640x480@30fps
2024-11-08 10:00:00 | INFO     | camera:_init_camera:98 - Pi camera initialized successfully
```

**If camera is unavailable:**

```
2024-11-08 10:00:00 | WARNING  | camera:<module>:18 - picamera2 not available - camera streaming will be disabled
2024-11-08 10:00:00 | INFO     | camera:_init_camera:75 - Using mock video source (camera not available)
```

### 2. Camera Hardware Test (on Raspberry Pi)

Test camera independently:

```bash
# Quick test with camera
rpicam-hello

# List available cameras
rpicam-still --list-cameras

# Capture test image
rpicam-jpeg -o test.jpg

# Test picamera2 (used by ChedWeb)
python3 -c "from picamera2 import Picamera2; cam = Picamera2(); cam.start(); print('Camera OK'); cam.stop()"
```

### 3. WebRTC Connection Test

1. **Start backend:**

   ```bash
   cd backend
   source .venv/bin/activate
   python main.py
   ```

2. **Start frontend (in new terminal):**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Open browser:**
   - Navigate to `http://localhost:5173`
   - Click the **Connect** button
   - Watch the browser console and backend logs

4. **Expected behavior:**
   - Backend logs show: "Received SDP offer from client"
   - Backend logs show: "Video track created successfully"
   - Backend logs show: "Adding video track to peer connection"
   - Frontend shows video feed (camera or test pattern)
   - No errors in browser console

### 4. Video Stream Quality Test

Monitor video stream performance:

```bash
# In backend logs, you should see periodic framerate reports:
2024-11-08 10:01:00 | DEBUG    | camera:recv:175 - Camera stats - Frames: 300, FPS: 29.8
2024-11-08 10:01:10 | DEBUG    | camera:recv:175 - Camera stats - Frames: 600, FPS: 30.0
```

**In browser console**, check WebRTC stats:

```javascript
// Open browser DevTools (F12)
// In Console tab, paste:
pc.getStats().then(stats => {
  stats.forEach(report => {
    if (report.type === 'inbound-rtp' && report.kind === 'video') {
      console.log('Video FPS:', report.framesPerSecond);
      console.log('Bitrate:', report.bytesReceived);
    }
  });
});
```

## 🔧 Troubleshooting

### Camera Not Detected

**Problem**: `picamera2 not available` or camera initialization fails

**Solutions**:

1. Verify camera is connected properly (cable seated properly, correct port)
2. Test camera detection: `rpicam-hello` (should show preview)
3. List cameras: `rpicam-still --list-cameras`
4. Check camera permissions: `sudo usermod -a -G video $USER`
5. If still not working, enable manually: `sudo raspi-config` -> Interface Options -> Camera
6. Reboot after making changes: `sudo reboot`

**Note**: Modern Raspberry Pi OS uses `rpicam-*` commands and has camera enabled by default.

### Low Framerate

**Problem**: FPS significantly below configured rate

**Solutions**:

1. Reduce resolution: Try 640x480 instead of 1280x720
2. Reduce framerate target: Use 15 or 20 fps
3. Check CPU usage: `top` (camera encoding should use ~20-40% on Pi 3B)
4. Ensure adequate lighting for camera
5. Check network bandwidth if using WiFi

### Video Not Showing in Browser

**Problem**: Connection succeeds but no video appears

**Solutions**:

1. Check browser console for errors
2. Verify WebRTC connection state: Should be "connected"
3. Check that video track was added (backend logs)
4. Try different browser (Chrome/Edge recommended)
5. Check browser permissions for media

### Mock Video Instead of Real Camera

**Problem**: Test pattern shows instead of camera feed

**Solutions**:

1. Check `CAMERA_ENABLED=true` in `.env`
2. Verify picamera2 is installed: `python3 -c "import picamera2"`
3. Check backend logs for camera initialization errors
4. Ensure you're running on Raspberry Pi (mock is default on other systems)

## 📊 Configuration Reference

### Camera Settings

| Setting | Values | Description | Recommendation (Pi 3B) |
|---------|--------|-------------|------------------------|
| `CAMERA_ENABLED` | `true`/`false` | Enable camera streaming | `true` |
| `CAMERA_WIDTH` | 320-1920 | Video width in pixels | 640 |
| `CAMERA_HEIGHT` | 240-1080 | Video height in pixels | 480 |
| `CAMERA_FRAMERATE` | 10-60 | Target frames per second | 30 |
| `CAMERA_FLIP_180` | `true`/`false` | Flip camera 180° | `false` (or `true` if upside-down) |

### Resolution Presets

| Preset | Resolution | Bandwidth | CPU Usage | Use Case |
|--------|------------|-----------|-----------|----------|
| Low | 320x240 @ 15fps | ~300 Kbps | Low | Slow network, battery saving |
| Standard | 640x480 @ 30fps | ~1 Mbps | Medium | **Recommended for Pi 3B** |
| HD | 1280x720 @ 30fps | ~2-3 Mbps | High | Good network, quality priority |
| Full HD | 1920x1080 @ 30fps | ~4-5 Mbps | Very High | Not recommended for Pi 3B |

## 🚀 Production Deployment

For production use on Raspberry Pi:

1. **Optimize settings:**

   ```bash
   # In .env
   DEBUG=false
   LOG_LEVEL=WARNING
   CAMERA_WIDTH=640
   CAMERA_HEIGHT=480
   CAMERA_FRAMERATE=30
   ```

2. **Use systemd service** (see `backend.service` file):

   ```bash
   sudo cp backend.service /etc/systemd/system/
   sudo systemctl enable backend
   sudo systemctl start backend
   ```

3. **Monitor performance:**

   ```bash
   # Check service status
   sudo systemctl status backend
   
   # View logs
   sudo journalctl -u backend -f
   
   # Monitor CPU/memory
   htop
   ```

## 📝 Next Steps

Now that video streaming is working:

1. **Optimize encoding parameters** for your network conditions
2. **Add adaptive bitrate** based on network quality
3. **Implement recording** for debugging/playback
4. **Add camera controls** (brightness, contrast, exposure)
5. **Consider multiple quality levels** (user-selectable)

## 🔗 Related Documentation

- [picamera2 Documentation](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [aiortc Documentation](https://aiortc.readthedocs.io/)
- [WebRTC Browser API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)

---

**Status**: ✅ Video streaming implementation complete and ready for testing!
