#!/bin/bash

# Configuration
# PYTHON_SCRIPT_INITAL="initalize.py"
PYTHON_SCRIPT="luna_main.py"
RUN_TIME=360  # 5 minutes max
VIRTUAL_ENV_PATH="./venv"  # Replace with your actual virtual env path

# echo "Starting initalization script..."
# source "$VIRTUAL_ENV_PATH/bin/activate"
# python "$PYTHON_SCRIPT_INITAL"

# Function to run the script with a time limit
run_loop() {
    # Activate virtual environment
    source "$VIRTUAL_ENV_PATH/bin/activate"
    
    # Start the script in background
    python "$PYTHON_SCRIPT" &
    PID=$!

    echo "Script started with PID: $PID"
    echo "Running for up to $RUN_TIME seconds..."
    
    # Monitor the process with timeout
    SECONDS=0
    while kill -0 $PID 2>/dev/null; do
        # Check if we've reached the time limit
        if [ $SECONDS -ge $RUN_TIME ]; then
            echo "Time's up! Stopping script..."
            kill -9 $PID 2>/dev/null
            break
        fi
        sleep 1
    done
    
    # Check if script ended naturally before timeout
    if [ $SECONDS -lt $RUN_TIME ]; then
        echo "Script ended naturally after $SECONDS seconds"
    fi
    
    # Deactivate virtual environment
    deactivate
    
    echo "Restarting in 30 seconds..."
    sleep 30
}

 

# Main loop to keep restarting the script
echo "=== Script Runner ==="
echo "Will run $PYTHON_SCRIPT for $RUN_TIME seconds repeatedly"

while true; do
    echo "====================================="
    echo "Starting new run at $(date)"
    echo "====================================="
    run_loop
done