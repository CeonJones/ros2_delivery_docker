# Telemetry message for Pixracer / UAV state

std_msgs/Header header

# ---------------- Global position (converted from GLOBAL_POSITION_INT) ----------------
# lat, lon in degrees
# alt in meters (AMSL)
# heading in degrees (0..360, yaw wrt north)
float64 lat
float64 lon
float32 alt
float32 heading

# ---------------- Attitude (quaternion + Euler) ----------------
# Quaternion attitude (ENU or NED depending on your convention)
float32 qx
float32 qy
float32 qz
float32 qw

# Euler angles in radians (same as MAVLink ATTITUDE)
float32 roll
float32 pitch
float32 yaw

# Body angular rates in rad/s
float32 roll_rate
float32 pitch_rate
float32 yaw_rate

# ---------------- Local position (NED frame, from LOCAL_POSITION_NED) ----------------
# Position in meters (NED)
float32 x
float32 y
float32 z

# Velocity in m/s (NED)
float32 vx
float32 vy
float32 vz

# ---------------- IMU data (from HIGHRES_IMU) ----------------
# Linear acceleration [m/s^2]
float32 ax
float32 ay
float32 az

# Angular velocity [rad/s]
float32 gx
float32 gy
float32 gz

# Magnetic field [Gauss]
float32 mx
float32 my
float32 mz
