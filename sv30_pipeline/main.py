"""
SV30 Main Pipeline (v4.0 - USB Camera + HMI Integration)

Two Operating Modes:
  1. CAPTURE_ONLY_MODE = True:
     - Capture 35-min video + snapshots at t=2, t=33
     - Upload RAW data to AWS
     - Send dashboard notifications
     - Shutdown Raspberry Pi
  
  2. CAPTURE_ONLY_MODE = False:
     - Capture 35-min video + snapshots
     - Process (extract → detect → metrics → graphs)
     - Upload everything to AWS
     - Send complete results to dashboard
     - Shutdown Raspberry Pi

Author: Updated Dec 2024
"""

import sys
import time
import os
from datetime import datetime

# Import all modules
from modules.camera_check import check_camera_connectivity
from modules.archiver import archive_old_data, check_previous_upload_status
from modules.video_capture import capture_video_and_snapshots
from modules.frame_extractor import extract_frames_from_video
from modules.preprocess import run_batch as preprocess_batch
from modules.mask_beaker import process_all as mask_batch
from modules.sludge_detect import run_batch as sludge_mask_batch
from modules.detect_geometry import run_batch as geometry_batch
from modules.sv30metrics import (
    run_stage as metrics_batch,
    get_final_metrics
)
from modules.rgb_analysis import (
    run_rgb_analysis,
    get_rgb_results
)
from modules.graph_generator import generate_graphs
from modules.aws_uploader import upload_test_data
from modules.socketio_client import (
    connect_socketio,
    send_sludge_data,
    send_test_warning,
    disconnect_socketio
)
from modules.system_shutdown import shutdown_system, test_shutdown_permissions

from sv30config import (
    MODBUS_ENABLED,
    AWS_ENABLED,
    DEV_MODE,
    SOCKETIO_ENABLED,
    UPLOAD_RAW_FOLDER,
    UPLOAD_VIDEOS_FOLDER,
    RESULTS_FOLDER,
    GRAPHS_FOLDER,
    CAMERA_CHECK_ENABLED,
    ARCHIVE_ENABLED,
    RUN_ONCE_PER_BOOT,
    BOOT_MARKER_FILE,
    CAPTURE_ONLY_MODE,
    AUTO_SHUTDOWN_ENABLED,
    SHUTDOWN_DELAY_SEC,
    CAM2_SNAPSHOT_T1_MIN,
    CAM2_SNAPSHOT_T2_MIN,
    VIDEO_DURATION_SEC,
)
from modbus_server import start_in_thread, write_register

# =====================
# BOOT CHECK
# =====================
def check_boot_marker():
    """Check if test has already run after this boot"""
    if not RUN_ONCE_PER_BOOT:
        return False
    
    if os.path.exists(BOOT_MARKER_FILE):
        print("\n" + "="*60)
        print("  TEST ALREADY COMPLETED THIS BOOT")
        print("="*60)
        print(f"Marker file exists: {BOOT_MARKER_FILE}")
        print("Reboot the system to run another test")
        print("="*60 + "\n")
        return True
    
    return False

def create_boot_marker():
    """Create marker file to indicate test completed"""
    if RUN_ONCE_PER_BOOT:
        try:
            with open(BOOT_MARKER_FILE, 'w') as f:
                f.write(datetime.now().isoformat())
            print(f"\n[BOOT] Created marker file: {BOOT_MARKER_FILE}")
        except Exception as e:
            print(f"\n[WARN] Could not create boot marker: {e}")

# =====================
# MODBUS PUSH FUNCTION
# =====================
def push_results_to_modbus(payload):
    """Push final results to Modbus registers"""
    try:
        sv30_scaled = int(payload["sv30"] * 100)
        velocity_scaled = int(payload["velocity"] * 10000)
        duration = payload["duration_min"]
        epoch = payload["epoch"]
        
        epoch_hi = (epoch >> 16) & 0xFFFF
        epoch_lo = epoch & 0xFFFF
        
        write_register(40001, sv30_scaled)
        write_register(40002, velocity_scaled)
        write_register(40003, duration)
        write_register(40004, epoch_hi)
        write_register(40005, epoch_lo)
        
        print(f"\n[MODBUS] Results pushed successfully")
        print(f"  SV30: {payload['sv30']:.2f}% (reg={sv30_scaled})")
        print(f"  Velocity: {payload['velocity']:.6f} %/sec (reg={velocity_scaled})")
        print(f"  Duration: {duration} min")
        print(f"  Epoch: {epoch} (HI={epoch_hi}, LO={epoch_lo})\n")
    except Exception as e:
        print(f"[ERROR] Failed to push to Modbus: {e}")

