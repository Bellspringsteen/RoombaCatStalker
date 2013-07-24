#!/usr/bin/env python

from RoombaSCI import RoombaAPI
import os
import re
import select
import sys
import termios
import time

RFCOMM_DEV="/dev/tty.usbserial-FTG661LW"
RFCOMM_BAUDRATE=115200

ANSI_RED='\033[31m'
ANSI_YELLOW='\033[33m'
ANSI_GREEN='\033[32m'
ANSI_BLINK='\033[1m'
ANSI_RST='\033[0m'
ANSI_CLEAR='\033[2J'

ROOMBA = "\
                OOOOOOO                \n\
            OOOOOOOOOOOOOOO            \n\
         OOOOO           OOOOO         \n\
       OOOOO               OOOOO       \n\
     OOOO     OOOOOOOOOOO      OOOO    \n\
   OOOO    OOOOO       OOOOO    OOOO   \n\
  OOOO   OOO               OOO   OOOO  \n\
 OOOO   OO       OOOOO       OO   OOOO \n\
 OOO   OO     OOOOOOOOOOO     OO   OOO \n\
OOO    OO    OOOOOOOOOOOOO    OO    OOO\n\
OOO         OOOOOOO_OOOOOOO         OOO\n\
OOO  I=I   OOOOOOO/ \OOOOOOO   I=I  OOO\n\
OOO  I=I   OOOOOO|   |OOOOOO   I=I  OOO\n\
OOO  I=I   OOOOOOO\_/OOOOOOO   I=I  OOO\n\
OOO  I=I    OOOOOOOOOOOOOOO    I=I  OOO\n\
OOO  I=I     OOOOOOOOOOOOO     I=I  OOO\n\
 OOO          OOOOOOOOOOO          OOO \n\
 OOOO            OOOOO            OOOO \n\
  OOOO                           OOOO  \n\
   OOOO                        OOOO    \n\
     OOOO                     OOOO     \n\
       OOOOO      OOO      OOOOO       \n\
         OOOOO   OOOOO    OOOOO        \n\
            OOOOOOOOOOOOOOO            \n\
                OOOOOOO                \n\
".split("\n")

TOP_LINES = range(0, 4)
SUBTOP_LINES = range(4, 10)
MIDDLE_LINES = range(10, 11)
WHEEL_LINES = range(11, 16)
WHEEL_ASCII = "I=I"
BOTTOM_LINES = range(16, 24)

class AsciiRoombaStaticLines:
    def __init__(self, lines_nb):
        self.piece = []
        for line_nb in lines_nb:
            self.piece.append("%20s%s" % ("", ROOMBA[line_nb]))

    def construct(self, sensors = None, ansi = False):
        pass

class AsciiRoombaWall:
    def __init__(self):
        self.piece = []

    def construct(self, sensors, ansi = False):
        self.piece = []
        if sensors.wall:
            self.piece.append("%20s=============     WALL     =============" % (""))
        if sensors.virtual_wall:
            self.piece.append("%20s------------- VIRTUAL WALL -------------" % (""))
        if len(self.piece) > 0:
            self.piece.append("")

class AsciiRoombaBasicPiece:
    def __init__(self):
        pass

    def construct_clean(self, lines_nb, left_side):
        self.piece = []
        for line_nb in lines_nb:
            line = ROOMBA[line_nb]
            sline = line.strip()
            middle = len(line)/2
            if left_side:
                line = line[:middle]
            else:
                line = line[middle:]
            self.piece.append(line)

    def add_text(self, left_side, text_lines):
        for i in range(0, len(self.piece)):
            if i < len(text_lines):
                text = text_lines[i]
            else:
                text = ""
            if left_side:
                if i == 0 and text != "":
                    text = "%s --> " % (text)
                else:
                    text = "%s     " % (text)
                self.piece[i] = "%20s%s" % (text, self.piece[i])
            else:
                if i == 0 and text != "":
                    text = " <-- %s" % (text)
                else:
                    text = "     %s" % (text)
                self.piece[i] = "%s%s" % (self.piece[i], text)

    def set_color(self, color, left, to_highlight = None):
        for i in range(0, len(self.piece)):
            if to_highlight == None:
                if left:
                    self.piece[i] = re.sub(r'^(\s*)(O+)', r'\1' + color + r'\2' + ANSI_RST, self.piece[i])
                else:
                    self.piece[i] = re.sub(r'(O+)(\s*)$', color + r'\1' + ANSI_RST + r'\2',
                                           self.piece[i])
            else:
                self.piece[i] = self.piece[i].replace(to_highlight,
                    "%s%s%s" % (color, to_highlight, ANSI_RST))


