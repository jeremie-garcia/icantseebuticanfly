import sys

from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from app.FrSky import find_available_frsky_ids, FrSky
from drone.tello import TelloDrone

if __name__ == "__main__":
    app = QApplication([])
    tello = TelloDrone()

    win = QWidget()
    takeoff_btn = QPushButton("takeoff")
    land_button = QPushButton("land")
    takeoff_btn.clicked.connect(tello.take_off)
    land_button.clicked.connect(tello.land)
    layout = QVBoxLayout()
    layout.addWidget(takeoff_btn)
    layout.addWidget(land_button)
    win.setLayout(layout)

    #tello.batteryValue.connect(lambda status: print('batt', status))
    #tello.tempValue.connect(lambda status: print('temp', status))
    tello.is_flying_signal.connect(lambda status: print('flying?', status))
    tello.connection.connect(lambda status: print('connection', status))
    tello.init()

    def value_updated(x, y, x2, y2):
        #print("x",x,"y",y,"x2",x2,"y2",y2)
        #tello.process_motion(x2,0,y2,x)
        tello.process_motion(x2/2,0,0,x/2)

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
    win.show()
    sys.exit(app.exec_())
    tello.stop()