from multiprocessing import Process, Manager, Value
import time
from sense_hat import SenseHat
from datetime import datetime 
import web
import sys
import json
from sqlite3 import connect, PARSE_DECLTYPES

####    CONSTANTS
DB_NAME = 'senserver.db'

####    GLOBAL OBJECTS
manager = Manager()
currentReading = []
settings = manager.dict({
    'readingSense': False   #   indicates whether the sense hat is busy
})
readingSense = Value('b',False)

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
        #   flag the sensehat as not busy
        readingSense.value = False

    if (len(currentReading) > 0):
        return currentReading[0];
    else:
        return None
        

    #while True:
    ##    time.sleep(interval)
        
    #    # get the new reading
    #    orientation = sense.get_orientation()
    #    newReading = {
    #        'time' : datetime.now(),
    #        't': round(sense.get_temperature(),1),
    #        'p': round(sense.get_pressure(),1),
    #        'h': round(sense.get_humidity(),1),
    #        'x': round(orientation['roll'],1),
    #        'y': round(orientation['pitch'], 1),
    #        'z': round(orientation['yaw'],1)
    #    }

    #    #   remove all other readings from the currentReading list
    #    while (len(currentReading) > 0):
    #        currentReading.pop()
        
    #    #   save the current reading
    #    currentReading.append(newReading)

    #    print('getCurrentReading')

def displayReadings(interval):

    while True:
        time.sleep(interval)
        r = getCurrentReading()
        ##print('currentReading: ' + str(getCurrentReading()))


def runWebServer():

    print (readingSense.value)

    urls = (
        '/sense/current', 'senseCurrent',
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
def startDatabaseLogging():

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
                     currentReading['t'],
                     currentReading['p'],
                     currentReading['h'],
                     currentReading['x'],
                     currentReading['y'],
                     currentReading['z']))
        try:
            connection.commit()             
        except:
            continue

        #   adjust the lastReadingTime
        lastReadingTime = currentReading['time']
                                    
    #   close the database cursor and connection
    cursor.close()
    connection.close()


if __name__ == '__main__':

    #   setup the database
    setupDatabase()

    #   start the database logging
    startDatabaseLoggingProcess = Process(target = startDatabaseLogging, args = ())
    startDatabaseLoggingProcess.start()

#    manager = Manager()

    readingSense.value = False

 #   l = []

 #   currentReading = manager.dict()

 #   d['a'] = 4
  #  d['d'] = [1,2,3]
 #   readings = manager.list([])
    currentReading = manager.list([])

    #   start the process which gets the current reading
 #   pGetCurrentReading = Process(target=getCurrentReading, args=([currentReading]))
 #   pGetCurrentReading.start()

 #   runWebServer()

    #   start the process which runs the web server
#    pRunWebServer = Process(target = runWebServer, args = ())
#    pRunWebServer.start()



    #pDisplayReadings = Process(target = displayReadings, args=([.15]))
    #pDisplayReadings.start()

    #pDisplayReadings2 = Process(target = displayReadings, args=([.125]))
    #pDisplayReadings2.start()

 #   while True:
 #       pass

 
