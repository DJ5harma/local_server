"""
Preprocessing Module - Crop Frames

Crops frames to region of interest: x1=440, x2=1360

Author: Jan 2026
"""

import os
import sys
import cv2
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def preprocess_frames():
    """
    Crop all frames to region of interest.
    
    Crops from (CROP_X1, CROP_Y1) to (CROP_X2, CROP_Y2)
    """
    logger.info("="*70)
    logger.info("  PREPROCESSING - Crop Frames")
    logger.info("="*70)
    logger.info(f"Input: {config.RAW_FOLDER}")
    logger.info(f"Output: {config.PREPROCESSED_FOLDER}")
    logger.info(f"Crop region: ({config.CROP_X1},{config.CROP_Y1}) to ({config.CROP_X2},{config.CROP_Y2})")
    logger.info("="*70 + "\n")
    
    # Get all frames
    frames = sorted([f for f in os.listdir(config.RAW_FOLDER) 
                    if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    if not frames:
        logger.warning("⚠️  No frames found to preprocess")
        return 0
    
    logger.info(f"Processing {len(frames)} frames...\n")
    
    processed = 0
    errors = 0
    
    for i, fname in enumerate(frames):
        src_path = os.path.join(config.RAW_FOLDER, fname)
        dst_path = os.path.join(config.PREPROCESSED_FOLDER, fname)
        
        try:
            # Read image
            img = cv2.imread(src_path)
            if img is None:
                logger.error(f"  ❌ Cannot read: {fname}")
                errors += 1
                continue
            
            # Crop
            cropped = img[config.CROP_Y1:config.CROP_Y2, config.CROP_X1:config.CROP_X2]
            
            # Save
            cv2.imwrite(dst_path, cropped)
            processed += 1
            
            # Progress
            if (i + 1) % 10 == 0:
                logger.info(f"  Processed {i + 1}/{len(frames)} frames...")
        
        except Exception as e:
            logger.error(f"  ❌ Error processing {fname}: {e}")
            errors += 1
    
    logger.info("\n" + "="*70)
    logger.info("  PREPROCESSING COMPLETE")
    logger.info("="*70)
    logger.info(f"Processed: {processed}")
    logger.info(f"Errors: {errors}")
    logger.info("="*70 + "\n")
    
    return processed


if __name__ == "__main__":
    # Test preprocessing
    count = preprocess_frames()
    print(f"✅ Processed {count} frames")
    