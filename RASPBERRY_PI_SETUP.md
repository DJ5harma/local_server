HI
# Raspberry Pi Auto-Start Setup Guide

This guide will help you set up the Thermax HMI server to automatically start when your Raspberry Pi boots up, and automatically open Chromium browser to `http://localhost:5000` in kiosk mode.

## Prerequisites

1. **Raspberry Pi OS** (or any Debian-based Linux distribution)
2. **Python 3.8+** installed
3. **Virtual environment** created and dependencies installed
4. **Chromium browser** installed (usually pre-installed on Raspberry Pi OS)

## Quick Setup

### Step 1: Navigate to Project Directory

```bash
cd ~/ThermaxDashboard/local_server
# Or wherever your project is located
```

### Step 2: Ensure Virtual Environment is Set Up

If you haven't already:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Run the Setup Script

The setup script will automatically:
- Install and configure the server systemd service
- Install desktop autostart for the browser
- Check and install missing dependencies
- Enable auto-start on boot

```bash
cd scripts
chmod +x setup_autostart.sh
./setup_autostart.sh
```

That's it! The setup script handles everything automatically.

## How It Works

1. **Server Service**: Starts automatically on boot via systemd (`thermax-hmi.service`)
   - Runs in the background
   - Automatically restarts if it crashes
   - Starts before the browser

2. **Browser Autostart**: Opens automatically when you log in to the desktop
   - Waits for the server to be ready (checks every 2 seconds)
   - Opens Chromium in kiosk mode (fullscreen)
   - Uses desktop autostart (more reliable than systemd for GUI apps)

## Testing

Before rebooting, test that everything works:

```bash
# Start the server service
sudo systemctl start thermax-hmi.service

# Check if it's running
sudo systemctl status thermax-hmi.service

# Wait a few seconds, then manually test the browser
./scripts/launch_browser.sh
```

## Reboot and Verify

```bash
sudo reboot
```

After reboot:
1. The server will start automatically in the background
2. When you log in to the desktop, the browser will automatically open in kiosk mode
3. The browser will wait for the server to be ready before opening

## Managing the Services

### Check Service Status

```bash
# Check server status
sudo systemctl status thermax-hmi.service
```

### View Logs

```bash
# View server logs (live)
sudo journalctl -u thermax-hmi.service -f

# View last 50 lines
sudo journalctl -u thermax-hmi.service -n 50
```

### Start/Stop Services Manually

```bash
# Start server
sudo systemctl start thermax-hmi.service

# Stop server
sudo systemctl stop thermax-hmi.service

# Restart server
sudo systemctl restart thermax-hmi.service

# Close browser (from SSH/terminal)
pkill chromium-browser

# Launch browser manually
./scripts/launch_browser.sh
```

### Disable Auto-Start

If you want to disable auto-start:

```bash
# Disable server auto-start
sudo systemctl disable thermax-hmi.service

# Disable browser auto-start
rm ~/.config/autostart/thermax-browser.desktop
```

To re-enable:

```bash
# Re-enable server
sudo systemctl enable thermax-hmi.service

# Re-enable browser (re-run setup script)
./scripts/setup_autostart.sh
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
   sudo systemctl status thermax-hmi.service
   ```

2. **Check if autostart file exists:**
   ```bash
   ls -la ~/.config/autostart/thermax-browser.desktop
   ```

3. **Manually test browser script:**
   ```bash
   ./scripts/launch_browser.sh
   ```

4. **Check browser script logs:**
   ```bash
   # Run with output visible
   DISPLAY=:0 ./scripts/launch_browser.sh
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

Edit `scripts/launch_browser.sh`:

- **Kiosk mode (fullscreen):** Already configured (default)
- **Normal window:** Remove `--kiosk` flag from the chromium-browser command
- **With specific window size:** Add `--window-size=1920,1080` flag

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

- `scripts/launch_browser.sh` - Script to open Chromium browser (waits for server)
- `scripts/thermax-hmi.service` - Systemd service template for the server
- `scripts/thermax-browser.desktop` - Desktop autostart template for the browser
- `scripts/setup_autostart.sh` - Setup script
- `/etc/systemd/system/thermax-hmi.service` - Installed server service
- `~/.config/autostart/thermax-browser.desktop` - Installed browser autostart

## Notes

- The server service runs as the user who ran the setup script (usually `pi`)
- The browser uses desktop autostart, so it only opens when you log in to the desktop
- The server will automatically restart if it crashes (configured with `Restart=always`)
- The browser script waits up to 60 seconds for the server to be ready
- Logs are available via `journalctl` for debugging
- To close the browser in kiosk mode: Press `Alt+F4` or run `pkill chromium-browser` from SSH

