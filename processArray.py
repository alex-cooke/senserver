from multiprocessing import Process, Manager
import time
from sense_hat import SenseHat
from datetime import datetime 
import web
import sys
import json

currentReading = []

class senseCurrent:
    def GET(self):
        print(currentReading)

        return 'OK'

def getCurrentReading(currentReading):

    interval = 1

    while True:
        time.sleep(interval)
        sense = SenseHat()

        # get the new reading
        orientation = sense.get_orientation()
        newReading = {
            'time' : datetime.now(),
            't': round(sense.get_temperature(),1),
            'p': round(sense.get_pressure(),1),
            'h': round(sense.get_humidity(),1),
            'x': round(orientation['roll'],1),
            'y': round(orientation['pitch'], 1),
            'z': round(orientation['yaw'],1)
        }

        #   remove all other readings from the currentReading list
        while (len(currentReading) > 0):
            currentReading.pop()
        
        #   save the current reading
        currentReading.append(newReading)

        print('getCurrentReading')

def displayReadings(currentReading):

    while True:
        time.sleep(4)
        print('currentReading: ' + str(currentReading))


def runWebServer():

    urls = (
        '/sense/current', 'senseCurrent',
        '/shutdown', 'shutdown',
        '/', 'index'
    )
    app = web.application(urls, globals())


    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        app.stop()
        sys.exit()
        
if __name__ == '__main__':
    manager = Manager()

    l = []

    currentReading = manager.dict()

 #   d['a'] = 4
  #  d['d'] = [1,2,3]
    readings = manager.list([])
    currentReading = manager.list([])

    #   start the process which gets the current reading
    pGetCurrentReading = Process(target=getCurrentReading, args=([currentReading]))
    pGetCurrentReading.start()

    #   runWebServer(currentReading)

    #   start the process which runs the web server
    pRunWebServer = Process(target = runWebServer, args = ())
    pRunWebServer.start()



#    pDisplayReadings = Process(target = displayReadings, args=([currentReading]))
#    pDisplayReadings.start()

    while True:
        pass

    print d
    print l

