#!/bin/bash

# Adding this section to see if we can fix the usb port issues. If nothing ever happens that means it was never able to find the port
# Make sure the script exits on error
set -e

# Wait for /dev/ttyACM0 to appear
echo "Waiting for USB device /dev/ttyACM0..."
while [ ! -e /dev/ttyACM0 ]; do
    sleep 1
done
echo "Device found! Starting scripts..."

# =========================================================
# Precision Delivery Automation Script
# Starts tmux with MAVROS + signal pub/sub + rosbag
# Layout:
# ┌────────────┬────────────┐
# │ MAVROS     │ signal_sub │
# ├────────────┼────────────┤
# │ rosbag     │ signal_pub │
# └────────────┴────────────┘
# =========================================================

SESSION="precision_delivery"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Start new tmux session (detached)
tmux new-session -d -s $SESSION -n main

# Attempting to add manual commands to .sh file
tmux send-keys -t $SESSION:0.0 "colcon build --symlink-install" C-m
tmux send-keys -t $SESSION:0.0 "cp -r data/ install/precision_delivery/share/precision_delivery/" C-m

# ---------------------------------------------------------
# Pane 0 (top left) – MAVROS Node
# ---------------------------------------------------------
tmux send-keys -t $SESSION:0.0 "echo 'Starting MAVROS...'" C-m
tmux send-keys -t $SESSION:0.0 "ros2 run mavros mavros_node --ros-args -p fcu_url:=serial:///dev/ttyACM0:115200@ftdi" C-m

# Wait 5 seconds for MAVROS to connect
sleep 5

# ---------------------------------------------------------
# Create 4-pane grid
# ---------------------------------------------------------
# Split vertically (top/bottom)
tmux split-window -v -t $SESSION:0.0
# Split left panes horizontally (creates right top pane)
tmux split-window -h -t $SESSION:0.0
# Split bottom left horizontally (creates bottom right pane)
tmux split-window -h -t $SESSION:0.2

# Arrange all evenly
tmux select-layout -t $SESSION tiled

# ---------------------------------------------------------
# Assign panes
# ---------------------------------------------------------
# Pane 0 (top left): MAVROS (already running)
# Pane 1 (top right): signal_sub
# Pane 2 (bottom left): rosbag
# Pane 3 (bottom right): signal_pub

# signal_sub (top right)
tmux send-keys -t $SESSION:0.1 "echo 'Starting signal_sub...'" C-m
tmux send-keys -t $SESSION:0.1 "ros2 run precision_delivery signal_sub.py" C-m

# rosbag (bottom left)
tmux send-keys -t $SESSION:0.2 "echo 'Recording /mavros/rc/in...'" C-m
tmux send-keys -t $SESSION:0.2 "ros2 bag record /mavros/rc/in" C-m

# signal_pub (bottom right)
tmux send-keys -t $SESSION:0.3 "echo 'Starting signal_pub...'" C-m
tmux send-keys -t $SESSION:0.3 "ros2 run precision_delivery signal_pub.py" C-m # Added auto run

# ---------------------------------------------------------
# Attach to session
# ---------------------------------------------------------
tmux attach -t $SESSION
