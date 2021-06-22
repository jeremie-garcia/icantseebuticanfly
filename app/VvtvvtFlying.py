import sys

import math
from PyQt5.QtWidgets import QApplication
from serial import Serial
from serial.tools.list_ports import comports

from NatNetClient import NatNetClient
from pythonosc.udp_client import SimpleUDPClient

# sound server info
from bracelet.bracelet import Bracelet

SOUND_SERVER_IP = "127.0.0.1"
SOUND_SERVER_PORT = 6666

# baudrate for arduino
BAUDRATE = 115200

# update from motive app
PILOT_ID = 224
DRONE_ID = 223

# Change based on where the targets are in voliere
target_location = [[-0.1620016098022461, -2.01731538772583, 0.3205585181713104],
                   [-2.461967945098877, 1.3924974203109741, 0.3217718005180359],
                   [2.544313430786133, 1.4535149335861206, 0.3303894102573395]]

TARGET_INDEX = 0


def distance_two_d(drone_loc, target_loc):
    distanceX = (drone_loc[0] - target_loc[0]) * (drone_loc[0] - target_loc[0])
    distanceY = (drone_loc[1] - target_loc[1]) * (drone_loc[1] - target_loc[1])
    distance = math.sqrt(distanceX + distanceY)
    return distance


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



def subtract_vectors(vec1, vec2):
    return [vec1[0] - vec2[0], vec1[1] - vec2[1], vec1[2] - vec2[2]]


def vector_to_text(vec):
    mess = ""
    for elem in vec:
        mess = mess + '{0:.3g}'.format(elem) + " "
    return mess


class VvtvvtFlying():
    # find available arduinos and if any start them

    def __init__(self, _pilot_id, _ac_id):
        super().__init__()

        # arduino code
        self.arduino = None
        self.init_arduino()

        # osc client to send data to audio server
        self.client = SimpleUDPClient(SOUND_SERVER_IP, SOUND_SERVER_PORT)

        # create NatNetClient to retrieve data from Motion Tracking
        self.natnet = NatNetClient(rigidBodyListListener=self.receive_rigid_body_list)

        # Drone's a,d pilot locations
        self.pilot_id = _pilot_id
        self.drone_id = _ac_id

        self.drone_location = [0, 0, 0]
        self.drone_prev_location = [0, 0, 0]
        self.pilot_location = [0, -5, 1.7]
        self.pilot_orientation = [0, 0, 0, 0]

        # distances
        self.current_distance = 0
        self.prev_distance = 0

        # create a bracelet
        self.bracelet = Bracelet()

        # start the server
        self.natnet.run()

    def stop(self):
        self.bracelet.stop()
        self.natnet.stop()

    def init_arduino(self):
        arduino_ports = find_available_arduinos()
        # print(arduino_ports)
        if len(arduino_ports) > 0:
            self.arduino = Serial(port=arduino_ports[0], baudrate=BAUDRATE, timeout=0.2)

    def send_data_to_arduino(self, message):
        if self.arduino != None:
            print(message)
            self.arduino.write(bytes(message, 'utf-8'))

    def send_data_to_audio_server(self, address, message):
        self.client.send_message(address, message)

    def send_data_to_devices(self):

        # send pilot head orientation
        self.send_data_to_audio_server("pilot", self.pilot_orientation)

        # compute position of drone relative to pilot
        relative_drone_pos = subtract_vectors(self.drone_location, self.pilot_location)
        self.send_data_to_audio_server("drone", relative_drone_pos)

        # compute position of target relative to pilot
        relative_target_pos = subtract_vectors(target_location[TARGET_INDEX], self.pilot_location)
        self.send_data_to_audio_server("target", relative_target_pos)

        # compute distance from drone to target (do not use elevation)
        distance = distance_two_d(self.drone_location, target_location[TARGET_INDEX])
        self.send_data_to_audio_server("distance", distance)
        #self.bracelet.set_distance_to_target(distance)

    def receive_rigid_body_list(self, rigidBodyList, stamp):
        for (ac_id, pos, quat, valid) in rigidBodyList:
            if valid:

                if ac_id == self.pilot_id:
                    self.pilot_location = pos
                    self.pilot_orientation = quat
                elif ac_id == self.drone_id:
                    self.drone_location = pos

        # update data to be sent to bracelet and audio
        self.send_data_to_devices()
        # Update the location of the app
        self.drone_prev_location = self.drone_location


if __name__ == "__main__":
    app = QApplication([])

    vvt = VvtvvtFlying(PILOT_ID, DRONE_ID)
    vvt.send_data_to_devices()

    app.aboutToQuit.connect(vvt.stop)
    sys.exit(app.exec_())