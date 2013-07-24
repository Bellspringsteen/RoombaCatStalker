from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import Http404
import logging
import json
import subprocess
from RoombaSCI import RoombaAPI
from roomba import AsciiRoomba
logger = logging.getLogger('app')


#RFCOMM_DEV="/dev/ttyUSB0"
RFCOMM_DEV="/dev/tty.usbserial-FTG661LW"
RFCOMM_BAUDRATE=115200
incrementer = 0
roomba = 0

@login_required
def index(request):
    return render_to_response('controlcenter/index.html', context_instance=RequestContext(request))

def takePicture():
    logger.debug("IN The take Picture function")
    process = subprocess.Popen(["/bin/bash", "/srv/roombaControl/takePicture.sh"],stdout=subprocess.PIPE)
    process.wait()
    return process.returncode

def controlAction(request):
    global incrementer, roomba
    incrementer += 1
    if request.method == "POST":
        if 'left' in request.POST:
            roomba.full()
            roomba.left()
            logger.debug("Move Left")
        elif 'right' in request.POST:
            roomba.full()
            roomba.right()
            logger.debug("Move Right")
        elif 'forward' in request.POST:
            roomba.full()
            roomba.forward()
            logger.debug("Move forward")
        elif 'backward' in request.POST:
            roomba.full()
            roomba.backward()
            logger.debug("Move backward")
        elif 'stop' in request.POST:
            roomba.full()
            roomba.stop()
            logger.debug("Move stop")
    elif request.method == "GET":
        if 'getSensors' in request.GET:
            logger.debug("Received Get Sensors Call")
            sensors = roomba.sensors
            jsonObject = {"bumps":{"left":sensors.bumps.left,"right":sensors.bumps.right},"cliff": {"front_left":sensors.cliff.front_left,"front_right":sensors.cliff.front_right,"left":sensors.cliff.left,"right":sensors.cliff.right}, "wheel_drops": {"castor":sensors.wheel_drops.castor,"left":sensors.wheel_drops.left,"right":sensors.wheel_drops.right},"voltage": sensors.voltage, "wall": sensors.wall}
            return HttpResponse(json.dumps(jsonObject), mimetype='application/json')
        elif 'connect' in request.GET:
            roomba = RoombaAPI(RFCOMM_DEV, RFCOMM_BAUDRATE);
            logger.debug("Started First Connect")
            roomba.connect()
            logger.debug("Received GetSensors Call")
            
            return HttpResponse(json.dumps(roomba.port.isOpen()), mimetype='application/json')
        elif 'takePicture' in request.GET:
            success = takePicture()
            return HttpResponse(json.dumps(success), mimetype='application/json')
        return Http404
    else:
        logger.debug("Not a Post or get Request")
    return render_to_response('controlcenter/index.html', context_instance=RequestContext(request))

