#!/bin/bash
# Complete installation script for Thermax SV30 System

echo "============================================"
echo "  THERMAX SV30 - INSTALLATION"
echo "============================================"

# 1. Install system dependencies
echo "[1/6] Installing system dependencies..."
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg v4l-utils

# 2. Setup HMI Server
echo "[2/6] Setting up HMI Server..."
cd hmi_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
deactivate
cd ..

# 3. Setup SV30 Pipeline
echo "[3/6] Setting up SV30 Pipeline..."
cd sv30_pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
deactivate
cd ..

# 4. Create necessary directories
echo "[4/6] Creating directories..."
mkdir -p sv30_pipeline/{logs,results,stage_inputs/upload_raw/videos}

# 5. Set permissions
echo "[5/6] Setting permissions..."
chmod +x scripts/*.sh

# 6. Configure cameras
echo "[6/6] Checking USB camera..."
ls -l /dev/video* || echo "⚠️  No camera detected"

echo ""
echo "============================================"
echo "  ✅ INSTALLATION COMPLETE!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit hmi_server/.env (set password, backend URL)"
echo "  2. Edit sv30_pipeline/sv30config.py (camera settings)"
echo "  3. Run: ./scripts/start_system.sh"
echo ""
