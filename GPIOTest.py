#import the GPIO and time package
import RPi.GPIO as GPIO
import time
import Config


GPIO.setmode(GPIO.BCM)

TEST_INTERVAL_PAUSE = 10

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

    for i in range(1, TEST_INTERVAL_PAUSE):
        print(f"{i}/{TEST_INTERVAL_PAUSE} seconds")
        time.sleep(1)

    input(f"Did {i} work? (y/n): ")


GPIO.cleanup()