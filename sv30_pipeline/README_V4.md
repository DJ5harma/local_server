# SV30 v4.0 - USB Camera + HMI Integration

## 🎯 What's New in v4.0

### **MAJOR CHANGES:**

1. **USB Camera Support** - CAM1 now uses ELP-USB8MP02G-SFV(5-50)
2. **35-Minute Tests** - Duration reduced from 45 to 35 minutes
3. **HMI Integration** - Local web interface for operators
4. **Updated Snapshot Timing** - t=2, t=33 (adjusted for 35 min)

---

## 📷 Camera Configuration

### **Camera 1 - USB (NEW!)**

**Model:** ELP-USB8MP02G-SFV(5-50)  
**Type:** USB 2.0/3.0  
**Resolution:** 1920x1080  
**Frame Rate:** 30 FPS  
**Purpose:** Main video recording

**Configuration:**
```python
# In sv30config.py
CAM1_TYPE = "USB"  # Changed from "RTSP"
CAM1_USB_INDEX = 0  # Usually 0 or 1
CAM1_USB_WIDTH = 1920
CAM1_USB_HEIGHT = 1080
CAM1_USB_FPS = 30
CAM1_USB_FOURCC = "MJPG"  # MJPG recommended for speed
```

### **Camera 2 - RTSP (Unchanged)**

**Purpose:** RGB snapshots at t=2 and t=33  
**Type:** RTSP IP Camera  
**Configuration:** Same as v3.0

---

## ⏱️ Test Duration

**Changed:** 45 minutes → **35 minutes**

```python
# In sv30config.py
VIDEO_DURATION_SEC = 35 * 60  # 35 minutes

# Snapshots
CAM2_SNAPSHOT_T1_MIN = 2   # t=2 minutes  
CAM2_SNAPSHOT_T2_MIN = 33  # t=33 minutes (was t=40)
```

---

## 🖥️ HMI Integration

### **What is the HMI?**

The HMI (Human-Machine Interface) is a local web server that provides an operator interface for running SV30 tests. It runs on the Raspberry Pi and can be accessed from any web browser on the local network.

### **HMI Features:**

✅ **6-Page Workflow:**
1. Login page (password protected)
2. Home/Idle page
3. Start experiment (confirmation)
4. Progress page (35-min countdown)
5. Test completion
6. Results display (SV30 value)

✅ **Real-time Updates:**
- Live countdown timer
- Progress bar
- WebSocket or polling

✅ **Backend Integration:**
- Automatically sends data to dashboard
- Uses Socket.IO

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────┐
│           Raspberry Pi (SV30 System)          │
│                                                │
│  ┌──────────────┐      ┌──────────────────┐  │
│  │ HMI Server   │◄─────┤ SV30 Pipeline    │  │
│  │ (FastAPI)    │      │ (Processing)     │  │
│  │ :5000        │      └──────────────────┘  │
│  └──────┬───────┘                             │
│         │                                      │
│         │  ┌─────────────────────────────┐   │
│         └──┤ USB Camera (ELP)            │   │
│            │ RTSP Camera 2 (Snapshots)   │   │
│            └─────────────────────────────┘   │
└────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Web Browser     │ ← Operator accesses HMI
│  http://IP:5000  │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│  Dashboard       │ ← Results sent here
│  Backend         │
└──────────────────┘
```

---

## 🚀 Quick Start

### **Step 1: Connect USB Camera**

```bash
# Check if camera is detected
ls -l /dev/video*

# Should see: /dev/video0 (or video1, video2, etc.)

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL'); cap.release()"
```

### **Step 2: Configure Camera**

Edit `sv30config.py`:

```python
# Camera 1 - USB
CAM1_TYPE = "USB"  # IMPORTANT: Changed from RTSP!
CAM1_USB_INDEX = 0  # Try 0, 1, 2 if one doesn't work

# Test Duration
VIDEO_DURATION_SEC = 35 * 60  # 35 minutes
```

### **Step 3: Install HMI Server (Optional but Recommended)**

```bash
cd ~/Desktop/sv30/hmi_server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
nano .env
# Set: TEST_DURATION_MINUTES=35
```

### **Step 4: Run System**

**Without HMI (traditional mode):**
```bash
cd ~/Desktop/sv30
python3 main.py
```

**With HMI (operator mode):**
```bash
# Terminal 1: Start HMI
cd ~/Desktop/sv30/hmi_server
source venv/bin/activate
python run.py

