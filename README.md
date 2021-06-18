# icantseebuticanfly
Prototypes to make drone piloting accessible to people with vision impairments

###Flying the drone
* startup the tello drone
* connect your laptop to its wifi network (tello-XXXX)
* connect the frsky remote via usb (HID/UsB device selected on the frsky)
* run piloting-tello.py
* use the takeoff and land button and the joystick to fly

speeds and axis can be adjusted in the value_updated method


### Audio Feedback
using the vvtvvtFlying app, it is possible to get audio 3D sound sources matching the drone and a "virtual target"
* start the audio app (vvtvvtFlyingAudio.app)
* start audio and add sound files (drag and drop) into source 1 (drone) and source 2 (target)
* in the flight arena connect to the pprzi router wifi network or the drone socket via ethernet
* be sure the motive app streams the drone and the hat on the network
* start vvtvvtFLying.py to retrieve the positions/orientations of the drone and hat, compute distances and send data to the audio server.
The sound sources should move in the spat.viewer GUI as well as the listener orientation.
You can adjust sound levels and or mute as required.

### Distance feedback
Using the crazy fly it is possible to test obstacle feedback in audio and tactile
* connect the radio dongle
* connect the arduino and bracelet
* run crazydistance.py
* check that head orientation is set to 0 (click on 0 0 0  message)
This will send data to the bracelet and audio engine to produce feedbacks (burst which frequency increase as distance decrease)

in the crazydistance.py file, R_MAX = 2 can be set to the maximum distance you want to detect in meters.

in the bracelet python file several parameters can be updated. 
* MIN_FREQ = 250 (when an object is close distance is 0)
* MAX_FREQ = 1000 (when an object is far distance is 1 (computed using RAX)
* BURST_DELAY = 100 (vibration burst duration)
)
