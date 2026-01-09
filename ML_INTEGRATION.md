# ML Model Integration Guide

This guide explains how to integrate your ML model with the Thermax SV30 Test System HMI server.

## Overview

The HMI server uses a **DataProvider** interface pattern that allows you to easily swap between different data sources. The interface is defined in `src/services/data_provider.py`. Currently, `SV30DataProvider` is used by default (real pipeline integration), but you can switch to `DummyDataProvider` for testing or create your own ML model provider.

## Architecture

```
┌─────────────────┐
│   Test Service  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Provider  │ ◄─── Your ML Model Implementation
│   (Interface)   │
└─────────────────┘
```

The `DataProvider` interface has three methods that your ML model must implement:
1. `generate_t0_data()` - Initial measurements at test start
2. `generate_t30_data()` - Final measurements at test end
3. `generate_height_history()` - Periodic height updates during test

## Step-by-Step Integration

### Step 1: Create Your ML Data Provider

Create a new file `src/services/ml_data_provider.py`:

```python
"""
ML Model Data Provider for SV30 Test System.

Replace DummyDataProvider with this implementation to use your ML model.
"""
from typing import Dict, Any, List
from .data_provider import DataProvider
from ..models.types import SludgeData, SludgeHeightEntry
from ..exceptions import DataGenerationError
from ..utils.dateUtils import now_ist, now_ist_iso_utc, parse_iso_to_ist, add_minutes_ist, format_date_ist
import logging

logger = logging.getLogger(__name__)


class MLDataProvider(DataProvider):
    """
    ML Model-based data provider.
    
    Replace the methods below with calls to your ML model.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize ML model.
        
        Args:
            model_path: Path to your ML model file (optional)
        """
        # TODO: Load your ML model here
        # Example:
        # import torch
        # self.model = torch.load(model_path)
        # OR
        # import tensorflow as tf
        # self.model = tf.keras.models.load_model(model_path)
        pass
    
    def generate_t0_data(self) -> Dict[str, Any]:
        """
        Generate initial SludgeData at t=0 (start of test).
        
        This method is called when a test starts. You should:
        1. Capture/process the initial image
        2. Run your ML model to analyze the image
        3. Return data matching SludgeData interface
        
        Returns:
            Dictionary matching SludgeData interface with initial measurements
            
        Raises:
            DataGenerationError: If data generation fails
        """
        try:
            # TODO: Replace with your ML model call
            # Example workflow:
            # 1. Capture image from camera
            # image = capture_image()
            
            # 2. Preprocess image for ML model
            # processed_image = preprocess_image(image)
            
            # 3. Run ML model inference
            # predictions = self.model.predict(processed_image)
            
            # 4. Extract measurements from predictions
            # sludge_height = predictions['sludge_height']
            # mixture_height = predictions['mixture_height']
            # etc.
            
            # 5. Format as SludgeData
            # Use IST timezone for all operations
            now = now_ist()
            test_type = self._determine_test_type(now.hour)
            date_str = format_date_ist(now)
            
            # Get timestamp in UTC format (for backend compatibility)
            timestamp = now_ist_iso_utc()
            
            data: SludgeData = {
                "testId": f"SV30-{date_str}-001-{test_type[1]}",
                "timestamp": timestamp,  # UTC ISO format
                "testType": test_type[0],
                "operator": "Operator",
                "sludge_height_mm": 0.0,  # Replace with ML model output
                "mixture_height_mm": 0.0,  # Replace with ML model output
                "floc_count": 0,  # Replace with ML model output
                "floc_avg_size_mm": 0.0,  # Replace with ML model output
                "rgb_clear_zone": {"r": 255, "g": 255, "b": 255},  # From ML model
                "rgb_sludge_zone": {"r": 200, "g": 180, "b": 150},  # From ML model
                "t_min": 0,
                # Optional fields
                "image_filename": f"t0_{now.strftime('%Y%m%d_%H%M%S')}.jpg",
                "image_path": f"/path/to/images/t0_{now.strftime('%Y%m%d_%H%M%S')}.jpg",
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to generate t0 data: {e}")
            raise DataGenerationError(f"ML model failed to generate t0 data: {e}")
    
    def generate_t30_data(
        self, 
        initial_data: Dict[str, Any], 
        test_duration_minutes: float
    ) -> Dict[str, Any]:
        """
        Generate final SludgeData at end of test (t=30 or test duration).
        
        This method is called when the test completes. You should:
        1. Capture/process the final image
        2. Run your ML model to analyze the final state
        3. Calculate SV30 values
        4. Return data matching SludgeData interface
        
        Args:
            initial_data: The t=0 data (for reference)
            test_duration_minutes: Actual test duration in minutes
            
        Returns:
            Dictionary matching SludgeData interface with final measurements
            including SV30 calculations
            
        Raises:
            DataGenerationError: If data generation fails
        """
        try:
            # TODO: Replace with your ML model call
            # Example workflow:
            # 1. Capture final image
            # final_image = capture_image()
            
            # 2. Run ML model inference
            # predictions = self.model.predict(preprocess_image(final_image))
            
            # 3. Extract final measurements
            # final_sludge_height = predictions['sludge_height']
            # final_mixture_height = predictions['mixture_height']
            
            # 4. Calculate SV30
            # sv30_height = final_sludge_height
            # sv30_mL_per_L = (sv30_height / initial_data['mixture_height_mm']) * 1000
            # velocity = sv30_height / test_duration_minutes
            
            # Use IST timezone for all operations
            now = now_ist()
            date_str = format_date_ist(now)
            test_id = initial_data.get("testId", f"SV30-{date_str}-001")
            
            # Example calculations (replace with your ML model outputs)
            final_sludge_height = 0.0  # From ML model
            final_mixture_height = initial_data.get("mixture_height_mm", 1000.0)
            sv30_mL_per_L = (final_sludge_height / final_mixture_height) * 1000
            velocity = final_sludge_height / test_duration_minutes if test_duration_minutes > 0 else 0
            
            # Get timestamp in UTC format (for backend compatibility)
            timestamp = now_ist_iso_utc()
            
            data: SludgeData = {
                "testId": test_id,
                "timestamp": timestamp,  # UTC ISO format
                "testType": initial_data.get("testType", "morning"),
                "operator": initial_data.get("operator", "Operator"),
                "t_min": int(test_duration_minutes),
                "sludge_height_mm": round(final_sludge_height, 2),  # From ML model
                "mixture_height_mm": round(final_mixture_height, 2),
                "sv30_height_mm": round(final_sludge_height, 2),
                "sv30_mL_per_L": round(sv30_mL_per_L, 1),
                "velocity_mm_per_min": round(velocity, 2),
                "floc_count": 0,  # From ML model
                "floc_avg_size_mm": 0.0,  # From ML model
                "rgb_clear_zone": initial_data.get("rgb_clear_zone", {"r": 255, "g": 255, "b": 255}),
                "rgb_sludge_zone": initial_data.get("rgb_sludge_zone", {"r": 200, "g": 180, "b": 150}),
                # Optional fields
                "image_filename": f"t30_{now.strftime('%Y%m%d_%H%M%S')}.jpg",
                "image_path": f"/path/to/images/t30_{now.strftime('%Y%m%d_%H%M%S')}.jpg",
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to generate t30 data: {e}")
            raise DataGenerationError(f"ML model failed to generate t30 data: {e}")
    
    def generate_height_history(
        self,
        initial_data: Dict[str, Any],
        duration_minutes: float,
        interval_seconds: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate periodic sludge height measurements during the test.
        
        This method is called periodically during the test (every 10 seconds by default).
        You can either:
        - Generate all measurements at once (current implementation)
        - Or implement real-time capture and processing
        
        Args:
            initial_data: The t=0 data
            duration_minutes: Test duration in minutes
            interval_seconds: Measurement interval in seconds (default: 10)
            
        Returns:
            List of SludgeHeightEntry dictionaries with height measurements
            at regular intervals
            
        Raises:
            DataGenerationError: If data generation fails
        """
        try:
            # TODO: Replace with your ML model calls
            # Option 1: Generate all at once (current approach)
            # Option 2: Real-time processing (capture and process each interval)
            
            entries: List[Dict[str, Any]] = []
            # Parse timestamp and convert to IST
            start_time = parse_iso_to_ist(initial_data["timestamp"])
            test_type = initial_data.get("testType")
            
            num_intervals = int((duration_minutes * 60) / interval_seconds)
            
            for i in range(num_intervals):
                elapsed_seconds = i * interval_seconds
                measurement_time = start_time + timedelta(seconds=elapsed_seconds)
                timestamp_ms = int(measurement_time.timestamp() * 1000)
                
                # Convert to UTC ISO format for backend compatibility
                from datetime import timezone
                measurement_time_utc = measurement_time.astimezone(timezone.utc)
                date_time_utc = measurement_time_utc.isoformat().replace("+00:00", "Z")
                
                # TODO: Replace with ML model call for this time point
                # Option 1: If you have a time-series model
                # height = self.model.predict_time_series(elapsed_seconds)
                
                # Option 2: If you need to capture images at each interval
                # image = capture_image()
                # height = self.model.predict(preprocess_image(image))['sludge_height']
                
                # For now, using placeholder
                height = 0.0  # Replace with ML model output
                
                entry: SludgeHeightEntry = {
                    "timestamp": timestamp_ms,
                    "dateTime": date_time_utc,  # UTC ISO format
                    "height": height,
                    "testType": test_type,
                }
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to generate height history: {e}")
            raise DataGenerationError(f"ML model failed to generate height history: {e}")
    
    def _determine_test_type(self, current_hour: int) -> tuple[str, str]:
        """Helper method to determine test type based on time of day."""
        if 6 <= current_hour < 12:
            return ("morning", "A")
        elif 12 <= current_hour < 18:
            return ("afternoon", "E")
        else:
            return ("evening", "E")
```

