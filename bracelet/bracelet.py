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

MIN_FREQ = 250
MAX_FREQ = 1000

BURST_DELAY = 100


class Bracelet():
    # find available arduinos and if any start them

    def __init__(self, ):
        super().__init__()

        # arduino code
        self.arduino = None
        self.state = OFF
        self.init_arduino()

        # refresh rate
        self.rate = 100
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.values_to_send = [0, 0, 0, 0]
        self.previous_values = [0,0,0,0]

        self.startup_pattern()
        # bracelet timers for each motors
        self.timers = [QTimer(), QTimer() , QTimer(), QTimer()]
        self.intervals = [1000,1000,1000,1000]


        #chaque timer se termine et se relance avec la fréquence définie

    def set_hight_value(self, index):
        self.values_to_send[index] = 0.7

    def set_low_value(self, index):
        self.values_to_send[index] = 0

    def init_arduino(self):
        arduino_ports = find_available_arduinos()
        print(arduino_ports)
        if len(arduino_ports) > 0:
            self.arduino = Serial(port=arduino_ports[0], baudrate=BAUDRATE, timeout=0.2)
            self.state = OFF

    def send_data_to_bracelet(self, message):
        #print('sending this to the bracelet', message)
        if self.arduino != None:
            self.arduino.write(bytes(message, 'utf-8'))

    def send_values_to_bracelet(self, values):
        print("sending val:", values)
        mess = f"<data {values[0]} {values[1]} {values[2]} {values[3]} 0 0>"
        self.send_data_to_bracelet(mess)

    def turn_off_all_motors(self):
        self.send_values_to_bracelet([0, 0, 0, 0])

    def turn_on_all_motors(self):
        self.send_values_to_bracelet([0.7, 0.7, 0.7, 0.7])

    def startup_pattern(self):
        print("BRACELET STARTUP")
        QTimer.singleShot(3000, self.turn_on_all_motors)
        QTimer.singleShot(4500, self.turn_off_all_motors)

        def set_state_to_ready():
            self.state = READY
            self.animation_timer.start(self.rate)
            print("BRACELET READY")

        QTimer.singleShot(5000, set_state_to_ready)

    def update_animation(self):
        if self.state == OFF:
            self.startup_pattern()
            self.state = STARTING
        elif self.state == READY:
            if self.values_to_send != self.previous_values:
                self.send_values_to_bracelet(self.values_to_send)
                self.previous_values = self.values_to_send.copy()

    def start(self):
        self.animation_timer.start(self.rate)

    def stop(self):
        self.send_values_to_bracelet([0,0,0,0])
        self.animation_timer.stop()

    def set_distance_to_target(self, values):
        print("distance")

    def trigger_burst_for_index(self, index):
        self.set_hight_value(index)
        QTimer.singleShot(BURST_DELAY, lambda: (self.set_low_value(index)))

    #values are right left up down distance from 0 (close) to 1(far)
    def set_distance_to_obstacles(self, values):
        for index in range(len(values)):
            self.process_distance_to_frequency(index, values[index])

    #1 is far away and 0 is close. update frequency when approaches 0
    def process_distance_to_frequency(self, index, value):
        timer = self.timers[index]
        interval = self.intervals[index]

        if value == 1:
            self.set_low_value(index)
            timer.stop()
        else:
            interval = value * (MAX_FREQ - MIN_FREQ) + MIN_FREQ
            self.intervals[index] = round(interval)
            if not timer.isActive():
                timer.start(interval)
                timer.timeout.connect(lambda: self.trigger_burst_for_index(index))
            else:
                timer.timeout.connect(lambda :  timer.setInterval(interval))



if __name__ == "__main__":
    import sys
    import time
    from PyQt5.QtCore import QCoreApplication, QTimer

    app = QCoreApplication([])
    bracelet = Bracelet()

    val = [0,0,0,0]
    QTimer.singleShot(5000, lambda: (bracelet.set_distance_to_obstacles([1,1,1,0.9])))
    QTimer.singleShot(5030, lambda: (bracelet.set_distance_to_obstacles([1, 1, 1, 0.8])))
    QTimer.singleShot(5060, lambda: (bracelet.set_distance_to_obstacles([1, 1, 1, 0.9])))
    QTimer.singleShot(5090, lambda: (bracelet.set_distance_to_obstacles([1, 1, 1, 0.8])))
    QTimer.singleShot(5150, lambda: (bracelet.set_distance_to_obstacles([1, 1, 1, 0.9])))

    QTimer.singleShot(8000, lambda: (bracelet.set_distance_to_obstacles([0.6,1, 1,1])))
    QTimer.singleShot(15000, lambda: (bracelet.set_distance_to_obstacles([1,1,0,1])))
    QTimer.singleShot(20000, lambda: (bracelet.set_distance_to_obstacles([1,1, 1,1])))


    app.aboutToQuit.connect(bracelet.stop)
    sys.exit(app.exec_())
