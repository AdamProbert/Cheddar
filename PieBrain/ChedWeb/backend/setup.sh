#!/bin/bash
# Setup script for ChedWeb backend on Raspberry Pi

set -e

echo "🚀 Setting up ChedWeb Backend..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment with system site packages (needed for picamera2)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment (with system site packages for picamera2)..."
    python3 -m venv venv --system-site-packages
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To start the backend:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or for production:"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
