# Description: Run mavros node with specific fcu_url
# this fcu url is the pixhawk's ip address and port number
# in the simulation space this will be the ip address of the host machine running
# SITL simulation and the port number 14551
ros2 run mavros mavros_node --ros-args --param fcu_url:=udp://:14550@192.168.1.101

