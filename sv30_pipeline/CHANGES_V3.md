# SV30 v3.0 - Changelog

## Version 3.0 - CAPTURE-ONLY MODE + AUTO SHUTDOWN

**Release Date:** December 2024  
**Status:** Production Ready

---

## 🎯 Summary

v3.0 introduces **dual-mode operation** and **automatic shutdown**, making the system more flexible and power-efficient.

---

## ✨ NEW FEATURES

### **1. CAPTURE_ONLY_MODE (Major Feature)**

**Purpose:** Backup raw test data without processing

```python
# New config flag
CAPTURE_ONLY_MODE = True  # or False
```

**When enabled (True):**
- ✅ Captures 45-minute video
- ✅ Takes CAM2 snapshots (t=2, t=40)
- ✅ Uploads RAW data to AWS S3
- ✅ Sends dashboard notifications
- ✅ Shuts down Raspberry Pi
- ❌ NO processing (saves time)

**When disabled (False):**
- ✅ Full pipeline (current behavior)
- ✅ Capture + Process + Results
- ✅ Everything uploaded
- ✅ Shuts down Raspberry Pi

**Benefits:**
- 📦 Preserve raw data for algorithm development
- ⏱️  Faster execution (~50 min vs ~90 min)
- 🔄 Process later with different algorithms
- 💾 Complete data backup

---

### **2. AUTO_SHUTDOWN (Major Feature)**

**Purpose:** Automatically power off Raspberry Pi after completion

```python
# New config flags
AUTO_SHUTDOWN_ENABLED = True
SHUTDOWN_DELAY_SEC = 10  # Countdown delay
```

**Features:**
- ✅ Graceful shutdown with countdown
- ✅ Configurable delay (default: 10 seconds)
- ✅ Cancel with Ctrl+C during countdown
- ✅ Checks permissions at startup
- ✅ Works in both modes

**Benefits:**
- 💡 Saves power
- 🔒 Prevents SD card corruption
- 📅 Perfect for automated daily tests
- 🎛️  Can be disabled for debugging

**Setup:**
```bash
sudo visudo
# Add: pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

---

### **3. Extended Test Duration**

**Changed:** 30 minutes → 45 minutes

```python
# Updated config
VIDEO_DURATION_SEC = 45 * 60  # Was 30 * 60
```

**Reason:** Better settling data for slower settling samples

---

### **4. New Snapshot Timing**

**Changed:** t=0, t=30 → t=2, t=40

```python
# New config
CAM2_SNAPSHOT_T1_MIN = 2   # Was t=0
CAM2_SNAPSHOT_T2_MIN = 40  # Was t=30
```

**Reason:**
- t=0 often captures before settling starts
- t=2 captures after initial mixing
- t=40 captures near end of 45-min test

---

## 📝 DETAILED CHANGES

### **sv30config.py - New Parameters**

```python
# CAPTURE ONLY MODE (NEW)
CAPTURE_ONLY_MODE = False

# AUTO SHUTDOWN (NEW)
AUTO_SHUTDOWN_ENABLED = True
SHUTDOWN_DELAY_SEC = 10

# EXPERIMENT SETTINGS (UPDATED)
VIDEO_DURATION_SEC = 45 * 60  # Changed from 30
CAM2_SNAPSHOT_T1_MIN = 2      # Changed from t=0
CAM2_SNAPSHOT_T2_MIN = 40     # Changed from t=30
```

---

### **main.py - Major Restructuring**

**Added:**
```python
# Two main functions instead of one
def run_capture_only():
    """Capture + upload + shutdown"""

def run_full_pipeline():
    """Capture + process + upload + shutdown"""

# Mode selection in main
if CAPTURE_ONLY_MODE:
    success = run_capture_only()
else:
    success = run_full_pipeline()

# Auto shutdown
if success and AUTO_SHUTDOWN_ENABLED:
    shutdown_system(SHUTDOWN_DELAY_SEC)
```

**Changes:**
- Reorganized into two distinct workflows
- Added shutdown functionality
- Updated stage numbers (15 stages in full mode, 4 in capture-only)
- Dashboard updates for both modes
- Better error handling

---

### **modules/video_capture.py - Updated Logic**

**Changed:**
```python
# Old
cam2_t0_captured = False
capture_cam2_snapshot('t0')   # At start
capture_cam2_snapshot('t30')  # At 30 min

# New
cam2_t1_captured = False
cam2_t2_captured = False
capture_cam2_snapshot('t2')   # At 2 min
capture_cam2_snapshot('t40')  # At 40 min
```

**Features:**
- Checks elapsed time for snapshot triggers
- Captures at specific minute marks (not start/end)
- Better handling of retry logic
- Updated file naming: cam2_t2.jpg, cam2_t40.jpg

---

### **modules/system_shutdown.py - NEW MODULE**

**Purpose:** Handle graceful Raspberry Pi shutdown

```python
def shutdown_system(delay_sec=10):
    """Shutdown with countdown"""

def test_shutdown_permissions():
    """Check if sudo shutdown works"""
