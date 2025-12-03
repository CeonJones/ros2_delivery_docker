#!/usr/bin/env python3

import time
import gpiod
import os
from gpiod.line import Direction, Bias, Edge

class LimitSwitch:
    """
    Modular GPIO limit switch interface for Pi Zero or Pi 5.

    Wiring Assumption:
      - COM → GND
      - NC → GPIO pin (default BCM 15 = physical pin 10)

    Logic:
      - Pressed  => LOW  => inactive
      - Released => HIGH => active/event
    """

    def __init__(self, line: int = 15, chip: str | None = None):
        self.line = line
        self.chip = chip
        self.request = None
        self.initialized = False

    def detect_gpiochip(self):
        """Auto-detect GPIO chip if not provided"""
        if self.chip:
            return self.chip

        # Pi Zero typically: /dev/gpiochip0
        # Pi 5 often: /dev/gpiochip4 (could change in newer kernels)
        possible_chips = [
            "/dev/gpiochip4",
            "/dev/gpiochip0",
            "/dev/gpiochip1",
        ]

        for dev in possible_chips:
            if os.path.exists(dev):
                return dev

        raise RuntimeError("No valid gpiochip device found")

    def setup(self):
        self.chip = self.detect_gpiochip()
        self.request = gpiod.request_lines(
            self.chip,
            consumer="limit-switch",
            config={
                self.line: gpiod.LineSettings(
                    direction=Direction.INPUT,
                    bias=Bias.PULL_UP,
                )
            },
        )
        self.initialized = True
        print(f"LimitSwitch initialized on {self.chip}, line {self.line}")

    def is_released(self) -> bool:
        if not self.initialized:
            raise RuntimeError("Call setup() before reading switch")
        # HIGH = released, LOW = pressed
        return bool(self.request.get_value(self.line))

    def wait_for_release_once(self, poll_delay: float = 0.01):
        """Block until the limit switch transitions to released."""
        if not self.initialized:
            raise RuntimeError("Call setup() before waiting")

        print("Waiting for release event...")
        last = self.is_released()

        while True:
            current = self.is_released()
            print(f"Switch state: {'RELEASED' if current else 'PRESSED'}")
            if not last and not current:  # LOW -> HIGH
                print("Switch released!")
                return True
            last = current
            time.sleep(poll_delay)

    def cleanup(self):
        if self.request:
            self.request.release()
            self.request = None
            self.initialized = False
            print("GPIO released and cleaned up.")

if __name__ == "__main__":
    switch = LimitSwitch(line=19)  # default GPIO15 OK
    switch.setup()

    # Block until release once
    switch.wait_for_release_once()

    print("Start servo commands now!")
    switch.cleanup()