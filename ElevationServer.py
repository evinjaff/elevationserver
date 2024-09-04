from flask import Flask, request, jsonify
from Config import GPIO_LOOKUP
from GPIOTest import testPin, initializeGPIO
import time

app = Flask(__name__)

# global variable
current_level = 0

# Constants

# How long to fire the optocouplers to press a preset
MEMORY_BUTTON_PRESS_DURATION = 0.125
# The ratio of seconds / number of ticks moved
TICKS_PER_SECOND_CONSTANT = 1 / 7

# HTTP Code
# Quick Wakeup test to make sure the server is running
@app.route("/")
def hello_world():
    return "Elevation Server is running!"

@app.route("/setElevation", methods=["GET"])
def setElevation():
    percentage = request.args.get('percentage', type=int)
    
    if percentage is None:
        return jsonify({"error": "No percentage value provided"}), 400
    
    if percentage >= 0 and percentage <= 100:
        setNonElevation(percentage=percentage, previous_level=0)
    else:
        return jsonify({"error": "Invalid percentage value"}), 400

    return jsonify({}), 200



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
        raise ValueError(f"Invalid mode {mode}. Must be between 1 and 4.")
    
    # Fire the optocoupler

    modestring = "preset" + str(mode)

    if modestring in GPIO_LOOKUP:
        testPin(modestring, duration=MEMORY_BUTTON_PRESS_DURATION, interactive=False)
    else:
        raise LookupError(f"Couldn't find modestring: {modestring} in {GPIO_LOOKUP}")


def setNonElevation(percentage, previous_level=0):
    '''
    Fires the up and down signals to approximate a percentage but there will likely be some error
    
    Parameters:
    percentage (int): The percentage to raise the table to
    previous_level (int): The previous level to move to. If set to None, will set the table to 0 and raise

    Returns:
    The elevation level set
    '''
    presets = [0, 33, 66, 100]

    if percentage in presets:
        return elevationPreset( (percentage // 33) + 1 )

    # Define the preset values
    # Find the closest preset value
    closest_preset = min(presets, key=lambda x: abs(x - percentage))
    closest_preset = (closest_preset // 33) + 1

    print(f"Setting preset to {closest_preset}")
    elevationPreset(closest_preset)
    
    # Calculate the difference between the target and the closest preset
    difference = percentage - closest_preset
    # Use goUp or goDown to reach the target value
    duration = abs(difference) * TICKS_PER_SECOND_CONSTANT

    print(f"{difference} runs for {duration} seconds")

    if difference > 0:
        testPin("up", duration=duration, interactive=False)
    elif difference < 0:
        testPin("down", duration=duration, interactive=False)


    return percentage


# startup the server
if __name__ == '__main__':

    initializeGPIO()

    app.run(debug=True, port=8080, host='0.0.0.0')

