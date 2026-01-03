# Raspberry Pi Auto-Start Setup Guide

This guide will help you set up the Thermax HMI server to automatically start when your Raspberry Pi boots up, and automatically open Chromium browser to `http://localhost:5000`.

## Prerequisites

1. **Raspberry Pi OS** (or any Debian-based Linux distribution)
2. **Python 3.8+** installed
3. **Virtual environment** created and dependencies installed
4. **Chromium browser** installed (usually pre-installed on Raspberry Pi OS)

## Step 1: Install Chromium (if not already installed)

```bash
sudo apt update
sudo apt install -y chromium-browser
```

## Step 2: Install Network Tools (for port checking)

```bash
sudo apt install -y netcat-openbsd
```

## Step 3: Navigate to Project Directory

```bash
cd ~/ThermaxDashboard/local_server
# Or wherever your project is located
```

## Step 4: Ensure Virtual Environment is Set Up

If you haven't already:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 5: Run the Setup Script

The setup script will:
- Make all scripts executable
- Update service files with correct paths
- Install systemd services
- Enable auto-start on boot

```bash
cd scripts
chmod +x setup_autostart.sh
./setup_autostart.sh
```

### Alternative: Desktop Autostart (if systemd browser service doesn't work)

If the browser doesn't open automatically with systemd, you can use the desktop autostart method:

```bash
# Copy desktop file to autostart directory
mkdir -p ~/.config/autostart
cp scripts/thermax-browser.desktop ~/.config/autostart/
```

This will open the browser when the desktop environment starts.

## Step 6: Test the Services

Before rebooting, test that everything works:

```bash
# Start the server service
sudo systemctl start thermax-hmi.service

# Check if it's running
sudo systemctl status thermax-hmi.service

# Start the browser service (if server is running)
sudo systemctl start thermax-browser.service

# Check browser service status
sudo systemctl status thermax-browser.service
```

## Step 7: Reboot and Verify

```bash
sudo reboot
```

After reboot, the server should start automatically and Chromium should open to `http://localhost:5000`.

## Managing the Services

### Check Service Status

```bash
# Check server status
sudo systemctl status thermax-hmi.service

# Check browser service status
sudo systemctl status thermax-browser.service
```

### View Logs

```bash
# View server logs
sudo journalctl -u thermax-hmi.service -f

# View browser service logs
sudo journalctl -u thermax-browser.service -f

# View all logs together
sudo journalctl -u thermax-hmi.service -u thermax-browser.service -f
```

### Start/Stop Services Manually

```bash
# Start server
sudo systemctl start thermax-hmi.service

# Stop server
sudo systemctl stop thermax-hmi.service

# Restart server
sudo systemctl restart thermax-hmi.service

# Start browser
sudo systemctl start thermax-browser.service

# Stop browser
sudo systemctl stop thermax-browser.service
```

### Disable Auto-Start

If you want to disable auto-start:

```bash
sudo systemctl disable thermax-hmi.service
sudo systemctl disable thermax-browser.service
```

To re-enable:

```bash
sudo systemctl enable thermax-hmi.service
sudo systemctl enable thermax-browser.service
```

## Troubleshooting

### Server Not Starting

1. **Check if port 5000 is already in use:**
   ```bash
   sudo netstat -tulpn | grep 5000
   ```

2. **Check service logs:**
   ```bash
   sudo journalctl -u thermax-hmi.service -n 50
   ```

3. **Verify virtual environment:**
   ```bash
   source venv/bin/activate
   python run.py
   ```

### Browser Not Opening

1. **Check if server is running:**
   ```bash
   curl http://localhost:5000
   ```

2. **Check browser service logs:**
   ```bash
   sudo journalctl -u thermax-browser.service -n 50
   ```

3. **Manually test browser script:**
   ```bash
   ./scripts/open_browser.sh
   ```

### Service Fails to Start

1. **Check file permissions:**
   ```bash
   ls -la scripts/
   chmod +x scripts/*.sh
   ```

2. **Verify paths in service files:**
   ```bash
   cat /etc/systemd/system/thermax-hmi.service
   ```

3. **Reload systemd:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart thermax-hmi.service
   ```

## Customization

### Change Browser Mode

Edit `scripts/open_browser.sh`:

- **Kiosk mode (fullscreen):** `chromium-browser --kiosk http://localhost:5000 &`
- **Normal window:** `chromium-browser http://localhost:5000 &`
- **With specific window size:** `chromium-browser --window-size=1920,1080 http://localhost:5000 &`

### Change Server Port

Edit `.env` file in the project root:
```
PORT=5000
```

Then restart the service:
```bash
sudo systemctl restart thermax-hmi.service
```

### Change Startup Delay

Edit `scripts/open_browser.sh` to adjust the wait time before opening the browser.

## Files Created

- `scripts/start_server.sh` - Script to start the server
- `scripts/open_browser.sh` - Script to open Chromium browser
- `scripts/thermax-hmi.service` - Systemd service for the server
- `scripts/thermax-browser.service` - Systemd service for the browser
- `scripts/setup_autostart.sh` - Setup script
- `/etc/systemd/system/thermax-hmi.service` - Installed service file
- `/etc/systemd/system/thermax-browser.service` - Installed service file

## Notes

- The server service runs as the user who ran the setup script (usually `pi`)
- The browser service requires a graphical session (runs after `graphical.target`)
- The server will automatically restart if it crashes (configured with `Restart=always`)
- Logs are available via `journalctl` for debugging

