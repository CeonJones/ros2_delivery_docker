from pymavlink import mavutil

# Use the raw device path, baudrate as a separate arg
m = mavutil.mavlink_connection('/dev/serial0', baud=57600)

print("Waiting for heartbeat...")
m.wait_heartbeat()
print("HEARTBEAT RECEIVED from system %u component %u" %
      (m.target_system, m.target_component))

while True:
    msg = m.recv_match(blocking=True, timeout=2)
    if msg is None:
        print("No message in 2 seconds")
        continue
    print(msg)
