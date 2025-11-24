#!/bin/bash

# Assign the first argument to SERIAL_DEVICE, default to /dev/ttyACM0 if not provided
SERIAL_DEVICE=${1:-/dev/ttyACM0}

# Assign the second argument to BAUD_RATE, default to 57600 if not provided
BAUD_RATE=${2:-921600}

# Assign the third argument to IP1, default to 192.168.1.101 if not provided
# this is the 
IP1=${3:-192.168.253.143}

# Assign the fourth argument to PORT1, default to 14550 if not provided
PORT1=${4:-14550}

# Assign the fifth argument to IP2, default to 127.0.0.1 if not provided
IP2=${5:-127.0.0.1}

# Assign the sixth argument to PORT2, default to 14550 if not provided 
PORT2=${6:-14550} 
PORT3=${7:-14551}
PORT4=${8:-14552}

# Echo the configuration for confirmation
echo "Starting mavlink-routerd with the following configuration:"
echo "Serial Device: $SERIAL_DEVICE"
echo "Baud Rate: $BAUD_RATE"
echo "Endpoint 1: $IP1:$PORT1"
echo "Endpoint 2: $IP2:$PORT2"
echo "Endpoint 3: $IP2:$PORT3"
echo "Endpoint 4: $IP2:$PORT4"

# Execute mavlink-routerd with the provided settings
mavlink-routerd -e $IP1:$PORT1 -e $IP2:$PORT2 -e $IP2:$PORT3 -e $IP2:$PORT4 $SERIAL_DEVICE:$BAUD_RATE 