import math
from serial import Serial
from serial.tools.list_ports import comports

from NatNetClient import NatNetClient
from pythonosc.udp_client import SimpleUDPClient

# sound server info
SOUND_SERVER_IP = "127.0.0.1"
SOUND_SERVER_PORT = 6666

# baudrate for arduino
BAUDRATE = 115200

# update from motive app
PILOT_ID = 224
DRONE_ID = 223

# Change based on where the targets are in voliere
targets = [[-0.1620016098022461, -2.01731538772583, 0.3205585181713104],
           [-2.461967945098877, 1.3924974203109741, 0.3217718005180359],
           [2.544313430786133, 1.4535149335861206, 0.3303894102573395]]


def distance(x1, x2, y1, y2, z1, z2):
    distanceX = (x2 - x1) * (x2 - x1)
    distanceY = (y2 - y1) * (y2 - y1)
    distanceZ = (y2 - x1) * (y2 - x1)
    distance = math.sqrt(distanceX + distanceY + distanceZ)
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


def constantRightMotor(x1, x2, z1, z2):
    changeX = x2 - x1
    changeZ = z2 - z1

    # Right wrist
    TR = "<data 0.7 0.0 0.0 0.0 0.0 0.0>"
    TL = "<data 0.0 0.7 0.0 0.0 0.0 0.0>"
    BL = "<data 0.0 0.0 0.7 0.0 0.0 0.0>"
    BR = "<data 0.0 0.0 0.0 0.7 0.0 0.0>"

    # Right wrist only for now
    if changeX > 0 and changeZ > 0:
        return TR
    elif changeX < 0 and changeZ > 0:
        return TL
    elif changeX < 0 and changeZ < 0:
        return BL
    else:
        return BR


def constantLeftMotor(y1, y2):
    changeY = y2 - y1

    # Left wrist
    Top = "<data 0.0 0.0 0.0 0.0 0.7 0.0>"
    Bot = "<data 0.0 0.0 0.0 0.0 0.0 0.7"

    if changeY > 0:
        return Top
    else:
        return Bot


def changeMotor(distance, x1, x2, z1, z2):
    changeX = x2 - x1
    changeZ = z2 - z1

    if distance >= 0.5 and distance < 0.6:
        d = 0.75
    elif distance >= 0.6 and distance < 0.7:
        d = 0.8
    elif distance >= 0.7 and distance < 0.8:
        d = 0.85
    elif distance >= 0.8 and distance < 0.9:
        d = 0.9
    else:
        d = 1.0

    # Right wrist
    TR = "<data " + distance + "0.0 0.0 0.0 0.0 0.0>"
    TL = "<data 0.0 " + distance + " 0.0 0.0 0.0 0.0>"
    BL = "<data 0.0 0.0 " + distance + " 0.0 0.0 0.0>"
    BR = "<data 0.0 0.0 0.0 " + distance + " 0.0 0.0>"

    # Right wrist only for now
    if changeX > 0 and changeZ > 0:
        return TR
    elif changeX < 0 and changeZ > 0:
        return TL
    elif changeX < 0 and changeZ < 0:
        return BL
    else:
        return BR


def subtract_vectors(vec1, vec2):
    return [vec1[0] - vec2[0], vec1[1] - vec2[1], vec1[2] - vec2[2]]


def vector_to_text(vec):
    mess = ""
    print(vec)
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

        # start the server
        self.natnet.run()

    def init_arduino(self):
        arduino_ports = find_available_arduinos()
        if len(arduino_ports) > 0:
            self.arduino = Serial(port=arduino_ports[0], baudrate=BAUDRATE, timeout=0.2)

    def send_data_to_arduino(self, message):
        if self.arduino != None:
            self.arduino.write(bytes(message, 'utf-8'))

    def send_data_to_audio_server(self, address, message):
        self.client.send_message(address, message)

    def send_data_to_devices(self):
        # bracelet code
        # If app has changed position
        if self.drone_location != self.drone_prev_location:
            current = self.drone_location
            self.current_distance = distance(current[0], targets[2][0], current[1], targets[2][1], current[2],
                                             targets[2][2])

            initial = self.drone_prev_location
            # If the distance from the app to the target is further than where it previous was, change the vibration pattern
            if self.current_distance > self.prev_distance:
                pass
                # message = changeMotor(self.current_distance, initial[0], current[0], initial[2], current[2])
                # self.send_data_to_arduino(message)  # Otherwise, keep the vibration pattern consistent
            else:
                # message1 = constantRightMotor(initial[0], current[0], initial[2], current[2])
                # self.send_data_to_arduino(message1)
                message2 = constantLeftMotor(initial[1], current[1])

            # compute position of drone relative to pilot (pilot is at 0,0,0)
            relative_pos = subtract_vectors(self.drone_location, self.pilot_location)
            #print(relative_pos)
            #mess = vector_to_text(relative_pos)
            #print("mess",mess)
            self.send_data_to_audio_server("drone", relative_pos)

            # send pilot head orientation
            #mess = vector_to_text(self.pilot_orientation)
            self.send_data_to_audio_server("pilot", self.pilot_orientation)

            # feedback right left front back up down (0-1)
            #self.send_data_to_audio_server("feedback", mess)

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
        # Update the distance between the app and the target
        self.prev_distance = self.current_distance


if __name__ == "__main__":
    vvt = VvtvvtFlying(PILOT_ID, DRONE_ID)
