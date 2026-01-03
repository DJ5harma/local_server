#!/bin/bash
# Script to close Chromium browser (all variants)
# Useful when browser is stuck or not responding

echo "Closing Chromium browser..."

# Method 1: Simple kill (try this first)
pkill chromium-browser 2>/dev/null
sleep 1

# Method 2: Force kill if still running
if pgrep chromium-browser > /dev/null || pgrep chromium > /dev/null || pgrep chrome > /dev/null; then
    echo "Force killing Chromium processes..."
    pkill -9 chromium-browser 2>/dev/null
    pkill -9 chromium 2>/dev/null
    pkill -9 chrome 2>/dev/null
    killall -9 chromium-browser 2>/dev/null
    killall -9 chromium 2>/dev/null
    killall -9 chrome 2>/dev/null
    sleep 1
fi

# Verify all processes are closed
if pgrep -i chromium > /dev/null || pgrep -i chrome > /dev/null; then
    echo "Warning: Some Chromium processes may still be running"
    echo "Remaining processes:"
    pgrep -i chromium chrome
else
    echo "✓ All Chromium processes closed successfully"
fi

