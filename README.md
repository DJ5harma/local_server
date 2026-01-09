# SV30 Test System - Local HMI Server

Local server for SV30 test system HMI interface. Runs on Raspberry Pi and serves the operator interface for running SV30 tests.

## Project Structure

```
local_server/
├── src/                    # Source code
│   ├── api/               # API routes and WebSocket handlers
│   ├── config.py          # Configuration management
│   ├── models/            # Data models and state management
│   ├── services/          # Business logic (data providers, backend client, test service)
│   ├── utils/             # Utility functions (date/time, results storage)
│   └── app.py             # Main Flask application
├── static/                 # Frontend files (HTML, CSS, JS)
├── config/                 # Configuration templates
├── scripts/                # Utility scripts (autostart setup, etc.)
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── ML_INTEGRATION.md      # ML model integration guide
└── RASPBERRY_PI_SETUP.md  # Raspberry Pi auto-start guide
```

## Features

- **6-Page HMI Flow**: Login → Home → Start → Progress → Completion → Results
- **Real-time Updates**: WebSocket and polling support for live test progress
- **Backend Integration**: Automatically sends final test data to backend server via Socket.IO
- **Dual Data Providers**: SV30DataProvider (real pipeline) and DummyDataProvider (testing)
- **IST Timezone Support**: All timestamps use Indian Standard Time (UTC+5:30)
- **Clean Architecture**: Organized codebase with separation of concerns

## Setup

### Prerequisites

- Python 3.8 or higher
- Backend server running (default: `http://localhost:4000`)

### Installation

1. Create and activate virtual environment (recommended):
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows CMD
python -m venv venv
venv\Scripts\activate.bat

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

Or use the provided activation scripts:
```bash
# Windows PowerShell
.\activate.ps1

# Windows CMD
activate.bat

# Linux/Mac
source activate.sh
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Windows PowerShell
python scripts\create_env.py

# Linux/Mac
python scripts/create_env.py

# Then edit .env with your settings
```

4. Run the server:
```bash
python run.py
```

Or using Flask directly:
```bash
python -m flask --app src.app run --host 0.0.0.0 --port 5000
```

**Note**: Always activate the virtual environment before running the server to ensure you're using the correct Python packages.

## Configuration

Environment variables (in `.env` file):

- `LOGIN_PASSWORD` - Password for HMI login (default: "thermax")
- `PORT` - Server port (default: 5000)
- `HOST` - Server host (default: "0.0.0.0")
- `TEST_DURATION_MINUTES` - Test duration in minutes (default: 31)
- `BACKEND_URL` - Backend server URL (default: `http://localhost:4000`)
- `FACTORY_CODE` - Factory identifier (default: `"factory-a"`)

**Note**: All timestamps use Indian Standard Time (IST - UTC+5:30). Timestamps sent to backend are converted to UTC ISO format for compatibility.

## Usage

1. Access the HMI at `http://localhost:5000` (or Raspberry Pi IP address)
2. Login with the configured password
3. Click "New Cycle" to start a test
4. Confirm test start
5. Monitor test progress (30 minutes)
6. View results after completion

## Page Flow

1. **Login Page**: Password authentication
2. **Home/Idle**: System ready for new test
3. **Start Experiment**: Confirmation before starting
4. **Experiment in Progress**: Real-time progress with timer
5. **Test Completion**: Auto-display after 30 minutes
6. **Final Result**: One-time display of SV30 value

## API Endpoints

- `GET /` - Serve HMI interface
- `POST /api/login` - Authenticate with password
- `POST /api/test/start` - Start new test cycle
- `GET /api/test/status` - Get current test status
- `GET /api/test/data` - Get test data (real-time updates)
- `POST /api/test/abort` - Abort running test
- `GET /api/test/result` - Get final test result
- `POST /api/test/reset` - Reset test state to idle
- `WS /ws` - WebSocket for real-time updates

## Data Flow

When a test starts:

1. **t=0**: Generate initial data → Display on HMI → Store locally (NOT sent to backend)
2. **During test (every 10s)**: Generate height updates → Display on HMI → Store locally (NOT sent to backend)
3. **t=30**: Generate final data → Display on HMI → Send to backend → Show results

