#!/usr/bin/env python3
import logging
import sys
import time
import random

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils.multiranger import Multiranger

from pythonosc.udp_client import SimpleUDPClient

from bracelet.bracelet import Bracelet
from drone.crazydrone import CrazyDrone

#set the maximum distance to start detecting obstacles
R_MAX = 2  # 2 meters

if __name__ == '__main__':


    from PyQt5.QtCore import QCoreApplication, QTimer

    app = QCoreApplication([])


    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    available = cflib.crtp.scan_interfaces()

    # sound server info
    SOUND_SERVER_IP = "127.0.0.1"
    SOUND_SERVER_PORT = 6666

    # osc client to send data to audio server
    client = SimpleUDPClient(SOUND_SERVER_IP, SOUND_SERVER_PORT)

    #create a bracelet to send tactile feedback
    bracelet = Bracelet()

    def normalize(val, max_val):
        newval = val / max_val
        return 1 - min(max(newval, 0), 1)


    if len(available) > 0:
        URI = available[0][0]
        drone = CrazyDrone(URI)

        def update_range():
            multiranger = drone.multiranger

            if multiranger is not None and multiranger.right is not None:

                # right left front back up down
                values = [normalize(multiranger.right, R_MAX),
                          normalize(multiranger.left, R_MAX),
                          normalize(multiranger.front, R_MAX),
                          normalize(multiranger.back, R_MAX),
                          normalize(multiranger.up, R_MAX),
                          normalize(multiranger.down, R_MAX)]
                print(values)
                client.send_message("feedback", values)
                #vibration_values = [values[0], values[1], values[4], values[5]]
                vibration_values = [values[0], values[1], values[2], values[3]]
                bracelet.set_distance_to_obstacles(vibration_values)

    timer = QTimer()
    timer.timeout.connect(update_range)
    timer.start(100)

    app.aboutToQuit.connect(bracelet.stop)
    sys.exit(app.exec_())
