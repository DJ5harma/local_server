import os
import cv2
import gc
from sv30config import (
    RAW_FOLDER,
    PREPROCESSED_FOLDER,
    CROP_X1, CROP_X2,
    CROP_Y1, CROP_Y2,
    IMG_EXTS,
    DEV_MODE,
)

def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(IMG_EXTS)

def preprocess_single(src_path, dst_path):
    """
    Crop a single image to beaker region
    - Loads image
    - Applies strict crop using configured coordinates
    - Saves as PNG for consistency
    """
    img = cv2.imread(src_path)
    if img is None:
        raise ValueError(f"Failed loading image: {src_path}")
    
    h, w = img.shape[:2]
    
    # Apply strict crop with bounds checking
    x1 = max(0, min(CROP_X1, w))
    x2 = max(0, min(CROP_X2, w))
    y1 = max(0, min(CROP_Y1, h))
    y2 = max(0, min(CROP_Y2, h))
    
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Invalid crop coordinates: x1={x1}, x2={x2}, y1={y1}, y2={y2}")
    
    cropped = img[y1:y2, x1:x2]
    
    # Save cropped image
    cv2.imwrite(dst_path, cropped)
    
    # Memory cleanup
    del img, cropped
    gc.collect()

def run_batch():
    """
    Process all images in RAW_FOLDER
    
    Behavior:
    - DEV_MODE=True: keeps originals in place
    - DEV_MODE=False: deletes each original after processing
    """
    print(f"\n" + "="*60)
    print("  PREPROCESS (CROP)")
    print("="*60)
    print(f"Input: {RAW_FOLDER}")
    print(f"Output: {PREPROCESSED_FOLDER}")
    print(f"Crop region: ({CROP_X1},{CROP_Y1}) to ({CROP_X2},{CROP_Y2})")
    print(f"Mode: {'DEV (keep originals)' if DEV_MODE else 'PROD (delete originals)'}")
    print("="*60 + "\n")
    
    files = sorted(os.listdir(RAW_FOLDER))
    processed_count = 0
    error_count = 0
    
    for f in files:
        if not is_image(f):
            continue
        
        src = os.path.join(RAW_FOLDER, f)
        name, _ = os.path.splitext(f)
        dst = os.path.join(PREPROCESSED_FOLDER, f"{name}.png")
        
        try:
            preprocess_single(src, dst)
            processed_count += 1
            
            if processed_count % 10 == 0:
                print(f"  [PROGRESS] {processed_count} frames processed...")
            
            # PRODUCTION MODE: Delete original after successful processing
            if not DEV_MODE:
                try:
                    os.remove(src)
                except Exception as e:
                    print(f"  [WARN] Could not delete {f}: {e}")
        
        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {f}: {e}")
    
    print(f"\n" + "="*60)
    print("  PREPROCESS COMPLETE")
    print("="*60)
    print(f"Processed: {processed_count}")
    print(f"Errors: {error_count}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_batch()
