#!/bin/bash

# Configuration
PYTHON_SCRIPT="main.py"
RUN_TIME=3600  # 1 hour in seconds
VIRTUAL_ENV_PATH="./venv"  # Replace with your actual virtual env path

# Function to run the script with a time limit
run_with_timeout() {
    # Activate virtual environment
    source "$VIRTUAL_ENV_PATH/bin/activate"
    
    # Start the script in background
    python "$PYTHON_SCRIPT" &
    PID=$!
    
    # Wait for specified time
    echo "Script started with PID: $PID"
    echo "Running for $RUN_TIME seconds..."
    sleep $RUN_TIME
    
    # Kill the process
    echo "Time's up! Stopping script..."
    kill -9 $PID
    
    # Deactivate virtual environment
    deactivate
    
    echo "Script stopped. Restarting in 5 seconds..."
    sleep 5
}

# Main loop to keep restarting the script
echo "=== Script Runner ==="
echo "Will run $PYTHON_SCRIPT for $RUN_TIME seconds repeatedly"

while true; do
    echo "====================================="
    echo "Starting new run at $(date)"
    echo "====================================="
    run_with_timeout
done