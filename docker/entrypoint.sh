#!/bin/bash
# Basic entrypoint for ROS / Colcon Docker containers

# Source ROS 2 Humble
source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
echo "Sourced ROS 2 Humble"

# Source the base workspace, if built
if [ -f /ros2_ws/install/setup.bash ]
then
  echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc
fi

# Source the overlay workspace, if built
if [ -f /develop_ws/install/setup.bash ]
then
  echo "source /develop_ws/install/setup.bash" >> ~/.bashrc
  source /develop_ws/install/setup.bash
  echo "Sourced ROS developer workspace"
fi

# --- Run your scripts sequentially --- Lab Changes
if [ -x "/develop_ws/run_prepare_container.sh" ]; then
    echo "Running container preparation script..."
    /develop_ws/run_prepare_container.sh
else
    echo "Error: run_prepare_container.sh not found or not executable"
    exit 1
fi

if [ -x "/develop_ws/run_multisines.sh" ]; then
    echo "Running multisines script..."
    /develop_ws/run_multisines.sh
else
    echo "Error: run_multisines.sh not found or not executable"
    exit 1
fi

# Execute the command passed into this entrypoint
exec "$@"

