# Requirements
- Docker service will be ran at the start:
    - The commander node will cache the commands of the servo and wait until 
    pin mechanism is released
    - When the pin mechanism is released the servo commands will then be published to the servos
    - Data/telemetry of the roll,pitch,yaw,velocity, position will then be recorded
    - Lift/Drag ratio will then be computed 

## Inputs
- Students need to generate csv with the following format
- time
- channel_1
- channel_2
- channel_3
- channel_4
- Values must be in RADIANS!

# Lighter weight
- Use pymavlink to interface instead of mavros
- mavlink-router forwards out three ports from usb port:
    - 127.0.0.1:14551 -> Signal subscriber node
    - 127.0.0.1:14552 -> payload publisher node
- Signal publisher node -> Publishes csv commands to /servo_n topic
- Signal subscriber node subscribes to /servo_n topic and sends servo commands via mavlink protocol since servos are connected to pixracer
- Payload publisher publishes Telem message with information of payload
- Rosbag will now cache the telem message protocol 
