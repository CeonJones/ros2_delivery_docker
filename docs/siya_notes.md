# Main title
## Second Title
- bullet point 1
- bullet point 2 
- bullet point 3

```
put stuff here
```

## ROS2 Stuff

If this is your first time using this workspace you need to compile the ros2 workspace by doing the following command
```
cd ../
colcon build --symlink-install

source install/setup.bash 
```

Now run the following command to connect the drone to ROS
```
./useful_shell_scripts/run_live.sh
```
This will open up 4 terminals for you, one of them will run mavros which allows ROS2 to get the information of the flight controller, the upper right pane will run Drone.py which is a ros node in the drone_ros package, this listens for the trajectory commands


## Task For Cartesian Conversion from ROS2
- User story: Convert waypoints from mission planner to cartesian
- Expected Outcome: When user loads waypoints to Mission planner and runs guidance_publisher in GUIDED mode the UAS will loiter at the same locations as if it was in AUTO mode

- Need to access mission_items and convert them to cartesian from home location