class AsciiRoombaTop(AsciiRoombaBasicPiece):
    def __init__(self, left_side):
        self.left_side = left_side

    def construct(self, sensors, ansi = False):
        AsciiRoombaBasicPiece.construct_clean(self, TOP_LINES, self.left_side)

        status = []
        ansi_color = ANSI_GREEN

        if self.left_side:
            cliff_status = sensors.cliff.front_left
        else:
            cliff_status = sensors.cliff.front_right
        if cliff_status:
            status.append("Cliff !")
            ansi_color = ANSI_YELLOW

        if self.left_side:
            bump_status = sensors.bumps.left
        else:
            bump_status = sensors.bumps.right
        if bump_status:
            ansi_color = ANSI_YELLOW

        if ansi:
            AsciiRoombaBasicPiece.set_color(self, ansi_color, self.left_side)
        if sensors.charging_state != 4: # -> charging
            status = []
        AsciiRoombaBasicPiece.add_text(self, self.left_side, status)

class AsciiRoombaSubTop(AsciiRoombaBasicPiece):
    def __init__(self, left_side):
        self.left_side = left_side

    def construct(self, sensors, ansi = False):
        AsciiRoombaBasicPiece.construct_clean(self, SUBTOP_LINES, self.left_side)

        status = []
        ansi_color = ANSI_GREEN

        if self.left_side:
            cliff_status = sensors.cliff.left
        else:
            cliff_status = sensors.cliff.right
        if cliff_status:
            status.append("Cliff !")
            ansi_color = ANSI_YELLOW

        if self.left_side:
            bump_status = sensors.bumps.left
        else:
            bump_status = sensors.bumps.right
        if bump_status:
            status.append("Bump !")
            ansi_color = ANSI_YELLOW

        if ansi:
            AsciiRoombaBasicPiece.set_color(self, ansi_color, self.left_side)
        if sensors.charging_state != 4: # -> charging
            status = []
        AsciiRoombaBasicPiece.add_text(self, self.left_side, status)


class AsciiRoombaWheel(AsciiRoombaBasicPiece):
    def __init__(self, left_side):
        self.left_side = left_side

    def construct(self, sensors, ansi = False):
        AsciiRoombaBasicPiece.construct_clean(self, WHEEL_LINES, self.left_side)

        status = []
        ansi_color = ""
        if self.left_side:
            cliff_status = sensors.wheel_drops.left
        else:
            cliff_status = sensors.wheel_drops.right
        if cliff_status:
            status.append("Wheel drop !")
            ansi_color = ANSI_RED + ANSI_BLINK

        if ansi:
            AsciiRoombaBasicPiece.set_color(self, ansi_color, self.left_side, WHEEL_ASCII)
        AsciiRoombaBasicPiece.add_text(self, self.left_side, status)

class AsciiRoombaBattery:
    def __init__(self):
        self.piece = []

    def construct(self, sensors, ansi = False):
        self.piece = [ "" ]

        ansi_color = ANSI_GREEN
        ansi_rst = ""
        if (sensors.charge < sensors.capacity / 2):
            ansi_color = ANSI_YELLOW
        if (sensors.charge < sensors.capacity / 4):
            ansi_color = ANSI_RED
        if ansi_color != "":
            ansi_rst = ANSI_RST
        if not ansi:
            ansi_color = ""
            ansi_rst = ""
        self.piece.append("Battery: %s%dmA%s / %dmA" % (ansi_color,
            sensors.charge, ansi_rst, sensors.capacity))

        ansi_color = ANSI_YELLOW
        txt = [
            "Charged",
            "Reconditioning charging",
            "Full charging",
            "Trickle Charging",
            "On battery",
            "Charging fault condition"
        ]
        ansi_rst = ""
        if sensors.charging_state == 0:
            ansi_color = ANSI_GREEN
        elif sensors.charging_state == 5:
            ansi_color = ANSI_RED
        if ansi_color != "":
            ansi_rst = ANSI_RST
        if not ansi:
            ansi_color = ""
            ansi_rst = ""
        self.piece[1] += (" (%s%s%s)" % (ansi_color, txt[sensors.charging_state], ansi_rst))

class AsciiRoomba:
    def __init__(self):
        self.pieces = [
            [ AsciiRoombaWall() ],
            [ AsciiRoombaTop(True), AsciiRoombaTop(False) ],
            [ AsciiRoombaSubTop(True), AsciiRoombaSubTop(False) ],
            [ AsciiRoombaStaticLines(MIDDLE_LINES) ],
            [ AsciiRoombaWheel(True), AsciiRoombaWheel(False) ],
            [ AsciiRoombaStaticLines(BOTTOM_LINES) ],
            [ AsciiRoombaBattery() ],
        ]

    def returnASCIIRoomba(self, sensors):
        ansi = "<pre>"

        for pieces_line in self.pieces:

            for piece in pieces_line:
                piece.construct(sensors, ansi)
                nb_lines = len(piece.piece)

            for nb_line in range(nb_lines):
                for piece in pieces_line:
                    ansi = ansi + piece.piece[nb_line]
                ansi = ansi + "\n"

        ansi = ansi + "\n </pre>"
        return ansi
        
    def display(self, sensors):
        ansi = sys.stdout.isatty()

        for pieces_line in self.pieces:

            for piece in pieces_line:
                piece.construct(sensors, ansi)
                nb_lines = len(piece.piece)

            for nb_line in range(nb_lines):
                for piece in pieces_line:
                    sys.stdout.write(piece.piece[nb_line])
                sys.stdout.write("\n")

        sys.stdout.write("\n")
        sys.stdout.flush()

