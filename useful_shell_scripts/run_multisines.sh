#!/bin/bash
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
tmux send-keys -t $SESSION:0.2 "cd data/Output_Data/" C-m
# tmux send-keys -t $SESSION:0.2 "sudo rm -rf ros2bag" C-m
tmux send-keys -t $SESSION:0.2 "ros2 bag record /mavros/rc/in /servo_n" C-m

# signal_pub (bottom right)
tmux send-keys -t $SESSION:0.3 "echo 'Starting signal_pub...'" C-m
tmux send-keys -t $SESSION:0.3 \
  'ros2 service call /mavros/set_message_interval mavros_msgs/srv/MessageInterval "{message_id: 65, message_rate: 100.0}"' C-m
tmux send-keys -t $SESSION:0.3 "ros2 run precision_delivery signal_pub.py" C-m # Added auto run

# ---------------------------------------------------------
# Attach to session
# ---------------------------------------------------------
tmux attach -t $SESSION
