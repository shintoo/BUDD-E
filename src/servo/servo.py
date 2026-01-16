import pigpio
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor

class Servo:
    def __init__(self, servo_pin=23, tpe=None):
        self.servo_pin = servo_pin
        self.current_angle = 60
        self.pi = pigpio.pi()

        if not self.pi.connected:
            raise RuntimeError("Failed to connect to pigpio daemon.")

        self.pi.set_servo_pulsewidth(self.servo_pin, 1500)

        self.gazing = threading.Event()

        if tpe:
            self.threadpoolexecutor = tpe
        else:
            self.threadpoolexecutor = ThreadPoolExecutor(max_workers=2)

    def set_turn_angle(self, angle):
        """
        Set the angle to which the servo should turn.
        Angle should be between 0 and 180 degrees.
        """
        if 0 <= angle <= 180:
            self.current_angle = angle

            pulsewidth = 500 + (angle / 180) * 2000
            self.pi.set_servo_pulsewidth(self.servo_pin, pulsewidth)
            time.sleep(0.1)
        else:
            print("Angle must be between 0 and 180 degrees.")


    def look(self, direction: str):
        angle = 90
        match direction:
            case "left":
                angle = 180
            case "right":
                angle = 0
            case "straight":
                angle = 90
            case _:
                print("Expecting left, right, or straight for Servo.look")

        self.set_turn_angle(angle)

    def shake(self):
        for angle in [60, 90]:
            self.set_turn_angle(angle)
            time.sleep(0.1)

    def _submit(self, task):
        self.threadpoolexecutor.submit(task)

    def random_turn(self, bounds=(0, 180)):
        self.set_turn_angle(random.randint(bounds))

    def gaze_on(self):
        self.gazing.set()

        def _gaze_on():
            while self.gazing.is_set():
                self.set_turn_angle(random.randint(0, 180))
                time.sleep(random.randint(5, 10))

        self._submit(_gaze_on)

    def gaze_off(self):
        self.gazing.clear()

    def center(self):
        self.set_turn_angle(60)

    def cleanup(self):
        """
        Stops the servo and cleans up pigpio.
        """
        self.pi.set_servo_pulsewidth(self.servo_pin, 0)
        self.pi.stop()


if __name__ == "__main__":
    servo = Servo(servo_pin=23)

    try:
        while True:
            for angle in range(0, 181, 20):
                servo.set_turn_angle(angle)
                print(f"Current angle: {servo.current_angle}")
                time.sleep(1)

            for angle in range(180, -1, -20):
                servo.set_turn_angle(angle)
                print(f"Current angle: {servo.current_angle}")
                time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        servo.cleanup()

