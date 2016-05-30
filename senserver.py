import web
import sys
import json
import time
import socket
import os
import re
from multiprocessing import Process, Manager, Value
from sense_hat import SenseHat
from datetime import datetime 
from sqlite3 import connect, PARSE_DECLTYPES
from twitter import *
from stick import SenseStick
from ctypes import c_char_p

####    CONSTANTS
DB_NAME = 'senserver.db'

####    GLOBAL OBJECTS
manager = Manager()
currentReading = []
settings = manager.dict({
    'readingSense': False   #   indicates whether the sense hat is busy
})
readingSense = Value('b',False)

#   notifier objects
notifierSettings = [
    {
        'sensor': 'humidity',
        'minimum': 20,
        'maximum': 50,
        'unit': '%'
    },
    {
        'sensor': 'temperature',
        'minimum': 0,
        'maximum': 50,
        'unit': '°'
    },
    {
        'sensor': 'pressure',
        'minimum': 0,
        'maximum': 2000,
        'unit': 'mb'
    }
]

#   Web application objects
render = web.template.render('templates/')

####    UTILITY FUNCTIONS
#   this serialises date objects in iso format
def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

##### HTTP ENDPOINTS

#   /   - returns the home page
class index:
    def GET(self):
        return render.index()

#   /sense/current - returns the most recent reading
class senseCurrent:
    def GET(self):
        return json.dumps(getCurrentReading(), default=date_handler)

#   /sense/current - returns the most recent reading
class senseRange:
    def GET(self):
        
        # get the querystring values
        startTime = web.input().startTime
        endTime = web.input().endTime

        # open a connection to the databased
        connection = connect(database = DB_NAME)
        cursor = connection.cursor()

        print datetime.now()
        # query the database for readings
        cursor.execute('''SELECT * FROM `reading` where `time` >= ? ''',
                       (startTime,))

        #   get a json dump of the readings
        returnValue = json.dumps(cursor.fetchall())

        #   close the database cursor and connection
        cursor.close()
        connection.close()

        #   return the data
        return returnValue

#   /notification/settings - returns the current notification settings
class notificationSettings:
    def GET(self):
        return json.dumps(notifierSettings)

####    SENSEHAT FUNCTIONS

#   returns the current reading and stores in the currentReading variable
def getCurrentReading():

    if (not readingSense.value):
        #   flag the sensehat as busy
        readingSense.value = True
        # get the new reading
        sense = SenseHat()
        orientation = sense.get_orientation()

        #   correct the pitch
        if (orientation['roll'] <= 90 or orientation['roll'] >= 270):
            orientation['pitch'] = 360 - orientation['pitch']
        else:
            orientation['pitch'] = orientation['pitch'] - 180
        
        #   generate the reading
        newReading = {
            'time' : datetime.now(),
            'temperature': round(sense.get_temperature(),1),
            'pressure': round(sense.get_pressure(),1),
            'humidity': round(sense.get_humidity(),1),
            'roll': round(orientation['roll'],1),
            'pitch': round(orientation['pitch'], 1),
            'yaw': round(orientation['yaw'],1)
        }

        #   remove all other readings from the currentReading list
        while (len(currentReading) > 0):
            currentReading.pop()
        
        #   save the current reading
        currentReading.append(newReading)
        #   flag the sensehat as not busy
        readingSense.value = False

    if (len(currentReading) > 0):
        return currentReading[0];
    else:
        return None

#   service that responds to HTTP requests
def webService():

    print('Starting Web Service')

    urls = (
        '/sense/current', 'senseCurrent',
        '/sense/range', 'senseRange',
        '/sense/test', 'senseTest',
        '/notification/settings', 'notificationSettings',
        '/shutdown', 'shutdown',
        '/', 'index'
    )

    app = web.application(urls, globals())

    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        app.stop()
        sys.exit()


#   ensures that the database structure is correct
def setupDatabase():

    # open a connection to the databased
    connection = connect(database = DB_NAME)
    cursor = connection.cursor()

    # create the reading table if it does not exist
    sql = 'CREATE TABLE if not exists `reading` (`time`	timestamp NOT NULL,`temperature`	NUMERIC,`pressure`	NUMERIC,`humidity`	NUMERIC,`roll`	NUMERIC,`pitch`	NUMERIC,`yaw`	NUMERIC, PRIMARY KEY(time));'
    cursor.execute(sql)
    connection.commit()

    #   close the database cursor and connection
    cursor.close()
    connection.close()
    
#   logs readings from the sense hat into the database on a regular basis      
def loggingService():

    print('Starting Logging Service')

    lastReadingTime = datetime.now()

    # open a connection to the database
    connection = connect(database = DB_NAME)
    cursor = connection.cursor()

    while True:

        #   wait a bit...
        time.sleep(1)                                            

        #   get the current readings
        currentReading = getCurrentReading()
        if (currentReading == None): continue
        
        #   strip out the milliseconds
        currentReadingTime = datetime(
            currentReading['time'].year,
            currentReading['time'].month,
            currentReading['time'].day,
            currentReading['time'].hour,
            currentReading['time'].minute,
            currentReading['time'].second)

        #   check that the reading time is greater than the last inserted time
        if (currentReadingTime <= lastReadingTime): continue
    
        #   insert the reading into the database
        cursor.execute('INSERT INTO `reading` (time, temperature,pressure, humidity, roll, pitch, yaw) values (?,?,?,?,?,?,?)',
                    (currentReadingTime,
                     currentReading['temperature'],
                     currentReading['pressure'],
                     currentReading['humidity'],
                     currentReading['roll'],
                     currentReading['pitch'],
                     currentReading['yaw']))
        try:
            connection.commit()             
        except:
            continue

        #   adjust the lastReadingTime
        lastReadingTime = currentReading['time']
                                    
    #   close the database cursor and connection
    cursor.close()
    connection.close()

