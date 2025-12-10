#!/usr/bin/env python3
import os
import time
import math
import subprocess
from typing import Dict

import numpy as np
from pymavlink import mavutil

# If ros2_sid is still available as a plain Python package, this will work.
# Otherwise, replace this import with your own multi_sine implementation.
from inputdesign import multi_sine
from limit_switch_pi5 import LimitSwitch

USE_PIZERO_LIMIT_SWITCH = True  # Set to False to skip limit switch check
SWITCH_GPIO_LINE = 19          # GPIO line for limit switch (BCM numbering)


class MultisineMAVController:
    """
    Combined functionality of:
      - MultisinePublisher (signal generation / CSV IO / tmux control)
      - SignalSubscriber (pymavlink connection, rad->PWM, MAV_CMD_DO_SET_SERVO)

    No ROS2 is used here.
    """

    def __init__(self):
        # ==============================
        # CONFIG: Multisine parameters
        # ==============================
        self.servo_num: int = 4               # number of servo channels to excite
        self.amp_deg: float = 45.0            # amplitude in degrees
        self.min_freq_hz: float = 1.0         # lowest excitation frequency
        self.max_freq_hz: float = 2.0         # highest excitation frequency
        self.time_step: float = 0.02          # sampling period (sec)
        self.total_time: float = 10.0         # total maneuver time (sec)

        self.save_csv: bool = True
        self.use_csv: bool = True
        self.loop: bool = True
        self.max_loops: int = 3               # number of loops for maneuver
        self.parse: bool = False              # whether to run Parcer.py afterwards

        self.limit_switch: LimitSwitch = self.setup_limit_switch()

        # Directory and file name for CSV signals

        self.cwd: str = "/home/cuav/ros2_delivery_docker"
        # add into data/Input_Data/
        self.data_dir: str = os.path.join(self.cwd, "data", "Input_Data")
        self.csv_path: str = self.data_dir
        self.csv_filename: str = "input_signal.csv"

        # Optional secondary signals directory (if present)
        # This is where your ROS2 package used to save signals.
        # We keep it, but we don't rely on ROS2; we'll just check the path.
        # adjust if needed
        self.precision_delivery_share: str = "/develop_ws/precision_delivery_share"

        # ==============================
        # CONFIG: MAVLink / servo mapping
        # ==============================
        self.mav_connection_string: str = "udp:127.0.0.1:14552"
        # self.mav_connection_string: str = "/dev/ttyACM0"

        self.baudrate: int = 115200

        self.min_angle_deg: float = -90.0
        self.max_angle_deg: float = 90.0
        self.min_pwm: int = 1000
        self.max_pwm: int = 2200

        self.servo_start_index: int = 1   # first MAV servo index (1→SERVO1)
        # rate limit (should usually match 1/time_step)
        self.cmd_rate_hz: float = 20.0

        # tmux session name for post-maneuver commands
        self.tmux_session_name: str = "precision_delivery"

        # Internal state
        self.loop_count: int = 0
        self.master = None
        self.maneuver: Dict[str, np.ndarray] = {}

        # Build everything
        self._setup_mavlink()
        self.maneuver = self._build_maneuver()

    def setup_limit_switch(self) -> LimitSwitch:
        limit_switch = LimitSwitch(line=SWITCH_GPIO_LINE)  # GPIO19
        limit_switch.setup()
        return limit_switch

    # =========================================================
    # MAVLINK SETUP
    # =========================================================
    def _setup_mavlink(self):
        print(
            f"[MAVLINK] Connecting to {self.mav_connection_string} @ {self.baudrate}")
        self.master = mavutil.mavlink_connection(
            self.mav_connection_string, baud=115200)

        print("[MAVLINK] Waiting for heartbeat...")
        self.master.wait_heartbeat()
        print(
            f"[MAVLINK] Heartbeat received from system {self.master.target_system}, "
            f"component {self.master.target_component}"
        )

    # =========================================================
    # MULTISINE BUILDING / CSV HANDLING
    # =========================================================
    def _build_maneuver(self) -> Dict[str, np.ndarray]:
        """
        Build an N-channel multisine maneuver and optionally save it to CSV.
        Returns:
          {
            'time': (N_samples,) float64,
            'signal': (N_samples, servo_num) float64,
            'time_step': float,
            'total_time': float
          }
        """
        time_step = self.time_step
        total_time = self.total_time
        csv_path = self.csv_path
        save_csv = self.save_csv
        csv_filename = self.csv_filename
        filepath = os.path.join(csv_path, csv_filename)

        # 1) Try loading from configured Input_Data path
        if self.use_csv:
            print(f"[MANEUVER] Trying to load CSV from '{csv_path}'...")
            if os.path.exists(csv_path):
                csv_files = [
                    f for f in os.listdir(csv_path)
                    if f.startswith("input_signal") and f.endswith(".csv")
                ]
                if csv_files:
                    latest_file = max(
                        csv_files,
                        key=lambda f: os.path.getmtime(
                            os.path.join(csv_path, f))
                    )
                    filepath = os.path.join(csv_path, latest_file)
                    print(
                        f"[MANEUVER] Loading most recent input signal from: {filepath}")
                    data = np.loadtxt(filepath, delimiter=",",
                                      skiprows=1)  # Skip header
                    time_vec = data[:, 0]
                    signal_data = data[:, 1:]  # remaining columns
                    num_channels = signal_data.shape[1]
                    print(
                        f"[MANEUVER] CSV contains {len(time_vec)} samples with {num_channels} channels")

                    if num_channels != self.servo_num:
                        print(
                            f"[MANEUVER] WARNING: CSV has {num_channels} channels "
                            f"but servo_num is {self.servo_num}. Using CSV channel count."
                        )
                        self.servo_num = num_channels

                    return {
                        "time": time_vec,
                        "signal": signal_data,
                        "time_step": time_step,
                        "total_time": total_time,
                    }
                else:
                    print(
                        "[MANEUVER] No matching input_signal*.csv files found in Input_Data.")
            else:
                print(f"[MANEUVER] Input_Data path does not exist: {csv_path}")

            # 2) Try loading from a secondary "precision_delivery" signals directory (if it exists)
            signals_dir = os.path.join(
                self.precision_delivery_share, "data", "signals")
            print(f"[MANEUVER] Trying to load CSV from '{signals_dir}'...")
            if os.path.exists(signals_dir):
                csv_files = [
                    f for f in os.listdir(signals_dir)
                    if f.startswith("input_signals") and f.endswith(".csv")
                ]
                if csv_files:
                    latest_file = max(
                        csv_files,
                        key=lambda f: os.path.getmtime(
                            os.path.join(signals_dir, f))
                    )
                    filepath = os.path.join(signals_dir, latest_file)
                    print(
                        f"[MANEUVER] Loading most recent input signal from: {filepath}")
                    data = np.loadtxt(filepath, delimiter=",", skiprows=1)
                    time_vec = data[:, 0]
                    signal_data = data[:, 1:]
                    num_channels = signal_data.shape[1]
                    print(
                        f"[MANEUVER] CSV contains {len(time_vec)} samples with {num_channels} channels")

                    if num_channels != self.servo_num:
                        print(
                            f"[MANEUVER] WARNING: CSV has {num_channels} channels "
                            f"but servo_num is {self.servo_num}. Using CSV channel count."
                        )
                        self.servo_num = num_channels

                    return {
                        "time": time_vec,
                        "signal": signal_data,
                        "time_step": time_step,
                        "total_time": total_time,
                    }
                else:
                    print(
                        "[MANEUVER] No matching input_signals*.csv files found in precision_delivery_share.")
            else:
                print(
                    f"[MANEUVER] precision_delivery_share not found: {signals_dir}")

            print("[MANEUVER] No CSV files found — generating new multisine signal.")

        # 3) Generate a new multisine signal
        amp_deg = self.amp_deg
        min_freq_hz = self.min_freq_hz
        max_freq_hz = self.max_freq_hz
        amp_rad = np.deg2rad(amp_deg)

        # Error checks
        if time_step <= 0.0:
            raise ValueError("time_step must be > 0")
        if total_time <= 0.0:
            raise ValueError("total_time must be > 0")
        if max_freq_hz <= min_freq_hz:
            raise ValueError("max_freq_hz must be > min_freq_hz")
        if self.servo_num <= 0:
            raise ValueError("servo_num must be >= 1")

        print("\n=== Multisine Generation ===")
        print(f"Amplitude: {amp_deg}° ({amp_rad:.4f} rad)")
        print(f"Frequency Range: {min_freq_hz:.2f} – {max_freq_hz:.2f} Hz")
        print(
            f"Time Step: {time_step:.4f} s ({1.0 / time_step:.1f} Hz sample rate)")
        print(f"Total Time: {total_time:.1f} s")
        print(f"Servo Channels: {self.servo_num}")

        time_vec, signal, *_ = multi_sine(
            amp_rad,
            min_freq_hz,
            max_freq_hz,
            time_step,
            total_time,
            num_channels=self.servo_num,
        )

        print("\n=== Generated Signal ===")
        print(f"Signal Shape: {signal.shape} (samples x channels)")
        print(f"Time Vector Length: {len(time_vec)} samples")
        print(f"Signal Range: [{signal.min():.4f}, {signal.max():.4f}] rad")
        print(
            f"Signal Range: [{np.rad2deg(signal.min()):.2f}, {np.rad2deg(signal.max()):.2f}]°")
        print(f"First 5 values (channel 0): {signal[:5, 0]}")
        print(f"RMS value per channel: {np.sqrt(np.mean(signal**2, axis=0))}")

        if save_csv:
            mat = np.column_stack((time_vec, signal))
            # Save under precision_delivery_share/data/signals (or create it)
            signals_dir = os.path.join(
                self.precision_delivery_share, "data", "signals")
            os.makedirs(signals_dir, exist_ok=True)
            filepath = os.path.join(signals_dir, csv_filename)

            num_channels = mat.shape[1] - 1
            header = ["time"] + [f"channel_{i+1}" for i in range(num_channels)]

            import csv
            with open(filepath, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(header)
                writer.writerows(mat)

            print(f"[MANEUVER] Signal saved to: {filepath}")

        return {
            "time": time_vec,
            "signal": signal,
            "time_step": time_step,
            "total_time": total_time,
        }

    # =========================================================
    # RAD → PWM
    # =========================================================
    def radian_to_pwm(self, radian_value: float) -> int:
        """
        Convert angle in radians to PWM microseconds.
        Maps [min_angle_deg, max_angle_deg] to [min_pwm, max_pwm].
        """
        # degree_value = math.degrees(radian_value)
        degree_value = radian_value

        # Normalize degree value to [0,1]
        alpha_norm = (degree_value - self.min_angle_deg) / (
            self.max_angle_deg - self.min_angle_deg
        )
        pwm_value = self.min_pwm + alpha_norm * (self.max_pwm - self.min_pwm)

        # Clip
        pwm_value = int(max(self.min_pwm, min(self.max_pwm, pwm_value)))
        return pwm_value

    # =========================================================
    # MAIN RUN LOOP
    # =========================================================
    def run(self):
        signal = self.maneuver["signal"]
        time_step = self.maneuver["time_step"]

        # Use time_step as the command rate if they differ
        cmd_period = 1.0 / self.cmd_rate_hz if self.cmd_rate_hz > 0 else time_step
        dt = cmd_period

        # If time_step and cmd_period differ a lot, you could resample here.
        # For now we just step using the samples and sleep dt.
        print(
            f"[RUN] Starting maneuver with dt={dt:.4f}s, loops={self.max_loops}")

        # we will wait for limit switch before starting
        if USE_PIZERO_LIMIT_SWITCH:
            print("[RUN] Waiting for limit switch release before starting maneuver...")
            self.limit_switch.wait_for_release_once()
            print("[RUN] Limit switch released, starting maneuver now.")

        try:
            while self.loop_count < self.max_loops:
                print(f"[RUN] Loop {self.loop_count + 1}/{self.max_loops}")
                start_time = time.monotonic()
                next_send_ts = start_time

                for k in range(signal.shape[0]):
                    row = signal[k, :]

                    # Rate limiting
                    now = time.monotonic()
                    if now < next_send_ts:
                        time.sleep(next_send_ts - now)
                    next_send_ts += dt

                    # Send each servo channel
                    for i, radian_value in enumerate(row):
                        pwm_value = self.radian_to_pwm(radian_value)
                        servo_num = self.servo_start_index + i
                        # Pixracer typically SERVO1–8
                        if servo_num < 1 or servo_num > 8:
                            continue

                        try:
                            self.master.mav.command_long_send(
                                self.master.target_system,
                                self.master.target_component,
                                mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
                                0,                       # confirmation
                                # param1: servo number (1–8)
                                float(servo_num),
                                # param2: PWM in microseconds
                                float(pwm_value),
                                0, 0, 0, 0, 0           # param3–7 unused
                            )
                        except Exception as e:
                            print(f"[RUN] Failed to send servo command: {e}")

                self.loop_count += 1

                if not self.loop:
                    break

            print("[RUN] Maneuver complete.")
            self._post_maneuver_tmux_actions()

        except KeyboardInterrupt:
            print("[RUN] Interrupted by user.")

        finally:
            if self.master is not None:
                try:
                    self.master.close()
                except Exception:
                    pass
            print("[RUN] MAVLink connection closed.")

    # =========================================================
    # TMUX POST-PROCESSING (same idea as original)
    # =========================================================
    def _post_maneuver_tmux_actions(self):
        print(
            "[TMUX] Maneuver complete — attempting to stop rosbag and run next script via tmux.")

        session_name = self.tmux_session_name
        try:
            # Step 1: stop rosbag (Pane 2)
            print("[TMUX] Stopping rosbag recording in pane 0.2...")
            subprocess.run(
                f"tmux send-keys -t {session_name}:0.2 C-c", shell=True)
            # Step 2: wait a few seconds for rosbag to finalize
            time.sleep(10)

            if not self.parse:
                print("[TMUX] parse=False, not running Parcer.py.")
                return

            # Step 3: Split pane vertically (new one below pane 0.3)
            print("[TMUX] Creating vertical split under pane 0.3...")
            subprocess.run(
                f"tmux split-window -v -t {session_name}:0.3", shell=True)

            # Step 4: run Parcer.py in pane 0.4
            next_script = "../develop_ws/data/Output_Data/Parcer.py"
            print(f"[TMUX] Launching {next_script} in pane 0.4...")
            subprocess.run(
                f"tmux send-keys -t {session_name}:0.4 \"/usr/bin/python3 '{next_script}'\" C-m",
                shell=True,
            )
            print("[TMUX] Parcer.py launched successfully in bottom-right pane.")

        except Exception as e:
            print(f"[TMUX] Failed to trigger tmux commands: {e}")


def main():
    controller = MultisineMAVController()
    controller.run()


if __name__ == "__main__":
    main()
