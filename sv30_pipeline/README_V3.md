# SV30 v3.0 - CAPTURE-ONLY MODE + AUTO SHUTDOWN

## 🎯 What's New in v3.0

### **MAJOR NEW FEATURES:**

1. **CAPTURE_ONLY_MODE** - Backup raw data without processing
2. **AUTO_SHUTDOWN** - Raspberry Pi shuts down after completion
3. **45-minute duration** - Increased from 30 minutes
4. **New snapshot timing** - t=2 min and t=40 min (changed from t=0 and t=30)

---

## 🎬 TWO OPERATING MODES

### **MODE 1: CAPTURE_ONLY_MODE = True**

**Purpose:** Backup all raw test data to AWS for later analysis

```
┌─────────────────────────────────────────┐
│ 1. Boot Raspberry Pi                    │
│ 2. Auto-start capture script            │
│ 3. Record 45-minute video               │
│ 4. Take CAM2 snapshots (t=2, t=40)      │
│ 5. Upload RAW video + snapshots to AWS  │
│ 6. Send dashboard notifications         │
│ 7. Shutdown Raspberry Pi                │
└─────────────────────────────────────────┘

⏱️  Total time: ~50-55 minutes (45 min capture + upload)
💾 Saved: Video + 2 snapshots
🚫 No processing (saves time and preserves raw data)
```

### **MODE 2: CAPTURE_ONLY_MODE = False**

**Purpose:** Complete analysis with results

```
┌─────────────────────────────────────────┐
│ 1. Boot Raspberry Pi                    │
│ 2. Camera check                          │
│ 3. Archive previous data                 │
│ 4. Record 45-minute video               │
│ 5. Take CAM2 snapshots (t=2, t=40)      │
│ 6. Extract frames (every 10 sec)        │
│ 7. Process frames (new v2.0 algorithm)  │
│ 8. Calculate SV30 metrics               │
│ 9. Generate graphs                       │
│ 10. Upload EVERYTHING to AWS             │
│ 11. Send results to dashboard            │
│ 12. Shutdown Raspberry Pi                │
└─────────────────────────────────────────┘

⏱️  Total time: ~90-100 minutes (45 min capture + 45 min processing)
💾 Saved: Video + snapshots + results + graphs
✅ Complete analysis
```

---

## ⚙️ Configuration

Edit `sv30config.py`:

```python
# =====================================
# CAPTURE ONLY MODE (v3.0)
# =====================================
CAPTURE_ONLY_MODE = False  # Set to True for capture-only

# When True:
#   - Only captures video + snapshots
#   - Uploads to AWS
#   - Shuts down
#   - NO processing

# When False:
#   - Full pipeline (capture + process + results)
#   - Uploads everything
#   - Shuts down

# =====================================
# AUTO SHUTDOWN (v3.0)
# =====================================
AUTO_SHUTDOWN_ENABLED = True  # Auto shutdown after completion
SHUTDOWN_DELAY_SEC = 10       # Countdown before shutdown

# =====================================
# VIDEO SETTINGS (v3.0 - UPDATED)
# =====================================
VIDEO_DURATION_SEC = 45 * 60  # 45 minutes (changed from 30)

# Camera 2 snapshot timing (v3.0 - UPDATED)
CAM2_SNAPSHOT_T1_MIN = 2   # t=2 minutes (changed from t=0)
CAM2_SNAPSHOT_T2_MIN = 40  # t=40 minutes (changed from t=30)
```

---

## 🚀 Quick Start

### **Setup Shutdown Permissions (One-Time)**

```bash
# Required for auto-shutdown to work
sudo visudo

# Add this line:
pi ALL=(ALL) NOPASSWD: /sbin/shutdown

# Save and exit
```

### **Mode 1: Capture-Only (for data backup)**

```python
# In sv30config.py:
CAPTURE_ONLY_MODE = True
AUTO_SHUTDOWN_ENABLED = True
AWS_ENABLED = True  # Must be enabled to upload

# Then run:
python3 main.py
```

**What happens:**
1. ✅ Captures 45-min video
2. ✅ Takes snapshots at t=2 and t=40
3. ✅ Uploads to AWS
4. ✅ Shuts down Pi

**Use when:** You want to backup raw data without processing

---

### **Mode 2: Full Pipeline (normal operation)**

```python
# In sv30config.py:
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = True
AWS_ENABLED = True

# Then run:
python3 main.py
```

**What happens:**
1. ✅ Everything from Mode 1
2. ✅ PLUS full processing
3. ✅ PLUS results and graphs
4. ✅ Shuts down Pi

**Use when:** You want complete analysis with results

---

## 📊 Dashboard Updates

### **Mode 1 (Capture-Only):**
```
Event 1 (t=2 min):
  - Test start notification
  - sludge_height_mm: 0
  - mixture_height_mm: 0

Event 2 (t=40 min):
  - Test end notification
  - No processing results
  - "Video uploaded to S3"
```