### Step 2: Update app.py to Use Your ML Provider

Edit `src/app.py` and replace the data provider initialization:

```python
# Find this line (around line 70):
data_provider = SV30DataProvider(sv30_path=sv30_path)

# Replace with:
from .services.ml_data_provider import MLDataProvider
data_provider = MLDataProvider(model_path="/path/to/your/model.pth")  # Or your model path

# Or to use dummy data for testing:
# from .services.dummy_data_provider import DummyDataProvider
# data_provider = DummyDataProvider()
```

### Step 3: Install ML Dependencies

Add your ML framework dependencies to `requirements.txt`:

```txt
# Add your ML framework
torch>=2.0.0  # For PyTorch
# OR
tensorflow>=2.13.0  # For TensorFlow
# OR
opencv-python>=4.8.0  # For image processing
# etc.
```

Then install:
```bash
pip install -r requirements.txt
```

## Data Structure Reference

### SludgeData Interface

Your ML model must return data matching this structure:

```python
{
    "testId": str,                    # e.g., "SV30-2026-01-03-001-A"
    "timestamp": str,                 # REQUIRED: ISO format UTC: "2026-01-03T10:30:00Z" (IST converted to UTC)
    "testType": str,                  # Optional: "morning" | "afternoon" | "evening"
    "operator": str,                  # Optional: Operator name
    "t_min": int,                     # Optional: Time in minutes (0 for t0, 30 for t30)
    "sludge_height_mm": float,       # REQUIRED: Sludge height in mm
    "mixture_height_mm": float,       # REQUIRED: Total mixture height in mm
    "sv30_height_mm": float,          # Optional: SV30 height (for t30)
    "sv30_mL_per_L": float,           # Optional: SV30 value (for t30)
    "velocity_mm_per_min": float,     # Optional: Settling velocity (for t30)
    "floc_count": int,               # REQUIRED: Number of flocs detected
    "floc_avg_size_mm": float,        # REQUIRED: Average floc size in mm
    "rgb_clear_zone": {               # Optional: RGB values for clear zone
        "r": int, "g": int, "b": int  # Values 0-255
    },
    "rgb_sludge_zone": {              # Optional: RGB values for sludge zone
        "r": int, "g": int, "b": int  # Values 0-255
    },
    "image_filename": str,           # Optional: Image filename
    "image_path": str,                # Optional: Full path to image
}
```

