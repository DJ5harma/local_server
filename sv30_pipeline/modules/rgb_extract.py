"""
RGB Extraction Module

Extracts RGB values from two specific points in color-masked images.

Points:
- Clear zone: 5 pixels below mixture top, at center X
- Sludge zone: 100 pixels below mixture top, at center X

Author: Jan 2026
"""

import os
import sys
import cv2
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def extract_rgb_values():
    """
    Extract RGB from two specific points in color-masked images.
    
    Uses the FIRST color-masked image.
    
    Returns:
        dict: RGB values for clear and sludge zones
    """
    logger.info("\n" + "="*70)
    logger.info("  RGB EXTRACTION")
    logger.info("="*70)
    logger.info(f"Input: {config.COLOR_MASKED_FOLDER}")
    logger.info(f"Output: {config.RESULTS_FOLDER}/rgb_values.json")
    logger.info("="*70 + "\n")
    
    # Load sludge detection results to get mixture_top_y
    sludge_json_path = os.path.join(config.RESULTS_FOLDER, "sludge_detection.json")
    
    if not os.path.exists(sludge_json_path):
        logger.error(f"[ERROR] Sludge detection results not found: {sludge_json_path}")
        logger.error("   Run sludge detection first!")
        return None
    
    with open(sludge_json_path, 'r') as f:
        sludge_data = json.load(f)
    
    mixture_top_y = sludge_data['mixture_top_y']
    
    # Get first color-masked image
    frames = sorted([f for f in os.listdir(config.COLOR_MASKED_FOLDER) 
                    if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    if not frames:
        logger.error("[ERROR] No color-masked frames found!")
        return None
    
    first_frame = frames[0]
    first_frame_path = os.path.join(config.COLOR_MASKED_FOLDER, first_frame)
    
    logger.info(f"Using frame: {first_frame}")
    logger.info(f"Mixture top: y = {mixture_top_y}\n")
    
    # Read image
    img = cv2.imread(first_frame_path)
    
    if img is None:
        logger.error(f"[ERROR] Cannot read image: {first_frame_path}")
        return None
    
    h, w = img.shape[:2]
    
    # Calculate positions
    center_x = w // 2
    clear_y = mixture_top_y + 5    # 5 pixels below mixture top
    sludge_y = mixture_top_y + 100  # 100 pixels below mixture top
    
    logger.info(f"Image size: {w}x{h}")
    logger.info(f"Center X: {center_x}")
    logger.info(f"Clear zone point: ({center_x}, {clear_y})")
    logger.info(f"Sludge zone point: ({center_x}, {sludge_y})\n")
    
    # Validate coordinates
    if clear_y < 0 or clear_y >= h:
        logger.error(f"[ERROR] Clear zone Y out of bounds: {clear_y}")
        return None
    
    if sludge_y < 0 or sludge_y >= h:
        logger.error(f"[ERROR] Sludge zone Y out of bounds: {sludge_y}")
        return None
    
    # Extract RGB values (OpenCV uses BGR, so reverse)
    clear_bgr = img[clear_y, center_x]
    sludge_bgr = img[sludge_y, center_x]
    
    # Convert BGR to RGB
    clear_rgb = {
        "r": int(clear_bgr[2]),
        "g": int(clear_bgr[1]),
        "b": int(clear_bgr[0])
    }
    
    sludge_rgb = {
        "r": int(sludge_bgr[2]),
        "g": int(sludge_bgr[1]),
        "b": int(sludge_bgr[0])
    }
    
    # Build result
    rgb_data = {
        "extraction_method": "single_pixel",
        "mixture_top_y": mixture_top_y,
        "clear_zone": {
            "position": {"x": center_x, "y": clear_y},
            "rgb": clear_rgb
        },
        "sludge_zone": {
            "position": {"x": center_x, "y": sludge_y},
            "rgb": sludge_rgb
        },
        "source_image": first_frame
    }
    
    # Save to JSON
    output_path = os.path.join(config.RESULTS_FOLDER, "rgb_values.json")
    with open(output_path, 'w') as f:
        json.dump(rgb_data, f, indent=2)
    
    # Log results
    logger.info("="*70)
    logger.info("  RGB EXTRACTION COMPLETE")
    logger.info("="*70)
    logger.info(f"Clear zone RGB: R={clear_rgb['r']}, G={clear_rgb['g']}, B={clear_rgb['b']}")
    logger.info(f"Sludge zone RGB: R={sludge_rgb['r']}, G={sludge_rgb['g']}, B={sludge_rgb['b']}")
    logger.info(f"\nSaved: {output_path}")
    logger.info("="*70 + "\n")
    
    return rgb_data


if __name__ == "__main__":
    # Test RGB extraction
    rgb_data = extract_rgb_values()
    if rgb_data:
        print(f"? RGB extraction successful!")
        print(f"   Clear: RGB({rgb_data['clear_zone']['rgb']['r']}, {rgb_data['clear_zone']['rgb']['g']}, {rgb_data['clear_zone']['rgb']['b']})")
        print(f"   Sludge: RGB({rgb_data['sludge_zone']['rgb']['r']}, {rgb_data['sludge_zone']['rgb']['g']}, {rgb_data['sludge_zone']['rgb']['b']})")
    else:
        print("? RGB extraction failed!")
        sys.exit(1)
