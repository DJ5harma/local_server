import os

# =====================================
# ABSOLUTE BASE DIRECTORY
# =====================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# =====================================
# STAGE FOLDERS (UPDATED)
# =====================================
STAGE_INPUTS = os.path.join(BASE_DIR, "stage_inputs")

RAW_FOLDER               = os.path.join(STAGE_INPUTS, "0_raw")
PREPROCESSED_FOLDER      = os.path.join(STAGE_INPUTS, "1_preprocessed")
COLOR_MASKED_FOLDER      = os.path.join(STAGE_INPUTS, "2_color_masked")
GRAY_MASKED_FOLDER       = os.path.join(STAGE_INPUTS, "3_gray_masked")
GEOMETRY_DEBUG_FOLDER    = os.path.join(STAGE_INPUTS, "4_geometry_debug")
SLUDGE_DEBUG_FOLDER      = os.path.join(STAGE_INPUTS, "5_sludge_debug")

# Upload folder (renamed from 0.1raw)
UPLOAD_RAW_FOLDER = os.path.join(STAGE_INPUTS, "upload_raw")
UPLOAD_VIDEOS_FOLDER = os.path.join(UPLOAD_RAW_FOLDER, "videos")

# =====================================
# ARCHIVES (used in production mode)
# =====================================
ARCHIVE_ROOT = os.path.join(BASE_DIR, "archive")
ARCHIVE_RAW  = os.path.join(ARCHIVE_ROOT, "raw")
ARCHIVE_PRE  = os.path.join(ARCHIVE_ROOT, "preprocess")
ARCHIVE_MASK = os.path.join(ARCHIVE_ROOT, "masked")

# =====================================
# RESULTS + LOGS
# =====================================
RESULTS_FOLDER = os.path.join(BASE_DIR, "results")
GRAPHS_FOLDER  = os.path.join(BASE_DIR, "graphs")
LOGS_FOLDER    = os.path.join(BASE_DIR, "logs")

# =====================================
# IMAGE SETTINGS
# =====================================
IMG_EXTS = (".png", ".jpg", ".jpeg")

# =====================================
# CROP COORDINATES (ADJUST PER CAMERA)
# =====================================
CROP_X1, CROP_X2 = 1110, 1510
CROP_Y1, CROP_Y2 = 440, 1215

# =====================================
# BEAKER GEOMETRY (CENTRALIZED)
# =====================================
BEAKER_HEIGHT_MM = 214
MIXTURE_TOP_Y = 135  # Y-coordinate of mixture top in cropped image
SCAN_BOTTOM_IGNORE = 80  # Ignore bottom pixels when detecting sludge
SCAN_OFFSET = 100  # Ignore transitions too close to mixture top

# =====================================
# EXPERIMENT SETTINGS (v4.0 - UPDATED)
# =====================================
FRAME_INTERVAL_SEC = 10
VIDEO_DURATION_SEC = 35 * 60  # 35 minutes (updated from 45)
VIDEO_BUFFER_SEC = 5 * 60  # 5 minute buffer for retries

# Camera 2 snapshot timing (updated for 35-min test)
CAM2_SNAPSHOT_T1_MIN = 2   # t=2 minutes
CAM2_SNAPSHOT_T2_MIN = 33  # t=33 minutes (updated from t=40 for 35-min test)

# =====================================
# RGB ANALYSIS POINTS (for cam2)
# =====================================
RGB_TOP_POINT = (1330, 810)
RGB_BOTTOM_POINT = (1330, 1280)
RGB_PATCH_SIZE = 5

# =====================================
# CAMERA SETTINGS (v4.0 - USB + RTSP SUPPORT)
# =====================================
# Camera 1 - Main video camera
CAM1_TYPE = "USB"  # "USB" or "RTSP"

# USB Camera settings (for CAM1_TYPE="USB")
CAM1_USB_INDEX = 0  # Device index (0, 1, 2, etc.) or device path like "/dev/video0"
CAM1_USB_WIDTH = 1920  # Resolution width
CAM1_USB_HEIGHT = 1080  # Resolution height
CAM1_USB_FPS = 30  # Frames per second
CAM1_USB_FOURCC = "MJPG"  # Codec: "MJPG" or "YUYV" (MJPG is faster)

# RTSP Camera settings (for CAM1_TYPE="RTSP" - legacy support)
CAM1_URL = "rtsp://admin:Autonex2025@192.168.1.101:554/cam/realmonitor?channel=1"

# Camera 2 - RGB camera for snapshots (RTSP only)
CAM2_URL = "rtsp://admin:Autonex2025@192.168.1.102:554/cam/realmonitor?channel=1"

# Camera adjustments (set if needed)
CAM1_ROTATE = None  # e.g., cv2.ROTATE_90_CLOCKWISE
CAM2_ROTATE = None
CAM1_FLIP = None    # 0=vertical, 1=horizontal, -1=both
CAM2_FLIP = None

# =====================================
# DEV MODE
# =====================================
DEV_MODE = True  # Set to False for production (progressive cleanup)

# =====================================
# CAPTURE ONLY MODE (NEW in v3.0)
# =====================================
# When True: Only capture video + snapshots, upload to AWS, then shutdown
# When False: Full pipeline (capture + process + results + upload + shutdown)
CAPTURE_ONLY_MODE = False  # Set to True to only capture and backup raw data

# =====================================
# AUTO SHUTDOWN (NEW in v3.0)
# =====================================
# Automatically shutdown Raspberry Pi after completing the pipeline
AUTO_SHUTDOWN_ENABLED = True  # Set to False to prevent shutdown
SHUTDOWN_DELAY_SEC = 10  # Wait 10 seconds before shutdown

