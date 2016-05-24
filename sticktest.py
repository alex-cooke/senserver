from sense_hat import SenseHat
import time
import random
from stick import SenseStick

sense = SenseHat()
sense.set_rotation(270)

KEY_UP = 103
KEY_LEFT = 105
KEY_RIGHT = 106
KEY_DOWN = 108
KEY_ENTER = 28

stick = SenseStick()

try:
   while True:

      if stick.wait(timeout=0.01)==True:
         user_input = stick.read()[1]
         print(user_input)
         
#         if user_input==KEY_LEFT:
#            print "Left"
#         elif user_input==KEY_RIGHT:
#            print "Right"
#         elif user_input==KEY_UP:
#            print "Up"
#         elif user_input==KEY_DOWN:
#            print "Down"            
#         elif user_input==KEY_ENTER:
#            print "exiting"
#            sense.clear()
#            break

except KeyboardInterrupt:
   sense.clear()
   print
   print ("program stopped")
