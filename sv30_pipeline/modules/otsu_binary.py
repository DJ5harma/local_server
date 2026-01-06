"""
Otsu Binary Mask Module

Applies Otsu's automatic thresholding to gray-masked images.
Creates binary masks: WHITE=clear liquid, BLACK=sludge

Author: Jan 2026
"""

import os
import sys
import cv2
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(('.png', '.jpg', '.jpeg'))


def apply_otsu_threshold(gray_image):
    """
    Apply Otsu's automatic thresholding.
    
    Args:
        gray_image: Grayscale image
        
    Returns:
        tuple: (binary_mask, threshold_value)
            - binary_mask: Binary image (255=clear, 0=sludge)
            - threshold_value: Otsu threshold value used
    """
    # Apply Otsu's method
    threshold_value, binary_mask = cv2.threshold(
        gray_image, 
        0,           # Threshold value (ignored - Otsu calculates automatically)
        255,         # Max value
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    return binary_mask, threshold_value


def process_all():
    """
    Apply Otsu thresholding to all gray-masked frames.
    
    Process:
    - Load gray_masked images
    - Apply Otsu's automatic threshold
    - Save binary masks
    - Production mode: deletes gray_masked originals after processing
    """
    logger.info("\n" + "="*70)
    logger.info("  OTSU BINARY THRESHOLDING")
    logger.info("="*70)
    logger.info(f"Input: {config.GRAY_MASKED_FOLDER}")
    logger.info(f"Output: {config.OTSU_BINARY_FOLDER}")
    logger.info(f"Method: Otsu's automatic threshold")
    logger.info(f"Mode: {'DEV' if config.DEV_MODE else 'PROD (delete gray_masked)'}")
    logger.info("="*70 + "\n")
    
    # Get all gray_masked frames
    frames = sorted([f for f in os.listdir(config.GRAY_MASKED_FOLDER) if is_image(f)])
    
    if not frames:
        logger.error("[ERROR] No gray_masked frames found")
        return 0
    
    logger.info(f"Processing {len(frames)} frames...\n")
    
    processed_count = 0
    error_count = 0
    
    # Store threshold values for logging
    threshold_values = []
    
    for i, fname in enumerate(frames):
        src_path = os.path.join(config.GRAY_MASKED_FOLDER, fname)
        dst_path = os.path.join(config.OTSU_BINARY_FOLDER, fname)
        
        try:
            # Read grayscale image
            gray = cv2.imread(src_path, cv2.IMREAD_GRAYSCALE)
            
            if gray is None:
                logger.error(f"  [ERROR] Cannot read: {fname}")
                error_count += 1
                continue
            
            # Apply Otsu threshold
            binary_mask, threshold_value = apply_otsu_threshold(gray)
            threshold_values.append(threshold_value)
            
            # Save binary mask
            cv2.imwrite(dst_path, binary_mask)
            
            processed_count += 1
            
            # Progress
            if (i + 1) % 10 == 0:
                logger.info(f"  [PROGRESS] {i + 1}/{len(frames)} frames processed...")
            
            # Log first few thresholds
            if i < 5:
                logger.info(f"  Frame {i}: threshold = {threshold_value:.1f}")
            
            # PRODUCTION MODE: Delete gray_masked file
            if not config.DEV_MODE:
                try:
                    os.remove(src_path)
                except Exception as e:
                    logger.warning(f"  [WARN] Could not delete {fname}: {e}")
        
        except Exception as e:
            error_count += 1
            logger.error(f"  [ERROR] {fname}: {e}")
    
    # Statistics
    if threshold_values:
        import numpy as np
        avg_threshold = np.mean(threshold_values)
        min_threshold = np.min(threshold_values)
        max_threshold = np.max(threshold_values)
        
        logger.info(f"\n[THRESHOLD STATISTICS]")
        logger.info(f"  Average: {avg_threshold:.1f}")
        logger.info(f"  Range: {min_threshold:.1f} - {max_threshold:.1f}")
    
    logger.info("\n" + "="*70)
    logger.info("  OTSU BINARY THRESHOLDING COMPLETE")
    logger.info("="*70)
    logger.info(f"Processed: {processed_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("="*70 + "\n")
    
    return processed_count


if __name__ == "__main__":
    # Test Otsu thresholding
    count = process_all()
    if count > 0:
        print(f"✅ Processed {count} frames successfully!")
    else:
        print("❌ Otsu thresholding failed!")
        sys.exit(1)