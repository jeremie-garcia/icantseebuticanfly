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
target_location = [[-0.1620016098022461, -2.01731538772583, 0.3205585181713104],
           [-2.461967945098877, 1.3924974203109741, 0.3217718005180359],
           [2.544313430786133, 1.4535149335861206, 0.3303894102573395]]

TARGET_INDEX = 2

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


def constant_feedback(drone_location_x1, drone_location_x2, drone_location_z1, drone_location_z2):
    changeX = drone_location_x2 - drone_location_x2
    changeZ = drone_location_z2 - drone_location_z1

    # Right wrist
    top_right_motor = "<data 0.7 0.0 0.0 0.0>"
    top_left_motor = "<data 0.0 0.7 0.0 0.0>"
    bottom_left_motor = "<data 0.0 0.0 0.7 0.0>"
    bottom_right_motor = "<data 0.0 0.0 0.0 0.7>"

    if changeX > 0 and changeZ > 0:
        return top_right_motor
    elif changeX < 0 and changeZ > 0:
        return top_left_motor
    elif changeX < 0 and changeZ < 0:
        return bottom_left_motor
    else:
        return bottom_right_motor


def corrective_feedback(distance_drone_to_target, drone_location_x1, drone_location_x2, drone_location_z1, drone_location_z2):
    changeX = drone_location_x2 - drone_location_x2
    changeZ = drone_location_z2 - drone_location_z1

    if distance_drone_to_target >= 0.5 and distance_drone_to_target < 0.6:
        d = 0.75
    elif distance_drone_to_target >= 0.6 and distance_drone_to_target < 0.7:
        d = 0.8
    elif distance_drone_to_target >= 0.7 and distance_drone_to_target < 0.8:
        d = 0.85
    elif distance_drone_to_target >= 0.8 and distance_drone_to_target < 0.9:
        d = 0.9
    else:
        d = 1.0

    d = max(0.0,min(d, 1.0))
    #print('d',d)
    # Right wrist
    top_right_motor = "<data " + '{0:.3g}'.format(d) + "0.0 0.0 0.0>"
    top_left_motor = "<data 0.0 " + '{0:.3g}'.format(d) + " 0.0 0.0>"
    bottom_left_motor = "<data 0.0 0.0 " + '{0:.3g}'.format(d) + " 0.0>"
    bottom_right_motor = "<data 0.0 0.0 0.0 " + '{0:.3g}'.format(d) + ">"

    if changeX > 0 and changeZ > 0:
        return top_right_motor
    elif changeX < 0 and changeZ > 0:
        return top_left_motor
    elif changeX < 0 and changeZ < 0:
        return bottom_left_motor
    else:
        return bottom_right_motor


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

        # start the server
        self.natnet.run()

    def init_arduino(self):
        arduino_ports = find_available_arduinos()
        #print(arduino_ports)
        if len(arduino_ports) > 0:
            self.arduino = Serial(port=arduino_ports[0], baudrate=BAUDRATE, timeout=0.2)

    def send_data_to_arduino(self, message):
        if self.arduino != None:
            print(message)
            self.arduino.write(bytes(message, 'utf-8'))

    def send_data_to_audio_server(self, address, message):
        print(message)
        self.client.send_message(address, message)

    def send_data_to_devices(self):
        # bracelet code
        # If app has changed position
        if self.drone_location != self.drone_prev_location:
            drone_current_location = self.drone_location
            self.current_distance = distance(drone_current_location[0], target_location[2][0], drone_current_location[1], target_location[2][1], drone_current_location[2],
                                             target_location[2][2])

            drone_previous_location = self.drone_prev_location
            #TODO update this part to make it working properly
            # If the distance from the app to the target is further than where it previous was, change the vibration pattern
            if self.current_distance > self.prev_distance:
                message = corrective_feedback(self.current_distance, drone_previous_location[0], drone_current_location[0], drone_previous_location[2], drone_current_location[2])
                #self.send_data_to_arduino(message)  # Otherwise, keep the vibration pattern consistent
            else:
                message = constant_feedback(drone_previous_location[0], drone_current_location[0], drone_previous_location[2], drone_current_location[2])
                #self.send_data_to_arduino(message)

        # compute position of drone relative to pilot
        relative_drone_pos = subtract_vectors(self.drone_location, self.pilot_location)
        self.send_data_to_audio_server("drone", relative_drone_pos)

        # compute position of target relative to pilot
        relative_target_pos = subtract_vectors(target_location[TARGET_INDEX], self.pilot_location)
        self.send_data_to_audio_server("target", relative_target_pos)

        # send pilot head orientation
        self.send_data_to_audio_server("pilot", self.pilot_orientation)



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
    vvt.send_data_to_devices()
