#!/usr/bin/env python3
"""
Payload Telemetry Logger (no ROS2)

- Connects to Pixracer via MAVLink (through mavlink-router UDP endpoint).
- Requests attitude, position, IMU, and servo output streams at a fixed rate.
- Logs everything to a CSV file.

Intended for low-resource boards like the Pi Zero.
"""

import math
import time
import csv
import os
from datetime import datetime

from pymavlink import mavutil


class PayloadTelemLogger:
    def __init__(self):
        # ==============================
        # CONFIG
        # ==============================
        # MAVLink connection (usually via mavlink-router)
        self.mav_connection_string = "udp:127.0.0.1:14551"

        # Telemetry frequency (Hz)
        self.payload_frequency = 30  # same as your original node

        # Logging config
        self.output_dir = "./logs"
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(
            self.output_dir, f"payload_telem_{timestamp_str}.csv"
        )

        # Optional: stop after N samples or after duration (seconds)
        # Set to None for unlimited.
        self.max_samples = None
        self.max_duration_s = None  # e.g. 600 for 10 minutes

        self.master = None
        self.csv_file = None
        self.csv_writer = None

        self._init_master_connection()
        self._start_listening()
        self._init_csv()

    # ------------------------------------------------------------------
    # MAVLink setup
    # ------------------------------------------------------------------
    def _init_master_connection(self) -> None:
        print(f"[MAVLINK] Connecting to {self.mav_connection_string} ...")
        self.master: mavutil.mavlink_connection = mavutil.mavlink_connection(
            self.mav_connection_string
        )
        self.master.wait_heartbeat()
        print(
            f"[MAVLINK] Connected to sysid={self.master.target_system}, "
            f"compid={self.master.target_component}"
        )

        # Send one heartbeat so mavlink-router latches this endpoint
        self.master.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0,
            0,
            0,
        )

    def _start_listening(self) -> None:
        """
        Configure the drone to send telemetry messages at the desired rate.
        """
        freq = self.payload_frequency

        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, freq
        )
        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, freq
        )
        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT, freq
        )
        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE_QUATERNION, freq
        )
        # IMU-ish messages: prefer SCALED_IMU; RAW_IMU as fallback
        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_SCALED_IMU, freq
        )
        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_RAW_IMU, freq
        )
        # Servo outputs (commanded outputs to actuators)
        self._request_message_interval(
            mavutil.mavlink.MAVLINK_MSG_ID_SERVO_OUTPUT_RAW, freq
        )

        print(f"[MAVLINK] Requested telemetry streams at {freq} Hz")

    def _request_message_interval(self, msg_id: int, frequency_hz: int) -> None:
        """
        Request a specific MAVLink message at a desired frequency.
        """
        if frequency_hz <= 0:
            print(
                f"[MAVLINK] Frequency for msg ID {msg_id} <= 0, not requesting stream."
            )
            return

        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
            0,  # confirmation
            msg_id,  # message ID
            1e6 / frequency_hz,  # interval in microseconds
            0,
            0,
            0,
            0,
            0,
        )

    # ------------------------------------------------------------------
    # CSV setup
    # ------------------------------------------------------------------
    def _init_csv(self) -> None:
        """
        Open CSV file and write header.
        """
        print(f"[LOG] Logging telemetry to {self.output_path}")
        self.csv_file = open(self.output_path, mode="w", newline="")
        self.csv_writer = csv.writer(self.csv_file)

        # Match fields from your Telem message + servo outputs
        header = [
            "timestamp",  # UNIX time (s)
            "lat",
            "lon",
            "alt",
            "heading",
            "qx",
            "qy",
            "qz",
            "qw",
            "roll",
            "pitch",
            "yaw",
            "roll_rate",
            "pitch_rate",
            "yaw_rate",
            "x",
            "y",
            "z",
            "vx",
            "vy",
            "vz",
            "ax",
            "ay",
            "az",
            "gx",
            "gy",
            "gz",
            "mx",
            "my",
            "mz",
            # Servo outputs (µs) – SERVO_OUTPUT_RAW
            "servo1_raw",
            "servo2_raw",
            "servo3_raw",
            "servo4_raw",
            "servo5_raw",
            "servo6_raw",
            "servo7_raw",
            "servo8_raw",
        ]
        self.csv_writer.writerow(header)
        self.csv_file.flush()

    # ------------------------------------------------------------------
    # Data path: MAVLink -> row dict
    # ------------------------------------------------------------------
    def _get_telem_row(self):
        """
        Retrieve the latest telemetry data from the drone and return as a dict.
        Similar to _get_telem() in your ROS2 node, but using a simple dict.
        """
        row = {
            "timestamp": time.time(),
            "lat": 0.0,
            "lon": 0.0,
            "alt": 0.0,
            "heading": 0.0,
            "qx": 0.0,
            "qy": 0.0,
            "qz": 0.0,
            "qw": 1.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "roll_rate": 0.0,
            "pitch_rate": 0.0,
            "yaw_rate": 0.0,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "vx": 0.0,
            "vy": 0.0,
            "vz": 0.0,
            "ax": 0.0,
            "ay": 0.0,
            "az": 0.0,
            "gx": 0.0,
            "gy": 0.0,
            "gz": 0.0,
            "mx": 0.0,
            "my": 0.0,
            "mz": 0.0,
            "servo1_raw": 0,
            "servo2_raw": 0,
            "servo3_raw": 0,
            "servo4_raw": 0,
            "servo5_raw": 0,
            "servo6_raw": 0,
            "servo7_raw": 0,
            "servo8_raw": 0,
        }

        # Wait for at least one of these to update master.messages
        _ = self.master.recv_match(
            type=[
                "LOCAL_POSITION_NED",
                "ATTITUDE",
                "ATTITUDE_QUATERNION",
                "GLOBAL_POSITION_INT",
                "SCALED_IMU",
                "RAW_IMU",
                "SERVO_OUTPUT_RAW",
            ],
            blocking=True,
        )

        try:
            # ---------------- GPS / GLOBAL POSITION ----------------
            if "GLOBAL_POSITION_INT" in self.master.messages:
                gp = self.master.messages["GLOBAL_POSITION_INT"]
                # lat / lon: 1e7 deg, alt: mm, hdg: cdeg
                row["lat"] = gp.lat / 1e7
                row["lon"] = gp.lon / 1e7
                row["alt"] = gp.alt / 1000.0
                row["heading"] = gp.hdg / 100.0  # degrees

            # ---------------- ATTITUDE QUATERNION ----------------
            if "ATTITUDE_QUATERNION" in self.master.messages:
                aq = self.master.messages["ATTITUDE_QUATERNION"]
                row["qx"] = aq.q1
                row["qy"] = aq.q2
                row["qz"] = aq.q3
                row["qw"] = aq.q4

            # ---------------- ATTITUDE (Euler + rates) ----------------
            if "ATTITUDE" in self.master.messages:
                att = self.master.messages["ATTITUDE"]
                row["roll"] = att.roll       # rad
                row["pitch"] = att.pitch     # rad
                row["yaw"] = att.yaw         # rad

                row["roll_rate"] = att.rollspeed     # rad/s
                row["pitch_rate"] = att.pitchspeed   # rad/s
                row["yaw_rate"] = att.yawspeed       # rad/s

            # ---------------- LOCAL POSITION (NED) ----------------
            if "LOCAL_POSITION_NED" in self.master.messages:
                lp = self.master.messages["LOCAL_POSITION_NED"]
                row["x"] = lp.x
                row["y"] = lp.y
                row["z"] = lp.z
                row["vx"] = lp.vx
                row["vy"] = lp.vy
                row["vz"] = lp.vz

            # ---------------- IMU DATA ----------------
            # Prefer SCALED_IMU if available (nice physical units)
            if "SCALED_IMU" in self.master.messages:
                imu = self.master.messages["SCALED_IMU"]
                # ArduPilot: accel in milli-g (mG), gyro in deg/s, mag in some scaled units
                mG_to_mps2 = 9.80665 / 1000.0
                deg_to_rad = math.pi / 180.0

                row["ax"] = imu.xacc * mG_to_mps2
                row["ay"] = imu.yacc * mG_to_mps2
                row["az"] = imu.zacc * mG_to_mps2

                row["gx"] = imu.xgyro * deg_to_rad
                row["gy"] = imu.ygyro * deg_to_rad
                row["gz"] = imu.zgyro * deg_to_rad

                row["mx"] = float(imu.xmag)
                row["my"] = float(imu.ymag)
                row["mz"] = float(imu.zmag)

            elif "RAW_IMU" in self.master.messages:
                imu = self.master.messages["RAW_IMU"]
                # raw units, not scaled – you can post-process later
                row["ax"] = float(imu.xacc)
                row["ay"] = float(imu.yacc)
                row["az"] = float(imu.zacc)

                row["gx"] = float(imu.xgyro)
                row["gy"] = float(imu.ygyro)
                row["gz"] = float(imu.zgyro)

                row["mx"] = float(imu.xmag)
                row["my"] = float(imu.ymag)
                row["mz"] = float(imu.zmag)

            # ---------------- SERVO OUTPUTS ----------------
            # SERVO_OUTPUT_RAW: servo1_raw..servo8_raw (µs)
            if "SERVO_OUTPUT_RAW" in self.master.messages:
                so = self.master.messages["SERVO_OUTPUT_RAW"]
                # Depending on ArduPilot version, fields are named servo1_raw...servo8_raw
                row["servo1_raw"] = getattr(so, "servo1_raw", 0)
                row["servo2_raw"] = getattr(so, "servo2_raw", 0)
                row["servo3_raw"] = getattr(so, "servo3_raw", 0)
                row["servo4_raw"] = getattr(so, "servo4_raw", 0)
                row["servo5_raw"] = getattr(so, "servo5_raw", 0)
                row["servo6_raw"] = getattr(so, "servo6_raw", 0)
                row["servo7_raw"] = getattr(so, "servo7_raw", 0)
                row["servo8_raw"] = getattr(so, "servo8_raw", 0)

        except KeyError:
            # If some data is missing, we just return what we have (zeros for missing)
            pass

        return row

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        print("[LOG] Starting telemetry logging loop...")
        dt = 1.0 / float(self.payload_frequency)
        start_time = time.time()
        sample_count = 0

        try:
            while True:
                loop_start = time.time()

                # Check duration limit (if any)
                if self.max_duration_s is not None:
                    if loop_start - start_time > self.max_duration_s:
                        print("[LOG] Max duration reached, stopping logging.")
                        break

                # Check sample limit (if any)
                if self.max_samples is not None and sample_count >= self.max_samples:
                    print("[LOG] Max sample count reached, stopping logging.")
                    break

                row_dict = self._get_telem_row()

                # Write CSV row
                self.csv_writer.writerow([
                    row_dict["timestamp"],
                    row_dict["lat"],
                    row_dict["lon"],
                    row_dict["alt"],
                    row_dict["heading"],
                    row_dict["qx"],
                    row_dict["qy"],
                    row_dict["qz"],
                    row_dict["qw"],
                    row_dict["roll"],
                    row_dict["pitch"],
                    row_dict["yaw"],
                    row_dict["roll_rate"],
                    row_dict["pitch_rate"],
                    row_dict["yaw_rate"],
                    row_dict["x"],
                    row_dict["y"],
                    row_dict["z"],
                    row_dict["vx"],
                    row_dict["vy"],
                    row_dict["vz"],
                    row_dict["ax"],
                    row_dict["ay"],
                    row_dict["az"],
                    row_dict["gx"],
                    row_dict["gy"],
                    row_dict["gz"],
                    row_dict["mx"],
                    row_dict["my"],
                    row_dict["mz"],
                    row_dict["servo1_raw"],
                    row_dict["servo2_raw"],
                    row_dict["servo3_raw"],
                    row_dict["servo4_raw"],
                    row_dict["servo5_raw"],
                    row_dict["servo6_raw"],
                    row_dict["servo7_raw"],
                    row_dict["servo8_raw"],
                ])
                sample_count += 1

                # Flush periodically to avoid losing data on crash
                if sample_count % 50 == 0:
                    self.csv_file.flush()

                # Sleep to roughly match payload_frequency
                elapsed = time.time() - loop_start
                sleep_time = dt - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("[LOG] Interrupted by user, stopping logging...")

        finally:
            if self.csv_file is not None:
                self.csv_file.flush()
                self.csv_file.close()
            if self.master is not None:
                try:
                    self.master.close()
                except Exception:
                    pass
            print(f"[LOG] Logging finished, samples={sample_count}")


def main():
    logger = PayloadTelemLogger()
    logger.run()


if __name__ == "__main__":
    main()
