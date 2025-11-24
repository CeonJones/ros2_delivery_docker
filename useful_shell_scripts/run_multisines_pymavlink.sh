#!/bin/bash
# =========================================================
# Precision Delivery Automation Script
# Starts tmux with MAVROS + signal pub/sub + rosbag + payload_pub
# Layout (2x3 grid):
# ┌────────────┬────────────┬────────────┐
# │ MAVROS     │ signal_sub │ rosbag     │
# ├────────────┼────────────┼────────────┤
# │ signal_pub │ debug      │ payload_pub│
# └────────────┴────────────┴────────────┘
# =========================================================

SESSION="precision_delivery"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null

# Start new tmux session (detached)
tmux new-session -d -s $SESSION -n main

# Pane 0 — MAVROS
tmux send-keys -t $SESSION:0.0 "echo 'Starting Pymavlink...'" C-m
tmux send-keys -t $SESSION:0.0 "./run_mavros_router.sh" C-m

sleep 5  # Give MAVROS time to latch

# Create 6-pane layout
tmux split-window -v -t $SESSION:0.0
tmux split-window -h -t $SESSION:0.0
tmux split-window -h -t $SESSION:0.1
tmux split-window -h -t $SESSION:0.3
tmux split-window -h -t $SESSION:0.4

tmux select-layout -t $SESSION tiled

# Pane 1 — signal_sub
tmux send-keys -t $SESSION:0.1 "echo 'Starting signal_sub...'" C-m
tmux send-keys -t $SESSION:0.1 "ros2 run precision_delivery signal_sub.py" C-m

# Pane 2 — rosbag
tmux send-keys -t $SESSION:0.2 "echo 'Recording /telem ...'" C-m
tmux send-keys -t $SESSION:0.2 "cd data/Output_Data/" C-m
tmux send-keys -t $SESSION:0.2 "ros2 bag record /telem /servo_n" C-m

# Pane 3 — signal_pub
tmux send-keys -t $SESSION:0.3 "echo 'Starting signal_pub...'" C-m
tmux send-keys -t $SESSION:0.3 "ros2 run precision_delivery signal_pub.py" C-m

# Pane 4 — debug shell
tmux send-keys -t $SESSION:0.4 "echo 'Debug shell ready.'" C-m

# Pane 5 — payload_pub
tmux send-keys -t $SESSION:0.5 "echo 'Starting payload_pub...'" C-m
tmux send-keys -t $SESSION:0.5 "ros2 run precision_delivery payload_pub.py" C-m

# Attach to session
tmux attach -t $SESSION
