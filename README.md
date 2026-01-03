# SV30 Test System - Local HMI Server

Local server for SV30 test system HMI interface. Runs on Raspberry Pi and serves the operator interface for running SV30 tests.

## Project Structure

```
local_server/
├── src/                    # Source code
│   ├── api/               # API routes and WebSocket handlers
│   ├── config.py          # Configuration management
│   ├── models/            # Data models and state management
│   ├── services/          # Business logic (data generation, backend client)
│   ├── utils/             # Utility functions
│   └── app.py             # Main FastAPI application
├── static/                 # Frontend files (HTML, CSS, JS)
├── config/                 # Configuration templates
├── scripts/                # Utility scripts
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Features

- **6-Page HMI Flow**: Login → Home → Start → Progress → Completion → Results
- **Real-time Updates**: WebSocket and polling support for live test progress
- **Backend Integration**: Automatically sends test data to backend server via Socket.IO
- **Dummy Data Generator**: Realistic test data generation (to be replaced with ML model)
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

Or using uvicorn directly:
```bash
uvicorn src.app:app --host 0.0.0.0 --port 5000
```

**Note**: Always activate the virtual environment before running the server to ensure you're using the correct Python packages.

## Configuration

Environment variables (in `.env` file):

- `LOGIN_PASSWORD` - Password for HMI login (default: "thermax")
- `PORT` - Server port (default: 5000)
- `TEST_DURATION_MINUTES` - Test duration in minutes (default: 30)
- `BACKEND_URL` - Backend server URL (default: `http://localhost:4000`)
- `FACTORY_CODE` - Factory identifier (default: `"factory-a"`)

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

1. **t=0**: Generate initial data → Display on HMI → Send to backend
2. **During test (every 10s)**: Generate height updates → Display on HMI → Send to backend
3. **t=30**: Generate final data → Display on HMI → Send to backend → Show results

## Integration with ML Model

The `src/services/data_generator.py` module contains placeholder functions that will be replaced with actual ML model calls:

- `generate_t0_data()` - Replace with ML model call at test start
- `generate_t30_data()` - Replace with ML model call at test end
- `generate_height_history()` - Replace with periodic ML model calls

The data structure matches the `SludgeData` interface from the backend, ensuring seamless integration.

## Backend Integration

The server automatically sends all test data to the backend server via Socket.IO:

- `sludge-data` event: t=0 and t=30 measurements
- `sludge-height-update` event: Periodic height updates
- `test-warning` event: Test-related warnings

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

### Replacing Dummy Data with ML Model

1. Edit `src/services/data_generator.py`
2. Replace functions with ML model calls
3. Ensure return format matches `SludgeData` interface
4. Test with actual hardware/ML model

### Customizing UI

- Edit `static/index.html` for page structure
- Edit `static/styles.css` for styling
- Edit `static/app.js` for behavior

## License

Part of the Thermax SV30 Test System.
