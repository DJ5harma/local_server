#!/bin/bash
# Setup script for auto-starting Thermax HMI on Raspberry Pi boot
# Run this script once to configure auto-start

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Thermax HMI auto-start on Raspberry Pi...${NC}"

# Get the project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Project directory: $PROJECT_DIR${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do not run this script as root${NC}"
   exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${RED}Virtual environment not found at $PROJECT_DIR/venv${NC}"
    echo -e "${YELLOW}Please create the virtual environment first:${NC}"
    echo "  cd $PROJECT_DIR"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Make scripts executable
chmod +x "$PROJECT_DIR/scripts/start_server.sh"
chmod +x "$PROJECT_DIR/scripts/open_browser.sh"
chmod +x "$PROJECT_DIR/scripts/setup_autostart.sh"

# Update service files with correct paths
USER_HOME=$(eval echo ~$USER)
PROJECT_DIR_ESCAPED=$(echo "$PROJECT_DIR" | sed 's/\//\\\//g')

# Update themax-hmi.service
sed -i "s|/home/pi/ThermaxDashboard/local_server|$PROJECT_DIR|g" "$PROJECT_DIR/scripts/thermax-hmi.service"
sed -i "s|User=pi|User=$USER|g" "$PROJECT_DIR/scripts/thermax-hmi.service"

# Update themax-browser.service
sed -i "s|/home/pi/ThermaxDashboard/local_server|$PROJECT_DIR|g" "$PROJECT_DIR/scripts/thermax-browser.service"
sed -i "s|User=pi|User=$USER|g" "$PROJECT_DIR/scripts/thermax-browser.service"

echo -e "${GREEN}Service files updated with correct paths${NC}"

# Copy service files to systemd directory
echo -e "${YELLOW}Installing systemd services...${NC}"
sudo cp "$PROJECT_DIR/scripts/thermax-hmi.service" /etc/systemd/system/
sudo cp "$PROJECT_DIR/scripts/thermax-browser.service" /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
echo -e "${YELLOW}Enabling services...${NC}"
sudo systemctl enable thermax-hmi.service
sudo systemctl enable thermax-browser.service

echo -e "${GREEN}✓ Services installed and enabled${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Test the services:"
echo "     sudo systemctl start thermax-hmi.service"
echo "     sudo systemctl start thermax-browser.service"
echo ""
echo "  2. Check service status:"
echo "     sudo systemctl status thermax-hmi.service"
echo "     sudo systemctl status thermax-browser.service"
echo ""
echo "  3. View logs:"
echo "     sudo journalctl -u thermax-hmi.service -f"
echo ""
echo "  4. To disable auto-start:"
echo "     sudo systemctl disable thermax-hmi.service"
echo "     sudo systemctl disable thermax-browser.service"
echo ""
echo -e "${GREEN}Setup complete! The services will start automatically on next boot.${NC}"

