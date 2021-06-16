import math
from PyQt5.QtCore import QTimer
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

MIN_FREQ = 100
MAX_FREQ = 500

BURST_DELAY = 50


class Bracelet():
    # find available arduinos and if any start them

    def __init__(self, ):
        super().__init__()

        # arduino code
        self.arduino = None
        self.state = OFF
        self.init_arduino()

        # refresh rate
        self.rate = 20
        self.duration = 1000
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.values_to_send = [0, 0, 0, 0]

        # bracelet timers for each motors
        self.timers = [QTimer(), QTimer() , QTimer(), QTimer()]

    def set_hight_value(self, index):
        self.values_to_send[index] = 0.7

    def set_low_value(self, index):
        self.values_to_send[index] = 0

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
        if self.state == OFF:
            self.startup_pattern()
            self.state = STARTING
        elif self.state == READY:
            self.send_values_to_bracelet(self.values_to_send)

    def start(self):
        self.animation_timer.start(self.rate)

    def stop(self):
        self.animation_timer.stop()

    def set_distance_to_target(self, values):
        print("distance")

    def trigger_burst_for_index(self, index):
        self.set_hight_value(index)
        QTimer.singleShot(BURST_DELAY, lambda: (self.set_low_value(index)))

    def set_distance_to_obstacles(self, values):
        print("obstacles")
        for index in range(len(values)):
            self.process_distance_to_frequency(index, values[index])

    def process_distance_to_frequency(self, index, value):
        timer = self.timers[index]
        if value == 0:
            self.set_low_value(index)
            timer.stop()
        else:
            interval = (1 - value) * (MAX_FREQ - MIN_FREQ) + MIN_FREQ
            if not timer.isActive():
                timer.start(interval)
                timer.timeout.connect(lambda: self.trigger_burst_for_index(index))
            else:
                self.timers[index].setInterval(interval)


if __name__ == "__main__":
    import sys
    import time
    from PyQt5.QtCore import QCoreApplication, QTimer

    app = QCoreApplication([])
    bracelet = Bracelet()
    bracelet.start()
    QTimer.singleShot(2000, lambda: (bracelet.set_distance_to_obstacles([1,1,1,1])))
    QTimer.singleShot(3000, lambda: (bracelet.set_distance_to_obstacles([0.5, 1, 1, 1])))
    QTimer.singleShot(3000, lambda: (bracelet.set_distance_to_obstacles([0.2, 1, 1, 1])))

    QTimer.singleShot(4000, lambda: (bracelet.set_distance_to_obstacles([1, 1, 1, 1])))
    QTimer.singleShot(5000, lambda: (bracelet.set_distance_to_obstacles([0.5, 0.5, 1, 1])))
    QTimer.singleShot(6000, lambda: (bracelet.set_distance_to_obstacles([1, 1, 0.3, 0.5])))

    app.aboutToQuit.connect(bracelet.stop)
    sys.exit(app.exec_())
