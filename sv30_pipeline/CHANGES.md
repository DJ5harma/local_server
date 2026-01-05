# SV30 System - Changes from V1 to V2

## 📋 Overview

This document details all changes made when migrating from **frame-by-frame capture** (v1) to **video-based workflow** (v2).

---

## 🎥 Major Workflow Change

### V1 Workflow (Old):
```
Camera 1 → Capture frame every 10s → Save to 0.1raw/cam1/ and 0_raw/
Camera 2 → Capture frame every 10s → Save to 0.1raw/cam2/
         ↓
   Process 0_raw/ frames directly
```

### V2 Workflow (New):
```
Camera 1 → Record 30-min video → Save to upload_raw/videos/
Camera 2 → Capture at t=0 and t=30 → Save to upload_raw/
         ↓
   Extract frames from video → Save to 0_raw/
         ↓
   Process 0_raw/ frames
```

---

## 🔄 File Changes

### New Files:
1. `modules/video_capture.py` - Records video + Camera 2 snapshots
2. `modules/frame_extractor.py` - Extracts frames from video
3. `modules/aws_uploader.py` - Uploads to AWS S3
4. `AWS_SETUP_GUIDE.md` - Complete AWS configuration guide

### Replaced Files:
- `modules/capture.py` → `modules/video_capture.py`

### Updated Files:
1. `sv30config.py` - New settings for video, AWS, folder structure
2. `main.py` - Sequential pipeline, AWS integration
3. `modules/preprocess.py` - Progressive cleanup
4. `modules/mask_beaker.py` - Progressive cleanup
5. `modules/sludge_detect.py` - Progressive cleanup
6. `modules/rgb_analysis.py` - Works with 2 snapshots instead of 181 frames
7. `requirements.txt` - Added boto3 for AWS

### Unchanged Files:
- `modules/detect_geometry.py` - No changes
- `modules/sv30metrics.py` - No changes
- `modules/graph_generator.py` - No changes
- `modbus_server.py` - No changes

---

## 📁 Folder Structure Changes

### Old Structure (V1):
```
stage_inputs/
├── 0_raw/              # Camera 1 frames (processing)
├── 0.1raw/
│   ├── cam1/          # All Camera 1 frames (cloud)
│   └── cam2/          # All Camera 2 frames (RGB)
└── ...
```

### New Structure (V2):
```
stage_inputs/
├── upload_raw/         # NEW: Renamed from 0.1raw
│   ├── videos/        # NEW: 30-min video files
│   ├── cam2_t0.jpg   # NEW: Snapshot at start
│   └── cam2_t30.jpg  # NEW: Snapshot at end
├── 0_raw/             # Extracted frames (processing)
└── ...
```

**Key Changes**:
- `0.1raw/` → `upload_raw/` (clearer name)
- Videos stored separately in `upload_raw/videos/`
- Camera 2 now captures only 2 snapshots (not 181)

---

## ⚙️ Configuration Changes (sv30config.py)

### New Settings:

```python
# Video recording
VIDEO_DURATION_SEC = 30 * 60
VIDEO_BUFFER_SEC = 5 * 60
VIDEO_CODEC = "copy"
VIDEO_FORMAT = "mp4"
VIDEO_RTSP_TRANSPORT = "tcp"

# Folder paths
UPLOAD_RAW_FOLDER = os.path.join(STAGE_INPUTS, "upload_raw")
UPLOAD_VIDEOS_FOLDER = os.path.join(UPLOAD_RAW_FOLDER, "videos")

# AWS S3
AWS_ENABLED = False
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "ap-south-1"
AWS_S3_BUCKET = "sv30-test-data"
AWS_S3_PREFIX = "sv30_tests"
AWS_UPLOAD_VIDEO = True
AWS_UPLOAD_IMAGES = True
AWS_UPLOAD_RESULTS = True
AWS_DELETE_AFTER_UPLOAD = True
AWS_MAX_RETRIES = 5
AWS_RETRY_DELAY_SEC = 30
```

### Removed Settings:
```python
# No longer needed
WARMUP_READS = 30  # Moved to video_capture.py
RAW_ALL_CAM1 = ...  # Replaced by UPLOAD_RAW_FOLDER
RAW_ALL_CAM2 = ...  # Replaced by UPLOAD_RAW_FOLDER
```

---

## 🔄 Pipeline Flow Changes

### V1 Pipeline:
```
1. Capture frames (30 min, live)
2. Process frames (parallel with capture)
3. Calculate metrics
4. Generate graphs
5. Update Modbus
```

### V2 Pipeline:
```
1. Record video (30 min) + Camera 2 snapshots
2. Extract frames from video (batch)
3. Process frames (batch, sequential)
   - Preprocess → delete 0_raw/
   - Mask → delete 1_preprocessed/
   - Sludge → delete 2_color_masked/, 3_gray_masked/
4. Calculate metrics
5. RGB analysis (2 snapshots)
6. Generate graphs
7. Upload to AWS
8. Update Modbus
```

