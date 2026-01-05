import os
import time
import json
from datetime import datetime
from sv30config import (
    AWS_ENABLED,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_S3_BUCKET,
    AWS_S3_PREFIX,
    AWS_MAX_RETRIES,
    AWS_RETRY_DELAY_SEC,
    AWS_UPLOAD_VIDEO,
    AWS_UPLOAD_IMAGES,
    AWS_UPLOAD_RESULTS,
    AWS_DELETE_AFTER_UPLOAD,
    DEV_MODE,
)

# Import boto3 only if AWS is enabled
if AWS_ENABLED:
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        print("[AWS ERROR] boto3 not installed. Run: pip install boto3")
        AWS_ENABLED = False

class AWSUploader:
    """
    Upload files to AWS S3 with retry logic
    """
    
    def __init__(self):
        if not AWS_ENABLED:
            print("[AWS] Disabled in configuration")
            return
        
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            print("[AWS ERROR] Credentials not configured")
            print("  Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            
            # Verify bucket exists
            self.s3_client.head_bucket(Bucket=AWS_S3_BUCKET)
            print(f"[AWS] Connected to bucket: {AWS_S3_BUCKET}")
            self.initialized = True
        
        except NoCredentialsError:
            print("[AWS ERROR] Invalid credentials")
            self.initialized = False
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"[AWS ERROR] Bucket not found: {AWS_S3_BUCKET}")
            elif error_code == '403':
                print(f"[AWS ERROR] Access denied to bucket: {AWS_S3_BUCKET}")
            else:
                print(f"[AWS ERROR] {e}")
            self.initialized = False
    
    def generate_s3_key(self, local_path, test_id):
        """
        Generate S3 object key with folder structure
        
        Format: sv30_tests/DDMMYY/DDMMYYtest1/filename.ext
        
        Args:
            local_path: Local file path
            test_id: Test identifier (e.g., '191224test1')
        
        Returns:
            S3 object key
        """
        filename = os.path.basename(local_path)
        date_str = test_id[:6]  # Extract DDMMYY
        
        s3_key = f"{AWS_S3_PREFIX}/{date_str}/{test_id}/{filename}"
        return s3_key
    
    def upload_file_with_retry(self, local_path, test_id):
        """
        Upload single file to S3 with retry logic
        
        Args:
            local_path: Path to local file
            test_id: Test identifier
        
        Returns:
            (success, s3_url)
        """
        if not self.initialized:
            return False, None
        
        if not os.path.exists(local_path):
            print(f"[AWS ERROR] File not found: {local_path}")
            return False, None
        
        s3_key = self.generate_s3_key(local_path, test_id)
        filename = os.path.basename(local_path)
        file_size = os.path.getsize(local_path)
        
        print(f"\n[AWS] Uploading: {filename} ({file_size/1024/1024:.2f} MB)")
        print(f"  S3 Key: {s3_key}")
        
        for attempt in range(1, AWS_MAX_RETRIES + 1):
            try:
                # Upload with progress callback
                self.s3_client.upload_file(
                    local_path,
                    AWS_S3_BUCKET,
                    s3_key,
                    Callback=lambda bytes_transferred: self._upload_progress(
                        bytes_transferred, file_size
                    )
                )
                
                s3_url = f"s3://{AWS_S3_BUCKET}/{s3_key}"
                print(f"\n[AWS] Upload complete: {s3_url}")
                
                # Delete local file if configured (production mode only)
                if AWS_DELETE_AFTER_UPLOAD and not DEV_MODE:
                    try:
                        os.remove(local_path)
                        print(f"[CLEANUP] Deleted local file: {filename}")
                    except Exception as e:
                        print(f"[WARN] Could not delete {filename}: {e}")
                
                return True, s3_url
            
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"\n[AWS ERROR] Attempt {attempt}/{AWS_MAX_RETRIES}: {error_code}")
                
                if attempt < AWS_MAX_RETRIES:
                    print(f"[AWS] Retrying in {AWS_RETRY_DELAY_SEC}s...")
                    time.sleep(AWS_RETRY_DELAY_SEC)
                else:
                    print(f"[AWS] Upload failed after {AWS_MAX_RETRIES} attempts")
                    return False, None
            
            except Exception as e:
                print(f"\n[AWS ERROR] Attempt {attempt}/{AWS_MAX_RETRIES}: {e}")
                
                if attempt < AWS_MAX_RETRIES:
                    time.sleep(AWS_RETRY_DELAY_SEC)
                else:
                    return False, None
        
        return False, None
    
    def _upload_progress(self, bytes_transferred, total_bytes):
        """Progress callback (prints dots)"""
        if total_bytes > 0:
            percent = (bytes_transferred / total_bytes) * 100
            if int(percent) % 10 == 0:  # Print every 10%
                print(f"  {int(percent)}%", end='', flush=True)

