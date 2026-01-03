#!/bin/bash
# Script to open Chromium browser after server starts
# Waits for server to be ready, then opens browser

# Set display if not already set
export DISPLAY=${DISPLAY:-:0}

# Wait for server to be ready (check if port 5000 is listening)
echo "Waiting for server to start..."
for i in {1..30}; do
    if nc -z localhost 5000 2>/dev/null; then
        echo "Server is ready!"
        break
    fi
    sleep 1
done

# Additional small delay to ensure server is fully ready
sleep 2

# Open Chromium browser in kiosk mode (fullscreen)
# Remove --kiosk if you want a normal browser window
chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5000 &

# Alternative: Open in normal window mode (uncomment if preferred)
# chromium-browser http://localhost:5000 &