**Key Differences**:
- ✅ Sequential (not parallel)
- ✅ Batch processing (not incremental)
- ✅ Progressive cleanup (production mode)
- ✅ AWS upload integrated

---

## 🎯 Camera 2 Changes

### V1 Behavior:
- Captured frame every 10 seconds
- 181 total frames
- All saved to `0.1raw/cam2/`
- RGB analysis used first and last frame

### V2 Behavior:
- Captures at t=0 only
- Captures at t=30 only
- 2 total snapshots
- Saved as `upload_raw/cam2_t0.jpg` and `cam2_t30.jpg`
- RGB analysis uses both snapshots

**Advantages**:
- ✅ 90% less storage (2 images vs 181)
- ✅ Clearer naming (t0, t30)
- ✅ Faster processing

---

## 📦 Module Changes

### 1. video_capture.py (NEW)

**Purpose**: Record 30-minute video and capture Camera 2 snapshots

**Features**:
- FFmpeg-based video recording
- Retry logic for 30-minute guarantee
- Concurrent Camera 2 snapshot capture
- Graceful shutdown handling

**Replaces**: `modules/capture.py`

---

### 2. frame_extractor.py (NEW)

**Purpose**: Extract frames from video at 10-second intervals

**Features**:
- Uses OpenCV VideoCapture
- Precise timing (10s intervals)
- Progress indicators
- Filename includes timestamp (MM:SS)

**Example Output**:
```
cam1_frame0000_00m00s.jpg
cam1_frame0001_00m10s.jpg
cam1_frame0002_00m20s.jpg
...
```

---

### 3. aws_uploader.py (NEW)

**Purpose**: Upload test data to AWS S3

**Features**:
- Boto3-based upload
- Retry logic (5 attempts)
- Progress indicators
- Automatic folder structure
- Post-upload cleanup (production mode)

**Upload Priority**:
1. Video first (largest file)
2. Camera 2 images
3. Results JSON
4. Graphs

---

### 4. rgb_analysis.py (UPDATED)

**Changes**:
- Now expects exactly 2 files: `cam2_t0.jpg` and `cam2_t30.jpg`
- Removed file listing and sorting logic
- Added brightness change calculation
- Updated file paths to `UPLOAD_RAW_FOLDER`

---

### 5. preprocess.py, mask_beaker.py, sludge_detect.py (UPDATED)

**Changes**:
- Added progressive cleanup logic
- `DEV_MODE = False` → delete source files after processing
- Progress indicators (every 10 frames)
- Batch processing (all frames at once)

---

### 6. main.py (MAJOR UPDATE)

**New Pipeline Structure**:
```python
def run_full():
    # 1. Start Modbus
    # 2. Video capture (30 min)
    # 3. Frame extraction
    # 4. Sequential processing (preprocess → mask → sludge → geometry)
    # 5. Metrics calculation
    # 6. RGB analysis
    # 7. Graph generation
    # 8. AWS upload
    # 9. Modbus update
```

**New Features**:
- Test ID generation (`DDMMYYtest1`)
- AWS upload integration
- Progressive cleanup coordination
- Better error handling
- Stage timing/duration tracking

---

## 🛠️ Dependency Changes

### requirements.txt

**Added**:
```
boto3==1.28.85  # AWS S3 upload
```

**System Dependencies**:
```bash
# Required for video recording
sudo apt install ffmpeg
```

---

## 📊 Storage Impact

### V1 Storage During Test:
```
0_raw/: 181 frames × ~1 MB = ~181 MB
0.1raw/cam1/: 181 frames × ~1 MB = ~181 MB
0.1raw/cam2/: 181 frames × ~1 MB = ~181 MB
TOTAL: ~543 MB
```

### V2 Storage During Test:

**Development Mode**:
```
Video: ~2-4 GB
0_raw/: 181 frames × ~1 MB = ~181 MB
All intermediate: ~1 GB
TOTAL: ~5-6 GB (temporary)
```

**Production Mode** (after cleanup):
```
Video: 0 (uploaded and deleted)
upload_raw/: 2 snapshots × ~1 MB = ~2 MB
results/: JSON files = ~500 KB
graphs/: 5 PNGs = ~2 MB
TOTAL: ~5 MB
```

**Winner**: V2 (production mode) uses **99% less disk space** long-term!

---

## ⚡ Performance Comparison

### V1 Pipeline:
```
Capture: 30 min (live, concurrent with processing)
Processing: Incremental (as frames arrive)
Total Time: ~30 minutes
```

