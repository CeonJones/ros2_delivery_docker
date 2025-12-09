#!/bin/bash

SESSION="mypanes"

# Create new tmux session
tmux new-session -d -s $SESSION

### --- Pane 1: MAVProxy --- ###
tmux send-keys -t $SESSION \
"mavproxy.py --master=/dev/ttyACM0 --baud=57600 \
 --out=127.0.0.1:14551 \
 --out=127.0.0.1:14552 \
 --out=127.0.0.1:14553" C-m

### --- Split for Pane 2 --- ###
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION:0.1 "python3 servo_signals.py" C-m

### --- Split Pane 1 vertically for Pane 3 --- ###
tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION
tmux send-keys -t $SESSION:0.2 "python3 logger.py" C-m

### --- Split Pane 2 vertically for Pane 4 --- ###
tmux select-pane -t $SESSION:0.1
tmux split-window -v -t $SESSION

# Attach to the final session
tmux attach -t $SESSION
