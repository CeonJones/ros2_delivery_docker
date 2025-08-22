#!/bin/bash
## This shell script runs the arduplane simulation on the host machine.
# The output from the sitl must be set to match the ip address of your raspberry pi/co-comptuer and the port number 14551
cd ../
cd /home/siya/ardupilot/ArduPlane # change this to the directory of your ardupilot stuff  
../Tools/autotest/sim_vehicle.py --map --console --out 127.0.0.1:14551 --out 127.0.0.1:14552 --out 127.0.0.1:14553 #These ports will be snowflake stuff 
