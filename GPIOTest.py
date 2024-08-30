#import the GPIO and time package
import RPi.GPIO as GPIO
import time
import Config


GPIO.setmode(GPIO.BCM)


for i in Config.GPIO_LOOKUP:
    print(f"Setting pin {Config.GPIO_LOOKUP[i]} (purpose: {i}) as OUT")
    GPIO.setup(Config.GPIO_LOOKUP[i], GPIO.OUT)
    print(i)
 
# loop through 50 times, on/off for 1 second

GPIO.output( Config.GPIO_LOOKUP["up"] ,True)
time.sleep(5)
GPIO.output( Config.GPIO_LOOKUP["up"],False)
time.sleep(5)

GPIO.output( Config.GPIO_LOOKUP["down"] ,True)
time.sleep(5)
GPIO.output( Config.GPIO_LOOKUP["down"],False)
time.sleep(5)

GPIO.output( Config.GPIO_LOOKUP["preset1"] ,True)
time.sleep(5)
GPIO.output( Config.GPIO_LOOKUP["preset1"],False)
time.sleep(5)



GPIO.cleanup()