### SludgeHeightEntry Interface

For height history updates:

```python
{
    "timestamp": int,                 # Unix timestamp
    "dateTime": str,                  # ISO format UTC datetime string: "2026-01-03T10:30:00Z"
    "height": float,                  # Sludge height in mm at this time
    "testType": str,                  # "morning" | "afternoon" | "evening"
}
```

## Integration Patterns

### Pattern 1: Image-Based ML Model

If your ML model processes images:

```python
def generate_t0_data(self) -> Dict[str, Any]:
    # Capture image
    image = self.camera.capture()
    
    # Preprocess
    processed = self.preprocess(image)
    
    # Run inference
    results = self.model(processed)
    
    # Extract measurements
    return {
        "sludge_height_mm": results['sludge_height'],
        "mixture_height_mm": results['mixture_height'],
        # ... etc
    }
```

### Pattern 2: Time-Series Model

If your model predicts height over time:

```python
def generate_height_history(self, initial_data, duration_minutes, interval_seconds):
    # Generate predictions for all time points
    time_points = np.arange(0, duration_minutes * 60, interval_seconds)
    heights = self.model.predict(time_points, initial_data)
    
    # Format as entries
    return [{"height": h, ...} for h in heights]
```

### Pattern 3: Real-Time Processing

If you want to process images in real-time during the test:

```python
# In generate_height_history, you could set up a callback
# that captures and processes images at each interval
def generate_height_history(self, ...):
    # This is called once at test start
    # You could spawn a background thread that captures images
    # and processes them at each interval
    pass
```

## Error Handling

Always wrap ML model calls in try-except blocks and raise `DataGenerationError`:

```python
from ..exceptions import DataGenerationError

try:
    predictions = self.model.predict(image)
except Exception as e:
    logger.error(f"ML model inference failed: {e}")
    raise DataGenerationError(f"Model inference error: {e}")
```

## Testing Your Integration

1. **Test t0 data generation:**
   ```python
   provider = MLDataProvider()
   t0_data = provider.generate_t0_data()
   print(t0_data)
   ```

2. **Test t30 data generation:**
   ```python
   t30_data = provider.generate_t30_data(t0_data, 30.0)
   print(t30_data)
   ```

3. **Test height history:**
   ```python
   history = provider.generate_height_history(t0_data, 30.0, 10)
   print(f"Generated {len(history)} height entries")
   ```

4. **Run the server:**
   ```bash
   python run.py
   ```
   Start a test and verify data is generated correctly.

## Best Practices

1. **Timezone**: Always use IST timezone utilities from `src/utils/dateUtils.py` - never use `datetime.now()` directly
2. **Caching**: Cache model loading - don't reload the model on every call
3. **Error Handling**: Always handle ML model failures gracefully, raise `DataGenerationError` on failures
4. **Logging**: Log ML model inputs/outputs for debugging
5. **Performance**: Optimize inference time - tests run for 30 minutes
6. **Image Storage**: Save processed images for debugging/analysis
7. **Validation**: Validate ML model outputs match expected ranges
8. **Data Format**: Ensure all returned data matches backend schema exactly (see `src/models/types.py`)
9. **Backend Sending**: Only t=30 data is sent to backend - t=0 is kept locally for frontend display
10. **Rounding**: Round numeric values appropriately (heights: 2 decimals, SV30: 1 decimal, velocity: 2 decimals)

## Example: Complete Integration

See `src/services/dummy_data_provider.py` or `src/services/sv30_data_provider.py` for complete reference implementations that you can use as templates.

## Troubleshooting

### Model Not Loading
- Check model path is correct
- Verify model file format matches your framework
- Check dependencies are installed

### Data Format Errors
- Verify return types match `SludgeData` interface exactly
- Check all required fields are present: `timestamp`, `sludge_height_mm`, `mixture_height_mm`, `floc_count`, `floc_avg_size_mm`
- Ensure numeric types are correct (float vs int)
- Verify timestamps are in UTC ISO format with Z suffix (use `now_ist_iso_utc()`)
- Check that IST timezone utilities are used for all datetime operations
- Ensure data format matches backend schema exactly (see `src/models/types.py`)

### Performance Issues
- Profile model inference time
- Consider model quantization or optimization
- Use GPU if available

## Support

For questions or issues with ML integration, contact the development team or refer to the main README.md.