def upload_test_data(video_path, test_id, cam2_t0_path, cam2_t30_path, results_folder, graphs_folder):
    """
    Upload all test data to AWS S3
    
    Args:
        video_path: Path to video file
        test_id: Test identifier (e.g., '191224_143045test1')
        cam2_t0_path: Camera 2 t=0 snapshot
        cam2_t30_path: Camera 2 t=30 snapshot
        results_folder: Folder containing JSON results
        graphs_folder: Folder containing graphs
    
    Returns:
        (success, upload_summary)
    """
    if not AWS_ENABLED:
        print("[AWS] Upload skipped (disabled in config)")
        return False, {"status": "disabled"}
    
    print("\n" + "="*60)
    print("  AWS S3 UPLOAD")
    print("="*60)
    print(f"Test ID: {test_id}")
    print(f"Bucket: {AWS_S3_BUCKET}")
    print("="*60 + "\n")
    
    uploader = AWSUploader()
    
    if not uploader.initialized:
        # Send warning to dashboard
        try:
            from modules.socketio_client import send_test_warning
            send_test_warning(
                message="AWS S3 upload initialization failed",
                error_details="Could not connect to AWS S3. Check credentials and bucket configuration."
            )
        except:
            pass
        
        return False, {"status": "initialization_failed"}
    
    upload_summary = {
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
        "uploads": []
    }
    
    # 1. Upload video (priority)
    video_upload_failed = False
    if AWS_UPLOAD_VIDEO and video_path and os.path.exists(video_path):
        success, s3_url = uploader.upload_file_with_retry(video_path, test_id)
        upload_summary["uploads"].append({
            "type": "video",
            "file": os.path.basename(video_path),
            "success": success,
            "s3_url": s3_url
        })
        
        if not success:
            video_upload_failed = True
    
    # 2. Upload Camera 2 images
    if AWS_UPLOAD_IMAGES:
        for img_path in [cam2_t0_path, cam2_t30_path]:
            if img_path and os.path.exists(img_path):
                success, s3_url = uploader.upload_file_with_retry(img_path, test_id)
                upload_summary["uploads"].append({
                    "type": "camera2_snapshot",
                    "file": os.path.basename(img_path),
                    "success": success,
                    "s3_url": s3_url
                })
    
    # 3. Upload results JSON files
    if AWS_UPLOAD_RESULTS and os.path.exists(results_folder):
        for filename in os.listdir(results_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(results_folder, filename)
                success, s3_url = uploader.upload_file_with_retry(filepath, test_id)
                upload_summary["uploads"].append({
                    "type": "results_json",
                    "file": filename,
                    "success": success,
                    "s3_url": s3_url
                })
    
    # 4. Upload graphs
    if AWS_UPLOAD_RESULTS and os.path.exists(graphs_folder):
        for filename in os.listdir(graphs_folder):
            if filename.endswith('.png'):
                filepath = os.path.join(graphs_folder, filename)
                success, s3_url = uploader.upload_file_with_retry(filepath, test_id)
                upload_summary["uploads"].append({
                    "type": "graph",
                    "file": filename,
                    "success": success,
                    "s3_url": s3_url
                })
    
    # Summary
    total_uploads = len(upload_summary["uploads"])
    successful_uploads = sum(1 for u in upload_summary["uploads"] if u["success"])
    failed_files = [u["file"] for u in upload_summary["uploads"] if not u["success"]]
    
    print("\n" + "="*60)
    print("  UPLOAD SUMMARY")
    print("="*60)
    print(f"Total: {total_uploads}")
    print(f"Successful: {successful_uploads}")
    print(f"Failed: {total_uploads - successful_uploads}")
    if failed_files:
        print(f"Failed files: {', '.join(failed_files)}")
    print("="*60 + "\n")
    
    upload_summary["total"] = total_uploads
    upload_summary["successful"] = successful_uploads
    upload_summary["failed"] = total_uploads - successful_uploads
    upload_summary["failed_files"] = failed_files
    
    # Send warning to dashboard if video upload failed
    if video_upload_failed:
        try:
            from modules.socketio_client import send_test_warning
            send_test_warning(
                message="Failed to upload video to AWS S3",
                error_details=f"Video file: {os.path.basename(video_path)}. Total failed: {len(failed_files)} files."
            )
        except Exception as e:
            print(f"[WARN] Could not send dashboard warning: {e}")
    elif len(failed_files) > 0:
        # Send warning for other failed uploads (non-video)
        try:
            from modules.socketio_client import send_test_warning
            send_test_warning(
                message=f"Failed to upload {len(failed_files)} file(s) to AWS S3",
                error_details=f"Failed files: {', '.join(failed_files)}"
            )
        except Exception as e:
            print(f"[WARN] Could not send dashboard warning: {e}")
    
    # Create upload marker file if all uploads successful
    if successful_uploads == total_uploads:
        try:
            marker_path = os.path.join(results_folder, ".uploaded")
            with open(marker_path, 'w') as f:
                f.write(datetime.now().isoformat())
            print("[AWS] Created upload marker file")
        except:
            pass
    
    return successful_uploads == total_uploads, upload_summary

if __name__ == "__main__":
    print("AWS Uploader Module")
    print("Use this module from main.py")