# =====================
# CAPTURE ONLY MODE
# =====================
def run_capture_only():
    """
    CAPTURE ONLY MODE
    
    Workflow:
    1. Capture 35-min video + snapshots (t=2, t=33)
    2. Upload RAW video + snapshots to AWS
    3. Send dashboard notifications
    4. Shutdown Raspberry Pi
    """
    print("\n" + "="*70)
    print(" "*15 + "SV30 CAPTURE ONLY MODE (v3.0)")
    print("="*70)
    print(f"Mode: CAPTURE + UPLOAD + SHUTDOWN")
    print(f"Duration: {VIDEO_DURATION_SEC/60:.0f} minutes")
    print(f"Snapshots: t={CAM2_SNAPSHOT_T1_MIN} min, t={CAM2_SNAPSHOT_T2_MIN} min")
    print(f"AWS Upload: {'ENABLED' if AWS_ENABLED else 'DISABLED'}")
    print(f"Dashboard: {'ENABLED' if SOCKETIO_ENABLED else 'DISABLED'}")
    print("="*70 + "\n")
    
    test_id = datetime.now().strftime("%d%m%y_%H%M%S") + "test1"
    
    # Connect to dashboard
    socketio_client = None
    if SOCKETIO_ENABLED:
        print("[STAGE 1/4] Connecting to dashboard...")
        socketio_client = connect_socketio()
    
    # Send test start notification
    if SOCKETIO_ENABLED and socketio_client:
        send_sludge_data(
            t_min=CAM2_SNAPSHOT_T1_MIN,
            sludge_height_mm=0,
            mixture_height_mm=0,
            test_id=test_id
        )
    
    # Capture video + snapshots
    print(f"[STAGE 2/4] Capturing {VIDEO_DURATION_SEC/60:.0f}-minute video...")
    success, video_path = capture_video_and_snapshots()
    
    if not success:
        print("\n[FATAL ERROR] Video capture failed!")
        if SOCKETIO_ENABLED and socketio_client:
            send_test_warning(
                message="Video capture failed in CAPTURE_ONLY mode",
                error_details="Could not capture video. Check cameras."
            )
        return False
    
    # Send capture complete notification
    if SOCKETIO_ENABLED and socketio_client:
        send_sludge_data(
            t_min=CAM2_SNAPSHOT_T2_MIN,
            sludge_height_mm=0,
            mixture_height_mm=0,
            test_id=test_id
        )
    
    # Upload to AWS
    if AWS_ENABLED:
        print(f"\n[STAGE 3/4] Uploading RAW data to AWS S3...")
        cam2_t2 = os.path.join(UPLOAD_RAW_FOLDER, "cam2_t2.jpg")
        cam2_t33 = os.path.join(UPLOAD_RAW_FOLDER, "cam2_t33.jpg")
        
        success, summary = upload_test_data(
            video_path=video_path,
            test_id=test_id,
            cam2_t0_path=cam2_t2,
            cam2_t30_path=cam2_t33,
            results_folder=None,  # No results in capture mode
            graphs_folder=None
        )
        
        if success:
            print("[AWS] ✅ Video uploaded successfully")
        else:
            print("[AWS] ⚠️  Upload failed")
    
    # Disconnect dashboard
    if SOCKETIO_ENABLED and socketio_client:
        disconnect_socketio()
    
    print("\n" + "="*70)
    print(" "*20 + "CAPTURE COMPLETE")
    print("="*70)
    print(f"Test ID: {test_id}")
    print(f"Video: {video_path}")
    print(f"AWS: {'Uploaded' if AWS_ENABLED and success else 'Not uploaded'}")
    print("="*70 + "\n")
    
    # Create boot marker
    create_boot_marker()
    
    return True

