# ROS Docker Template
This repository provides a dockerfile to integrate ROS2 humble with a raspberry pi to control a drone via MAVLINK protocol.

## Initial Install Docker
- If you are raspberry pi or an arm64 architecture follow this link to install docker https://docs.docker.com/engine/install/debian/
  - Otherwise use this link https://docs.docker.com/engine/install/raspberry-pi-os/


## Setup
First off make the shell scripts inside the docker directory executable do this by doing the following command
```
cd docker
chmod +x *.sh
ls #you should see the shell scripts green
```
After you have made the shell scripts executable the build the docker images with the the following command
```
docker compose build
```
Now you need to pull out the submodules to make this work in the ros2 repo 
```
git submodule update --init --recursive
```
If you are running Software In The Loop, and have not installed ardupilot you can install ardupilot with the shell script provided by running the following command, this basically sets you up to run Ardupilot SITL
```
./useful_shell_scripts/download_ardupilot.sh
```
## Basic Usage
To run a docker container run the developer container 
```
docker compose up develop
```

Once that is running run a separate container using:
```
docker exec -it ros2_trajectory_docker-develop-1 bash
```
## Extending Volumes from your host
In the **docker-compose.yaml** to extend volumes from your host directory add the folder extension underneath the **volumes**
```yaml
 # develop image containing the example source code.
  # develop image containing the example source code.
  develop:
    extends: base
    image: ros2_pi:develop
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: develop
    # Interactive shell
    stdin_open: true
    tty: true
    # Networking and IPC for ROS 2
    network_mode: host
    ipc: host
    #port access from the container to the host
    ports:
    - "10000:10000"
    environment:
    - DISPLAY=${DISPLAY}
    - QT_X11_NO_MITSHM=1
    - NVIDIA_DRIVER_CAPABILITIES=all
    volumes:
    # - ./drone_ros:/develop_ws/src/drone_ros:rw
    # - ./mpc_ros:/develop_ws/src/mpc_ros:rw
    # - ./drone_interfaces:/develop_ws/src/drone_interfaces:rw
    # - ./unity_robotics_demo:/develop_ws/src/unity_robotics_demo:rw
    # - ./unity_robotics_demo_msgs:/develop_ws/src/unity_robotics_demo_msgs:rw
    command: sleep infinity
    logging:
      options:
        max-size: 50m # maximum size of log file before rotation
```
## Creating new packages
When creating a new package, make sure you are outside of any docker container. It is best to copy an existing package to use as a template
 - Extend the volumes in docker-compose.yml as shown in previous step
 - In the `package.xml` change the name
 ```xml
 <package format="3">
  <name>CHANGE THIS</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="jnguyenblue2804@gmail.com">justin</maintainer>
  <license>TODO: License declaration</license>
  ```
  When you add new nodes/scripts to your package add them to the executables in your `CMakeLists.txt` like this
  ```txt
  # Install Python modules
ament_python_install_package(${PROJECT_NAME})
# Install Python executables
install(PROGRAMS
  scripts/pub_example.py
  scripts/sub_example.py
  scripts/goal_vis.py
  scripts/target_estimator.py
  scripts/guidance_publisher.py
  scripts/testingsignals_SINL.py
  # scripts/client_member_function.py
  # scripts/service_member_function.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()
```
Rebuild the container using 
```
docker compose build
``` 
Enter the container, ensure you are in root directory and run 
```
colcon build --symlink-install
source install/setup.bash
```

## Helpful Shell Scripts/Commands
### Cleaning Dangling Containers
If you ever notice that you have a lot of dangling Docker containers run the following shell command
```
./clean_docker_out.sh
```
This will prune and remove any containers that have <None> tag

### GUI with Docker
```
xhost +local:docker 
```

# Demonstration of trajectory controller

## Run Ardupilot SITL
First off run ardupilot SITL, you can do this automatically by running the run_arduplane_host.sh in the useful_shell_scripts, you must change the directory to map it to where ardupilot is installed and also route out the IP address that you care about in the last line. Once you do that you can run the following line
```
./useful_shell_scripts/run_arduplane_host.sh
```
You can also open up missionplanner or QGC to get the connection  as well.
To make it takeoff do the following commands in the terminal from pops off
```
arm throttle
mode takeoff
takeoff 50
```
You might also need to increase the streamrate to do that in the terminal do the following command
```
set streamrate 100
```

## Run the ROS2 trajectory stack
Now you can run the docker container by doing the following command, this sets up the docker develop image
```
docker compose up develop
```
Once that is down on a separate terminal run the following command to open up and enter the container
```
docker exec -it ros2_trajectory_docker-develop-1 bash
```
If this is your first time using this workspace you need to compile the ros2 workspace by doing the following command
```
cd ../
colcon build --symlink-install
```

Now run the following command
```
../useful_shell_scripts/run_live.sh
```
This will open up 4 terminals for you, one of them will run mavros which allows ROS2 to get the information of the flight controller, the upper right pane will run Drone.py which is a ros node in the drone_ros package, this listens for the trajectory commands
