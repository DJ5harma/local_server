# SV30 v4.0 - HMI Integration Guide

## 🎯 Overview

Version 4.0 integrates a local HMI (Human-Machine Interface) server that provides a web-based operator interface for running SV30 tests. The HMI runs alongside the SV30 processing pipeline on the Raspberry Pi.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Raspberry Pi                          │
│                                                          │
│  ┌──────────────────┐         ┌────────────────────┐   │
│  │   HMI Server     │         │  SV30 Pipeline     │   │
│  │   (FastAPI)      │◄────────┤  (Python)          │   │
│  │   Port 5000      │         │                    │   │
│  └─────────┬────────┘         └────────────────────┘   │
│            │                                            │
│            ▼                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │  USB Camera (ELP-USB8MP02G-SFV)                 │   │
│  │  RTSP Camera 2 (RGB Snapshots)                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
          │
          ▼
  ┌────────────────┐
  │  Web Browser   │
  │  (Operator UI) │
  └────────────────┘
          │
          ▼
  ┌────────────────┐
  │  Dashboard     │
  │  Backend       │
  └────────────────┘
```

---

## 📦 What's New in v4.0

### **1. Camera Changes**
- ✅ CAM1: RTSP → USB (ELP-USB8MP02G-SFV(5-50))
- ✅ Support for both USB and RTSP cameras
- ✅ Configurable camera type via `CAM1_TYPE`

### **2. Test Duration**
- ✅ 45 minutes → **35 minutes**
- ✅ Snapshots: t=2 min, t=33 min (updated from t=2, t=40)

### **3. HMI Server**
- ✅ Local web interface for operators
- ✅ 6-page workflow: Login → Home → Start → Progress → Complete → Results
- ✅ Real-time progress updates
- ✅ Automatic backend integration

---

## 🚀 Installation

### **Step 1: Install HMI Server**

The HMI server code should be in the `hmi_server/` directory. If not, obtain it from your web developer.

```bash
cd ~/Desktop/sv30/hmi_server

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Configure HMI**

Create `.env` file in `hmi_server/` directory:

```bash
cd ~/Desktop/sv30/hmi_server
nano .env
```

Add these settings:

```bash
# HMI Configuration
LOGIN_PASSWORD=thermax
PORT=5000
TEST_DURATION_MINUTES=35

# Backend Integration
BACKEND_URL=https://noble-liberation-production-db43.up.railway.app
FACTORY_CODE=factory-a
```

### **Step 3: Configure SV30 System**

Edit `sv30config.py`:

```python
# Camera Settings
CAM1_TYPE = "USB"  # Use USB camera
CAM1_USB_INDEX = 0  # Usually 0 or 1
CAM1_USB_WIDTH = 1920
CAM1_USB_HEIGHT = 1080
CAM1_USB_FPS = 30

# Test Duration
VIDEO_DURATION_SEC = 35 * 60  # 35 minutes

# HMI Settings
HMI_ENABLED = True
HMI_PORT = 5000
HMI_AUTO_START = True
```

---

## 🎮 Usage

### **Option 1: Manual Start (for testing)**

**Terminal 1 - Start HMI Server:**
```bash
cd ~/Desktop/sv30/hmi_server
source venv/bin/activate
python run.py
```

**Terminal 2 - Monitor SV30 System:**
```bash
cd ~/Desktop/sv30
# System will be triggered by HMI
```

**Open Web Browser:**
```
http://localhost:5000
# or from another device:
http://192.168.1.XXX:5000
```

---

### **Option 2: Auto-Start (Production)**

Create systemd service for HMI:

```bash
sudo nano /etc/systemd/system/sv30-hmi.service
```

Add:

```ini
[Unit]
Description=SV30 HMI Server
After=network.target

[Service]
Type=simple
User=recomputer
WorkingDirectory=/home/recomputer/Desktop/sv30/hmi_server
Environment="PATH=/home/recomputer/Desktop/sv30/hmi_server/venv/bin"
ExecStart=/home/recomputer/Desktop/sv30/hmi_server/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable sv30-hmi.service
sudo systemctl start sv30-hmi.service
sudo systemctl status sv30-hmi.service
```

---

## 🔧 Integration Points

### **1. ML Data Provider**

The HMI calls `sv30_ml_provider.py` which bridges to the SV30 pipeline:

```python
# In hmi_server/src/app.py (you'll need to modify):
from sv30_ml_provider import SV30MLProvider

# Replace DummyDataProvider with:
data_provider = SV30MLProvider()
```

### **2. Test Workflow**

```
1. Operator logs in to HMI
2. Operator clicks "Start Test"
3. HMI calls SV30MLProvider.generate_t0_data()
4. SV30 starts video capture (35 minutes)
5. HMI shows progress bar
6. After 35 minutes, HMI calls SV30MLProvider.generate_t30_data()
7. SV30 processes video → calculates SV30
8. HMI displays results
9. Results sent to backend dashboard
```

### **3. Camera Integration**

The USB camera is accessed via OpenCV:

```python
# In modules/video_capture.py
cap = cv2.VideoCapture(CAM1_USB_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM1_USB_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM1_USB_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, CAM1_USB_FPS)
```

---

## 📊 HMI Page Flow