# =====================
# FULL PIPELINE MODE
# =====================
def run_full_pipeline():
    """
    FULL PIPELINE MODE
    
    Workflow:
    1. Camera check
    2. Archive old data
    3. Capture 35-min video + snapshots
    4. Process (extract → detect → metrics → graphs)
    5. Upload everything to AWS
    6. Send results to dashboard
    7. Shutdown Raspberry Pi
    """
    print("\n" + "="*70)
    print(" "*15 + "SV30 FULL PIPELINE MODE (v3.0)")
    print("="*70)
    print(f"Mode: {'DEVELOPMENT' if DEV_MODE else 'PRODUCTION'}")
    print(f"Duration: {VIDEO_DURATION_SEC/60:.0f} minutes")
    print(f"Modbus: {'ENABLED' if MODBUS_ENABLED else 'DISABLED'}")
    print(f"AWS: {'ENABLED' if AWS_ENABLED else 'DISABLED'}")
    print(f"Dashboard: {'ENABLED' if SOCKETIO_ENABLED else 'DISABLED'}")
    print("="*70 + "\n")
    
    test_id = datetime.now().strftime("%d%m%y_%H%M%S") + "test1"
    
    # Camera check
    if CAMERA_CHECK_ENABLED:
        print("[STAGE 1/15] Checking cameras...")
        cam1_ok, cam2_ok = check_camera_connectivity()
        if not (cam1_ok and cam2_ok):
            print("\n[FATAL ERROR] Camera check failed!")
            return False
    
    # Archive old data
    socketio_client = None
    if ARCHIVE_ENABLED:
        print("[STAGE 2/15] Archiving previous data...")
        archive_success, archive_path, had_data = archive_old_data()
        
        if had_data:
            upload_status = check_previous_upload_status(archive_path)
            if upload_status['warning_needed']:
                print(f"\n[WARNING] Previous data not uploaded!")
                if SOCKETIO_ENABLED:
                    temp_client = connect_socketio()
                    if temp_client:
                        send_test_warning(
                            test_type=upload_status['test_type'],
                            message=f"Previous {upload_status['test_type']} test data not uploaded",
                            error_details=f"Archive: {archive_path}"
                        )
                        disconnect_socketio()
    
    # Start Modbus
    if MODBUS_ENABLED:
        print("[STAGE 3/15] Starting Modbus server...")
        start_in_thread()
        time.sleep(1)
    
    # Connect to dashboard
    if SOCKETIO_ENABLED:
        print("[STAGE 4/15] Connecting to dashboard...")
        socketio_client = connect_socketio()
    
    # Send test start
    if SOCKETIO_ENABLED and socketio_client:
        send_sludge_data(
            t_min=CAM2_SNAPSHOT_T1_MIN,
            sludge_height_mm=0,
            mixture_height_mm=0,
            test_id=test_id
        )
    
    # Capture video
    print(f"[STAGE 5/15] Capturing {VIDEO_DURATION_SEC/60:.0f}-minute video...")
    success, video_path = capture_video_and_snapshots()
    
    if not success:
        print("\n[FATAL ERROR] Video capture failed!")
        if SOCKETIO_ENABLED and socketio_client:
            send_test_warning(message="Video capture failed", error_details="Check cameras")
        return False
    
    # Extract frames
    print("[STAGE 6/15] Extracting frames...")
    success, frame_count, error = extract_frames_from_video(video_path)
    if not success:
        print(f"\n[FATAL ERROR] Frame extraction failed: {error}")
        return False
    
    # Process frames
    print("[STAGE 7/15] Preprocessing...")
    preprocess_batch()
    
    print("[STAGE 8/15] Masking...")
    mask_batch()
    
    print("[STAGE 9/15] Detecting sludge (v2.0)...")
    sludge_mask_batch()
    
    print("[STAGE 10/15] Detecting geometry...")
    geometry_batch()
    
    # Calculate metrics
    print("[STAGE 11/15] Calculating metrics...")
    metrics_batch()
    
    # RGB analysis
    print("[STAGE 12/15] Analyzing RGB...")
    run_rgb_analysis()
    
    # Generate graphs
    print("[STAGE 13/15] Generating graphs...")
    generate_graphs()
    
    # Get results
    metrics = get_final_metrics()
    rgb = get_rgb_results()
    
    if metrics is None:
        print("[ERROR] No metrics generated!")
        return False
    
    payload = {
        "test_id": test_id,
        "sv30": metrics["sv30_pct"],
        "velocity": metrics["avg_velocity"],
        "duration_min": VIDEO_DURATION_SEC / 60,
        "epoch": int(time.time()),
        "rgb": rgb
    }
    
    # Send to dashboard
    if SOCKETIO_ENABLED and socketio_client:
        print("\n[STAGE 14/15] Sending results to dashboard...")
        send_sludge_data(
            t_min=CAM2_SNAPSHOT_T2_MIN,
            sludge_height_mm=metrics.get("sludge_height_mm", 0),
            mixture_height_mm=metrics.get("mixture_height_mm", 0),
            sv30_mL_per_L=metrics["sv30_pct"] * 10,
            velocity_mm_per_min=metrics["avg_velocity"],
            rgb_clear_zone=rgb.get("clear_zone"),
            rgb_sludge_zone=rgb.get("sludge_zone"),
            test_id=test_id
        )
    
    # Upload to AWS
    if AWS_ENABLED:
        print("\n[STAGE 15/15] Uploading to AWS S3...")
        cam2_t2 = os.path.join(UPLOAD_RAW_FOLDER, "cam2_t2.jpg")
        cam2_t33 = os.path.join(UPLOAD_RAW_FOLDER, "cam2_t33.jpg")
        
        success, summary = upload_test_data(
            video_path=video_path,
            test_id=test_id,
            cam2_t0_path=cam2_t2,
            cam2_t30_path=cam2_t33,
            results_folder=RESULTS_FOLDER,
            graphs_folder=GRAPHS_FOLDER
        )
    
    # Push to Modbus
    if MODBUS_ENABLED:
        push_results_to_modbus(payload)
    
    # Results
    print("\n" + "="*70)
    print(" "*25 + "PIPELINE COMPLETE")
    print("="*70)
    print(f"Test ID: {test_id}")
    print(f"SV30: {payload['sv30']:.2f}%")
    print(f"Velocity: {payload['velocity']:.6f} %/sec")
    print(f"AWS: {'Uploaded' if AWS_ENABLED else 'Disabled'}")
    print("="*70 + "\n")
    
    # Disconnect dashboard
    if SOCKETIO_ENABLED and socketio_client:
        disconnect_socketio()
    
    # Create boot marker
    create_boot_marker()
    
    return True

