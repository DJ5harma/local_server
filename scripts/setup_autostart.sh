#!/bin/bash
# Setup script for auto-starting Thermax HMI on Raspberry Pi
# This script configures the server and browser to start automatically on boot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Thermax HMI Auto-Start Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CURRENT_USER=$(whoami)

echo -e "${BLUE}Project directory:${NC} $PROJECT_DIR"
echo -e "${BLUE}Current user:${NC} $CURRENT_USER"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}ERROR: Please do not run this script as root${NC}"
   echo -e "${YELLOW}Run as your regular user (usually 'pi')${NC}"
   exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo -e "${YELLOW}Please create the virtual environment first:${NC}"
    echo "  cd $PROJECT_DIR"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if Python is available in venv
if [ ! -f "$PROJECT_DIR/venv/bin/python" ]; then
    echo -e "${RED}ERROR: Python not found in virtual environment${NC}"
    exit 1
fi

# Check if run.py exists
if [ ! -f "$PROJECT_DIR/run.py" ]; then
    echo -e "${RED}ERROR: run.py not found in project directory${NC}"
    exit 1
fi

# Check/create .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file template...${NC}"
    cat > "$PROJECT_DIR/.env" << EOF
# Server Configuration
PORT=5000
HOST=0.0.0.0

# Test Configuration
TEST_DURATION_MINUTES=31

# Backend Configuration
BACKEND_URL=http://localhost:4000
FACTORY_CODE=factory-a
EOF
    echo -e "${GREEN}✓ Created .env file template${NC}"
    echo -e "${YELLOW}  Please edit $PROJECT_DIR/.env if you need to change settings${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Ensure required directories exist
echo -e "${YELLOW}Checking required directories...${NC}"
mkdir -p "$PROJECT_DIR/results"
mkdir -p "$PROJECT_DIR/static"
if [ -d "$PROJECT_DIR/results" ] && [ -d "$PROJECT_DIR/static" ]; then
    echo -e "${GREEN}✓ Required directories exist${NC}"
else
    echo -e "${RED}✗ Failed to create required directories${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 1: Making scripts executable...${NC}"
chmod +x "$PROJECT_DIR/scripts/launch_browser.sh"
chmod +x "$PROJECT_DIR/scripts/close_browser.sh"
chmod +x "$PROJECT_DIR/scripts/setup_autostart.sh"
chmod +x "$PROJECT_DIR/scripts/start_hmi.sh"
chmod +x "$PROJECT_DIR/scripts/stop_hmi.sh"
chmod +x "$PROJECT_DIR/scripts/check_browser.sh"
echo -e "${GREEN}✓ Scripts are executable${NC}"
echo ""

# Update service files with correct paths
echo -e "${YELLOW}Step 2: Updating service files with correct paths...${NC}"

# Create a temporary copy of the service file with correct paths
TEMP_SERVICE=$(mktemp)
sed "s|/home/pi/ThermaxDashboard/local_server|$PROJECT_DIR|g; s|User=pi|User=$CURRENT_USER|g" \
    "$PROJECT_DIR/scripts/thermax-hmi.service" > "$TEMP_SERVICE"

# Verify the temp service file was created correctly
if [ ! -s "$TEMP_SERVICE" ]; then
    echo -e "${RED}ERROR: Failed to create service file${NC}"
    exit 1
fi

# Update desktop file with correct path
TEMP_DESKTOP=$(mktemp)
sed "s|/home/pi/ThermaxDashboard/local_server|$PROJECT_DIR|g" \
    "$PROJECT_DIR/scripts/thermax-browser.desktop" > "$TEMP_DESKTOP"

# Verify the temp desktop file was created correctly
if [ ! -s "$TEMP_DESKTOP" ]; then
    echo -e "${RED}ERROR: Failed to create desktop file${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Service files updated${NC}"
echo -e "${BLUE}  Project directory: $PROJECT_DIR${NC}"
echo -e "${BLUE}  User: $CURRENT_USER${NC}"
echo ""

