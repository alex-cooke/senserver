import datetime
import time

time1 = datetime.now()

sleep(5)

time2 = datetime.now()

timeDiff = time2 - time1
print(str(timeDiff.seconds))
