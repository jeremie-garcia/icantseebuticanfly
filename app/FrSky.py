import pygame
from PyQt5.QtCore import pyqtSignal, QObject, QTimer, pyqtSlot
from pygame import joystick

# init py-game and Joystick lib
pygame.init()
joystick.init()

def find_available_frsky_ids():
    pygame.init()
    if joystick.get_init():
        joystick.quit()

    joystick.init()

    for i in range(joystick.get_count()):
        print(joystick.Joystick(i).get_name().lower())


    frsky_ids = [
            i
            for i in range(joystick.get_count())
            if ("frsky") in joystick.Joystick(i).get_name().lower()
            ]
    return frsky_ids

class FrSky(QObject):
    values = pyqtSignal(float, float, float, float)
    connection = pyqtSignal(bool)
    buttons = pyqtSignal(int, int, str)

    def __init__(self, _stream=False, _update_in_millis=50, _id=0):
        super().__init__()
        self.update_in_millis = _update_in_millis
        self.stream = _stream
        self.running = False
        self.id = _id
        self.buttonTags = ["SA", "SB", "SC", "SD", "SE", "SF", "SG", "SH"]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process)

        # retrieve the connected and initialize
        print("Opening FRSKY on iD " + str(_id))
        self.stick = joystick.Joystick(self.id)
        self.stick.init()

        self.name = self.stick.get_name()
        self.axes = self.stick.get_numaxes()

        self.axesValues = [0] * self.axes
        self.prevAxesValues = [0] * self.axes

        self.buttons_count = self.stick.get_numbuttons()
        self.buttonsValues = [False] * self.buttons_count
        self.prevButtonsValues = [True] * self.buttons_count

    def emit_button_for_index(self, index):
        self.buttons.emit(index + 1, self.buttonsValues[index], "Button")

    def stop(self):
        self.timer.stop()
        self.connection.emit(False)

    def process(self):
        # necessary to update the event queue
        events = pygame.event.get()
        # retrieve data
        for i in range(self.axes):
            self.axesValues[i] = self.stick.get_axis(i)
        for i in range(self.buttons_count):
            self.buttonsValues[i] = self.stick.get_button(i)

        # fire events in streaming conditions
        if self.stream:
            self.values.emit(self.axesValues[0], self.axesValues[3], self.axesValues[2], self.axesValues[1])
            self.emit_button_for_index(0)
            self.emit_button_for_index(3)

        else:
            # fire events only if value changed
            if self.prevAxesValues[0] != self.axesValues[0] or self.prevAxesValues[3] != self.axesValues[3] or self.prevAxesValues[1] != self.axesValues[1] or self.prevAxesValues[2] != self.axesValues[2]:
                self.prevAxesValues[3] = self.axesValues[3]
                self.prevAxesValues[0] = self.axesValues[0]
                self.prevAxesValues[1] = self.axesValues[1]
                self.prevAxesValues[2] = self.axesValues[2]
                self.values.emit(self.axesValues[0], self.axesValues[3], self.axesValues[2], self.axesValues[1])

            for i in range(self.buttons_count):
                if self.prevButtonsValues[i] != self.buttonsValues[i]:
                    self.emit_button_for_index(i)
                    self.prevButtonsValues[i] = self.buttonsValues[i]

    def send_last_values(self):
        self.values.emit(self.axesValues[0], self.axesValues[3], self.axesValues[2], self.axesValues[1])

    def start(self):
        self.timer.start(self.update_in_millis)
        self.connection.emit(True)

@pyqtSlot(float, float, float, float)
def value_updated(x, y, x2, y2):
    '''slot to listen to the stick values, index, x, y'''
    print(x, y, x2, y2)


@pyqtSlot(int, int, str)
def button_updated(id, value, tag):
    '''slot to listen to the button values, index, state'''
    print(id, value, tag)

if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    stream = False
    refresh_duration_in_millis = 50
    joysticks = find_available_frsky_ids()
    print(joysticks)
    if (len(joysticks) > 0):
        gamepad = FrSky(stream, refresh_duration_in_millis, joysticks[0])
        gamepad.values.connect(value_updated)
        gamepad.buttons.connect(button_updated)
        gamepad.start()
        app.aboutToQuit.connect(gamepad.stop)
        sys.exit(app.exec_())