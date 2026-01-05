"""
Data Archiving Module

Archives previous test data to dated folders before starting a new test.
Prevents data loss and allows checking if previous data was uploaded to AWS.
"""

import os
import shutil
from datetime import datetime
from sv30config import (
    STAGE_INPUTS,
    ARCHIVE_ROOT,
    ARCHIVE_FORMAT,
    UPLOAD_RAW_FOLDER,
    UPLOAD_VIDEOS_FOLDER,
    RESULTS_FOLDER,
    GRAPHS_FOLDER,
    DEV_MODE
)

def has_data_to_archive():
    """
    Check if there's any data from a previous test
    
    Returns:
        Boolean: True if data exists
    """
    # Check for any files in stage_inputs folders
    for folder in [UPLOAD_RAW_FOLDER, RESULTS_FOLDER, GRAPHS_FOLDER]:
        if os.path.exists(folder) and os.listdir(folder):
            return True
    
    return False

def check_upload_marker(folder_path):
    """
    Check if data in folder was uploaded to AWS
    
    Args:
        folder_path: Path to check
    
    Returns:
        uploaded: Boolean
        marker_file: Path to marker file if exists
    """
    # Look for .uploaded marker file
    marker_file = os.path.join(folder_path, ".uploaded")
    
    if os.path.exists(marker_file):
        return True, marker_file
    
    return False, None

def determine_test_type_from_timestamp(timestamp_str):
    """
    Determine test type from timestamp
    
    Args:
        timestamp_str: Timestamp string (format: YYYYMMDD_HHMMSS)
    
    Returns:
        test_type: "morning" | "afternoon" | "evening"
    """
    try:
        # Parse timestamp
        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        hour = dt.hour
        
        if hour >= 4 and hour < 12:
            return "morning"
        elif hour >= 12 and hour < 20:
            return "afternoon"
        else:
            return "evening"
    except:
        return "unknown"

def archive_old_data():
    """
    Archive previous test data to dated folder
    
    Returns:
        success: Boolean
        archive_path: Path to archived data
        has_data: Boolean - was there data to archive
    """
    # Check if there's data to archive
    if not has_data_to_archive():
        print("[ARCHIVE] No previous data found - skipping archive")
        return True, None, False
    
    print("\n" + "="*60)
    print("  ARCHIVING PREVIOUS TEST DATA")
    print("="*60)
    
    # Create archive folder with timestamp
    timestamp = datetime.now().strftime(ARCHIVE_FORMAT)
    archive_path = os.path.join(ARCHIVE_ROOT, f"test_{timestamp}")
    
    os.makedirs(archive_path, exist_ok=True)
    
    try:
        archived_items = []
        
        # Archive upload_raw folder (videos + snapshots)
        if os.path.exists(UPLOAD_RAW_FOLDER) and os.listdir(UPLOAD_RAW_FOLDER):
            dst = os.path.join(archive_path, "upload_raw")
            shutil.copytree(UPLOAD_RAW_FOLDER, dst)
            archived_items.append("upload_raw")
            print(f"  ✓ Archived: upload_raw/")
        
        # Archive results
        if os.path.exists(RESULTS_FOLDER) and os.listdir(RESULTS_FOLDER):
            dst = os.path.join(archive_path, "results")
            shutil.copytree(RESULTS_FOLDER, dst)
            archived_items.append("results")
            print(f"  ✓ Archived: results/")
        
        # Archive graphs
        if os.path.exists(GRAPHS_FOLDER) and os.listdir(GRAPHS_FOLDER):
            dst = os.path.join(archive_path, "graphs")
            shutil.copytree(GRAPHS_FOLDER, dst)
            archived_items.append("graphs")
            print(f"  ✓ Archived: graphs/")
        
        print(f"\n" + "="*60)
        print(f"  ✅ ARCHIVE COMPLETE")
        print(f"="*60)
        print(f"  Location: {archive_path}")
        print(f"  Items: {', '.join(archived_items)}")
        print(f"="*60 + "\n")
        
        # Clean up original folders (only in production mode)
        if not DEV_MODE:
            for folder in [UPLOAD_RAW_FOLDER, RESULTS_FOLDER, GRAPHS_FOLDER]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                    os.makedirs(folder, exist_ok=True)
            print("[ARCHIVE] Original folders cleaned (PROD mode)\n")
        
        return True, archive_path, True
        
    except Exception as e:
        print(f"\n[ARCHIVE] ❌ FAILED: {e}\n")
        return False, archive_path, True

def check_previous_upload_status(archive_path):
    """
    Check if previous archived data was uploaded to AWS
    
    Args:
        archive_path: Path to archived data
    
    Returns:
        status: Dict with upload status info
    """
    if archive_path is None:
        return {
            'uploaded': True,  # No data to check
            'test_type': None,
            'files_pending': [],
            'warning_needed': False
        }
    
    # Extract timestamp from archive path
    folder_name = os.path.basename(archive_path)  # e.g., test_20241224_063015
    timestamp_str = folder_name.replace("test_", "")
    
    # Check for upload marker
    uploaded, marker_file = check_upload_marker(archive_path)
    
    # Determine test type from timestamp
    test_type = determine_test_type_from_timestamp(timestamp_str)
    
    # Check for video file
    video_folder = os.path.join(archive_path, "upload_raw", "videos")
    has_video = False
    if os.path.exists(video_folder):
        video_files = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.avi'))]
        has_video = len(video_files) > 0
    
    files_pending = []
    if not uploaded:
        if has_video:
            files_pending.append("video")
        files_pending.extend(["results", "graphs"])
    
    warning_needed = not uploaded and len(files_pending) > 0
    
    return {
        'uploaded': uploaded,
        'test_type': test_type,
        'files_pending': files_pending,
        'warning_needed': warning_needed,
        'archive_path': archive_path,
        'timestamp': timestamp_str
    }

if __name__ == "__main__":
    # Test archiving
    success, archive_path, has_data = archive_old_data()
    
    if success and has_data:
        print(f"\n✅ Archive successful: {archive_path}")
        
        # Check upload status
        status = check_previous_upload_status(archive_path)
        print(f"\nUpload status:")
        print(f"  Uploaded: {status['uploaded']}")
        print(f"  Test type: {status['test_type']}")
        print(f"  Pending files: {status['files_pending']}")
        print(f"  Warning needed: {status['warning_needed']}")
    elif success and not has_data:
        print("\n✅ No data to archive")
    else:
        print("\n❌ Archive failed")
