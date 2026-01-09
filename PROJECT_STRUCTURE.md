# Project Structure

## Overview

The project is organized with clear separation of concerns following best practices.

```
local_server/
├── src/                          # Source code
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # Main Flask application
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── routes.py            # HTTP API routes
│   │   └── websocket.py         # WebSocket handlers
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── test_state.py        # Test state machine
│   │   └── types.py             # Type definitions
│   │
│   ├── services/                # Business logic
│   │   ├── __init__.py
│   │   ├── data_provider.py     # DataProvider interface (abstract base class)
│   │   ├── dummy_data_provider.py  # Dummy data generator (for testing)
│   │   ├── sv30_data_provider.py   # Real SV30 pipeline integration
│   │   ├── test_service.py      # Test lifecycle management
│   │   ├── test_monitor.py      # Background test monitoring
│   │   └── backend_client.py    # Backend Socket.IO client
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       ├── dateUtils.py         # IST timezone utilities
│       └── results_storage.py   # Local results file storage
│
├── static/                       # Frontend files
│   ├── index.html               # HMI interface
│   ├── styles.css               # Styling
│   └── app.js                   # Frontend logic
│
├── config/                       # Configuration templates
│   └── .env.example             # Environment variables template
│
├── scripts/                      # Utility scripts
│   └── create_env.py            # Create .env file
│
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── QUICKSTART.md                 # Quick start guide
└── .gitignore                    # Git ignore rules
```

## Module Responsibilities

### `src/app.py`
- Main Flask application setup
- Dependency injection
- Data provider selection (SV30DataProvider or DummyDataProvider)
- Background task management
- Application lifecycle (startup/shutdown)

### `src/config.py`
- Centralized configuration management
- Environment variable loading
- Configuration validation
- Path management

### `src/api/routes.py`
- HTTP API endpoints
- Request/response handling
- Business logic orchestration

### `src/api/websocket.py`
- WebSocket connection handling
- Real-time data streaming
- Client management

### `src/models/test_state.py`
- Test state machine
- Thread-safe state management
- Test lifecycle tracking

### `src/models/types.py`
- Type definitions
- Data structure interfaces
- Request/response models

### `src/services/data_provider.py`
- Abstract `DataProvider` interface
- Defines contract for all data providers

### `src/services/dummy_data_provider.py`
- Dummy data generation for testing
- Generates realistic test data with random values
- Uses IST timezone for all timestamps

### `src/services/sv30_data_provider.py`
- Real SV30 pipeline integration
- Runs `sv30_pipeline/main.py` as subprocess
- Reads results from pipeline output files
- Uses IST timezone for all timestamps

### `src/services/test_service.py`
- Test lifecycle management
- Coordinates between data provider, state manager, and backend client
- Handles test start, completion, and data generation

### `src/services/test_monitor.py`
- Background monitoring of test state
- Auto-completes tests when duration elapses
- WebSocket broadcasting

### `src/services/backend_client.py`
- Backend server communication
- Socket.IO client management
- Data transmission

### `src/utils/dateUtils.py`
- Indian Standard Time (IST) timezone utilities
- Functions for IST-aware datetime operations
- UTC conversion for backend compatibility

### `src/utils/results_storage.py`
- Local file storage for test results
- Organizes results by date (IST dates)
- Saves sludge data and height updates

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a single responsibility
2. **Maintainability**: Easy to locate and modify code
3. **Testability**: Components can be tested in isolation
4. **Scalability**: Easy to add new features without cluttering
5. **Readability**: Clear organization makes code easy to understand

## Adding New Features

### Adding a New API Endpoint
1. Add route handler in `src/api/routes.py`
2. Add request/response models in `src/models/types.py` if needed
3. Update API documentation

### Adding a New Service
1. Create file in `src/services/`
2. Export from `src/services/__init__.py`
3. Use in routes or other services

### Adding Configuration
1. Add to `src/config.py`
2. Update `.env.example`
3. Document in README

## Key Features

### Timezone Support
- All datetime operations use Indian Standard Time (IST - UTC+5:30)
- Timestamps sent to backend are converted to UTC ISO format
- Local file organization uses IST dates

### Data Flow
- t=0 data: Generated and stored locally (for frontend display, NOT sent to backend)
- t=30 data: Generated and sent to backend (final results)
- Height history: Generated locally for frontend display

### Data Providers
- `SV30DataProvider`: Real pipeline integration (default)
- `DummyDataProvider`: Testing/development
- Easy to add custom ML model providers