### **Page 1: Login**
- Password authentication
- Default password: `thermax`

### **Page 2: Home/Idle**
- Shows system ready
- "New Cycle" button to start test

### **Page 3: Start Experiment**
- Confirmation dialog
- Shows test duration (35 minutes)

### **Page 4: Progress**
- Real-time countdown timer
- Progress bar
- "Abort Test" option

### **Page 5: Test Complete**
- Auto-displays after 35 minutes
- Processing message while calculating results

### **Page 6: Results**
- Final SV30 value (mL/L)
- Settling velocity
- RGB values
- "New Test" button

---

## 🔍 Testing

### **Test USB Camera:**

```bash
cd ~/Desktop/sv30
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('✅ Camera 0 working')
    ret, frame = cap.read()
    if ret:
        print(f'✅ Resolution: {frame.shape[1]}x{frame.shape[0]}')
else:
    print('❌ Camera 0 not available')
cap.release()
"
```

### **Test HMI Server:**

```bash
cd ~/Desktop/sv30/hmi_server
source venv/bin/activate
python run.py

# Should see:
# INFO:     Uvicorn running on http://0.0.0.0:5000
```

### **Test SV30 Provider:**

```bash
cd ~/Desktop/sv30/hmi_server
python sv30_ml_provider.py
```

---

## 🐛 Troubleshooting

### **Problem: USB Camera Not Found**

```bash
# List available cameras
ls -l /dev/video*

# Test with v4l2
v4l2-ctl --list-devices

# Try different index
# In sv30config.py:
CAM1_USB_INDEX = 1  # Try 0, 1, 2, etc.
```

### **Problem: HMI Server Won't Start**

```bash
# Check port availability
sudo netstat -tulpn | grep 5000

# Kill existing process if needed
sudo kill -9 $(lsof -t -i:5000)

# Check logs
journalctl -u sv30-hmi.service -f
```

### **Problem: Video Capture Fails**

```bash
# Check camera permissions
sudo usermod -a -G video $USER
# Logout and login again

# Test camera directly
ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

### **Problem: Results Not Showing**

Check logs:
```bash
# HMI logs
tail -f ~/Desktop/sv30/hmi_server/logs/hmi.log

# SV30 logs
tail -f ~/Desktop/sv30/logs/sv30.log
```

---

## ⚙️ Configuration Reference

### **sv30config.py - USB Camera Settings:**

```python
# Camera Type
CAM1_TYPE = "USB"  # or "RTSP"

# USB Camera (ELP-USB8MP02G-SFV)
CAM1_USB_INDEX = 0  # Device index
CAM1_USB_WIDTH = 1920  # 1920x1080 recommended
CAM1_USB_HEIGHT = 1080
CAM1_USB_FPS = 30  # 30 fps recommended
CAM1_USB_FOURCC = "MJPG"  # MJPG faster than YUYV

# Test Duration
VIDEO_DURATION_SEC = 35 * 60  # 35 minutes
CAM2_SNAPSHOT_T1_MIN = 2  # t=2 minutes
CAM2_SNAPSHOT_T2_MIN = 33  # t=33 minutes
```

### **HMI .env Settings:**

```bash
# Access
LOGIN_PASSWORD=thermax
PORT=5000

# Test
TEST_DURATION_MINUTES=35

# Backend
BACKEND_URL=https://noble-liberation-production-db43.up.railway.app
FACTORY_CODE=factory-a
```

---

## 📋 Checklist Before Production

- [ ] USB camera connected and tested
- [ ] RTSP Camera 2 working for snapshots
- [ ] HMI server starts without errors
- [ ] Can login to HMI at http://localhost:5000
- [ ] Test workflow completes successfully
- [ ] Results displayed correctly
- [ ] Backend receives data
- [ ] Auto-start configured (systemd)
- [ ] Network accessible from operator station

---

## 🔄 Migration from v3.0

### **What Changed:**

1. **Camera:**
   - CAM1: RTSP → USB
   - Added `CAM1_TYPE`, `CAM1_USB_*` settings

2. **Duration:**
   - 45 min → 35 min
   - Snapshots: t=40 → t=33

3. **HMI:**
   - New FastAPI server
   - Web-based operator interface
   - ML provider integration

### **Migration Steps:**

1. Update `sv30config.py` with new settings
2. Install HMI server dependencies
3. Copy `sv30_ml_provider.py` to HMI directory
4. Configure HMI `.env` file
5. Test camera and HMI separately
6. Test integrated workflow
7. Setup auto-start

---

## 📞 Support

**Camera Issues:** Check device index, permissions, resolution settings  
**HMI Issues:** Check logs, port availability, backend connection  
**Integration Issues:** Check ML provider, test workflow, logging

---

## 🎓 Next Steps

1. **Read**: This guide + README_V4.md
2. **Install**: HMI server + dependencies
3. **Configure**: USB camera + HMI settings
4. **Test**: Camera → HMI → Full workflow
5. **Deploy**: Auto-start services

---

**Version:** 4.0  
**Release Date:** December 2024  
**Status:** Ready for Integration

**Key Features:**
- ✅ USB Camera support
- ✅ 35-minute tests
- ✅ Local HMI interface
- ✅ Real-time progress
- ✅ Automatic backend sync
