# 🚀 SV30 v2.0 - Quick Start Guide

**Get up and running in 10 minutes!**

---

## ✅ Step 1: Install (2 min)

```bash
# Copy project to Raspberry Pi
cd /home/pi
cp -r /path/to/sv30_v2_integrated ./sv30

# Install dependencies
cd sv30
pip install -r requirements.txt --break-system-packages

# Download rembg model (one-time, ~100MB)
python3 -c "from rembg import remove; print('✅ Model ready')"
```

---

## ⚙️ Step 2: Configure (3 min)

Edit `sv30config.py`:

```python
# 1. SET YOUR FACTORY CODE
FACTORY_CODE = "factory-a"  # ← Change this!

# 2. SET CAMERA URLs
CAM1_URL = "rtsp://admin:password@192.168.1.101:554/..."  # ← Update
CAM2_URL = "rtsp://admin:password@192.168.1.102:554/..."  # ← Update

# 3. ENABLE FEATURES
DEV_MODE = True  # Start with True for testing
AWS_ENABLED = False  # Enable later after AWS setup
SOCKETIO_ENABLED = True  # Dashboard enabled
MODBUS_ENABLED = False  # Enable if using Modbus
CAMERA_CHECK_ENABLED = True  # Recommended
ARCHIVE_ENABLED = True  # Recommended
```

**That's it for basic config!** Other settings have good defaults.

---

## 🧪 Step 3: Test Run (5 min)

```bash
# Quick test (dev mode keeps all files)
python3 main.py
```

**What happens:**
```
✅ Camera check (both cameras)
✅ Archive old data (if any)
✅ Connect to dashboard
✅ Start 30-minute video capture
✅ Process frames with new algorithm
✅ Generate results
✅ Send to dashboard
```

**Check results:**
```bash
# View metrics
cat results/sv30_metrics.json

# View detection details
cat results/sludge_detection_v2.json

# View graphs
ls graphs/
```

---

## 🔧 Optional: AWS Setup

### **1. Get AWS Credentials**

1. Go to AWS Console → IAM → Users
2. Create access key
3. Download credentials

### **2. Configure**

```bash
# Option A: Environment variables (recommended)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Option B: Edit sv30config.py
AWS_ACCESS_KEY_ID = "your-key"
AWS_SECRET_ACCESS_KEY = "your-secret"
AWS_S3_BUCKET = "your-bucket-name"
```

### **3. Enable**

```python
# In sv30config.py:
AWS_ENABLED = True
```

See [AWS_SETUP_GUIDE.md](AWS_SETUP_GUIDE.md) for details.

---

## 🎛️ Production Mode

Once testing is complete:

```python
# In sv30config.py:
DEV_MODE = False  # Enables file cleanup
RUN_ONCE_PER_BOOT = True  # Prevents duplicates
AWS_ENABLED = True  # Upload to S3
```

---

## 📊 Monitoring

### **Dashboard (Socket.IO)**

Dashboard receives:
- ✅ Test start notification (t=0)
- ✅ Test complete with results (t=30)
- ⚠️ AWS upload warnings
- ⚠️ System errors

URL: `https://noble-liberation-production-db43.up.railway.app`

### **Modbus (Optional)**

Enable in config:
```python
MODBUS_ENABLED = True
MODBUS_HOST = "0.0.0.0"
MODBUS_PORT = 5020
```

**Registers:**
- 40001: SV30 (% × 100)
- 40002: Velocity (%/sec × 10,000)
- 40003: Duration (min)
- 40004-40005: Epoch timestamp

---

## 🔍 Troubleshooting

### **Problem: Camera check fails**

```bash
# Test camera manually
ffplay rtsp://admin:password@192.168.1.101:554/...

# If timeout, check network
ping 192.168.1.101

# Verify credentials
```

### **Problem: Detection seems off**

```python
# Adjust in sv30config.py:

# If detecting too early (interface too close to top):
MIN_SLUDGE_DISTANCE_PX = 30  # Increase from 20

# If detecting too late (interface too far down):
MIN_SLUDGE_DISTANCE_PX = 10  # Decrease from 20
```

### **Problem: Dashboard not receiving data**

```bash
# Test connection
curl https://noble-liberation-production-db43.up.railway.app/health

# Check config
SOCKETIO_ENABLED = True  # Must be True
FACTORY_CODE = "factory-a"  # Must match dashboard
```

### **Problem: AWS upload fails**

```bash
# Check credentials
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Check bucket
aws s3 ls s3://your-bucket-name

# Check network
ping s3.amazonaws.com
```

---

## 📁 Important Folders

```
sv30/
├── stage_inputs/upload_raw/videos/  ← Videos saved here
├── results/                          ← JSON results
├── graphs/                           ← PNG graphs
└── archive/                          ← Old test data
```

---

## 🎯 Next Steps

1. ✅ Run test in dev mode
2. ✅ Review results
3. ✅ Configure AWS (if needed)
4. ✅ Switch to production mode
5. ✅ Set up auto-start on boot

---

## 📚 Full Documentation

- [README.md](README.md) - Complete documentation
- [CHANGES_V2.md](CHANGES_V2.md) - What's new in v2.0
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Technical details
- [AWS_SETUP_GUIDE.md](AWS_SETUP_GUIDE.md) - AWS configuration
- [SOCKETIO_SETUP_GUIDE.md](SOCKETIO_SETUP_GUIDE.md) - Dashboard setup

---

## 🆘 Help

**Questions?**
1. Check documentation above
2. Review logs in `logs/` folder
3. Contact system administrator

---

**That's it! You're ready to go!** 🎉

**Version:** 2.0  
**Updated:** December 2024
