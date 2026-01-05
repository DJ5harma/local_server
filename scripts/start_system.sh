#!/bin/bash
echo "Starting Thermax SV30 HMI Server..."
cd hmi_server
source venv/bin/activate
python run.py