# Install systemd service for the server
echo -e "${YELLOW}Step 3: Installing systemd service for server...${NC}"
sudo cp "$TEMP_SERVICE" /etc/systemd/system/thermax-hmi.service
sudo systemctl daemon-reload
sudo systemctl enable thermax-hmi.service

# Try to start the service to verify it works
echo -e "${BLUE}Starting service to verify configuration...${NC}"
if sudo systemctl start thermax-hmi.service; then
    sleep 3
    if sudo systemctl is-active --quiet thermax-hmi.service; then
        echo -e "${GREEN}✓ Server service installed, enabled, and started successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Service installed but failed to start${NC}"
        echo -e "${YELLOW}  Check logs with: sudo journalctl -u thermax-hmi.service -n 50${NC}"
    fi
else
    echo -e "${RED}✗ Failed to start service${NC}"
    echo -e "${YELLOW}  Check logs with: sudo journalctl -u thermax-hmi.service -n 50${NC}"
fi
echo ""

# Install desktop autostart for browser
echo -e "${YELLOW}Step 4: Installing desktop autostart for browser...${NC}"
mkdir -p "$HOME/.config/autostart"
cp "$TEMP_DESKTOP" "$HOME/.config/autostart/thermax-browser.desktop"
echo -e "${GREEN}✓ Browser autostart installed${NC}"
echo ""

# Clean up temp files
rm -f "$TEMP_SERVICE" "$TEMP_DESKTOP"

# Check if required tools are installed
echo -e "${YELLOW}Step 5: Checking dependencies...${NC}"
MISSING_DEPS=0

if ! command -v chromium-browser &> /dev/null; then
    echo -e "${RED}  ✗ chromium-browser not found${NC}"
    MISSING_DEPS=1
else
    echo -e "${GREEN}  ✓ chromium-browser found${NC}"
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}  ✗ curl not found${NC}"
    MISSING_DEPS=1
else
    echo -e "${GREEN}  ✓ curl found${NC}"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    sudo apt update
    sudo apt install -y chromium-browser curl x11-utils
fi

# Verify X server is available (for browser launch)
echo -e "${YELLOW}Step 6: Verifying X server availability...${NC}"
if command -v xset &> /dev/null; then
    if xset q &>/dev/null 2>&1 || [ -n "$DISPLAY" ]; then
        echo -e "${GREEN}✓ X server is available${NC}"
    else
        echo -e "${YELLOW}⚠ X server not currently available (this is OK if not logged in yet)${NC}"
        echo -e "${YELLOW}  Browser will wait for X server on boot${NC}"
    fi
else
    echo -e "${YELLOW}⚠ xset not found, installing x11-utils...${NC}"
    sudo apt install -y x11-utils
fi
echo ""

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}What was configured:${NC}"
echo "  • Server service: /etc/systemd/system/thermax-hmi.service"
echo "  • Browser autostart: $HOME/.config/autostart/thermax-browser.desktop"
echo "  • Service will start automatically on boot"
echo "  • Browser will launch 10 seconds after login"
echo ""
echo -e "${YELLOW}Verification:${NC}"
echo "  1. Check service status:"
echo "     sudo systemctl status thermax-hmi.service"
echo ""
echo "  2. Check service logs:"
echo "     sudo journalctl -u thermax-hmi.service -n 50"
echo ""
echo "  3. Test browser launch manually:"
echo "     $PROJECT_DIR/scripts/launch_browser.sh"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  • Reboot to test auto-start:"
echo "    sudo reboot"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  • Start server:     sudo systemctl start thermax-hmi.service"
echo "  • Stop server:      sudo systemctl stop thermax-hmi.service"
echo "  • Restart server:   sudo systemctl restart thermax-hmi.service"
echo "  • View logs:        sudo journalctl -u thermax-hmi.service -f"
echo "  • Close browser:    pkill chromium-browser"
echo "  • Disable auto-start: sudo systemctl disable thermax-hmi.service"
echo ""
echo -e "${GREEN}The system will automatically start on next boot!${NC}"
