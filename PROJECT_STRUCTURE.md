# Project Structure

## Overview

The project is organized with clear separation of concerns following best practices.

```
local_server/
├── src/                          # Source code
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # Main FastAPI application
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
│   │   ├── data_generator.py    # Data generation (ML placeholder)
│   │   └── backend_client.py    # Backend Socket.IO client
│   │
│   └── utils/                   # Utilities
│       ├── __init__.py
│       └── auth.py              # Authentication utilities
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
- Main FastAPI application setup
- Dependency injection
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

### `src/services/data_generator.py`
- Test data generation (dummy)
- ML model integration point
- Data formatting

### `src/services/backend_client.py`
- Backend server communication
- Socket.IO client management
- Data transmission

### `src/utils/auth.py`
- Authentication logic
- Password verification
- Session management (future)

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

## Migration Notes

Old files (can be removed):
- `app.py` (root) → `src/app.py`
- `test_state.py` (root) → `src/models/test_state.py`
- `dummy_data.py` (root) → `src/services/data_generator.py`
- `backend_sender.py` (root) → `src/services/backend_client.py`

