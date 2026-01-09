#!/bin/bash
# Script to check which browser is installed and running on the system

echo "=========================================="
echo "Browser Detection Script"
echo "=========================================="
echo ""

echo "Checking installed browsers..."
echo ""

# Check for chromium-browser
if command -v chromium-browser &> /dev/null; then
    CHROMIUM_BROWSER_PATH=$(which chromium-browser)
    CHROMIUM_BROWSER_VERSION=$(chromium-browser --version 2>&1 | head -n 1)
    echo "✓ chromium-browser found:"
    echo "  Path: $CHROMIUM_BROWSER_PATH"
    echo "  Version: $CHROMIUM_BROWSER_VERSION"
else
    echo "✗ chromium-browser NOT found"
fi
echo ""

# Check for chromium
if command -v chromium &> /dev/null; then
    CHROMIUM_PATH=$(which chromium)
    CHROMIUM_VERSION=$(chromium --version 2>&1 | head -n 1)
    echo "✓ chromium found:"
    echo "  Path: $CHROMIUM_PATH"
    echo "  Version: $CHROMIUM_VERSION"
else
    echo "✗ chromium NOT found"
fi
echo ""

# Check for google-chrome
if command -v google-chrome &> /dev/null; then
    GOOGLE_CHROME_PATH=$(which google-chrome)
    GOOGLE_CHROME_VERSION=$(google-chrome --version 2>&1 | head -n 1)
    echo "✓ google-chrome found:"
    echo "  Path: $GOOGLE_CHROME_PATH"
    echo "  Version: $GOOGLE_CHROME_VERSION"
else
    echo "✗ google-chrome NOT found"
fi
echo ""

# Check for chrome
if command -v chrome &> /dev/null; then
    CHROME_PATH=$(which chrome)
    CHROME_VERSION=$(chrome --version 2>&1 | head -n 1)
    echo "✓ chrome found:"
    echo "  Path: $CHROME_PATH"
    echo "  Version: $CHROME_VERSION"
else
    echo "✗ chrome NOT found"
fi
echo ""

echo "=========================================="
echo "Currently Running Browser Processes:"
echo "=========================================="
echo ""

# Check for running processes
RUNNING_BROWSERS=0

if pgrep -f "chromium-browser" > /dev/null; then
    echo "✓ chromium-browser is RUNNING:"
    ps aux | grep -E "[c]hromium-browser" | head -n 3
    RUNNING_BROWSERS=$((RUNNING_BROWSERS + 1))
    echo ""
fi

if pgrep -f "chromium" > /dev/null && ! pgrep -f "chromium-browser" > /dev/null; then
    echo "✓ chromium is RUNNING:"
    ps aux | grep -E "[c]hromium[^-]" | head -n 3
    RUNNING_BROWSERS=$((RUNNING_BROWSERS + 1))
    echo ""
fi

if pgrep -f "google-chrome" > /dev/null; then
    echo "✓ google-chrome is RUNNING:"
    ps aux | grep -E "[g]oogle-chrome" | head -n 3
    RUNNING_BROWSERS=$((RUNNING_BROWSERS + 1))
    echo ""
fi

if pgrep -f "chrome" > /dev/null && ! pgrep -f "google-chrome\|chromium" > /dev/null; then
    echo "✓ chrome is RUNNING:"
    ps aux | grep -E "[c]hrome[^-]" | head -n 3
    RUNNING_BROWSERS=$((RUNNING_BROWSERS + 3))
    echo ""
fi

if [ $RUNNING_BROWSERS -eq 0 ]; then
    echo "✗ No browser processes are currently running"
    echo ""
fi

echo "=========================================="
echo "Recommendation:"
echo "=========================================="
echo ""

# Determine which browser to use (priority order)
if command -v chromium-browser &> /dev/null; then
    echo "RECOMMENDED: Use 'chromium-browser'"
    echo "  Command: chromium-browser"
    echo "  Full path: $(which chromium-browser)"
elif command -v chromium &> /dev/null; then
    echo "RECOMMENDED: Use 'chromium'"
    echo "  Command: chromium"
    echo "  Full path: $(which chromium)"
elif command -v google-chrome &> /dev/null; then
    echo "RECOMMENDED: Use 'google-chrome'"
    echo "  Command: google-chrome"
    echo "  Full path: $(which google-chrome)"
elif command -v chrome &> /dev/null; then
    echo "RECOMMENDED: Use 'chrome'"
    echo "  Command: chrome"
    echo "  Full path: $(which chrome)"
else
    echo "ERROR: No browser found!"
    echo "Please install a browser:"
    echo "  sudo apt update"
    echo "  sudo apt install -y chromium-browser"
fi

echo ""
echo "=========================================="
echo "To test browser launch:"
echo "=========================================="
if command -v chromium-browser &> /dev/null; then
    echo "chromium-browser --version"
elif command -v chromium &> /dev/null; then
    echo "chromium --version"
fi
echo ""