#   service to check the readings and post notifications
def notificationService():
    
    print('Starting Notification Service')

    while True:
        time.sleep(2)

        #   get the current reading
        currentReading = getCurrentReading()
        if (currentReading == None): continue

        #   check against the notifierSettings to see if notification is required
        for reading in notifierSettings:
            readingName = reading['sensor']
            currentValue = currentReading[readingName]

            if (currentValue < reading['minimum']
                 or currentValue > reading['maximum']):

                message = (readingName + ' WARNING').upper() + '\n'
                message += 'Current: ' + str(currentValue) + ' ' + reading['unit'] +'\n'
                message += 'Acceptable: ' + str(reading['minimum']) + ' - ' + str(reading['maximum']) + reading['unit']

                notify(message)

#   function to post a notication
def notify(message):

    #   oauth constants to post to twitter
    access_token = '732479895855464449-gPfQbiOAb1Fd4juxM37fD4exhdwIMe8'
    access_token_secret = 'wGR7aVlmtHYT2K7QUXCjujwRwgk2dqWceSlIiw6NksbaB'
    consumer_key = 'X6VmWQqqLK9cjPxiuZkgqlaDu'
    consumer_secret = 'gevnV75tu3HT9VVXAY5g7WvMhyUMYHK4IrzJoEIC6ph1yruFoY'

    #   create a twitter object
    t = Twitter(auth=OAuth(access_token, access_token_secret, consumer_key, consumer_secret))

    #   post the status update to twitter
    t.statuses.update(status=message)
    print(message)

####    SENSE STICK AND DISPLAY FUNCTIONS

SCROLL_SPEED = 0.05

allDisplayModes = ['server', 'temperature', 'pressure', 'humidity']
currentDisplayMode = 'server'

#   this service listens for clicks on the joystick and cycles through the display modes
def senseStickService():
    print 'Starting SenseHat Stick Service'

    STICK_MIDDLE = 28
    stick = SenseStick()

    while True:
        if stick.wait(timeout=0.10) == True:

            #   Get the input from the joystick
            stick_input = stick.read()
            direction = stick_input[1]
            state = stick_input[2]  #   1 = pressed, 2 = held, 0 = released

            if (state == 0):    #   Only register if the joystick has been released
                if (direction == STICK_MIDDLE):
                    #   cycle the currentDisplayMode through the allDisplayModes array
                    currentDisplayMode.value = allDisplayModes[(allDisplayModes.index(currentDisplayMode.value) + 1) % len(allDisplayModes)]

#   show the server network details on the sensehat display
def senseDisplayServer(sense):
    name = socket.gethostname()
    ifconfig = os.popen('ifconfig').read()
    match = re.compile('^([^\s]+?)\s+?.+\n.\s+?[^\d].*?inet addr:((?:[0-9]{1,3}\.){3}[0-9]{1,3})', re.MULTILINE)
    interfaces = re.findall(match, ifconfig)
    sense.show_message(name, SCROLL_SPEED)
    for (interface, ipaddress) in interfaces:
        if (interface != 'lo'):
            sense.show_message(interface, SCROLL_SPEED)
            sense.show_message(ipaddress, SCROLL_SPEED)  

def senseDisplayTemperature(sense):
    sense.show_message("Temp (C) " + str(round(sense.get_temperature(),1)), SCROLL_SPEED)

def senseDisplayHumidity(sense):
    sense.show_message("Humidity (%) " + str(round(sense.get_humidity(),1)), SCROLL_SPEED)    

def senseDisplayPressure(sense):
    sense.show_message("Pressure (mBar) " + str(round(sense.get_pressure(),1)), SCROLL_SPEED)  

#   this service displays messages on the sensehat led screen according to the current mode
def senseDisplayService():
    print 'Starting SenseHat Display Service'

    #   create an object with display functions
    show = {
        'server': senseDisplayServer,
        'temperature': senseDisplayTemperature,
        'humidity': senseDisplayHumidity,
        'pressure': senseDisplayPressure
    }

    #   Initialise the sense hat
    sense = SenseHat()
    sense.clear(0,0,0)

    #   display a message according to the currentDisplayMode on a loop
    while True:
        show[currentDisplayMode.value](sense)

####    MAIN PROGRAM

if __name__ == '__main__':

    #   setup multiprocess variables
    currentDisplayMode = manager.Value(c_char_p, 'server')
    currentReading = manager.list([])

    #   setup the database
    setupDatabase()

    #   start the logging service
    loggingServiceProcess = Process(target = loggingService, args = ())
    loggingServiceProcess.start()

    #   start the notifier service
    notificationServiceProcess = Process(target = notificationService, args = ())
    notificationServiceProcess.start()

    #   start the the web service
    webServiceProcess = Process(target = webService, args = ())
    webServiceProcess.start()

    #   start the the senseStick service
    senseStickServiceProcess = Process(target = senseStickService, args = ())
    senseStickServiceProcess.start()

    #   start the the senseStick service
    senseDisplayServiceProcess = Process(target = senseDisplayService, args = ())
    senseDisplayServiceProcess.start()

    #   loop to do nothing whilst the processes run
    while True:
        try:
            pass
        except KeyboardInterrupt:
            print("OOPS")

 
