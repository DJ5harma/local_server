"""
SV30 Configuration (v4.1 - Complete)

USB Camera Only - CAM2 Removed
Complete configuration for full pipeline

Author: Jan 2026
"""

import os

# ==========================================
# BASE PATHS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# STAGE FOLDERS
# ==========================================
STAGE_INPUTS_DIR = os.path.join(BASE_DIR, "stage_inputs")

# Processing stages
RAW_FOLDER = os.path.join(STAGE_INPUTS_DIR, "0_raw")
PREPROCESSED_FOLDER = os.path.join(STAGE_INPUTS_DIR, "1_preprocessed")
COLOR_MASKED_FOLDER = os.path.join(STAGE_INPUTS_DIR, "2_color_masked")
GRAY_MASKED_FOLDER = os.path.join(STAGE_INPUTS_DIR, "3_gray_masked")
OTSU_BINARY_FOLDER = os.path.join(STAGE_INPUTS_DIR, "4_otsu_binary")
SLUDGE_DEBUG_FOLDER = os.path.join(STAGE_INPUTS_DIR, "5_sludge_debug")

# Upload folders
UPLOAD_RAW_FOLDER = os.path.join(STAGE_INPUTS_DIR, "upload_raw")
UPLOAD_VIDEOS_FOLDER = os.path.join(UPLOAD_RAW_FOLDER, "videos")

# Output folders
RESULTS_FOLDER = os.path.join(BASE_DIR, "results")
LOGS_FOLDER = os.path.join(BASE_DIR, "logs")

# ==========================================
# CAMERA SETTINGS - USB ONLY
# ==========================================
CAM1_USB_INDEX = 0  # /dev/video0 (change to 1, 2, etc. if needed)

# ==========================================
# VIDEO CAPTURE
# ==========================================
VIDEO_DURATION_SEC = 35* 60  # 35 minutes (change to 2*60 for testing)
FRAME_INTERVAL_SEC = 10  # Extract frame every 10 seconds

# ==========================================
# IMAGE PREPROCESSING - CROP COORDINATES
# ==========================================
CROP_X1 = 180
CROP_Y1 = 0
CROP_X2 = 500
CROP_Y2 = 480

# ==========================================
# IMAGE EXTENSIONS
# ==========================================
IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp')

# ==========================================
# OPERATING MODE
# ==========================================
DEV_MODE = True  # Keep intermediate files for debugging

# ==========================================
# CALCULATIONS
# ==========================================
BEAKER_HEIGHT_MM = 214.0  # Standard beaker height
TEST_DURATION_MIN = 35.0  # Test duration in minutes

# ==========================================
# SOCKETIO DASHBOARD
# ==========================================
SOCKETIO_ENABLED = True  # Set to True to enable
SOCKETIO_URL = "https://noble-liberation-production-db43.up.railway.app"
FACTORY_CODE = "factory-a"

# ==========================================
# AWS S3 UPLOAD
# ==========================================
AWS_ENABLED = True  # Set to True to enable
AWS_REGION = "ap-southeast-2"
AWS_BUCKET_NAME = "sv30-testdata-thermax"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# ==========================================
# MODBUS SERVER
# ==========================================
MODBUS_ENABLED = False  # Set to True to enable
MODBUS_HOST = "0.0.0.0"
MODBUS_PORT = 502

# ==========================================
# CREATE DIRECTORIES ON IMPORT
# ==========================================
def create_directories():
    """Create all necessary directories"""
    dirs = [
        RAW_FOLDER,
        PREPROCESSED_FOLDER,
        COLOR_MASKED_FOLDER,
        GRAY_MASKED_FOLDER,
        OTSU_BINARY_FOLDER,
        SLUDGE_DEBUG_FOLDER,
        UPLOAD_RAW_FOLDER,
        UPLOAD_VIDEOS_FOLDER,
        RESULTS_FOLDER,
        LOGS_FOLDER,
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Auto-create directories
create_directories()
