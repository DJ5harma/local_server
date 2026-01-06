"""
Tight Crop Module - Beaker Extraction

Uses rembg on frame #2 to find beaker position, then crops all frames to that region.

Process:
1. Load frame #2 (not blurred)
2. Apply rembg to remove background
3. Find bounding box of beaker
4. Apply same crop to ALL frames

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


def find_beaker_bounds_from_frame2():
    """
    Load frame #2, apply rembg, find beaker bounding box.
    
    Returns:
        tuple: (x1, y1, x2, y2) crop coordinates, or None if failed
    """
    logger.info("="*70)
    logger.info("  FINDING BEAKER POSITION (Frame #2)")
    logger.info("="*70)
    
    # Get frame #2 (second frame in sorted list)
    frames = sorted([f for f in os.listdir(config.PREPROCESSED_FOLDER) 
                    if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    if len(frames) < 2:
        logger.error("❌ Not enough frames! Need at least 2 frames.")
        return None
    
    frame2_name = frames[1]  # Index 1 = second frame
    frame2_path = os.path.join(config.PREPROCESSED_FOLDER, frame2_name)
    
    logger.info(f"Reference frame: {frame2_name}")
    
    # Load image
    img = cv2.imread(frame2_path)
    if img is None:
        logger.error(f"❌ Cannot read frame: {frame2_name}")
        return None
    
    logger.info(f"Original size: {img.shape[1]}x{img.shape[0]}")
    
    # Convert to PIL for rembg
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    
    # Apply rembg
    logger.info("Applying rembg to remove background...")
    output_pil = remove(img_pil)
    
    # Convert back to OpenCV
    output = cv2.cvtColor(np.array(output_pil), cv2.COLOR_RGBA2BGRA)
    
    # Extract alpha channel (transparency = beaker mask)
    alpha = output[:, :, 3]
    
    # Find non-zero pixels (where beaker exists)
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        logger.error("❌ No beaker found in frame after rembg!")
        return None
    
    # Get bounding box
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    
    # Add small margin (5 pixels)
    margin = 5
    h, w = img.shape[:2]
    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(w, x2 + margin)
    y2 = min(h, y2 + margin)
    
    crop_width = x2 - x1
    crop_height = y2 - y1
    
    logger.info(f"\n✅ Beaker found!")
    logger.info(f"   Bounding box: ({x1}, {y1}) to ({x2}, {y2})")
    logger.info(f"   Crop size: {crop_width}x{crop_height}")
    logger.info("="*70 + "\n")
    
    return (x1, y1, x2, y2)


def apply_tight_crop_to_all(crop_coords):
    """
    Apply tight crop coordinates to all preprocessed frames.
    
    Args:
        crop_coords: Tuple of (x1, y1, x2, y2)
        
    Returns:
        int: Number of frames processed
    """
    if crop_coords is None:
        logger.error("❌ No crop coordinates provided!")
        return 0
    
    x1, y1, x2, y2 = crop_coords
    
    logger.info("="*70)
    logger.info("  APPLYING TIGHT CROP TO ALL FRAMES")
    logger.info("="*70)
    logger.info(f"Input: {config.PREPROCESSED_FOLDER}")
    logger.info(f"Output: {config.TIGHT_CROPPED_FOLDER}")
    logger.info(f"Crop: ({x1},{y1}) to ({x2},{y2})")
    logger.info("="*70 + "\n")
    
    # Get all frames
    frames = sorted([f for f in os.listdir(config.PREPROCESSED_FOLDER) 
                    if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    logger.info(f"Processing {len(frames)} frames...\n")
    
    processed = 0
    errors = 0
    
    for i, fname in enumerate(frames):
        src_path = os.path.join(config.PREPROCESSED_FOLDER, fname)
        dst_path = os.path.join(config.TIGHT_CROPPED_FOLDER, fname)
        
        try:
            # Read image
            img = cv2.imread(src_path)
            if img is None:
                logger.error(f"  ❌ Cannot read: {fname}")
                errors += 1
                continue
            
            # Apply tight crop
            cropped = img[y1:y2, x1:x2]
            
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
    logger.info("  TIGHT CROP COMPLETE")
    logger.info("="*70)
    logger.info(f"Processed: {processed}")
    logger.info(f"Errors: {errors}")
    logger.info("="*70 + "\n")
    
    return processed


def create_tight_cropped_frames():
    """
    Main function: Find beaker bounds from frame 2, then crop all frames.
    
    Returns:
        bool: True if successful
    """
    # Step 1: Find beaker position from frame 2
    crop_coords = find_beaker_bounds_from_frame2()
    
    if crop_coords is None:
        logger.error("❌ Failed to find beaker bounds!")
        return False
    
    # Step 2: Apply to all frames
    processed = apply_tight_crop_to_all(crop_coords)
    
    if processed == 0:
        logger.error("❌ No frames processed!")
        return False
    
    logger.info(f"✅ Successfully created {processed} tight-cropped frames")
    return True


if __name__ == "__main__":
    # Test tight crop
    success = create_tight_cropped_frames()
    if success:
        print("✅ Tight crop test successful!")
    else:
        print("❌ Tight crop test failed!")
        sys.exit(1)