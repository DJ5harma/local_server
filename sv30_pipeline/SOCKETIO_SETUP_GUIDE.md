# Socket.IO Dashboard Integration Guide

## 📋 Overview

This guide will help you integrate your SV30 system with the Thermax Dashboard Backend using Socket.IO for real-time data streaming.

**Backend URL**: https://noble-liberation-production-db43.up.railway.app

---

## 🎯 What Socket.IO Does

Socket.IO provides **real-time** bidirectional communication between your SV30 system and the web dashboard.

### Data Flow:
```
SV30 System (Raspberry Pi)
    ↓ Socket.IO
Thermax Backend (Railway)
    ↓ API/WebSocket
Web Dashboard (Browser)
```

### What Gets Sent:
- ✅ Complete test data at t=0 (start)
- ✅ Complete test data at t=30 (end)
- ✅ Test ID and timestamp
- ✅ Sludge height (mm)
- ✅ Mixture height (mm)
- ✅ Settling velocity (mm/min)
- ✅ RGB values (clear zone & sludge zone)
- ✅ Test type (morning/afternoon/evening)

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install python-socketio

```bash
cd ~/Desktop/sv30
source sv30_env/bin/activate  # If using venv

pip3 install python-socketio --break-system-packages
```

### Step 2: Enable Socket.IO in Config

Edit `sv30config.py`:

```python
# Find this line:
SOCKETIO_ENABLED = False

# Change to:
SOCKETIO_ENABLED = True
```

### Step 3: Test Connection

```bash
python3 modules/socketio_client.py
```

**Expected output:**
```
Testing Socket.IO connection...
[SOCKETIO] 🔌 Connecting to https://noble-liberation-production-db43.up.railway.app...
[SOCKETIO] ✅ Connected to https://noble-liberation-production-db43.up.railway.app
✅ Connected successfully!
[SOCKETIO] 📤 Sending t=0 data...
  - Test ID: SV30-2024-12-22-001-A
  - Test Type: afternoon
  ...
[SOCKETIO] ✅ Complete data sent successfully
```

---

## 📦 Installation Details

### Required Package:

```bash
pip3 install python-socketio --break-system-packages
```

### Verify Installation:

```bash
python3 -c "import socketio; print('python-socketio version:', socketio.__version__)"
```

**Expected**: `python-socketio version: 5.x.x`

---

## ⚙️ Configuration

### sv30config.py Settings:

```python
# =====================================
# SOCKET.IO SETTINGS
# =====================================
SOCKETIO_ENABLED = True  # Set to True to enable

# Production backend (default)
SOCKETIO_URL = "https://noble-liberation-production-db43.up.railway.app"

# For local testing (if backend is running locally)
# SOCKETIO_URL = "http://localhost:4000"
```

---

## 🧪 Testing

### Test 1: Connection Test

```bash
cd ~/Desktop/sv30
python3 modules/socketio_client.py
```

This will:
1. Connect to backend
2. Send dummy test data
3. Disconnect

### Test 2: Full Pipeline Test

```bash
# Run full pipeline with Socket.IO enabled
python3 main.py full
```

**Look for these messages:**
```
[STAGE 0.5/10] Connecting to Socket.IO dashboard...
[SOCKETIO] ✅ Connected

... (pipeline runs) ...

[SOCKETIO] Sending test results to dashboard...
[SOCKETIO] 📤 Sending t=0 data...
[SOCKETIO] 📤 Sending t=30 data...
[SOCKETIO] ✅ Results sent successfully
```

### Test 3: Check Dashboard

1. Open web dashboard in browser
2. You should see real-time data appear
3. Check that:
   - Test ID appears
   - Sludge height updates
   - RGB values display
   - Graphs update

---

## 📊 Data Format

### What SV30 System Sends:

