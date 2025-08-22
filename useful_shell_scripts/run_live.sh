#!/bin/bash

# Start a new tmux session and window
tmux new-session -d -s MavrosSession

# Split the window into four horizontal panes
tmux split-window -h
tmux split-window -v -t 0
tmux split-window -v -t 2

# Navigate and run the script in pane 1
tmux send-keys -t 0 'ros2 run rviz2 rviz2' C-m

# Run mavros_node in pane 2
tmux send-keys -t 1 'ros2 run mavros mavros_node --ros-args --param fcu_url:=udp://:14552@127.0.0.1' C-m

# Run Drone.py in pane 3
tmux send-keys -t 2 'ros2 run drone_ros Drone.py' C-m

# Select pane 4
tmux select-pane -t 'ros2 launch ros2_template_package vis_traj.launch.py' C-m

# Attach to the tmux session
tmux attach-session -d -t MavrosSession
