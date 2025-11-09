#!/bin/bash
# ChedWeb Systemd Service Installation Script
# This script installs and enables both backend and frontend services

set -e

echo "🚀 Installing ChedWeb systemd services..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (sudo ./install_services.sh)"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SERVICE="$SCRIPT_DIR/backend/cheddar-backend.service"
FRONTEND_SERVICE="$SCRIPT_DIR/frontend/cheddar-frontend.service"

# Check if service files exist
if [ ! -f "$BACKEND_SERVICE" ]; then
    echo "❌ Backend service file not found: $BACKEND_SERVICE"
    exit 1
fi

if [ ! -f "$FRONTEND_SERVICE" ]; then
    echo "❌ Frontend service file not found: $FRONTEND_SERVICE"
    exit 1
fi

# Install backend service
echo "📦 Installing backend service..."
cp "$BACKEND_SERVICE" /etc/systemd/system/cheddar-backend.service

# Install frontend service
echo "📦 Installing frontend service..."
cp "$FRONTEND_SERVICE" /etc/systemd/system/cheddar-frontend.service

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable services (start on boot)
echo "✅ Enabling services to start on boot..."
systemctl enable cheddar-backend.service
systemctl enable cheddar-frontend.service

# Start services
echo "▶️  Starting services..."
systemctl start cheddar-backend.service
systemctl start cheddar-frontend.service

# Show status
echo ""
echo "✨ Installation complete!"
echo ""
echo "📊 Service Status:"
echo "===================="
systemctl status cheddar-backend.service --no-pager -l
echo ""
systemctl status cheddar-frontend.service --no-pager -l
echo ""
echo "📝 Useful Commands:"
echo "===================="
echo "  View backend logs:      journalctl -u cheddar-backend -f"
echo "  View frontend logs:     journalctl -u cheddar-frontend -f"
echo "  Restart backend:        sudo systemctl restart cheddar-backend"
echo "  Restart frontend:       sudo systemctl restart cheddar-frontend"
echo "  Stop services:          sudo systemctl stop cheddar-backend cheddar-frontend"
echo "  Disable services:       sudo systemctl disable cheddar-backend cheddar-frontend"
echo "  Reset Backend starts:   sudo systemctl reset-failed cheddar-backend"
echo "  Reset Frontend starts:  sudo systemctl reset-failed cheddar-frontend"
echo ""
echo "🌐 Access Points:"
echo "===================="
echo "  Backend API:  http://$(hostname -I | awk '{print $1}'):8000"
echo "  Frontend UI:  http://$(hostname -I | awk '{print $1}'):3000"
echo ""
