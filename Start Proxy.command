#!/bin/bash
# ─────────────────────────────────────────────
#  Tanker Tracker — AIS Proxy Launcher
#  Double-click this file to start the proxy.
# ─────────────────────────────────────────────

cd "$(dirname "$0")"

echo ""
echo "  🛢️  Tanker Tracker — AIS Stream Proxy"
echo "  ───────────────────────────────────────"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "  ✗ python3 not found. Install from python.org"
  read -p "  Press Enter to close..."
  exit 1
fi

# Install websockets if missing
python3 -c "import websockets" 2>/dev/null || {
  echo "  Installing websockets..."
  pip3 install websockets --quiet --break-system-packages 2>/dev/null || pip3 install websockets --quiet
}

echo "  ✓ Starting proxy on ws://localhost:8765"
echo "  ✓ Open tanker-tracker.html → Live AIS tab → Connect"
echo "  ✗ Press Ctrl+C to stop"
echo ""

python3 proxy.py
