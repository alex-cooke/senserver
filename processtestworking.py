from time import sleep
import os
from ctypes import c_char_p
from multiprocessing import Process, Value, Manager
from sense_hat import SenseHat
import re
import socket
import sys

sense = SenseHat()

#   constants
SCROLL_SPEED = 0.05

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
    scrollMessage("Humidity: " + str(round(sense.get_humidity(),1)))    


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
    while mode.value != "quit":
        newMode = raw_input('Mode? ')
        mode.value = newMode
            
# Main Program

if __name__ == '__main__':

    manager = Manager()

    mode = manager.Value(c_char_p, 'server')

    print(mode.value)
    
    showValueProcess = Process(target = showValue, args=(mode,))
    showValueProcess.start()

    getValue(mode)
    showValueProcess.join()    


    