# Browser: Open http://localhost:5000
# Login with password (default: thermax)
# Click "New Cycle" to start test
```

---

## 🎮 Operating Modes

### **Mode 1: CAPTURE_ONLY_MODE = True**

**Purpose:** Backup raw data only

```
1. Boot Pi
2. Capture 35-min video (USB camera)
3. Take snapshots at t=2, t=33
4. Upload to AWS
5. Shutdown
```

**Use when:** You want to collect raw data for later processing

---

### **Mode 2: CAPTURE_ONLY_MODE = False**

**Purpose:** Complete analysis

```
1. Boot Pi
2. Capture 35-min video
3. Take snapshots at t=2, t=33
4. Process frames (extract → detect → metrics)
5. Calculate SV30
6. Upload everything to AWS
7. Send results to dashboard
8. Shutdown
```

**Use when:** You need immediate results

---

## 📋 Configuration Files

### **sv30config.py - Key Settings:**

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAMERA (v4.0 - UPDATED)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAM1_TYPE = "USB"  # USB or RTSP
CAM1_USB_INDEX = 0
CAM1_USB_WIDTH = 1920
CAM1_USB_HEIGHT = 1080
CAM1_USB_FPS = 30
CAM1_USB_FOURCC = "MJPG"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DURATION (v4.0 - UPDATED)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VIDEO_DURATION_SEC = 35 * 60  # 35 minutes
CAM2_SNAPSHOT_T1_MIN = 2
CAM2_SNAPSHOT_T2_MIN = 33

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAPTURE_ONLY_MODE = False  # True = backup only
AUTO_SHUTDOWN_ENABLED = True
DEV_MODE = False  # Set True for testing

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HMI (v4.0 - NEW)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HMI_ENABLED = True
HMI_PORT = 5000
HMI_AUTO_START = True
```

### **HMI .env - Settings:**

```bash
LOGIN_PASSWORD=thermax
PORT=5000
TEST_DURATION_MINUTES=35
BACKEND_URL=https://noble-liberation-production-db43.up.railway.app
FACTORY_CODE=factory-a
```

---

## 🔧 Troubleshooting

### **USB Camera Not Found**

```bash
# List cameras
ls -l /dev/video*

# Check permissions
sudo usermod -a -G video $USER
# Logout and login

# Test with different indices
CAM1_USB_INDEX = 1  # Try 0, 1, 2

# Check camera info
v4l2-ctl --list-devices
```

### **Video Recording Fails**

```bash
# Test camera manually
python3 << 'EOF'
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"✅ Camera working: {frame.shape}")
    else:
        print("❌ Cannot read frame")
else:
    print("❌ Cannot open camera")
cap.release()
EOF
```

### **HMI Not Accessible**

```bash
# Check if HMI is running
sudo netstat -tulpn | grep 5000

# Check firewall
sudo ufw status
sudo ufw allow 5000  # If needed

# Access from browser
http://192.168.1.XXX:5000  # Replace with Pi's IP
```

### **Wrong Snapshot Timing**

```bash
# Verify config
grep "CAM2_SNAPSHOT" sv30config.py

# Should show:
# CAM2_SNAPSHOT_T1_MIN = 2
# CAM2_SNAPSHOT_T2_MIN = 33
```

---

## 📊 File Structure

```
sv30_v4_hmi_integrated/
├── main.py                     ← Main pipeline (updated for v4.0)
├── sv30config.py               ← Config (USB camera + 35 min)
├── modbus_server.py
├── requirements.txt
│
├── modules/
│   ├── video_capture.py        ← USB + RTSP support (NEW)
│   ├── system_shutdown.py
│   ├── camera_check.py
│   ├── archiver.py
│   ├── sludge_detect.py
│   ├── socketio_client.py
│   ├── aws_uploader.py
│   └── ... (other modules)
│
├── hmi_server/                 ← HMI web interface (NEW)
│   ├── src/
│   │   ├── app.py
│   │   ├── api/
│   │   ├── services/
│   │   └── ...
│   ├── static/
│   ├── run.py
│   ├── requirements.txt
│   ├── .env
│   └── sv30_ml_provider.py    ← Bridges HMI ↔ Pipeline
│
└── Documentation/
    ├── README_V4.md            ← This file
    ├── HMI_INTEGRATION_GUIDE.md ← HMI setup guide
    ├── CHANGES_V4.md           ← Changelog
    ├── README_V3.md
    ├── README.md
    └── ...
```

