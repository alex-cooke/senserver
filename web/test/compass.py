from time import sleep
from sense_hat import SenseHat
sense = SenseHat()

while True:
    for i in range(10):
        compass = sense.get_compass()
    print(str(sense.get_compass()))
