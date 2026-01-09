"""
SV30 Main Pipeline (v4.1 - Master Orchestrator)

Master script that orchestrates the complete SV30 pipeline.
Calls all modules sequentially with proper error handling.

Pipeline Stages:
1. Video capture (35 min)
2. Frame extraction (every 10 sec)
3. Preprocessing (crop x1=440, x2=1360)
4. Beaker masking (rembg on frame #2)
5. Otsu binary threshold
6. Sludge detection (top-down scan)
7. Calculate metrics (SV30%, settling rate)
8. Send to dashboard (SocketIO)
9. Upload to AWS (S3)

Author: Jan 2026
"""

import os
import sys
import time
import logging
from datetime import datetime

# Setup logging FIRST
os.makedirs("logs", exist_ok=True)
log_filename = f'logs/sv30_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import config
try:
    import sv30config as config
except ImportError:
    logger.error("❌ Cannot import sv30config.py!")
    sys.exit(1)

# Import all modules
try:
    from modules.video_capture import capture_video
    from modules.frame_extract import extract_frames
    from modules.preprocess import preprocess_frames
    from modules.mask_beaker import process_all as mask_beaker
    from modules.otsu_binary import process_all as create_otsu_binary
    from modules.sludge_detect import process_all as detect_sludge
    from modules.calculate_metrics import calculate_metrics
    from modules.send_to_dashboard import send_results
    from modules.aws_uploader import upload_to_s3
    from modules.rgb_extract import extract_rgb_values
except ImportError as e:
    logger.error(f"❌ Failed to import modules: {e}")
    sys.exit(1)