### V2 Pipeline:
```
Video Capture: 30 min (recording)
Frame Extraction: ~30 sec
Processing: ~5 min (batch)
Metrics: ~10 sec
Graphs: ~5 sec
AWS Upload: ~5-10 min (optional)
Total Time: ~35-40 minutes (without AWS) or ~45-50 min (with AWS)
```

**Trade-off**: V2 is slower but more reliable and manageable

---

## 🔐 Security Improvements

### V1:
- Camera credentials in config file

### V2:
- Camera credentials in config file
- **AWS credentials** via environment variables (recommended)
- IAM user with limited permissions
- Automatic credential rotation support
- S3 bucket lifecycle policies

---

## 🐛 Bug Fixes from V1

### Fixed in V2:
1. ✅ **RTSP timeout issues** → Retry logic for full 30-minute capture
2. ✅ **Frame timing inconsistency** → Post-extraction ensures precise 10s intervals
3. ✅ **Storage management** → Progressive cleanup in production mode
4. ✅ **Disk space issues** → Video deleted after AWS upload
5. ✅ **Race conditions** → Sequential processing eliminates conflicts

---

## 🎓 Migration Guide (V1 → V2)

### Step 1: Backup V1 System
```bash
cp -r /path/to/v1_system /path/to/v1_backup
```

### Step 2: Install FFmpeg
```bash
sudo apt update
sudo apt install ffmpeg -y
```

### Step 3: Install boto3 (if using AWS)
```bash
pip3 install boto3
```

### Step 4: Update Configuration
```bash
# Copy old config values
OLD_CROP_X1=$(grep CROP_X1 v1/sv30config.py)

# Edit new config
nano v2/sv30config.py
# Paste old values for:
# - CROP coordinates
# - MIXTURE_TOP_Y
# - Camera URLs
# - RGB points
```

### Step 5: Configure AWS (Optional)
```bash
# See AWS_SETUP_GUIDE.md
```

### Step 6: Test New System
```bash
# Test video capture (Ctrl+C after 1 min)
python3 main.py capture

# Extract frames
python3 main.py extract

# Test full pipeline
python3 main.py full
```

### Step 7: Verify Outputs
```bash
# Check video exists
ls -lh upload_raw/videos/

# Check snapshots
ls -lh upload_raw/cam2_*.jpg

# Check results
cat results/sv30_metrics.json | jq
cat results/rgb_values.json | jq

# Check graphs
ls -lh graphs/
```

---

## 📈 Advantages of V2

1. **Reliability**
   - Retry logic ensures 30-minute capture
   - No dropped frames during network issues
   - Post-processing allows re-extraction

2. **Storage Efficiency**
   - Production mode: 99% less long-term storage
   - Video upload to cloud
   - Automatic cleanup

3. **Flexibility**
   - Can re-extract at different intervals
   - Can analyze video manually if needed
   - Easier to review raw footage

4. **Cloud Integration**
   - Automatic AWS S3 upload
   - Organized folder structure
   - Retry logic for network issues

5. **Maintainability**
   - Sequential processing (easier debugging)
   - Clear stage separation
   - Better error handling

---

## ⚠️ Disadvantages of V2

1. **Longer Pipeline**
   - Extra 5-15 minutes for extraction/processing
   - Cannot start processing during capture

2. **Storage Spike**
   - Needs 5-6 GB during test (vs 0.5 GB in V1)
   - Requires sufficient disk space buffer

3. **FFmpeg Dependency**
   - Additional software requirement
   - Platform-specific (Linux/Pi only)

---

## 🔮 Future Enhancements

Planned improvements:
- [ ] Parallel frame extraction (faster processing)
- [ ] Real-time streaming to dashboard during capture
- [ ] Adaptive quality encoding (reduce file size)
- [ ] Multi-region AWS support
- [ ] Automatic retry on AWS upload failure
- [ ] Email notifications on test completion
- [ ] Video compression before upload

---

## ✅ Compatibility Matrix

| Feature | V1 | V2 | Notes |
|---------|----|----|-------|
| Raspberry Pi 4 | ✅ | ✅ | Both versions |
| Camera RTSP | ✅ | ✅ | Same configuration |
| Modbus output | ✅ | ✅ | Unchanged |
| JSON results | ✅ | ✅ | Same format |
| Graphs | ✅ | ✅ | Same outputs |
| DEV_MODE | ✅ | ✅ | Enhanced in V2 |
| AWS Upload | ❌ | ✅ | New in V2 |
| Socket.IO | ❌ | ❌ | Planned for both |

---

## 📞 Support

If you encounter issues during migration:
1. Check this document for changes
2. Review AWS_SETUP_GUIDE.md for AWS issues
3. Test individual stages (capture, extract, etc.)
4. Compare config files (V1 vs V2)
5. Check FFmpeg is installed: `ffmpeg -version`

---

**Migration Version**: 1.0 → 2.0  
**Document Last Updated**: December 2024  
**Status**: Production Ready ✅
