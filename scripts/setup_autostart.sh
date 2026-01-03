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

echo -e "${YELLOW}Step 1: Making scripts executable...${NC}"
chmod +x "$PROJECT_DIR/scripts/launch_browser.sh"
chmod +x "$PROJECT_DIR/scripts/setup_autostart.sh"
echo -e "${GREEN}✓ Scripts are executable${NC}"
echo ""

# Update service files with correct paths
echo -e "${YELLOW}Step 2: Updating service files with correct paths...${NC}"

# Create a temporary copy of the service file
TEMP_SERVICE=$(mktemp)
sed "s|/home/pi/ThermaxDashboard/local_server|$PROJECT_DIR|g; s|User=pi|User=$CURRENT_USER|g" \
    "$PROJECT_DIR/scripts/thermax-hmi.service" > "$TEMP_SERVICE"

# Update desktop file with correct path
TEMP_DESKTOP=$(mktemp)
sed "s|/home/pi/ThermaxDashboard/local_server|$PROJECT_DIR|g" \
    "$PROJECT_DIR/scripts/thermax-browser.desktop" > "$TEMP_DESKTOP"

echo -e "${GREEN}✓ Service files updated${NC}"
echo ""

# Install systemd service for the server
echo -e "${YELLOW}Step 3: Installing systemd service for server...${NC}"
sudo cp "$TEMP_SERVICE" /etc/systemd/system/thermax-hmi.service
sudo systemctl daemon-reload
sudo systemctl enable thermax-hmi.service
echo -e "${GREEN}✓ Server service installed and enabled${NC}"
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
    sudo apt install -y chromium-browser curl
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}What was configured:${NC}"
echo "  • Server service: /etc/systemd/system/thermax-hmi.service"
echo "  • Browser autostart: $HOME/.config/autostart/thermax-browser.desktop"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Test the server:"
echo "     sudo systemctl start thermax-hmi.service"
echo "     sudo systemctl status thermax-hmi.service"
echo ""
echo "  2. Test the browser (after server is running):"
echo "     $PROJECT_DIR/scripts/launch_browser.sh"
echo ""
echo "  3. View server logs:"
echo "     sudo journalctl -u thermax-hmi.service -f"
echo ""
echo "  4. Reboot to test auto-start:"
echo "     sudo reboot"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  • Stop server:     sudo systemctl stop thermax-hmi.service"
echo "  • Restart server:  sudo systemctl restart thermax-hmi.service"
echo "  • Close browser:   pkill chromium-browser"
echo "  • Disable auto-start: sudo systemctl disable thermax-hmi.service"
echo ""
echo -e "${GREEN}The system will automatically start on next boot!${NC}"
