"""
Mask Beaker Module

Uses rembg on frame #2 to create beaker mask, then applies to all frames.

Process:
1. Take frame #2 (second frame - avoids blur from first frame)
2. Apply rembg to remove background
3. Extract alpha channel → binary mask
4. Apply this mask to ALL frames
5. Output: color_masked and gray_masked versions

Author: Jan 2026
"""

import os
import sys
import cv2
import numpy as np
import logging
from rembg import remove
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(('.png', '.jpg', '.jpeg'))


def create_beaker_mask(image_path):
    """
    Generate binary mask from image using rembg.
    
    Args:
        image_path: Path to image file
        
    Returns:
        numpy.ndarray: Binary mask (255=beaker, 0=background)
    """
    logger.info(f"  [REMBG] Processing: {os.path.basename(image_path)}")
    
    # Load image
    original = Image.open(image_path).convert("RGBA")
    
    # Background removal (computationally expensive - only on this frame)
    cutout = remove(original)
    
    # Extract alpha channel
    alpha = np.array(cutout.split()[-1])
    
    # Create binary mask (threshold at 10 to remove noise)
    mask = (alpha > 10).astype(np.uint8) * 255
    
    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    logger.info(f"  [MASK] Generated shape: {mask.shape}")
    
    return mask


def apply_mask_to_image(img, beaker_mask):
    """
    Apply binary mask to image (works for both color and grayscale).
    
    Args:
        img: Image to mask (color or grayscale)
        beaker_mask: Binary mask
        
    Returns:
        numpy.ndarray: Masked image
    """
    h, w = img.shape[:2]
    mh, mw = beaker_mask.shape[:2]
    
    # Resize mask if dimensions don't match
    if (mh != h) or (mw != w):
        beaker_mask = cv2.resize(beaker_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    
    # Apply mask based on image type
    if len(img.shape) == 3:  # Color image
        mask3 = cv2.merge([beaker_mask, beaker_mask, beaker_mask])
        return cv2.bitwise_and(img, mask3)
    else:  # Grayscale
        return cv2.bitwise_and(img, beaker_mask)


def process_all():
    """
    Apply beaker mask to all preprocessed frames.
    
    Process:
    - Generates mask from SECOND frame (frame[1]) to avoid blur
    - Applies mask to all frames
    - Outputs both color and grayscale masked versions
    - Production mode: deletes preprocessed originals after processing
    """
    logger.info("\n" + "="*70)
    logger.info("  MASK BEAKER")
    logger.info("="*70)
    logger.info(f"Input: {config.PREPROCESSED_FOLDER}")
    logger.info(f"Output Color: {config.COLOR_MASKED_FOLDER}")
    logger.info(f"Output Gray: {config.GRAY_MASKED_FOLDER}")
    logger.info(f"Mode: {'DEV' if config.DEV_MODE else 'PROD (delete preprocessed)'}")
    logger.info("="*70 + "\n")
    
    # Get all frames
    frames = sorted([f for f in os.listdir(config.PREPROCESSED_FOLDER) if is_image(f)])
    
    if not frames:
        logger.error("[ERROR] No preprocessed frames found")
        return
    
    if len(frames) < 2:
        logger.warning("[WARNING] Less than 2 frames! Using first frame for mask.")
        mask_frame_idx = 0
    else:
        mask_frame_idx = 1  # Use SECOND frame (index 1) to avoid blur
    
    # Generate mask from SECOND frame
    mask_frame = frames[mask_frame_idx]
    mask_frame_path = os.path.join(config.PREPROCESSED_FOLDER, mask_frame)
    
    logger.info(f"[GENERATING MASK]")
    logger.info(f"  Using frame: {mask_frame} (frame #{mask_frame_idx + 1})")
    
    beaker_mask = create_beaker_mask(mask_frame_path)
    logger.info("")
    
    # Apply mask to all frames
    processed_count = 0
    error_count = 0
    
    logger.info(f"[APPLYING MASK TO ALL FRAMES]")
    logger.info(f"  Processing {len(frames)} frames...\n")
    
    for f in frames:
        src = os.path.join(config.PREPROCESSED_FOLDER, f)
        color = cv2.imread(src)
        
        if color is None:
            logger.error(f"  [ERROR] Cannot read: {f}")
            error_count += 1
            continue
        
        try:
            # Create color masked version
            masked_color = apply_mask_to_image(color, beaker_mask)
            cv2.imwrite(os.path.join(config.COLOR_MASKED_FOLDER, f), masked_color)
            
            # Create grayscale masked version
            gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
            masked_gray = apply_mask_to_image(gray, beaker_mask)
            cv2.imwrite(os.path.join(config.GRAY_MASKED_FOLDER, f), masked_gray)
            
            processed_count += 1
            
            if processed_count % 10 == 0:
                logger.info(f"  [PROGRESS] {processed_count} frames processed...")
            
            # PRODUCTION MODE: Delete preprocessed file
            if not config.DEV_MODE:
                try:
                    os.remove(src)
                except Exception as e:
                    logger.warning(f"  [WARN] Could not delete {f}: {e}")
        
        except Exception as e:
            error_count += 1
            logger.error(f"  [ERROR] {f}: {e}")
    
    logger.info("\n" + "="*70)
    logger.info("  MASK BEAKER COMPLETE")
    logger.info("="*70)
    logger.info(f"Processed: {processed_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("="*70 + "\n")
    
    return processed_count


if __name__ == "__main__":
    # Test masking
    count = process_all()
    if count > 0:
        print(f"✅ Masked {count} frames successfully!")
    else:
        print("❌ Masking failed!")
        sys.exit(1)
