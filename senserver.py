from multiprocessing import Process, Manager, Value
import time
from sense_hat import SenseHat
from datetime import datetime 
import web
import sys
import json
from sqlite3 import connect, PARSE_DECLTYPES
from twitter import *

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
        'maximum': 40,
        'unit': '°'
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
        
        startTime = web.input().startTime
        endTime = web.input().endTime

        print(startTime)
        print(endTime)
        # open a connection to the databased
        connection = connect(database = DB_NAME)
        cursor = connection.cursor()

        print datetime.now()
        # query the database for readings
        cursor.execute('''SELECT * FROM `reading` where `time` >= ? ''',
                       (startTime,))

        return json.dumps(cursor.fetchall())

        for row in cursor.fetchall():
            print row[0], row[1], row[2], row[3], row[4]

        #   close the database cursor and connection
        cursor.close()
        connection.close()

        return "Range"

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

if __name__ == '__main__':

    currentReading = manager.list([])

    #   setup the database
    setupDatabase()

    #   start the logging service
    loggingServiceProcess = Process(target = loggingService, args = ())
    loggingServiceProcess.start()

    #   start the notifier service
    notificationServiceProcess = Process(target = notificationService, args = ())
    notificationServiceProcess.start()

    #   start the web server
 #   notificationServiceProcess.join()
#    loggingServiceProcess.join()
    webService()


    #   start the process which runs the web server
#    pRunWebServer = Process(target = runWebServer, args = ())
#    pRunWebServer.start()



    #pDisplayReadings = Process(target = displayReadings, args=([.15]))
    #pDisplayReadings.start()

    #pDisplayReadings2 = Process(target = displayReadings, args=([.125]))
    #pDisplayReadings2.start()

 #   while True:
 #       pass

 
