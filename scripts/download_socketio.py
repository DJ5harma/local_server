#!/usr/bin/env python
"""
Download Socket.IO client library for local use.
"""
import urllib.request
from pathlib import Path

# Get the script directory and find static folder
script_dir = Path(__file__).parent.parent
static_dir = script_dir / "static"
socketio_file = static_dir / "socket.io.min.js"

# Ensure static directory exists
static_dir.mkdir(exist_ok=True)

# Download Socket.IO client
url = "https://cdn.socket.io/4.5.4/socket.io.min.js"
print(f"Downloading Socket.IO client from {url}...")
print(f"Saving to {socketio_file}...")

urllib.request.urlretrieve(url, socketio_file)

print(f"Successfully downloaded Socket.IO client to {socketio_file}")
print(f"   File size: {socketio_file.stat().st_size / 1024:.1f} KB")