```

**Features:**
- 10-second countdown (configurable)
- Can cancel with Ctrl+C
- Tests permissions at startup
- Provides setup instructions

---

## 🔄 MIGRATION FROM v2.0

### **Breaking Changes:**

1. **Snapshot files renamed:**
   - `cam2_t0.jpg` → `cam2_t2.jpg`
   - `cam2_t30.jpg` → `cam2_t40.jpg`

2. **Video duration:**
   - 30 minutes → 45 minutes
   - Plan accordingly (1.5x longer)

3. **Auto-shutdown:**
   - System will shutdown by default
   - Set `AUTO_SHUTDOWN_ENABLED = False` to prevent

### **Migration Steps:**

1. **Update config:**
   ```python
   # In sv30config.py, add new parameters:
   CAPTURE_ONLY_MODE = False
   AUTO_SHUTDOWN_ENABLED = True
   SHUTDOWN_DELAY_SEC = 10
   ```

2. **Setup shutdown permissions:**
   ```bash
   sudo visudo
   # Add: pi ALL=(ALL) NOPASSWD: /sbin/shutdown
   ```

3. **Update AWS uploader** (if custom):
   - Change snapshot names: t0→t2, t30→t40

4. **Test in dev mode:**
   ```python
   DEV_MODE = True
   AUTO_SHUTDOWN_ENABLED = False
   ```

5. **Enable production mode:**
   ```python
   DEV_MODE = False
   AUTO_SHUTDOWN_ENABLED = True
   CAPTURE_ONLY_MODE = False  # or True for backup mode
   ```

---

## 🐛 BUG FIXES

### **Fixed in v3.0:**

1. **Snapshot timing:**
   - ✅ t=0 sometimes captured before test started
   - ✅ t=30 missed in 30-min tests
   - ✅ Now captures at t=2 (after start) and t=40 (before end)

2. **Duration limitation:**
   - ✅ 30 min too short for slow settling
   - ✅ Now 45 min provides better data

3. **Power management:**
   - ✅ Pi stayed on indefinitely
   - ✅ Now auto-shutdowns to save power

---

## 📊 PERFORMANCE

### **Capture-Only Mode:**
```
Duration: ~50-55 minutes
  - 45 min capture
  - 5-10 min upload
  - Shutdown

Resources: Minimal processing
Power: Shutdown after completion ✅
```

### **Full Pipeline Mode:**
```
Duration: ~90-100 minutes
  - 45 min capture
  - 45-50 min processing
  - 5-10 min upload
  - Shutdown

Resources: Full processing
Power: Shutdown after completion ✅
```

---

## 💡 USE CASES

### **When to use CAPTURE_ONLY_MODE:**

✅ **Algorithm Development**
- Collect raw data from multiple tests
- Process later with different parameters
- Compare algorithm versions

✅ **Data Backup**
- Preserve original videos
- Insurance against processing failures
- Historical data archive

✅ **Quick Tests**
- Need results fast
- Process later on powerful machine
- Field testing

### **When to use FULL PIPELINE:**

✅ **Production Operations**
- Daily automated tests
- Immediate results needed
- Complete documentation

✅ **Quality Control**
- Real-time monitoring
- Dashboard integration
- Modbus reporting

---

## 🎓 EXAMPLES

### **Example 1: Daily Production (Full Pipeline)**

```python
# sv30config.py
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = True
RUN_ONCE_PER_BOOT = True
DEV_MODE = False
AWS_ENABLED = True
SOCKETIO_ENABLED = True
```

**Workflow:**
1. Boot at 6 AM → Full analysis → Upload → Shutdown
2. Boot at 2 PM → Full analysis → Upload → Shutdown
3. Boot at 10 PM → Full analysis → Upload → Shutdown

---

### **Example 2: Algorithm Testing (Capture-Only)**

```python
# sv30config.py
CAPTURE_ONLY_MODE = True
AUTO_SHUTDOWN_ENABLED = True
RUN_ONCE_PER_BOOT = True
AWS_ENABLED = True
```

**Workflow:**
1. Run 10 tests over 5 days
2. Collect all raw videos in S3
3. Process offline with new algorithm
4. Compare results
5. Deploy best algorithm

---

### **Example 3: Debugging (No Shutdown)**

```python
# sv30config.py
CAPTURE_ONLY_MODE = False
AUTO_SHUTDOWN_ENABLED = False  # Stay on
DEV_MODE = True  # Keep files
AWS_ENABLED = False
```

**Workflow:**
1. Run test
2. Review intermediate files
3. Debug issues
4. Modify code
5. Test again

---

## 📚 DOCUMENTATION UPDATES

### **New Files:**
- ✅ `README_V3.md` - v3.0 features and usage
- ✅ `CHANGES_V3.md` - This changelog
- ✅ `modules/system_shutdown.py` - Shutdown module

### **Updated Files:**
- ✅ All documentation updated with v3.0 features

---

## 🔮 FUTURE ENHANCEMENTS

**Planned for v3.1:**
- [ ] Remote processing mode (download from S3, process, upload)
- [ ] Multi-test batch processing
- [ ] Automatic algorithm parameter tuning
- [ ] Email notifications on completion

**Planned for v4.0:**
- [ ] Cloud processing (AWS Lambda)
- [ ] Real-time streaming
- [ ] Mobile app control
- [ ] AI-powered anomaly detection

---

## 📞 SUPPORT

**Upgrade Issues?**
1. Check README_V3.md
2. Review this changelog
3. Test with AUTO_SHUTDOWN_ENABLED = False first
4. Contact system administrator

**Permissions Issues?**
```bash
# Test shutdown
sudo shutdown --help

# Fix if needed
sudo visudo
# Add: pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

---

## ✅ TESTING CHECKLIST

Before production deployment:

- [ ] Shutdown permissions configured
- [ ] CAPTURE_ONLY_MODE tested (both True and False)
- [ ] Auto-shutdown tested (with cancel)
- [ ] 45-minute duration verified
- [ ] Snapshots at t=2 and t=40 confirmed
- [ ] Dashboard receives notifications (both modes)
- [ ] AWS upload works (both modes)
- [ ] Boot marker prevents duplicates
- [ ] Archive system works

---

**End of Changelog**

**Version:** 3.0  
**Date:** December 2024  
**Upgrade:** RECOMMENDED for all users
