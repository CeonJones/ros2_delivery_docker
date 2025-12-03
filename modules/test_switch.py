    #!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

LIMIT_PIN = 15  # BCM numbering

GPIO.setmode(GPIO.BCM)
GPIO.setup(LIMIT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_state = GPIO.input(LIMIT_PIN)

print("Watching limit switch... (CTRL+C to exit)")

try:
    while True:
        current = GPIO.input(LIMIT_PIN)

        # detect LOW -> HIGH transition
        if last_state == GPIO.LOW and current == GPIO.HIGH:
            print("Switch released! Parachute deployed!")

        last_state = current
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()
