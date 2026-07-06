#!/bin/bash
# Rebuild the ChedWeb frontend production bundle and restart the frontend service.
#
# The frontend is intentionally NOT rebuilt on boot: `npm install && npm run build`
# is too slow to finish within a systemd start timeout on a Raspberry Pi 3B, which
# caused cheddar-frontend.service to time out and restart-loop. Instead, the service
# just serves the pre-built dist/, and you run this script after changing anything
# under frontend/.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"

echo "🏗️  Building frontend (npm install + npm run build)..."
echo "    (this can take several minutes on a Raspberry Pi)"
npm install
npm run build

echo "🔄 Restarting cheddar-frontend.service..."
sudo systemctl restart cheddar-frontend.service

echo "✅ Done. Frontend UI: http://$(hostname -I | awk '{print $1}'):3000"
