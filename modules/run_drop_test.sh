# #!/bin/bash

# SESSION="mypanes"

#!/bin/bash

# Start a new tmux session and window
tmux new-session -d -s MavrosSession

# Split the window into four horizontal panes
tmux split-window -h
tmux split-window -v -t 0
tmux split-window -v -t 2

# Navigate and run the script in pane 1
tmux send-keys -t 0 "mavproxy.py --master=/dev/ttyACM0 --baud=57600 \
 --out=127.0.0.1:14551 \
 --out=127.0.0.1:14552 \
 --out=127.0.0.1:14553" C-m

# Run mavros_node in pane 2
tmux send-keys -t 1 'python3 servo_signals.py' C-m

# Run Drone.py in pane 3
tmux send-keys -t 2 'python3 servo_signals.py' C-m

# Select pane 4
tmux select-pane -t 'python3 logger.py' C-m

# Attach to the tmux session
tmux attach-session -d -t MavrosSession

