from time import sleep
from sense_hat import SenseHat
sense = SenseHat()

while True:
    sense = SenseHat()
    orientation = sense.get_orientation()
    print(orientation)