**Note**: Only t=30 (final) data is sent to backend. Backend stores one record per factory/date/testType and replaces the entire data field on update, so sending t=0 data is redundant.

## Data Providers

The system uses a `DataProvider` interface that allows easy swapping between different data sources. Two implementations are available:

1. **SV30DataProvider** (default): Integrates with the SV30 pipeline (`sv30_pipeline/`) to run real video capture and analysis
2. **DummyDataProvider**: Generates realistic test data for testing and development

### Switching Data Providers

To switch between providers, edit `src/app.py` (around line 70):

```python
# Currently using SV30DataProvider (real pipeline):
data_provider = SV30DataProvider(sv30_path=sv30_path)

# To use dummy data instead, comment out above and uncomment:
# from .services.dummy_data_provider import DummyDataProvider
# data_provider = DummyDataProvider()
```

### Integration with ML Model

To integrate your own ML model, create a new provider implementing the `DataProvider` interface:
- See `src/services/data_provider.py` for the interface definition
- See `src/services/dummy_data_provider.py` or `src/services/sv30_data_provider.py` for reference implementations

**Required Methods**:
- `generate_t0_data()` - Generate initial measurements at test start (for local display only)
- `generate_t30_data(initial_data, test_duration_minutes)` - Generate final measurements (sent to backend)
- `generate_height_history(initial_data, duration_minutes, interval_seconds)` - Generate periodic height updates (for local display)

**Data Format**: All methods must return dictionaries matching the `SludgeData` and `SludgeHeightEntry` interfaces (see `src/models/types.py`). Data format must match backend schema exactly.

For detailed ML integration instructions, see [ML_INTEGRATION.md](ML_INTEGRATION.md).

## Backend Integration

The server automatically sends test data to the backend server via Socket.IO:

- `sludge-data` event: **Only t=30 (final) measurements** are sent to backend
- `test-warning` event: Test-related warnings (if any)

**Note**: 
- t=0 data is kept locally for frontend display and height history generation
- Only final t=30 data is sent to backend (matches backend's "one complete payload" expectation)
- Backend stores one record per factory/date/testType and replaces entire data field on update

## Code Organization

- **`src/api/`**: API routes and WebSocket handlers
- **`src/config.py`**: Centralized configuration management
- **`src/models/`**: Data models, state machine, and type definitions
- **`src/services/`**: Business logic (data generation, backend communication)
- **`src/utils/`**: Utility functions (authentication, helpers)
- **`static/`**: Frontend files (HTML, CSS, JavaScript)

## Troubleshooting

### WebSocket Connection Issues

If WebSocket fails, the system automatically falls back to polling (HTTP requests every second).

### Backend Connection Issues

Check that:
- Backend server is running
- `BACKEND_URL` is correct
- Network connectivity is available
- Firewall allows connections

### Test Not Starting

- Ensure no test is currently running
- Check server logs for errors
- Verify backend connection

## Development

### Switching Data Providers

The system currently uses `SV30DataProvider` by default (real pipeline integration). To switch:

1. **Use Dummy Data Provider**: Edit `src/app.py` line 70, comment out `SV30DataProvider` and uncomment `DummyDataProvider`
2. **Use Custom ML Model**: See [ML_INTEGRATION.md](ML_INTEGRATION.md) for comprehensive guide

Quick steps for ML integration:
1. Create `src/services/ml_data_provider.py` implementing the `DataProvider` interface
2. Replace data provider instantiation in `src/app.py` (around line 70)
3. Implement the three required methods: `generate_t0_data()`, `generate_t30_data()`, and `generate_height_history()`
4. Ensure return format matches backend `SludgeData` schema exactly (see `src/models/types.py`)
5. Use IST timezone utilities from `src/utils/dateUtils.py` for all timestamps

### Customizing UI

- Edit `static/index.html` for page structure
- Edit `static/styles.css` for styling
- Edit `static/app.js` for behavior

### Raspberry Pi Auto-Start

For setting up automatic startup on Raspberry Pi, see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md).

## License

Part of the Thermax SV30 Test System.
