import socket

class Battery:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', 8423))

    def percentage(self):
        try:
            self.socket.send(b"get battery")
            resp = self.socket.recv(1024)
            percentage = float(resp.split()[1])

            return percentage
        except:
            return 100.0

    def is_charging(self):
        try:
            self.socket.send(b"get battery_power_plugged")
            resp = self.socket.recv(1024)
            plugged = resp[23] == 116
    
            self.socket.send(b"get battery_allow_charging")
            resp = self.socket.recv(1024)
            allow_charging = resp[24] == 116

            return plugged and allow_charging
        except:
            return False


if __name__ == "__main__":
    b = Battery()
    print(b.percentage())
    print(b.is_charging())
