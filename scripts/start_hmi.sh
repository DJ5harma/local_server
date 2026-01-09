#!/bin/bash
# Simple script to start the Thermax HMI server and browser in kiosk mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Starting Thermax HMI${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo -e "${YELLOW}Please create it first:${NC}"
    echo "  cd $PROJECT_DIR"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if server is already running
if pgrep -f "run.py" > /dev/null; then
    echo -e "${YELLOW}⚠ Server is already running${NC}"
    echo -e "${YELLOW}  Use './stop_hmi.sh' to stop it first${NC}"
    echo ""
    read -p "Do you want to restart it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo -e "${YELLOW}Stopping existing server...${NC}"
    pkill -f "run.py" || true
    sleep 2
fi

# Activate virtual environment and start server
echo -e "${GREEN}Step 1: Starting server...${NC}"
cd "$PROJECT_DIR"

# Start server in background
source venv/bin/activate
nohup python run.py > /tmp/thermax-hmi.log 2>&1 &
SERVER_PID=$!

echo -e "${BLUE}  Server PID: $SERVER_PID${NC}"
echo -e "${BLUE}  Logs: /tmp/thermax-hmi.log${NC}"

# Wait for server to be ready
echo -e "${YELLOW}  Waiting for server to start...${NC}"
SERVER_URL="http://localhost:5000"
MAX_WAIT=30
CHECK_INTERVAL=1
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -o /dev/null -w "%{http_code}" "$SERVER_URL" 2>/dev/null | grep -q "200\|30[0-9]"; then
        echo -e "${GREEN}  ✓ Server is ready!${NC}"
        break
    fi
    sleep $CHECK_INTERVAL
    WAITED=$((WAITED + CHECK_INTERVAL))
    echo -n "."
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}  ✗ Server did not start in time${NC}"
    echo -e "${YELLOW}  Check logs: tail -f /tmp/thermax-hmi.log${NC}"
    exit 1
fi

echo ""

# Set display for browser
export DISPLAY=:0

# Wait for X server if needed
if ! xset q &>/dev/null 2>&1; then
    echo -e "${YELLOW}  Waiting for X server...${NC}"
    sleep 3
fi

# Determine which browser to use
if command -v chromium-browser &> /dev/null; then
    BROWSER_CMD="chromium-browser"
elif command -v chromium &> /dev/null; then
    BROWSER_CMD="chromium"
elif command -v google-chrome &> /dev/null; then
    BROWSER_CMD="google-chrome"
else
    echo -e "${RED}ERROR: No browser found${NC}"
    echo -e "${YELLOW}  Install chromium-browser: sudo apt install chromium-browser${NC}"
    exit 1
fi

# Close any existing browser instances
echo -e "${GREEN}Step 2: Launching browser...${NC}"
pkill -f "$BROWSER_CMD" 2>/dev/null || true
sleep 1

# Launch browser in kiosk mode
echo -e "${BLUE}  Using: $BROWSER_CMD${NC}"
$BROWSER_CMD \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --autoplay-policy=no-user-gesture-required \
    "$SERVER_URL" > /dev/null 2>&1 &

BROWSER_PID=$!
sleep 2

# Verify browser started
if pgrep -f "$BROWSER_CMD" > /dev/null; then
    echo -e "${GREEN}  ✓ Browser launched (PID: $BROWSER_PID)${NC}"
else
    echo -e "${YELLOW}  ⚠ Browser may not have started properly${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Thermax HMI Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Server:${NC}"
echo "  URL: http://localhost:5000"
echo "  PID: $SERVER_PID"
echo "  Logs: tail -f /tmp/thermax-hmi.log"
echo ""
echo -e "${BLUE}Browser:${NC}"
echo "  PID: $BROWSER_PID"
echo "  Mode: Kiosk"
echo ""
echo -e "${YELLOW}To stop:${NC}"
echo "  ./scripts/stop_hmi.sh"
echo ""