def print_banner():
    """Print startup banner"""
    logger.info("\n" + "="*70)
    logger.info("  SV30 PIPELINE v4.1")
    logger.info("="*70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: {'DEVELOPMENT' if config.DEV_MODE else 'PRODUCTION'}")
    logger.info(f"Camera: USB {config.CAM1_USB_INDEX}")
    logger.info(f"Duration: {config.VIDEO_DURATION_SEC/60:.0f} minutes")
    logger.info(f"Log file: {log_filename}")
    logger.info("="*70 + "\n")


def print_stage_header(stage_num, total_stages, stage_name):
    """Print stage header"""
    logger.info("\n" + "="*70)
    logger.info(f"  STAGE {stage_num}/{total_stages}: {stage_name}")
    logger.info("="*70)


def print_stage_complete(stage_name, duration_sec):
    """Print stage completion"""
    logger.info(f"\n✅ {stage_name} complete ({duration_sec:.1f}s)")


def main():
    """Main pipeline execution"""
    overall_start = time.time()
    
    try:
        print_banner()
        
        TOTAL_STAGES = 10
        
        # ==========================================
        # STAGE 1: VIDEO CAPTURE
        # ==========================================
        print_stage_header(1, TOTAL_STAGES, "VIDEO CAPTURE")
        stage_start = time.time()
        
        video_path = capture_video()
        if not video_path:
            logger.error("❌ Video capture failed!")
            return False
        
        print_stage_complete("Video Capture", time.time() - stage_start)
        
        # ==========================================
        # STAGE 2: FRAME EXTRACTION
        # ==========================================
        print_stage_header(2, TOTAL_STAGES, "FRAME EXTRACTION")
        stage_start = time.time()
        
        frame_count = extract_frames(video_path)
        if frame_count == 0:
            logger.error("❌ Frame extraction failed!")
            return False
        
        print_stage_complete("Frame Extraction", time.time() - stage_start)
        
        # ==========================================
        # STAGE 3: PREPROCESSING (CROP)
        # ==========================================
        print_stage_header(3, TOTAL_STAGES, "PREPROCESSING")
        stage_start = time.time()
        
        preprocessed_count = preprocess_frames()
        if preprocessed_count == 0:
            logger.error("❌ Preprocessing failed!")
            return False
        
        print_stage_complete("Preprocessing", time.time() - stage_start)
        
        # ==========================================
        # STAGE 4: BEAKER MASKING (REMBG)
        # ==========================================
        print_stage_header(4, TOTAL_STAGES, "BEAKER MASKING")
        stage_start = time.time()
        
        mask_beaker()
        
        print_stage_complete("Beaker Masking", time.time() - stage_start)
        
        # ==========================================
        # STAGE 5: OTSU BINARY THRESHOLD
        # ==========================================
        print_stage_header(5, TOTAL_STAGES, "OTSU BINARY THRESHOLD")
        stage_start = time.time()
        
        binary_count = create_otsu_binary()
        if binary_count == 0:
            logger.error("❌ Otsu thresholding failed!")
            return False
        
        print_stage_complete("Otsu Binary Threshold", time.time() - stage_start)
        
        # ==========================================
        # STAGE 6: SLUDGE DETECTION
        # ==========================================
        print_stage_header(6, TOTAL_STAGES, "SLUDGE DETECTION")
        stage_start = time.time()
        
        sludge_results = detect_sludge()
        if not sludge_results:
            logger.error("❌ Sludge detection failed!")
            return False
        
        print_stage_complete("Sludge Detection", time.time() - stage_start)
        
        # ==========================================
        # STAGE 7: RGB EXTRACTION
        # ==========================================
        
        print_stage_header(7, TOTAL_STAGES, "RGB EXTRACTION")
        stage_start = time.time()
        rgb_data = extract_rgb_values()
        if not rgb_data:
                logger.warning("??  RGB extraction failed (non-critical)")
        print_stage_complete("RGB Extraction", time.time() - stage_start)        
        
        

        
        
        
            

        
        # ==========================================
        # STAGE 7: CALCULATE METRICS
        # ==========================================
        print_stage_header(7, TOTAL_STAGES, "CALCULATE METRICS")
        stage_start = time.time()
        
        metrics = calculate_metrics()
        if not metrics:
            logger.error("❌ Metrics calculation failed!")
            return False
        
        print_stage_complete("Calculate Metrics", time.time() - stage_start)
        
        # ==========================================
        # STAGE 8: SEND TO DASHBOARD
        # ==========================================
        # NOTE: Data sending is now handled by local_server/src/services/backend_client.py
        # The sv30_pipeline should only generate results, not send them directly.
        # This prevents duplicate data sending and ensures consistent data format.
        print_stage_header(8, TOTAL_STAGES, "SEND TO DASHBOARD")
        stage_start = time.time()
        
        # DISABLED: Data sending is handled by local_server/src/services/backend_client.py
        # The test_service.py calls data_provider.generate_t30_data() which reads results
        # from this pipeline and sends them via backend_client.send_sludge_data()
        # if config.SOCKETIO_ENABLED:
        #     send_results()
        # else:
        #     logger.info("SocketIO disabled - skipping dashboard send")
        logger.info("Data sending handled by local_server/src/services/backend_client.py")
        
        print_stage_complete("Send to Dashboard", time.time() - stage_start)
        
        # ==========================================
        # STAGE 9: AWS UPLOAD
        # ==========================================
        print_stage_header(9, TOTAL_STAGES, "AWS UPLOAD")
        stage_start = time.time()
        
        if config.AWS_ENABLED:
            upload_to_s3()
        else:
            logger.info("AWS disabled - skipping upload")
        
        print_stage_complete("AWS Upload", time.time() - stage_start)
        
        # ==========================================
        # PIPELINE COMPLETE
        # ==========================================
        total_duration = time.time() - overall_start
        
        logger.info("\n" + "="*70)
        logger.info("  ✅ PIPELINE COMPLETE!")
        logger.info("="*70)
        logger.info(f"Total duration: {total_duration/60:.1f} minutes")
        logger.info(f"\nFinal Results:")
        logger.info(f"  SV30: {metrics['sv30_pct']}%")
        logger.info(f"  Mixture height: {metrics['mixture_height_mm']:.2f} mm")
        logger.info(f"  Sludge height: {metrics['sludge_height_t30_mm']:.2f} mm")
        logger.info(f"  Settling rate: {metrics['settling_rate_mm_per_min']:.4f} mm/min")
        logger.info(f"\nResults saved to: {config.RESULTS_FOLDER}")
        logger.info("="*70 + "\n")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n\n❌ Pipeline interrupted by user")
        return False
        
    except Exception as e:
        logger.error(f"\n\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
