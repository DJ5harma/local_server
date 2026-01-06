"""
AWS S3 Upload Module

Uploads results to S3 (same as v4).

Author: Jan 2026
"""

import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def upload_to_s3():
    """
    Upload video, results, and debug images to S3.
    
    Same S3 structure as v4.
    """
    logger.info("\n" + "="*70)
    logger.info("  AWS S3 UPLOAD")
    logger.info("="*70)
    
    # Check if AWS is enabled
    if not config.AWS_ENABLED:
        logger.info("AWS disabled in config - skipping upload")
        return False
    
    try:
        import boto3
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
        )
        
        # Generate folder name (date/test_id)
        date_str = datetime.now().strftime('%Y-%m-%d')
        test_id = f"SV30-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        s3_prefix = f"{date_str}/{test_id}/"
        
        logger.info(f"S3 Bucket: {config.AWS_BUCKET_NAME}")
        logger.info(f"S3 Prefix: {s3_prefix}\n")
        
        uploaded = []
        
        # 1. Upload video
        video_files = [f for f in os.listdir(config.UPLOAD_VIDEOS_FOLDER) if f.endswith('.mp4')]
        if video_files:
            video_file = os.path.join(config.UPLOAD_VIDEOS_FOLDER, video_files[-1])
            s3_key = f"{s3_prefix}video.mp4"
            logger.info(f"Uploading video: {video_file}")
            s3.upload_file(video_file, config.AWS_BUCKET_NAME, s3_key)
            uploaded.append(s3_key)
        
        # 2. Upload final metrics
        metrics_file = os.path.join(config.RESULTS_FOLDER, "final_metrics.json")
        if os.path.exists(metrics_file):
            s3_key = f"{s3_prefix}final_metrics.json"
            logger.info(f"Uploading metrics: {metrics_file}")
            s3.upload_file(metrics_file, config.AWS_BUCKET_NAME, s3_key)
            uploaded.append(s3_key)
        
        # 3. Upload sludge detection results
        sludge_file = os.path.join(config.RESULTS_FOLDER, "sludge_detection.json")
        if os.path.exists(sludge_file):
            s3_key = f"{s3_prefix}sludge_detection.json"
            logger.info(f"Uploading sludge results: {sludge_file}")
            s3.upload_file(sludge_file, config.AWS_BUCKET_NAME, s3_key)
            uploaded.append(s3_key)
        
        # 4. Upload debug images (if DEV_MODE)
        if config.DEV_MODE:
            debug_files = [f for f in os.listdir(config.SLUDGE_DEBUG_FOLDER) if f.endswith('.png')]
            if debug_files:
                logger.info(f"Uploading {len(debug_files)} debug images...")
                for debug_file in debug_files[:5]:  # Upload first 5 only
                    local_path = os.path.join(config.SLUDGE_DEBUG_FOLDER, debug_file)
                    s3_key = f"{s3_prefix}debug/{debug_file}"
                    s3.upload_file(local_path, config.AWS_BUCKET_NAME, s3_key)
                    uploaded.append(s3_key)
        
        logger.info(f"\n✅ Uploaded {len(uploaded)} files to S3")
        logger.info("="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] AWS upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test AWS upload
    success = upload_to_s3()
    if success:
        print("✅ AWS upload successful!")
    else:
        print("❌ AWS upload failed!")
        sys.exit(1)