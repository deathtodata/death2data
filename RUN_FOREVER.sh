#!/bin/bash
# Death2Data - Keep Running Forever

echo "🚀 Death2Data - Auto-restart mode"
echo ""

# Kill existing
lsof -ti:3000 | xargs kill -9 2>/dev/null
pkill -f cloudflared 2>/dev/null

# Start server
cd ~/Desktop/death2data
python3 -m http.server 3000 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo "   http://localhost:3000"
echo ""

# Wait for server to be ready
sleep 2

# Start tunnel with auto-restart
echo "🌐 Starting cloudflare tunnel..."
echo "   (This will auto-restart if it dies)"
echo ""

while true; do
    cloudflared tunnel --url http://localhost:3000

    echo ""
    echo "⚠️  Tunnel died. Restarting in 5 seconds..."
    echo ""
    sleep 5
done
