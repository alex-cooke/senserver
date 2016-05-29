import web
import json
import sense_hat
import sys
from sense_hat import SenseHat
sense = SenseHat()

render = web.template.render('templates/')

urls = (
    '/sense/current', 'senseCurrent',
    '/shutdown', 'shutdown',
    '/', 'index'
)

app = web.application(urls, globals())

class index:
    def GET(self):
        return render.index()

class shutdown:
    def GET(self):
        print('Shutting Down')
        sys.exit(0)

class senseCurrent:
    def GET(self):

        sense = SenseHat()
        data = {
            "temperature": sense.get_temperature(),
            "humidity": sense.get_humidity(),
            "pressure": sense.get_pressure(),
            "orientation": sense.get_orientation()
        }
        
        return json.dumps(data)
    
if __name__ == '__main__':
    try:
        app.run()
    except (KeyboardInterrupt, SystemExit):
        app.stop()
        sys.exit()
