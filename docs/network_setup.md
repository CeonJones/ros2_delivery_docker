# Network set up
To be able to have different machines communicate with each other via ROS2 and Docker do the following

In your ~/.bashrc directory set the following environment variables where the machine_ip_address can be found via ipconfig
```
export ROS_DOMAIN_ID=0
export ROS_IP=<machine_ip_address>
```