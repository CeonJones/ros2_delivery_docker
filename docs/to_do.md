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

# Software
