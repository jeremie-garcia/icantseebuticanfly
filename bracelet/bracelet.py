import math
from serial import Serial
from serial.tools.list_ports import comports

# baudrate for arduino
BAUDRATE = 115200


def find_available_arduinos():
    arduino_descriptions = ["arduino", "usb"]
    arduino_devices = ["usb", "tty", "arduino"]
    arduino_ports = [
        p.device
        for p in comports(False)
        if any(device in str(p.device).lower() for device in arduino_devices) or any(
            description in str(p.description).lower() for description in arduino_descriptions)
    ]
    return arduino_ports


OFF = 0
STARTING = 1
READY = 2


class Bracelet():
    # find available arduinos and if any start them

    def __init__(self, ):
        super().__init__()

        # arduino code
        self.arduino = None
        self.state = OFF
        self.init_arduino()

        # refresh rate
        self.rate = 50
        self.duration = 1000
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)

    def init_arduino(self):
        arduino_ports = find_available_arduinos()
        print(arduino_ports)
        if len(arduino_ports) > 0:
            self.arduino = Serial(port=arduino_ports[0], baudrate=BAUDRATE, timeout=0.2)
            self.state = STARTING

    def send_data_to_bracelet(self, message):
        print('sending this to the bracelet', message)
        if self.arduino != None:
            self.arduino.write(bytes(message, 'utf-8'))

    def send_values_to_bracelet(self, values):
        mess = f"<data {values[0]} {values[1]} {values[2]} {values[3]}>"
        self.send_data_to_bracelet(mess)

    def turn_off_all_motors(self):
        self.send_values_to_bracelet([0, 0, 0, 0])

    def turn_on_all_motors(self):
        self.send_values_to_bracelet([0.7, 0.7, 0.7, 0.7])

    def startup_pattern(self):
        self.turn_on_all_motors()
        QTimer.singleShot(250, self.turn_off_all_motors)
        QTimer.singleShot(750, self.turn_on_all_motors)
        QTimer.singleShot(1750, self.turn_off_all_motors)
        def set_state_to_ready():
            self.state = READY
        QTimer.singleShot(1750, set_state_to_ready)

    def update_animation(self):
        print('animation loop')
        if self.state == OFF:
            self.startup_pattern()
            self.state = STARTING
        elif self.state == READY:
            print('ready to send data')

    def start(self):
        self.animation_timer.start(self.rate)

    def stop(self):
        self.animation_timer.stop()

    def set_distance_to_target(self, values):
        print()

    def set_distance_to_obstacles(self, values):
        print()


if __name__ == "__main__":
    import sys
    import time
    from PyQt5.QtCore import QCoreApplication, QTimer

    app = QCoreApplication([])
    bracelet = Bracelet()
    bracelet.start()
    app.aboutToQuit.connect(bracelet.stop)
    sys.exit(app.exec_())