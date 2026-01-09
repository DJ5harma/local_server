#!/bin/bash
# Reliable browser launcher for Thermax HMI
# Waits for server to be ready, then opens Chromium in kiosk mode

# Set display (required for GUI apps)
export DISPLAY=:0

# Wait for X server to be ready
if ! xset q &>/dev/null; then
    echo "Waiting for X server to be ready..."
    sleep 5
    # Try again
    if ! xset q &>/dev/null; then
        echo "ERROR: X server not available"
        exit 1
    fi
fi

# Configuration
SERVER_URL="http://localhost:5000"
MAX_WAIT=120  # Maximum seconds to wait for server (increased for boot time)
CHECK_INTERVAL=2  # Check every 2 seconds

# Function to check if server is ready
check_server() {
    curl -s -o /dev/null -w "%{http_code}" "$SERVER_URL" 2>/dev/null | grep -q "200\|30[0-9]"
}

# Wait for server to be ready
echo "Waiting for server at $SERVER_URL..."
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if check_server; then
        echo "Server is ready!"
        break
    fi
    sleep $CHECK_INTERVAL
    WAITED=$((WAITED + CHECK_INTERVAL))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "ERROR: Server did not become ready after $MAX_WAIT seconds"
    exit 1
fi

# Close any existing Chromium instances
pkill chromium-browser 2>/dev/null || true
pkill chromium 2>/dev/null || true
sleep 2

# Open Chromium in kiosk mode
echo "Launching Chromium browser..."
# Use full path to chromium-browser if available, fallback to chromium
if command -v chromium-browser &> /dev/null; then
    CHROMIUM_CMD="chromium-browser"
elif command -v chromium &> /dev/null; then
    CHROMIUM_CMD="chromium"
else
    echo "ERROR: Chromium browser not found"
    exit 1
fi

$CHROMIUM_CMD \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --autoplay-policy=no-user-gesture-required \
    "$SERVER_URL" &

# Wait a moment to check if browser started successfully
sleep 2
if ! pgrep -f "$CHROMIUM_CMD" > /dev/null; then
    echo "ERROR: Browser failed to start"
    exit 1
fi

echo "Browser launched in kiosk mode"
echo ""
echo "To close the browser:"
echo "  • Keyboard: Press Alt+F4"
echo "  • Terminal: pkill chromium-browser"
echo "  • Force:    pkill -9 chromium-browser chromium chrome"

