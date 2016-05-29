from time import sleep
import os
from ctypes import c_char_p
from multiprocessing import Process, Value, Manager
from sense_hat import SenseHat
import re
import socket
import sys
from stick import SenseStick

#   Initialise the sense hat
sense = SenseHat()
sense.clear(0,0,0)

#   Constants
SCROLL_SPEED = 0.05
STICK_UP = 103
STICK_LEFT = 105
STICK_RIGHT = 106
STICK_DOWN = 108
STICK_MIDDLE = 28

#   A list of modes that the user can cycle through
modes = ["server", "temp", "humidity", "pressure"]

#   Changes the mode the next mode in the sequence
def cycleMode(mode):
    print("old mode: " + mode.value)
    mode.value = modes[(modes.index(mode.value) + 1) % len(modes)]
    print("new mode: " + mode.value)

def scrollMessage(message):
    sense.show_message(message, SCROLL_SPEED)
    
def showServer():
    name = socket.gethostname()
    ifconfig = os.popen('ifconfig').read()
    match = re.compile('^([^\s]+?)\s+?.+\n.\s+?[^\d].*?inet addr:((?:[0-9]{1,3}\.){3}[0-9]{1,3})', re.MULTILINE)
    interfaces = re.findall(match, ifconfig)
    scrollMessage(name)
    for (interface, ipaddress) in interfaces:
        if (interface != 'lo'):
            scrollMessage(interface)
            scrollMessage(ipaddress)
            
def showTemperature():
    scrollMessage("Temperature: " + str(round(sense.get_temperature(),1)))

def showHumidity():
    scrollMessage("Humidity: " + str(round(sense.get_humidity(),1)) + '%')    

def showPressure():
    scrollMessage("Pressure: " + str(round(sense.get_pressure(),1)))    

def showValue(mode):
    show = {
        "server": showServer,
        "temp": showTemperature,
        "humidity": showHumidity,
        "pressure": showPressure
    }
    
    while mode.value != "quit":
        show[mode.value]()
      
def getValue(mode):
        
    stick = SenseStick()

    while (mode.value != "quit"):
        if stick.wait(timeout=0.01) == True:

            #   Get the input from the joystick
            stick_input = stick.read()
            direction = stick_input[1]
            state = stick_input[2]  #   1 = pressed, 2 = held, 0 = released

            if (state == 0):    #   Only register if the joystick has been released
                if (direction == STICK_MIDDLE):
                    cycleMode(mode);



# Main Program

if __name__ == '__main__':
        
    manager = Manager()

    mode = manager.Value(c_char_p, 'server')

    print(mode.value)
    
    showValueProcess = Process(target = showValue, args=(mode,))
    showValueProcess.start()

    getValue(mode)
    showValueProcess.join()    

    
