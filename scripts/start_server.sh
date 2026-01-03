#!/bin/bash
# Startup script for SV30 Test System HMI Server
# This script activates the virtual environment and starts the server

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source venv/bin/activate

# Start the server
python run.py

