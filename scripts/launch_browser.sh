#!/bin/bash
# Reliable browser launcher for Thermax HMI
# Waits for server to be ready, then opens Chromium in kiosk mode

# Set display
export DISPLAY=:0

# Configuration
SERVER_URL="http://localhost:5000"
MAX_WAIT=60  # Maximum seconds to wait for server
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
sleep 1

# Open Chromium in kiosk mode
echo "Launching Chromium browser..."
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    "$SERVER_URL" &

echo "Browser launched in kiosk mode"
echo "Press Alt+F4 or run 'pkill chromium-browser' to close"

