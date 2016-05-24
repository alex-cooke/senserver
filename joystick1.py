from sense_hat import SenseHat
import curses
import os
import time

sense = SenseHat()

sense.clear(0,0,0)

screen = curses.initscr()

screen.keypad(True)


def catchkeys(processName):
    print "Starting CatchKeys"
    while True:
        key = screen.getch()
        if (key > -1):
            print(processName + ":" + str(key))

def printstuff():
    while True:
        time.sleep(1)
        print("Process 2")



#pid = os.fork()
#if pid == 0:
    catchkeys("process1")
#else:
 #   printstuff()
