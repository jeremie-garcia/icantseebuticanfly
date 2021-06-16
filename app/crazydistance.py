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


if len(sys.argv) > 1:
    URI = sys.argv[1]

if __name__ == '__main__':
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
        cf = Crazyflie(rw_cache='./cache')

        with SyncCrazyflie(URI, cf=cf) as scf:
            with Multiranger(scf) as multiranger:

                while(True):

                    if multiranger.right is not None:
                        R_MAX = 1  # 2 meters
                        # right left front back up down
                        values = [normalize(multiranger.right, R_MAX),
                                  normalize(multiranger.left, R_MAX),
                                  normalize(multiranger.front, R_MAX),
                                  normalize(multiranger.back, R_MAX),
                                  normalize(multiranger.up, R_MAX),
                                  normalize(multiranger.down, R_MAX)]

                        client.send_message("feedback", values)
                        bracelet.set_distance_to_obstacles(values)

                    time.sleep(0.05)
