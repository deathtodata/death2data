#!/bin/bash
# Death2Data - Run from Laptop

echo "Starting Death2Data..."

# Kill any existing server on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Start Python server
cd ~/Desktop/death2data
python3 -m http.server 3000 &

echo ""
echo "✅ Death2Data is running!"
echo ""
echo "Local:    http://localhost:3000"
echo ""
echo "To expose to internet:"
echo "  cloudflared tunnel --url http://localhost:3000"
echo ""
echo "To stop:"
echo "  lsof -ti:3000 | xargs kill -9"
echo ""
