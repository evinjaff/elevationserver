#import the GPIO and time package
import RPi.GPIO as GPIO
import time
import Config


TEST_INTERVAL_PAUSE = 10


def testPin(GPIO_ID , duration=3, interactive=False):

    print(f"Setting pin {Config.GPIO_LOOKUP[GPIO_ID]} (purpose: {GPIO_ID}) as OUT")
    GPIO.setup(Config.GPIO_LOOKUP[GPIO_ID], GPIO.OUT)

    print(f"Testing Function of {GPIO_ID}")
    GPIO.output( Config.GPIO_LOOKUP[GPIO_ID] ,True)
    time.sleep(duration)
    GPIO.output( Config.GPIO_LOOKUP[GPIO_ID],False)
    time.sleep(duration)

    if interactive:
        input(f"Did {GPIO_ID} work? (y/n): ")



def testSuite(duration=3):

    GPIO.setmode(GPIO.BCM)

    for i in Config.GPIO_LOOKUP:
        print(f"Setting pin {Config.GPIO_LOOKUP[i]} (purpose: {i}) as OUT")
        GPIO.setup(Config.GPIO_LOOKUP[i], GPIO.OUT)
        print(i)
    
    for i in Config.GPIO_LOOKUP:
        testPin(i, duration=duration, interactive=True)

    GPIO.cleanup()




def main():
    print("type \"all\" to test all or type a number below to test a specific one: ")

    Select = {
        "preset1": 1,
        "preset2": 2,
        "preset3": 3,
        "preset4": 4,
        "up": 5,
        "down": 6,
    }

    print(Select)

    response = input("#")

    if "all" in response:
        testSuite()
        return
    
    for i in Select:

        GPIO.setmode(GPIO.BCM)
        if str(Select[i]) in response:
            testPin(i, duration=2, interactive=True)


if __name__ == "__main__":
    main()