# =====================
# MAIN ENTRY POINT
# =====================
if __name__ == "__main__":
    try:
        # Check boot marker
        if check_boot_marker():
            sys.exit(0)
        
        # Check shutdown permissions
        if AUTO_SHUTDOWN_ENABLED:
            if not test_shutdown_permissions():
                print("\n⚠️  WARNING: No shutdown permissions!")
                print("Auto-shutdown is enabled but won't work without permissions")
                print("To fix: sudo visudo")
                print("Add: pi ALL=(ALL) NOPASSWD: /sbin/shutdown\n")
        
        # Run appropriate mode
        if CAPTURE_ONLY_MODE:
            print("\n🎥 Running in CAPTURE ONLY mode")
            success = run_capture_only()
        else:
            print("\n⚙️  Running in FULL PIPELINE mode")
            success = run_full_pipeline()
        
        # Shutdown if enabled
        if success and AUTO_SHUTDOWN_ENABLED:
            shutdown_system(SHUTDOWN_DELAY_SEC)
        elif success:
            print("\n✅ Pipeline completed successfully!")
            print("Auto-shutdown is disabled in config\n")
        else:
            print("\n❌ Pipeline failed!")
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Pipeline stopped by user")
        disconnect_socketio()
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n[FATAL ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            from modules.socketio_client import connect_socketio, send_test_warning, disconnect_socketio
            client = connect_socketio()
            if client:
                send_test_warning(
                    message="Pipeline crashed with unexpected error",
                    error_details=str(e)
                )
                disconnect_socketio()
        except:
            pass
        
        sys.exit(1)