---

## 🎓 Usage Examples

### **Example 1: Production (with HMI)**

```bash
# 1. Start HMI server
cd ~/Desktop/sv30/hmi_server
source venv/bin/activate
python run.py

# 2. Access from browser
# http://192.168.1.100:5000 (use Pi's actual IP)

# 3. Login → Start Test → Wait 35 min → View Results
```

### **Example 2: Production (without HMI)**

```python
# sv30config.py
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = True
RUN_ONCE_PER_BOOT = True
```

```bash
# Run
python3 main.py

# System will:
# - Capture 35-min video
# - Process
# - Upload results
# - Shutdown
```

### **Example 3: Data Collection (Capture Only)**

```python
# sv30config.py
CAPTURE_ONLY_MODE = True
AUTO_SHUTDOWN_ENABLED = True
```

```bash
# Run
python3 main.py

# System will:
# - Capture 35-min video
# - Take snapshots
# - Upload RAW to AWS
# - Shutdown (no processing)
```

### **Example 4: Development/Testing**

```python
# sv30config.py
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = False  # Don't shutdown
DEV_MODE = True  # Keep all files
CAM1_TYPE = "USB"
CAM1_USB_INDEX = 0
```

```bash
# Run
python3 main.py

# Review results, debug, iterate
```

---

## 📈 Comparison: v3.0 vs v4.0

| Feature | v3.0 | v4.0 |
|---------|------|------|
| **CAM1** | RTSP | USB ✅ |
| **CAM2** | RTSP | RTSP (same) |
| **Duration** | 45 min | 35 min ✅ |
| **Snapshots** | t=2, t=40 | t=2, t=33 ✅ |
| **HMI** | ❌ No | ✅ Yes (web UI) |
| **Operator Interface** | None | ✅ Web browser |
| **Camera API** | FFmpeg (RTSP) | OpenCV (USB) ✅ |

---

## 🔄 Migration from v3.0

### **What You Need to Change:**

1. **Update sv30config.py:**
   ```python
   # Change these lines:
   CAM1_TYPE = "USB"  # Was RTSP
   VIDEO_DURATION_SEC = 35 * 60  # Was 45
   CAM2_SNAPSHOT_T2_MIN = 33  # Was 40
   ```

2. **Connect USB camera** (disconnect old RTSP CAM1)

3. **Optional: Install HMI server**

4. **Test USB camera** before running

---

## ✅ Pre-Production Checklist

- [ ] USB camera connected and detected
- [ ] Camera permissions configured
- [ ] sv30config.py updated (CAM1_TYPE, duration, snapshots)
- [ ] Test USB camera capture
- [ ] RTSP Camera 2 working for snapshots
- [ ] HMI server installed (if using)
- [ ] HMI accessible from browser
- [ ] Test complete workflow
- [ ] Dashboard receives data
- [ ] Auto-shutdown configured
- [ ] Auto-start services setup

---

## 📞 Support

**Camera Issues:**
- Check device index (0, 1, 2)
- Verify permissions (`usermod -a -G video`)
- Test with `v4l2-ctl`

**Duration Issues:**
- Verify `VIDEO_DURATION_SEC = 35 * 60`
- Check `CAM2_SNAPSHOT_T2_MIN = 33`

**HMI Issues:**
- Check logs in `hmi_server/logs/`
- Verify port 5000 not blocked
- Check `.env` configuration

---

## 📚 Documentation

1. **README_V4.md** (this file) - v4.0 overview
2. **HMI_INTEGRATION_GUIDE.md** - Complete HMI setup
3. **CHANGES_V4.md** - Detailed changelog
4. **README_V3.md** - Previous version docs
5. **QUICK_START.md** - Fast setup guide

---

**Version:** 4.0  
**Release Date:** December 2024  
**Status:** Production Ready ✅

**Key Features:**
- ✅ USB Camera support (ELP-USB8MP02G-SFV)
- ✅ 35-minute test duration
- ✅ Local HMI web interface
- ✅ Real-time operator feedback
- ✅ Dual-mode architecture maintained
- ✅ Auto-shutdown support
- ✅ Dashboard integration
