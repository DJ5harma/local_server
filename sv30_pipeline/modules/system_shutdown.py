"""
System Shutdown Module

Handles graceful Raspberry Pi shutdown after test completion.
"""

import os
import time
import subprocess

def shutdown_system(delay_sec=10):
    """
    Shutdown the Raspberry Pi after a delay
    
    Args:
        delay_sec: Delay in seconds before shutdown
    
    Returns:
        success: Boolean (False if not running on Linux/Pi)
    """
    print("\n" + "="*60)
    print("  SYSTEM SHUTDOWN")
    print("="*60)
    print(f"Shutting down in {delay_sec} seconds...")
    print("  Press Ctrl+C to cancel")
    print("="*60 + "\n")
    
    try:
        # Countdown
        for i in range(delay_sec, 0, -1):
            print(f"  Shutdown in {i}...", end='\r', flush=True)
            time.sleep(1)
        
        print("\n\n[SHUTDOWN] Powering off Raspberry Pi...")
        
        # Execute shutdown command
        # This requires the script to be run with appropriate permissions
        # Add to sudoers: pi ALL=(ALL) NOPASSWD: /sbin/shutdown
        subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Cancelled by user")
        return False
    
    except subprocess.CalledProcessError as e:
        print(f"\n[SHUTDOWN ERROR] Failed to execute shutdown: {e}")
        print("  Make sure you have sudo permissions for shutdown")
        print("  Add to /etc/sudoers: pi ALL=(ALL) NOPASSWD: /sbin/shutdown")
        return False
    
    except Exception as e:
        print(f"\n[SHUTDOWN ERROR] Unexpected error: {e}")
        return False

def test_shutdown_permissions():
    """
    Test if the system has permissions to shutdown
    
    Returns:
        has_permission: Boolean
    """
    try:
        # Test with dry-run
        result = subprocess.run(
            ['sudo', '-n', 'shutdown', '--help'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False

if __name__ == "__main__":
    # Test shutdown (will countdown but not actually shutdown in test mode)
    print("Testing shutdown permissions...")
    
    if test_shutdown_permissions():
        print("✅ Shutdown permissions OK")
        print("\nTo actually shutdown, uncomment the shutdown call in main.py")
    else:
        print("❌ No shutdown permissions")
        print("\nTo fix, run:")
        print("  sudo visudo")
        print("  Add line: pi ALL=(ALL) NOPASSWD: /sbin/shutdown")
