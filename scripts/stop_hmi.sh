#!/bin/bash
# Simple script to stop the Thermax HMI server and browser
# 
# IMPORTANT: This script ONLY stops the local_server and browser processes.
# It does NOT shut down, reboot, or affect the Raspberry Pi system in any way.
# The device will continue running normally after stopping the HMI.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stopping Thermax HMI${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop server
echo -e "${YELLOW}Step 1: Stopping server...${NC}"
SERVER_PIDS=$(pgrep -f "run.py" || true)

if [ -z "$SERVER_PIDS" ]; then
    echo -e "${YELLOW}  ⚠ No server process found${NC}"
else
    echo -e "${BLUE}  Found server PIDs: $SERVER_PIDS${NC}"
    pkill -f "run.py" || true
    sleep 2
    
    # Force kill if still running
    if pgrep -f "run.py" > /dev/null; then
        echo -e "${YELLOW}  Force killing server...${NC}"
        pkill -9 -f "run.py" || true
        sleep 1
    fi
    
    if ! pgrep -f "run.py" > /dev/null; then
        echo -e "${GREEN}  ✓ Server stopped${NC}"
    else
        echo -e "${RED}  ✗ Failed to stop server${NC}"
    fi
fi

echo ""

# Stop browser
echo -e "${YELLOW}Step 2: Stopping browser...${NC}"

# Determine which browser might be running
BROWSER_FOUND=0
BROWSER_PIDS=""

if pgrep -f "chromium-browser" > /dev/null; then
    BROWSER_CMD="chromium-browser"
    BROWSER_PIDS=$(pgrep -f "chromium-browser")
    BROWSER_FOUND=1
elif pgrep -f "chromium" > /dev/null; then
    BROWSER_CMD="chromium"
    BROWSER_PIDS=$(pgrep -f "chromium")
    BROWSER_FOUND=1
elif pgrep -f "google-chrome" > /dev/null; then
    BROWSER_CMD="google-chrome"
    BROWSER_PIDS=$(pgrep -f "google-chrome")
    BROWSER_FOUND=1
elif pgrep -f "chrome" > /dev/null; then
    BROWSER_CMD="chrome"
    BROWSER_PIDS=$(pgrep -f "chrome")
    BROWSER_FOUND=1
fi

if [ $BROWSER_FOUND -eq 0 ]; then
    echo -e "${YELLOW}  ⚠ No browser process found${NC}"
else
    echo -e "${BLUE}  Found $BROWSER_CMD PIDs: $BROWSER_PIDS${NC}"
    
    # Try graceful shutdown first
    pkill "$BROWSER_CMD" 2>/dev/null || true
    sleep 2
    
    # Force kill if still running
    if pgrep -f "$BROWSER_CMD" > /dev/null; then
        echo -e "${YELLOW}  Force killing browser...${NC}"
        pkill -9 "$BROWSER_CMD" 2>/dev/null || true
        pkill -9 -f "$BROWSER_CMD" 2>/dev/null || true
        sleep 1
    fi
    
    # Also try generic chrome/chromium kill
    pkill -9 chromium-browser 2>/dev/null || true
    pkill -9 chromium 2>/dev/null || true
    pkill -9 chrome 2>/dev/null || true
    
    if ! pgrep -f "$BROWSER_CMD" > /dev/null && ! pgrep -f "chromium\|chrome" > /dev/null; then
        echo -e "${GREEN}  ✓ Browser stopped${NC}"
    else
        echo -e "${YELLOW}  ⚠ Some browser processes may still be running${NC}"
        echo -e "${BLUE}  Remaining processes:${NC}"
        pgrep -f "chromium\|chrome" || true
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Thermax HMI Stopped${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}To start again:${NC}"
echo "  ./scripts/start_hmi.sh"
echo ""
