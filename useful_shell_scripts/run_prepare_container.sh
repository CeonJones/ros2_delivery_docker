#!/bin/bash

# Adding this section to see if we can fix the usb port issues. If nothing ever happens that means it was never able to find the port
# Make sure the script exits on error
#set -e

# Wait for /dev/ttyACM0 to appear
#echo "Waiting for USB device /dev/ttyACM0..."
#while [ ! -e /dev/ttyACM0 ]; do
#    sleep 1
#done
#echo "Device found! Starting scripts..."

SESSION="Container_Prep"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Start new tmux session (detached)
tmux new-session -d -s $SESSION -n main

# Attempting to add manual commands to .sh file
# Split vertically (top/bottom)
tmux send-keys -t $SESSION:0.0 "echo 'Starting colcon...'" C-m
tmux send-keys -t $SESSION:0.0 "colcon build --symlink-install" C-m

tmux send-keys -t $SESSION:0.0 "echo 'Copying CSV File...'" C-m
tmux send-keys -t $SESSION:0.0 "cp -r data/ install/precision_delivery/share/precision_delivery/" C-m

tmux attach -t $SESSION
tmux kill-session -t $SESSION 2>/dev/null

# --- Run multisines script automatically ---
if [ -x "./run_multisines.sh" ]; then
    echo "Starting multisines script..."
    ./run_multisines.sh
else
    echo "Error: run_multisines.sh not found or not executable"
    exit 1
fi