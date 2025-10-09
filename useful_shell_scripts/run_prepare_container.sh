#!/bin/bash
set -e  # Exit immediately if any command fails

echo "Starting container preparation..."

# Optional: Wait for USB device
# echo "Waiting for USB device /dev/ttyACM0..."
# while [ ! -e /dev/ttyACM0 ]; do
#     sleep 1
# done
# echo "Device found!"

# --- Build workspace ---
echo "Starting colcon build..."
colcon build --symlink-install
echo "Colcon build finished."

# --- Copy CSV files ---
echo "Copying CSV files..."
cp -r data/ install/precision_delivery/share/precision_delivery/
echo "CSV files copied."

# --- Run multisines script automatically ---
if [ -x "./run_multisines.sh" ]; then
    echo "Starting multisines script..."
    ./run_multisines.sh
else
    echo "Error: run_multisines.sh not found or not executable"
    exit 1
fi