### **Mode 2 (Full Pipeline):**
```
Event 1 (t=2 min):
  - Test start notification
  - Initial measurements: 0

Event 2 (t=40 min):
  - Test complete with FULL results
  - SV30 percentage
  - Settling velocity
  - RGB values
  - All metrics
```

---

## 🎛️ Auto-Start on Boot

### **Option A: systemd service (Recommended)**

```bash
# Create service file
sudo nano /etc/systemd/system/sv30.service
```

```ini
[Unit]
Description=SV30 Automated Test
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sv30_v3_final
ExecStart=/usr/bin/python3 /home/pi/sv30_v3_final/main.py
Restart=no

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable sv30.service
sudo systemctl start sv30.service

# Check status
sudo systemctl status sv30.service
```

### **Option B: crontab**

```bash
crontab -e

# Add line:
@reboot sleep 30 && cd /home/pi/sv30_v3_final && /usr/bin/python3 main.py > /home/pi/sv30.log 2>&1
```

---

## 📁 File Changes from v2.0

### **New Files:**
- ✅ `modules/system_shutdown.py` - Shutdown functionality

### **Updated Files:**
- ✅ `sv30config.py` - New flags and settings
- ✅ `main.py` - Two-mode operation + shutdown
- ✅ `modules/video_capture.py` - 45 min + t=2, t=40 snapshots

### **All Other Files:** Unchanged from v2.0

---

## 🔧 Troubleshooting

### **Problem: Shutdown doesn't work**

```
Error: "Failed to execute shutdown"

Solution:
1. Check permissions:
   sudo visudo
   
2. Add line:
   pi ALL=(ALL) NOPASSWD: /sbin/shutdown
   
3. Test:
   sudo shutdown --help
```

### **Problem: Video duration wrong**

```
Check: sv30config.py
Expected: VIDEO_DURATION_SEC = 45 * 60  # 45 minutes
```

### **Problem: Snapshots at wrong time**

```
Check: sv30config.py
Expected:
  CAM2_SNAPSHOT_T1_MIN = 2   # t=2 minutes
  CAM2_SNAPSHOT_T2_MIN = 40  # t=40 minutes
```

---

## 📊 Comparison: v2.0 vs v3.0

| Feature | v2.0 | v3.0 |
|---------|------|------|
| **Modes** | Single (full pipeline) | Dual (capture-only + full) |
| **Duration** | 30 minutes | 45 minutes ✅ |
| **Snapshots** | t=0, t=30 | t=2, t=40 ✅ |
| **Auto-Shutdown** | ❌ No | ✅ Yes (configurable) |
| **Raw Data Backup** | Manual | ✅ CAPTURE_ONLY_MODE |
| **Dashboard** | Results only | Both modes ✅ |

---

## 💡 Use Cases

### **Scenario 1: Production Daily Tests**
```python
CAPTURE_ONLY_MODE = False  # Full pipeline
AUTO_SHUTDOWN_ENABLED = True
RUN_ONCE_PER_BOOT = True
```
- Boot at 6 AM → Complete analysis → Shutdown
- Boot at 2 PM → Complete analysis → Shutdown
- Boot at 10 PM → Complete analysis → Shutdown

### **Scenario 2: Algorithm Development**
```python
CAPTURE_ONLY_MODE = True  # Just capture
AUTO_SHUTDOWN_ENABLED = True
```
- Collect raw data from multiple tests
- Process later with different algorithms
- Compare results

### **Scenario 3: Debugging**
```python
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = False  # Stay on
DEV_MODE = True  # Keep files
```
- Full pipeline but no shutdown
- Review intermediate files
- Debug issues

---

## 🎯 Recommended Settings

### **Production (Daily Automated Tests):**
```python
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = True
RUN_ONCE_PER_BOOT = True
DEV_MODE = False
AWS_ENABLED = True
SOCKETIO_ENABLED = True
```

### **Data Collection (Raw Backup):**
```python
CAPTURE_ONLY_MODE = True
AUTO_SHUTDOWN_ENABLED = True
RUN_ONCE_PER_BOOT = True
DEV_MODE = False
AWS_ENABLED = True  # Must be True!
SOCKETIO_ENABLED = True
```

### **Development/Testing:**
```python
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = False
RUN_ONCE_PER_BOOT = False
DEV_MODE = True
AWS_ENABLED = False
SOCKETIO_ENABLED = False
```

---

## 📚 Additional Documentation

- [README.md](README.md) - Complete v2.0 documentation
- [QUICK_START.md](QUICK_START.md) - 10-minute setup guide
- [CHANGES_V2.md](CHANGES_V2.md) - v1.0 → v2.0 changelog
- [CHANGES_V3.md](CHANGES_V3.md) - v2.0 → v3.0 changelog (this version)

---

**Version:** 3.0  
**Release Date:** December 2024  
**Status:** Production Ready ✅

**Key Benefits:**
- ✅ Raw data backup (capture-only mode)
- ✅ Longer test duration (45 min)
- ✅ Automatic shutdown (saves power)
- ✅ Better snapshot timing (t=2, t=40)
- ✅ Dual-mode flexibility
