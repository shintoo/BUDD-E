from gpiozero import Motor, PWMOutputDevice
from time import sleep

class Wheels:
    def __init__(self, left_1, left_2, left_pwm, right_1, right_2, right_pwm):
        self.left_motor = Motor(forward=left_1, backward=left_2)
        self.left_speed = PWMOutputDevice(left_pwm)
        self.right_motor = Motor(forward=right_1, backward=right_2)
        self.right_speed = PWMOutputDevice(right_pwm)

    def left(self, speed=1.0):  
        self.left_speed.value = speed
        self.right_speed.value = speed
        self.left_motor.forward()
        self.right_motor.backward()

    def right(self, speed=1.0):
        self.left_speed.value = speed
        self.right_speed.value = speed
        self.left_motor.backward()
        self.right_motor.forward()

    def stop(self):
        self.left_speed.value = 0
        self.right_speed.value = 0
        self.left_motor.stop()
        self.right_motor.stop()

    def forward(self, speed=1.0):
        self.left_speed.value = speed
        self.right_speed.value = speed
        self.left_motor.forward()
        self.right_motor.forward()

    def backward(self, speed=1.0):
        self.left_speed.value = speed
        self.right_speed.value = speed
        self.left_motor.backward()
        self.right_motor.backward()   

    def curve_left(self, ratio=0.5, speed=1.0):
        self.right_speed.value = speed * ratio
        self.left_speed.value = speed

    def curve_right(self, ratio=0.5, speed=1.0):
        self.left_speed.value = speed * ratio
        self.right_speed.value = speed

if __name__ == "__main__":
    wheels = Wheels(4, 17, 13, 24, 16, 12)
    wheels.stop()
    cmd = ""

    while True:
        cmd = input("[f/b/l/r/s/q]> ")
        match cmd:
            case "f":
                wheels.forward()
                print("forward")
            case "b":
                print("backward")
                wheels.backward()
            case "l":
                print("left")
                wheels.left()
            case "r":
                print("right")
                wheels.right()
            case "s":
                print("stop")
                wheels.stop()
            case "q":
                print("quit")
                wheels.stop()
                break
