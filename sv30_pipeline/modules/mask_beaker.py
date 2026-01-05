import os
import cv2
import numpy as np
from rembg import remove
from PIL import Image
from sv30config import (
    PREPROCESSED_FOLDER,
    COLOR_MASKED_FOLDER,
    GRAY_MASKED_FOLDER,
    IMG_EXTS,
    DEV_MODE,
)

def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(IMG_EXTS)

def create_beaker_mask(first_image_path):
    """
    Generate binary mask from first preprocessed image using rembg
    - Removes background
    - Creates binary mask from alpha channel
    - Applies morphological closing to cleanup
    """
    print(f"  [REMBG] Processing: {os.path.basename(first_image_path)}")
    
    original = Image.open(first_image_path).convert("RGBA")
    
    # Background removal (computationally expensive - only on first frame)
    cutout = remove(original)
    
    # Extract alpha channel
    alpha = np.array(cutout.split()[-1])
    
    # Create binary mask (threshold at 10 to remove noise)
    mask = (alpha > 10).astype(np.uint8) * 255
    
    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    print(f"  [MASK] Generated shape: {mask.shape}")
    return mask

def apply_mask_to_image(img, beaker_mask):
    """
    Apply binary mask to image (works for both color and grayscale)
    - Handles size mismatches by resizing mask
    - Returns masked image
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
    Apply beaker mask to all preprocessed frames
    - Generates mask from first frame only
    - Applies to all frames
    - Outputs both color and grayscale masked versions
    - Production mode: deletes preprocessed originals after processing
    """
    print(f"\n" + "="*60)
    print("  MASK BEAKER")
    print("="*60)
    print(f"Input: {PREPROCESSED_FOLDER}")
    print(f"Output Color: {COLOR_MASKED_FOLDER}")
    print(f"Output Gray: {GRAY_MASKED_FOLDER}")
    print(f"Mode: {'DEV' if DEV_MODE else 'PROD (delete preprocessed)'}")
    print("="*60 + "\n")
    
    frames = sorted([f for f in os.listdir(PREPROCESSED_FOLDER) if is_image(f)])
    
    if not frames:
        print("[ERROR] No preprocessed frames found")
        return
    
    # Generate mask from FIRST frame
    first = frames[0]
    first_path = os.path.join(PREPROCESSED_FOLDER, first)
    print(f"[GENERATING MASK]")
    beaker_mask = create_beaker_mask(first_path)
    print()
    
    # Apply mask to all frames
    processed_count = 0
    error_count = 0
    
    for f in frames:
        src = os.path.join(PREPROCESSED_FOLDER, f)
        color = cv2.imread(src)
        
        if color is None:
            print(f"  [ERROR] Cannot read: {f}")
            error_count += 1
            continue
        
        try:
            # Create color masked version
            masked_color = apply_mask_to_image(color, beaker_mask)
            cv2.imwrite(os.path.join(COLOR_MASKED_FOLDER, f), masked_color)
            
            # Create grayscale masked version
            gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
            masked_gray = apply_mask_to_image(gray, beaker_mask)
            cv2.imwrite(os.path.join(GRAY_MASKED_FOLDER, f), masked_gray)
            
            processed_count += 1
            
            if processed_count % 10 == 0:
                print(f"  [PROGRESS] {processed_count} frames processed...")
            
            # PRODUCTION MODE: Delete preprocessed file
            if not DEV_MODE:
                try:
                    os.remove(src)
                except Exception as e:
                    print(f"  [WARN] Could not delete {f}: {e}")
        
        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {f}: {e}")
    
    print(f"\n" + "="*60)
    print("  MASK BEAKER COMPLETE")
    print("="*60)
    print(f"Processed: {processed_count}")
    print(f"Errors: {error_count}")
    print("="*60 + "\n")

if __name__ == "__main__":
    process_all()
