from flask import Flask
from Config import GPIO_LOOKUP
from GPIOTest import testPin
import time

app = Flask(__name__)


# HTTP Code
# Quick Wakeup test to make sure the server is running
@app.route("/")
def hello_world():
    return "Elevation Server is running!"

@app.route("/setElevation")
def setElevation():
    return "Set Elevation"




## Routines that manipulate GPIO for routing

# TODO: fill in the GPIO pins

def elevationPreset(mode, previous_level=0):
    '''
    Fires the optocoupler (range 1-4) which selects a preset elevation.

    Parameters:
    mode (int): The preset elevation to select. Range 1-4 where 1 is 0%, 2 is 33%, 3 is 66%, 4 is 100%

    Returns:
    The elevation level set
    '''

    if mode < 1 or mode > 4:
        return "Invalid mode. Must be between 1 and 4."
    
    # Fire the optocoupler

    modestring = "preset" + str(mode)

    if modestring in GPIO_LOOKUP:
        testPin(modestring, duration=0.25, interactive=False)



TICKS_PER_SECOND_CONSTANT = 1 / 15

def setNonElevation(percentage, previous_level=0):
    '''
    Fires the up and down signals to approximate a percentage but there will likely be some error
    
    Parameters:
    percentage (int): The percentage to raise the table to
    previous_level (int): The previous level to move to. If set to None, will set the table to 0 and raise

    Returns:
    The elevation level set
    '''

    if percentage in [0, 33, 66, 100]:
        return elevationPreset( (percentage // 33) + 1 )
    
    
    percentage_delta = percentage - previous_level if previous_level != None else percentage

    pi = pigpio.pi()
    # pull
    sleep_duration = abs(percentage_delta) * TICKS_PER_SECOND_CONSTANT

    if percentage_delta < 0:
        testPin("down", duration=sleep_duration, interactive=False)
    else:
        testPin("up", duration=sleep_duration, interactive=False)

        
    return percentage

        