# =====================================
# HMI INTEGRATION (NEW in v4.0)
# =====================================
HMI_ENABLED = True  # Enable HMI server integration
HMI_HOST = "0.0.0.0"  # Listen on all interfaces
HMI_PORT = 5000  # HMI web server port
HMI_PASSWORD = "thermax"  # Login password for HMI
HMI_AUTO_START = True  # Auto-start HMI server with main pipeline

# =====================================
# MODBUS SETTINGS
# =====================================
MODBUS_ENABLED = True
MODBUS_HOST = "0.0.0.0"
MODBUS_PORT = 5020

# =====================================
# AWS S3 SETTINGS
# =====================================
AWS_ENABLED = False  # Enable after configuration

# AWS Credentials (DO NOT COMMIT TO GIT!)
# Recommended: Use environment variables or AWS credentials file
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = "ap-south-1"  # Mumbai region (change if needed)

# S3 Bucket Configuration
AWS_S3_BUCKET = "sv30-test-data"  # Change to your bucket name
AWS_S3_PREFIX = "sv30_tests"  # Folder prefix in bucket

# Upload settings
AWS_UPLOAD_VIDEO = True  # Upload raw video
AWS_UPLOAD_IMAGES = True  # Upload Camera 2 snapshots
AWS_UPLOAD_RESULTS = True  # Upload JSON results and graphs
AWS_DELETE_AFTER_UPLOAD = True  # Delete local files after successful upload (production)

# Retry settings
AWS_MAX_RETRIES = 5
AWS_RETRY_DELAY_SEC = 30

# =====================================
# VIDEO RECORDING SETTINGS
# =====================================
VIDEO_CODEC = "copy"  # Use 'copy' for no re-encoding (faster, smaller)
VIDEO_FORMAT = "mp4"
VIDEO_RTSP_TRANSPORT = "tcp"  # tcp or udp (tcp is more reliable)

# =====================================
# SOCKET.IO SETTINGS (for dashboard)
# =====================================
SOCKETIO_ENABLED = False  # Set to True to enable real-time dashboard
SOCKETIO_URL = "https://noble-liberation-production-db43.up.railway.app"  # Production backend
# SOCKETIO_URL = "http://localhost:4000"  # Use this for local testing

# =====================================
# AUTO CREATE ALL FOLDERS
# =====================================
for folder in [
    RAW_FOLDER,
    UPLOAD_RAW_FOLDER,
    UPLOAD_VIDEOS_FOLDER,
    PREPROCESSED_FOLDER,
    COLOR_MASKED_FOLDER,
    GRAY_MASKED_FOLDER,
    GEOMETRY_DEBUG_FOLDER,
    SLUDGE_DEBUG_FOLDER,
    ARCHIVE_ROOT,
    ARCHIVE_RAW,
    ARCHIVE_PRE,
    ARCHIVE_MASK,
    RESULTS_FOLDER,
    GRAPHS_FOLDER,
    LOGS_FOLDER,
]:
    os.makedirs(folder, exist_ok=True)

# =====================================
# NEW DETECTION ALGORITHM PARAMETERS (v2.0)
# =====================================
# Mixture top detection
MIXTURE_TOP_SEARCH_REGION = 0.6  # Search in top 60% of image

# Sludge interface detection
MIN_SLUDGE_DISTANCE_PX = 20  # Minimum distance below mixture_top
MAX_SEARCH_DEPTH_PCT = 85  # Don't search in bottom 15%
NUM_SCAN_LINES = 10  # Number of vertical scan lines
BLACK_PIXELS_REQUIRED = 10  # Consecutive black pixels needed

# Outlier rejection
OUTLIER_THRESHOLD_EXTREME = 100  # Stage 1: pixels
OUTLIER_THRESHOLD_MODERATE = 20  # Stage 2: pixels

# =====================================
# SYSTEM WORKFLOW SETTINGS
# =====================================
# Camera check
CAMERA_CHECK_ENABLED = True
CAMERA_CHECK_TIMEOUT_SEC = 10

# Data archiving
ARCHIVE_ENABLED = True  # Archive old data before new test
ARCHIVE_FORMAT = "%Y%m%d_%H%M%S"  # Dated folder format

# Test execution
RUN_ONCE_PER_BOOT = True  # Only run once after boot
BOOT_MARKER_FILE = "/tmp/sv30_test_completed"  # Marker file

# Retry settings
TEST_RETRY_ENABLED = True
TEST_RETRY_WINDOW_MIN = 5  # 5-minute retry window
TEST_RETRY_INTERVAL_SEC = 30  # Check every 30 seconds

# =====================================
# FACTORY SETTINGS (for dashboard)
# =====================================
FACTORY_CODE = "factory-a"  # Change to your factory code
FACTORY_LOCATION = "Mumbai"  # Optional

# Test timing (for dashboard)
MORNING_TEST_HOUR = 6  # 6:00 AM
AFTERNOON_TEST_HOUR = 14  # 2:00 PM
EVENING_TEST_HOUR = 22  # 10:00 PM

# =====================================
# DASHBOARD NOTIFICATION SETTINGS
# =====================================
SEND_TEST_START_NOTIFICATION = True  # Notify when test starts
SEND_TEST_COMPLETE_NOTIFICATION = True  # Notify when test completes
SEND_PROGRESS_UPDATES = True  # Send sludge-height-update during test
PROGRESS_UPDATE_INTERVAL_SEC = 10  # Update every 10 seconds
