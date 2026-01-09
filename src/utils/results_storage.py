"""
Utility functions for storing test results locally.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .dateUtils import now_ist_iso_utc, format_date_ist, parse_iso_to_ist
from ..config import Config

logger = logging.getLogger(__name__)


def ensure_results_dir() -> Path:
    """
    Ensure the results directory exists.
    
    Returns:
        Path to the results directory
    """
    results_dir = Config.RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def save_sludge_data(data: Dict[str, Any]) -> Optional[str]:
    """
    Save sludge data (t=0 or t=30) to results folder.
    Organizes by date and test ID.
    
    Args:
        data: SludgeData dictionary
        
    Returns:
        Path to saved file if successful, None otherwise
    """
    try:
        results_dir = ensure_results_dir()
        
        # Extract test ID and timestamp
        test_id = data.get("testId", "unknown")
        timestamp = data.get("timestamp", now_ist_iso_utc())
        t_min = data.get("t_min", "unknown")
        
        # Parse date from timestamp - convert to IST first, then extract date
        # This ensures correct date even if UTC timestamp is from previous day
        try:
            dt_ist = parse_iso_to_ist(timestamp)
            date_str = format_date_ist(dt_ist)
        except:
            date_str = format_date_ist()
        
        # Create date folder
        date_dir = results_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename: testId_t{min}.json
        filename = f"{test_id}_t{t_min}.json"
        filepath = date_dir / filename
        
        # Save data as JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved sludge data to: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Failed to save sludge data: {e}")
        return None


def save_height_update(height_mm: float, timestamp: Optional[str] = None, 
                       test_type: Optional[str] = None, 
                       factory_code: Optional[str] = None) -> Optional[str]:
    """
    Save height update to results folder.
    Appends to a daily height updates file.
    
    Args:
        height_mm: Current sludge height in millimeters
        timestamp: ISO timestamp (default: current time)
        test_type: Test type (optional)
        factory_code: Factory code (optional)
        
    Returns:
        Path to saved file if successful, None otherwise
    """
    try:
        results_dir = ensure_results_dir()
        
        # Use current IST time (converted to UTC) if timestamp not provided
        if timestamp is None:
            timestamp = now_ist_iso_utc()
        
        # Parse date from timestamp - convert to IST first, then extract date
        # This ensures correct date even if UTC timestamp is from previous day
        try:
            dt_ist = parse_iso_to_ist(timestamp)
            date_str = format_date_ist(dt_ist)
        except:
            date_str = format_date_ist()
        
        # Create date folder
        date_dir = results_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename for height updates
        filename = "height_updates.jsonl"  # JSON Lines format
        filepath = date_dir / filename
        
        # Prepare update entry
        update_entry = {
            "timestamp": timestamp,
            "height_mm": height_mm,
        }
        if test_type:
            update_entry["test_type"] = test_type
        if factory_code:
            update_entry["factory_code"] = factory_code
        
        # Append to file (JSON Lines format - one JSON object per line)
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(update_entry, ensure_ascii=False) + '\n')
        
        # Return path (logging is done at higher level to avoid spam)
        return str(filepath)
    except Exception as e:
        logger.error(f"Failed to save height update: {e}")
        return None