The system sends data in this format (matching backend's `SludgeData` interface):

```json
{
  "testId": "SV30-2024-12-22-001-A",
  "timestamp": "2024-12-22T14:30:00.000Z",
  "testType": "afternoon",
  "t_min": 30,
  "sludge_height_mm": 152.7,
  "mixture_height_mm": 214.0,
  "sv30_height_mm": 152.7,
  "velocity_mm_per_min": 2.8404,
  "floc_count": 0,
  "floc_avg_size_mm": 0.0,
  "rgb_clear_zone": {
    "r": 168,
    "g": 161,
    "b": 153
  },
  "rgb_sludge_zone": {
    "r": 72,
    "g": 67,
    "b": 61
  }
}
```

### Test Type Determination:

Based on current time:
- **Morning**: 6:00 - 13:59 → Test ID ends with `-M`
- **Afternoon**: 14:00 - 21:59 → Test ID ends with `-A`
- **Evening**: 22:00 - 5:59 → Test ID ends with `-E`

### Data Sent Twice Per Test:

1. **t=0 (Start)**: Initial state with RGB values
2. **t=30 (End)**: Final state with velocity and RGB values

---

## 🔄 How It Works in Pipeline

### Integration Points:

```python
# 1. Connect at start
socketio_client = connect_socketio()

# 2. Process video and extract data
# ... (video capture, frame extraction, processing) ...

# 3. Collect results
metrics = get_final_metrics()
rgb = get_rgb_results()

# 4. Send to dashboard
send_test_results(metrics, rgb)

# 5. Disconnect at end
disconnect_socketio()
```

### What Happens:

```
1. Pipeline starts
   ↓
2. Socket.IO connects to backend
   ↓
3. Test runs (30 minutes)
   ↓
4. Results calculated
   ↓
5. Send t=0 data (initial state + RGB)
   ↓ (wait 2 seconds)
6. Send t=30 data (final state + RGB + velocity)
   ↓
7. Backend broadcasts to all dashboard clients
   ↓
8. Dashboard updates in real-time
```

---

## 🔍 Understanding the Backend

### Backend Events:

**Client → Server (SV30 sends):**
- `sludge-data` - Complete test data
- `sludge-height-update` - Height updates (optional)

**Server → Client (Dashboard receives):**
- `sludge-data-update` - Broadcast of complete data
- `sludge-height-update` - Broadcast of height updates

### Backend API:

Your backend also provides REST API:
- `GET /api/current` - Get latest data
- `GET /api/sludge-height-history` - Get historical data
- `GET /health` - Check server status

See `ThermaxBackend/API.md` for complete documentation.

---

## 🐛 Troubleshooting

### Issue 1: "Connection Failed"

**Error:**
```
[SOCKETIO] ❌ Connection error: ...
```

**Fixes:**

1. **Check internet connection**
```bash
ping noble-liberation-production-db43.up.railway.app
```

2. **Verify backend is running**
```bash
curl https://noble-liberation-production-db43.up.railway.app/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "...",
  "cache": {...}
}
```

3. **Check if python-socketio is installed**
```bash
python3 -c "import socketio"
```

4. **Try local backend** (if you have it running locally)
```python
# In sv30config.py
SOCKETIO_URL = "http://localhost:4000"
```

### Issue 2: "Module Not Found: socketio"

**Error:**
```
ModuleNotFoundError: No module named 'socketio'
```

**Fix:**
```bash
pip3 install python-socketio --break-system-packages
```

### Issue 3: Data Not Appearing in Dashboard

**Checklist:**
- [ ] Socket.IO connection successful?
- [ ] Data sent successfully (check logs)?
- [ ] Dashboard open in browser?
- [ ] Dashboard connected to backend?
- [ ] Check browser console for errors (F12)

**Debug:**
```bash
# Check what data was sent
python3 modules/socketio_client.py
# Look for "Sending t=0 data" and "Sending t=30 data" messages
```

### Issue 4: Wrong Test Type

**Problem**: Dashboard shows wrong test type (morning/afternoon/evening)

**Fix**: Test type is determined by system time
```bash
# Check system time
date

# If wrong, update:
sudo timedatectl set-timezone Asia/Kolkata
```

### Issue 5: Connection Drops During Test

**Problem**: Socket.IO disconnects during 30-minute test

**Solution**: The client has auto-reconnect enabled
```python
# In socketio_client.py
reconnection=True,
reconnection_attempts=5,
reconnection_delay=1,
```

If it keeps dropping, check network stability.

---

## 💡 Advanced Features

### Send Real-Time Height Updates (Optional)

If you want to send height updates during the test (not just at t=0 and t=30):

```python
from modules.socketio_client import get_client

client = get_client()

# During test, send height updates
for height in sludge_heights:
    client.send_height_update(height)
    time.sleep(1)  # Send every second
```

### Custom Test ID

```python
from modules.socketio_client import get_client

client = get_client()
client.test_id = "SV30-2024-12-22-CUSTOM-A"
```

### Force Test Type

```python
from modules.socketio_client import get_client

client = get_client()
client.test_type = "morning"  # Force morning type
```

---

## 📈 Production Deployment

### Systemd Service Integration

When running as a systemd service, Socket.IO works seamlessly:

```ini
[Service]
ExecStart=/usr/bin/python3 /path/to/sv30/main.py full
Environment="SOCKETIO_ENABLED=True"
```

### Auto-Restart on Failure

Socket.IO has built-in reconnection logic:
- 5 reconnection attempts
- 1 second delay between attempts
- Exponential backoff

### Monitoring

Check Socket.IO status:
```bash
# In your logs, look for:
[SOCKETIO] ✅ Connected
[SOCKETIO] ✅ Results sent successfully

# If you see:
[SOCKETIO] ❌ Connection error
# Check backend status
```

---

## 🔒 Security Notes

### HTTPS Connection

The production backend uses HTTPS:
```
https://noble-liberation-production-db43.up.railway.app
```

This provides:
- ✅ Encrypted data transmission
- ✅ Secure WebSocket connection
- ✅ Protection against MITM attacks

### No Authentication Required

Currently, the backend doesn't require authentication.

**Future Enhancement**: Add API key authentication:
```python
# In sv30config.py (future)
SOCKETIO_API_KEY = "your-secret-key"

# In socketio_client.py (future)
self.sio.connect(SOCKETIO_URL, auth={"api_key": SOCKETIO_API_KEY})
```

---

## 📝 Complete Example

### End-to-End Test:

```bash
# 1. Install dependencies
pip3 install python-socketio --break-system-packages

# 2. Enable Socket.IO
nano sv30config.py
# Set SOCKETIO_ENABLED = True

# 3. Test connection
python3 modules/socketio_client.py

# 4. Run full pipeline
python3 main.py full

# 5. Check dashboard
# Open https://your-dashboard-url.com in browser
# Verify data appears in real-time
```

---

## ✅ Integration Checklist

Before going to production:

**Installation:**
- [ ] python-socketio installed
- [ ] Connection test passes
- [ ] Backend is accessible

**Configuration:**
- [ ] SOCKETIO_ENABLED = True
- [ ] SOCKETIO_URL is correct
- [ ] System time is correct (for test type)

**Testing:**
- [ ] Connection test successful
- [ ] Full pipeline test successful
- [ ] Data appears in dashboard
- [ ] All fields populate correctly
- [ ] RGB values display
- [ ] Test type is correct

**Production:**
- [ ] Runs as systemd service
- [ ] Auto-restarts on failure
- [ ] Logs are monitored
- [ ] Dashboard accessible to users

---

## 🎓 Understanding the Flow

### Complete Data Flow:

```
SV30 Test (30 minutes)
  ↓
Results Generated:
  - sv30_metrics.json (SV30%, velocity)
  - rgb_values.json (RGB top/bottom)
  ↓
Python Socket.IO Client:
  - Converts to backend format
  - Generates test ID
  - Determines test type (time-based)
  ↓
Socket.IO Connection:
  - Sends t=0 data (initial + RGB)
  - Waits 2 seconds
  - Sends t=30 data (final + RGB + velocity)
  ↓
Thermax Backend:
  - Receives data
  - Stores in cache
  - Broadcasts to all connected clients
  ↓
Web Dashboard:
  - Receives real-time updates
  - Updates UI instantly
  - Shows graphs and metrics
```

---

## 📞 Need Help?

### Logs to Check:

```bash
# SV30 system logs
cat logs/sv30_pipeline.log | grep SOCKETIO

# Backend logs
# Check Railway dashboard for backend logs
```

### Common Log Messages:

**Success:**
```
[SOCKETIO] ✅ Connected
[SOCKETIO] ✅ Results sent successfully
```

**Warnings:**
```
[SOCKETIO] ⚠️  Not connected, skipping send
[SOCKETIO] ⚠️  Connection failed, continuing without dashboard
```

**Errors:**
```
[SOCKETIO] ❌ Connection error: ...
[SOCKETIO] ❌ Failed to send data: ...
```

---

## 🚀 You're Ready!

Your SV30 system can now stream real-time data to the dashboard!

**Quick Command:**
```bash
python3 main.py full
```

Watch the data flow to your dashboard in real-time! 📊✨
