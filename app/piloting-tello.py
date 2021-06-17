import sys

from PyQt5.QtWidgets import QApplication, QPushButton

from app.FrSky import find_available_frsky_ids, FrSky
from drone.tello import TelloDrone

if __name__ == "__main__":
    app = QApplication([])
    tello = TelloDrone()
    button = QPushButton("start")
    stp_button = QPushButton("stop")
    button.clicked.connect(tello.take_off)
    stp_button.clicked.connect(tello.land)
    button.show()
    stp_button.show()
    tello.batteryValue.connect(lambda status: print('batt', status))
    tello.is_flying_signal.connect(lambda status: print('flying?', status))
    tello.connection.connect(lambda status: print('connection', status))
    tello.init()


    def value_updated(x, y, x2, y2):
        tello.process_motion(y,x,y2,x2)

    stream = False
    refresh_duration_in_millis = 50
    joysticks = find_available_frsky_ids()
    print(joysticks)
    if (len(joysticks) > 0):
        gamepad = FrSky(stream, refresh_duration_in_millis, joysticks[0])
        gamepad.values.connect(value_updated)
        gamepad.start()
        app.aboutToQuit.connect(gamepad.stop)

    app.aboutToQuit.connect(tello.stop)
    sys.exit(app.exec_())
    tello.stop()