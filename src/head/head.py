import pigpio
import time

class Head:
    def __init__(self, servo_pin=23):
        self.servo_pin = servo_pin
        self.current_angle = 90
        self.pi = pigpio.pi()

        if not self.pi.connected:
            raise RuntimeError("Failed to connect to pigpio daemon.")

        self.pi.set_servo_pulsewidth(self.servo_pin, 1500)

    def set_turn_angle(self, angle):
        """
        Set the angle to which the head should turn.
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
            case "up":
                angle = 180
            case "down":
                angle = 0
            case "straight":
                angle = 90
            case _:
                print("Expecting up, down, or straight for Head.look")

        self.set_turn_angle(angle)

    def nod(self):
        for angle in [60, 90]:
            self.set_turn_angle(angle)
            time.sleep(0.1)

    def cleanup(self):
        """
        Stops the servo and cleans up pigpio.
        """
        self.pi.set_servo_pulsewidth(self.servo_pin, 0)
        self.pi.stop()


if __name__ == "__main__":
    head = Head(servo_pin=23)

    try:
        while True:
            for angle in range(0, 181, 20):
                head.set_turn_angle(angle)
                print(f"Current angle: {head.current_angle}")
                time.sleep(1)

            for angle in range(180, -1, -20):
                head.set_turn_angle(angle)
                print(f"Current angle: {head.current_angle}")
                time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        head.cleanup()