def getchar():
	fd = sys.stdin.fileno()
	
	if os.isatty(fd):
		
		old = termios.tcgetattr(fd)
		new = termios.tcgetattr(fd)
		new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
		new[6] [termios.VMIN] = 1
		new[6] [termios.VTIME] = 0
		
		try:
			termios.tcsetattr(fd, termios.TCSANOW, new)
			termios.tcsendbreak(fd,0)
			ch = os.read(fd,7)

		finally:
			termios.tcsetattr(fd, termios.TCSAFLUSH, old)
	else:
		ch = os.read(fd,7)
	
	return(ch)

def control(roomba):
    print "Controls:"
    print "     ^8^"
    print "<4<   5    >6>"
    print "     v2v"
    print ""

    aRoomba = AsciiRoomba()

    roomba.full()
    while True:
        c = getchar()
        if c == "8":
            roomba.forward()
        elif c == "4":
            roomba.left()
        elif c == "6":
            roomba.right()
        elif c == "2":
            roomba.backward()
        elif c == "5":
            roomba.stop()
        elif c == "+":
            roomba.speed = roomba.speed + 50
        elif c == "-":
            roomba.speed = roomba.speed - 50

        sensors = roomba.sensors
        print ANSI_CLEAR
        aRoomba.display(sensors)
        print "Speed: %d/500" % roomba.speed


def usage():
    print "Syntax: %s [<options>] <order 1> [<order 2> [<order3> [...]]]" % sys.argv[0]
    print "Possible options are:"
    print "\t-v : verbose"
    print "Possible orders are:"
    print "\tclean : Start cleaning the room you lazy robot !"
    print "\tdock : Ok, forget it, you're making more crap than you're cleaning"
    print "\toff : OMG, stop breaking things ! right now !"
    print "\tstatus : Show me"
    print "\tmonitor : I think I will keep an eye on you"
    print "\tcontrol : Goddamnnit, let me do it ..."

if __name__ == "__main__":
    verbose = False

    if len(sys.argv) <= 1 or "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(2)
    
    orders = sys.argv[1:]
    if "-v" in orders:
        orders.remove("-v")
        verbose = True

    if verbose:
        sys.stdout.write("Connecting to the Rootooth ... ")
        sys.stdout.flush()
    roomba = RoombaAPI(RFCOMM_DEV, RFCOMM_BAUDRATE);
    if verbose:
        sys.stdout.write("OK\n")

    try:
        if verbose:
            sys.stdout.write("Rootooth version: ")
            sys.stdout.flush()
            sys.stdout.write(roomba.rootoothVersion + "\n")

        if verbose:
            sys.stdout.write("Connecting to the Roomba ... ")
            sys.stdout.flush()
        roomba.connect()
        if verbose:
            sys.stdout.write("OK\n")
            sys.stdout.flush()

        sensors = None
        if "sensors" in orders or \
           "status" in orders:
            if verbose:
                sys.stdout.write("Loading sensors informations ... ");
                sys.stdout.flush()
            sensors = roomba.sensors
            if verbose:
                sys.stdout.write("OK\n")

        if verbose:
            print "Sending orders:";
        for order in orders:
            if verbose:
                print "- %s" % order
            if order == "clean":
                roomba.clean()
            elif order == "dock":
                roomba.dock()
            elif order == "off":
                roomba.off()
            elif order == "sensors":
                assert(sensors != None)
                print "Battery Charge: %dmA / %dmA (%s)" % (sensors.charge,
                        sensors.capacity, str(sensors.charging_state))
                print "Cliffs:                %-7r | %-7r | %-7r | %-7r" % (
                    sensors.cliff.left,
                    sensors.cliff.front_left,
                    sensors.cliff.front_right,
                    sensors.cliff.right
                )
                print "Wheels drops:                    %-7r | %-7r" % (
                    sensors.wheel_drops.left,
                    sensors.wheel_drops.right
                )
                print "Bumps:                           %-7r | %-7r" % (
                    sensors.bumps.left,
                    sensors.bumps.right
                )
                print "Wall:                                %-7r" % (sensors.wall)
                print "Virtual wall:                        %-7r" % (sensors.virtual_wall)
                print "Battery temperature:              %d Celsius" % (sensors.temperature)
                print "Dirt detector:                   %-7d | %-7d" % (
                    sensors.dirt_detector.left,
                    sensors.dirt_detector.right)
            elif order == "status":
                assert(sensors != None)
                ascii_roomba = AsciiRoomba()
                ascii_roomba.display(sensors)
            elif order == "monitor":
                ascii_roomba = AsciiRoomba()
                while True:
                    sensors = roomba.sensors
                    print ANSI_CLEAR
                    ascii_roomba.display(sensors)
                    if not sys.stdout.isatty():
                        time.sleep(1)
                    else:
                        time.sleep(0.01)
            elif order == "control":
                control(roomba)
            else:
                usage()
                sys.exit(2)
            print ""
        if verbose:
            print "Done"
    finally:
        roomba.close()

    sys.exit(0)

