#import the GPIO and time package
import RPi.GPIO as GPIO
import time
import Config


GPIO.setmode(GPIO.BCM)


for i in Config.GPIO_LOOKUP:
    print(f"Setting pin {Config.GPIO_LOOKUP[i]} (purpose: {i}) as OUT")
    GPIO.setup(Config.GPIO_LOOKUP[i], GPIO.OUT)
    print(i)
 

for i in Config.GPIO_LOOKUP:
    print(f"Testing Function of {i}")
    GPIO.output( Config.GPIO_LOOKUP[i] ,True)
    time.sleep(3)
    GPIO.output( Config.GPIO_LOOKUP[i],False)
    time.sleep(3)


GPIO.cleanup()