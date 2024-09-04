# elevationserver - Remotely Controlling a Standing Desk via Optocouplers on a Pi


![Raspberry Pi circuit](finalmount.png "Final mount and wiring ")

# Backgroud

I was tasked with trying to reverse engineer the serial port on a standing desk so that we could manipulate it remotely on a raspberry pi for automated testing of a system. I did some probing of the serial connection, and even got to finally use my [Raspberry Pi debug probe](https://www.raspberrypi.com/products/debug-probe/) to try and read UART signals. While I did fetch some bytes, a replay attack failed to get the table manipulated over serial. Because this table has easily usable buttons, I decided instead to wire up optocouplers to press the buttons with a raspberry pi.

# The Server

The actual server that drives the table up and down is pretty simple. It just uses Flask and has one endpoint that you supply the percentage up or down you want the table to be positioned in addition to a root endpoint that tells you if the server is running. 

The way it manipulates the table is that I've set the 4 presets to be at 0, 33, 66, and 100 percent of the full height. Based on the value of the number, the Pi clicks a preset and then moves the table up or down to get as close to the specific percentage as possible. 0, 33, 66, and 100 are guaranteed to be stable amounts since they're presets while the other ones are closer to guesswork.

The OpenAPI spec in YAML form is [here](openapi.yaml) with HTML client docs [here](openapi-docs.html).


# How To Build this

## Prep the display for soldering

This table has a display unit with buttons that is connected to a controller unit via an RJ45 jack. Disconnect the RJ45 plug from the display unit and then unscrew the display unit from the table using a Philips head screwdriver. Then, remove the board it from the plastic shell using a Phillips head screwdriver to remove the 4 screws in the rear of the unit. Then remove the tape holding the metal circles where the buttons are to expose the pads that are bridged to trigger the buttons. With the board ready, we can now solder.

### Soldering

Using a soldering iron, we solder two wires to each button. While you could easily strip one end of a Dupont wire to get a connection from the board, I find these wires very difficult to solder to pads because the wires are very thin (often 28 AWG). That's why I reccomend using thicker non-terminated wire with an AWG closer to 22 AWG. As always with unleaded solder, remember to be liberal with your flux and use a helping hands to help hold the board in place. Also, test your solder joints for [continuity with a multimeter](https://www.wikihow.com/Test-Continuity-with-a-Multimeter)- you don't want any globs of solder shorting out buttons.

Once you've confirmed it all works, I'd recommend throwing some Kapton tape over the joints to protect them from shorting.


### Terminating with a Dupont Connector

I'm embarrased to say that I spent probably 1-2 hours terminating these wires because it took me a while to figure out how to get them to slip through the black dupont sleeve. I'm not going to try and explain it here, I'll just point you to a [youtube video that might explain it better](https://www.youtube.com/watch?v=jET1QTP1B7c
). Since these go on a breadboard, I'd reccomend terminating with male ends. Plus, if you can't get the sleeve on the metal, you can still just stick the pin in the breadboard.


### Optocoupler circuit

Optocouplers are great pieces of techology. They comprise of an LED and a phototransistor. On the control side of the optocoupler (in our case the raspberry pi), the controller is connected to an LED that it can turn on and off. On the other side of the optocoupler chip, the phototransistor connects the two pins if the LED is on, thereby isolating the two circuits, preventing any need for nasty buck converters or diodes to manipulate the other system. 


When wiring up our optocouplers (in our case a SHARP PC817), this is what you want the circuit to theoretically look like:

![Optocoupler circuit](OptocouplerExample.png "Example circuit diagram indicating how to wire GPIO pins to a SHARP PC817 optocoupler")

We need a resistor to drop the voltage so we don't burn out the LED, and we want the Pi to be entirely hooked up to the right legs of the optocoupler (the "control side") while the left legs connect the leads of the buttons to each side of the optocoupler to close the switch.

The optocouplers from gikfun off Amazon seemed to have various levels of wear, and even an in-spec resistor sometimes failed to trigger the phototransistor, requiring me to wire my resistors in parallel to drop the resistance. If it's not working, double check the wiring and then play around with different resistances.


### Connecting to a Pi and configuring your GPIO pins

To test the GPIO pins, I'd reccomend using the testPin.py file. But that can be a little annoying so if you want something even simpler, use this little script. My script uses the Broadcom mappings, so use the "GPIO X" number from https://pinout.xyz/ to figure out which one works.


```py 

import RPi.GPIO as GPIO
import time
 
pin = 21         # The pin connected to the LED
interval = .25   # The length of time to blink on or off

# Setting to BCM will use Broadcom's GPIO numbers, while using Pi will set it to the pi's physical pin count
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(pin, GPIO.OUT)

# write to pin
GPIO.output(pin, GPIO.HIGH)
time.sleep(interval)
GPIO.output(pin, GPIO.LOW)

```

Then, you can fill in the correct pin mappings in `Config.py` that match how you wired it up:

```py
GPIO_LOOKUP = {
    "preset1": 17, # sets at 72
    "preset2": 6, # sets at 88
    "preset3": 13, # sets at 104
    "preset4": 5, # sets at 120
    "up": 26,
    "down": 27,
}
```


### Run the server


Since this is likely running on your own network, I'd reccomend adding a DHCP entry that points to the Raspberry Pi's IP. 

Bonus points for running the server as a systemd daemon too, that way you don't even need to SSH in when you reboot the pi. You can do this using the same tutorial from my [Oatmeal Computer Vision Server](https://github.com/evinjaff/oatmeal-cv-server?tab=readme-ov-file#run-it-as-a-systemd-service):


`elevationserver.service`
```toml
[Unit]
Description=Elevation Server
After=multi-user.target

[Service]
Type=idle
ExecStart=/path_to_this_repo/pi/venv/bin/python /path_to_this_repo/ElevationServer.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable the service by typing `systemctl enable elevationserver.service`

Start the service by typing `systemctl start elevationserver.service`

Check that it worked by typing `systemctl status elevationserver.service`


## Mounting

Once you're sure that this works, you can mount it all up. I remixed a common raspberry pi mounting plate to include a tray to hold the display unit in addition to the breadboard. Should print ok with no supports needed. Here's a render of the 3D model, it's a little tight to put in the breadboard, but it will fit snugly.


```stl
solid Mesh
  facet normal 0.000000 -1.000000 -0.000000
    outer loop
      vertex 82.998001 -84.000000 10.500000
      vertex 25.000000 -84.000000 0.000000
      vertex 82.998001 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.799351 0.331226 0.501326
    outer loop
      vertex -86.600998 -56.223999 5.500000
      vertex -86.042000 -56.061001 4.501000
      vertex -86.901001 -55.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex 25.000000 -84.000000 0.000000
      vertex 82.998001 -84.000000 10.500000
      vertex 25.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal -0.000000 -1.000000 0.000000
    outer loop
      vertex 23.000000 -84.000000 10.500000
      vertex -33.000000 -84.000000 10.500000
      vertex -33.000000 -84.000000 3.500000
    endloop
  endfacet
  facet normal -0.915685 -0.379948 0.130999
    outer loop
      vertex -49.895000 16.483000 3.241000
      vertex -49.865002 16.500000 3.500000
      vertex -49.965000 16.740999 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.609154 0.793052
    outer loop
      vertex -80.999001 18.292999 2.793000
      vertex -80.999001 18.500000 2.634000
      vertex -92.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 -56.034000 5.500000
      vertex -89.499001 -56.000000 5.500000
      vertex -89.499001 -54.000000 5.500000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 0.000000
    outer loop
      vertex -49.965000 16.740999 3.500000
      vertex -49.965000 16.740999 10.500000
      vertex -49.999001 17.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.377998 -54.879002 5.500000
      vertex -88.999001 -56.133999 5.500000
      vertex -88.792000 -56.292999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.377998 -54.879002 5.500000
      vertex -88.792000 -56.292999 5.500000
      vertex -88.633003 -56.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.999001 -56.133999 5.500000
      vertex -87.377998 -54.879002 5.500000
      vertex -87.999001 -54.402000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.633003 -56.500000 5.500000
      vertex -86.901001 -55.500000 5.500000
      vertex -87.377998 -54.879002 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -86.901001 -55.500000 5.500000
      vertex -88.633003 -56.500000 5.500000
      vertex -88.532997 -56.741001 5.500000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 -0.000000
    outer loop
      vertex -33.000000 -84.000000 3.500000
      vertex -34.057999 -84.000000 2.826000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -33.000000 -84.000000 3.500000
      vertex 23.000000 -84.000000 0.000000
      vertex 23.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal -0.982714 -0.132004 0.129801
    outer loop
      vertex -49.998001 16.732000 3.241000
      vertex -49.965000 16.740999 3.500000
      vertex -50.034000 17.000000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 -56.741001 5.500000
      vertex -88.499001 -57.000000 5.500000
      vertex -86.499001 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.916231 -0.379005 0.129912
    outer loop
      vertex -49.998001 16.732000 3.241000
      vertex -49.895000 16.483000 3.241000
      vertex -49.965000 16.740999 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -86.499001 -57.000000 5.500000
      vertex -86.600998 -56.223999 5.500000
      vertex -88.532997 -56.741001 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 -56.741001 5.500000
      vertex -86.600998 -56.223999 5.500000
      vertex -86.901001 -55.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -86.499001 -57.000000 5.500000
      vertex -88.499001 -57.000000 5.500000
      vertex -88.532997 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.156387 0.109770 0.981577
    outer loop
      vertex -36.060001 1.065000 3.951000
      vertex -36.222000 1.573000 3.920000
      vertex -36.249001 1.066000 3.981000
    endloop
  endfacet
  facet normal 0.383253 -0.923643 0.000000
    outer loop
      vertex -89.758003 -56.034000 5.500000
      vertex -89.999001 -56.133999 5.500000
      vertex -89.758003 -56.034000 0.000000
    endloop
  endfacet
  facet normal 0.734212 -0.302793 0.607659
    outer loop
      vertex -79.750000 16.665001 2.793000
      vertex -79.903999 16.707001 3.000000
      vertex -80.016998 16.433001 3.000000
    endloop
  endfacet
  facet normal 0.130158 -0.991493 -0.000000
    outer loop
      vertex -89.499001 -56.000000 5.500000
      vertex -89.758003 -56.034000 5.500000
      vertex -89.758003 -56.034000 0.000000
    endloop
  endfacet
  facet normal -0.982712 -0.129006 0.132798
    outer loop
      vertex -49.999001 17.000000 3.500000
      vertex -50.034000 17.000000 3.241000
      vertex -49.965000 16.740999 3.500000
    endloop
  endfacet
  facet normal 0.134678 0.103088 0.985512
    outer loop
      vertex -36.222000 1.573000 3.920000
      vertex -36.060001 1.065000 3.951000
      vertex -36.035999 1.569000 3.895000
    endloop
  endfacet
  facet normal -0.923635 -0.383273 -0.000000
    outer loop
      vertex -88.532997 -56.741001 5.500000
      vertex -88.633003 -56.500000 5.500000
      vertex -88.532997 -56.741001 0.000000
    endloop
  endfacet
  facet normal -0.991495 -0.130145 0.000000
    outer loop
      vertex -88.499001 -57.000000 5.500000
      vertex -88.532997 -56.741001 5.500000
      vertex -88.532997 -56.741001 0.000000
    endloop
  endfacet
  facet normal -0.854125 -0.353314 0.381629
    outer loop
      vertex -49.998001 16.732000 3.241000
      vertex -49.981998 16.433001 3.000000
      vertex -49.895000 16.483000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.923642 0.383256
    outer loop
      vertex -92.999001 18.134001 3.000000
      vertex -92.999001 18.034000 3.241000
      vertex -80.999001 18.034000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.793054 0.609151
    outer loop
      vertex -80.999001 18.292999 2.793000
      vertex -92.999001 18.134001 3.000000
      vertex -80.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal -0.982712 0.129006 0.132798
    outer loop
      vertex -49.999001 17.000000 3.500000
      vertex -49.965000 17.259001 3.500000
      vertex -50.034000 17.000000 3.241000
    endloop
  endfacet
  facet normal -0.923644 0.383250 0.000000
    outer loop
      vertex -49.965000 17.259001 3.500000
      vertex -49.965000 17.259001 10.500000
      vertex -49.865002 17.500000 10.500000
    endloop
  endfacet
  facet normal -0.917938 -0.123303 0.377075
    outer loop
      vertex -50.132999 17.000000 3.000000
      vertex -49.998001 16.732000 3.241000
      vertex -50.034000 17.000000 3.241000
    endloop
  endfacet
  facet normal -0.982714 0.132004 0.129801
    outer loop
      vertex -49.998001 17.268000 3.241000
      vertex -50.034000 17.000000 3.241000
      vertex -49.965000 17.259001 3.500000
    endloop
  endfacet
  facet normal -0.445202 0.575959 0.685613
    outer loop
      vertex -92.041000 3.524000 4.501000
      vertex -91.301003 4.096000 4.501000
      vertex -92.606003 4.086000 3.662000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 18.034000 3.241000
      vertex -92.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal -0.527055 0.686168 0.501385
    outer loop
      vertex -90.999001 3.598000 5.500000
      vertex -91.301003 4.096000 4.501000
      vertex -91.620003 3.121000 5.500000
    endloop
  endfacet
  facet normal -0.793050 -0.609157 0.000000
    outer loop
      vertex -94.413002 16.586000 3.500000
      vertex -94.413002 16.586000 10.500000
      vertex -94.731003 17.000000 10.500000
    endloop
  endfacet
  facet normal -0.529740 0.685325 0.499705
    outer loop
      vertex -91.620003 3.121000 5.500000
      vertex -91.301003 4.096000 4.501000
      vertex -92.041000 3.524000 4.501000
    endloop
  endfacet
  facet normal -0.916765 -0.118893 0.381322
    outer loop
      vertex -50.095001 16.707001 3.000000
      vertex -49.998001 16.732000 3.241000
      vertex -50.132999 17.000000 3.000000
    endloop
  endfacet
  facet normal -0.686033 0.526950 0.501680
    outer loop
      vertex -91.620003 3.121000 5.500000
      vertex -92.041000 3.524000 4.501000
      vertex -92.097000 2.500000 5.500000
    endloop
  endfacet
  facet normal -0.689143 0.524975 0.499482
    outer loop
      vertex -92.097000 2.500000 5.500000
      vertex -92.041000 3.524000 4.501000
      vertex -92.607002 2.781000 4.501000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 -0.000000
    outer loop
      vertex -34.057999 -84.000000 2.826000
      vertex -34.620998 -84.000000 2.597000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 -0.000000
    outer loop
      vertex -34.620998 -84.000000 2.597000
      vertex -34.931000 -84.000000 2.526000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 18.292999 2.793000
      vertex -92.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 18.134001 3.000000
      vertex -92.999001 18.292999 2.793000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 18.500000 2.634000
      vertex -92.999001 18.740999 2.534000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 18.740999 2.534000
      vertex -92.999001 19.000000 2.500000
    endloop
  endfacet
  facet normal 1.000000 -0.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 19.000000 2.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex 23.000000 -84.000000 0.000000
      vertex -34.931000 -84.000000 2.526000
      vertex -35.236000 -84.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.793054 0.609151
    outer loop
      vertex -80.999001 18.292999 2.793000
      vertex -92.999001 18.292999 2.793000
      vertex -92.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal -0.000000 -1.000000 0.000000
    outer loop
      vertex -35.236000 -84.000000 2.500000
      vertex -92.999001 -84.000000 2.500000
      vertex -92.999001 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 -0.000000
    outer loop
      vertex -35.236000 -84.000000 2.500000
      vertex -92.999001 -84.000000 0.000000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.609154 0.793052
    outer loop
      vertex -92.999001 18.292999 2.793000
      vertex -80.999001 18.292999 2.793000
      vertex -92.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.130157 0.991493
    outer loop
      vertex -92.999001 18.740999 2.534000
      vertex -80.999001 19.000000 2.500000
      vertex -92.999001 19.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.364998 1.500000 5.500000
      vertex -91.620003 3.121000 5.500000
      vertex -92.097000 2.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.097000 2.500000 5.500000
      vertex -90.464996 1.259000 5.500000
      vertex -90.364998 1.500000 5.500000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 0.000000
    outer loop
      vertex -94.413002 16.586000 3.500000
      vertex -93.999001 16.268000 3.500000
      vertex -94.413002 16.586000 10.500000
    endloop
  endfacet
  facet normal -0.604078 -0.786442 0.128839
    outer loop
      vertex -93.999001 16.268000 3.500000
      vertex -94.413002 16.586000 3.500000
      vertex -94.436996 16.562000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.999001 1.866000 5.500000
      vertex -90.999001 3.598000 5.500000
      vertex -91.620003 3.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -91.620003 3.121000 5.500000
      vertex -90.364998 1.500000 5.500000
      vertex -90.206001 1.707000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -91.620003 3.121000 5.500000
      vertex -90.206001 1.707000 5.500000
      vertex -89.999001 1.866000 5.500000
    endloop
  endfacet
  facet normal -0.793050 -0.609157 -0.000000
    outer loop
      vertex -94.731003 17.000000 10.500000
      vertex -94.731003 17.000000 3.500000
      vertex -94.413002 16.586000 3.500000
    endloop
  endfacet
  facet normal 0.538995 -0.057987 0.840311
    outer loop
      vertex -36.222000 0.433000 3.920000
      vertex -36.249001 1.066000 3.981000
      vertex -36.762001 0.674000 4.283000
    endloop
  endfacet
  facet normal -0.925506 0.107974 0.363017
    outer loop
      vertex -35.203999 -53.703999 3.400000
      vertex -35.018002 -52.261002 3.445000
      vertex -35.164001 -52.328999 3.093000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex 25.000000 85.000000 0.000000
      vertex 82.998001 85.000000 0.000000
      vertex -39.534000 1.259000 0.000000
    endloop
  endfacet
  facet normal -0.925814 0.045264 0.375258
    outer loop
      vertex -35.018002 -52.261002 3.445000
      vertex -35.034000 -50.896999 3.241000
      vertex -35.164001 -52.328999 3.093000
    endloop
  endfacet
  facet normal 0.155702 -0.088170 0.983861
    outer loop
      vertex -36.249001 1.066000 3.981000
      vertex -36.222000 0.433000 3.920000
      vertex -36.060001 1.065000 3.951000
    endloop
  endfacet
  facet normal -0.265775 -0.094184 0.959423
    outer loop
      vertex -36.035999 0.437000 3.896000
      vertex -35.455002 0.407000 4.054000
      vertex -36.060001 1.065000 3.951000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex 23.518000 84.931999 0.000000
      vertex 24.000000 84.732002 0.000000
      vertex -39.792000 1.707000 0.000000
    endloop
  endfacet
  facet normal 0.129271 -0.081610 0.988245
    outer loop
      vertex -36.060001 1.065000 3.951000
      vertex -36.222000 0.433000 3.920000
      vertex -36.035999 0.437000 3.896000
    endloop
  endfacet
  facet normal -0.785873 -0.604815 0.128850
    outer loop
      vertex -94.436996 16.562000 3.241000
      vertex -94.413002 16.586000 3.500000
      vertex -94.761002 16.983000 3.241000
    endloop
  endfacet
  facet normal -0.786246 -0.603931 0.130708
    outer loop
      vertex -94.413002 16.586000 3.500000
      vertex -94.731003 17.000000 3.500000
      vertex -94.761002 16.983000 3.241000
    endloop
  endfacet
  facet normal -0.923645 -0.383249 -0.000000
    outer loop
      vertex -94.931000 17.482000 10.500000
      vertex -94.931000 17.482000 3.500000
      vertex -94.731003 17.000000 3.500000
    endloop
  endfacet
  facet normal -0.923645 -0.383249 0.000000
    outer loop
      vertex -94.931000 17.482000 10.500000
      vertex -94.731003 17.000000 3.500000
      vertex -94.731003 17.000000 10.500000
    endloop
  endfacet
  facet normal -0.915995 -0.380075 0.128439
    outer loop
      vertex -94.963997 17.474001 3.241000
      vertex -94.731003 17.000000 3.500000
      vertex -94.931000 17.482000 3.500000
    endloop
  endfacet
  facet normal -0.916174 -0.378775 0.130978
    outer loop
      vertex -94.761002 16.983000 3.241000
      vertex -94.731003 17.000000 3.500000
      vertex -94.963997 17.474001 3.241000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -94.999001 18.000000 10.500000
      vertex -94.999001 18.000000 3.500000
      vertex -94.931000 17.482000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex 24.482000 84.931999 0.000000
      vertex 25.000000 85.000000 0.000000
      vertex -39.534000 1.259000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.792000 1.707000 0.000000
      vertex -40.000000 1.866000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.534000 1.259000 0.000000
      vertex 24.000000 84.732002 0.000000
      vertex 24.482000 84.931999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.000000 1.866000 0.000000
      vertex -40.241001 1.966000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.241001 1.966000 0.000000
      vertex -40.500000 2.000000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.916231 0.379005 0.129912
    outer loop
      vertex -49.895000 17.517000 3.241000
      vertex -49.998001 17.268000 3.241000
      vertex -49.965000 17.259001 3.500000
    endloop
  endfacet
  facet normal -0.854125 0.353314 0.381629
    outer loop
      vertex -49.981998 17.566999 3.000000
      vertex -49.998001 17.268000 3.241000
      vertex -49.895000 17.517000 3.241000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.000000 1.866000 0.000000
      vertex -86.015999 0.000000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -40.500000 2.000000 0.000000
      vertex -40.757999 1.966000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.633999 1.500000 0.000000
      vertex -39.792000 1.707000 0.000000
      vertex 24.000000 84.732002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.534000 1.259000 0.000000
      vertex -39.633999 1.500000 0.000000
      vertex 24.000000 84.732002 0.000000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -94.999001 18.000000 3.500000
      vertex -94.931000 17.482000 3.500000
      vertex -94.931000 17.482000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -40.000000 0.134000 0.000000
      vertex -39.792000 0.293000 0.000000
      vertex -40.959999 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex -40.241001 0.034000 0.000000
      vertex -40.000000 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.983177 -0.129067 0.129245
    outer loop
      vertex -94.963997 17.474001 3.241000
      vertex -94.931000 17.482000 3.500000
      vertex -94.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.500000 1.000000 0.000000
      vertex -39.534000 1.259000 0.000000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.353943 0.855118 0.378810
    outer loop
      vertex -49.566002 17.982000 3.000000
      vertex -49.266998 17.999001 3.241000
      vertex -49.292999 18.094999 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.534000 0.741000 0.000000
      vertex -39.500000 1.000000 0.000000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex -39.633999 0.500000 0.000000
      vertex -39.534000 0.741000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -40.757999 1.966000 0.000000
      vertex -41.000000 1.866000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.733417 -0.564445 0.378816
    outer loop
      vertex -94.847000 16.933001 3.000000
      vertex -94.436996 16.562000 3.241000
      vertex -94.761002 16.983000 3.241000
    endloop
  endfacet
  facet normal -0.303933 0.734294 0.606990
    outer loop
      vertex -49.646000 18.120001 2.793000
      vertex -49.566002 17.982000 3.000000
      vertex -49.292999 18.094999 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -41.207001 0.293000 0.000000
      vertex -41.000000 0.134000 0.000000
      vertex -40.959999 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -41.207001 0.293000 0.000000
      vertex -40.959999 -8.192000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -41.465000 0.741000 0.000000
      vertex -41.366001 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -41.500000 1.000000 0.000000
      vertex -41.465000 0.741000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.500000 1.000000 0.000000
      vertex -86.015999 0.000000 0.000000
      vertex -41.465000 1.259000 0.000000
    endloop
  endfacet
  facet normal -0.733386 -0.562477 0.381792
    outer loop
      vertex -94.847000 16.933001 3.000000
      vertex -94.508003 16.490999 3.000000
      vertex -94.436996 16.562000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -41.366001 1.500000 0.000000
      vertex -41.465000 1.259000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -41.000000 1.866000 0.000000
      vertex -41.207001 1.707000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal -0.631702 -0.485410 0.604425
    outer loop
      vertex -94.985001 16.854000 2.793000
      vertex -94.620003 16.379000 2.793000
      vertex -94.508003 16.490999 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -41.207001 1.707000 0.000000
      vertex -41.366001 1.500000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex 23.000000 85.000000 0.000000
      vertex 23.518000 84.931999 0.000000
      vertex -39.792000 1.707000 0.000000
    endloop
  endfacet
  facet normal -0.803651 -0.332255 0.493712
    outer loop
      vertex -94.999001 16.941999 2.826000
      vertex -94.761002 16.983000 3.241000
      vertex -94.963997 17.474001 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 83.000000 0.000000
      vertex -94.931000 83.517998 0.000000
      vertex -94.731003 84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.413002 84.414001 0.000000
      vertex -94.999001 83.000000 0.000000
      vertex -94.731003 84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -93.999001 84.732002 0.000000
      vertex -94.999001 83.000000 0.000000
      vertex -94.413002 84.414001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -93.516998 84.931999 0.000000
      vertex -94.999001 83.000000 0.000000
      vertex -93.999001 84.732002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 83.000000 0.000000
      vertex -93.516998 84.931999 0.000000
      vertex -92.999001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.631367 -0.484233 0.605718
    outer loop
      vertex -94.508003 16.490999 3.000000
      vertex -94.847000 16.933001 3.000000
      vertex -94.985001 16.854000 2.793000
    endloop
  endfacet
  facet normal 0.067402 0.088544 0.993789
    outer loop
      vertex -84.964996 -52.435001 2.634000
      vertex -84.654999 -51.167000 2.500000
      vertex -86.301003 -51.417999 2.634000
    endloop
  endfacet
  facet normal -0.423778 -0.844872 0.326503
    outer loop
      vertex -94.999001 16.941999 2.826000
      vertex -94.847000 16.933001 3.000000
      vertex -94.761002 16.983000 3.241000
    endloop
  endfacet
  facet normal -0.716387 -0.342019 0.608123
    outer loop
      vertex -94.985001 16.854000 2.793000
      vertex -94.847000 16.933001 3.000000
      vertex -94.999001 16.941999 2.826000
    endloop
  endfacet
  facet normal 0.062541 0.118898 0.990935
    outer loop
      vertex -84.654999 -51.167000 2.500000
      vertex -87.154999 -49.852001 2.500000
      vertex -86.301003 -51.417999 2.634000
    endloop
  endfacet
  facet normal -0.877893 -0.257284 0.403867
    outer loop
      vertex -94.999001 18.000000 3.500000
      vertex -94.999001 16.941999 2.826000
      vertex -94.963997 17.474001 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -92.999001 85.000000 0.000000
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 83.000000 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 83.000000 0.000000
      vertex -94.999001 18.000000 3.500000
      vertex -94.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal -0.794901 0.606739 0.000000
    outer loop
      vertex -39.792000 0.293000 0.000000
      vertex -39.633999 0.500000 5.500000
      vertex -39.633999 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.044947 0.109478 0.992972
    outer loop
      vertex -86.301003 -51.417999 2.634000
      vertex -87.154999 -49.852001 2.500000
      vertex -87.855003 -50.779999 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.239998 1.966000 0.000000
      vertex -94.999001 16.384001 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 85.000000 0.000000
      vertex -88.999001 1.866000 0.000000
      vertex -89.239998 1.966000 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 18.000000 3.500000
      vertex -94.999001 83.000000 0.000000
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal 0.016762 0.130498 0.991307
    outer loop
      vertex -87.855003 -50.779999 2.634000
      vertex -87.154999 -49.852001 2.500000
      vertex -89.521004 -50.566002 2.634000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -89.758003 1.966000 0.000000
      vertex -89.999001 1.866000 0.000000
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.239998 1.966000 0.000000
      vertex -89.499001 2.000000 0.000000
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -89.499001 2.000000 0.000000
      vertex -89.758003 1.966000 0.000000
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -39.500000 1.000000 5.500000
      vertex -39.534000 1.259000 0.000000
      vertex -39.500000 1.000000 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 16.941999 2.826000
      vertex -94.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal -0.991493 0.130159 -0.000000
    outer loop
      vertex -39.534000 0.741000 0.000000
      vertex -39.500000 1.000000 5.500000
      vertex -39.500000 1.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 85.000000 0.000000
      vertex -88.792000 1.707000 0.000000
      vertex -88.999001 1.866000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.633003 1.500000 0.000000
      vertex -88.792000 1.707000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.532997 1.259000 0.000000
      vertex -88.633003 1.500000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.383252 -0.923644 -0.000000
    outer loop
      vertex -40.000000 1.866000 5.500000
      vertex -40.241001 1.966000 0.000000
      vertex -40.000000 1.866000 0.000000
    endloop
  endfacet
  facet normal 0.130158 -0.991493 0.000000
    outer loop
      vertex -80.739998 16.034000 10.500000
      vertex -80.999001 16.000000 10.500000
      vertex -80.739998 16.034000 3.500000
    endloop
  endfacet
  facet normal -0.607308 -0.794466 -0.000000
    outer loop
      vertex -39.792000 1.707000 0.000000
      vertex -40.000000 1.866000 5.500000
      vertex -40.000000 1.866000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.999001 0.134000 0.000000
      vertex -88.792000 0.293000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -89.239998 0.034000 0.000000
      vertex -88.999001 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.923645 0.383249 0.000000
    outer loop
      vertex -39.633999 0.500000 0.000000
      vertex -39.633999 0.500000 5.500000
      vertex -39.534000 0.741000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -88.499001 1.000000 0.000000
      vertex -88.532997 1.259000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.532997 0.741000 0.000000
      vertex -88.499001 1.000000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.633003 0.500000 0.000000
      vertex -88.532997 0.741000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -92.999001 85.000000 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -90.364998 0.500000 0.000000
      vertex -90.206001 0.293000 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -90.464996 1.259000 0.000000
      vertex -90.499001 1.000000 0.000000
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -90.499001 1.000000 0.000000
      vertex -90.464996 0.741000 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -90.364998 1.500000 0.000000
      vertex -90.464996 1.259000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -89.999001 1.866000 0.000000
      vertex -90.206001 1.707000 0.000000
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -90.206001 1.707000 0.000000
      vertex -90.364998 1.500000 0.000000
    endloop
  endfacet
  facet normal 0.069904 0.546711 0.834398
    outer loop
      vertex -89.516998 -51.653999 3.028000
      vertex -89.514000 -52.622002 3.662000
      vertex -88.379997 -52.766998 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 25.000000 -84.000000 0.000000
      vertex 24.482000 -83.931999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 24.482000 -83.931999 0.000000
      vertex 24.000000 -83.732002 0.000000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.069922 0.546724 0.834388
    outer loop
      vertex -89.516998 -51.653999 3.028000
      vertex -88.379997 -52.766998 3.662000
      vertex -88.133003 -51.831001 3.028000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 -84.000000 0.000000
      vertex 25.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex 24.000000 -83.732002 0.000000
      vertex 23.518000 -83.931999 0.000000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex 23.518000 -83.931999 0.000000
      vertex 23.000000 -84.000000 0.000000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -39.633999 0.500000 0.000000
      vertex 82.998001 85.000000 0.000000
      vertex -40.959999 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex -40.757999 0.034000 0.000000
      vertex -40.500000 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex -40.500000 0.000000 0.000000
      vertex -40.241001 0.034000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex -39.792000 0.293000 0.000000
      vertex -39.633999 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.083482 -0.034586 0.995909
    outer loop
      vertex -79.258003 17.000000 2.534000
      vertex -79.767998 15.769000 2.534000
      vertex -79.067001 16.482000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -41.366001 0.500000 0.000000
      vertex -41.207001 0.293000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -41.000000 0.134000 0.000000
      vertex -40.757999 0.034000 0.000000
      vertex -40.959999 -8.192000 0.000000
    endloop
  endfacet
  facet normal -0.331475 0.799987 0.500145
    outer loop
      vertex -41.426998 4.460000 4.501000
      vertex -42.291000 4.102000 4.501000
      vertex -41.276001 3.898000 5.500000
    endloop
  endfacet
  facet normal 0.043713 0.340311 0.939296
    outer loop
      vertex -89.516998 -51.653999 3.028000
      vertex -87.855003 -50.779999 2.634000
      vertex -89.521004 -50.566002 2.634000
    endloop
  endfacet
  facet normal 0.130158 -0.991493 -0.000000
    outer loop
      vertex -80.739998 16.034000 3.500000
      vertex -80.999001 16.000000 10.500000
      vertex -80.999001 16.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 -84.000000 0.000000
      vertex -39.633999 -57.500000 0.000000
      vertex -39.534000 -57.258999 0.000000
    endloop
  endfacet
  facet normal -0.331484 0.799979 0.500152
    outer loop
      vertex -41.276001 3.898000 5.500000
      vertex -42.291000 4.102000 4.501000
      vertex -42.000000 3.598000 5.500000
    endloop
  endfacet
  facet normal 0.991491 0.130173 -0.000000
    outer loop
      vertex -90.499001 1.000000 0.000000
      vertex -90.499001 1.000000 5.500000
      vertex -90.464996 0.741000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.364998 0.500000 5.500000
      vertex -92.097000 -0.500000 5.500000
      vertex -91.620003 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.991491 -0.130173 0.000000
    outer loop
      vertex -90.499001 1.000000 5.500000
      vertex -90.499001 1.000000 0.000000
      vertex -90.464996 1.259000 5.500000
    endloop
  endfacet
  facet normal 0.129069 -0.983200 0.129070
    outer loop
      vertex -80.999001 15.966000 3.241000
      vertex -80.739998 16.034000 3.500000
      vertex -80.999001 16.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex -40.500000 -56.000000 0.000000
      vertex -40.757999 -56.034000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex -40.241001 -56.034000 0.000000
      vertex -40.500000 -56.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.464996 0.741000 5.500000
      vertex -92.097000 -0.500000 5.500000
      vertex -90.364998 0.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.000000 -56.133999 0.000000
      vertex -40.241001 -56.034000 0.000000
      vertex -40.959999 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.959999 -8.192000 0.000000
      vertex 82.998001 85.000000 0.000000
      vertex -40.000000 -56.133999 0.000000
    endloop
  endfacet
  facet normal -0.527396 0.686821 0.500130
    outer loop
      vertex -42.000000 3.598000 5.500000
      vertex -42.291000 4.102000 4.501000
      vertex -43.032001 3.533000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex -39.633999 -56.500000 0.000000
      vertex -39.792000 -56.292999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex -39.792000 -56.292999 0.000000
      vertex -40.000000 -56.133999 0.000000
    endloop
  endfacet
  facet normal 0.383259 -0.923641 0.000000
    outer loop
      vertex -80.739998 16.034000 3.500000
      vertex -80.499001 16.134001 10.500000
      vertex -80.739998 16.034000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex -39.534000 -56.741001 0.000000
      vertex -39.633999 -56.500000 0.000000
    endloop
  endfacet
  facet normal 0.793057 0.609147 0.000000
    outer loop
      vertex -90.364998 0.500000 5.500000
      vertex -90.206001 0.293000 5.500000
      vertex -90.206001 0.293000 0.000000
    endloop
  endfacet
  facet normal 0.923645 0.383249 -0.000000
    outer loop
      vertex -90.364998 0.500000 5.500000
      vertex -90.464996 0.741000 0.000000
      vertex -90.464996 0.741000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 -84.000000 0.000000
      vertex -92.999001 -84.000000 0.000000
      vertex -40.500000 -58.000000 0.000000
    endloop
  endfacet
  facet normal -0.527470 0.686704 0.500214
    outer loop
      vertex -42.000000 3.598000 5.500000
      vertex -43.032001 3.533000 4.501000
      vertex -42.620998 3.121000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.465000 -57.258999 0.000000
      vertex -43.928200 -57.344002 0.000000
      vertex -41.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.923645 -0.383249 0.000000
    outer loop
      vertex -90.364998 1.500000 5.500000
      vertex -90.464996 1.259000 5.500000
      vertex -90.364998 1.500000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -43.928200 -57.344002 0.000000
      vertex -41.465000 -56.741001 0.000000
      vertex -41.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.793057 -0.609147 -0.000000
    outer loop
      vertex -90.206001 1.707000 5.500000
      vertex -90.364998 1.500000 5.500000
      vertex -90.364998 1.500000 0.000000
    endloop
  endfacet
  facet normal 0.128884 -0.983200 0.129255
    outer loop
      vertex -80.999001 15.966000 3.241000
      vertex -80.732002 16.000999 3.241000
      vertex -80.739998 16.034000 3.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.465000 -56.741001 0.000000
      vertex -43.928200 -57.344002 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -41.366001 -56.500000 0.000000
      vertex -41.465000 -56.741001 0.000000
    endloop
  endfacet
  facet normal 0.383259 -0.923641 0.000000
    outer loop
      vertex -80.739998 16.034000 3.500000
      vertex -80.499001 16.134001 3.500000
      vertex -80.499001 16.134001 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -40.959999 -8.192000 0.000000
      vertex -40.757999 -56.034000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.207001 -56.292999 0.000000
      vertex -41.366001 -56.500000 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -40.757999 -56.034000 0.000000
      vertex -41.000000 -56.133999 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.000000 -56.133999 0.000000
      vertex -41.207001 -56.292999 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 -84.000000 0.000000
      vertex -39.534000 -57.258999 0.000000
      vertex -39.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.534000 -56.741001 0.000000
      vertex 82.998001 85.000000 0.000000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.303736 0.734620 0.606694
    outer loop
      vertex -49.646000 18.120001 2.793000
      vertex -49.292999 18.094999 3.000000
      vertex -49.334000 18.249001 2.793000
    endloop
  endfacet
  facet normal -0.857959 -0.112770 0.501187
    outer loop
      vertex -92.499001 1.000000 5.500000
      vertex -93.081001 0.988000 4.501000
      vertex -92.397003 0.224000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 -84.000000 0.000000
      vertex -39.500000 -57.000000 0.000000
      vertex -39.534000 -56.741001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -39.792000 -57.707001 0.000000
      vertex -39.633999 -57.500000 0.000000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.380084 -0.915990 0.128446
    outer loop
      vertex -80.732002 16.000999 3.241000
      vertex -80.499001 16.134001 3.500000
      vertex -80.739998 16.034000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.000000 -57.866001 0.000000
      vertex -39.792000 -57.707001 0.000000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.799350 -0.331226 0.501327
    outer loop
      vertex -92.956001 0.061000 4.501000
      vertex -92.097000 -0.500000 5.500000
      vertex -92.397003 0.224000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.241001 -57.966000 0.000000
      vertex -40.000000 -57.866001 0.000000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -40.500000 -58.000000 0.000000
      vertex -40.241001 -57.966000 0.000000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -92.999001 -84.000000 0.000000
      vertex -40.757999 -57.966000 0.000000
      vertex -40.500000 -58.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.499001 1.000000 5.500000
      vertex -92.397003 0.224000 5.500000
      vertex -90.464996 0.741000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.464996 1.259000 5.500000
      vertex -92.397003 1.776000 5.500000
      vertex -92.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.499001 1.000000 5.500000
      vertex -90.499001 1.000000 5.500000
      vertex -90.464996 1.259000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.464996 0.741000 5.500000
      vertex -90.499001 1.000000 5.500000
      vertex -92.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -40.757999 -57.966000 0.000000
      vertex -92.999001 -84.000000 0.000000
      vertex -41.000000 -57.866001 0.000000
    endloop
  endfacet
  facet normal 0.609150 -0.793055 0.000000
    outer loop
      vertex -80.292000 16.292999 10.500000
      vertex -80.499001 16.134001 10.500000
      vertex -80.499001 16.134001 3.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -41.000000 -57.866001 0.000000
      vertex -92.999001 -84.000000 0.000000
      vertex -41.207001 -57.707001 0.000000
    endloop
  endfacet
  facet normal -0.234334 0.566763 0.789853
    outer loop
      vertex -49.749001 18.299000 2.634000
      vertex -49.646000 18.120001 2.793000
      vertex -49.334000 18.249001 2.793000
    endloop
  endfacet
  facet normal -0.234316 0.306188 0.922683
    outer loop
      vertex -50.049999 18.370001 2.534000
      vertex -50.060001 18.061001 2.634000
      vertex -49.749001 18.299000 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -43.928200 -57.344002 0.000000
      vertex -41.207001 -57.707001 0.000000
      vertex -92.999001 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -43.928200 -57.344002 0.000000
      vertex -41.465000 -57.258999 0.000000
      vertex -41.366001 -57.500000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -43.928200 -57.344002 0.000000
      vertex -41.366001 -57.500000 0.000000
      vertex -41.207001 -57.707001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex 23.000000 85.000000 0.000000
      vertex -86.015999 0.000000 0.000000
      vertex -88.532997 1.259000 0.000000
    endloop
  endfacet
  facet normal 0.609150 -0.793055 0.000000
    outer loop
      vertex -80.499001 16.134001 3.500000
      vertex -80.292000 16.292999 3.500000
      vertex -80.292000 16.292999 10.500000
    endloop
  endfacet
  facet normal -0.588310 0.197456 0.784157
    outer loop
      vertex -35.604000 -52.397999 2.730000
      vertex -35.307999 -53.740002 3.290000
      vertex -35.248001 -52.349998 2.985000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -89.758003 0.034000 0.000000
      vertex -89.499001 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -90.206001 0.293000 0.000000
      vertex -89.999001 0.134000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -89.499001 0.000000 0.000000
      vertex -89.239998 0.034000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -94.999001 -8.192000 0.000000
      vertex -88.999001 0.134000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -88.792000 0.293000 0.000000
      vertex -88.633003 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.605501 -0.785338 0.128886
    outer loop
      vertex -80.267998 16.268999 3.241000
      vertex -80.292000 16.292999 3.500000
      vertex -80.482002 16.104000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -94.999001 16.384001 0.000000
      vertex -90.499001 1.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -89.999001 0.134000 0.000000
      vertex -89.758003 0.034000 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -90.464996 0.741000 0.000000
      vertex -90.364998 0.500000 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal -0.631603 0.486467 0.603678
    outer loop
      vertex -50.118999 17.646000 2.793000
      vertex -49.981998 17.566999 3.000000
      vertex -49.800999 17.802000 3.000000
    endloop
  endfacet
  facet normal -0.799383 0.331239 0.501266
    outer loop
      vertex -92.607002 2.781000 4.501000
      vertex -92.397003 1.776000 5.500000
      vertex -92.097000 2.500000 5.500000
    endloop
  endfacet
  facet normal 0.603924 -0.786251 0.130709
    outer loop
      vertex -80.482002 16.104000 3.241000
      vertex -80.292000 16.292999 3.500000
      vertex -80.499001 16.134001 3.500000
    endloop
  endfacet
  facet normal -0.722049 0.092960 0.685568
    outer loop
      vertex -93.081001 0.988000 4.501000
      vertex -93.732002 2.119000 3.662000
      vertex -93.877998 0.985000 3.662000
    endloop
  endfacet
  facet normal 0.564319 -0.731925 0.381877
    outer loop
      vertex -80.196999 16.198000 3.000000
      vertex -80.267998 16.268999 3.241000
      vertex -80.482002 16.104000 3.241000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -86.015999 0.000000 0.000000
      vertex -43.928200 -57.344002 0.000000
      vertex -88.792000 -56.292999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -43.928200 -57.344002 0.000000
      vertex -92.999001 -84.000000 0.000000
      vertex -88.792000 -57.707001 0.000000
    endloop
  endfacet
  facet normal -0.801502 0.328936 0.499395
    outer loop
      vertex -92.397003 1.776000 5.500000
      vertex -92.607002 2.781000 4.501000
      vertex -92.961998 1.916000 4.501000
    endloop
  endfacet
  facet normal -0.000000 0.000000 -1.000000
    outer loop
      vertex -89.758003 -56.034000 0.000000
      vertex -89.999001 -56.133999 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal -0.631664 0.483172 0.606255
    outer loop
      vertex -50.118999 17.646000 2.793000
      vertex -49.800999 17.802000 3.000000
      vertex -49.914001 17.914000 2.793000
    endloop
  endfacet
  facet normal -0.858026 0.112779 0.501070
    outer loop
      vertex -92.397003 1.776000 5.500000
      vertex -92.961998 1.916000 4.501000
      vertex -92.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -89.499001 -56.000000 0.000000
      vertex -89.758003 -56.034000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.999001 -56.133999 0.000000
      vertex -89.239998 -56.034000 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal 0.377657 -0.916637 0.130962
    outer loop
      vertex -80.732002 16.000999 3.241000
      vertex -80.482002 16.104000 3.241000
      vertex -80.499001 16.134001 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -86.015999 0.000000 0.000000
      vertex -88.999001 -56.133999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.792000 -56.292999 0.000000
      vertex -88.999001 -56.133999 0.000000
      vertex -86.015999 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -43.928200 -57.344002 0.000000
      vertex -88.633003 -56.500000 0.000000
      vertex -88.792000 -56.292999 0.000000
    endloop
  endfacet
  facet normal -0.859373 0.110203 0.499333
    outer loop
      vertex -92.499001 1.000000 5.500000
      vertex -92.961998 1.916000 4.501000
      vertex -93.081001 0.988000 4.501000
    endloop
  endfacet
  facet normal -0.562531 0.734405 0.379748
    outer loop
      vertex -49.730999 17.731001 3.241000
      vertex -49.566002 17.982000 3.000000
      vertex -49.800999 17.802000 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.499001 -57.000000 0.000000
      vertex -88.532997 -56.741001 0.000000
      vertex -43.928200 -57.344002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.532997 -56.741001 0.000000
      vertex -88.633003 -56.500000 0.000000
      vertex -43.928200 -57.344002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.532997 -57.258999 0.000000
      vertex -88.499001 -57.000000 0.000000
      vertex -43.928200 -57.344002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.239998 -56.034000 0.000000
      vertex -89.499001 -56.000000 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal -0.484812 0.630726 0.605923
    outer loop
      vertex -49.914001 17.914000 2.793000
      vertex -49.800999 17.802000 3.000000
      vertex -49.646000 18.120001 2.793000
    endloop
  endfacet
  facet normal -0.858632 -0.115781 0.499345
    outer loop
      vertex -92.397003 0.224000 5.500000
      vertex -93.081001 0.988000 4.501000
      vertex -92.956001 0.061000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.464996 1.259000 5.500000
      vertex -92.097000 2.500000 5.500000
      vertex -92.397003 1.776000 5.500000
    endloop
  endfacet
  facet normal -0.483141 0.630758 0.607223
    outer loop
      vertex -49.646000 18.120001 2.793000
      vertex -49.800999 17.802000 3.000000
      vertex -49.566002 17.982000 3.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -90.499001 -57.000000 0.000000
      vertex -90.464996 -57.258999 0.000000
      vertex -94.999001 -82.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -90.464996 -56.741001 0.000000
      vertex -90.499001 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -90.364998 -56.500000 0.000000
      vertex -90.464996 -56.741001 0.000000
    endloop
  endfacet
  facet normal -0.336915 0.436053 0.834474
    outer loop
      vertex -93.292000 4.768000 3.028000
      vertex -91.700996 4.784000 3.662000
      vertex -92.188004 5.621000 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -89.999001 -56.133999 0.000000
      vertex -90.206001 -56.292999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -90.206001 -56.292999 0.000000
      vertex -90.364998 -56.500000 0.000000
    endloop
  endfacet
  facet normal -0.373853 0.486372 0.789732
    outer loop
      vertex -49.749001 18.299000 2.634000
      vertex -49.914001 17.914000 2.793000
      vertex -49.646000 18.120001 2.793000
    endloop
  endfacet
  facet normal -0.371931 0.486014 0.790859
    outer loop
      vertex -50.060001 18.061001 2.634000
      vertex -49.914001 17.914000 2.793000
      vertex -49.749001 18.299000 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -88.999001 -57.866001 0.000000
      vertex -88.792000 -57.707001 0.000000
      vertex -92.999001 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.336806 0.436692 0.834183
    outer loop
      vertex -92.606003 4.086000 3.662000
      vertex -91.700996 4.784000 3.662000
      vertex -93.292000 4.768000 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.633003 -57.500000 0.000000
      vertex -88.532997 -57.258999 0.000000
      vertex -43.928200 -57.344002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -88.792000 -57.707001 0.000000
      vertex -88.633003 -57.500000 0.000000
      vertex -43.928200 -57.344002 0.000000
    endloop
  endfacet
  facet normal 0.733757 -0.562027 0.381741
    outer loop
      vertex -80.196999 16.198000 3.000000
      vertex -80.016998 16.433001 3.000000
      vertex -80.267998 16.268999 3.241000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -89.239998 -57.966000 0.000000
      vertex -88.999001 -57.866001 0.000000
      vertex -92.999001 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 -1.000000
    outer loop
      vertex -89.499001 -58.000000 0.000000
      vertex -89.239998 -57.966000 0.000000
      vertex -92.999001 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.212692 0.508336 0.834480
    outer loop
      vertex -92.188004 5.621000 3.028000
      vertex -91.700996 4.784000 3.662000
      vertex -90.647003 5.225000 3.662000
    endloop
  endfacet
  facet normal 0.632832 -0.484074 0.604314
    outer loop
      vertex -79.879997 16.354000 2.793000
      vertex -80.196999 16.198000 3.000000
      vertex -80.084999 16.086000 2.793000
    endloop
  endfacet
  facet normal -0.212504 0.508746 0.834278
    outer loop
      vertex -92.188004 5.621000 3.028000
      vertex -90.647003 5.225000 3.662000
      vertex -90.900002 6.159000 3.028000
    endloop
  endfacet
  facet normal 0.485505 -0.631622 0.604433
    outer loop
      vertex -80.084999 16.086000 2.793000
      vertex -80.196999 16.198000 3.000000
      vertex -80.352997 15.880000 2.793000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.499001 -58.000000 0.000000
      vertex -93.999001 -83.732002 0.000000
      vertex -94.413002 -83.414001 0.000000
    endloop
  endfacet
  facet normal -0.170898 0.484136 0.858141
    outer loop
      vertex -48.999001 18.740999 2.534000
      vertex -50.049999 18.370001 2.534000
      vertex -49.749001 18.299000 2.634000
    endloop
  endfacet
  facet normal 0.632820 -0.484713 0.603814
    outer loop
      vertex -80.016998 16.433001 3.000000
      vertex -80.196999 16.198000 3.000000
      vertex -79.879997 16.354000 2.793000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.499001 -58.000000 0.000000
      vertex -94.731003 -83.000000 0.000000
      vertex -94.931000 -82.517998 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -89.758003 -57.966000 0.000000
      vertex -89.499001 -58.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -90.464996 -57.258999 0.000000
      vertex -90.364998 -57.500000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.499001 -58.000000 0.000000
      vertex -94.931000 -82.517998 0.000000
      vertex -94.999001 -82.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.499001 -58.000000 0.000000
      vertex -94.413002 -83.414001 0.000000
      vertex -94.731003 -83.000000 0.000000
    endloop
  endfacet
  facet normal -0.209859 0.271570 0.939260
    outer loop
      vertex -94.064003 5.534000 2.634000
      vertex -92.188004 5.621000 3.028000
      vertex -92.735001 6.561000 2.634000
    endloop
  endfacet
  facet normal 0.562731 -0.734677 0.378925
    outer loop
      vertex -80.196999 16.198000 3.000000
      vertex -80.482002 16.104000 3.241000
      vertex -80.431999 16.018000 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -94.999001 -8.192000 0.000000
      vertex -90.499001 -57.000000 0.000000
    endloop
  endfacet
  facet normal -0.794215 0.154323 0.587713
    outer loop
      vertex -35.248001 -52.349998 2.985000
      vertex -35.203999 -53.703999 3.400000
      vertex -35.164001 -52.328999 3.093000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -89.499001 -58.000000 0.000000
      vertex -92.999001 -84.000000 0.000000
      vertex -93.516998 -83.931999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -93.516998 -83.931999 0.000000
      vertex -93.999001 -83.732002 0.000000
      vertex -89.499001 -58.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -89.999001 -57.866001 0.000000
      vertex -89.758003 -57.966000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -90.206001 -57.707001 0.000000
      vertex -89.999001 -57.866001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 -1.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -90.364998 -57.500000 0.000000
      vertex -90.206001 -57.707001 0.000000
    endloop
  endfacet
  facet normal -0.051760 0.241966 0.968903
    outer loop
      vertex -35.733002 -52.407001 2.686000
      vertex -36.209000 -52.673000 2.727000
      vertex -35.884998 -53.825001 3.032000
    endloop
  endfacet
  facet normal -0.486254 0.371945 0.790705
    outer loop
      vertex -50.298000 17.750000 2.634000
      vertex -50.118999 17.646000 2.793000
      vertex -49.914001 17.914000 2.793000
    endloop
  endfacet
  facet normal -0.209858 0.271609 0.939249
    outer loop
      vertex -92.188004 5.621000 3.028000
      vertex -94.064003 5.534000 2.634000
      vertex -93.292000 4.768000 3.028000
    endloop
  endfacet
  facet normal -0.486290 0.372142 0.790590
    outer loop
      vertex -50.298000 17.750000 2.634000
      vertex -49.914001 17.914000 2.793000
      vertex -50.060001 18.061001 2.634000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 82.621002 85.000000 2.597000
      vertex 82.931000 85.000000 2.526000
    endloop
  endfacet
  facet normal -0.132335 0.316543 0.939302
    outer loop
      vertex -92.735001 6.561000 2.634000
      vertex -90.900002 6.159000 3.028000
      vertex -91.184998 7.209000 2.634000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 82.931000 85.000000 2.526000
      vertex 82.998001 85.000000 2.520288
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.073859 0.546244 0.834363
    outer loop
      vertex -89.516998 6.346000 3.028000
      vertex -90.900002 6.159000 3.028000
      vertex -89.514000 5.378000 3.662000
    endloop
  endfacet
  facet normal -0.132289 0.316707 0.939253
    outer loop
      vertex -92.735001 6.561000 2.634000
      vertex -92.188004 5.621000 3.028000
      vertex -90.900002 6.159000 3.028000
    endloop
  endfacet
  facet normal -0.384073 0.293919 0.875271
    outer loop
      vertex -50.594002 17.660999 2.534000
      vertex -50.298000 17.750000 2.634000
      vertex -50.060001 18.061001 2.634000
    endloop
  endfacet
  facet normal 0.044917 -0.340151 0.939297
    outer loop
      vertex -40.500000 -62.346001 3.028000
      vertex -40.500000 -63.433998 2.634000
      vertex -38.834000 -63.214001 2.634000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 81.000000 85.000000 3.500000
      vertex 25.000000 85.000000 0.000000
      vertex 25.000000 85.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 81.000000 85.000000 3.500000
      vertex 82.057999 85.000000 2.826000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 82.057999 85.000000 2.826000
      vertex 82.621002 85.000000 2.597000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.385027 0.295423 0.874345
    outer loop
      vertex -50.060001 18.061001 2.634000
      vertex -50.049999 18.370001 2.534000
      vertex -50.594002 17.660999 2.534000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 25.000000 85.000000 0.000000
      vertex 81.000000 85.000000 3.500000
    endloop
  endfacet
  facet normal -0.107895 0.082785 0.990710
    outer loop
      vertex -50.831001 17.759001 2.500000
      vertex -50.594002 17.660999 2.534000
      vertex -50.049999 18.370001 2.534000
    endloop
  endfacet
  facet normal -0.000000 1.000000 0.000000
    outer loop
      vertex 25.000000 85.000000 10.500000
      vertex 81.000000 85.000000 10.500000
      vertex 81.000000 85.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 82.414001 84.414001 10.500000
      vertex 82.000000 84.732002 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 82.000000 84.732002 10.500000
      vertex 81.516998 84.931999 10.500000
      vertex 80.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 82.998001 83.015015 10.500000
      vertex 82.931000 83.517998 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 81.000000 85.000000 10.500000
      vertex 25.000000 85.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 82.931000 83.517998 10.500000
      vertex 82.732002 84.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 82.732002 84.000000 10.500000
      vertex 82.414001 84.414001 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 81.516998 84.931999 10.500000
      vertex 81.000000 85.000000 10.500000
    endloop
  endfacet
  facet normal 0.352590 -0.855795 0.378545
    outer loop
      vertex -80.482002 16.104000 3.241000
      vertex -80.732002 16.000999 3.241000
      vertex -80.431999 16.018000 3.000000
    endloop
  endfacet
  facet normal -0.686732 0.527543 0.500097
    outer loop
      vertex -42.620998 3.121000 5.500000
      vertex -43.032001 3.533000 4.501000
      vertex -43.602001 2.791000 4.501000
    endloop
  endfacet
  facet normal 0.483818 -0.631652 0.605751
    outer loop
      vertex -80.431999 16.018000 3.000000
      vertex -80.352997 15.880000 2.793000
      vertex -80.196999 16.198000 3.000000
    endloop
  endfacet
  facet normal 0.209338 0.509917 0.834363
    outer loop
      vertex -88.133003 -51.831001 3.028000
      vertex -88.379997 -52.766998 3.662000
      vertex -86.842003 -52.361000 3.028000
    endloop
  endfacet
  facet normal -0.686745 0.527501 0.500124
    outer loop
      vertex -42.620998 3.121000 5.500000
      vertex -43.602001 2.791000 4.501000
      vertex -43.098000 2.500000 5.500000
    endloop
  endfacet
  facet normal 0.352834 -0.855552 0.378866
    outer loop
      vertex -80.706001 15.905000 3.000000
      vertex -80.431999 16.018000 3.000000
      vertex -80.732002 16.000999 3.241000
    endloop
  endfacet
  facet normal 0.485077 -0.371052 0.791846
    outer loop
      vertex -79.699997 16.250000 2.634000
      vertex -79.879997 16.354000 2.793000
      vertex -80.084999 16.086000 2.793000
    endloop
  endfacet
  facet normal 0.485451 -0.373073 0.790666
    outer loop
      vertex -79.939003 15.939000 2.634000
      vertex -79.699997 16.250000 2.634000
      vertex -80.084999 16.086000 2.793000
    endloop
  endfacet
  facet normal -0.588022 0.092137 0.803580
    outer loop
      vertex -35.248001 -52.349998 2.985000
      vertex -35.500000 -50.896999 2.634000
      vertex -35.604000 -52.397999 2.730000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.276001 3.898000 5.500000
      vertex -42.000000 3.598000 5.500000
      vertex -41.000000 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -42.000000 3.598000 5.500000
      vertex -42.620998 3.121000 5.500000
      vertex -41.000000 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.303734 -0.734624 0.606690
    outer loop
      vertex -80.352997 15.880000 2.793000
      vertex -80.706001 15.905000 3.000000
      vertex -80.665001 15.751000 2.793000
    endloop
  endfacet
  facet normal 0.043556 0.340570 0.939210
    outer loop
      vertex -87.855003 -50.779999 2.634000
      vertex -89.516998 -51.653999 3.028000
      vertex -88.133003 -51.831001 3.028000
    endloop
  endfacet
  facet normal 0.303276 -0.735383 0.606000
    outer loop
      vertex -80.706001 15.905000 3.000000
      vertex -80.352997 15.880000 2.793000
      vertex -80.431999 16.018000 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.366001 1.500000 5.500000
      vertex -43.098000 2.500000 5.500000
      vertex -43.396999 1.776000 5.500000
    endloop
  endfacet
  facet normal 0.372909 -0.485139 0.790936
    outer loop
      vertex -79.939003 15.939000 2.634000
      vertex -80.084999 16.086000 2.793000
      vertex -80.352997 15.880000 2.793000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.366001 1.500000 5.500000
      vertex -41.207001 1.707000 5.500000
      vertex -42.620998 3.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.207001 1.707000 5.500000
      vertex -41.000000 1.866000 5.500000
      vertex -42.620998 3.121000 5.500000
    endloop
  endfacet
  facet normal 0.305852 -0.235050 0.922608
    outer loop
      vertex -79.939003 15.939000 2.634000
      vertex -79.767998 15.769000 2.534000
      vertex -79.699997 16.250000 2.634000
    endloop
  endfacet
  facet normal 0.209356 0.509880 0.834382
    outer loop
      vertex -86.842003 -52.361000 3.028000
      vertex -88.379997 -52.766998 3.662000
      vertex -87.322998 -53.201000 3.662000
    endloop
  endfacet
  facet normal -0.800022 -0.330396 0.500802
    outer loop
      vertex -43.396999 -57.776001 5.500000
      vertex -43.959999 -57.926998 4.501000
      vertex -43.098000 -58.500000 5.500000
    endloop
  endfacet
  facet normal 0.130390 0.317612 0.939213
    outer loop
      vertex -86.301003 -51.417999 2.634000
      vertex -88.133003 -51.831001 3.028000
      vertex -86.842003 -52.361000 3.028000
    endloop
  endfacet
  facet normal 0.334138 0.438408 0.834356
    outer loop
      vertex -86.842003 -52.361000 3.028000
      vertex -87.322998 -53.201000 3.662000
      vertex -85.732002 -53.207001 3.028000
    endloop
  endfacet
  facet normal -0.577752 -0.443825 0.684997
    outer loop
      vertex -43.602001 -58.791000 4.501000
      vertex -44.291000 -59.188999 3.662000
      vertex -43.032001 -59.533001 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -43.396999 1.776000 5.500000
      vertex -41.500000 1.000000 5.500000
      vertex -41.465000 1.259000 5.500000
    endloop
  endfacet
  facet normal 0.207922 0.273141 0.939235
    outer loop
      vertex -86.301003 -51.417999 2.634000
      vertex -86.842003 -52.361000 3.028000
      vertex -84.964996 -52.435001 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -43.396999 0.224000 5.500000
      vertex -41.366001 0.500000 5.500000
      vertex -41.465000 0.741000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -43.396999 1.776000 5.500000
      vertex -41.465000 1.259000 5.500000
      vertex -41.366001 1.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -43.396999 0.224000 5.500000
      vertex -41.465000 0.741000 5.500000
      vertex -41.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.207929 0.272815 0.939328
    outer loop
      vertex -84.964996 -52.435001 2.634000
      vertex -86.842003 -52.361000 3.028000
      vertex -85.732002 -53.207001 3.028000
    endloop
  endfacet
  facet normal -0.799984 -0.331472 0.500152
    outer loop
      vertex -43.098000 -58.500000 5.500000
      vertex -43.959999 -57.926998 4.501000
      vertex -43.602001 -58.791000 4.501000
    endloop
  endfacet
  facet normal -0.854871 -0.352565 0.380650
    outer loop
      vertex -49.981998 16.433001 3.000000
      vertex -49.998001 16.732000 3.241000
      vertex -50.095001 16.707001 3.000000
    endloop
  endfacet
  facet normal -0.686744 -0.527502 0.500124
    outer loop
      vertex -43.098000 -58.500000 5.500000
      vertex -43.602001 -58.791000 4.501000
      vertex -42.620998 -59.120998 5.500000
    endloop
  endfacet
  facet normal 0.793050 0.609156 0.000000
    outer loop
      vertex -41.366001 0.500000 5.500000
      vertex -41.207001 0.293000 5.500000
      vertex -41.207001 0.293000 0.000000
    endloop
  endfacet
  facet normal -0.045971 0.339985 0.939307
    outer loop
      vertex -89.521004 -50.566002 2.634000
      vertex -91.184998 -50.791000 2.634000
      vertex -89.516998 -51.653999 3.028000
    endloop
  endfacet
  facet normal -0.686732 -0.527543 0.500098
    outer loop
      vertex -42.620998 -59.120998 5.500000
      vertex -43.602001 -58.791000 4.501000
      vertex -43.032001 -59.533001 4.501000
    endloop
  endfacet
  facet normal 0.990992 0.133917 -0.000000
    outer loop
      vertex -41.465000 0.741000 5.500000
      vertex -41.500000 1.000000 0.000000
      vertex -41.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.130393 0.317603 0.939216
    outer loop
      vertex -86.301003 -51.417999 2.634000
      vertex -87.855003 -50.779999 2.634000
      vertex -88.133003 -51.831001 3.028000
    endloop
  endfacet
  facet normal 0.990992 -0.133917 0.000000
    outer loop
      vertex -41.500000 1.000000 5.500000
      vertex -41.500000 1.000000 0.000000
      vertex -41.465000 1.259000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.000000 -57.866001 5.500000
      vertex -41.207001 -57.707001 5.500000
      vertex -42.620998 -59.120998 5.500000
    endloop
  endfacet
  facet normal -0.735791 -0.303454 0.605415
    outer loop
      vertex -50.095001 16.707001 3.000000
      vertex -50.248001 16.665001 2.793000
      vertex -49.981998 16.433001 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.207001 -57.707001 5.500000
      vertex -41.366001 -57.500000 5.500000
      vertex -42.620998 -59.120998 5.500000
    endloop
  endfacet
  facet normal -0.917938 0.123303 0.377075
    outer loop
      vertex -50.132999 17.000000 3.000000
      vertex -50.034000 17.000000 3.241000
      vertex -49.998001 17.268000 3.241000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -43.098000 -58.500000 5.500000
      vertex -42.620998 -59.120998 5.500000
      vertex -41.366001 -57.500000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -42.620998 -59.120998 5.500000
      vertex -42.000000 -59.598000 5.500000
      vertex -41.000000 -57.866001 5.500000
    endloop
  endfacet
  facet normal -0.789898 -0.102439 0.604622
    outer loop
      vertex -50.248001 16.665001 2.793000
      vertex -50.095001 16.707001 3.000000
      vertex -50.132999 17.000000 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 82.998001 83.015015 10.500000
      vertex 80.000000 83.000000 10.500000
      vertex 80.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.052434 0.125420 0.990717
    outer loop
      vertex -90.879997 8.395000 2.500000
      vertex -92.735001 6.561000 2.634000
      vertex -91.184998 7.209000 2.634000
    endloop
  endfacet
  facet normal -0.081535 0.154411 0.984637
    outer loop
      vertex -92.735001 6.561000 2.634000
      vertex -90.879997 8.395000 2.500000
      vertex -94.999001 6.220000 2.500000
    endloop
  endfacet
  facet normal -0.799984 0.331473 0.500152
    outer loop
      vertex -43.602001 2.791000 4.501000
      vertex -43.959999 1.927000 4.501000
      vertex -43.098000 2.500000 5.500000
    endloop
  endfacet
  facet normal -0.916765 0.118893 0.381322
    outer loop
      vertex -50.095001 17.292999 3.000000
      vertex -50.132999 17.000000 3.000000
      vertex -49.998001 17.268000 3.241000
    endloop
  endfacet
  facet normal -0.800022 0.330396 0.500803
    outer loop
      vertex -43.098000 2.500000 5.500000
      vertex -43.959999 1.927000 4.501000
      vertex -43.396999 1.776000 5.500000
    endloop
  endfacet
  facet normal -0.527470 -0.686703 0.500215
    outer loop
      vertex -42.620998 -59.120998 5.500000
      vertex -43.032001 -59.533001 4.501000
      vertex -42.000000 -59.598000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 -82.000000 10.500000
      vertex 82.998001 -84.000000 10.500000
      vertex 82.998001 83.015015 10.500000
    endloop
  endfacet
  facet normal -0.858434 0.113942 0.500109
    outer loop
      vertex -43.396999 1.776000 5.500000
      vertex -44.082001 1.000000 4.501000
      vertex -43.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.854871 0.352565 0.380650
    outer loop
      vertex -50.095001 17.292999 3.000000
      vertex -49.998001 17.268000 3.241000
      vertex -49.981998 17.566999 3.000000
    endloop
  endfacet
  facet normal -0.527396 -0.686820 0.500131
    outer loop
      vertex -42.000000 -59.598000 5.500000
      vertex -43.032001 -59.533001 4.501000
      vertex -42.291000 -60.102001 4.501000
    endloop
  endfacet
  facet normal -0.858206 0.112948 0.500725
    outer loop
      vertex -43.396999 1.776000 5.500000
      vertex -43.959999 1.927000 4.501000
      vertex -44.082001 1.000000 4.501000
    endloop
  endfacet
  facet normal -0.331483 -0.799979 0.500153
    outer loop
      vertex -42.000000 -59.598000 5.500000
      vertex -42.291000 -60.102001 4.501000
      vertex -41.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal -0.858206 -0.112948 0.500725
    outer loop
      vertex -43.396999 0.224000 5.500000
      vertex -44.082001 1.000000 4.501000
      vertex -43.959999 0.073000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 80.000000 -82.000000 10.500000
      vertex 25.000000 -82.000000 10.500000
      vertex 25.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal -0.331474 -0.799988 0.500145
    outer loop
      vertex -41.276001 -59.897999 5.500000
      vertex -42.291000 -60.102001 4.501000
      vertex -41.426998 -60.459999 4.501000
    endloop
  endfacet
  facet normal -0.858434 -0.113942 0.500109
    outer loop
      vertex -43.500000 1.000000 5.500000
      vertex -44.082001 1.000000 4.501000
      vertex -43.396999 0.224000 5.500000
    endloop
  endfacet
  facet normal 0.793051 0.609155 0.000000
    outer loop
      vertex 82.414001 84.414001 10.500000
      vertex 82.732002 84.000000 10.500000
      vertex 82.414001 84.414001 3.500000
    endloop
  endfacet
  facet normal 0.609155 0.793051 0.000000
    outer loop
      vertex 82.414001 84.414001 10.500000
      vertex 82.414001 84.414001 3.500000
      vertex 82.000000 84.732002 10.500000
    endloop
  endfacet
  facet normal -0.788783 -0.103599 0.605878
    outer loop
      vertex -50.248001 16.665001 2.793000
      vertex -50.132999 17.000000 3.000000
      vertex -50.292000 17.000000 2.793000
    endloop
  endfacet
  facet normal -0.722121 -0.095038 0.685208
    outer loop
      vertex -44.082001 -57.000000 4.501000
      vertex -44.729000 -58.132999 3.662000
      vertex -43.959999 -57.926998 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.500000 1.000000 5.500000
      vertex -43.396999 1.776000 5.500000
      vertex -43.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -43.500000 1.000000 5.500000
      vertex -43.396999 0.224000 5.500000
      vertex -41.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.672882 -0.278807 0.685198
    outer loop
      vertex -44.729000 -58.132999 3.662000
      vertex -43.602001 -58.791000 4.501000
      vertex -43.959999 -57.926998 4.501000
    endloop
  endfacet
  facet normal -0.672931 -0.279113 0.685025
    outer loop
      vertex -44.729000 -58.132999 3.662000
      vertex -44.291000 -59.188999 3.662000
      vertex -43.602001 -58.791000 4.501000
    endloop
  endfacet
  facet normal -0.546481 -0.071864 0.834382
    outer loop
      vertex -44.729000 -58.132999 3.662000
      vertex -45.846001 -57.000000 3.028000
      vertex -45.664001 -58.383999 3.028000
    endloop
  endfacet
  facet normal 0.609155 0.793051 -0.000000
    outer loop
      vertex 82.000000 84.732002 3.500000
      vertex 82.000000 84.732002 10.500000
      vertex 82.414001 84.414001 3.500000
    endloop
  endfacet
  facet normal -0.131288 0.317176 0.939235
    outer loop
      vertex -41.882999 6.164000 3.028000
      vertex -42.165001 7.214000 2.634000
      vertex -43.716000 6.572000 2.634000
    endloop
  endfacet
  facet normal 0.379275 0.915966 0.130984
    outer loop
      vertex 82.000000 84.732002 3.500000
      vertex 82.016998 84.762001 3.241000
      vertex 81.516998 84.931999 3.500000
    endloop
  endfacet
  facet normal -0.042307 0.102208 0.993863
    outer loop
      vertex -42.165001 7.214000 2.634000
      vertex -43.472000 7.976000 2.500000
      vertex -43.716000 6.572000 2.634000
    endloop
  endfacet
  facet normal -0.062223 0.105536 0.992467
    outer loop
      vertex -43.472000 7.976000 2.500000
      vertex -45.162998 6.979000 2.500000
      vertex -43.716000 6.572000 2.634000
    endloop
  endfacet
  facet normal -0.607272 -0.079820 0.790474
    outer loop
      vertex -50.448002 16.612000 2.634000
      vertex -50.248001 16.665001 2.793000
      vertex -50.499001 17.000000 2.634000
    endloop
  endfacet
  facet normal -0.607213 -0.079751 0.790526
    outer loop
      vertex -50.499001 17.000000 2.634000
      vertex -50.248001 16.665001 2.793000
      vertex -50.292000 17.000000 2.793000
    endloop
  endfacet
  facet normal -0.789898 0.102439 0.604622
    outer loop
      vertex -50.248001 17.334999 2.793000
      vertex -50.132999 17.000000 3.000000
      vertex -50.095001 17.292999 3.000000
    endloop
  endfacet
  facet normal -0.788783 0.103599 0.605878
    outer loop
      vertex -50.292000 17.000000 2.793000
      vertex -50.132999 17.000000 3.000000
      vertex -50.248001 17.334999 2.793000
    endloop
  endfacet
  facet normal 0.604076 0.786439 0.128862
    outer loop
      vertex 82.000000 84.732002 3.500000
      vertex 82.414001 84.414001 3.500000
      vertex 82.438004 84.438004 3.241000
    endloop
  endfacet
  facet normal -0.735791 0.303454 0.605415
    outer loop
      vertex -49.981998 17.566999 3.000000
      vertex -50.248001 17.334999 2.793000
      vertex -50.095001 17.292999 3.000000
    endloop
  endfacet
  facet normal 0.786785 0.603627 0.128852
    outer loop
      vertex 82.438004 84.438004 3.241000
      vertex 82.414001 84.414001 3.500000
      vertex 82.761002 84.016998 3.241000
    endloop
  endfacet
  facet normal 0.604654 0.785693 0.130687
    outer loop
      vertex 82.016998 84.762001 3.241000
      vertex 82.000000 84.732002 3.500000
      vertex 82.438004 84.438004 3.241000
    endloop
  endfacet
  facet normal -0.131291 0.317165 0.939239
    outer loop
      vertex -41.882999 6.164000 3.028000
      vertex -43.716000 6.572000 2.634000
      vertex -43.173000 5.630000 3.028000
    endloop
  endfacet
  facet normal 0.372867 -0.485664 0.790633
    outer loop
      vertex -80.249001 15.701000 2.634000
      vertex -79.939003 15.939000 2.634000
      vertex -80.352997 15.880000 2.793000
    endloop
  endfacet
  facet normal -0.480825 -0.063199 0.874536
    outer loop
      vertex -50.594002 16.339001 2.534000
      vertex -50.448002 16.612000 2.634000
      vertex -50.499001 17.000000 2.634000
    endloop
  endfacet
  facet normal 0.234060 -0.566106 0.790405
    outer loop
      vertex -80.249001 15.701000 2.634000
      vertex -80.352997 15.880000 2.793000
      vertex -80.665001 15.751000 2.793000
    endloop
  endfacet
  facet normal 0.235071 -0.306183 0.922493
    outer loop
      vertex -80.249001 15.701000 2.634000
      vertex -79.767998 15.769000 2.534000
      vertex -79.939003 15.939000 2.634000
    endloop
  endfacet
  facet normal 0.234297 -0.565434 0.790815
    outer loop
      vertex -80.249001 15.701000 2.634000
      vertex -80.665001 15.751000 2.793000
      vertex -80.611000 15.551000 2.634000
    endloop
  endfacet
  facet normal 0.378831 0.916303 0.129907
    outer loop
      vertex 81.526001 84.964996 3.241000
      vertex 81.516998 84.931999 3.500000
      vertex 82.016998 84.762001 3.241000
    endloop
  endfacet
  facet normal -0.607213 0.079751 0.790526
    outer loop
      vertex -50.499001 17.000000 2.634000
      vertex -50.292000 17.000000 2.793000
      vertex -50.248001 17.334999 2.793000
    endloop
  endfacet
  facet normal -0.607272 0.079820 0.790474
    outer loop
      vertex -50.499001 17.000000 2.634000
      vertex -50.248001 17.334999 2.793000
      vertex -50.448002 17.388000 2.634000
    endloop
  endfacet
  facet normal -0.736271 0.305402 0.603849
    outer loop
      vertex -50.118999 17.646000 2.793000
      vertex -50.248001 17.334999 2.793000
      vertex -49.981998 17.566999 3.000000
    endloop
  endfacet
  facet normal 0.793051 0.609155 -0.000000
    outer loop
      vertex 82.732002 84.000000 3.500000
      vertex 82.414001 84.414001 3.500000
      vertex 82.732002 84.000000 10.500000
    endloop
  endfacet
  facet normal -0.071874 0.546533 0.834348
    outer loop
      vertex -40.500000 5.378000 3.662000
      vertex -41.882999 6.164000 3.028000
      vertex -41.632999 5.229000 3.662000
    endloop
  endfacet
  facet normal -0.072991 0.094455 0.992850
    outer loop
      vertex -94.999001 6.220000 2.500000
      vertex -94.064003 5.534000 2.634000
      vertex -92.735001 6.561000 2.634000
    endloop
  endfacet
  facet normal -0.480825 0.063199 0.874536
    outer loop
      vertex -50.594002 17.660999 2.534000
      vertex -50.499001 17.000000 2.634000
      vertex -50.448002 17.388000 2.634000
    endloop
  endfacet
  facet normal -0.565882 0.234484 0.790439
    outer loop
      vertex -50.448002 17.388000 2.634000
      vertex -50.118999 17.646000 2.793000
      vertex -50.298000 17.750000 2.634000
    endloop
  endfacet
  facet normal -0.566025 0.234784 0.790248
    outer loop
      vertex -50.118999 17.646000 2.793000
      vertex -50.448002 17.388000 2.634000
      vertex -50.248001 17.334999 2.793000
    endloop
  endfacet
  facet normal -0.356097 0.147556 0.922725
    outer loop
      vertex -50.594002 17.660999 2.534000
      vertex -50.448002 17.388000 2.634000
      vertex -50.298000 17.750000 2.634000
    endloop
  endfacet
  facet normal -0.278500 0.672988 0.685219
    outer loop
      vertex -42.688999 4.792000 3.662000
      vertex -41.426998 4.460000 4.501000
      vertex -41.632999 5.229000 3.662000
    endloop
  endfacet
  facet normal 0.786557 0.604166 0.127720
    outer loop
      vertex 82.414001 84.414001 3.500000
      vertex 82.732002 84.000000 3.500000
      vertex 82.761002 84.016998 3.241000
    endloop
  endfacet
  facet normal -0.380532 0.084626 0.920888
    outer loop
      vertex -50.741001 17.000000 2.534000
      vertex -50.499001 17.000000 2.634000
      vertex -50.594002 17.660999 2.534000
    endloop
  endfacet
  facet normal -0.353399 0.000000 0.935473
    outer loop
      vertex -50.831001 16.240999 2.500000
      vertex -50.741001 17.000000 2.534000
      vertex -50.831001 17.759001 2.500000
    endloop
  endfacet
  facet normal -0.130204 0.028956 0.991064
    outer loop
      vertex -50.831001 17.759001 2.500000
      vertex -50.741001 17.000000 2.534000
      vertex -50.594002 17.660999 2.534000
    endloop
  endfacet
  facet normal -0.209018 0.272215 0.939260
    outer loop
      vertex -44.279999 4.780000 3.028000
      vertex -43.173000 5.630000 3.028000
      vertex -45.049000 5.549000 2.634000
    endloop
  endfacet
  facet normal -0.209016 0.272354 0.939221
    outer loop
      vertex -45.049000 5.549000 2.634000
      vertex -43.173000 5.630000 3.028000
      vertex -43.716000 6.572000 2.634000
    endloop
  endfacet
  facet normal 0.564654 0.233192 0.791699
    outer loop
      vertex 82.985001 84.146004 2.793000
      vertex 82.998001 84.130882 2.788182
      vertex 82.998001 84.153511 2.781517
    endloop
  endfacet
  facet normal -0.278724 0.672677 0.685433
    outer loop
      vertex -42.688999 4.792000 3.662000
      vertex -42.291000 4.102000 4.501000
      vertex -41.426998 4.460000 4.501000
    endloop
  endfacet
  facet normal -0.673764 0.276513 0.685261
    outer loop
      vertex -92.607002 2.781000 4.501000
      vertex -93.732002 2.119000 3.662000
      vertex -92.961998 1.916000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -50.831001 17.759001 2.500000
      vertex -92.999001 83.000000 2.500000
      vertex -79.426003 18.207001 2.500000
    endloop
  endfacet
  facet normal 0.565452 0.234151 0.790846
    outer loop
      vertex 82.985001 84.146004 2.793000
      vertex 82.998001 84.114609 2.793000
      vertex 82.998001 84.130882 2.788182
    endloop
  endfacet
  facet normal 0.239229 -0.375273 0.895511
    outer loop
      vertex -79.767998 15.769000 2.534000
      vertex -80.249001 15.701000 2.634000
      vertex -80.338997 15.405000 2.534000
    endloop
  endfacet
  facet normal 0.147755 -0.356581 0.922506
    outer loop
      vertex -80.338997 15.405000 2.534000
      vertex -80.249001 15.701000 2.634000
      vertex -80.611000 15.551000 2.634000
    endloop
  endfacet
  facet normal 0.736474 0.304970 0.603821
    outer loop
      vertex 82.998001 84.114609 2.793000
      vertex 82.985001 84.146004 2.793000
      vertex 82.848000 84.067001 3.000000
    endloop
  endfacet
  facet normal 0.484792 0.371501 0.791811
    outer loop
      vertex 82.998001 84.153511 2.781517
      vertex 82.998001 84.363892 2.682811
      vertex 82.621002 84.621002 2.793000
    endloop
  endfacet
  facet normal -0.579480 0.441435 0.685082
    outer loop
      vertex -93.297997 3.176000 3.662000
      vertex -92.607002 2.781000 4.501000
      vertex -92.041000 3.524000 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 84.130882 2.788182
      vertex 82.998001 84.114609 2.793000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.122118 -0.917455 0.378633
    outer loop
      vertex -80.999001 15.866000 3.000000
      vertex -80.706001 15.905000 3.000000
      vertex -80.732002 16.000999 3.241000
    endloop
  endfacet
  facet normal 0.120199 -0.916947 0.380474
    outer loop
      vertex -80.999001 15.866000 3.000000
      vertex -80.732002 16.000999 3.241000
      vertex -80.999001 15.966000 3.241000
    endloop
  endfacet
  facet normal -0.793979 -0.607946 -0.000000
    outer loop
      vertex -35.584999 15.414000 10.500000
      vertex -35.584999 15.414000 3.500000
      vertex -35.268002 15.000000 10.500000
    endloop
  endfacet
  facet normal -0.608231 -0.793760 -0.000000
    outer loop
      vertex -36.000000 15.732000 10.500000
      vertex -35.584999 15.414000 3.500000
      vertex -35.584999 15.414000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.793050 0.609156
    outer loop
      vertex -80.999001 15.866000 3.000000
      vertex -92.999001 15.866000 3.000000
      vertex -80.999001 15.707000 2.793000
    endloop
  endfacet
  facet normal -0.130157 -0.991493 -0.000000
    outer loop
      vertex -37.000000 16.000000 10.500000
      vertex -37.000000 16.000000 3.500000
      vertex -36.481998 15.932000 3.500000
    endloop
  endfacet
  facet normal 0.104975 -0.788669 0.605790
    outer loop
      vertex -80.999001 15.866000 3.000000
      vertex -80.999001 15.707000 2.793000
      vertex -80.706001 15.905000 3.000000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 84.153511 2.781517
      vertex 82.998001 84.130882 2.788182
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 84.114609 2.793000
      vertex 82.998001 83.872734 2.915164
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 84.467354 2.634000
      vertex 82.998001 84.363892 2.682811
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 84.363892 2.682811
      vertex 82.998001 84.153511 2.781517
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.673789 0.276659 0.685178
    outer loop
      vertex -93.732002 2.119000 3.662000
      vertex -92.607002 2.781000 4.501000
      vertex -93.297997 3.176000 3.662000
    endloop
  endfacet
  facet normal 0.103814 -0.788029 0.606823
    outer loop
      vertex -80.665001 15.751000 2.793000
      vertex -80.706001 15.905000 3.000000
      vertex -80.999001 15.707000 2.793000
    endloop
  endfacet
  facet normal -0.608231 -0.793760 -0.000000
    outer loop
      vertex -35.584999 15.414000 3.500000
      vertex -36.000000 15.732000 10.500000
      vertex -36.000000 15.732000 3.500000
    endloop
  endfacet
  facet normal -0.383255 -0.923643 0.000000
    outer loop
      vertex -36.481998 15.932000 10.500000
      vertex -36.000000 15.732000 3.500000
      vertex -36.000000 15.732000 10.500000
    endloop
  endfacet
  facet normal -0.383255 -0.923643 0.000000
    outer loop
      vertex -36.481998 15.932000 3.500000
      vertex -36.000000 15.732000 3.500000
      vertex -36.481998 15.932000 10.500000
    endloop
  endfacet
  facet normal -0.509907 0.209368 0.834362
    outer loop
      vertex -94.667999 2.366000 3.028000
      vertex -93.732002 2.119000 3.662000
      vertex -93.297997 3.176000 3.662000
    endloop
  endfacet
  facet normal 0.079992 -0.607203 0.790510
    outer loop
      vertex -80.999001 15.707000 2.793000
      vertex -80.999001 15.500000 2.634000
      vertex -80.665001 15.751000 2.793000
    endloop
  endfacet
  facet normal 0.079789 -0.607031 0.790663
    outer loop
      vertex -80.999001 15.500000 2.634000
      vertex -80.611000 15.551000 2.634000
      vertex -80.665001 15.751000 2.793000
    endloop
  endfacet
  facet normal -0.438612 0.334293 0.834187
    outer loop
      vertex -93.292000 4.768000 3.028000
      vertex -94.138000 3.658000 3.028000
      vertex -92.606003 4.086000 3.662000
    endloop
  endfacet
  facet normal -0.579551 0.440709 0.685490
    outer loop
      vertex -92.606003 4.086000 3.662000
      vertex -93.297997 3.176000 3.662000
      vertex -92.041000 3.524000 4.501000
    endloop
  endfacet
  facet normal -0.380126 -0.916101 0.127524
    outer loop
      vertex -36.016998 15.703000 3.241000
      vertex -36.000000 15.732000 3.500000
      vertex -36.481998 15.932000 3.500000
    endloop
  endfacet
  facet normal -0.438535 0.333477 0.834554
    outer loop
      vertex -92.606003 4.086000 3.662000
      vertex -94.138000 3.658000 3.028000
      vertex -93.297997 3.176000 3.662000
    endloop
  endfacet
  facet normal 0.050312 -0.382769 0.922473
    outer loop
      vertex -80.999001 15.259000 2.534000
      vertex -80.611000 15.551000 2.634000
      vertex -80.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal -0.603162 -0.787145 0.128834
    outer loop
      vertex -35.609001 15.390000 3.241000
      vertex -35.584999 15.414000 3.500000
      vertex -36.000000 15.732000 3.500000
    endloop
  endfacet
  facet normal -0.509101 -0.211161 0.834403
    outer loop
      vertex -44.291000 -59.188999 3.662000
      vertex -44.729000 -58.132999 3.662000
      vertex -45.664001 -58.383999 3.028000
    endloop
  endfacet
  facet normal -0.272950 0.208032 0.939266
    outer loop
      vertex -94.064003 5.534000 2.634000
      vertex -94.138000 3.658000 3.028000
      vertex -93.292000 4.768000 3.028000
    endloop
  endfacet
  facet normal -0.603693 -0.786918 0.127732
    outer loop
      vertex -35.609001 15.390000 3.241000
      vertex -36.000000 15.732000 3.500000
      vertex -36.016998 15.703000 3.241000
    endloop
  endfacet
  facet normal -0.721518 -0.097520 0.685494
    outer loop
      vertex -93.877998 0.985000 3.662000
      vertex -93.724998 -0.147000 3.662000
      vertex -92.956001 0.061000 4.501000
    endloop
  endfacet
  facet normal -0.722318 0.092627 0.685330
    outer loop
      vertex -93.732002 2.119000 3.662000
      vertex -93.081001 0.988000 4.501000
      vertex -92.961998 1.916000 4.501000
    endloop
  endfacet
  facet normal 0.609155 0.793051 -0.000000
    outer loop
      vertex -41.000000 -57.866001 5.500000
      vertex -41.207001 -57.707001 0.000000
      vertex -41.207001 -57.707001 5.500000
    endloop
  endfacet
  facet normal 0.793051 0.609155 -0.000000
    outer loop
      vertex -41.207001 -57.707001 0.000000
      vertex -41.366001 -57.500000 5.500000
      vertex -41.207001 -57.707001 5.500000
    endloop
  endfacet
  facet normal -0.378882 -0.916281 0.129916
    outer loop
      vertex -36.016998 15.703000 3.241000
      vertex -36.481998 15.932000 3.500000
      vertex -36.491001 15.899000 3.241000
    endloop
  endfacet
  facet normal -0.721410 -0.097277 0.685642
    outer loop
      vertex -93.081001 0.988000 4.501000
      vertex -93.877998 0.985000 3.662000
      vertex -92.956001 0.061000 4.501000
    endloop
  endfacet
  facet normal 0.131292 0.317165 0.939238
    outer loop
      vertex -37.283001 -51.428001 2.634000
      vertex -39.116001 -51.835999 3.028000
      vertex -37.826000 -52.369999 3.028000
    endloop
  endfacet
  facet normal -0.577857 -0.442789 0.685579
    outer loop
      vertex -44.291000 -59.188999 3.662000
      vertex -43.596001 -60.096001 3.662000
      vertex -43.032001 -59.533001 4.501000
    endloop
  endfacet
  facet normal 0.047988 0.115932 0.992097
    outer loop
      vertex -37.283001 -51.428001 2.634000
      vertex -38.667999 -49.708000 2.500000
      vertex -38.834000 -50.785999 2.634000
    endloop
  endfacet
  facet normal 0.271482 0.210006 0.939252
    outer loop
      vertex -85.732002 -53.207001 3.028000
      vertex -84.877998 -54.311001 3.028000
      vertex -83.938004 -53.764000 2.634000
    endloop
  endfacet
  facet normal 0.271417 0.209739 0.939331
    outer loop
      vertex -85.732002 -53.207001 3.028000
      vertex -83.938004 -53.764000 2.634000
      vertex -84.964996 -52.435001 2.634000
    endloop
  endfacet
  facet normal -0.443399 -0.577432 0.685543
    outer loop
      vertex -43.032001 -59.533001 4.501000
      vertex -43.596001 -60.096001 3.662000
      vertex -42.291000 -60.102001 4.501000
    endloop
  endfacet
  facet normal 0.316655 0.132383 0.939257
    outer loop
      vertex -83.290001 -55.313999 2.634000
      vertex -83.938004 -53.764000 2.634000
      vertex -84.877998 -54.311001 3.028000
    endloop
  endfacet
  facet normal -0.443300 -0.577693 0.685388
    outer loop
      vertex -42.291000 -60.102001 4.501000
      vertex -43.596001 -60.096001 3.662000
      vertex -42.688999 -60.792000 3.662000
    endloop
  endfacet
  facet normal -0.437570 -0.335293 0.834333
    outer loop
      vertex -43.596001 -60.096001 3.662000
      vertex -44.291000 -59.188999 3.662000
      vertex -45.129002 -59.673000 3.028000
    endloop
  endfacet
  facet normal 0.102249 0.042747 0.993840
    outer loop
      vertex -83.938004 -53.764000 2.634000
      vertex -83.290001 -55.313999 2.634000
      vertex -82.446999 -54.215000 2.500000
    endloop
  endfacet
  facet normal 0.113946 0.082544 0.990052
    outer loop
      vertex -82.446999 -54.215000 2.500000
      vertex -84.654999 -51.167000 2.500000
      vertex -83.938004 -53.764000 2.634000
    endloop
  endfacet
  facet normal -0.546637 -0.073883 0.834104
    outer loop
      vertex -93.877998 0.985000 3.662000
      vertex -94.845001 0.982000 3.028000
      vertex -93.724998 -0.147000 3.662000
    endloop
  endfacet
  facet normal 0.103004 0.079597 0.991491
    outer loop
      vertex -83.938004 -53.764000 2.634000
      vertex -84.654999 -51.167000 2.500000
      vertex -84.964996 -52.435001 2.634000
    endloop
  endfacet
  facet normal -0.437599 -0.335613 0.834189
    outer loop
      vertex -43.596001 -60.096001 3.662000
      vertex -45.129002 -59.673000 3.028000
      vertex -44.279999 -60.779999 3.028000
    endloop
  endfacet
  facet normal -0.278723 -0.672678 0.685433
    outer loop
      vertex -42.291000 -60.102001 4.501000
      vertex -42.688999 -60.792000 3.662000
      vertex -41.426998 -60.459999 4.501000
    endloop
  endfacet
  facet normal -0.923642 -0.383255 -0.000000
    outer loop
      vertex -35.268002 15.000000 10.500000
      vertex -35.268002 15.000000 3.500000
      vertex -35.068001 14.518000 3.500000
    endloop
  endfacet
  facet normal 0.991491 0.130173 0.000000
    outer loop
      vertex -90.499001 1.000000 0.000000
      vertex -90.464996 0.741000 5.500000
      vertex -90.464996 0.741000 0.000000
    endloop
  endfacet
  facet normal -0.278500 -0.672987 0.685220
    outer loop
      vertex -41.426998 -60.459999 4.501000
      vertex -42.688999 -60.792000 3.662000
      vertex -41.632999 -61.229000 3.662000
    endloop
  endfacet
  facet normal -0.793979 -0.607946 -0.000000
    outer loop
      vertex -35.584999 15.414000 3.500000
      vertex -35.268002 15.000000 3.500000
      vertex -35.268002 15.000000 10.500000
    endloop
  endfacet
  facet normal 0.991491 -0.130173 0.000000
    outer loop
      vertex -90.464996 1.259000 0.000000
      vertex -90.464996 1.259000 5.500000
      vertex -90.499001 1.000000 0.000000
    endloop
  endfacet
  facet normal 0.923645 -0.383249 -0.000000
    outer loop
      vertex -90.364998 1.500000 0.000000
      vertex -90.464996 1.259000 5.500000
      vertex -90.464996 1.259000 0.000000
    endloop
  endfacet
  facet normal 0.793057 -0.609147 0.000000
    outer loop
      vertex -90.206001 1.707000 0.000000
      vertex -90.206001 1.707000 5.500000
      vertex -90.364998 1.500000 0.000000
    endloop
  endfacet
  facet normal -0.335721 -0.437499 0.834198
    outer loop
      vertex -43.596001 -60.096001 3.662000
      vertex -44.279999 -60.779999 3.028000
      vertex -42.688999 -60.792000 3.662000
    endloop
  endfacet
  facet normal -0.915817 -0.380008 0.129895
    outer loop
      vertex -35.101002 14.509000 3.241000
      vertex -35.068001 14.518000 3.500000
      vertex -35.268002 15.000000 3.500000
    endloop
  endfacet
  facet normal 0.508427 0.212525 0.834467
    outer loop
      vertex -84.877998 -54.311001 3.028000
      vertex -85.714996 -54.798000 3.662000
      vertex -85.274002 -55.853001 3.662000
    endloop
  endfacet
  facet normal -0.095038 -0.722121 0.685208
    outer loop
      vertex -41.426998 -60.459999 4.501000
      vertex -41.632999 -61.229000 3.662000
      vertex -40.500000 -60.582001 4.501000
    endloop
  endfacet
  facet normal -0.787473 -0.602965 0.127748
    outer loop
      vertex -35.297001 14.983000 3.241000
      vertex -35.268002 15.000000 3.500000
      vertex -35.584999 15.414000 3.500000
    endloop
  endfacet
  facet normal -0.916570 -0.379002 0.127502
    outer loop
      vertex -35.101002 14.509000 3.241000
      vertex -35.268002 15.000000 3.500000
      vertex -35.297001 14.983000 3.241000
    endloop
  endfacet
  facet normal 0.793057 0.609147 0.000000
    outer loop
      vertex -90.364998 0.500000 5.500000
      vertex -90.206001 0.293000 0.000000
      vertex -90.364998 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.923645 0.383249 0.000000
    outer loop
      vertex -90.364998 0.500000 5.500000
      vertex -90.364998 0.500000 0.000000
      vertex -90.464996 0.741000 0.000000
    endloop
  endfacet
  facet normal 0.508601 0.212445 0.834381
    outer loop
      vertex -85.274002 -55.853001 3.662000
      vertex -84.339996 -55.598999 3.028000
      vertex -84.877998 -54.311001 3.028000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 0.000000
    outer loop
      vertex -35.068001 14.518000 3.500000
      vertex -35.000000 14.000000 10.500000
      vertex -35.068001 14.518000 10.500000
    endloop
  endfacet
  facet normal -0.923642 -0.383255 -0.000000
    outer loop
      vertex -35.068001 14.518000 10.500000
      vertex -35.268002 15.000000 10.500000
      vertex -35.068001 14.518000 3.500000
    endloop
  endfacet
  facet normal 0.381896 0.924205 -0.000000
    outer loop
      vertex -41.000000 -57.866001 0.000000
      vertex -41.000000 -57.866001 5.500000
      vertex -40.757999 -57.966000 5.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 84.785255 2.556923
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 85.000000 2.520288
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 84.785255 2.556923
      vertex 82.998001 84.467354 2.634000
    endloop
  endfacet
  facet normal 0.609155 0.793051 -0.000000
    outer loop
      vertex -41.207001 -57.707001 0.000000
      vertex -41.000000 -57.866001 5.500000
      vertex -41.000000 -57.866001 0.000000
    endloop
  endfacet
  facet normal 0.793051 0.609155 0.000000
    outer loop
      vertex -41.366001 -57.500000 5.500000
      vertex -41.207001 -57.707001 0.000000
      vertex -41.366001 -57.500000 0.000000
    endloop
  endfacet
  facet normal 0.563202 0.734332 0.378893
    outer loop
      vertex 82.509003 84.509003 3.000000
      vertex 82.067001 84.848000 3.000000
      vertex 82.016998 84.762001 3.241000
    endloop
  endfacet
  facet normal 0.563673 0.732442 0.381839
    outer loop
      vertex 82.016998 84.762001 3.241000
      vertex 82.438004 84.438004 3.241000
      vertex 82.509003 84.509003 3.000000
    endloop
  endfacet
  facet normal 0.096092 -0.434392 0.895584
    outer loop
      vertex -80.338997 15.405000 2.534000
      vertex -80.611000 15.551000 2.634000
      vertex -80.999001 15.259000 2.534000
    endloop
  endfacet
  facet normal 0.224014 0.263339 0.938334
    outer loop
      vertex -36.209000 -52.673000 2.727000
      vertex -37.283001 -51.428001 2.634000
      vertex -37.826000 -52.369999 3.028000
    endloop
  endfacet
  facet normal 0.228286 0.297308 0.927089
    outer loop
      vertex -36.719002 -53.220001 3.028000
      vertex -36.209000 -52.673000 2.727000
      vertex -37.826000 -52.369999 3.028000
    endloop
  endfacet
  facet normal 0.213182 -0.163662 0.963207
    outer loop
      vertex -79.067001 16.482000 2.500000
      vertex -79.767998 15.769000 2.534000
      vertex -79.999001 15.268000 2.500000
    endloop
  endfacet
  facet normal 0.484852 0.632175 0.604379
    outer loop
      vertex 82.621002 84.621002 2.793000
      vertex 82.067001 84.848000 3.000000
      vertex 82.509003 84.509003 3.000000
    endloop
  endfacet
  facet normal 0.060877 -0.095497 0.993566
    outer loop
      vertex -79.999001 15.268000 2.500000
      vertex -79.767998 15.769000 2.534000
      vertex -80.338997 15.405000 2.534000
    endloop
  endfacet
  facet normal -0.787023 -0.603320 0.128839
    outer loop
      vertex -35.297001 14.983000 3.241000
      vertex -35.584999 15.414000 3.500000
      vertex -35.609001 15.390000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -79.999001 15.268000 2.500000
      vertex -80.999001 15.000000 2.500000
      vertex -82.903000 4.617000 2.500000
    endloop
  endfacet
  facet normal 0.733394 0.562483 0.381768
    outer loop
      vertex 82.848000 84.067001 3.000000
      vertex 82.509003 84.509003 3.000000
      vertex 82.438004 84.438004 3.241000
    endloop
  endfacet
  facet normal 0.131288 0.317177 0.939235
    outer loop
      vertex -37.283001 -51.428001 2.634000
      vertex -38.834000 -50.785999 2.634000
      vertex -39.116001 -51.835999 3.028000
    endloop
  endfacet
  facet normal -0.854173 -0.353201 0.381624
    outer loop
      vertex -35.383999 14.933000 3.000000
      vertex -35.101002 14.509000 3.241000
      vertex -35.297001 14.983000 3.241000
    endloop
  endfacet
  facet normal 0.039477 -0.147301 0.988304
    outer loop
      vertex -79.999001 15.268000 2.500000
      vertex -80.338997 15.405000 2.534000
      vertex -80.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal -0.854646 -0.355153 0.378744
    outer loop
      vertex -35.101002 14.509000 3.241000
      vertex -35.383999 14.933000 3.000000
      vertex -35.196999 14.483000 3.000000
    endloop
  endfacet
  facet normal 0.028780 -0.130103 0.991083
    outer loop
      vertex -80.338997 15.405000 2.534000
      vertex -80.999001 15.259000 2.534000
      vertex -80.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -79.067001 16.482000 2.500000
      vertex -79.999001 15.268000 2.500000
      vertex -50.831001 16.240999 2.500000
    endloop
  endfacet
  facet normal 0.484833 0.630949 0.605673
    outer loop
      vertex 82.621002 84.621002 2.793000
      vertex 82.146004 84.986000 2.793000
      vertex 82.067001 84.848000 3.000000
    endloop
  endfacet
  facet normal 0.335760 0.437276 0.834299
    outer loop
      vertex -38.310001 -53.208000 3.662000
      vertex -36.719002 -53.220001 3.028000
      vertex -37.826000 -52.369999 3.028000
    endloop
  endfacet
  facet normal -0.353080 -0.854222 0.381628
    outer loop
      vertex -36.016998 15.703000 3.241000
      vertex -36.516998 15.802000 3.000000
      vertex -36.067001 15.616000 3.000000
    endloop
  endfacet
  facet normal 0.353629 0.855344 0.378593
    outer loop
      vertex 81.526001 84.964996 3.241000
      vertex 82.016998 84.762001 3.241000
      vertex 82.067001 84.848000 3.000000
    endloop
  endfacet
  facet normal -0.353164 -0.854085 0.381857
    outer loop
      vertex -36.516998 15.802000 3.000000
      vertex -36.016998 15.703000 3.241000
      vertex -36.491001 15.899000 3.241000
    endloop
  endfacet
  facet normal -0.562645 -0.733411 0.381496
    outer loop
      vertex -36.067001 15.616000 3.000000
      vertex -35.609001 15.390000 3.241000
      vertex -36.016998 15.703000 3.241000
    endloop
  endfacet
  facet normal 0.341998 0.716396 0.608124
    outer loop
      vertex 82.146004 84.986000 2.793000
      vertex 82.057999 85.000000 2.826000
      vertex 82.067001 84.848000 3.000000
    endloop
  endfacet
  facet normal 0.500330 0.075860 -0.862505
    outer loop
      vertex -94.999001 0.000000 2.866047
      vertex -95.059998 -2.236000 2.634000
      vertex -94.999001 1.000000 2.954000
    endloop
  endfacet
  facet normal 0.370487 0.181899 0.910852
    outer loop
      vertex 82.146004 84.986000 2.793000
      vertex 82.621002 85.000000 2.597000
      vertex 82.057999 85.000000 2.826000
    endloop
  endfacet
  facet normal 0.015967 0.120918 0.992534
    outer loop
      vertex -38.834000 -50.785999 2.634000
      vertex -38.667999 -49.708000 2.500000
      vertex -40.500000 -50.566002 2.634000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 0.000000 2.866047
      vertex -94.999001 1.000000 2.954000
      vertex -94.999001 6.220000 2.500000
    endloop
  endfacet
  facet normal -1.000000 -0.000000 -0.000000
    outer loop
      vertex -94.999001 6.220000 2.500000
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 0.000000 2.866047
    endloop
  endfacet
  facet normal -0.000000 -0.923644 0.383253
    outer loop
      vertex -92.999001 15.866000 3.000000
      vertex -80.999001 15.966000 3.241000
      vertex -92.999001 15.966000 3.241000
    endloop
  endfacet
  facet normal 0.000000 -0.923644 0.383253
    outer loop
      vertex -92.999001 15.866000 3.000000
      vertex -80.999001 15.866000 3.000000
      vertex -80.999001 15.966000 3.241000
    endloop
  endfacet
  facet normal -0.938612 0.212727 0.271577
    outer loop
      vertex -94.064003 5.534000 2.634000
      vertex -94.999001 1.000000 2.954000
      vertex -94.667999 2.366000 3.028000
    endloop
  endfacet
  facet normal -0.546724 0.069921 0.834389
    outer loop
      vertex -94.845001 0.982000 3.028000
      vertex -93.732002 2.119000 3.662000
      vertex -94.667999 2.366000 3.028000
    endloop
  endfacet
  facet normal 0.210850 0.509357 0.834325
    outer loop
      vertex -39.366001 -52.771000 3.662000
      vertex -37.826000 -52.369999 3.028000
      vertex -39.116001 -51.835999 3.028000
    endloop
  endfacet
  facet normal -0.547087 0.070434 0.834107
    outer loop
      vertex -93.732002 2.119000 3.662000
      vertex -94.845001 0.982000 3.028000
      vertex -93.877998 0.985000 3.662000
    endloop
  endfacet
  facet normal 0.000000 -0.130157 0.991493
    outer loop
      vertex -80.999001 15.000000 2.500000
      vertex -80.999001 15.259000 2.534000
      vertex -92.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal -0.427271 0.054644 0.902471
    outer loop
      vertex -94.667999 2.366000 3.028000
      vertex -94.999001 1.000000 2.954000
      vertex -94.845001 0.982000 3.028000
    endloop
  endfacet
  facet normal -0.000000 -1.000000 -0.000000
    outer loop
      vertex -80.999001 16.000000 10.500000
      vertex -92.999001 16.000000 10.500000
      vertex -80.999001 16.000000 3.500000
    endloop
  endfacet
  facet normal -0.546357 -0.073481 0.834323
    outer loop
      vertex -93.724998 -0.147000 3.662000
      vertex -94.845001 0.982000 3.028000
      vertex -94.658997 -0.401000 3.028000
    endloop
  endfacet
  facet normal 0.044764 0.340406 0.939212
    outer loop
      vertex -40.500000 -51.653999 3.028000
      vertex -39.116001 -51.835999 3.028000
      vertex -38.834000 -50.785999 2.634000
    endloop
  endfacet
  facet normal -0.509821 0.209137 0.834473
    outer loop
      vertex -94.138000 3.658000 3.028000
      vertex -94.667999 2.366000 3.028000
      vertex -93.297997 3.176000 3.662000
    endloop
  endfacet
  facet normal -0.210816 0.509431 0.834288
    outer loop
      vertex -41.632999 5.229000 3.662000
      vertex -43.173000 5.630000 3.028000
      vertex -42.688999 4.792000 3.662000
    endloop
  endfacet
  facet normal 0.044917 0.340151 0.939297
    outer loop
      vertex -40.500000 -50.566002 2.634000
      vertex -40.500000 -51.653999 3.028000
      vertex -38.834000 -50.785999 2.634000
    endloop
  endfacet
  facet normal -0.483091 0.198172 0.852849
    outer loop
      vertex -94.064003 5.534000 2.634000
      vertex -94.667999 2.366000 3.028000
      vertex -94.138000 3.658000 3.028000
    endloop
  endfacet
  facet normal -0.078958 0.086376 0.993129
    outer loop
      vertex -94.999001 6.220000 2.500000
      vertex -94.999001 1.000000 2.954000
      vertex -94.064003 5.534000 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -88.056000 8.444000 2.500000
      vertex -80.999001 15.000000 2.500000
      vertex -92.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal -0.437946 -0.058901 0.897069
    outer loop
      vertex -94.845001 0.982000 3.028000
      vertex -94.999001 1.000000 2.954000
      vertex -94.658997 -0.401000 3.028000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 -0.000000
    outer loop
      vertex 25.000000 -84.000000 10.500000
      vertex 24.482000 -83.931999 10.500000
      vertex 24.482000 -83.931999 0.000000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 -0.000000
    outer loop
      vertex 24.482000 -83.931999 0.000000
      vertex 25.000000 -84.000000 0.000000
      vertex 25.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal -0.383249 -0.923645 0.000000
    outer loop
      vertex 24.482000 -83.931999 0.000000
      vertex 24.482000 -83.931999 10.500000
      vertex 24.000000 -83.732002 10.500000
    endloop
  endfacet
  facet normal -0.383249 -0.923645 0.000000
    outer loop
      vertex 24.000000 -83.732002 0.000000
      vertex 24.482000 -83.931999 0.000000
      vertex 24.000000 -83.732002 10.500000
    endloop
  endfacet
  facet normal 0.383249 -0.923645 0.000000
    outer loop
      vertex 23.518000 -83.931999 10.500000
      vertex 23.518000 -83.931999 0.000000
      vertex 24.000000 -83.732002 0.000000
    endloop
  endfacet
  facet normal 0.383249 -0.923645 0.000000
    outer loop
      vertex 24.000000 -83.732002 0.000000
      vertex 24.000000 -83.732002 10.500000
      vertex 23.518000 -83.931999 10.500000
    endloop
  endfacet
  facet normal -0.000000 -0.383255 0.923643
    outer loop
      vertex -80.999001 15.259000 2.534000
      vertex -80.999001 15.500000 2.634000
      vertex -92.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal 0.130159 -0.991493 0.000000
    outer loop
      vertex 23.000000 -84.000000 0.000000
      vertex 23.518000 -83.931999 10.500000
      vertex 23.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal 0.130159 -0.991493 0.000000
    outer loop
      vertex 23.518000 -83.931999 0.000000
      vertex 23.518000 -83.931999 10.500000
      vertex 23.000000 -84.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 23.000000 -82.000000 10.500000
      vertex 23.000000 -82.000000 2.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.210850 0.509357 0.834324
    outer loop
      vertex -41.882999 6.164000 3.028000
      vertex -43.173000 5.630000 3.028000
      vertex -41.632999 5.229000 3.662000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex 23.000000 -82.000000 10.500000
      vertex 23.000000 83.000000 10.500000
      vertex 23.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 0.000000
    outer loop
      vertex -93.999001 16.268000 3.500000
      vertex -93.999001 16.268000 10.500000
      vertex -94.413002 16.586000 10.500000
    endloop
  endfacet
  facet normal -0.383251 -0.923644 0.000000
    outer loop
      vertex -93.516998 16.068001 10.500000
      vertex -93.999001 16.268000 10.500000
      vertex -93.999001 16.268000 3.500000
    endloop
  endfacet
  facet normal -0.383251 -0.923644 0.000000
    outer loop
      vertex -93.999001 16.268000 3.500000
      vertex -93.516998 16.068001 3.500000
      vertex -93.516998 16.068001 10.500000
    endloop
  endfacet
  facet normal 0.210816 0.509431 0.834288
    outer loop
      vertex -39.366001 -52.771000 3.662000
      vertex -38.310001 -53.208000 3.662000
      vertex -37.826000 -52.369999 3.028000
    endloop
  endfacet
  facet normal -0.443300 0.577692 0.685388
    outer loop
      vertex -43.596001 4.096000 3.662000
      vertex -42.291000 4.102000 4.501000
      vertex -42.688999 4.792000 3.662000
    endloop
  endfacet
  facet normal -0.335721 0.437499 0.834198
    outer loop
      vertex -42.688999 4.792000 3.662000
      vertex -44.279999 4.780000 3.028000
      vertex -43.596001 4.096000 3.662000
    endloop
  endfacet
  facet normal -0.604663 -0.785686 0.130687
    outer loop
      vertex -93.999001 16.268000 3.500000
      vertex -94.436996 16.562000 3.241000
      vertex -94.015999 16.238001 3.241000
    endloop
  endfacet
  facet normal -0.335759 0.437276 0.834299
    outer loop
      vertex -43.173000 5.630000 3.028000
      vertex -44.279999 4.780000 3.028000
      vertex -42.688999 4.792000 3.662000
    endloop
  endfacet
  facet normal 0.071864 0.546483 0.834381
    outer loop
      vertex -40.500000 -52.622002 3.662000
      vertex -39.116001 -51.835999 3.028000
      vertex -40.500000 -51.653999 3.028000
    endloop
  endfacet
  facet normal -0.379500 -0.916026 0.129908
    outer loop
      vertex -93.526001 16.035000 3.241000
      vertex -93.516998 16.068001 3.500000
      vertex -94.015999 16.238001 3.241000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 0.000000
    outer loop
      vertex -93.516998 16.068001 3.500000
      vertex -92.999001 16.000000 3.500000
      vertex -92.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 0.000000
    outer loop
      vertex -93.516998 16.068001 3.500000
      vertex -92.999001 16.000000 10.500000
      vertex -93.516998 16.068001 10.500000
    endloop
  endfacet
  facet normal 0.071812 0.546546 0.834344
    outer loop
      vertex -39.116001 -51.835999 3.028000
      vertex -40.500000 -52.622002 3.662000
      vertex -39.366001 -52.771000 3.662000
    endloop
  endfacet
  facet normal 0.372843 0.485208 0.790925
    outer loop
      vertex 82.766998 84.767998 2.634000
      vertex 82.146004 84.986000 2.793000
      vertex 82.621002 84.621002 2.793000
    endloop
  endfacet
  facet normal 0.736473 0.304973 0.603821
    outer loop
      vertex 82.848000 84.067001 3.000000
      vertex 82.998001 83.872734 2.915164
      vertex 82.998001 84.114609 2.793000
    endloop
  endfacet
  facet normal -0.379948 -0.915685 0.130996
    outer loop
      vertex -93.999001 16.268000 3.500000
      vertex -94.015999 16.238001 3.241000
      vertex -93.516998 16.068001 3.500000
    endloop
  endfacet
  facet normal 0.924998 0.379973 0.000000
    outer loop
      vertex -41.465000 -57.258999 0.000000
      vertex -41.366001 -57.500000 5.500000
      vertex -41.366001 -57.500000 0.000000
    endloop
  endfacet
  facet normal -0.129071 -0.983200 0.129070
    outer loop
      vertex -92.999001 15.966000 3.241000
      vertex -92.999001 16.000000 3.500000
      vertex -93.516998 16.068001 3.500000
    endloop
  endfacet
  facet normal 0.632384 0.484605 0.604358
    outer loop
      vertex 82.985001 84.146004 2.793000
      vertex 82.621002 84.621002 2.793000
      vertex 82.509003 84.509003 3.000000
    endloop
  endfacet
  facet normal -0.304311 -0.736233 0.604446
    outer loop
      vertex -36.557999 15.649000 2.793000
      vertex -36.067001 15.616000 3.000000
      vertex -36.516998 15.802000 3.000000
    endloop
  endfacet
  facet normal 0.632532 0.485126 0.603785
    outer loop
      vertex 82.985001 84.146004 2.793000
      vertex 82.509003 84.509003 3.000000
      vertex 82.848000 84.067001 3.000000
    endloop
  endfacet
  facet normal -0.304904 -0.734619 0.606110
    outer loop
      vertex -36.146000 15.478000 2.793000
      vertex -36.067001 15.616000 3.000000
      vertex -36.557999 15.649000 2.793000
    endloop
  endfacet
  facet normal 0.546266 0.073861 0.834349
    outer loop
      vertex -84.339996 -55.598999 3.028000
      vertex -85.274002 -55.853001 3.662000
      vertex -84.153000 -56.981998 3.028000
    endloop
  endfacet
  facet normal 0.733397 0.562667 0.381490
    outer loop
      vertex 82.761002 84.016998 3.241000
      vertex 82.848000 84.067001 3.000000
      vertex 82.438004 84.438004 3.241000
    endloop
  endfacet
  facet normal -0.234803 -0.565720 0.790461
    outer loop
      vertex -36.250000 15.299000 2.634000
      vertex -36.146000 15.478000 2.793000
      vertex -36.557999 15.649000 2.793000
    endloop
  endfacet
  facet normal 0.347314 0.356862 0.867192
    outer loop
      vertex 82.621002 85.000000 2.597000
      vertex 82.146004 84.986000 2.793000
      vertex 82.766998 84.767998 2.634000
    endloop
  endfacet
  facet normal -0.235144 -0.565912 0.790222
    outer loop
      vertex -36.250000 15.299000 2.634000
      vertex -36.557999 15.649000 2.793000
      vertex -36.611000 15.449000 2.634000
    endloop
  endfacet
  facet normal 0.484831 0.371533 0.791772
    outer loop
      vertex 82.621002 84.621002 2.793000
      vertex 82.985001 84.146004 2.793000
      vertex 82.998001 84.153511 2.781517
    endloop
  endfacet
  facet normal -0.113704 -0.047108 0.992397
    outer loop
      vertex -46.714001 -58.665001 2.634000
      vertex -47.028000 -60.730000 2.500000
      vertex -46.070999 -60.216999 2.634000
    endloop
  endfacet
  facet normal 0.546245 0.073830 0.834366
    outer loop
      vertex -84.153000 -56.981998 3.028000
      vertex -85.274002 -55.853001 3.662000
      vertex -85.121002 -56.985001 3.662000
    endloop
  endfacet
  facet normal 0.485491 0.373015 0.790670
    outer loop
      vertex 82.621002 84.621002 2.793000
      vertex 82.998001 84.363892 2.682811
      vertex 82.998001 84.467354 2.634000
    endloop
  endfacet
  facet normal 0.214075 0.283780 0.934687
    outer loop
      vertex 82.766998 84.767998 2.634000
      vertex 82.931000 85.000000 2.526000
      vertex 82.621002 85.000000 2.597000
    endloop
  endfacet
  facet normal 0.316573 0.132234 0.939306
    outer loop
      vertex -84.339996 -55.598999 3.028000
      vertex -83.290001 -55.313999 2.634000
      vertex -84.877998 -54.311001 3.028000
    endloop
  endfacet
  facet normal 0.293188 0.225271 0.929136
    outer loop
      vertex 82.998001 84.785255 2.556923
      vertex 82.931000 85.000000 2.526000
      vertex 82.766998 84.767998 2.634000
    endloop
  endfacet
  facet normal -0.317015 -0.131341 0.939282
    outer loop
      vertex -46.070999 -60.216999 2.634000
      vertex -45.129002 -59.673000 3.028000
      vertex -46.714001 -58.665001 2.634000
    endloop
  endfacet
  facet normal -0.067352 0.087762 0.993862
    outer loop
      vertex -43.716000 6.572000 2.634000
      vertex -45.162998 6.979000 2.500000
      vertex -45.049000 5.549000 2.634000
    endloop
  endfacet
  facet normal -0.121403 -0.916211 0.381862
    outer loop
      vertex -37.000000 15.866000 3.000000
      vertex -36.516998 15.802000 3.000000
      vertex -36.491001 15.899000 3.241000
    endloop
  endfacet
  facet normal 0.340261 0.046007 0.939205
    outer loop
      vertex -83.066002 -56.978001 2.634000
      vertex -84.339996 -55.598999 3.028000
      vertex -84.153000 -56.981998 3.028000
    endloop
  endfacet
  facet normal -0.103654 -0.789921 0.604385
    outer loop
      vertex -37.000000 15.707000 2.793000
      vertex -36.557999 15.649000 2.793000
      vertex -36.516998 15.802000 3.000000
    endloop
  endfacet
  facet normal -0.102178 0.084732 0.991151
    outer loop
      vertex -45.049000 5.549000 2.634000
      vertex -45.162998 6.979000 2.500000
      vertex -47.028000 4.730000 2.500000
    endloop
  endfacet
  facet normal 0.340037 0.045774 0.939297
    outer loop
      vertex -83.066002 -56.978001 2.634000
      vertex -83.290001 -55.313999 2.634000
      vertex -84.339996 -55.598999 3.028000
    endloop
  endfacet
  facet normal -0.272275 0.208818 0.939288
    outer loop
      vertex -46.070999 4.217000 2.634000
      vertex -45.129002 3.673000 3.028000
      vertex -44.279999 4.780000 3.028000
    endloop
  endfacet
  facet normal -0.272302 0.208928 0.939255
    outer loop
      vertex -45.049000 5.549000 2.634000
      vertex -46.070999 4.217000 2.634000
      vertex -44.279999 4.780000 3.028000
    endloop
  endfacet
  facet normal -0.098448 0.075536 0.992271
    outer loop
      vertex -45.049000 5.549000 2.634000
      vertex -47.028000 4.730000 2.500000
      vertex -46.070999 4.217000 2.634000
    endloop
  endfacet
  facet normal -0.079690 -0.607301 0.790465
    outer loop
      vertex -36.557999 15.649000 2.793000
      vertex -37.000000 15.707000 2.793000
      vertex -36.611000 15.449000 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -47.028000 4.730000 2.500000
      vertex -45.162998 6.979000 2.500000
      vertex -48.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -45.162998 6.979000 2.500000
      vertex -43.472000 7.976000 2.500000
      vertex -48.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal -0.733529 -0.562312 0.381760
    outer loop
      vertex -35.680000 15.319000 3.000000
      vertex -35.297001 14.983000 3.241000
      vertex -35.609001 15.390000 3.241000
    endloop
  endfacet
  facet normal 0.122328 0.016467 0.992353
    outer loop
      vertex -83.066002 -56.978001 2.634000
      vertex -81.975998 -57.000000 2.500000
      vertex -83.290001 -55.313999 2.634000
    endloop
  endfacet
  facet normal -0.733525 -0.562497 0.381495
    outer loop
      vertex -35.383999 14.933000 3.000000
      vertex -35.297001 14.983000 3.241000
      vertex -35.680000 15.319000 3.000000
    endloop
  endfacet
  facet normal -0.577857 0.442789 0.685579
    outer loop
      vertex -44.291000 3.189000 3.662000
      vertex -43.032001 3.533000 4.501000
      vertex -43.596001 4.096000 3.662000
    endloop
  endfacet
  facet normal -0.577752 0.443825 0.684998
    outer loop
      vertex -43.602001 2.791000 4.501000
      vertex -43.032001 3.533000 4.501000
      vertex -44.291000 3.189000 3.662000
    endloop
  endfacet
  facet normal 0.129119 0.021837 0.991389
    outer loop
      vertex -82.446999 -54.215000 2.500000
      vertex -83.290001 -55.313999 2.634000
      vertex -81.975998 -57.000000 2.500000
    endloop
  endfacet
  facet normal -0.443399 0.577432 0.685543
    outer loop
      vertex -43.596001 4.096000 3.662000
      vertex -43.032001 3.533000 4.501000
      vertex -42.291000 4.102000 4.501000
    endloop
  endfacet
  facet normal -0.437599 0.335612 0.834189
    outer loop
      vertex -43.596001 4.096000 3.662000
      vertex -44.279999 4.780000 3.028000
      vertex -45.129002 3.673000 3.028000
    endloop
  endfacet
  facet normal -0.632320 -0.485436 0.603757
    outer loop
      vertex -35.521000 14.854000 2.793000
      vertex -35.383999 14.933000 3.000000
      vertex -35.792000 15.207000 2.793000
    endloop
  endfacet
  facet normal 0.276568 0.673573 0.685426
    outer loop
      vertex -88.584000 -53.536999 4.501000
      vertex -87.322998 -53.201000 3.662000
      vertex -88.379997 -52.766998 3.662000
    endloop
  endfacet
  facet normal 0.527257 -0.686640 0.500526
    outer loop
      vertex -37.966999 -1.533000 4.501000
      vertex -39.000000 -1.598000 5.500000
      vertex -38.708000 -2.102000 4.501000
    endloop
  endfacet
  facet normal -0.437570 0.335293 0.834332
    outer loop
      vertex -43.596001 4.096000 3.662000
      vertex -45.129002 3.673000 3.028000
      vertex -44.291000 3.189000 3.662000
    endloop
  endfacet
  facet normal 0.686733 -0.527544 0.500095
    outer loop
      vertex -38.377998 -1.121000 5.500000
      vertex -37.966999 -1.533000 4.501000
      vertex -37.396999 -0.791000 4.501000
    endloop
  endfacet
  facet normal 0.686747 -0.527498 0.500124
    outer loop
      vertex -38.377998 -1.121000 5.500000
      vertex -37.396999 -0.791000 4.501000
      vertex -37.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.334156 0.438306 0.834402
    outer loop
      vertex -87.322998 -53.201000 3.662000
      vertex -86.414001 -53.894001 3.662000
      vertex -85.732002 -53.207001 3.028000
    endloop
  endfacet
  facet normal -0.743355 0.173816 0.645919
    outer loop
      vertex -35.307999 -53.740002 3.290000
      vertex -35.203999 -53.703999 3.400000
      vertex -35.248001 -52.349998 2.985000
    endloop
  endfacet
  facet normal -0.484305 -0.632635 0.604335
    outer loop
      vertex -35.792000 15.207000 2.793000
      vertex -35.680000 15.319000 3.000000
      vertex -36.146000 15.478000 2.793000
    endloop
  endfacet
  facet normal -0.743710 0.224988 0.629505
    outer loop
      vertex -35.203999 -53.703999 3.400000
      vertex -35.307999 -53.740002 3.290000
      vertex -35.257999 -55.108002 3.838000
    endloop
  endfacet
  facet normal -0.672882 0.278808 0.685198
    outer loop
      vertex -44.729000 2.133000 3.662000
      vertex -43.959999 1.927000 4.501000
      vertex -43.602001 2.791000 4.501000
    endloop
  endfacet
  facet normal -0.562701 -0.733218 0.381784
    outer loop
      vertex -35.680000 15.319000 3.000000
      vertex -35.609001 15.390000 3.241000
      vertex -36.067001 15.616000 3.000000
    endloop
  endfacet
  facet normal 0.435958 0.337237 0.834393
    outer loop
      vertex -85.732002 -53.207001 3.028000
      vertex -86.414001 -53.894001 3.662000
      vertex -84.877998 -54.311001 3.028000
    endloop
  endfacet
  facet normal -0.672931 0.279113 0.685025
    outer loop
      vertex -44.729000 2.133000 3.662000
      vertex -43.602001 2.791000 4.501000
      vertex -44.291000 3.189000 3.662000
    endloop
  endfacet
  facet normal -0.484432 -0.631232 0.605699
    outer loop
      vertex -36.146000 15.478000 2.793000
      vertex -35.680000 15.319000 3.000000
      vertex -36.067001 15.616000 3.000000
    endloop
  endfacet
  facet normal 0.435945 0.337089 0.834460
    outer loop
      vertex -84.877998 -54.311001 3.028000
      vertex -86.414001 -53.894001 3.662000
      vertex -85.714996 -54.798000 3.662000
    endloop
  endfacet
  facet normal -0.632212 -0.484806 0.604376
    outer loop
      vertex -35.792000 15.207000 2.793000
      vertex -35.383999 14.933000 3.000000
      vertex -35.680000 15.319000 3.000000
    endloop
  endfacet
  facet normal -0.736051 -0.305871 0.603881
    outer loop
      vertex -35.521000 14.854000 2.793000
      vertex -35.196999 14.483000 3.000000
      vertex -35.383999 14.933000 3.000000
    endloop
  endfacet
  facet normal -0.734810 -0.303195 0.606734
    outer loop
      vertex -35.351002 14.442000 2.793000
      vertex -35.196999 14.483000 3.000000
      vertex -35.521000 14.854000 2.793000
    endloop
  endfacet
  facet normal 0.383253 -0.923643 0.000000
    outer loop
      vertex -89.758003 -56.034000 0.000000
      vertex -89.999001 -56.133999 5.500000
      vertex -89.999001 -56.133999 0.000000
    endloop
  endfacet
  facet normal -0.317185 -0.131648 0.939182
    outer loop
      vertex -45.129002 -59.673000 3.028000
      vertex -45.664001 -58.383999 3.028000
      vertex -46.714001 -58.665001 2.634000
    endloop
  endfacet
  facet normal -0.130158 -0.991493 0.000000
    outer loop
      vertex -89.239998 -56.034000 5.500000
      vertex -89.499001 -56.000000 5.500000
      vertex -89.499001 -56.000000 0.000000
    endloop
  endfacet
  facet normal -0.509162 -0.211327 0.834323
    outer loop
      vertex -44.291000 -59.188999 3.662000
      vertex -45.664001 -58.383999 3.028000
      vertex -45.129002 -59.673000 3.028000
    endloop
  endfacet
  facet normal -0.383253 -0.923643 -0.000000
    outer loop
      vertex -89.239998 -56.034000 5.500000
      vertex -89.239998 -56.034000 0.000000
      vertex -88.999001 -56.133999 0.000000
    endloop
  endfacet
  facet normal -0.722175 0.094972 0.685160
    outer loop
      vertex -44.082001 1.000000 4.501000
      vertex -44.729000 2.133000 3.662000
      vertex -44.877998 1.000000 3.662000
    endloop
  endfacet
  facet normal -0.722121 0.095038 0.685208
    outer loop
      vertex -44.729000 2.133000 3.662000
      vertex -44.082001 1.000000 4.501000
      vertex -43.959999 1.927000 4.501000
    endloop
  endfacet
  facet normal -0.923635 -0.383273 -0.000000
    outer loop
      vertex -88.532997 -56.741001 0.000000
      vertex -88.633003 -56.500000 5.500000
      vertex -88.633003 -56.500000 0.000000
    endloop
  endfacet
  facet normal -0.722175 -0.094972 0.685160
    outer loop
      vertex -44.729000 -0.133000 3.662000
      vertex -44.082001 1.000000 4.501000
      vertex -44.877998 1.000000 3.662000
    endloop
  endfacet
  facet normal 0.130158 -0.991493 0.000000
    outer loop
      vertex -89.499001 -56.000000 0.000000
      vertex -89.499001 -56.000000 5.500000
      vertex -89.758003 -56.034000 0.000000
    endloop
  endfacet
  facet normal -0.722121 -0.095038 0.685208
    outer loop
      vertex -43.959999 0.073000 4.501000
      vertex -44.082001 1.000000 4.501000
      vertex -44.729000 -0.133000 3.662000
    endloop
  endfacet
  facet normal -0.130158 -0.991493 0.000000
    outer loop
      vertex -89.499001 -56.000000 0.000000
      vertex -89.239998 -56.034000 0.000000
      vertex -89.239998 -56.034000 5.500000
    endloop
  endfacet
  facet normal -0.383253 -0.923643 0.000000
    outer loop
      vertex -88.999001 -56.133999 0.000000
      vertex -88.999001 -56.133999 5.500000
      vertex -89.239998 -56.034000 5.500000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 -0.000000
    outer loop
      vertex -88.999001 -56.133999 0.000000
      vertex -88.792000 -56.292999 0.000000
      vertex -88.792000 -56.292999 5.500000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 -0.000000
    outer loop
      vertex -88.792000 -56.292999 5.500000
      vertex -88.999001 -56.133999 5.500000
      vertex -88.999001 -56.133999 0.000000
    endloop
  endfacet
  facet normal -0.793058 -0.609146 0.000000
    outer loop
      vertex -88.633003 -56.500000 0.000000
      vertex -88.633003 -56.500000 5.500000
      vertex -88.792000 -56.292999 5.500000
    endloop
  endfacet
  facet normal -0.793058 -0.609146 -0.000000
    outer loop
      vertex -88.792000 -56.292999 5.500000
      vertex -88.792000 -56.292999 0.000000
      vertex -88.633003 -56.500000 0.000000
    endloop
  endfacet
  facet normal -0.991495 -0.130145 0.000000
    outer loop
      vertex -88.499001 -57.000000 0.000000
      vertex -88.499001 -57.000000 5.500000
      vertex -88.532997 -56.741001 0.000000
    endloop
  endfacet
  facet normal 0.609154 0.793052 0.000000
    outer loop
      vertex -41.000000 0.134000 5.500000
      vertex -41.207001 0.293000 0.000000
      vertex -41.207001 0.293000 5.500000
    endloop
  endfacet
  facet normal -0.991495 0.130145 -0.000000
    outer loop
      vertex -88.499001 -57.000000 0.000000
      vertex -88.532997 -57.258999 0.000000
      vertex -88.532997 -57.258999 5.500000
    endloop
  endfacet
  facet normal -0.991495 0.130145 -0.000000
    outer loop
      vertex -88.532997 -57.258999 5.500000
      vertex -88.499001 -57.000000 5.500000
      vertex -88.499001 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.000000 -1.598000 5.500000
      vertex -39.792000 0.293000 5.500000
      vertex -40.000000 0.134000 5.500000
    endloop
  endfacet
  facet normal 0.793050 0.609156 0.000000
    outer loop
      vertex -41.366001 0.500000 5.500000
      vertex -41.207001 0.293000 0.000000
      vertex -41.366001 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.924997 0.379974 0.000000
    outer loop
      vertex -41.366001 0.500000 5.500000
      vertex -41.366001 0.500000 0.000000
      vertex -41.465000 0.741000 0.000000
    endloop
  endfacet
  facet normal 0.990992 0.133917 -0.000000
    outer loop
      vertex -41.500000 1.000000 0.000000
      vertex -41.465000 0.741000 5.500000
      vertex -41.465000 0.741000 0.000000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -92.999001 16.000000 3.500000
      vertex -80.999001 16.000000 3.500000
      vertex -92.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.526948 -0.687133 0.500174
    outer loop
      vertex -37.966999 -1.533000 4.501000
      vertex -38.377998 -1.121000 5.500000
      vertex -39.000000 -1.598000 5.500000
    endloop
  endfacet
  facet normal -0.098448 -0.075536 0.992271
    outer loop
      vertex -47.028000 -60.730000 2.500000
      vertex -45.049000 -61.549000 2.634000
      vertex -46.070999 -60.216999 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 0.034000 5.500000
      vertex -39.723000 -1.898000 5.500000
      vertex -39.000000 -1.598000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -38.377998 -1.121000 5.500000
      vertex -37.901001 -0.500000 5.500000
      vertex -39.792000 0.293000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.792000 0.293000 5.500000
      vertex -39.000000 -1.598000 5.500000
      vertex -38.377998 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.381901 -0.924203 -0.000000
    outer loop
      vertex -41.000000 1.866000 5.500000
      vertex -40.757999 1.966000 0.000000
      vertex -40.757999 1.966000 5.500000
    endloop
  endfacet
  facet normal -0.128725 -0.983156 0.129745
    outer loop
      vertex -92.999001 15.966000 3.241000
      vertex -93.516998 16.068001 3.500000
      vertex -93.526001 16.035000 3.241000
    endloop
  endfacet
  facet normal 0.381901 0.924203 -0.000000
    outer loop
      vertex -41.000000 0.134000 0.000000
      vertex -41.000000 0.134000 5.500000
      vertex -40.757999 0.034000 5.500000
    endloop
  endfacet
  facet normal 0.609154 0.793052 0.000000
    outer loop
      vertex -41.207001 0.293000 0.000000
      vertex -41.000000 0.134000 5.500000
      vertex -41.000000 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.374123 0.334794 0.864838
    outer loop
      vertex -35.897999 -55.220001 3.533000
      vertex -35.386002 -55.148998 3.727000
      vertex -35.735001 -53.816002 3.060000
    endloop
  endfacet
  facet normal 0.000000 -0.991493 0.130159
    outer loop
      vertex -80.999001 16.000000 3.500000
      vertex -92.999001 16.000000 3.500000
      vertex -92.999001 15.966000 3.241000
    endloop
  endfacet
  facet normal 0.000000 -0.991493 0.130159
    outer loop
      vertex -92.999001 15.966000 3.241000
      vertex -80.999001 15.966000 3.241000
      vertex -80.999001 16.000000 3.500000
    endloop
  endfacet
  facet normal 0.924997 0.379974 -0.000000
    outer loop
      vertex -41.465000 0.741000 0.000000
      vertex -41.465000 0.741000 5.500000
      vertex -41.366001 0.500000 5.500000
    endloop
  endfacet
  facet normal 0.112868 -0.858540 0.500170
    outer loop
      vertex -40.500000 -2.582000 4.501000
      vertex -39.571999 -2.460000 4.501000
      vertex -40.500000 -2.000000 5.500000
    endloop
  endfacet
  facet normal -0.678813 0.251546 0.689882
    outer loop
      vertex -35.257999 -55.108002 3.838000
      vertex -35.307999 -53.740002 3.290000
      vertex -35.386002 -55.148998 3.727000
    endloop
  endfacet
  facet normal 0.990992 -0.133917 0.000000
    outer loop
      vertex -41.465000 1.259000 0.000000
      vertex -41.465000 1.259000 5.500000
      vertex -41.500000 1.000000 0.000000
    endloop
  endfacet
  facet normal 0.924997 -0.379974 -0.000000
    outer loop
      vertex -41.465000 1.259000 0.000000
      vertex -41.366001 1.500000 0.000000
      vertex -41.366001 1.500000 5.500000
    endloop
  endfacet
  facet normal 0.924997 -0.379974 -0.000000
    outer loop
      vertex -41.366001 1.500000 5.500000
      vertex -41.465000 1.259000 5.500000
      vertex -41.465000 1.259000 0.000000
    endloop
  endfacet
  facet normal 0.793050 -0.609156 0.000000
    outer loop
      vertex -41.207001 1.707000 0.000000
      vertex -41.207001 1.707000 5.500000
      vertex -41.366001 1.500000 5.500000
    endloop
  endfacet
  facet normal 0.793050 -0.609156 0.000000
    outer loop
      vertex -41.366001 1.500000 5.500000
      vertex -41.366001 1.500000 0.000000
      vertex -41.207001 1.707000 0.000000
    endloop
  endfacet
  facet normal 0.609154 -0.793052 -0.000000
    outer loop
      vertex -41.207001 1.707000 0.000000
      vertex -41.000000 1.866000 0.000000
      vertex -41.000000 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.609154 -0.793052 -0.000000
    outer loop
      vertex -41.000000 1.866000 5.500000
      vertex -41.207001 1.707000 5.500000
      vertex -41.207001 1.707000 0.000000
    endloop
  endfacet
  facet normal -0.493394 0.282464 0.822664
    outer loop
      vertex -35.386002 -55.148998 3.727000
      vertex -35.307999 -53.740002 3.290000
      vertex -35.735001 -53.816002 3.060000
    endloop
  endfacet
  facet normal 0.112715 -0.858621 0.500065
    outer loop
      vertex -40.500000 -2.000000 5.500000
      vertex -39.571999 -2.460000 4.501000
      vertex -39.723000 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.381901 -0.924203 -0.000000
    outer loop
      vertex -40.757999 1.966000 0.000000
      vertex -41.000000 1.866000 5.500000
      vertex -41.000000 1.866000 0.000000
    endloop
  endfacet
  facet normal -0.317015 0.131341 0.939282
    outer loop
      vertex -45.129002 3.673000 3.028000
      vertex -46.070999 4.217000 2.634000
      vertex -46.714001 2.665000 2.634000
    endloop
  endfacet
  facet normal 0.331476 -0.799986 0.500146
    outer loop
      vertex -39.723000 -1.898000 5.500000
      vertex -39.571999 -2.460000 4.501000
      vertex -38.708000 -2.102000 4.501000
    endloop
  endfacet
  facet normal 0.331814 -0.799672 0.500425
    outer loop
      vertex -38.708000 -2.102000 4.501000
      vertex -39.000000 -1.598000 5.500000
      vertex -39.723000 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.443559 -0.577641 0.685263
    outer loop
      vertex -38.708000 -2.102000 4.501000
      vertex -37.403999 -2.096000 3.662000
      vertex -37.966999 -1.533000 4.501000
    endloop
  endfacet
  facet normal -0.113704 0.047108 0.992397
    outer loop
      vertex -47.028000 4.730000 2.500000
      vertex -46.714001 2.665000 2.634000
      vertex -46.070999 4.217000 2.634000
    endloop
  endfacet
  facet normal -0.484813 -0.629592 0.607101
    outer loop
      vertex -94.620003 16.379000 2.793000
      vertex -94.146004 16.014000 2.793000
      vertex -94.066002 16.152000 3.000000
    endloop
  endfacet
  facet normal 0.074890 0.327357 0.941928
    outer loop
      vertex -36.070000 -55.220001 3.531000
      vertex -36.160999 -55.883999 3.769000
      vertex -35.980000 -55.888000 3.756000
    endloop
  endfacet
  facet normal -0.340442 0.044769 0.939199
    outer loop
      vertex -45.664001 2.384000 3.028000
      vertex -46.714001 2.665000 2.634000
      vertex -45.846001 1.000000 3.028000
    endloop
  endfacet
  facet normal -0.484854 -0.632173 0.604379
    outer loop
      vertex -94.508003 16.490999 3.000000
      vertex -94.620003 16.379000 2.793000
      vertex -94.066002 16.152000 3.000000
    endloop
  endfacet
  facet normal -0.340429 0.044777 0.939203
    outer loop
      vertex -46.932999 1.000000 2.634000
      vertex -45.846001 1.000000 3.028000
      vertex -46.714001 2.665000 2.634000
    endloop
  endfacet
  facet normal 0.424488 -0.204483 0.882041
    outer loop
      vertex -36.667999 -0.316000 3.961000
      vertex -36.141998 -0.255000 3.722000
      vertex -36.222000 0.433000 3.920000
    endloop
  endfacet
  facet normal 0.234789 0.291385 0.927345
    outer loop
      vertex -36.446999 -54.272999 3.290000
      vertex -36.209000 -52.673000 2.727000
      vertex -36.719002 -53.220001 3.028000
    endloop
  endfacet
  facet normal -0.079782 -0.607282 0.790471
    outer loop
      vertex -93.646004 15.585000 2.634000
      vertex -92.999001 15.500000 2.634000
      vertex -93.593002 15.785000 2.793000
    endloop
  endfacet
  facet normal -0.317186 0.131648 0.939182
    outer loop
      vertex -45.664001 2.384000 3.028000
      vertex -45.129002 3.673000 3.028000
      vertex -46.714001 2.665000 2.634000
    endloop
  endfacet
  facet normal -0.079735 -0.607216 0.790526
    outer loop
      vertex -93.593002 15.785000 2.793000
      vertex -92.999001 15.500000 2.634000
      vertex -92.999001 15.707000 2.793000
    endloop
  endfacet
  facet normal -0.328296 0.242768 0.912845
    outer loop
      vertex -35.735001 -53.816002 3.060000
      vertex -35.604000 -52.397999 2.730000
      vertex -35.733002 -52.407001 2.686000
    endloop
  endfacet
  facet normal -0.153466 0.040732 0.987314
    outer loop
      vertex -48.018002 1.000000 2.500000
      vertex -46.714001 2.665000 2.634000
      vertex -47.028000 4.730000 2.500000
    endloop
  endfacet
  facet normal -0.192166 0.252025 0.948449
    outer loop
      vertex -35.884998 -53.825001 3.032000
      vertex -35.735001 -53.816002 3.060000
      vertex -35.733002 -52.407001 2.686000
    endloop
  endfacet
  facet normal -0.192292 0.333281 0.923010
    outer loop
      vertex -35.884998 -53.825001 3.032000
      vertex -35.897999 -55.220001 3.533000
      vertex -35.735001 -53.816002 3.060000
    endloop
  endfacet
  facet normal -0.010943 0.338073 0.941056
    outer loop
      vertex -36.070000 -55.220001 3.531000
      vertex -35.897999 -55.220001 3.533000
      vertex -35.884998 -53.825001 3.032000
    endloop
  endfacet
  facet normal -0.122555 0.016120 0.992331
    outer loop
      vertex -46.714001 2.665000 2.634000
      vertex -48.018002 1.000000 2.500000
      vertex -46.932999 1.000000 2.634000
    endloop
  endfacet
  facet normal -0.493128 0.240148 0.836154
    outer loop
      vertex -35.307999 -53.740002 3.290000
      vertex -35.604000 -52.397999 2.730000
      vertex -35.735001 -53.816002 3.060000
    endloop
  endfacet
  facet normal 0.052573 -0.270533 0.961274
    outer loop
      vertex -36.222000 0.433000 3.920000
      vertex -36.141998 -0.255000 3.722000
      vertex -35.962002 -0.252000 3.713000
    endloop
  endfacet
  facet normal 0.293188 0.225274 0.929135
    outer loop
      vertex 82.998001 84.467354 2.634000
      vertex 82.998001 84.785255 2.556923
      vertex 82.766998 84.767998 2.634000
    endloop
  endfacet
  facet normal -0.234685 -0.566058 0.790253
    outer loop
      vertex -93.593002 15.785000 2.793000
      vertex -94.249001 15.835000 2.634000
      vertex -93.646004 15.585000 2.634000
    endloop
  endfacet
  facet normal 0.485494 0.373034 0.790658
    outer loop
      vertex 82.998001 84.467354 2.634000
      vertex 82.766998 84.767998 2.634000
      vertex 82.621002 84.621002 2.793000
    endloop
  endfacet
  facet normal -0.234635 -0.566610 0.789873
    outer loop
      vertex -93.593002 15.785000 2.793000
      vertex -94.146004 16.014000 2.793000
      vertex -94.249001 15.835000 2.634000
    endloop
  endfacet
  facet normal 0.083736 0.167576 0.982296
    outer loop
      vertex 82.998001 84.785255 2.556923
      vertex 82.998001 85.000000 2.520288
      vertex 82.931000 85.000000 2.526000
    endloop
  endfacet
  facet normal -0.266445 -0.228310 0.936420
    outer loop
      vertex -35.417000 -0.310000 3.890000
      vertex -35.455002 0.407000 4.054000
      vertex -36.035999 0.437000 3.896000
    endloop
  endfacet
  facet normal 0.991244 0.132042 0.000000
    outer loop
      vertex 82.998001 83.015015 3.500000
      vertex 82.931000 83.517998 3.500000
      vertex 82.931000 83.517998 10.500000
    endloop
  endfacet
  facet normal 0.991244 0.132042 0.000000
    outer loop
      vertex 82.931000 83.517998 10.500000
      vertex 82.998001 83.015015 10.500000
      vertex 82.998001 83.015015 3.500000
    endloop
  endfacet
  facet normal 0.129290 -0.241554 0.961736
    outer loop
      vertex -35.962002 -0.252000 3.713000
      vertex -36.035999 0.437000 3.896000
      vertex -36.222000 0.433000 3.920000
    endloop
  endfacet
  facet normal -0.272275 -0.208819 0.939288
    outer loop
      vertex -44.279999 -60.779999 3.028000
      vertex -45.129002 -59.673000 3.028000
      vertex -46.070999 -60.216999 2.634000
    endloop
  endfacet
  facet normal -0.303878 -0.733820 0.607591
    outer loop
      vertex -93.551003 15.939000 3.000000
      vertex -94.146004 16.014000 2.793000
      vertex -93.593002 15.785000 2.793000
    endloop
  endfacet
  facet normal -0.303736 -0.734384 0.606980
    outer loop
      vertex -94.146004 16.014000 2.793000
      vertex -93.551003 15.939000 3.000000
      vertex -94.066002 16.152000 3.000000
    endloop
  endfacet
  facet normal -0.354418 -0.855483 0.377540
    outer loop
      vertex -93.551003 15.939000 3.000000
      vertex -93.526001 16.035000 3.241000
      vertex -94.015999 16.238001 3.241000
    endloop
  endfacet
  facet normal -0.353743 -0.855292 0.378605
    outer loop
      vertex -94.066002 16.152000 3.000000
      vertex -93.551003 15.939000 3.000000
      vertex -94.015999 16.238001 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -47.028000 -60.730000 2.500000
      vertex -48.018002 -56.019001 2.500000
      vertex -81.975998 -57.000000 2.500000
    endloop
  endfacet
  facet normal -0.323329 -0.275198 0.905387
    outer loop
      vertex -36.035999 0.437000 3.896000
      vertex -35.962002 -0.252000 3.713000
      vertex -35.417000 -0.310000 3.890000
    endloop
  endfacet
  facet normal 0.982957 0.130938 0.129038
    outer loop
      vertex 82.998001 83.181046 3.331524
      vertex 82.931000 83.517998 3.500000
      vertex 82.998001 83.015015 3.500000
    endloop
  endfacet
  facet normal -0.272302 -0.208928 0.939255
    outer loop
      vertex -44.279999 -60.779999 3.028000
      vertex -46.070999 -60.216999 2.634000
      vertex -45.049000 -61.549000 2.634000
    endloop
  endfacet
  facet normal -0.209018 -0.272215 0.939261
    outer loop
      vertex -43.173000 -61.630001 3.028000
      vertex -44.279999 -60.779999 3.028000
      vertex -45.049000 -61.549000 2.634000
    endloop
  endfacet
  facet normal 0.982941 0.130810 0.129286
    outer loop
      vertex 82.931000 83.517998 3.500000
      vertex 82.998001 83.181046 3.331524
      vertex 82.998001 83.270515 3.241000
    endloop
  endfacet
  facet normal -0.104306 -0.788725 0.605833
    outer loop
      vertex -93.551003 15.939000 3.000000
      vertex -92.999001 15.707000 2.793000
      vertex -92.999001 15.866000 3.000000
    endloop
  endfacet
  facet normal 0.924323 0.381612 -0.000000
    outer loop
      vertex 82.931000 83.517998 3.500000
      vertex 82.732002 84.000000 3.500000
      vertex 82.732002 84.000000 10.500000
    endloop
  endfacet
  facet normal -0.209016 -0.272355 0.939221
    outer loop
      vertex -45.049000 -61.549000 2.634000
      vertex -43.716000 -62.571999 2.634000
      vertex -43.173000 -61.630001 3.028000
    endloop
  endfacet
  facet normal 0.924323 0.381612 -0.000000
    outer loop
      vertex 82.732002 84.000000 10.500000
      vertex 82.931000 83.517998 10.500000
      vertex 82.931000 83.517998 3.500000
    endloop
  endfacet
  facet normal -0.103454 -0.787847 0.607120
    outer loop
      vertex -93.593002 15.785000 2.793000
      vertex -92.999001 15.707000 2.793000
      vertex -93.551003 15.939000 3.000000
    endloop
  endfacet
  facet normal -0.102178 -0.084732 0.991151
    outer loop
      vertex -45.162998 -62.979000 2.500000
      vertex -45.049000 -61.549000 2.634000
      vertex -47.028000 -60.730000 2.500000
    endloop
  endfacet
  facet normal -0.651223 -0.190956 0.734469
    outer loop
      vertex -35.305000 0.385000 4.170000
      vertex -35.417000 -0.310000 3.890000
      vertex -35.278999 -0.346000 4.003000
    endloop
  endfacet
  facet normal 0.916592 0.378951 0.127498
    outer loop
      vertex 82.761002 84.016998 3.241000
      vertex 82.732002 84.000000 3.500000
      vertex 82.963997 83.526001 3.241000
    endloop
  endfacet
  facet normal -0.121368 -0.917747 0.378166
    outer loop
      vertex -93.551003 15.939000 3.000000
      vertex -92.999001 15.866000 3.000000
      vertex -93.526001 16.035000 3.241000
    endloop
  endfacet
  facet normal -0.067352 -0.087762 0.993862
    outer loop
      vertex -45.049000 -61.549000 2.634000
      vertex -45.162998 -62.979000 2.500000
      vertex -43.716000 -62.571999 2.634000
    endloop
  endfacet
  facet normal -0.131288 -0.317177 0.939235
    outer loop
      vertex -42.165001 -63.214001 2.634000
      vertex -41.882999 -62.164001 3.028000
      vertex -43.716000 -62.571999 2.634000
    endloop
  endfacet
  facet normal 0.916662 0.378449 0.128479
    outer loop
      vertex 82.963997 83.526001 3.241000
      vertex 82.732002 84.000000 3.500000
      vertex 82.931000 83.517998 3.500000
    endloop
  endfacet
  facet normal 0.000000 -0.609155 0.793051
    outer loop
      vertex -80.999001 15.707000 2.793000
      vertex -92.999001 15.707000 2.793000
      vertex -92.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal 0.916229 0.121184 0.381887
    outer loop
      vertex 82.963997 83.526001 3.241000
      vertex 82.998001 83.420799 3.192800
      vertex 82.998001 83.535110 3.156526
    endloop
  endfacet
  facet normal -0.617337 -0.206361 0.759151
    outer loop
      vertex -35.305000 0.385000 4.170000
      vertex -35.455002 0.407000 4.054000
      vertex -35.417000 -0.310000 3.890000
    endloop
  endfacet
  facet normal -0.120058 -0.916963 0.380480
    outer loop
      vertex -93.526001 16.035000 3.241000
      vertex -92.999001 15.866000 3.000000
      vertex -92.999001 15.966000 3.241000
    endloop
  endfacet
  facet normal -0.054574 -0.131844 0.989767
    outer loop
      vertex -43.716000 -62.571999 2.634000
      vertex -45.162998 -62.979000 2.500000
      vertex -42.165001 -63.214001 2.634000
    endloop
  endfacet
  facet normal 0.916727 0.122013 0.380428
    outer loop
      vertex 82.963997 83.526001 3.241000
      vertex 82.998001 83.270515 3.241000
      vertex 82.998001 83.420799 3.192800
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 83.420799 3.192800
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 83.704323 3.000000
    endloop
  endfacet
  facet normal 0.000000 -0.793050 0.609156
    outer loop
      vertex -92.999001 15.707000 2.793000
      vertex -80.999001 15.707000 2.793000
      vertex -92.999001 15.866000 3.000000
    endloop
  endfacet
  facet normal 0.982941 0.130826 0.129271
    outer loop
      vertex 82.998001 83.270515 3.241000
      vertex 82.963997 83.526001 3.241000
      vertex 82.931000 83.517998 3.500000
    endloop
  endfacet
  facet normal -0.335760 -0.437276 0.834299
    outer loop
      vertex -42.688999 -60.792000 3.662000
      vertex -44.279999 -60.779999 3.028000
      vertex -43.173000 -61.630001 3.028000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 83.420799 3.192800
      vertex 82.998001 83.270515 3.241000
    endloop
  endfacet
  facet normal -0.043530 -0.155468 0.986881
    outer loop
      vertex -45.162998 -62.979000 2.500000
      vertex -39.619999 -64.530998 2.500000
      vertex -40.500000 -63.433998 2.634000
    endloop
  endfacet
  facet normal -0.084187 -0.637149 0.766129
    outer loop
      vertex -42.165001 -63.214001 2.634000
      vertex -45.162998 -62.979000 2.500000
      vertex -40.500000 -63.433998 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.609155 0.793051
    outer loop
      vertex -80.999001 15.707000 2.793000
      vertex -92.999001 15.500000 2.634000
      vertex -80.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal 0.736177 0.304478 0.604431
    outer loop
      vertex 82.848000 84.067001 3.000000
      vertex 82.998001 83.704323 3.000000
      vertex 82.998001 83.872734 2.915164
    endloop
  endfacet
  facet normal -0.131292 -0.317165 0.939238
    outer loop
      vertex -41.882999 -62.164001 3.028000
      vertex -43.173000 -61.630001 3.028000
      vertex -43.716000 -62.571999 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 6.220000 2.500000
      vertex -92.999001 15.000000 2.500000
      vertex -94.402000 15.348000 2.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 83.704323 3.000000
      vertex 82.998001 83.535110 3.156526
      vertex 82.998001 83.420799 3.192800
    endloop
  endfacet
  facet normal -0.050286 -0.382770 0.922474
    outer loop
      vertex -93.646004 15.585000 2.634000
      vertex -92.999001 15.259000 2.534000
      vertex -92.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal 0.854193 0.353153 0.381626
    outer loop
      vertex 82.963997 83.526001 3.241000
      vertex 82.848000 84.067001 3.000000
      vertex 82.761002 84.016998 3.241000
    endloop
  endfacet
  facet normal -0.044796 -0.340398 0.939214
    outer loop
      vertex -42.165001 -63.214001 2.634000
      vertex -40.500000 -62.346001 3.028000
      vertex -41.882999 -62.164001 3.028000
    endloop
  endfacet
  facet normal -0.210850 -0.509357 0.834325
    outer loop
      vertex -41.632999 -61.229000 3.662000
      vertex -43.173000 -61.630001 3.028000
      vertex -41.882999 -62.164001 3.028000
    endloop
  endfacet
  facet normal -0.050094 -0.382433 0.922624
    outer loop
      vertex -93.646004 15.585000 2.634000
      vertex -93.709000 15.352000 2.534000
      vertex -92.999001 15.259000 2.534000
    endloop
  endfacet
  facet normal 0.854045 0.353234 0.381880
    outer loop
      vertex 82.848000 84.067001 3.000000
      vertex 82.963997 83.526001 3.241000
      vertex 82.998001 83.535110 3.156526
    endloop
  endfacet
  facet normal 0.854055 0.353232 0.381861
    outer loop
      vertex 82.998001 83.535110 3.156526
      vertex 82.998001 83.704323 3.000000
      vertex 82.848000 84.067001 3.000000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 83.872734 2.915164
      vertex 82.998001 83.704323 3.000000
      vertex 82.998001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.210816 -0.509431 0.834288
    outer loop
      vertex -42.688999 -60.792000 3.662000
      vertex -43.173000 -61.630001 3.028000
      vertex -41.632999 -61.229000 3.662000
    endloop
  endfacet
  facet normal 0.521628 -0.297739 0.799534
    outer loop
      vertex -36.446999 -1.728000 3.291000
      vertex -36.667999 -0.316000 3.961000
      vertex -36.708000 -1.189000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -45.162998 -62.979000 2.500000
      vertex -92.999001 -84.000000 2.500000
      vertex -36.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal -0.856953 -0.157374 0.490781
    outer loop
      vertex -35.278999 -0.346000 4.003000
      vertex -35.021000 -2.911000 3.631000
      vertex -35.026001 -1.680000 4.017000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -82.446999 -54.215000 2.500000
      vertex -48.018002 -56.019001 2.500000
      vertex -45.162998 -51.021000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -45.162998 -51.021000 2.500000
      vertex -84.654999 -51.167000 2.500000
      vertex -82.446999 -54.215000 2.500000
    endloop
  endfacet
  facet normal 0.382571 0.923926 0.000000
    outer loop
      vertex 82.000000 84.732002 10.500000
      vertex 81.516998 84.931999 3.500000
      vertex 81.516998 84.931999 10.500000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex -32.000000 -82.000000 10.500000
      vertex 23.000000 -82.000000 2.500000
      vertex -32.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal 0.130407 0.991461 -0.000000
    outer loop
      vertex 81.516998 84.931999 3.500000
      vertex 81.000000 85.000000 10.500000
      vertex 81.516998 84.931999 10.500000
    endloop
  endfacet
  facet normal -0.331672 0.799332 0.501061
    outer loop
      vertex -90.276001 -54.102001 5.500000
      vertex -90.438004 -53.542999 4.501000
      vertex -90.999001 -54.402000 5.500000
    endloop
  endfacet
  facet normal 0.382571 0.923926 0.000000
    outer loop
      vertex 82.000000 84.732002 10.500000
      vertex 82.000000 84.732002 3.500000
      vertex 81.516998 84.931999 3.500000
    endloop
  endfacet
  facet normal 0.412230 0.696606 0.587202
    outer loop
      vertex 82.067001 84.848000 3.000000
      vertex 82.057999 85.000000 2.826000
      vertex 81.526001 84.964996 3.241000
    endloop
  endfacet
  facet normal 0.130407 0.991461 0.000000
    outer loop
      vertex 81.516998 84.931999 3.500000
      vertex 81.000000 85.000000 3.500000
      vertex 81.000000 85.000000 10.500000
    endloop
  endfacet
  facet normal 0.129305 0.983081 0.129741
    outer loop
      vertex 81.526001 84.964996 3.241000
      vertex 81.000000 85.000000 3.500000
      vertex 81.516998 84.931999 3.500000
    endloop
  endfacet
  facet normal -0.509162 0.211328 0.834323
    outer loop
      vertex -45.129002 3.673000 3.028000
      vertex -45.664001 2.384000 3.028000
      vertex -44.291000 3.189000 3.662000
    endloop
  endfacet
  facet normal 0.257280 0.877898 0.403860
    outer loop
      vertex 82.057999 85.000000 2.826000
      vertex 81.000000 85.000000 3.500000
      vertex 81.526001 84.964996 3.241000
    endloop
  endfacet
  facet normal -0.000000 -1.000000 -0.000000
    outer loop
      vertex 80.000000 83.000000 10.500000
      vertex 25.000000 83.000000 10.500000
      vertex 80.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.000000 -82.000000 2.500000
      vertex -39.619999 -64.530998 2.500000
      vertex -45.162998 -62.979000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.383255 0.923643
    outer loop
      vertex -92.999001 15.259000 2.534000
      vertex -80.999001 15.259000 2.534000
      vertex -92.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal -0.017046 -0.130138 0.991349
    outer loop
      vertex -93.709000 15.352000 2.534000
      vertex -92.999001 15.000000 2.500000
      vertex -92.999001 15.259000 2.534000
    endloop
  endfacet
  facet normal -0.122555 -0.016120 0.992331
    outer loop
      vertex -46.714001 -0.665000 2.634000
      vertex -46.932999 1.000000 2.634000
      vertex -48.018002 1.000000 2.500000
    endloop
  endfacet
  facet normal -0.873677 -0.160878 0.459137
    outer loop
      vertex -35.032001 -0.483000 4.425000
      vertex -35.278999 -0.346000 4.003000
      vertex -35.026001 -1.680000 4.017000
    endloop
  endfacet
  facet normal -0.509101 0.211161 0.834403
    outer loop
      vertex -45.664001 2.384000 3.028000
      vertex -44.729000 2.133000 3.662000
      vertex -44.291000 3.189000 3.662000
    endloop
  endfacet
  facet normal -0.047022 -0.189577 0.980739
    outer loop
      vertex -92.999001 15.000000 2.500000
      vertex -93.709000 15.352000 2.534000
      vertex -94.402000 15.348000 2.500000
    endloop
  endfacet
  facet normal -0.340429 -0.044777 0.939203
    outer loop
      vertex -45.846001 1.000000 3.028000
      vertex -46.932999 1.000000 2.634000
      vertex -46.714001 -0.665000 2.634000
    endloop
  endfacet
  facet normal -0.000000 -0.130157 0.991493
    outer loop
      vertex -92.999001 15.000000 2.500000
      vertex -80.999001 15.259000 2.534000
      vertex -92.999001 15.259000 2.534000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 -0.000000
    outer loop
      vertex -34.000000 -83.732002 10.500000
      vertex -34.414001 -83.414001 10.500000
      vertex -34.414001 -83.414001 3.500000
    endloop
  endfacet
  facet normal -0.382571 -0.923926 0.000000
    outer loop
      vertex -33.516998 -83.931999 10.500000
      vertex -34.000000 -83.732002 10.500000
      vertex -34.000000 -83.732002 3.500000
    endloop
  endfacet
  facet normal -0.432881 -0.343061 0.833620
    outer loop
      vertex -35.962002 -0.252000 3.713000
      vertex -35.819000 -1.419000 3.307000
      vertex -35.347000 -1.497000 3.520000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 6.220000 2.500000
      vertex -94.402000 15.348000 2.500000
      vertex -94.999001 15.764000 2.500000
    endloop
  endfacet
  facet normal -0.131104 -0.022914 0.991104
    outer loop
      vertex -46.714001 -0.665000 2.634000
      vertex -48.018002 1.000000 2.500000
      vertex -47.514999 -1.878000 2.500000
    endloop
  endfacet
  facet normal -0.130407 -0.991461 0.000000
    outer loop
      vertex -33.000000 -84.000000 10.500000
      vertex -33.516998 -83.931999 10.500000
      vertex -33.516998 -83.931999 3.500000
    endloop
  endfacet
  facet normal -0.546483 0.071867 0.834381
    outer loop
      vertex -44.729000 2.133000 3.662000
      vertex -45.846001 1.000000 3.028000
      vertex -44.877998 1.000000 3.662000
    endloop
  endfacet
  facet normal -0.651439 -0.260531 0.712566
    outer loop
      vertex -35.417000 -0.310000 3.890000
      vertex -35.347000 -1.497000 3.520000
      vertex -35.278999 -0.346000 4.003000
    endloop
  endfacet
  facet normal -0.546483 -0.071867 0.834381
    outer loop
      vertex -44.877998 1.000000 3.662000
      vertex -45.846001 1.000000 3.028000
      vertex -44.729000 -0.133000 3.662000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 -0.000000
    outer loop
      vertex -34.414001 -83.414001 3.500000
      vertex -34.000000 -83.732002 3.500000
      vertex -34.000000 -83.732002 10.500000
    endloop
  endfacet
  facet normal -0.323393 -0.298927 0.897808
    outer loop
      vertex -35.962002 -0.252000 3.713000
      vertex -35.347000 -1.497000 3.520000
      vertex -35.417000 -0.310000 3.890000
    endloop
  endfacet
  facet normal -0.546481 0.071864 0.834382
    outer loop
      vertex -45.664001 2.384000 3.028000
      vertex -45.846001 1.000000 3.028000
      vertex -44.729000 2.133000 3.662000
    endloop
  endfacet
  facet normal -0.562480 -0.733385 0.381789
    outer loop
      vertex -94.066002 16.152000 3.000000
      vertex -94.436996 16.562000 3.241000
      vertex -94.508003 16.490999 3.000000
    endloop
  endfacet
  facet normal -0.604077 -0.786440 0.128853
    outer loop
      vertex -34.000000 -83.732002 3.500000
      vertex -34.414001 -83.414001 3.500000
      vertex -34.438000 -83.438004 3.241000
    endloop
  endfacet
  facet normal -0.564437 -0.733417 0.378829
    outer loop
      vertex -94.015999 16.238001 3.241000
      vertex -94.436996 16.562000 3.241000
      vertex -94.066002 16.152000 3.000000
    endloop
  endfacet
  facet normal -0.340442 -0.044769 0.939199
    outer loop
      vertex -45.664001 -0.384000 3.028000
      vertex -45.846001 1.000000 3.028000
      vertex -46.714001 -0.665000 2.634000
    endloop
  endfacet
  facet normal -0.546481 -0.071864 0.834382
    outer loop
      vertex -44.729000 -0.133000 3.662000
      vertex -45.846001 1.000000 3.028000
      vertex -45.664001 -0.384000 3.028000
    endloop
  endfacet
  facet normal -0.604658 -0.785691 0.130687
    outer loop
      vertex -34.438000 -83.438004 3.241000
      vertex -34.016998 -83.762001 3.241000
      vertex -34.000000 -83.732002 3.500000
    endloop
  endfacet
  facet normal -0.091357 -0.356815 0.929697
    outer loop
      vertex -35.819000 -1.419000 3.307000
      vertex -36.141998 -0.255000 3.722000
      vertex -35.980999 -1.414000 3.293000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -48.018002 1.000000 2.500000
      vertex -47.028000 4.730000 2.500000
      vertex -81.975998 1.948000 2.500000
    endloop
  endfacet
  facet normal 0.052630 -0.322369 0.945150
    outer loop
      vertex -36.141998 -0.255000 3.722000
      vertex -35.819000 -1.419000 3.307000
      vertex -35.962002 -0.252000 3.713000
    endloop
  endfacet
  facet normal -0.147637 -0.356098 0.922712
    outer loop
      vertex -93.646004 15.585000 2.634000
      vertex -94.249001 15.835000 2.634000
      vertex -93.709000 15.352000 2.534000
    endloop
  endfacet
  facet normal 0.207647 -0.314065 0.926416
    outer loop
      vertex -36.446999 -1.728000 3.291000
      vertex -35.980999 -1.414000 3.293000
      vertex -36.141998 -0.255000 3.722000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -81.975998 0.052000 2.500000
      vertex -82.903000 -2.617000 2.500000
      vertex -47.514999 -1.878000 2.500000
    endloop
  endfacet
  facet normal -0.372612 -0.483885 0.791843
    outer loop
      vertex -94.620003 16.379000 2.793000
      vertex -94.766998 16.232000 2.634000
      vertex -94.146004 16.014000 2.793000
    endloop
  endfacet
  facet normal 0.184667 -0.280061 0.942053
    outer loop
      vertex -35.825001 -2.697000 2.881000
      vertex -35.980999 -1.414000 3.293000
      vertex -36.446999 -1.728000 3.291000
    endloop
  endfacet
  facet normal -0.793055 -0.609150 -0.000000
    outer loop
      vertex -34.731998 -83.000000 10.500000
      vertex -34.731998 -83.000000 3.500000
      vertex -34.414001 -83.414001 10.500000
    endloop
  endfacet
  facet normal 0.421750 -0.333979 0.842962
    outer loop
      vertex -36.141998 -0.255000 3.722000
      vertex -36.667999 -0.316000 3.961000
      vertex -36.446999 -1.728000 3.291000
    endloop
  endfacet
  facet normal -0.045978 -0.251560 0.966749
    outer loop
      vertex -94.402000 15.348000 2.500000
      vertex -93.709000 15.352000 2.534000
      vertex -94.249001 15.835000 2.634000
    endloop
  endfacet
  facet normal -0.383254 -0.923643 0.000000
    outer loop
      vertex -49.257999 16.034000 10.500000
      vertex -49.499001 16.134001 10.500000
      vertex -49.499001 16.134001 3.500000
    endloop
  endfacet
  facet normal -0.484307 -0.372149 0.791803
    outer loop
      vertex -94.985001 16.854000 2.793000
      vertex -94.766998 16.232000 2.634000
      vertex -94.620003 16.379000 2.793000
    endloop
  endfacet
  facet normal -0.786783 -0.603633 0.128841
    outer loop
      vertex -34.438000 -83.438004 3.241000
      vertex -34.414001 -83.414001 3.500000
      vertex -34.761002 -83.016998 3.241000
    endloop
  endfacet
  facet normal -0.914795 -0.146600 0.376377
    outer loop
      vertex -35.278999 -0.346000 4.003000
      vertex -35.188000 -2.806000 3.266000
      vertex -35.021000 -2.911000 3.631000
    endloop
  endfacet
  facet normal -0.382571 -0.923926 -0.000000
    outer loop
      vertex -33.516998 -83.931999 10.500000
      vertex -34.000000 -83.732002 3.500000
      vertex -33.516998 -83.931999 3.500000
    endloop
  endfacet
  facet normal -0.167547 -0.084010 0.982278
    outer loop
      vertex -94.999001 15.764000 2.500000
      vertex -94.249001 15.835000 2.634000
      vertex -94.999001 16.068001 2.526000
    endloop
  endfacet
  facet normal -0.762520 -0.211276 0.611495
    outer loop
      vertex -35.284000 -2.775000 3.157000
      vertex -35.188000 -2.806000 3.266000
      vertex -35.347000 -1.497000 3.520000
    endloop
  endfacet
  facet normal -0.607304 -0.794469 0.000000
    outer loop
      vertex -49.499001 16.134001 3.500000
      vertex -49.499001 16.134001 10.500000
      vertex -49.707001 16.292999 10.500000
    endloop
  endfacet
  facet normal -0.607304 -0.794469 0.000000
    outer loop
      vertex -49.707001 16.292999 3.500000
      vertex -49.499001 16.134001 3.500000
      vertex -49.707001 16.292999 10.500000
    endloop
  endfacet
  facet normal -0.383254 -0.923643 0.000000
    outer loop
      vertex -49.499001 16.134001 3.500000
      vertex -49.257999 16.034000 3.500000
      vertex -49.257999 16.034000 10.500000
    endloop
  endfacet
  facet normal -0.763135 -0.211207 0.610751
    outer loop
      vertex -35.347000 -1.497000 3.520000
      vertex -35.188000 -2.806000 3.266000
      vertex -35.278999 -0.346000 4.003000
    endloop
  endfacet
  facet normal -0.334321 0.799220 0.499477
    outer loop
      vertex -90.999001 -54.402000 5.500000
      vertex -90.438004 -53.542999 4.501000
      vertex -91.301003 -53.903999 4.501000
    endloop
  endfacet
  facet normal -0.793055 -0.609150 -0.000000
    outer loop
      vertex -34.731998 -83.000000 3.500000
      vertex -34.414001 -83.414001 3.500000
      vertex -34.414001 -83.414001 10.500000
    endloop
  endfacet
  facet normal -0.432687 -0.266002 0.861409
    outer loop
      vertex -35.819000 -1.419000 3.307000
      vertex -35.284000 -2.775000 3.157000
      vertex -35.347000 -1.497000 3.520000
    endloop
  endfacet
  facet normal -0.527055 0.686167 0.501385
    outer loop
      vertex -90.999001 -54.402000 5.500000
      vertex -91.301003 -53.903999 4.501000
      vertex -91.620003 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.529741 0.685324 0.499705
    outer loop
      vertex -91.620003 -54.879002 5.500000
      vertex -91.301003 -53.903999 4.501000
      vertex -92.041000 -54.476002 4.501000
    endloop
  endfacet
  facet normal -0.151661 -0.217649 0.964172
    outer loop
      vertex -94.402000 15.348000 2.500000
      vertex -94.249001 15.835000 2.634000
      vertex -94.999001 15.764000 2.500000
    endloop
  endfacet
  facet normal -0.181768 -0.370498 0.910874
    outer loop
      vertex -94.999001 16.379000 2.597000
      vertex -94.985001 16.854000 2.793000
      vertex -94.999001 16.941999 2.826000
    endloop
  endfacet
  facet normal -0.358152 -0.347092 0.866749
    outer loop
      vertex -94.999001 16.379000 2.597000
      vertex -94.766998 16.232000 2.634000
      vertex -94.985001 16.854000 2.793000
    endloop
  endfacet
  facet normal -0.284272 -0.213387 0.934695
    outer loop
      vertex -94.766998 16.232000 2.634000
      vertex -94.999001 16.379000 2.597000
      vertex -94.999001 16.068001 2.526000
    endloop
  endfacet
  facet normal -0.224988 -0.293560 0.929087
    outer loop
      vertex -94.766998 16.232000 2.634000
      vertex -94.999001 16.068001 2.526000
      vertex -94.249001 15.835000 2.634000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 16.379000 2.597000
      vertex -94.999001 16.941999 2.826000
    endloop
  endfacet
  facet normal -0.373124 -0.486845 0.789785
    outer loop
      vertex -94.146004 16.014000 2.793000
      vertex -94.766998 16.232000 2.634000
      vertex -94.249001 15.835000 2.634000
    endloop
  endfacet
  facet normal -0.353629 -0.855344 0.378593
    outer loop
      vertex -33.526001 -83.964996 3.241000
      vertex -34.016998 -83.762001 3.241000
      vertex -34.067001 -83.848000 3.000000
    endloop
  endfacet
  facet normal -0.378831 -0.916303 0.129907
    outer loop
      vertex -33.526001 -83.964996 3.241000
      vertex -33.516998 -83.931999 3.500000
      vertex -34.016998 -83.762001 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.999001 -54.402000 5.500000
      vertex -91.620003 -54.879002 5.500000
      vertex -89.999001 -56.133999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -91.620003 -54.879002 5.500000
      vertex -92.097000 -55.500000 5.500000
      vertex -90.364998 -56.500000 5.500000
    endloop
  endfacet
  facet normal -0.686032 0.526951 0.501680
    outer loop
      vertex -91.620003 -54.879002 5.500000
      vertex -92.041000 -54.476002 4.501000
      vertex -92.097000 -55.500000 5.500000
    endloop
  endfacet
  facet normal -0.379275 -0.915966 0.130984
    outer loop
      vertex -34.016998 -83.762001 3.241000
      vertex -33.516998 -83.931999 3.500000
      vertex -34.000000 -83.732002 3.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 6.220000 2.500000
      vertex -94.999001 15.764000 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 16.068001 2.526000
      vertex -94.999001 16.379000 2.597000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 15.764000 2.500000
      vertex -94.999001 16.068001 2.526000
    endloop
  endfacet
  facet normal -0.998893 -0.012283 0.045409
    outer loop
      vertex -35.018002 -3.994000 3.404000
      vertex -35.000000 -5.103000 3.500000
      vertex -35.021000 -2.911000 3.631000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -90.879997 8.395000 2.500000
      vertex -88.056000 8.444000 2.500000
      vertex -92.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 6.220000 2.500000
      vertex -90.879997 8.395000 2.500000
      vertex -92.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -90.499001 -57.000000 5.500000
      vertex -90.464996 -56.741001 5.500000
      vertex -92.499001 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -92.499001 -57.000000 5.500000
      vertex -90.464996 -57.258999 5.500000
      vertex -90.499001 -57.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -90.464996 -56.741001 5.500000
      vertex -90.364998 -56.500000 5.500000
      vertex -92.097000 -55.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -90.364998 -56.500000 5.500000
      vertex -90.206001 -56.292999 5.500000
      vertex -91.620003 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.915079 -0.085155 0.394183
    outer loop
      vertex -35.188000 -2.806000 3.266000
      vertex -35.018002 -3.994000 3.404000
      vertex -35.021000 -2.911000 3.631000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 -56.034000 5.500000
      vertex -90.276001 -54.102001 5.500000
      vertex -90.999001 -54.402000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.999001 -54.402000 5.500000
      vertex -89.999001 -56.133999 5.500000
      vertex -89.758003 -56.034000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -90.206001 -56.292999 5.500000
      vertex -89.999001 -56.133999 5.500000
      vertex -91.620003 -54.879002 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.097000 -55.500000 5.500000
      vertex -92.397003 -56.223999 5.500000
      vertex -90.464996 -56.741001 5.500000
    endloop
  endfacet
  facet normal -0.786559 -0.604160 0.127731
    outer loop
      vertex -34.761002 -83.016998 3.241000
      vertex -34.414001 -83.414001 3.500000
      vertex -34.731998 -83.000000 3.500000
    endloop
  endfacet
  facet normal -0.689144 0.524975 0.499481
    outer loop
      vertex -92.607002 -55.219002 4.501000
      vertex -92.097000 -55.500000 5.500000
      vertex -92.041000 -54.476002 4.501000
    endloop
  endfacet
  facet normal -0.799383 0.331240 0.501266
    outer loop
      vertex -92.397003 -56.223999 5.500000
      vertex -92.097000 -55.500000 5.500000
      vertex -92.607002 -55.219002 4.501000
    endloop
  endfacet
  facet normal -0.924320 -0.381618 -0.000000
    outer loop
      vertex -34.931000 -82.517998 3.500000
      vertex -34.731998 -83.000000 3.500000
      vertex -34.731998 -83.000000 10.500000
    endloop
  endfacet
  facet normal -0.916588 -0.378956 0.127512
    outer loop
      vertex -34.761002 -83.016998 3.241000
      vertex -34.731998 -83.000000 3.500000
      vertex -34.964001 -82.526001 3.241000
    endloop
  endfacet
  facet normal -0.916658 -0.378455 0.128492
    outer loop
      vertex -34.931000 -82.517998 3.500000
      vertex -34.964001 -82.526001 3.241000
      vertex -34.731998 -83.000000 3.500000
    endloop
  endfacet
  facet normal -0.673764 0.276513 0.685260
    outer loop
      vertex -92.607002 -55.219002 4.501000
      vertex -93.732002 -55.881001 3.662000
      vertex -92.961998 -56.084000 4.501000
    endloop
  endfacet
  facet normal -0.563205 -0.734329 0.378893
    outer loop
      vertex -34.508999 -83.509003 3.000000
      vertex -34.067001 -83.848000 3.000000
      vertex -34.016998 -83.762001 3.241000
    endloop
  endfacet
  facet normal 0.233809 -0.292281 0.927311
    outer loop
      vertex -36.719002 -2.780000 3.028000
      vertex -36.209000 -3.327000 2.727000
      vertex -36.446999 -1.728000 3.291000
    endloop
  endfacet
  facet normal -0.801502 0.328937 0.499395
    outer loop
      vertex -92.607002 -55.219002 4.501000
      vertex -92.961998 -56.084000 4.501000
      vertex -92.397003 -56.223999 5.500000
    endloop
  endfacet
  facet normal -0.563676 -0.732440 0.381839
    outer loop
      vertex -34.438000 -83.438004 3.241000
      vertex -34.508999 -83.509003 3.000000
      vertex -34.016998 -83.762001 3.241000
    endloop
  endfacet
  facet normal -0.722318 0.092627 0.685329
    outer loop
      vertex -92.961998 -56.084000 4.501000
      vertex -93.732002 -55.881001 3.662000
      vertex -93.081001 -57.012001 4.501000
    endloop
  endfacet
  facet normal -0.484854 -0.632172 0.604379
    outer loop
      vertex -34.620998 -83.621002 2.793000
      vertex -34.067001 -83.848000 3.000000
      vertex -34.508999 -83.509003 3.000000
    endloop
  endfacet
  facet normal -0.858026 0.112779 0.501070
    outer loop
      vertex -92.397003 -56.223999 5.500000
      vertex -92.961998 -56.084000 4.501000
      vertex -92.499001 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.859373 0.110203 0.499333
    outer loop
      vertex -92.499001 -57.000000 5.500000
      vertex -92.961998 -56.084000 4.501000
      vertex -93.081001 -57.012001 4.501000
    endloop
  endfacet
  facet normal -0.247860 -0.323394 0.913226
    outer loop
      vertex -35.682999 -2.707000 2.916000
      vertex -35.980999 -1.414000 3.293000
      vertex -35.825001 -2.697000 2.881000
    endloop
  endfacet
  facet normal -0.857959 -0.112770 0.501187
    outer loop
      vertex -92.499001 -57.000000 5.500000
      vertex -93.081001 -57.012001 4.501000
      vertex -92.397003 -57.776001 5.500000
    endloop
  endfacet
  facet normal 0.134297 -0.311785 0.940614
    outer loop
      vertex -35.825001 -2.697000 2.881000
      vertex -36.446999 -1.728000 3.291000
      vertex -36.209000 -3.327000 2.727000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.397003 -56.223999 5.500000
      vertex -92.499001 -57.000000 5.500000
      vertex -90.464996 -56.741001 5.500000
    endloop
  endfacet
  facet normal 0.010084 0.152069 0.988319
    outer loop
      vertex -87.154999 -49.852001 2.500000
      vertex -90.879997 -49.605000 2.500000
      vertex -89.521004 -50.566002 2.634000
    endloop
  endfacet
  facet normal -0.928869 -0.091215 0.359003
    outer loop
      vertex -35.188000 -2.806000 3.266000
      vertex -35.158001 -3.938000 3.056000
      vertex -35.018002 -3.994000 3.404000
    endloop
  endfacet
  facet normal -0.632381 -0.484608 0.604359
    outer loop
      vertex -34.985001 -83.146004 2.793000
      vertex -34.620998 -83.621002 2.793000
      vertex -34.508999 -83.509003 3.000000
    endloop
  endfacet
  facet normal -0.015718 0.116247 0.993096
    outer loop
      vertex -89.521004 -50.566002 2.634000
      vertex -90.879997 -49.605000 2.500000
      vertex -91.184998 -50.791000 2.634000
    endloop
  endfacet
  facet normal -0.733390 -0.562487 0.381768
    outer loop
      vertex -34.848000 -83.067001 3.000000
      vertex -34.508999 -83.509003 3.000000
      vertex -34.438000 -83.438004 3.241000
    endloop
  endfacet
  facet normal -0.052434 0.125420 0.990717
    outer loop
      vertex -91.184998 -50.791000 2.634000
      vertex -90.879997 -49.605000 2.500000
      vertex -92.735001 -51.438999 2.634000
    endloop
  endfacet
  facet normal 1.000000 -0.000000 0.000000
    outer loop
      vertex 82.998001 -84.000000 10.500000
      vertex 82.998001 83.015015 3.500000
      vertex 82.998001 83.015015 10.500000
    endloop
  endfacet
  facet normal -0.762596 -0.144921 0.630433
    outer loop
      vertex -35.238998 -3.921000 2.948000
      vertex -35.188000 -2.806000 3.266000
      vertex -35.284000 -2.775000 3.157000
    endloop
  endfacet
  facet normal 0.181521 0.309781 0.933320
    outer loop
      vertex -35.884998 -53.825001 3.032000
      vertex -36.446999 -54.272999 3.290000
      vertex -36.070000 -55.220001 3.531000
    endloop
  endfacet
  facet normal -0.802958 -0.129221 0.581859
    outer loop
      vertex -35.188000 -2.806000 3.266000
      vertex -35.238998 -3.921000 2.948000
      vertex -35.158001 -3.938000 3.056000
    endloop
  endfacet
  facet normal 0.189374 0.300735 0.934717
    outer loop
      vertex -36.446999 -54.272999 3.290000
      vertex -35.884998 -53.825001 3.032000
      vertex -36.209000 -52.673000 2.727000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 -32.768002 2.500000
      vertex -93.531998 -50.578999 2.500000
      vertex -90.879997 -49.605000 2.500000
    endloop
  endfacet
  facet normal 0.519713 0.300782 0.799643
    outer loop
      vertex -36.708000 -54.811001 3.662000
      vertex -36.667999 -55.682999 3.964000
      vertex -36.446999 -54.272999 3.290000
    endloop
  endfacet
  facet normal -0.530266 -0.297054 0.794089
    outer loop
      vertex -35.682999 -2.707000 2.916000
      vertex -35.284000 -2.775000 3.157000
      vertex -35.819000 -1.419000 3.307000
    endloop
  endfacet
  facet normal -0.336915 0.436054 0.834473
    outer loop
      vertex -93.292000 -53.231998 3.028000
      vertex -91.700996 -53.216000 3.662000
      vertex -92.188004 -52.379002 3.028000
    endloop
  endfacet
  facet normal -0.091313 -0.298084 0.950162
    outer loop
      vertex -35.819000 -1.419000 3.307000
      vertex -35.980999 -1.414000 3.293000
      vertex -35.682999 -2.707000 2.916000
    endloop
  endfacet
  facet normal -0.530633 -0.172194 0.829926
    outer loop
      vertex -35.238998 -3.921000 2.948000
      vertex -35.284000 -2.775000 3.157000
      vertex -35.682999 -2.707000 2.916000
    endloop
  endfacet
  facet normal -0.281155 0.671966 0.685137
    outer loop
      vertex -90.647003 -52.775002 3.662000
      vertex -91.700996 -53.216000 3.662000
      vertex -90.438004 -53.542999 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 83.015015 3.500000
      vertex 82.998001 -84.000000 10.500000
      vertex 82.998001 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.060093 -0.202311 0.977476
    outer loop
      vertex -35.825001 -2.697000 2.881000
      vertex -36.209000 -3.327000 2.727000
      vertex -35.708000 -3.872000 2.645000
    endloop
  endfacet
  facet normal -0.212692 0.508337 0.834479
    outer loop
      vertex -92.188004 -52.379002 3.028000
      vertex -91.700996 -53.216000 3.662000
      vertex -90.647003 -52.775002 3.662000
    endloop
  endfacet
  facet normal -0.310412 0.335078 0.889588
    outer loop
      vertex -35.980000 -55.888000 3.756000
      vertex -35.426998 -55.834999 3.929000
      vertex -35.897999 -55.220001 3.533000
    endloop
  endfacet
  facet normal -0.373903 0.282473 0.883406
    outer loop
      vertex -35.386002 -55.148998 3.727000
      vertex -35.897999 -55.220001 3.533000
      vertex -35.426998 -55.834999 3.929000
    endloop
  endfacet
  facet normal -0.348606 -0.074898 0.934272
    outer loop
      vertex -35.583000 -3.880000 2.691000
      vertex -35.708000 -3.872000 2.645000
      vertex -35.741001 -5.103000 2.534000
    endloop
  endfacet
  facet normal -0.209859 0.271570 0.939260
    outer loop
      vertex -94.064003 -52.466000 2.634000
      vertex -92.188004 -52.379002 3.028000
      vertex -92.735001 -51.438999 2.634000
    endloop
  endfacet
  facet normal -0.349313 -0.217826 0.911336
    outer loop
      vertex -35.825001 -2.697000 2.881000
      vertex -35.708000 -3.872000 2.645000
      vertex -35.583000 -3.880000 2.691000
    endloop
  endfacet
  facet normal -0.209858 0.271610 0.939248
    outer loop
      vertex -92.188004 -52.379002 3.028000
      vertex -94.064003 -52.466000 2.634000
      vertex -93.292000 -53.231998 3.028000
    endloop
  endfacet
  facet normal -0.601618 -0.199645 0.773433
    outer loop
      vertex -35.682999 -2.707000 2.916000
      vertex -35.583000 -3.880000 2.691000
      vertex -35.238998 -3.921000 2.948000
    endloop
  endfacet
  facet normal -0.212504 0.508745 0.834278
    outer loop
      vertex -90.900002 -51.841000 3.028000
      vertex -92.188004 -52.379002 3.028000
      vertex -90.647003 -52.775002 3.662000
    endloop
  endfacet
  facet normal -0.247780 -0.202839 0.947344
    outer loop
      vertex -35.825001 -2.697000 2.881000
      vertex -35.583000 -3.880000 2.691000
      vertex -35.682999 -2.707000 2.916000
    endloop
  endfacet
  facet normal -0.073859 0.546244 0.834364
    outer loop
      vertex -90.900002 -51.841000 3.028000
      vertex -89.514000 -52.622002 3.662000
      vertex -89.516998 -51.653999 3.028000
    endloop
  endfacet
  facet normal 0.348754 0.359141 0.865672
    outer loop
      vertex -36.070000 -55.220001 3.531000
      vertex -36.446999 -54.272999 3.290000
      vertex -36.667999 -55.682999 3.964000
    endloop
  endfacet
  facet normal -0.073778 0.546342 0.834306
    outer loop
      vertex -90.900002 -51.841000 3.028000
      vertex -90.647003 -52.775002 3.662000
      vertex -89.514000 -52.622002 3.662000
    endloop
  endfacet
  facet normal 0.063330 -0.091310 0.993807
    outer loop
      vertex -36.209000 -3.327000 2.727000
      vertex -35.741001 -5.103000 2.534000
      vertex -35.708000 -3.872000 2.645000
    endloop
  endfacet
  facet normal -0.132335 0.316543 0.939302
    outer loop
      vertex -90.900002 -51.841000 3.028000
      vertex -91.184998 -50.791000 2.634000
      vertex -92.735001 -51.438999 2.634000
    endloop
  endfacet
  facet normal 0.278500 -0.672988 0.685219
    outer loop
      vertex -39.366001 -3.229000 3.662000
      vertex -38.310001 -2.792000 3.662000
      vertex -39.571999 -2.460000 4.501000
    endloop
  endfacet
  facet normal 0.278725 -0.672676 0.685434
    outer loop
      vertex -39.571999 -2.460000 4.501000
      vertex -38.310001 -2.792000 3.662000
      vertex -38.708000 -2.102000 4.501000
    endloop
  endfacet
  facet normal -0.132289 0.316706 0.939253
    outer loop
      vertex -92.735001 -51.438999 2.634000
      vertex -92.188004 -52.379002 3.028000
      vertex -90.900002 -51.841000 3.028000
    endloop
  endfacet
  facet normal 0.443622 -0.577475 0.685362
    outer loop
      vertex -37.403999 -2.096000 3.662000
      vertex -38.708000 -2.102000 4.501000
      vertex -38.310001 -2.792000 3.662000
    endloop
  endfacet
  facet normal -0.045971 0.339986 0.939306
    outer loop
      vertex -91.184998 -50.791000 2.634000
      vertex -90.900002 -51.841000 3.028000
      vertex -89.516998 -51.653999 3.028000
    endloop
  endfacet
  facet normal 0.577797 -0.443381 0.685248
    outer loop
      vertex -37.966999 -1.533000 4.501000
      vertex -37.403999 -2.096000 3.662000
      vertex -36.708000 -1.189000 3.662000
    endloop
  endfacet
  facet normal 0.335789 -0.437105 0.834377
    outer loop
      vertex -36.719002 -2.780000 3.028000
      vertex -37.403999 -2.096000 3.662000
      vertex -38.310001 -2.792000 3.662000
    endloop
  endfacet
  facet normal -0.011025 0.317852 0.948076
    outer loop
      vertex -35.980000 -55.888000 3.756000
      vertex -35.897999 -55.220001 3.533000
      vertex -36.070000 -55.220001 3.531000
    endloop
  endfacet
  facet normal -0.042371 0.115366 0.992419
    outer loop
      vertex -90.879997 -49.605000 2.500000
      vertex -93.531998 -50.578999 2.500000
      vertex -92.735001 -51.438999 2.634000
    endloop
  endfacet
  facet normal 0.432591 0.251091 0.865921
    outer loop
      vertex -36.160999 -55.883999 3.769000
      vertex -36.070000 -55.220001 3.531000
      vertex -36.667999 -55.682999 3.964000
    endloop
  endfacet
  facet normal 0.679548 -0.265387 0.683948
    outer loop
      vertex -36.708000 -1.189000 3.662000
      vertex -36.667999 -0.316000 3.961000
      vertex -37.396999 -0.791000 4.501000
    endloop
  endfacet
  facet normal 0.577752 -0.443825 0.684998
    outer loop
      vertex -36.708000 -1.189000 3.662000
      vertex -37.396999 -0.791000 4.501000
      vertex -37.966999 -1.533000 4.501000
    endloop
  endfacet
  facet normal 0.451972 -0.346827 0.821847
    outer loop
      vertex -36.446999 -1.728000 3.291000
      vertex -36.708000 -1.189000 3.662000
      vertex -37.403999 -2.096000 3.662000
    endloop
  endfacet
  facet normal -0.069704 0.090201 0.993481
    outer loop
      vertex -94.064003 -52.466000 2.634000
      vertex -92.735001 -51.438999 2.634000
      vertex -93.531998 -50.578999 2.500000
    endloop
  endfacet
  facet normal 0.447704 -0.324102 0.833378
    outer loop
      vertex -37.403999 -2.096000 3.662000
      vertex -36.719002 -2.780000 3.028000
      vertex -36.446999 -1.728000 3.291000
    endloop
  endfacet
  facet normal -0.564714 -0.233011 0.791710
    outer loop
      vertex -35.701000 14.750000 2.634000
      vertex -35.351002 14.442000 2.793000
      vertex -35.521000 14.854000 2.793000
    endloop
  endfacet
  facet normal -0.938613 0.212727 0.271575
    outer loop
      vertex -94.667999 -55.633999 3.028000
      vertex -94.064003 -52.466000 2.634000
      vertex -94.999001 -57.000000 2.954000
    endloop
  endfacet
  facet normal -0.075049 0.091671 0.992957
    outer loop
      vertex -93.531998 -50.578999 2.500000
      vertex -94.999001 -51.779999 2.500000
      vertex -94.064003 -52.466000 2.634000
    endloop
  endfacet
  facet normal -0.565440 -0.234300 0.790810
    outer loop
      vertex -35.351002 14.442000 2.793000
      vertex -35.701000 14.750000 2.634000
      vertex -35.550999 14.388000 2.634000
    endloop
  endfacet
  facet normal 0.094936 -0.722141 0.685200
    outer loop
      vertex -40.500000 -2.582000 4.501000
      vertex -39.366001 -3.229000 3.662000
      vertex -39.571999 -2.460000 4.501000
    endloop
  endfacet
  facet normal -0.078958 0.086376 0.993129
    outer loop
      vertex -94.999001 -51.779999 2.500000
      vertex -94.999001 -57.000000 2.954000
      vertex -94.064003 -52.466000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -93.531998 -50.578999 2.500000
      vertex -94.999001 -32.768002 2.500000
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -94.999001 -51.779999 2.500000
      vertex -94.999001 -32.768002 2.500000
    endloop
  endfacet
  facet normal 0.210816 -0.509431 0.834288
    outer loop
      vertex -39.366001 -3.229000 3.662000
      vertex -37.826000 -3.630000 3.028000
      vertex -38.310001 -2.792000 3.662000
    endloop
  endfacet
  facet normal -0.445203 0.575958 0.685614
    outer loop
      vertex -91.301003 -53.903999 4.501000
      vertex -92.606003 -53.914001 3.662000
      vertex -92.041000 -54.476002 4.501000
    endloop
  endfacet
  facet normal 0.335759 -0.437276 0.834299
    outer loop
      vertex -37.826000 -3.630000 3.028000
      vertex -36.719002 -2.780000 3.028000
      vertex -38.310001 -2.792000 3.662000
    endloop
  endfacet
  facet normal 0.156389 0.109770 0.981577
    outer loop
      vertex -36.060001 -56.935001 3.951000
      vertex -36.222000 -56.426998 3.920000
      vertex -36.249001 -56.933998 3.981000
    endloop
  endfacet
  facet normal -0.444880 0.576817 0.685101
    outer loop
      vertex -91.301003 -53.903999 4.501000
      vertex -91.700996 -53.216000 3.662000
      vertex -92.606003 -53.914001 3.662000
    endloop
  endfacet
  facet normal -0.357251 -0.148034 0.922203
    outer loop
      vertex -35.701000 14.750000 2.634000
      vertex -35.909000 14.629000 2.534000
      vertex -35.550999 14.388000 2.634000
    endloop
  endfacet
  facet normal -0.281114 0.672025 0.685097
    outer loop
      vertex -91.700996 -53.216000 3.662000
      vertex -91.301003 -53.903999 4.501000
      vertex -90.438004 -53.542999 4.501000
    endloop
  endfacet
  facet normal 0.134679 0.103087 0.985512
    outer loop
      vertex -36.060001 -56.935001 3.951000
      vertex -36.035999 -56.431000 3.895000
      vertex -36.222000 -56.426998 3.920000
    endloop
  endfacet
  facet normal 0.228286 -0.297308 0.927089
    outer loop
      vertex -36.209000 -3.327000 2.727000
      vertex -36.719002 -2.780000 3.028000
      vertex -37.826000 -3.630000 3.028000
    endloop
  endfacet
  facet normal -0.579551 0.440709 0.685490
    outer loop
      vertex -92.041000 -54.476002 4.501000
      vertex -92.606003 -53.914001 3.662000
      vertex -93.297997 -54.824001 3.662000
    endloop
  endfacet
  facet normal 0.094890 -0.722179 0.685167
    outer loop
      vertex -40.500000 -3.378000 3.662000
      vertex -39.366001 -3.229000 3.662000
      vertex -40.500000 -2.582000 4.501000
    endloop
  endfacet
  facet normal -0.483091 0.198172 0.852849
    outer loop
      vertex -94.138000 -54.341999 3.028000
      vertex -94.064003 -52.466000 2.634000
      vertex -94.667999 -55.633999 3.028000
    endloop
  endfacet
  facet normal -0.336806 0.436691 0.834184
    outer loop
      vertex -93.292000 -53.231998 3.028000
      vertex -92.606003 -53.914001 3.662000
      vertex -91.700996 -53.216000 3.662000
    endloop
  endfacet
  facet normal 0.155701 -0.088169 0.983862
    outer loop
      vertex -36.222000 -57.567001 3.920000
      vertex -36.060001 -56.935001 3.951000
      vertex -36.249001 -56.933998 3.981000
    endloop
  endfacet
  facet normal -0.579480 0.441435 0.685083
    outer loop
      vertex -93.297997 -54.824001 3.662000
      vertex -92.607002 -55.219002 4.501000
      vertex -92.041000 -54.476002 4.501000
    endloop
  endfacet
  facet normal -0.378951 -0.916100 0.130985
    outer loop
      vertex -49.266998 16.000999 3.241000
      vertex -49.499001 16.134001 3.500000
      vertex -49.515999 16.104000 3.241000
    endloop
  endfacet
  facet normal 0.071813 -0.546546 0.834344
    outer loop
      vertex -40.500000 -3.378000 3.662000
      vertex -39.116001 -4.164000 3.028000
      vertex -39.366001 -3.229000 3.662000
    endloop
  endfacet
  facet normal -0.372146 -0.486125 0.790689
    outer loop
      vertex -35.792000 15.207000 2.793000
      vertex -36.146000 15.478000 2.793000
      vertex -36.250000 15.299000 2.634000
    endloop
  endfacet
  facet normal -0.380007 -0.915818 0.129894
    outer loop
      vertex -49.266998 16.000999 3.241000
      vertex -49.257999 16.034000 3.500000
      vertex -49.499001 16.134001 3.500000
    endloop
  endfacet
  facet normal -0.438611 0.334293 0.834187
    outer loop
      vertex -92.606003 -53.914001 3.662000
      vertex -93.292000 -53.231998 3.028000
      vertex -94.138000 -54.341999 3.028000
    endloop
  endfacet
  facet normal -0.794902 -0.606738 -0.000000
    outer loop
      vertex -49.707001 16.292999 10.500000
      vertex -49.865002 16.500000 3.500000
      vertex -49.707001 16.292999 3.500000
    endloop
  endfacet
  facet normal 0.210850 -0.509357 0.834324
    outer loop
      vertex -39.116001 -4.164000 3.028000
      vertex -37.826000 -3.630000 3.028000
      vertex -39.366001 -3.229000 3.662000
    endloop
  endfacet
  facet normal -0.438535 0.333476 0.834554
    outer loop
      vertex -92.606003 -53.914001 3.662000
      vertex -94.138000 -54.341999 3.028000
      vertex -93.297997 -54.824001 3.662000
    endloop
  endfacet
  facet normal -0.085971 -0.320484 0.943345
    outer loop
      vertex -36.611000 15.449000 2.634000
      vertex -37.000000 15.259000 2.534000
      vertex -36.369999 15.090000 2.534000
    endloop
  endfacet
  facet normal -0.272950 0.208032 0.939266
    outer loop
      vertex -94.138000 -54.341999 3.028000
      vertex -93.292000 -53.231998 3.028000
      vertex -94.064003 -52.466000 2.634000
    endloop
  endfacet
  facet normal -0.923645 0.000000 0.383249
    outer loop
      vertex -35.034000 -5.103000 3.241000
      vertex -35.133999 -5.103000 3.000000
      vertex -35.133999 -50.896999 3.000000
    endloop
  endfacet
  facet normal -0.991482 -0.004827 0.130157
    outer loop
      vertex -35.018002 -3.994000 3.404000
      vertex -35.034000 -5.103000 3.241000
      vertex -35.000000 -5.103000 3.500000
    endloop
  endfacet
  facet normal -0.267332 0.095208 0.958889
    outer loop
      vertex -35.467999 -56.931000 4.103000
      vertex -35.455002 -56.401001 4.054000
      vertex -36.035999 -56.431000 3.895000
    endloop
  endfacet
  facet normal -0.722049 0.092960 0.685569
    outer loop
      vertex -93.081001 -57.012001 4.501000
      vertex -93.732002 -55.881001 3.662000
      vertex -93.877998 -57.014999 3.662000
    endloop
  endfacet
  facet normal -0.929220 -0.040579 0.367292
    outer loop
      vertex -35.158001 -3.938000 3.056000
      vertex -35.034000 -5.103000 3.241000
      vertex -35.018002 -3.994000 3.404000
    endloop
  endfacet
  facet normal -0.148082 -0.356382 0.922531
    outer loop
      vertex -36.369999 15.090000 2.534000
      vertex -36.250000 15.299000 2.634000
      vertex -36.611000 15.449000 2.634000
    endloop
  endfacet
  facet normal -0.602091 -0.787649 0.130751
    outer loop
      vertex -49.707001 16.292999 3.500000
      vertex -49.515999 16.104000 3.241000
      vertex -49.499001 16.134001 3.500000
    endloop
  endfacet
  facet normal -0.279246 -0.279245 0.918719
    outer loop
      vertex -35.909000 14.629000 2.534000
      vertex -35.701000 14.750000 2.634000
      vertex -36.369999 15.090000 2.534000
    endloop
  endfacet
  facet normal -0.372144 -0.486291 0.790588
    outer loop
      vertex -35.938999 15.061000 2.634000
      vertex -35.792000 15.207000 2.793000
      vertex -36.250000 15.299000 2.634000
    endloop
  endfacet
  facet normal -0.353789 -0.855272 0.378607
    outer loop
      vertex -49.566002 16.018000 3.000000
      vertex -49.266998 16.000999 3.241000
      vertex -49.515999 16.104000 3.241000
    endloop
  endfacet
  facet normal -0.485384 -0.372632 0.790915
    outer loop
      vertex -35.938999 15.061000 2.634000
      vertex -35.521000 14.854000 2.793000
      vertex -35.792000 15.207000 2.793000
    endloop
  endfacet
  facet normal -0.267236 0.264744 0.926550
    outer loop
      vertex -36.035999 -56.431000 3.895000
      vertex -35.455002 -56.401001 4.054000
      vertex -35.980000 -55.888000 3.756000
    endloop
  endfacet
  facet normal -0.603742 -0.786699 0.128840
    outer loop
      vertex -49.730999 16.268999 3.241000
      vertex -49.515999 16.104000 3.241000
      vertex -49.707001 16.292999 3.500000
    endloop
  endfacet
  facet normal -0.485007 -0.371161 0.791838
    outer loop
      vertex -35.521000 14.854000 2.793000
      vertex -35.938999 15.061000 2.634000
      vertex -35.701000 14.750000 2.634000
    endloop
  endfacet
  facet normal -0.234658 -0.306634 0.922449
    outer loop
      vertex -36.369999 15.090000 2.534000
      vertex -35.938999 15.061000 2.634000
      vertex -36.250000 15.299000 2.634000
    endloop
  endfacet
  facet normal 0.074823 0.240045 0.967874
    outer loop
      vertex -36.035999 -56.431000 3.895000
      vertex -35.980000 -55.888000 3.756000
      vertex -36.160999 -55.883999 3.769000
    endloop
  endfacet
  facet normal 0.134242 0.251467 0.958511
    outer loop
      vertex -36.222000 -56.426998 3.920000
      vertex -36.035999 -56.431000 3.895000
      vertex -36.160999 -55.883999 3.769000
    endloop
  endfacet
  facet normal -0.233776 -0.178902 0.955690
    outer loop
      vertex -35.701000 14.750000 2.634000
      vertex -35.938999 15.061000 2.634000
      vertex -36.369999 15.090000 2.534000
    endloop
  endfacet
  facet normal -0.673789 0.276659 0.685178
    outer loop
      vertex -92.607002 -55.219002 4.501000
      vertex -93.297997 -54.824001 3.662000
      vertex -93.732002 -55.881001 3.662000
    endloop
  endfacet
  facet normal -0.563425 -0.734165 0.378886
    outer loop
      vertex -49.515999 16.104000 3.241000
      vertex -49.730999 16.268999 3.241000
      vertex -49.566002 16.018000 3.000000
    endloop
  endfacet
  facet normal -0.353945 -0.855116 0.378813
    outer loop
      vertex -49.292999 15.905000 3.000000
      vertex -49.266998 16.000999 3.241000
      vertex -49.566002 16.018000 3.000000
    endloop
  endfacet
  facet normal -0.603689 0.088058 0.792342
    outer loop
      vertex -35.313999 -56.928001 4.220000
      vertex -35.455002 -56.401001 4.054000
      vertex -35.467999 -56.931000 4.103000
    endloop
  endfacet
  facet normal -0.050183 -0.382772 0.922479
    outer loop
      vertex -37.000000 15.259000 2.534000
      vertex -36.611000 15.449000 2.634000
      vertex -37.000000 15.500000 2.634000
    endloop
  endfacet
  facet normal -0.786913 -0.603058 0.130728
    outer loop
      vertex -49.730999 16.268999 3.241000
      vertex -49.865002 16.500000 3.500000
      vertex -49.895000 16.483000 3.241000
    endloop
  endfacet
  facet normal 0.991491 0.130174 0.000000
    outer loop
      vertex -90.499001 -57.000000 5.500000
      vertex -90.464996 -57.258999 5.500000
      vertex -90.499001 -57.000000 0.000000
    endloop
  endfacet
  facet normal -0.788281 -0.601685 0.128795
    outer loop
      vertex -49.730999 16.268999 3.241000
      vertex -49.707001 16.292999 3.500000
      vertex -49.865002 16.500000 3.500000
    endloop
  endfacet
  facet normal -0.034911 -0.130140 0.990881
    outer loop
      vertex -36.500000 14.866000 2.500000
      vertex -36.369999 15.090000 2.534000
      vertex -37.000000 15.259000 2.534000
    endloop
  endfacet
  facet normal 0.991491 -0.130174 0.000000
    outer loop
      vertex -90.499001 -57.000000 0.000000
      vertex -90.464996 -56.741001 0.000000
      vertex -90.464996 -56.741001 5.500000
    endloop
  endfacet
  facet normal 0.991491 -0.130174 0.000000
    outer loop
      vertex -90.464996 -56.741001 5.500000
      vertex -90.499001 -57.000000 5.500000
      vertex -90.499001 -57.000000 0.000000
    endloop
  endfacet
  facet normal -0.562531 -0.734405 0.379748
    outer loop
      vertex -49.566002 16.018000 3.000000
      vertex -49.730999 16.268999 3.241000
      vertex -49.800999 16.198000 3.000000
    endloop
  endfacet
  facet normal 0.923646 -0.383248 0.000000
    outer loop
      vertex -90.464996 -56.741001 5.500000
      vertex -90.464996 -56.741001 0.000000
      vertex -90.364998 -56.500000 0.000000
    endloop
  endfacet
  facet normal -0.095171 -0.095171 0.990901
    outer loop
      vertex -36.369999 15.090000 2.534000
      vertex -36.500000 14.866000 2.500000
      vertex -36.133999 14.500000 2.500000
    endloop
  endfacet
  facet normal -0.095172 -0.095171 0.990901
    outer loop
      vertex -36.133999 14.500000 2.500000
      vertex -35.909000 14.629000 2.534000
      vertex -36.369999 15.090000 2.534000
    endloop
  endfacet
  facet normal -0.310390 0.219617 0.924892
    outer loop
      vertex -35.455002 -56.401001 4.054000
      vertex -35.426998 -55.834999 3.929000
      vertex -35.980000 -55.888000 3.756000
    endloop
  endfacet
  facet normal 0.991491 0.130174 -0.000000
    outer loop
      vertex -90.499001 -57.000000 0.000000
      vertex -90.464996 -57.258999 5.500000
      vertex -90.464996 -57.258999 0.000000
    endloop
  endfacet
  facet normal -0.733061 -0.564611 0.379257
    outer loop
      vertex -49.800999 16.198000 3.000000
      vertex -49.730999 16.268999 3.241000
      vertex -49.981998 16.433001 3.000000
    endloop
  endfacet
  facet normal 0.923646 -0.383248 0.000000
    outer loop
      vertex -90.364998 -56.500000 0.000000
      vertex -90.364998 -56.500000 5.500000
      vertex -90.464996 -56.741001 5.500000
    endloop
  endfacet
  facet normal -0.733692 -0.562272 0.381506
    outer loop
      vertex -49.730999 16.268999 3.241000
      vertex -49.895000 16.483000 3.241000
      vertex -49.981998 16.433001 3.000000
    endloop
  endfacet
  facet normal 0.793058 -0.609146 -0.000000
    outer loop
      vertex -90.364998 -56.500000 0.000000
      vertex -90.206001 -56.292999 0.000000
      vertex -90.206001 -56.292999 5.500000
    endloop
  endfacet
  facet normal 0.793058 -0.609146 -0.000000
    outer loop
      vertex -90.206001 -56.292999 5.500000
      vertex -90.364998 -56.500000 5.500000
      vertex -90.364998 -56.500000 0.000000
    endloop
  endfacet
  facet normal 0.609155 -0.793051 0.000000
    outer loop
      vertex -90.206001 -56.292999 5.500000
      vertex -89.999001 -56.133999 0.000000
      vertex -89.999001 -56.133999 5.500000
    endloop
  endfacet
  facet normal 0.609155 -0.793051 0.000000
    outer loop
      vertex -90.206001 -56.292999 5.500000
      vertex -90.206001 -56.292999 0.000000
      vertex -89.999001 -56.133999 0.000000
    endloop
  endfacet
  facet normal 0.577752 0.443825 0.684997
    outer loop
      vertex -36.708000 -54.811001 3.662000
      vertex -37.966999 -54.466999 4.501000
      vertex -37.396999 -55.209000 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -57.344002 2.923744
      vertex -94.999001 -57.000000 2.954000
      vertex -94.999001 -61.439999 2.567839
    endloop
  endfacet
  facet normal 0.577797 0.443380 0.685248
    outer loop
      vertex -37.966999 -54.466999 4.501000
      vertex -36.708000 -54.811001 3.662000
      vertex -37.403999 -53.903999 3.662000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -57.344002 2.923744
      vertex -94.999001 -57.000000 2.954000
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -51.779999 2.500000
      vertex -94.999001 -8.192000 0.000000
      vertex -94.999001 -82.000000 0.000000
    endloop
  endfacet
  facet normal 0.448528 0.323194 0.833288
    outer loop
      vertex -36.719002 -53.220001 3.028000
      vertex -37.403999 -53.903999 3.662000
      vertex -36.446999 -54.272999 3.290000
    endloop
  endfacet
  facet normal -0.509907 0.209369 0.834362
    outer loop
      vertex -93.732002 -55.881001 3.662000
      vertex -93.297997 -54.824001 3.662000
      vertex -94.667999 -55.633999 3.028000
    endloop
  endfacet
  facet normal -0.546724 0.069921 0.834389
    outer loop
      vertex -93.732002 -55.881001 3.662000
      vertex -94.667999 -55.633999 3.028000
      vertex -94.845001 -57.018002 3.028000
    endloop
  endfacet
  facet normal -0.547087 0.070434 0.834107
    outer loop
      vertex -93.732002 -55.881001 3.662000
      vertex -94.845001 -57.018002 3.028000
      vertex -93.877998 -57.014999 3.662000
    endloop
  endfacet
  facet normal 0.335789 0.437106 0.834376
    outer loop
      vertex -37.403999 -53.903999 3.662000
      vertex -36.719002 -53.220001 3.028000
      vertex -38.310001 -53.208000 3.662000
    endloop
  endfacet
  facet normal 0.453141 0.347723 0.820824
    outer loop
      vertex -36.446999 -54.272999 3.290000
      vertex -37.403999 -53.903999 3.662000
      vertex -36.708000 -54.811001 3.662000
    endloop
  endfacet
  facet normal -0.983155 -0.129416 0.129064
    outer loop
      vertex -35.101002 14.509000 3.241000
      vertex -35.034000 14.000000 3.241000
      vertex -35.000000 14.000000 3.500000
    endloop
  endfacet
  facet normal 0.278500 0.672988 0.685219
    outer loop
      vertex -39.366001 -52.771000 3.662000
      vertex -39.571999 -53.540001 4.501000
      vertex -38.310001 -53.208000 3.662000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -35.068001 14.518000 3.500000
      vertex -35.000000 14.000000 3.500000
      vertex -35.000000 14.000000 10.500000
    endloop
  endfacet
  facet normal -0.983112 -0.129059 0.129749
    outer loop
      vertex -35.101002 14.509000 3.241000
      vertex -35.000000 14.000000 3.500000
      vertex -35.068001 14.518000 3.500000
    endloop
  endfacet
  facet normal -0.427270 0.054644 0.902471
    outer loop
      vertex -94.667999 -55.633999 3.028000
      vertex -94.999001 -57.000000 2.954000
      vertex -94.845001 -57.018002 3.028000
    endloop
  endfacet
  facet normal -0.916893 -0.120694 0.380448
    outer loop
      vertex -35.034000 14.000000 3.241000
      vertex -35.101002 14.509000 3.241000
      vertex -35.133999 14.000000 3.000000
    endloop
  endfacet
  facet normal 0.443622 0.577476 0.685362
    outer loop
      vertex -38.708000 -53.897999 4.501000
      vertex -37.403999 -53.903999 3.662000
      vertex -38.310001 -53.208000 3.662000
    endloop
  endfacet
  facet normal -0.917823 -0.119716 0.378509
    outer loop
      vertex -35.101002 14.509000 3.241000
      vertex -35.196999 14.483000 3.000000
      vertex -35.133999 14.000000 3.000000
    endloop
  endfacet
  facet normal -0.787778 -0.105159 0.606917
    outer loop
      vertex -35.292000 14.000000 2.793000
      vertex -35.196999 14.483000 3.000000
      vertex -35.351002 14.442000 2.793000
    endloop
  endfacet
  facet normal -0.509821 0.209136 0.834473
    outer loop
      vertex -94.138000 -54.341999 3.028000
      vertex -94.667999 -55.633999 3.028000
      vertex -93.297997 -54.824001 3.662000
    endloop
  endfacet
  facet normal -0.303936 -0.734295 0.606988
    outer loop
      vertex -49.646000 15.880000 2.793000
      vertex -49.292999 15.905000 3.000000
      vertex -49.566002 16.018000 3.000000
    endloop
  endfacet
  facet normal -0.790662 -0.103129 0.603504
    outer loop
      vertex -35.196999 14.483000 3.000000
      vertex -35.292000 14.000000 2.793000
      vertex -35.133999 14.000000 3.000000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 0.000000
    outer loop
      vertex -40.241001 -56.034000 0.000000
      vertex -40.241001 -56.034000 5.500000
      vertex -40.500000 -56.000000 0.000000
    endloop
  endfacet
  facet normal -0.605322 -0.080803 0.791869
    outer loop
      vertex -35.292000 14.000000 2.793000
      vertex -35.351002 14.442000 2.793000
      vertex -35.500000 14.000000 2.634000
    endloop
  endfacet
  facet normal -0.483142 -0.630759 0.607221
    outer loop
      vertex -49.646000 15.880000 2.793000
      vertex -49.566002 16.018000 3.000000
      vertex -49.800999 16.198000 3.000000
    endloop
  endfacet
  facet normal -0.607038 -0.079789 0.790657
    outer loop
      vertex -35.500000 14.000000 2.634000
      vertex -35.351002 14.442000 2.793000
      vertex -35.550999 14.388000 2.634000
    endloop
  endfacet
  facet normal -0.383248 -0.923646 0.000000
    outer loop
      vertex -40.241001 -56.034000 0.000000
      vertex -40.000000 -56.133999 0.000000
      vertex -40.241001 -56.034000 5.500000
    endloop
  endfacet
  facet normal -0.321191 -0.085787 0.943121
    outer loop
      vertex -35.741001 14.000000 2.534000
      vertex -35.550999 14.388000 2.634000
      vertex -35.909000 14.629000 2.534000
    endloop
  endfacet
  facet normal -0.382768 -0.050311 0.922474
    outer loop
      vertex -35.741001 14.000000 2.534000
      vertex -35.500000 14.000000 2.634000
      vertex -35.550999 14.388000 2.634000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -39.500000 -57.000000 5.500000
      vertex -39.534000 -56.741001 0.000000
      vertex -39.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal -0.129856 -0.034683 0.990926
    outer loop
      vertex -35.741001 14.000000 2.534000
      vertex -35.909000 14.629000 2.534000
      vertex -36.133999 14.500000 2.500000
    endloop
  endfacet
  facet normal -0.484810 -0.630727 0.605923
    outer loop
      vertex -49.646000 15.880000 2.793000
      vertex -49.800999 16.198000 3.000000
      vertex -49.914001 16.086000 2.793000
    endloop
  endfacet
  facet normal -0.991493 0.130159 -0.000000
    outer loop
      vertex -39.534000 -57.258999 0.000000
      vertex -39.500000 -57.000000 5.500000
      vertex -39.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal -0.130157 -0.991493 0.000000
    outer loop
      vertex -36.481998 15.932000 3.500000
      vertex -36.481998 15.932000 10.500000
      vertex -37.000000 16.000000 10.500000
    endloop
  endfacet
  facet normal -0.129057 -0.983112 0.129747
    outer loop
      vertex -36.481998 15.932000 3.500000
      vertex -37.000000 16.000000 3.500000
      vertex -36.491001 15.899000 3.241000
    endloop
  endfacet
  facet normal -0.129413 -0.983155 0.129064
    outer loop
      vertex -36.491001 15.899000 3.241000
      vertex -37.000000 16.000000 3.500000
      vertex -37.000000 15.966000 3.241000
    endloop
  endfacet
  facet normal -0.120690 -0.916892 0.380451
    outer loop
      vertex -37.000000 15.966000 3.241000
      vertex -37.000000 15.866000 3.000000
      vertex -36.491001 15.899000 3.241000
    endloop
  endfacet
  facet normal 0.331292 0.799518 0.501016
    outer loop
      vertex -87.999001 3.598000 5.500000
      vertex -87.719002 4.108000 4.501000
      vertex -88.723000 3.898000 5.500000
    endloop
  endfacet
  facet normal -0.112858 0.858598 0.500073
    outer loop
      vertex -40.500000 -54.000000 5.500000
      vertex -41.426998 -53.540001 4.501000
      vertex -41.276001 -54.102001 5.500000
    endloop
  endfacet
  facet normal -0.631603 -0.486467 0.603678
    outer loop
      vertex -50.118999 16.354000 2.793000
      vertex -49.800999 16.198000 3.000000
      vertex -49.981998 16.433001 3.000000
    endloop
  endfacet
  facet normal 0.000000 -0.923644 0.383253
    outer loop
      vertex -37.000000 15.966000 3.241000
      vertex -48.999001 15.966000 3.241000
      vertex -37.000000 15.866000 3.000000
    endloop
  endfacet
  facet normal -0.631664 -0.483172 0.606255
    outer loop
      vertex -49.914001 16.086000 2.793000
      vertex -49.800999 16.198000 3.000000
      vertex -50.118999 16.354000 2.793000
    endloop
  endfacet
  facet normal -0.736271 -0.305402 0.603849
    outer loop
      vertex -50.118999 16.354000 2.793000
      vertex -49.981998 16.433001 3.000000
      vertex -50.248001 16.665001 2.793000
    endloop
  endfacet
  facet normal 0.328994 0.801631 0.499150
    outer loop
      vertex -88.723000 3.898000 5.500000
      vertex -87.719002 4.108000 4.501000
      vertex -88.584000 4.463000 4.501000
    endloop
  endfacet
  facet normal -0.331474 0.799988 0.500145
    outer loop
      vertex -41.276001 -54.102001 5.500000
      vertex -41.426998 -53.540001 4.501000
      vertex -42.291000 -53.897999 4.501000
    endloop
  endfacet
  facet normal 0.112788 0.858073 0.500989
    outer loop
      vertex -88.723000 3.898000 5.500000
      vertex -88.584000 4.463000 4.501000
      vertex -89.499001 4.000000 5.500000
    endloop
  endfacet
  facet normal -0.104508 -0.788708 0.605820
    outer loop
      vertex -37.000000 15.707000 2.793000
      vertex -36.516998 15.802000 3.000000
      vertex -37.000000 15.866000 3.000000
    endloop
  endfacet
  facet normal -0.566025 -0.234784 0.790248
    outer loop
      vertex -50.448002 16.612000 2.634000
      vertex -50.118999 16.354000 2.793000
      vertex -50.248001 16.665001 2.793000
    endloop
  endfacet
  facet normal -0.331483 0.799979 0.500153
    outer loop
      vertex -41.276001 -54.102001 5.500000
      vertex -42.291000 -53.897999 4.501000
      vertex -42.000000 -54.402000 5.500000
    endloop
  endfacet
  facet normal -0.079610 -0.607222 0.790534
    outer loop
      vertex -36.611000 15.449000 2.634000
      vertex -37.000000 15.707000 2.793000
      vertex -37.000000 15.500000 2.634000
    endloop
  endfacet
  facet normal 0.110317 0.859363 0.499325
    outer loop
      vertex -89.499001 4.000000 5.500000
      vertex -88.584000 4.463000 4.501000
      vertex -89.511002 4.582000 4.501000
    endloop
  endfacet
  facet normal -0.034861 -0.130078 0.990891
    outer loop
      vertex -37.000000 15.000000 2.500000
      vertex -36.500000 14.866000 2.500000
      vertex -37.000000 15.259000 2.534000
    endloop
  endfacet
  facet normal -0.527396 0.686820 0.500131
    outer loop
      vertex -42.000000 -54.402000 5.500000
      vertex -42.291000 -53.897999 4.501000
      vertex -43.032001 -54.466999 4.501000
    endloop
  endfacet
  facet normal -0.097347 0.721929 0.685086
    outer loop
      vertex -90.438004 4.457000 4.501000
      vertex -89.511002 4.582000 4.501000
      vertex -90.647003 5.225000 3.662000
    endloop
  endfacet
  facet normal -0.527470 0.686703 0.500215
    outer loop
      vertex -42.000000 -54.402000 5.500000
      vertex -43.032001 -54.466999 4.501000
      vertex -42.620998 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.103511 -0.788083 0.606803
    outer loop
      vertex -48.999001 15.707000 2.793000
      vertex -49.292999 15.905000 3.000000
      vertex -49.334000 15.751000 2.793000
    endloop
  endfacet
  facet normal 0.000000 -0.793050 0.609156
    outer loop
      vertex -48.999001 15.707000 2.793000
      vertex -37.000000 15.707000 2.793000
      vertex -37.000000 15.866000 3.000000
    endloop
  endfacet
  facet normal -0.303737 -0.734623 0.606690
    outer loop
      vertex -49.334000 15.751000 2.793000
      vertex -49.292999 15.905000 3.000000
      vertex -49.646000 15.880000 2.793000
    endloop
  endfacet
  facet normal 0.000000 -0.609155 0.793051
    outer loop
      vertex -48.999001 15.707000 2.793000
      vertex -37.000000 15.500000 2.634000
      vertex -37.000000 15.707000 2.793000
    endloop
  endfacet
  facet normal -0.686732 0.527543 0.500098
    outer loop
      vertex -42.620998 -54.879002 5.500000
      vertex -43.032001 -54.466999 4.501000
      vertex -43.602001 -55.209000 4.501000
    endloop
  endfacet
  facet normal -0.079590 -0.607074 0.790649
    outer loop
      vertex -48.999001 15.500000 2.634000
      vertex -49.334000 15.751000 2.793000
      vertex -49.388000 15.551000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -42.000000 -54.402000 5.500000
      vertex -42.620998 -54.879002 5.500000
      vertex -41.000000 -56.133999 5.500000
    endloop
  endfacet
  facet normal 0.924998 0.379973 -0.000000
    outer loop
      vertex -41.465000 -57.258999 0.000000
      vertex -41.465000 -57.258999 5.500000
      vertex -41.366001 -57.500000 5.500000
    endloop
  endfacet
  facet normal 0.990992 0.133918 -0.000000
    outer loop
      vertex -41.465000 -57.258999 0.000000
      vertex -41.500000 -57.000000 5.500000
      vertex -41.465000 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.366001 -57.500000 5.500000
      vertex -41.465000 -57.258999 5.500000
      vertex -43.396999 -57.776001 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.465000 -57.258999 5.500000
      vertex -41.500000 -57.000000 5.500000
      vertex -43.396999 -57.776001 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.130157 0.991493
    outer loop
      vertex -37.000000 15.259000 2.534000
      vertex -48.999001 15.259000 2.534000
      vertex -48.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.500000 -57.000000 5.500000
      vertex -41.465000 -56.741001 5.500000
      vertex -43.396999 -56.223999 5.500000
    endloop
  endfacet
  facet normal -0.234333 -0.566761 0.789854
    outer loop
      vertex -49.334000 15.751000 2.793000
      vertex -49.646000 15.880000 2.793000
      vertex -49.749001 15.701000 2.634000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -43.396999 -57.776001 5.500000
      vertex -43.098000 -58.500000 5.500000
      vertex -41.366001 -57.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.366001 -56.500000 5.500000
      vertex -41.207001 -56.292999 5.500000
      vertex -42.620998 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.371933 -0.486014 0.790858
    outer loop
      vertex -49.749001 15.701000 2.634000
      vertex -49.914001 16.086000 2.793000
      vertex -50.060001 15.939000 2.634000
    endloop
  endfacet
  facet normal -0.373851 -0.486372 0.789733
    outer loop
      vertex -49.914001 16.086000 2.793000
      vertex -49.749001 15.701000 2.634000
      vertex -49.646000 15.880000 2.793000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.465000 -56.741001 5.500000
      vertex -41.366001 -56.500000 5.500000
      vertex -43.396999 -56.223999 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.207001 -56.292999 5.500000
      vertex -41.000000 -56.133999 5.500000
      vertex -42.620998 -54.879002 5.500000
    endloop
  endfacet
  facet normal 0.381896 -0.924205 -0.000000
    outer loop
      vertex -41.000000 -56.133999 5.500000
      vertex -40.757999 -56.034000 0.000000
      vertex -40.757999 -56.034000 5.500000
    endloop
  endfacet
  facet normal -0.794901 0.000000 0.606739
    outer loop
      vertex -35.292000 14.000000 2.793000
      vertex -35.292000 7.103000 2.793000
      vertex -35.133999 7.103000 3.000000
    endloop
  endfacet
  facet normal -0.234869 -0.565250 0.790777
    outer loop
      vertex -49.334000 15.751000 2.793000
      vertex -49.749001 15.701000 2.634000
      vertex -49.388000 15.551000 2.634000
    endloop
  endfacet
  facet normal -0.607308 0.000000 0.794467
    outer loop
      vertex -35.292000 7.103000 2.793000
      vertex -35.292000 14.000000 2.793000
      vertex -35.500000 14.000000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.366001 -56.500000 5.500000
      vertex -42.620998 -54.879002 5.500000
      vertex -43.098000 -55.500000 5.500000
    endloop
  endfacet
  facet normal -0.383253 0.000000 0.923643
    outer loop
      vertex -35.741001 14.000000 2.534000
      vertex -35.741001 7.103000 2.534000
      vertex -35.500000 14.000000 2.634000
    endloop
  endfacet
  facet normal -0.234317 -0.306188 0.922683
    outer loop
      vertex -49.749001 15.701000 2.634000
      vertex -50.060001 15.939000 2.634000
      vertex -50.049999 15.630000 2.534000
    endloop
  endfacet
  facet normal -0.686744 0.527502 0.500124
    outer loop
      vertex -43.602001 -55.209000 4.501000
      vertex -43.098000 -55.500000 5.500000
      vertex -42.620998 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.385026 -0.295423 0.874345
    outer loop
      vertex -50.594002 16.339001 2.534000
      vertex -50.049999 15.630000 2.534000
      vertex -50.060001 15.939000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.500000 14.866000 2.500000
      vertex -37.000000 15.000000 2.500000
      vertex -37.716999 8.053000 2.500000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 0.000000
    outer loop
      vertex -48.999001 16.000000 10.500000
      vertex -49.257999 16.034000 10.500000
      vertex -49.257999 16.034000 3.500000
    endloop
  endfacet
  facet normal -0.799984 0.331472 0.500152
    outer loop
      vertex -43.959999 -56.073002 4.501000
      vertex -43.098000 -55.500000 5.500000
      vertex -43.602001 -55.209000 4.501000
    endloop
  endfacet
  facet normal -0.107895 -0.082785 0.990709
    outer loop
      vertex -50.831001 16.240999 2.500000
      vertex -50.049999 15.630000 2.534000
      vertex -50.594002 16.339001 2.534000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -48.999001 16.000000 10.500000
      vertex -37.000000 16.000000 3.500000
      vertex -37.000000 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.991493 0.130159
    outer loop
      vertex -37.000000 15.966000 3.241000
      vertex -37.000000 16.000000 3.500000
      vertex -48.999001 16.000000 3.500000
    endloop
  endfacet
  facet normal -0.486254 -0.371945 0.790705
    outer loop
      vertex -49.914001 16.086000 2.793000
      vertex -50.118999 16.354000 2.793000
      vertex -50.298000 16.250000 2.634000
    endloop
  endfacet
  facet normal 0.799220 0.334320 0.499477
    outer loop
      vertex -86.901001 2.500000 5.500000
      vertex -86.042000 1.939000 4.501000
      vertex -86.403000 2.802000 4.501000
    endloop
  endfacet
  facet normal -0.800022 0.330396 0.500802
    outer loop
      vertex -43.098000 -55.500000 5.500000
      vertex -43.959999 -56.073002 4.501000
      vertex -43.396999 -56.223999 5.500000
    endloop
  endfacet
  facet normal -0.000000 -0.923644 0.383253
    outer loop
      vertex -48.999001 15.966000 3.241000
      vertex -48.999001 15.866000 3.000000
      vertex -37.000000 15.866000 3.000000
    endloop
  endfacet
  facet normal -0.565882 -0.234484 0.790439
    outer loop
      vertex -50.298000 16.250000 2.634000
      vertex -50.118999 16.354000 2.793000
      vertex -50.448002 16.612000 2.634000
    endloop
  endfacet
  facet normal -0.000000 -0.793050 0.609156
    outer loop
      vertex -48.999001 15.707000 2.793000
      vertex -37.000000 15.866000 3.000000
      vertex -48.999001 15.866000 3.000000
    endloop
  endfacet
  facet normal -0.486290 -0.372144 0.790589
    outer loop
      vertex -50.060001 15.939000 2.634000
      vertex -49.914001 16.086000 2.793000
      vertex -50.298000 16.250000 2.634000
    endloop
  endfacet
  facet normal 0.686169 0.527054 0.501384
    outer loop
      vertex -86.901001 2.500000 5.500000
      vertex -86.403000 2.802000 4.501000
      vertex -87.377998 3.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.130157 0.991493
    outer loop
      vertex -48.999001 15.000000 2.500000
      vertex -37.000000 15.000000 2.500000
      vertex -37.000000 15.259000 2.534000
    endloop
  endfacet
  facet normal -0.858434 0.113942 0.500109
    outer loop
      vertex -43.396999 -56.223999 5.500000
      vertex -44.082001 -57.000000 4.501000
      vertex -43.500000 -57.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.000000 15.000000 2.500000
      vertex -48.999001 15.000000 2.500000
      vertex -43.472000 7.976000 2.500000
    endloop
  endfacet
  facet normal -0.858434 -0.113942 0.500109
    outer loop
      vertex -43.500000 -57.000000 5.500000
      vertex -44.082001 -57.000000 4.501000
      vertex -43.396999 -57.776001 5.500000
    endloop
  endfacet
  facet normal -0.384073 -0.293920 0.875271
    outer loop
      vertex -50.060001 15.939000 2.634000
      vertex -50.298000 16.250000 2.634000
      vertex -50.594002 16.339001 2.534000
    endloop
  endfacet
  facet normal 0.685144 0.530314 0.499344
    outer loop
      vertex -87.377998 3.121000 5.500000
      vertex -86.403000 2.802000 4.501000
      vertex -86.974998 3.541000 4.501000
    endloop
  endfacet
  facet normal -0.356097 -0.147556 0.922725
    outer loop
      vertex -50.298000 16.250000 2.634000
      vertex -50.448002 16.612000 2.634000
      vertex -50.594002 16.339001 2.534000
    endloop
  endfacet
  facet normal -0.858206 0.112948 0.500725
    outer loop
      vertex -43.396999 -56.223999 5.500000
      vertex -43.959999 -56.073002 4.501000
      vertex -44.082001 -57.000000 4.501000
    endloop
  endfacet
  facet normal 0.527131 0.686268 0.501167
    outer loop
      vertex -87.377998 3.121000 5.500000
      vertex -86.974998 3.541000 4.501000
      vertex -87.999001 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.858206 -0.112948 0.500725
    outer loop
      vertex -43.396999 -57.776001 5.500000
      vertex -44.082001 -57.000000 4.501000
      vertex -43.959999 -57.926998 4.501000
    endloop
  endfacet
  facet normal 0.000000 -0.609155 0.793051
    outer loop
      vertex -48.999001 15.500000 2.634000
      vertex -37.000000 15.500000 2.634000
      vertex -48.999001 15.707000 2.793000
    endloop
  endfacet
  facet normal 0.525254 0.689226 0.499075
    outer loop
      vertex -87.999001 3.598000 5.500000
      vertex -86.974998 3.541000 4.501000
      vertex -87.719002 4.108000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.366001 -56.500000 5.500000
      vertex -43.098000 -55.500000 5.500000
      vertex -43.396999 -56.223999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -43.396999 -56.223999 5.500000
      vertex -43.500000 -57.000000 5.500000
      vertex -41.500000 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -43.500000 -57.000000 5.500000
      vertex -43.396999 -57.776001 5.500000
      vertex -41.500000 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.380532 -0.084626 0.920888
    outer loop
      vertex -50.594002 16.339001 2.534000
      vertex -50.499001 17.000000 2.634000
      vertex -50.741001 17.000000 2.534000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 0.000000
    outer loop
      vertex -49.257999 16.034000 3.500000
      vertex -48.999001 16.000000 3.500000
      vertex -48.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal -0.044944 0.340150 0.939296
    outer loop
      vertex -40.500000 -51.653999 3.028000
      vertex -40.500000 -50.566002 2.634000
      vertex -42.165001 -50.785999 2.634000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -48.999001 16.000000 3.500000
      vertex -37.000000 16.000000 3.500000
      vertex -48.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal -0.128403 -0.983199 0.129737
    outer loop
      vertex -48.999001 15.966000 3.241000
      vertex -49.257999 16.034000 3.500000
      vertex -49.266998 16.000999 3.241000
    endloop
  endfacet
  facet normal -0.129071 -0.983200 0.129070
    outer loop
      vertex -49.257999 16.034000 3.500000
      vertex -48.999001 15.966000 3.241000
      vertex -48.999001 16.000000 3.500000
    endloop
  endfacet
  facet normal -0.278500 0.672987 0.685220
    outer loop
      vertex -41.632999 -52.771000 3.662000
      vertex -42.688999 -53.208000 3.662000
      vertex -41.426998 -53.540001 4.501000
    endloop
  endfacet
  facet normal -0.130204 -0.028956 0.991064
    outer loop
      vertex -50.831001 16.240999 2.500000
      vertex -50.594002 16.339001 2.534000
      vertex -50.741001 17.000000 2.534000
    endloop
  endfacet
  facet normal -0.112630 0.857974 0.501194
    outer loop
      vertex -89.511002 4.582000 4.501000
      vertex -90.276001 3.898000 5.500000
      vertex -89.499001 4.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 1.966000 5.500000
      vertex -89.499001 2.000000 5.500000
      vertex -89.499001 4.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 4.000000 5.500000
      vertex -90.276001 3.898000 5.500000
      vertex -89.758003 1.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.999001 3.598000 5.500000
      vertex -88.723000 3.898000 5.500000
      vertex -89.239998 1.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.723000 3.898000 5.500000
      vertex -89.499001 4.000000 5.500000
      vertex -89.239998 1.966000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -89.239998 1.966000 5.500000
      vertex -88.999001 1.866000 5.500000
      vertex -87.999001 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.002139 0.158763 0.987314
    outer loop
      vertex -42.527000 -49.759998 2.500000
      vertex -40.500000 -50.566002 2.634000
      vertex -38.667999 -49.708000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.991493 0.130159
    outer loop
      vertex -48.999001 16.000000 3.500000
      vertex -48.999001 15.966000 3.241000
      vertex -37.000000 15.966000 3.241000
    endloop
  endfacet
  facet normal -0.131288 0.317177 0.939235
    outer loop
      vertex -43.716000 -51.428001 2.634000
      vertex -41.882999 -51.835999 3.028000
      vertex -42.165001 -50.785999 2.634000
    endloop
  endfacet
  facet normal -0.119757 -0.916996 0.380494
    outer loop
      vertex -48.999001 15.966000 3.241000
      vertex -49.266998 16.000999 3.241000
      vertex -48.999001 15.866000 3.000000
    endloop
  endfacet
  facet normal -0.121711 -0.917517 0.378614
    outer loop
      vertex -48.999001 15.866000 3.000000
      vertex -49.266998 16.000999 3.241000
      vertex -49.292999 15.905000 3.000000
    endloop
  endfacet
  facet normal -0.044796 0.340398 0.939214
    outer loop
      vertex -42.165001 -50.785999 2.634000
      vertex -41.882999 -51.835999 3.028000
      vertex -40.500000 -51.653999 3.028000
    endloop
  endfacet
  facet normal 0.722499 -0.092651 0.685136
    outer loop
      vertex -85.917000 1.012000 4.501000
      vertex -86.036003 0.084000 4.501000
      vertex -85.121002 1.015000 3.662000
    endloop
  endfacet
  facet normal -0.034699 -0.098299 0.994552
    outer loop
      vertex -49.999001 15.268000 2.500000
      vertex -48.999001 15.259000 2.534000
      vertex -50.049999 15.630000 2.534000
    endloop
  endfacet
  facet normal -0.129580 -0.110802 0.985359
    outer loop
      vertex -49.999001 15.268000 2.500000
      vertex -50.049999 15.630000 2.534000
      vertex -50.831001 16.240999 2.500000
    endloop
  endfacet
  facet normal -0.104622 -0.788698 0.605813
    outer loop
      vertex -49.292999 15.905000 3.000000
      vertex -48.999001 15.707000 2.793000
      vertex -48.999001 15.866000 3.000000
    endloop
  endfacet
  facet normal 0.801502 -0.328936 0.499395
    outer loop
      vertex -86.390999 -0.781000 4.501000
      vertex -86.036003 0.084000 4.501000
      vertex -86.600998 0.224000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.999001 15.268000 2.500000
      vertex -50.831001 16.240999 2.500000
      vertex -81.975998 1.948000 2.500000
    endloop
  endfacet
  facet normal -0.484836 -0.630953 0.605667
    outer loop
      vertex -34.620998 -83.621002 2.793000
      vertex -34.146000 -83.986000 2.793000
      vertex -34.067001 -83.848000 3.000000
    endloop
  endfacet
  facet normal -0.079755 -0.607215 0.790525
    outer loop
      vertex -48.999001 15.707000 2.793000
      vertex -49.334000 15.751000 2.793000
      vertex -48.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal -0.130407 -0.991461 0.000000
    outer loop
      vertex -33.516998 -83.931999 3.500000
      vertex -33.000000 -84.000000 3.500000
      vertex -33.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal 0.858026 -0.112779 0.501070
    outer loop
      vertex -86.600998 0.224000 5.500000
      vertex -86.036003 0.084000 4.501000
      vertex -86.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.412230 -0.696606 0.587202
    outer loop
      vertex -34.057999 -84.000000 2.826000
      vertex -33.526001 -83.964996 3.241000
      vertex -34.067001 -83.848000 3.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -79.999001 15.268000 2.500000
      vertex -82.903000 4.617000 2.500000
      vertex -50.831001 16.240999 2.500000
    endloop
  endfacet
  facet normal 0.859373 -0.110203 0.499333
    outer loop
      vertex -86.036003 0.084000 4.501000
      vertex -85.917000 1.012000 4.501000
      vertex -86.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.050183 -0.382772 0.922479
    outer loop
      vertex -49.388000 15.551000 2.634000
      vertex -48.999001 15.259000 2.534000
      vertex -48.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal -0.129305 -0.983081 0.129741
    outer loop
      vertex -33.526001 -83.964996 3.241000
      vertex -33.000000 -84.000000 3.500000
      vertex -33.516998 -83.931999 3.500000
    endloop
  endfacet
  facet normal -0.257280 -0.877898 0.403860
    outer loop
      vertex -33.000000 -84.000000 3.500000
      vertex -33.526001 -83.964996 3.241000
      vertex -34.057999 -84.000000 2.826000
    endloop
  endfacet
  facet normal -0.245178 -0.590061 0.769231
    outer loop
      vertex -48.999001 15.259000 2.534000
      vertex -49.388000 15.551000 2.634000
      vertex -49.749001 15.701000 2.634000
    endloop
  endfacet
  facet normal -0.342011 -0.716392 0.608120
    outer loop
      vertex -34.146000 -83.986000 2.793000
      vertex -34.057999 -84.000000 2.826000
      vertex -34.067001 -83.848000 3.000000
    endloop
  endfacet
  facet normal -0.370495 -0.181817 0.910866
    outer loop
      vertex -34.146000 -83.986000 2.793000
      vertex -34.620998 -84.000000 2.597000
      vertex -34.057999 -84.000000 2.826000
    endloop
  endfacet
  facet normal -0.923646 0.383248 0.000000
    outer loop
      vertex -94.931000 83.517998 10.500000
      vertex -94.731003 84.000000 10.500000
      vertex -94.731003 84.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 -0.383255 0.923643
    outer loop
      vertex -48.999001 15.500000 2.634000
      vertex -48.999001 15.259000 2.534000
      vertex -37.000000 15.259000 2.534000
    endloop
  endfacet
  facet normal -0.793051 0.609155 0.000000
    outer loop
      vertex -94.731003 84.000000 10.500000
      vertex -94.413002 84.414001 10.500000
      vertex -94.731003 84.000000 0.000000
    endloop
  endfacet
  facet normal -0.034861 -0.130078 0.990891
    outer loop
      vertex -48.999001 15.259000 2.534000
      vertex -49.999001 15.268000 2.500000
      vertex -48.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal -0.609155 0.793051 0.000000
    outer loop
      vertex -94.413002 84.414001 10.500000
      vertex -93.999001 84.732002 10.500000
      vertex -93.999001 84.732002 0.000000
    endloop
  endfacet
  facet normal -0.383248 0.923646 0.000000
    outer loop
      vertex -93.516998 84.931999 10.500000
      vertex -93.999001 84.732002 0.000000
      vertex -93.999001 84.732002 10.500000
    endloop
  endfacet
  facet normal -0.170899 -0.484137 0.858141
    outer loop
      vertex -48.999001 15.259000 2.534000
      vertex -49.749001 15.701000 2.634000
      vertex -50.049999 15.630000 2.534000
    endloop
  endfacet
  facet normal -0.000000 -0.383255 0.923643
    outer loop
      vertex -37.000000 15.259000 2.534000
      vertex -37.000000 15.500000 2.634000
      vertex -48.999001 15.500000 2.634000
    endloop
  endfacet
  facet normal -0.991493 0.130159 -0.000000
    outer loop
      vertex -94.931000 83.517998 0.000000
      vertex -94.999001 83.000000 0.000000
      vertex -94.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal -0.991493 0.130159 -0.000000
    outer loop
      vertex -94.999001 83.000000 10.500000
      vertex -94.931000 83.517998 10.500000
      vertex -94.931000 83.517998 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -47.028000 4.730000 2.500000
      vertex -49.999001 15.268000 2.500000
      vertex -81.975998 1.948000 2.500000
    endloop
  endfacet
  facet normal -0.923646 0.383248 0.000000
    outer loop
      vertex -94.931000 83.517998 10.500000
      vertex -94.731003 84.000000 0.000000
      vertex -94.931000 83.517998 0.000000
    endloop
  endfacet
  facet normal -0.793051 0.609155 0.000000
    outer loop
      vertex -94.731003 84.000000 0.000000
      vertex -94.413002 84.414001 10.500000
      vertex -94.413002 84.414001 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -47.028000 4.730000 2.500000
      vertex -48.999001 15.000000 2.500000
      vertex -49.999001 15.268000 2.500000
    endloop
  endfacet
  facet normal -0.609155 0.793051 0.000000
    outer loop
      vertex -94.413002 84.414001 10.500000
      vertex -93.999001 84.732002 0.000000
      vertex -94.413002 84.414001 0.000000
    endloop
  endfacet
  facet normal -0.383248 0.923646 0.000000
    outer loop
      vertex -93.999001 84.732002 0.000000
      vertex -93.516998 84.931999 10.500000
      vertex -93.516998 84.931999 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -43.472000 7.976000 2.500000
      vertex -37.716999 8.053000 2.500000
      vertex -37.000000 15.000000 2.500000
    endloop
  endfacet
  facet normal -0.130159 0.991493 0.000000
    outer loop
      vertex -93.516998 84.931999 0.000000
      vertex -93.516998 84.931999 10.500000
      vertex -92.999001 85.000000 10.500000
    endloop
  endfacet
  facet normal -0.130159 0.991493 0.000000
    outer loop
      vertex -92.999001 85.000000 10.500000
      vertex -92.999001 85.000000 0.000000
      vertex -93.516998 84.931999 0.000000
    endloop
  endfacet
  facet normal -0.372840 -0.485204 0.790928
    outer loop
      vertex -34.766998 -83.767998 2.634000
      vertex -34.146000 -83.986000 2.793000
      vertex -34.620998 -83.621002 2.793000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 83.000000 2.500000
      vertex -92.999001 19.000000 2.500000
      vertex -80.999001 19.000000 2.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 19.000000 2.500000
      vertex -92.999001 83.000000 2.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -92.999001 83.000000 10.500000
      vertex -92.999001 18.000000 10.500000
      vertex -92.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal -0.347313 -0.356867 0.867191
    outer loop
      vertex -34.766998 -83.767998 2.634000
      vertex -34.620998 -84.000000 2.597000
      vertex -34.146000 -83.986000 2.793000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 18.000000 3.500000
      vertex -94.999001 18.000000 10.500000
      vertex -94.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.799383 -0.331240 0.501266
    outer loop
      vertex -86.901001 -58.500000 5.500000
      vertex -86.390999 -58.780998 4.501000
      vertex -86.600998 -57.776001 5.500000
    endloop
  endfacet
  facet normal -0.991244 -0.132039 -0.000000
    outer loop
      vertex -35.000000 -82.000000 3.500000
      vertex -34.931000 -82.517998 3.500000
      vertex -34.931000 -82.517998 10.500000
    endloop
  endfacet
  facet normal -0.991244 -0.132039 -0.000000
    outer loop
      vertex -34.931000 -82.517998 10.500000
      vertex -35.000000 -82.000000 10.500000
      vertex -35.000000 -82.000000 3.500000
    endloop
  endfacet
  facet normal 0.801502 -0.328937 0.499395
    outer loop
      vertex -86.600998 -57.776001 5.500000
      vertex -86.390999 -58.780998 4.501000
      vertex -86.036003 -57.916000 4.501000
    endloop
  endfacet
  facet normal -0.922998 -0.037426 0.382981
    outer loop
      vertex -35.133999 -5.103000 3.000000
      vertex -35.034000 -5.103000 3.241000
      vertex -35.158001 -3.938000 3.056000
    endloop
  endfacet
  facet normal -0.794078 -0.045495 0.606111
    outer loop
      vertex -35.133999 -5.103000 3.000000
      vertex -35.158001 -3.938000 3.056000
      vertex -35.292000 -5.103000 2.793000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -87.377998 -59.120998 5.500000
      vertex -86.901001 -58.500000 5.500000
      vertex -88.633003 -57.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -86.901001 -58.500000 5.500000
      vertex -86.600998 -57.776001 5.500000
      vertex -88.532997 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 -57.258999 5.500000
      vertex -88.633003 -57.500000 5.500000
      vertex -86.901001 -58.500000 5.500000
    endloop
  endfacet
  facet normal -0.605457 -0.078005 0.792046
    outer loop
      vertex -35.292000 -5.103000 2.793000
      vertex -35.583000 -3.880000 2.691000
      vertex -35.500000 -5.103000 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -86.600998 -57.776001 5.500000
      vertex -86.499001 -57.000000 5.500000
      vertex -88.532997 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.633003 -57.500000 5.500000
      vertex -88.792000 -57.707001 5.500000
      vertex -87.377998 -59.120998 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.792000 -57.707001 5.500000
      vertex -88.999001 -57.866001 5.500000
      vertex -87.377998 -59.120998 5.500000
    endloop
  endfacet
  facet normal -0.924320 -0.381618 -0.000000
    outer loop
      vertex -34.931000 -82.517998 10.500000
      vertex -34.931000 -82.517998 3.500000
      vertex -34.731998 -83.000000 10.500000
    endloop
  endfacet
  facet normal -0.000000 1.000000 0.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -80.999001 18.000000 10.500000
      vertex -80.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 83.000000 2.500000
      vertex -80.999001 19.000000 2.500000
      vertex -80.482002 18.931999 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.999001 -57.866001 5.500000
      vertex -89.239998 -57.966000 5.500000
      vertex -87.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal -0.982957 -0.130936 0.129038
    outer loop
      vertex -35.034000 -82.000000 3.241000
      vertex -34.931000 -82.517998 3.500000
      vertex -35.000000 -82.000000 3.500000
    endloop
  endfacet
  facet normal -0.000000 -0.000000 1.000000
    outer loop
      vertex -80.482002 18.931999 2.500000
      vertex -79.426003 18.207001 2.500000
      vertex -92.999001 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 -58.000000 5.500000
      vertex -89.758003 -57.966000 5.500000
      vertex -89.499001 -60.000000 5.500000
    endloop
  endfacet
  facet normal -0.854190 -0.353158 0.381626
    outer loop
      vertex -34.964001 -82.526001 3.241000
      vertex -34.848000 -83.067001 3.000000
      vertex -34.761002 -83.016998 3.241000
    endloop
  endfacet
  facet normal 0.050313 0.382770 0.922472
    outer loop
      vertex -80.611000 18.448999 2.634000
      vertex -80.999001 18.740999 2.534000
      vertex -80.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 -57.966000 5.500000
      vertex -89.999001 -57.866001 5.500000
      vertex -90.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.999001 -57.866001 5.500000
      vertex -91.620003 -59.120998 5.500000
      vertex -90.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.383256 0.923642
    outer loop
      vertex -80.999001 18.500000 2.634000
      vertex -80.999001 18.740999 2.534000
      vertex -92.999001 18.740999 2.534000
    endloop
  endfacet
  facet normal 0.000000 0.383256 0.923642
    outer loop
      vertex -92.999001 18.740999 2.534000
      vertex -92.999001 18.500000 2.634000
      vertex -80.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 0.007355 0.055916 0.998408
    outer loop
      vertex -80.482002 18.931999 2.500000
      vertex -80.999001 19.000000 2.500000
      vertex -79.767998 18.231001 2.534000
    endloop
  endfacet
  facet normal -0.609155 0.793051 0.000000
    outer loop
      vertex -88.792000 -57.707001 5.500000
      vertex -88.999001 -57.866001 0.000000
      vertex -88.999001 -57.866001 5.500000
    endloop
  endfacet
  facet normal -0.916745 -0.122000 0.380387
    outer loop
      vertex -34.964001 -82.526001 3.241000
      vertex -35.034000 -82.000000 3.241000
      vertex -35.133999 -82.000000 3.000000
    endloop
  endfacet
  facet normal -0.982942 -0.130809 0.129285
    outer loop
      vertex -34.931000 -82.517998 3.500000
      vertex -35.034000 -82.000000 3.241000
      vertex -34.964001 -82.526001 3.241000
    endloop
  endfacet
  facet normal -0.383253 0.923643 0.000000
    outer loop
      vertex -89.239998 -57.966000 0.000000
      vertex -89.239998 -57.966000 5.500000
      vertex -88.999001 -57.866001 5.500000
    endloop
  endfacet
  facet normal -0.383253 0.923643 0.000000
    outer loop
      vertex -88.999001 -57.866001 5.500000
      vertex -88.999001 -57.866001 0.000000
      vertex -89.239998 -57.966000 0.000000
    endloop
  endfacet
  facet normal -0.130158 0.991493 -0.000000
    outer loop
      vertex -89.499001 -58.000000 5.500000
      vertex -89.239998 -57.966000 5.500000
      vertex -89.239998 -57.966000 0.000000
    endloop
  endfacet
  facet normal 0.130158 0.991493 0.000000
    outer loop
      vertex -89.499001 -58.000000 5.500000
      vertex -89.758003 -57.966000 0.000000
      vertex -89.758003 -57.966000 5.500000
    endloop
  endfacet
  facet normal 0.383253 0.923643 -0.000000
    outer loop
      vertex -89.999001 -57.866001 5.500000
      vertex -89.758003 -57.966000 5.500000
      vertex -89.758003 -57.966000 0.000000
    endloop
  endfacet
  facet normal -0.794901 0.000000 0.606739
    outer loop
      vertex -35.133999 -82.000000 3.000000
      vertex -35.292000 -63.103001 2.793000
      vertex -35.292000 -82.000000 2.793000
    endloop
  endfacet
  facet normal 0.000000 0.130157 0.991493
    outer loop
      vertex -80.999001 19.000000 2.500000
      vertex -92.999001 18.740999 2.534000
      vertex -80.999001 18.740999 2.534000
    endloop
  endfacet
  facet normal -0.916246 -0.121167 0.381853
    outer loop
      vertex -35.061001 -82.552002 3.000000
      vertex -34.964001 -82.526001 3.241000
      vertex -35.133999 -82.000000 3.000000
    endloop
  endfacet
  facet normal -0.607308 0.000000 0.794467
    outer loop
      vertex -35.292000 -63.103001 2.793000
      vertex -35.500000 -82.000000 2.634000
      vertex -35.292000 -82.000000 2.793000
    endloop
  endfacet
  facet normal -0.605379 -0.079627 0.791944
    outer loop
      vertex -35.292000 -82.000000 2.793000
      vertex -35.500000 -82.000000 2.634000
      vertex -35.214001 -82.593002 2.793000
    endloop
  endfacet
  facet normal -0.789778 -0.104442 0.604435
    outer loop
      vertex -35.133999 -82.000000 3.000000
      vertex -35.214001 -82.593002 2.793000
      vertex -35.061001 -82.552002 3.000000
    endloop
  endfacet
  facet normal -0.736173 -0.304478 0.604435
    outer loop
      vertex -35.214001 -82.593002 2.793000
      vertex -34.848000 -83.067001 3.000000
      vertex -35.061001 -82.552002 3.000000
    endloop
  endfacet
  facet normal 0.112774 -0.857959 0.501187
    outer loop
      vertex -89.499001 -60.000000 5.500000
      vertex -89.487000 -60.582001 4.501000
      vertex -88.723000 -59.897999 5.500000
    endloop
  endfacet
  facet normal -0.790591 -0.103988 0.603450
    outer loop
      vertex -35.214001 -82.593002 2.793000
      vertex -35.133999 -82.000000 3.000000
      vertex -35.292000 -82.000000 2.793000
    endloop
  endfacet
  facet normal 0.115781 -0.858631 0.499348
    outer loop
      vertex -88.723000 -59.897999 5.500000
      vertex -89.487000 -60.582001 4.501000
      vertex -88.559998 -60.457001 4.501000
    endloop
  endfacet
  facet normal 0.331222 -0.799350 0.501329
    outer loop
      vertex -88.723000 -59.897999 5.500000
      vertex -88.559998 -60.457001 4.501000
      vertex -87.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal -0.382757 -0.050875 0.922447
    outer loop
      vertex -35.500000 -82.000000 2.634000
      vertex -35.741001 -82.000000 2.534000
      vertex -35.414001 -82.647003 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -79.426003 18.207001 2.500000
      vertex -79.032997 17.259001 2.500000
      vertex -50.831001 17.759001 2.500000
    endloop
  endfacet
  facet normal -0.606841 -0.080660 0.790720
    outer loop
      vertex -35.414001 -82.647003 2.634000
      vertex -35.214001 -82.593002 2.793000
      vertex -35.500000 -82.000000 2.634000
    endloop
  endfacet
  facet normal 0.334701 -0.799203 0.499249
    outer loop
      vertex -88.559998 -60.457001 4.501000
      vertex -87.697998 -60.096001 4.501000
      vertex -87.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal 0.108675 0.158291 0.981394
    outer loop
      vertex -80.482002 18.931999 2.500000
      vertex -79.767998 18.231001 2.534000
      vertex -79.426003 18.207001 2.500000
    endloop
  endfacet
  facet normal 0.101772 0.042191 0.993913
    outer loop
      vertex -79.426003 18.207001 2.500000
      vertex -79.767998 18.231001 2.534000
      vertex -79.032997 17.259001 2.500000
    endloop
  endfacet
  facet normal 0.527195 -0.686349 0.500990
    outer loop
      vertex -87.999001 -59.598000 5.500000
      vertex -87.697998 -60.096001 4.501000
      vertex -87.377998 -59.120998 5.500000
    endloop
  endfacet
  facet normal 0.445203 -0.575958 0.685614
    outer loop
      vertex -86.958000 -59.523998 4.501000
      vertex -87.697998 -60.096001 4.501000
      vertex -86.392998 -60.085999 3.662000
    endloop
  endfacet
  facet normal -0.130138 -0.017254 0.991346
    outer loop
      vertex -35.741001 -82.000000 2.534000
      vertex -36.000000 -82.000000 2.500000
      vertex -35.646999 -82.709000 2.534000
    endloop
  endfacet
  facet normal 0.529881 -0.685506 0.499307
    outer loop
      vertex -87.377998 -59.120998 5.500000
      vertex -87.697998 -60.096001 4.501000
      vertex -86.958000 -59.523998 4.501000
    endloop
  endfacet
  facet normal -0.188291 -0.046704 0.981002
    outer loop
      vertex -35.646999 -82.709000 2.534000
      vertex -36.000000 -82.000000 2.500000
      vertex -35.652000 -83.403000 2.500000
    endloop
  endfacet
  facet normal 0.916996 -0.119770 0.380491
    outer loop
      vertex -79.864998 17.000000 3.000000
      vertex -79.964996 17.000000 3.241000
      vertex -80.000000 16.732000 3.241000
    endloop
  endfacet
  facet normal -0.382467 -0.050709 0.922577
    outer loop
      vertex -35.414001 -82.647003 2.634000
      vertex -35.741001 -82.000000 2.534000
      vertex -35.646999 -82.709000 2.534000
    endloop
  endfacet
  facet normal 0.686268 -0.527132 0.501167
    outer loop
      vertex -87.377998 -59.120998 5.500000
      vertex -86.958000 -59.523998 4.501000
      vertex -86.901001 -58.500000 5.500000
    endloop
  endfacet
  facet normal 0.787595 0.104838 0.607209
    outer loop
      vertex -79.864998 17.000000 3.000000
      vertex -79.750000 17.334999 2.793000
      vertex -79.903999 17.292999 3.000000
    endloop
  endfacet
  facet normal 0.688719 -0.525578 0.499434
    outer loop
      vertex -86.901001 -58.500000 5.500000
      vertex -86.958000 -59.523998 4.501000
      vertex -86.390999 -58.780998 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 -60.000000 5.500000
      vertex -88.723000 -59.897999 5.500000
      vertex -89.239998 -57.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.239998 -57.966000 5.500000
      vertex -89.499001 -58.000000 5.500000
      vertex -89.499001 -60.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.239998 -57.966000 5.500000
      vertex -88.723000 -59.897999 5.500000
      vertex -87.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -87.999001 -59.598000 5.500000
      vertex -87.377998 -59.120998 5.500000
      vertex -88.999001 -57.866001 5.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex 80.000000 83.000000 2.500000
      vertex 80.000000 -82.000000 10.500000
      vertex 80.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.722369 -0.092364 0.685312
    outer loop
      vertex -85.121002 -56.985001 3.662000
      vertex -86.036003 -57.916000 4.501000
      vertex -85.265999 -58.118999 3.662000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex 80.000000 83.000000 2.500000
      vertex 25.000000 83.000000 10.500000
      vertex 25.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.673764 -0.276513 0.685260
    outer loop
      vertex -85.265999 -58.118999 3.662000
      vertex -86.036003 -57.916000 4.501000
      vertex -86.390999 -58.780998 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.000000 -82.000000 2.500000
      vertex -92.999001 -84.000000 2.500000
      vertex -35.652000 -83.403000 2.500000
    endloop
  endfacet
  facet normal 0.587658 0.243495 0.771601
    outer loop
      vertex -79.767998 18.231001 2.534000
      vertex -79.699997 17.750000 2.634000
      vertex -79.550003 17.388000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 -82.000000 2.500000
      vertex 80.000000 -82.000000 2.500000
      vertex 80.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 83.000000 2.500000
      vertex 25.000000 -82.000000 2.500000
      vertex 80.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.722499 -0.092650 0.685136
    outer loop
      vertex -85.917000 -56.987999 4.501000
      vertex -86.036003 -57.916000 4.501000
      vertex -85.121002 -56.985001 3.662000
    endloop
  endfacet
  facet normal 0.546712 -0.069904 0.834398
    outer loop
      vertex -85.121002 -56.985001 3.662000
      vertex -85.265999 -58.118999 3.662000
      vertex -84.153000 -56.981998 3.028000
    endloop
  endfacet
  facet normal -0.802468 -0.042069 0.595210
    outer loop
      vertex -35.292000 -5.103000 2.793000
      vertex -35.158001 -3.938000 3.056000
      vertex -35.238998 -3.921000 2.948000
    endloop
  endfacet
  facet normal -0.602607 -0.077138 0.794301
    outer loop
      vertex -35.583000 -3.880000 2.691000
      vertex -35.292000 -5.103000 2.793000
      vertex -35.238998 -3.921000 2.948000
    endloop
  endfacet
  facet normal 0.547032 -0.070356 0.834150
    outer loop
      vertex -84.153000 -56.981998 3.028000
      vertex -85.265999 -58.118999 3.662000
      vertex -84.331001 -58.366001 3.028000
    endloop
  endfacet
  facet normal -0.128864 -0.140633 0.981640
    outer loop
      vertex -35.741001 -5.103000 2.534000
      vertex -36.209000 -3.327000 2.727000
      vertex -36.000000 -5.103000 2.500000
    endloop
  endfacet
  facet normal 0.673788 -0.276654 0.685181
    outer loop
      vertex -85.699997 -59.175999 3.662000
      vertex -85.265999 -58.118999 3.662000
      vertex -86.390999 -58.780998 4.501000
    endloop
  endfacet
  facet normal 0.917629 -0.122147 0.378202
    outer loop
      vertex -79.903999 16.707001 3.000000
      vertex -79.864998 17.000000 3.000000
      vertex -80.000000 16.732000 3.241000
    endloop
  endfacet
  facet normal -0.382343 -0.068894 0.921449
    outer loop
      vertex -35.741001 -5.103000 2.534000
      vertex -35.500000 -5.103000 2.634000
      vertex -35.583000 -3.880000 2.691000
    endloop
  endfacet
  facet normal 0.510250 -0.209506 0.834118
    outer loop
      vertex -84.331001 -58.366001 3.028000
      vertex -85.265999 -58.118999 3.662000
      vertex -85.699997 -59.175999 3.662000
    endloop
  endfacet
  facet normal 0.788790 0.103600 0.605869
    outer loop
      vertex -79.706001 17.000000 2.793000
      vertex -79.750000 17.334999 2.793000
      vertex -79.864998 17.000000 3.000000
    endloop
  endfacet
  facet normal -0.991493 0.000000 0.130159
    outer loop
      vertex -35.034000 -5.103000 3.241000
      vertex -35.034000 -50.896999 3.241000
      vertex -35.000000 -5.103000 3.500000
    endloop
  endfacet
  facet normal 0.607291 0.079762 0.790465
    outer loop
      vertex -79.550003 17.388000 2.634000
      vertex -79.750000 17.334999 2.793000
      vertex -79.706001 17.000000 2.793000
    endloop
  endfacet
  facet normal -0.794901 0.000000 0.606739
    outer loop
      vertex -35.292000 -5.103000 2.793000
      vertex -35.292000 -50.896999 2.793000
      vertex -35.133999 -50.896999 3.000000
    endloop
  endfacet
  facet normal -0.607308 -0.000000 0.794467
    outer loop
      vertex -35.292000 -5.103000 2.793000
      vertex -35.500000 -5.103000 2.634000
      vertex -35.500000 -50.896999 2.634000
    endloop
  endfacet
  facet normal 0.340587 -0.043804 0.939192
    outer loop
      vertex -84.331001 -58.366001 3.028000
      vertex -83.066002 -56.978001 2.634000
      vertex -84.153000 -56.981998 3.028000
    endloop
  endfacet
  facet normal 0.509993 -0.208813 0.834449
    outer loop
      vertex -84.860001 -59.658001 3.028000
      vertex -84.331001 -58.366001 3.028000
      vertex -85.699997 -59.175999 3.662000
    endloop
  endfacet
  facet normal 0.607210 0.079818 0.790522
    outer loop
      vertex -79.550003 17.388000 2.634000
      vertex -79.706001 17.000000 2.793000
      vertex -79.499001 17.000000 2.634000
    endloop
  endfacet
  facet normal 0.438331 -0.333806 0.834530
    outer loop
      vertex -84.860001 -59.658001 3.028000
      vertex -85.699997 -59.175999 3.662000
      vertex -86.392998 -60.085999 3.662000
    endloop
  endfacet
  facet normal 0.788790 -0.103600 0.605869
    outer loop
      vertex -79.706001 17.000000 2.793000
      vertex -79.864998 17.000000 3.000000
      vertex -79.750000 16.665001 2.793000
    endloop
  endfacet
  facet normal 0.224014 -0.263338 0.938334
    outer loop
      vertex -37.826000 -3.630000 3.028000
      vertex -37.283001 -4.572000 2.634000
      vertex -36.209000 -3.327000 2.727000
    endloop
  endfacet
  facet normal 0.787595 -0.104838 0.607209
    outer loop
      vertex -79.750000 16.665001 2.793000
      vertex -79.864998 17.000000 3.000000
      vertex -79.903999 16.707001 3.000000
    endloop
  endfacet
  facet normal 0.735341 -0.307370 0.603985
    outer loop
      vertex -79.750000 16.665001 2.793000
      vertex -80.016998 16.433001 3.000000
      vertex -79.879997 16.354000 2.793000
    endloop
  endfacet
  facet normal -0.016359 0.123810 0.992171
    outer loop
      vertex -40.500000 -50.566002 2.634000
      vertex -42.527000 -49.759998 2.500000
      vertex -42.165001 -50.785999 2.634000
    endloop
  endfacet
  facet normal 0.607291 -0.079762 0.790465
    outer loop
      vertex -79.550003 16.612000 2.634000
      vertex -79.706001 17.000000 2.793000
      vertex -79.750000 16.665001 2.793000
    endloop
  endfacet
  facet normal -0.046817 0.113104 0.992480
    outer loop
      vertex -42.165001 -50.785999 2.634000
      vertex -42.527000 -49.759998 2.500000
      vertex -43.716000 -51.428001 2.634000
    endloop
  endfacet
  facet normal 0.565520 -0.236385 0.790132
    outer loop
      vertex -79.550003 16.612000 2.634000
      vertex -79.750000 16.665001 2.793000
      vertex -79.879997 16.354000 2.793000
    endloop
  endfacet
  facet normal 0.607210 -0.079818 0.790522
    outer loop
      vertex -79.499001 17.000000 2.634000
      vertex -79.706001 17.000000 2.793000
      vertex -79.550003 16.612000 2.634000
    endloop
  endfacet
  facet normal -0.057792 0.120807 0.990992
    outer loop
      vertex -45.162998 -51.021000 2.500000
      vertex -43.716000 -51.428001 2.634000
      vertex -42.527000 -49.759998 2.500000
    endloop
  endfacet
  facet normal -0.071873 0.546532 0.834348
    outer loop
      vertex -40.500000 -52.622002 3.662000
      vertex -41.882999 -51.835999 3.028000
      vertex -41.632999 -52.771000 3.662000
    endloop
  endfacet
  facet normal 0.382773 -0.050315 0.922471
    outer loop
      vertex -79.258003 17.000000 2.534000
      vertex -79.499001 17.000000 2.634000
      vertex -79.550003 16.612000 2.634000
    endloop
  endfacet
  facet normal -0.209016 0.272355 0.939221
    outer loop
      vertex -43.716000 -51.428001 2.634000
      vertex -45.049000 -52.451000 2.634000
      vertex -43.173000 -52.369999 3.028000
    endloop
  endfacet
  facet normal 0.587789 -0.243517 0.771495
    outer loop
      vertex -79.258003 17.000000 2.534000
      vertex -79.550003 16.612000 2.634000
      vertex -79.767998 15.769000 2.534000
    endloop
  endfacet
  facet normal 0.587659 -0.243496 0.771600
    outer loop
      vertex -79.767998 15.769000 2.534000
      vertex -79.550003 16.612000 2.634000
      vertex -79.699997 16.250000 2.634000
    endloop
  endfacet
  facet normal 0.273172 -0.208202 0.939164
    outer loop
      vertex -83.917000 -60.198002 2.634000
      vertex -84.860001 -59.658001 3.028000
      vertex -85.706001 -60.768002 3.028000
    endloop
  endfacet
  facet normal 0.564299 -0.233817 0.791768
    outer loop
      vertex -79.699997 16.250000 2.634000
      vertex -79.550003 16.612000 2.634000
      vertex -79.879997 16.354000 2.793000
    endloop
  endfacet
  facet normal 0.587788 0.243516 0.771495
    outer loop
      vertex -79.767998 18.231001 2.534000
      vertex -79.550003 17.388000 2.634000
      vertex -79.258003 17.000000 2.534000
    endloop
  endfacet
  facet normal -0.071916 0.546481 0.834378
    outer loop
      vertex -41.882999 -51.835999 3.028000
      vertex -40.500000 -52.622002 3.662000
      vertex -40.500000 -51.653999 3.028000
    endloop
  endfacet
  facet normal 0.340297 -0.043507 0.939311
    outer loop
      vertex -84.331001 -58.366001 3.028000
      vertex -83.278999 -58.644001 2.634000
      vertex -83.066002 -56.978001 2.634000
    endloop
  endfacet
  facet normal 0.317452 -0.129978 0.939324
    outer loop
      vertex -83.278999 -58.644001 2.634000
      vertex -84.331001 -58.366001 3.028000
      vertex -84.860001 -59.658001 3.028000
    endloop
  endfacet
  facet normal 0.382773 0.050315 0.922471
    outer loop
      vertex -79.258003 17.000000 2.534000
      vertex -79.550003 17.388000 2.634000
      vertex -79.499001 17.000000 2.634000
    endloop
  endfacet
  facet normal -0.131292 0.317165 0.939238
    outer loop
      vertex -43.173000 -52.369999 3.028000
      vertex -41.882999 -51.835999 3.028000
      vertex -43.716000 -51.428001 2.634000
    endloop
  endfacet
  facet normal 0.317708 -0.130436 0.939174
    outer loop
      vertex -83.278999 -58.644001 2.634000
      vertex -84.860001 -59.658001 3.028000
      vertex -83.917000 -60.198002 2.634000
    endloop
  endfacet
  facet normal 0.101693 0.042131 0.993923
    outer loop
      vertex -79.258003 17.000000 2.534000
      vertex -79.032997 17.259001 2.500000
      vertex -79.767998 18.231001 2.534000
    endloop
  endfacet
  facet normal -0.094972 0.722174 0.685161
    outer loop
      vertex -40.500000 4.582000 4.501000
      vertex -40.500000 5.378000 3.662000
      vertex -41.632999 5.229000 3.662000
    endloop
  endfacet
  facet normal 0.112149 -0.046043 0.992624
    outer loop
      vertex -83.917000 -60.198002 2.634000
      vertex -82.903000 -60.617001 2.500000
      vertex -83.278999 -58.644001 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -79.032997 17.259001 2.500000
      vertex -79.067001 16.482000 2.500000
      vertex -50.831001 16.240999 2.500000
    endloop
  endfacet
  facet normal -0.067352 0.087762 0.993862
    outer loop
      vertex -43.716000 -51.428001 2.634000
      vertex -45.162998 -51.021000 2.500000
      vertex -45.049000 -52.451000 2.634000
    endloop
  endfacet
  facet normal 0.157142 -0.006877 0.987552
    outer loop
      vertex -79.032997 17.259001 2.500000
      vertex -79.258003 17.000000 2.534000
      vertex -79.067001 16.482000 2.500000
    endloop
  endfacet
  facet normal 0.150149 -0.038482 0.987914
    outer loop
      vertex -82.903000 -60.617001 2.500000
      vertex -81.975998 -57.000000 2.500000
      vertex -83.278999 -58.644001 2.634000
    endloop
  endfacet
  facet normal -0.109575 0.084073 0.990417
    outer loop
      vertex -45.049000 -52.451000 2.634000
      vertex -45.162998 -51.021000 2.500000
      vertex -46.070999 -53.783001 2.634000
    endloop
  endfacet
  facet normal 0.121693 -0.015558 0.992446
    outer loop
      vertex -83.278999 -58.644001 2.634000
      vertex -81.975998 -57.000000 2.500000
      vertex -83.066002 -56.978001 2.634000
    endloop
  endfacet
  facet normal -0.210816 0.509431 0.834288
    outer loop
      vertex -41.632999 -52.771000 3.662000
      vertex -43.173000 -52.369999 3.028000
      vertex -42.688999 -53.208000 3.662000
    endloop
  endfacet
  facet normal -0.095036 0.722121 0.685207
    outer loop
      vertex -41.426998 4.460000 4.501000
      vertex -40.500000 4.582000 4.501000
      vertex -41.632999 5.229000 3.662000
    endloop
  endfacet
  facet normal -0.112989 0.858528 0.500163
    outer loop
      vertex -40.500000 4.582000 4.501000
      vertex -41.426998 4.460000 4.501000
      vertex -40.500000 4.000000 5.500000
    endloop
  endfacet
  facet normal 0.383259 0.923641 -0.000000
    outer loop
      vertex -80.499001 17.865999 10.500000
      vertex -80.739998 17.966000 3.500000
      vertex -80.739998 17.966000 10.500000
    endloop
  endfacet
  facet normal 0.130158 0.991493 0.000000
    outer loop
      vertex -80.739998 17.966000 3.500000
      vertex -80.999001 18.000000 3.500000
      vertex -80.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.579216 -0.441096 0.685524
    outer loop
      vertex -85.699997 -59.175999 3.662000
      vertex -86.958000 -59.523998 4.501000
      vertex -86.392998 -60.085999 3.662000
    endloop
  endfacet
  facet normal 0.579132 -0.441950 0.685044
    outer loop
      vertex -85.699997 -59.175999 3.662000
      vertex -86.390999 -58.780998 4.501000
      vertex -86.958000 -59.523998 4.501000
    endloop
  endfacet
  facet normal -0.210850 0.509357 0.834325
    outer loop
      vertex -41.882999 -51.835999 3.028000
      vertex -43.173000 -52.369999 3.028000
      vertex -41.632999 -52.771000 3.662000
    endloop
  endfacet
  facet normal 0.609150 0.793055 -0.000000
    outer loop
      vertex -80.499001 17.865999 10.500000
      vertex -80.292000 17.707001 10.500000
      vertex -80.292000 17.707001 3.500000
    endloop
  endfacet
  facet normal -0.609155 0.793051 0.000000
    outer loop
      vertex -88.999001 -57.866001 0.000000
      vertex -88.792000 -57.707001 5.500000
      vertex -88.792000 -57.707001 0.000000
    endloop
  endfacet
  facet normal 0.383259 0.923641 0.000000
    outer loop
      vertex -80.499001 17.865999 10.500000
      vertex -80.499001 17.865999 3.500000
      vertex -80.739998 17.966000 3.500000
    endloop
  endfacet
  facet normal -0.209018 0.272215 0.939261
    outer loop
      vertex -44.279999 -53.220001 3.028000
      vertex -43.173000 -52.369999 3.028000
      vertex -45.049000 -52.451000 2.634000
    endloop
  endfacet
  facet normal 0.857959 0.112770 0.501187
    outer loop
      vertex -85.917000 1.012000 4.501000
      vertex -86.600998 1.776000 5.500000
      vertex -86.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.858632 0.115781 0.499345
    outer loop
      vertex -85.917000 1.012000 4.501000
      vertex -86.042000 1.939000 4.501000
      vertex -86.600998 1.776000 5.500000
    endloop
  endfacet
  facet normal -0.335760 0.437276 0.834299
    outer loop
      vertex -42.688999 -53.208000 3.662000
      vertex -43.173000 -52.369999 3.028000
      vertex -44.279999 -53.220001 3.028000
    endloop
  endfacet
  facet normal 0.799350 0.331226 0.501326
    outer loop
      vertex -86.600998 1.776000 5.500000
      vertex -86.042000 1.939000 4.501000
      vertex -86.901001 2.500000 5.500000
    endloop
  endfacet
  facet normal 0.438358 -0.334100 0.834397
    outer loop
      vertex -84.860001 -59.658001 3.028000
      vertex -86.392998 -60.085999 3.662000
      vertex -85.706001 -60.768002 3.028000
    endloop
  endfacet
  facet normal 0.445043 -0.576386 0.685359
    outer loop
      vertex -86.392998 -60.085999 3.662000
      vertex -87.697998 -60.096001 4.501000
      vertex -87.296997 -60.784000 3.662000
    endloop
  endfacet
  facet normal 0.281319 -0.671736 0.685296
    outer loop
      vertex -87.697998 -60.096001 4.501000
      vertex -88.559998 -60.457001 4.501000
      vertex -87.296997 -60.784000 3.662000
    endloop
  endfacet
  facet normal 0.280985 -0.672202 0.684976
    outer loop
      vertex -88.559998 -60.457001 4.501000
      vertex -88.351997 -61.224998 3.662000
      vertex -87.296997 -60.784000 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 1.259000 5.500000
      vertex -86.499001 1.000000 5.500000
      vertex -86.600998 1.776000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -86.600998 1.776000 5.500000
      vertex -86.901001 2.500000 5.500000
      vertex -88.532997 1.259000 5.500000
    endloop
  endfacet
  facet normal 0.336875 -0.436295 0.834363
    outer loop
      vertex -85.706001 -60.768002 3.028000
      vertex -86.392998 -60.085999 3.662000
      vertex -87.296997 -60.784000 3.662000
    endloop
  endfacet
  facet normal -0.958305 0.078505 0.274753
    outer loop
      vertex -35.035999 1.706000 4.619000
      vertex -35.000000 1.001000 4.946000
      vertex -35.030998 2.684000 4.357000
    endloop
  endfacet
  facet normal 0.336861 -0.436378 0.834325
    outer loop
      vertex -85.706001 -60.768002 3.028000
      vertex -87.296997 -60.784000 3.662000
      vertex -86.810997 -61.620998 3.028000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -88.999001 1.866000 5.500000
      vertex -88.792000 1.707000 5.500000
      vertex -87.377998 3.121000 5.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 -0.000000
    outer loop
      vertex -35.000000 14.000000 10.500000
      vertex -35.000000 14.000000 3.500000
      vertex -35.000000 4.029000 4.132000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.377998 3.121000 5.500000
      vertex -87.999001 3.598000 5.500000
      vertex -88.999001 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.097355 -0.721987 0.685023
    outer loop
      vertex -88.559998 -60.457001 4.501000
      vertex -89.487000 -60.582001 4.501000
      vertex -88.351997 -61.224998 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -45.162998 -51.021000 2.500000
      vertex -42.527000 -49.759998 2.500000
      vertex -36.000000 -32.768002 2.500000
    endloop
  endfacet
  facet normal -0.247685 0.118634 0.961550
    outer loop
      vertex -35.467999 1.069000 4.103000
      vertex -36.035999 1.569000 3.895000
      vertex -36.060001 1.065000 3.951000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -88.633003 1.500000 5.500000
      vertex -88.532997 1.259000 5.500000
      vertex -86.901001 2.500000 5.500000
    endloop
  endfacet
  facet normal -0.267333 0.095208 0.958889
    outer loop
      vertex -35.467999 1.069000 4.103000
      vertex -35.455002 1.599000 4.054000
      vertex -36.035999 1.569000 3.895000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -88.792000 1.707000 5.500000
      vertex -88.633003 1.500000 5.500000
      vertex -87.377998 3.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -86.901001 2.500000 5.500000
      vertex -87.377998 3.121000 5.500000
      vertex -88.633003 1.500000 5.500000
    endloop
  endfacet
  facet normal 0.212585 -0.508569 0.834365
    outer loop
      vertex -86.810997 -61.620998 3.028000
      vertex -87.296997 -60.784000 3.662000
      vertex -88.351997 -61.224998 3.662000
    endloop
  endfacet
  facet normal 0.097560 -0.721819 0.685171
    outer loop
      vertex -89.484001 -61.377998 3.662000
      vertex -88.351997 -61.224998 3.662000
      vertex -89.487000 -60.582001 4.501000
    endloop
  endfacet
  facet normal -0.603690 0.088058 0.792341
    outer loop
      vertex -35.455002 1.599000 4.054000
      vertex -35.467999 1.069000 4.103000
      vertex -35.313999 1.072000 4.220000
    endloop
  endfacet
  facet normal -0.443399 0.577432 0.685543
    outer loop
      vertex -43.032001 -54.466999 4.501000
      vertex -42.291000 -53.897999 4.501000
      vertex -43.596001 -53.903999 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.999001 3.598000 5.500000
      vertex -89.999001 1.866000 5.500000
      vertex -89.758003 1.966000 5.500000
    endloop
  endfacet
  facet normal -0.617157 0.081392 0.782619
    outer loop
      vertex -35.313999 1.072000 4.220000
      vertex -35.305000 1.621000 4.170000
      vertex -35.455002 1.599000 4.054000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 1.966000 5.500000
      vertex -90.276001 3.898000 5.500000
      vertex -90.999001 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.443300 0.577693 0.685388
    outer loop
      vertex -43.596001 -53.903999 3.662000
      vertex -42.291000 -53.897999 4.501000
      vertex -42.688999 -53.208000 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 2.000000 5.500000
      vertex -89.239998 1.966000 5.500000
      vertex -89.499001 4.000000 5.500000
    endloop
  endfacet
  facet normal -0.617620 0.198619 0.760984
    outer loop
      vertex -35.455002 1.599000 4.054000
      vertex -35.305000 1.621000 4.170000
      vertex -35.426998 2.165000 3.929000
    endloop
  endfacet
  facet normal -0.278723 0.672678 0.685433
    outer loop
      vertex -42.688999 -53.208000 3.662000
      vertex -42.291000 -53.897999 4.501000
      vertex -41.426998 -53.540001 4.501000
    endloop
  endfacet
  facet normal -0.856279 0.060750 0.512929
    outer loop
      vertex -35.036999 1.084000 4.681000
      vertex -35.305000 1.621000 4.170000
      vertex -35.313999 1.072000 4.220000
    endloop
  endfacet
  facet normal 0.073859 -0.546244 0.834364
    outer loop
      vertex -88.098000 -62.159000 3.028000
      vertex -89.484001 -61.377998 3.662000
      vertex -89.481003 -62.346001 3.028000
    endloop
  endfacet
  facet normal -0.860971 0.051822 0.506007
    outer loop
      vertex -35.036999 1.084000 4.681000
      vertex -35.035999 1.706000 4.619000
      vertex -35.305000 1.621000 4.170000
    endloop
  endfacet
  facet normal -0.335721 0.437499 0.834198
    outer loop
      vertex -42.688999 -53.208000 3.662000
      vertex -44.279999 -53.220001 3.028000
      vertex -43.596001 -53.903999 3.662000
    endloop
  endfacet
  facet normal -0.855586 -0.048715 0.515363
    outer loop
      vertex -35.305000 0.385000 4.170000
      vertex -35.036999 1.084000 4.681000
      vertex -35.313999 1.072000 4.220000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.999001 -1.598000 5.500000
      vertex -88.999001 0.134000 5.500000
      vertex -89.239998 0.034000 5.500000
    endloop
  endfacet
  facet normal -0.923635 0.383273 0.000000
    outer loop
      vertex -88.633003 -57.500000 5.500000
      vertex -88.532997 -57.258999 5.500000
      vertex -88.532997 -57.258999 0.000000
    endloop
  endfacet
  facet normal -0.923635 0.383273 0.000000
    outer loop
      vertex -88.532997 -57.258999 0.000000
      vertex -88.633003 -57.500000 0.000000
      vertex -88.633003 -57.500000 5.500000
    endloop
  endfacet
  facet normal -0.793058 0.609146 -0.000000
    outer loop
      vertex -88.792000 -57.707001 0.000000
      vertex -88.633003 -57.500000 5.500000
      vertex -88.633003 -57.500000 0.000000
    endloop
  endfacet
  facet normal -0.793058 0.609146 0.000000
    outer loop
      vertex -88.792000 -57.707001 5.500000
      vertex -88.633003 -57.500000 5.500000
      vertex -88.792000 -57.707001 0.000000
    endloop
  endfacet
  facet normal -0.577752 0.443825 0.684997
    outer loop
      vertex -43.032001 -54.466999 4.501000
      vertex -44.291000 -54.811001 3.662000
      vertex -43.602001 -55.209000 4.501000
    endloop
  endfacet
  facet normal -0.861009 0.135711 0.490149
    outer loop
      vertex -35.035999 1.706000 4.619000
      vertex -35.030998 2.684000 4.357000
      vertex -35.305000 1.621000 4.170000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 1.259000 5.500000
      vertex -88.499001 1.000000 5.500000
      vertex -86.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.130158 0.991493 0.000000
    outer loop
      vertex -89.499001 -58.000000 5.500000
      vertex -89.239998 -57.966000 0.000000
      vertex -89.499001 -58.000000 0.000000
    endloop
  endfacet
  facet normal 0.130158 0.991493 0.000000
    outer loop
      vertex -89.758003 -57.966000 0.000000
      vertex -89.499001 -58.000000 5.500000
      vertex -89.499001 -58.000000 0.000000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -88.499001 1.000000 5.500000
      vertex -88.532997 0.741000 5.500000
      vertex -86.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 0.741000 5.500000
      vertex -86.600998 0.224000 5.500000
      vertex -86.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.532997 0.741000 5.500000
      vertex -88.633003 0.500000 5.500000
      vertex -86.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.377998 -1.121000 5.500000
      vertex -88.792000 0.293000 5.500000
      vertex -88.999001 0.134000 5.500000
    endloop
  endfacet
  facet normal 0.383253 0.923643 0.000000
    outer loop
      vertex -89.999001 -57.866001 5.500000
      vertex -89.758003 -57.966000 0.000000
      vertex -89.999001 -57.866001 0.000000
    endloop
  endfacet
  facet normal 0.609155 0.793051 -0.000000
    outer loop
      vertex -90.206001 -57.707001 0.000000
      vertex -89.999001 -57.866001 5.500000
      vertex -89.999001 -57.866001 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 14.000000 10.500000
      vertex -35.000000 4.029000 4.132000
      vertex -35.000000 1.001000 4.946000
    endloop
  endfacet
  facet normal 0.131291 -0.317165 0.939239
    outer loop
      vertex -37.283001 -4.572000 2.634000
      vertex -37.826000 -3.630000 3.028000
      vertex -39.116001 -4.164000 3.028000
    endloop
  endfacet
  facet normal -0.973473 0.059399 0.220958
    outer loop
      vertex -35.000000 4.029000 4.132000
      vertex -35.030998 2.684000 4.357000
      vertex -35.000000 1.001000 4.946000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.239998 0.034000 5.500000
      vertex -89.499001 -2.000000 5.500000
      vertex -88.723000 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -89.499001 -2.000000 5.500000
      vertex -89.499001 0.000000 5.500000
      vertex -89.758003 0.034000 5.500000
    endloop
  endfacet
  facet normal 0.209855 -0.271852 0.939179
    outer loop
      vertex -84.934998 -61.534000 2.634000
      vertex -85.706001 -60.768002 3.028000
      vertex -86.810997 -61.620998 3.028000
    endloop
  endfacet
  facet normal 0.071864 -0.546484 0.834380
    outer loop
      vertex -40.500000 -3.378000 3.662000
      vertex -40.500000 -4.346000 3.028000
      vertex -39.116001 -4.164000 3.028000
    endloop
  endfacet
  facet normal 0.273156 -0.208138 0.939183
    outer loop
      vertex -84.934998 -61.534000 2.634000
      vertex -83.917000 -60.198002 2.634000
      vertex -85.706001 -60.768002 3.028000
    endloop
  endfacet
  facet normal 0.053709 -0.120379 0.991274
    outer loop
      vertex -37.283001 -4.572000 2.634000
      vertex -36.000000 -5.103000 2.500000
      vertex -36.209000 -3.327000 2.727000
    endloop
  endfacet
  facet normal -0.989577 0.015857 0.143129
    outer loop
      vertex -35.000000 1.001000 4.946000
      vertex -35.035999 1.706000 4.619000
      vertex -35.036999 1.084000 4.681000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.999001 -1.598000 5.500000
      vertex -89.758003 0.034000 5.500000
      vertex -89.999001 0.134000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -91.620003 -1.121000 5.500000
      vertex -90.206001 0.293000 5.500000
      vertex -90.364998 0.500000 5.500000
    endloop
  endfacet
  facet normal 0.112783 -0.105543 0.987998
    outer loop
      vertex -82.903000 -60.617001 2.500000
      vertex -84.934998 -61.534000 2.634000
      vertex -85.454002 -63.342999 2.500000
    endloop
  endfacet
  facet normal 0.044764 -0.340406 0.939212
    outer loop
      vertex -40.500000 -4.346000 3.028000
      vertex -38.834000 -5.214000 2.634000
      vertex -39.116001 -4.164000 3.028000
    endloop
  endfacet
  facet normal 0.099712 -0.075978 0.992111
    outer loop
      vertex -84.934998 -61.534000 2.634000
      vertex -82.903000 -60.617001 2.500000
      vertex -83.917000 -60.198002 2.634000
    endloop
  endfacet
  facet normal 0.044918 -0.340150 0.939298
    outer loop
      vertex -40.500000 -5.434000 2.634000
      vertex -38.834000 -5.214000 2.634000
      vertex -40.500000 -4.346000 3.028000
    endloop
  endfacet
  facet normal 0.535985 0.072653 0.841095
    outer loop
      vertex -36.222000 1.573000 3.920000
      vertex -36.763000 1.327000 4.286000
      vertex -36.249001 1.066000 3.981000
    endloop
  endfacet
  facet normal 0.131288 -0.317176 0.939235
    outer loop
      vertex -39.116001 -4.164000 3.028000
      vertex -38.834000 -5.214000 2.634000
      vertex -37.283001 -4.572000 2.634000
    endloop
  endfacet
  facet normal 0.014496 -0.109772 0.993851
    outer loop
      vertex -40.500000 -5.434000 2.634000
      vertex -39.619999 -6.531000 2.500000
      vertex -38.834000 -5.214000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -82.903000 -60.617001 2.500000
      vertex -85.454002 -63.342999 2.500000
      vertex -47.028000 -60.730000 2.500000
    endloop
  endfacet
  facet normal -0.383258 -0.923641 -0.000000
    outer loop
      vertex -88.999001 1.866000 5.500000
      vertex -89.239998 1.966000 5.500000
      vertex -89.239998 1.966000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -85.454002 -63.342999 2.500000
      vertex -88.056000 -64.444000 2.500000
      vertex -92.999001 -84.000000 2.500000
    endloop
  endfacet
  facet normal 0.051966 -0.131735 0.989922
    outer loop
      vertex -39.619999 -6.531000 2.500000
      vertex -36.000000 -5.103000 2.500000
      vertex -38.834000 -5.214000 2.634000
    endloop
  endfacet
  facet normal -0.609154 -0.793052 -0.000000
    outer loop
      vertex -88.999001 1.866000 5.500000
      vertex -88.999001 1.866000 0.000000
      vertex -88.792000 1.707000 5.500000
    endloop
  endfacet
  facet normal 0.051745 -0.125009 0.990805
    outer loop
      vertex -37.283001 -4.572000 2.634000
      vertex -38.834000 -5.214000 2.634000
      vertex -36.000000 -5.103000 2.500000
    endloop
  endfacet
  facet normal 0.504391 0.154655 0.849512
    outer loop
      vertex -36.222000 1.573000 3.920000
      vertex -36.742001 1.654000 4.214000
      vertex -36.763000 1.327000 4.286000
    endloop
  endfacet
  facet normal -0.564639 -0.233161 0.791718
    outer loop
      vertex -34.985001 -83.146004 2.793000
      vertex -35.414001 -82.647003 2.634000
      vertex -35.165001 -83.250000 2.634000
    endloop
  endfacet
  facet normal -0.130156 0.991494 0.000000
    outer loop
      vertex -89.499001 0.000000 0.000000
      vertex -89.499001 0.000000 5.500000
      vertex -89.239998 0.034000 5.500000
    endloop
  endfacet
  facet normal -0.130156 0.991494 0.000000
    outer loop
      vertex -89.239998 0.034000 5.500000
      vertex -89.239998 0.034000 0.000000
      vertex -89.499001 0.000000 0.000000
    endloop
  endfacet
  facet normal -0.565477 -0.234166 0.790824
    outer loop
      vertex -35.214001 -82.593002 2.793000
      vertex -35.414001 -82.647003 2.634000
      vertex -34.985001 -83.146004 2.793000
    endloop
  endfacet
  facet normal -0.484790 -0.371506 0.791809
    outer loop
      vertex -35.165001 -83.250000 2.634000
      vertex -34.620998 -83.621002 2.793000
      vertex -34.985001 -83.146004 2.793000
    endloop
  endfacet
  facet normal 0.130156 0.991494 0.000000
    outer loop
      vertex -89.499001 0.000000 5.500000
      vertex -89.499001 0.000000 0.000000
      vertex -89.758003 0.034000 5.500000
    endloop
  endfacet
  facet normal 0.509111 -0.003175 0.860695
    outer loop
      vertex -36.763000 1.327000 4.286000
      vertex -36.762001 0.674000 4.283000
      vertex -36.249001 1.066000 3.981000
    endloop
  endfacet
  facet normal -0.800022 -0.330396 0.500803
    outer loop
      vertex -43.959999 0.073000 4.501000
      vertex -43.098000 -0.500000 5.500000
      vertex -43.396999 0.224000 5.500000
    endloop
  endfacet
  facet normal -0.736471 -0.304976 0.603822
    outer loop
      vertex -34.848000 -83.067001 3.000000
      vertex -35.214001 -82.593002 2.793000
      vertex -34.985001 -83.146004 2.793000
    endloop
  endfacet
  facet normal 0.737610 -0.097613 0.668134
    outer loop
      vertex -36.762001 0.674000 4.283000
      vertex -37.039001 0.073000 4.501000
      vertex -36.742001 0.346000 4.213000
    endloop
  endfacet
  facet normal -0.632529 -0.485129 0.603785
    outer loop
      vertex -34.985001 -83.146004 2.793000
      vertex -34.508999 -83.509003 3.000000
      vertex -34.848000 -83.067001 3.000000
    endloop
  endfacet
  facet normal -0.799984 -0.331473 0.500152
    outer loop
      vertex -43.098000 -0.500000 5.500000
      vertex -43.959999 0.073000 4.501000
      vertex -43.602001 -0.791000 4.501000
    endloop
  endfacet
  facet normal 0.757898 -0.156374 0.633354
    outer loop
      vertex -36.742001 0.346000 4.213000
      vertex -37.039001 0.073000 4.501000
      vertex -36.667999 -0.316000 3.961000
    endloop
  endfacet
  facet normal -0.854055 -0.353233 0.381858
    outer loop
      vertex -34.964001 -82.526001 3.241000
      vertex -35.061001 -82.552002 3.000000
      vertex -34.848000 -83.067001 3.000000
    endloop
  endfacet
  facet normal 0.073834 -0.546275 0.834346
    outer loop
      vertex -88.098000 -62.159000 3.028000
      vertex -88.351997 -61.224998 3.662000
      vertex -89.484001 -61.377998 3.662000
    endloop
  endfacet
  facet normal -0.686745 -0.527501 0.500124
    outer loop
      vertex -43.098000 -0.500000 5.500000
      vertex -43.602001 -0.791000 4.501000
      vertex -42.620998 -1.121000 5.500000
    endloop
  endfacet
  facet normal -0.686732 -0.527543 0.500097
    outer loop
      vertex -42.620998 -1.121000 5.500000
      vertex -43.602001 -0.791000 4.501000
      vertex -43.032001 -1.533000 4.501000
    endloop
  endfacet
  facet normal -0.069870 -0.546713 0.834400
    outer loop
      vertex -90.865997 -62.168999 3.028000
      vertex -89.481003 -62.346001 3.028000
      vertex -89.484001 -61.377998 3.662000
    endloop
  endfacet
  facet normal -0.527470 -0.686704 0.500214
    outer loop
      vertex -42.620998 -1.121000 5.500000
      vertex -43.032001 -1.533000 4.501000
      vertex -42.000000 -1.598000 5.500000
    endloop
  endfacet
  facet normal -0.278724 -0.672677 0.685434
    outer loop
      vertex -42.291000 -2.102000 4.501000
      vertex -42.688999 -2.792000 3.662000
      vertex -41.426998 -2.460000 4.501000
    endloop
  endfacet
  facet normal -0.527396 -0.686821 0.500130
    outer loop
      vertex -42.000000 -1.598000 5.500000
      vertex -43.032001 -1.533000 4.501000
      vertex -42.291000 -2.102000 4.501000
    endloop
  endfacet
  facet normal -0.331484 -0.799979 0.500152
    outer loop
      vertex -42.000000 -1.598000 5.500000
      vertex -42.291000 -2.102000 4.501000
      vertex -41.276001 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.271417 0.209739 0.939331
    outer loop
      vertex -84.964996 5.565000 2.634000
      vertex -85.732002 4.793000 3.028000
      vertex -83.938004 4.236000 2.634000
    endloop
  endfacet
  facet normal 0.049672 -0.117390 0.991843
    outer loop
      vertex -88.056000 -64.444000 2.500000
      vertex -85.454002 -63.342999 2.500000
      vertex -87.813004 -63.209000 2.634000
    endloop
  endfacet
  facet normal 0.099988 0.077266 0.991984
    outer loop
      vertex -83.938004 4.236000 2.634000
      vertex -82.903000 4.617000 2.500000
      vertex -84.964996 5.565000 2.634000
    endloop
  endfacet
  facet normal -0.331475 -0.799987 0.500145
    outer loop
      vertex -41.276001 -1.898000 5.500000
      vertex -42.291000 -2.102000 4.501000
      vertex -41.426998 -2.460000 4.501000
    endloop
  endfacet
  facet normal 0.112690 0.105456 0.988018
    outer loop
      vertex -82.903000 4.617000 2.500000
      vertex -85.454002 7.343000 2.500000
      vertex -84.964996 5.565000 2.634000
    endloop
  endfacet
  facet normal -0.112989 -0.858528 0.500163
    outer loop
      vertex -40.500000 -2.000000 5.500000
      vertex -41.426998 -2.460000 4.501000
      vertex -40.500000 -2.582000 4.501000
    endloop
  endfacet
  facet normal 0.212591 -0.508557 0.834371
    outer loop
      vertex -86.810997 -61.620998 3.028000
      vertex -88.351997 -61.224998 3.662000
      vertex -88.098000 -62.159000 3.028000
    endloop
  endfacet
  facet normal -0.112857 -0.858598 0.500073
    outer loop
      vertex -41.276001 -1.898000 5.500000
      vertex -41.426998 -2.460000 4.501000
      vertex -40.500000 -2.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.000000 0.134000 5.500000
      vertex -41.207001 0.293000 5.500000
      vertex -42.620998 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.366001 0.500000 5.500000
      vertex -43.396999 0.224000 5.500000
      vertex -43.098000 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.366001 0.500000 5.500000
      vertex -43.098000 -0.500000 5.500000
      vertex -42.620998 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -42.620998 -1.121000 5.500000
      vertex -41.207001 0.293000 5.500000
      vertex -41.366001 0.500000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -42.620998 -1.121000 5.500000
      vertex -42.000000 -1.598000 5.500000
      vertex -41.000000 0.134000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -42.000000 -1.598000 5.500000
      vertex -41.276001 -1.898000 5.500000
      vertex -41.000000 0.134000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -41.276001 -1.898000 5.500000
      vertex -40.500000 -2.000000 5.500000
      vertex -40.500000 0.000000 5.500000
    endloop
  endfacet
  facet normal 0.045971 -0.339986 0.939306
    outer loop
      vertex -87.813004 -63.209000 2.634000
      vertex -88.098000 -62.159000 3.028000
      vertex -89.481003 -62.346001 3.028000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -82.903000 4.617000 2.500000
      vertex -81.975998 1.948000 2.500000
      vertex -50.831001 16.240999 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -85.454002 7.343000 2.500000
      vertex -82.903000 4.617000 2.500000
      vertex -80.999001 15.000000 2.500000
    endloop
  endfacet
  facet normal 0.045949 -0.340023 0.939294
    outer loop
      vertex -89.477997 -63.433998 2.634000
      vertex -87.813004 -63.209000 2.634000
      vertex -89.481003 -62.346001 3.028000
    endloop
  endfacet
  facet normal -0.672882 -0.278808 0.685198
    outer loop
      vertex -43.959999 0.073000 4.501000
      vertex -44.729000 -0.133000 3.662000
      vertex -43.602001 -0.791000 4.501000
    endloop
  endfacet
  facet normal -0.672931 -0.279113 0.685025
    outer loop
      vertex -44.729000 -0.133000 3.662000
      vertex -44.291000 -1.189000 3.662000
      vertex -43.602001 -0.791000 4.501000
    endloop
  endfacet
  facet normal 0.014969 -0.110767 0.993734
    outer loop
      vertex -89.477997 -63.433998 2.634000
      vertex -88.056000 -64.444000 2.500000
      vertex -87.813004 -63.209000 2.634000
    endloop
  endfacet
  facet normal 0.209859 -0.271570 0.939260
    outer loop
      vertex -86.264000 -62.561001 2.634000
      vertex -84.934998 -61.534000 2.634000
      vertex -86.810997 -61.620998 3.028000
    endloop
  endfacet
  facet normal 0.132411 -0.316521 0.939298
    outer loop
      vertex -86.264000 -62.561001 2.634000
      vertex -88.098000 -62.159000 3.028000
      vertex -87.813004 -63.209000 2.634000
    endloop
  endfacet
  facet normal 0.132372 -0.316659 0.939258
    outer loop
      vertex -86.264000 -62.561001 2.634000
      vertex -86.810997 -61.620998 3.028000
      vertex -88.098000 -62.159000 3.028000
    endloop
  endfacet
  facet normal 0.049598 -0.118561 0.991707
    outer loop
      vertex -87.813004 -63.209000 2.634000
      vertex -85.454002 -63.342999 2.500000
      vertex -86.264000 -62.561001 2.634000
    endloop
  endfacet
  facet normal -0.577857 -0.442790 0.685579
    outer loop
      vertex -44.291000 -1.189000 3.662000
      vertex -43.596001 -2.096000 3.662000
      vertex -43.032001 -1.533000 4.501000
    endloop
  endfacet
  facet normal -0.577752 -0.443825 0.684998
    outer loop
      vertex -43.602001 -0.791000 4.501000
      vertex -44.291000 -1.189000 3.662000
      vertex -43.032001 -1.533000 4.501000
    endloop
  endfacet
  facet normal 0.043556 0.340571 0.939209
    outer loop
      vertex -87.855003 7.220000 2.634000
      vertex -89.516998 6.346000 3.028000
      vertex -88.133003 6.169000 3.028000
    endloop
  endfacet
  facet normal -0.509101 -0.211161 0.834403
    outer loop
      vertex -44.729000 -0.133000 3.662000
      vertex -45.664001 -0.384000 3.028000
      vertex -44.291000 -1.189000 3.662000
    endloop
  endfacet
  facet normal 0.073021 -0.094494 0.992844
    outer loop
      vertex -84.934998 -61.534000 2.634000
      vertex -86.264000 -62.561001 2.634000
      vertex -85.454002 -63.342999 2.500000
    endloop
  endfacet
  facet normal 0.504309 -0.150709 0.850270
    outer loop
      vertex -36.222000 0.433000 3.920000
      vertex -36.762001 0.674000 4.283000
      vertex -36.742001 0.346000 4.213000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.056000 -64.444000 2.500000
      vertex -93.999001 -83.732002 2.500000
      vertex -93.516998 -83.931999 2.500000
    endloop
  endfacet
  facet normal 0.130393 0.317604 0.939215
    outer loop
      vertex -88.133003 6.169000 3.028000
      vertex -86.301003 6.582000 2.634000
      vertex -87.855003 7.220000 2.634000
    endloop
  endfacet
  facet normal 0.506690 -0.256661 0.823037
    outer loop
      vertex -36.742001 0.346000 4.213000
      vertex -36.667999 -0.316000 3.961000
      vertex -36.222000 0.433000 3.920000
    endloop
  endfacet
  facet normal 0.072047 0.094646 0.992901
    outer loop
      vertex -84.964996 5.565000 2.634000
      vertex -85.454002 7.343000 2.500000
      vertex -86.301003 6.582000 2.634000
    endloop
  endfacet
  facet normal -0.247479 -0.076352 0.965880
    outer loop
      vertex -35.455002 0.407000 4.054000
      vertex -35.467999 1.069000 4.103000
      vertex -36.060001 1.065000 3.951000
    endloop
  endfacet
  facet normal -0.602567 -0.070670 0.794933
    outer loop
      vertex -35.467999 1.069000 4.103000
      vertex -35.455002 0.407000 4.054000
      vertex -35.313999 1.072000 4.220000
    endloop
  endfacet
  facet normal -0.858632 -0.115781 0.499345
    outer loop
      vertex -92.956001 -57.938999 4.501000
      vertex -92.397003 -57.776001 5.500000
      vertex -93.081001 -57.012001 4.501000
    endloop
  endfacet
  facet normal -0.799351 -0.331226 0.501326
    outer loop
      vertex -92.397003 -57.776001 5.500000
      vertex -92.956001 -57.938999 4.501000
      vertex -92.097000 -58.500000 5.500000
    endloop
  endfacet
  facet normal -0.045971 0.339986 0.939306
    outer loop
      vertex -90.900002 6.159000 3.028000
      vertex -89.516998 6.346000 3.028000
      vertex -91.184998 7.209000 2.634000
    endloop
  endfacet
  facet normal -0.861201 -0.126221 0.492342
    outer loop
      vertex -35.032001 -0.483000 4.425000
      vertex -35.035999 0.301000 4.619000
      vertex -35.305000 0.385000 4.170000
    endloop
  endfacet
  facet normal -0.443399 -0.577432 0.685543
    outer loop
      vertex -43.596001 -2.096000 3.662000
      vertex -42.291000 -2.102000 4.501000
      vertex -43.032001 -1.533000 4.501000
    endloop
  endfacet
  facet normal -0.443300 -0.577692 0.685388
    outer loop
      vertex -42.291000 -2.102000 4.501000
      vertex -43.596001 -2.096000 3.662000
      vertex -42.688999 -2.792000 3.662000
    endloop
  endfacet
  facet normal -0.873657 -0.137685 0.466655
    outer loop
      vertex -35.305000 0.385000 4.170000
      vertex -35.278999 -0.346000 4.003000
      vertex -35.032001 -0.483000 4.425000
    endloop
  endfacet
  facet normal -0.799220 -0.334321 0.499476
    outer loop
      vertex -92.956001 -57.938999 4.501000
      vertex -92.595001 -58.801998 4.501000
      vertex -92.097000 -58.500000 5.500000
    endloop
  endfacet
  facet normal -0.616408 -0.065186 0.784724
    outer loop
      vertex -35.305000 0.385000 4.170000
      vertex -35.313999 1.072000 4.220000
      vertex -35.455002 0.407000 4.054000
    endloop
  endfacet
  facet normal -0.686168 -0.527055 0.501384
    outer loop
      vertex -92.595001 -58.801998 4.501000
      vertex -91.620003 -59.120998 5.500000
      vertex -92.097000 -58.500000 5.500000
    endloop
  endfacet
  facet normal 0.049382 0.116704 0.991938
    outer loop
      vertex -85.454002 7.343000 2.500000
      vertex -88.056000 8.444000 2.500000
      vertex -87.855003 7.220000 2.634000
    endloop
  endfacet
  facet normal -0.860485 -0.041307 0.507799
    outer loop
      vertex -35.035999 0.301000 4.619000
      vertex -35.036999 1.084000 4.681000
      vertex -35.305000 0.385000 4.170000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -92.097000 -58.500000 5.500000
      vertex -91.620003 -59.120998 5.500000
      vertex -90.364998 -57.500000 5.500000
    endloop
  endfacet
  facet normal -0.990828 -0.011923 0.134603
    outer loop
      vertex -35.035999 0.301000 4.619000
      vertex -35.000000 1.001000 4.946000
      vertex -35.036999 1.084000 4.681000
    endloop
  endfacet
  facet normal -0.209016 -0.272354 0.939221
    outer loop
      vertex -43.173000 -3.630000 3.028000
      vertex -45.049000 -3.549000 2.634000
      vertex -43.716000 -4.572000 2.634000
    endloop
  endfacet
  facet normal -0.966316 -0.066451 0.248631
    outer loop
      vertex -35.000000 1.001000 4.946000
      vertex -35.035999 0.301000 4.619000
      vertex -35.032001 -0.483000 4.425000
    endloop
  endfacet
  facet normal 0.049201 0.119840 0.991573
    outer loop
      vertex -87.855003 7.220000 2.634000
      vertex -86.301003 6.582000 2.634000
      vertex -85.454002 7.343000 2.500000
    endloop
  endfacet
  facet normal -0.209018 -0.272215 0.939261
    outer loop
      vertex -44.279999 -2.780000 3.028000
      vertex -45.049000 -3.549000 2.634000
      vertex -43.173000 -3.630000 3.028000
    endloop
  endfacet
  facet normal -0.045972 0.339984 0.939307
    outer loop
      vertex -89.516998 6.346000 3.028000
      vertex -89.521004 7.434000 2.634000
      vertex -91.184998 7.209000 2.634000
    endloop
  endfacet
  facet normal 0.043713 0.340311 0.939296
    outer loop
      vertex -89.521004 7.434000 2.634000
      vertex -89.516998 6.346000 3.028000
      vertex -87.855003 7.220000 2.634000
    endloop
  endfacet
  facet normal -0.915665 -0.123644 0.382452
    outer loop
      vertex -35.000000 1.001000 4.946000
      vertex -35.026001 -1.680000 4.017000
      vertex -35.021000 -2.911000 3.631000
    endloop
  endfacet
  facet normal -0.342022 -0.304704 0.888919
    outer loop
      vertex -35.000000 1.001000 4.946000
      vertex -35.032001 -0.483000 4.425000
      vertex -35.026001 -1.680000 4.017000
    endloop
  endfacet
  facet normal 0.014275 0.111132 0.993703
    outer loop
      vertex -87.855003 7.220000 2.634000
      vertex -88.056000 8.444000 2.500000
      vertex -89.521004 7.434000 2.634000
    endloop
  endfacet
  facet normal -0.998459 -0.012793 0.054002
    outer loop
      vertex -35.021000 -2.911000 3.631000
      vertex -35.000000 -5.103000 3.500000
      vertex -35.000000 1.001000 4.946000
    endloop
  endfacet
  facet normal -0.721410 -0.097278 0.685642
    outer loop
      vertex -93.081001 -57.012001 4.501000
      vertex -93.877998 -57.014999 3.662000
      vertex -92.956001 -57.938999 4.501000
    endloop
  endfacet
  facet normal -0.002340 0.134855 0.990863
    outer loop
      vertex -88.056000 8.444000 2.500000
      vertex -90.879997 8.395000 2.500000
      vertex -89.521004 7.434000 2.634000
    endloop
  endfacet
  facet normal -0.335759 -0.437276 0.834299
    outer loop
      vertex -42.688999 -2.792000 3.662000
      vertex -44.279999 -2.780000 3.028000
      vertex -43.173000 -3.630000 3.028000
    endloop
  endfacet
  facet normal -0.015719 0.116247 0.993096
    outer loop
      vertex -89.521004 7.434000 2.634000
      vertex -90.879997 8.395000 2.500000
      vertex -91.184998 7.209000 2.634000
    endloop
  endfacet
  facet normal -0.210816 -0.509431 0.834288
    outer loop
      vertex -42.688999 -2.792000 3.662000
      vertex -43.173000 -3.630000 3.028000
      vertex -41.632999 -3.229000 3.662000
    endloop
  endfacet
  facet normal -0.335721 -0.437499 0.834198
    outer loop
      vertex -43.596001 -2.096000 3.662000
      vertex -44.279999 -2.780000 3.028000
      vertex -42.688999 -2.792000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.206001 -57.707001 5.500000
      vertex -90.364998 -57.500000 5.500000
      vertex -91.620003 -59.120998 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -85.454002 7.343000 2.500000
      vertex -80.999001 15.000000 2.500000
      vertex -88.056000 8.444000 2.500000
    endloop
  endfacet
  facet normal -0.278500 -0.672988 0.685219
    outer loop
      vertex -41.632999 -3.229000 3.662000
      vertex -41.426998 -2.460000 4.501000
      vertex -42.688999 -2.792000 3.662000
    endloop
  endfacet
  facet normal -0.095037 -0.722121 0.685207
    outer loop
      vertex -41.426998 -2.460000 4.501000
      vertex -41.632999 -3.229000 3.662000
      vertex -40.500000 -2.582000 4.501000
    endloop
  endfacet
  facet normal -0.097475 0.721824 0.685178
    outer loop
      vertex -89.511002 4.582000 4.501000
      vertex -89.514000 5.378000 3.662000
      vertex -90.647003 5.225000 3.662000
    endloop
  endfacet
  facet normal -0.094973 -0.722174 0.685161
    outer loop
      vertex -40.500000 -2.582000 4.501000
      vertex -41.632999 -3.229000 3.662000
      vertex -40.500000 -3.378000 3.662000
    endloop
  endfacet
  facet normal -0.210850 -0.509357 0.834324
    outer loop
      vertex -41.882999 -4.164000 3.028000
      vertex -41.632999 -3.229000 3.662000
      vertex -43.173000 -3.630000 3.028000
    endloop
  endfacet
  facet normal 0.380084 0.915990 0.128446
    outer loop
      vertex -80.732002 17.999001 3.241000
      vertex -80.739998 17.966000 3.500000
      vertex -80.499001 17.865999 3.500000
    endloop
  endfacet
  facet normal -0.733394 -0.562671 0.381490
    outer loop
      vertex -34.761002 -83.016998 3.241000
      vertex -34.848000 -83.067001 3.000000
      vertex -34.438000 -83.438004 3.241000
    endloop
  endfacet
  facet normal 0.609150 0.793055 -0.000000
    outer loop
      vertex -80.499001 17.865999 3.500000
      vertex -80.499001 17.865999 10.500000
      vertex -80.292000 17.707001 3.500000
    endloop
  endfacet
  facet normal -0.217649 -0.151662 0.964172
    outer loop
      vertex -35.165001 -83.250000 2.634000
      vertex -35.652000 -83.403000 2.500000
      vertex -35.236000 -84.000000 2.500000
    endloop
  endfacet
  facet normal -0.214072 -0.283782 0.934687
    outer loop
      vertex -34.766998 -83.767998 2.634000
      vertex -34.931000 -84.000000 2.526000
      vertex -34.620998 -84.000000 2.597000
    endloop
  endfacet
  facet normal -0.071874 -0.546533 0.834348
    outer loop
      vertex -41.882999 -4.164000 3.028000
      vertex -40.500000 -3.378000 3.662000
      vertex -41.632999 -3.229000 3.662000
    endloop
  endfacet
  facet normal -0.293189 -0.225271 0.929136
    outer loop
      vertex -34.766998 -83.767998 2.634000
      vertex -35.165001 -83.250000 2.634000
      vertex -34.931000 -84.000000 2.526000
    endloop
  endfacet
  facet normal -0.485493 -0.373027 0.790663
    outer loop
      vertex -34.766998 -83.767998 2.634000
      vertex -34.620998 -83.621002 2.793000
      vertex -35.165001 -83.250000 2.634000
    endloop
  endfacet
  facet normal 0.377657 0.916637 0.130962
    outer loop
      vertex -80.482002 17.896000 3.241000
      vertex -80.732002 17.999001 3.241000
      vertex -80.499001 17.865999 3.500000
    endloop
  endfacet
  facet normal 0.793058 0.609146 -0.000000
    outer loop
      vertex -80.292000 17.707001 3.500000
      vertex -80.292000 17.707001 10.500000
      vertex -80.133003 17.500000 10.500000
    endloop
  endfacet
  facet normal 0.793058 0.609146 -0.000000
    outer loop
      vertex -80.133003 17.500000 3.500000
      vertex -80.292000 17.707001 3.500000
      vertex -80.133003 17.500000 10.500000
    endloop
  endfacet
  facet normal 0.603924 0.786251 0.130709
    outer loop
      vertex -80.482002 17.896000 3.241000
      vertex -80.499001 17.865999 3.500000
      vertex -80.292000 17.707001 3.500000
    endloop
  endfacet
  facet normal -0.083737 -0.167577 0.982296
    outer loop
      vertex -34.931000 -84.000000 2.526000
      vertex -35.165001 -83.250000 2.634000
      vertex -35.236000 -84.000000 2.500000
    endloop
  endfacet
  facet normal 0.923634 0.383275 0.000000
    outer loop
      vertex -80.133003 17.500000 10.500000
      vertex -80.032997 17.259001 10.500000
      vertex -80.032997 17.259001 3.500000
    endloop
  endfacet
  facet normal -0.251692 -0.045548 0.966735
    outer loop
      vertex -35.646999 -82.709000 2.534000
      vertex -35.652000 -83.403000 2.500000
      vertex -35.165001 -83.250000 2.634000
    endloop
  endfacet
  facet normal -0.102166 -0.042328 0.993866
    outer loop
      vertex -46.714001 -0.665000 2.634000
      vertex -47.514999 -1.878000 2.500000
      vertex -46.070999 -2.217000 2.634000
    endloop
  endfacet
  facet normal -0.356738 -0.147311 0.922517
    outer loop
      vertex -35.165001 -83.250000 2.634000
      vertex -35.414001 -82.647003 2.634000
      vertex -35.646999 -82.709000 2.534000
    endloop
  endfacet
  facet normal -0.106373 -0.060802 0.992466
    outer loop
      vertex -46.070999 -2.217000 2.634000
      vertex -47.514999 -1.878000 2.500000
      vertex -46.541000 -3.582000 2.500000
    endloop
  endfacet
  facet normal -0.317015 -0.131341 0.939282
    outer loop
      vertex -46.070999 -2.217000 2.634000
      vertex -45.129002 -1.673000 3.028000
      vertex -46.714001 -0.665000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.236000 -84.000000 2.500000
      vertex -35.652000 -83.403000 2.500000
      vertex -92.999001 -84.000000 2.500000
    endloop
  endfacet
  facet normal 0.799984 0.331473 0.500152
    outer loop
      vertex -37.039001 1.927000 4.501000
      vertex -37.396999 2.791000 4.501000
      vertex -37.901001 2.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 -84.000000 2.500000
      vertex -45.162998 -62.979000 2.500000
      vertex -47.028000 -60.730000 2.500000
    endloop
  endfacet
  facet normal 0.092385 0.722515 0.685155
    outer loop
      vertex -88.379997 5.233000 3.662000
      vertex -89.514000 5.378000 3.662000
      vertex -89.511002 4.582000 4.501000
    endloop
  endfacet
  facet normal -0.272302 -0.208928 0.939255
    outer loop
      vertex -45.049000 -3.549000 2.634000
      vertex -44.279999 -2.780000 3.028000
      vertex -46.070999 -2.217000 2.634000
    endloop
  endfacet
  facet normal 0.092715 0.722247 0.685393
    outer loop
      vertex -88.379997 5.233000 3.662000
      vertex -89.511002 4.582000 4.501000
      vertex -88.584000 4.463000 4.501000
    endloop
  endfacet
  facet normal -0.087772 -0.067344 0.993862
    outer loop
      vertex -46.541000 -3.582000 2.500000
      vertex -45.049000 -3.549000 2.634000
      vertex -46.070999 -2.217000 2.634000
    endloop
  endfacet
  facet normal 0.069906 0.546712 0.834397
    outer loop
      vertex -89.516998 6.346000 3.028000
      vertex -89.514000 5.378000 3.662000
      vertex -88.379997 5.233000 3.662000
    endloop
  endfacet
  facet normal 0.686747 0.527498 0.500124
    outer loop
      vertex -37.901001 2.500000 5.500000
      vertex -37.396999 2.791000 4.501000
      vertex -38.377998 3.121000 5.500000
    endloop
  endfacet
  facet normal 0.069921 0.546723 0.834389
    outer loop
      vertex -89.516998 6.346000 3.028000
      vertex -88.379997 5.233000 3.662000
      vertex -88.133003 6.169000 3.028000
    endloop
  endfacet
  facet normal 0.686733 0.527544 0.500095
    outer loop
      vertex -38.377998 3.121000 5.500000
      vertex -37.396999 2.791000 4.501000
      vertex -37.966999 3.533000 4.501000
    endloop
  endfacet
  facet normal -0.317186 -0.131648 0.939182
    outer loop
      vertex -45.129002 -1.673000 3.028000
      vertex -45.664001 -0.384000 3.028000
      vertex -46.714001 -0.665000 2.634000
    endloop
  endfacet
  facet normal 0.443559 0.577641 0.685263
    outer loop
      vertex -38.708000 4.102000 4.501000
      vertex -37.966999 3.533000 4.501000
      vertex -37.403999 4.096000 3.662000
    endloop
  endfacet
  facet normal -0.509162 -0.211328 0.834323
    outer loop
      vertex -44.291000 -1.189000 3.662000
      vertex -45.664001 -0.384000 3.028000
      vertex -45.129002 -1.673000 3.028000
    endloop
  endfacet
  facet normal 0.527257 0.686640 0.500526
    outer loop
      vertex -39.000000 3.598000 5.500000
      vertex -37.966999 3.533000 4.501000
      vertex -38.708000 4.102000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.464996 -57.258999 5.500000
      vertex -92.499001 -57.000000 5.500000
      vertex -92.397003 -57.776001 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -92.397003 -57.776001 5.500000
      vertex -92.097000 -58.500000 5.500000
      vertex -90.464996 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -91.620003 -59.120998 5.500000
      vertex -89.999001 -57.866001 5.500000
      vertex -90.206001 -57.707001 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -90.364998 -57.500000 5.500000
      vertex -90.464996 -57.258999 5.500000
      vertex -92.097000 -58.500000 5.500000
    endloop
  endfacet
  facet normal -0.577857 0.442789 0.685579
    outer loop
      vertex -44.291000 -54.811001 3.662000
      vertex -43.032001 -54.466999 4.501000
      vertex -43.596001 -53.903999 3.662000
    endloop
  endfacet
  facet normal 0.605501 0.785338 0.128886
    outer loop
      vertex -80.482002 17.896000 3.241000
      vertex -80.292000 17.707001 3.500000
      vertex -80.267998 17.731001 3.241000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex 80.000000 -82.000000 10.500000
      vertex 80.000000 83.000000 2.500000
      vertex 80.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal 0.786447 0.604067 0.128857
    outer loop
      vertex -80.133003 17.500000 3.500000
      vertex -80.267998 17.731001 3.241000
      vertex -80.292000 17.707001 3.500000
    endloop
  endfacet
  facet normal -0.685380 -0.529567 0.499812
    outer loop
      vertex -92.595001 -58.801998 4.501000
      vertex -92.024002 -59.541000 4.501000
      vertex -91.620003 -59.120998 5.500000
    endloop
  endfacet
  facet normal -0.722175 0.094972 0.685160
    outer loop
      vertex -44.082001 -57.000000 4.501000
      vertex -44.729000 -55.867001 3.662000
      vertex -44.877998 -57.000000 3.662000
    endloop
  endfacet
  facet normal 0.787219 0.603293 0.127764
    outer loop
      vertex -80.267998 17.731001 3.241000
      vertex -80.133003 17.500000 3.500000
      vertex -80.103996 17.517000 3.241000
    endloop
  endfacet
  facet normal -0.722121 0.095038 0.685208
    outer loop
      vertex -44.729000 -55.867001 3.662000
      vertex -44.082001 -57.000000 4.501000
      vertex -43.959999 -56.073002 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 -84.000000 0.000000
      vertex 82.998001 83.181046 3.331524
      vertex 82.998001 83.015015 3.500000
    endloop
  endfacet
  facet normal -0.672882 0.278807 0.685198
    outer loop
      vertex -43.959999 -56.073002 4.501000
      vertex -43.602001 -55.209000 4.501000
      vertex -44.729000 -55.867001 3.662000
    endloop
  endfacet
  facet normal -0.672931 0.279113 0.685025
    outer loop
      vertex -44.729000 -55.867001 3.662000
      vertex -43.602001 -55.209000 4.501000
      vertex -44.291000 -54.811001 3.662000
    endloop
  endfacet
  facet normal -0.509101 0.211161 0.834403
    outer loop
      vertex -44.291000 -54.811001 3.662000
      vertex -45.664001 -55.616001 3.028000
      vertex -44.729000 -55.867001 3.662000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 -84.000000 0.000000
      vertex 82.998001 85.000000 0.000000
      vertex 82.998001 83.270515 3.241000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 82.998001 -84.000000 0.000000
      vertex 82.998001 83.270515 3.241000
      vertex 82.998001 83.181046 3.331524
    endloop
  endfacet
  facet normal -0.526993 -0.686085 0.501563
    outer loop
      vertex -91.620003 -59.120998 5.500000
      vertex -92.024002 -59.541000 4.501000
      vertex -90.999001 -59.598000 5.500000
    endloop
  endfacet
  facet normal 0.923634 0.383275 0.000000
    outer loop
      vertex -80.032997 17.259001 3.500000
      vertex -80.133003 17.500000 3.500000
      vertex -80.133003 17.500000 10.500000
    endloop
  endfacet
  facet normal 0.526948 0.687133 0.500174
    outer loop
      vertex -38.377998 3.121000 5.500000
      vertex -37.966999 3.533000 4.501000
      vertex -39.000000 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.722175 -0.094972 0.685160
    outer loop
      vertex -44.877998 -57.000000 3.662000
      vertex -44.729000 -58.132999 3.662000
      vertex -44.082001 -57.000000 4.501000
    endloop
  endfacet
  facet normal -0.525117 -0.689044 0.499470
    outer loop
      vertex -90.999001 -59.598000 5.500000
      vertex -92.024002 -59.541000 4.501000
      vertex -91.279999 -60.108002 4.501000
    endloop
  endfacet
  facet normal 0.564319 0.731925 0.381877
    outer loop
      vertex -80.267998 17.731001 3.241000
      vertex -80.196999 17.802000 3.000000
      vertex -80.482002 17.896000 3.241000
    endloop
  endfacet
  facet normal -0.546483 -0.071867 0.834381
    outer loop
      vertex -44.877998 -57.000000 3.662000
      vertex -45.846001 -57.000000 3.028000
      vertex -44.729000 -58.132999 3.662000
    endloop
  endfacet
  facet normal 0.331814 0.799672 0.500425
    outer loop
      vertex -39.000000 3.598000 5.500000
      vertex -38.708000 4.102000 4.501000
      vertex -39.723000 3.898000 5.500000
    endloop
  endfacet
  facet normal 0.990992 0.133918 0.000000
    outer loop
      vertex -41.500000 -57.000000 5.500000
      vertex -41.465000 -57.258999 0.000000
      vertex -41.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.990992 -0.133918 -0.000000
    outer loop
      vertex -41.500000 -57.000000 0.000000
      vertex -41.465000 -56.741001 0.000000
      vertex -41.465000 -56.741001 5.500000
    endloop
  endfacet
  facet normal 0.990992 -0.133918 -0.000000
    outer loop
      vertex -41.465000 -56.741001 5.500000
      vertex -41.500000 -57.000000 5.500000
      vertex -41.500000 -57.000000 0.000000
    endloop
  endfacet
  facet normal 0.924998 -0.379973 -0.000000
    outer loop
      vertex -41.366001 -56.500000 0.000000
      vertex -41.465000 -56.741001 5.500000
      vertex -41.465000 -56.741001 0.000000
    endloop
  endfacet
  facet normal 0.924998 -0.379973 0.000000
    outer loop
      vertex -41.366001 -56.500000 5.500000
      vertex -41.465000 -56.741001 5.500000
      vertex -41.366001 -56.500000 0.000000
    endloop
  endfacet
  facet normal 0.331476 0.799986 0.500146
    outer loop
      vertex -38.708000 4.102000 4.501000
      vertex -39.571999 4.460000 4.501000
      vertex -39.723000 3.898000 5.500000
    endloop
  endfacet
  facet normal -0.331622 -0.799211 0.501286
    outer loop
      vertex -90.999001 -59.598000 5.500000
      vertex -91.279999 -60.108002 4.501000
      vertex -90.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal 0.793051 -0.609155 0.000000
    outer loop
      vertex -41.366001 -56.500000 0.000000
      vertex -41.207001 -56.292999 0.000000
      vertex -41.207001 -56.292999 5.500000
    endloop
  endfacet
  facet normal 0.793051 -0.609155 0.000000
    outer loop
      vertex -41.207001 -56.292999 5.500000
      vertex -41.366001 -56.500000 5.500000
      vertex -41.366001 -56.500000 0.000000
    endloop
  endfacet
  facet normal 0.112868 0.858540 0.500170
    outer loop
      vertex -40.500000 4.000000 5.500000
      vertex -39.571999 4.460000 4.501000
      vertex -40.500000 4.582000 4.501000
    endloop
  endfacet
  facet normal 0.733692 0.562272 0.381506
    outer loop
      vertex -80.016998 17.566999 3.000000
      vertex -80.267998 17.731001 3.241000
      vertex -80.103996 17.517000 3.241000
    endloop
  endfacet
  facet normal 0.609155 -0.793051 0.000000
    outer loop
      vertex -41.000000 -56.133999 5.500000
      vertex -41.207001 -56.292999 5.500000
      vertex -41.207001 -56.292999 0.000000
    endloop
  endfacet
  facet normal 0.112715 0.858621 0.500065
    outer loop
      vertex -39.571999 4.460000 4.501000
      vertex -40.500000 4.000000 5.500000
      vertex -39.723000 3.898000 5.500000
    endloop
  endfacet
  facet normal -0.276485 -0.673688 0.685347
    outer loop
      vertex -90.415001 -60.463001 4.501000
      vertex -91.279999 -60.108002 4.501000
      vertex -91.676003 -60.799000 3.662000
    endloop
  endfacet
  facet normal -0.112857 0.858598 0.500073
    outer loop
      vertex -40.500000 4.000000 5.500000
      vertex -41.426998 4.460000 4.501000
      vertex -41.276001 3.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.500000 4.000000 5.500000
      vertex -41.276001 3.898000 5.500000
      vertex -40.500000 2.000000 5.500000
    endloop
  endfacet
  facet normal 0.733757 0.562027 0.381741
    outer loop
      vertex -80.196999 17.802000 3.000000
      vertex -80.267998 17.731001 3.241000
      vertex -80.016998 17.566999 3.000000
    endloop
  endfacet
  facet normal -0.328993 -0.801630 0.499152
    outer loop
      vertex -90.276001 -59.897999 5.500000
      vertex -91.279999 -60.108002 4.501000
      vertex -90.415001 -60.463001 4.501000
    endloop
  endfacet
  facet normal -0.112647 -0.858094 0.500984
    outer loop
      vertex -90.276001 -59.897999 5.500000
      vertex -90.415001 -60.463001 4.501000
      vertex -89.499001 -60.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -40.757999 1.966000 5.500000
      vertex -40.500000 2.000000 5.500000
      vertex -41.276001 3.898000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -40.500000 2.000000 5.500000
      vertex -40.241001 1.966000 5.500000
      vertex -40.500000 4.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -38.377998 3.121000 5.500000
      vertex -39.000000 3.598000 5.500000
      vertex -39.792000 1.707000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.723000 3.898000 5.500000
      vertex -40.500000 4.000000 5.500000
      vertex -40.241001 1.966000 5.500000
    endloop
  endfacet
  facet normal 0.609155 -0.793051 0.000000
    outer loop
      vertex -41.000000 -56.133999 5.500000
      vertex -41.207001 -56.292999 0.000000
      vertex -41.000000 -56.133999 0.000000
    endloop
  endfacet
  facet normal -0.110199 -0.859374 0.499333
    outer loop
      vertex -90.415001 -60.463001 4.501000
      vertex -89.487000 -60.582001 4.501000
      vertex -89.499001 -60.000000 5.500000
    endloop
  endfacet
  facet normal 0.130158 0.991493 0.000000
    outer loop
      vertex -80.999001 18.000000 10.500000
      vertex -80.739998 17.966000 10.500000
      vertex -80.739998 17.966000 3.500000
    endloop
  endfacet
  facet normal 0.381896 -0.924205 0.000000
    outer loop
      vertex -41.000000 -56.133999 0.000000
      vertex -40.757999 -56.034000 0.000000
      vertex -41.000000 -56.133999 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -90.276001 -59.897999 5.500000
      vertex -89.499001 -60.000000 5.500000
      vertex -89.758003 -57.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 -57.966000 5.500000
      vertex -90.999001 -59.598000 5.500000
      vertex -90.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal 0.276485 0.673687 0.685348
    outer loop
      vertex -87.322998 4.799000 3.662000
      vertex -88.584000 4.463000 4.501000
      vertex -87.719002 4.108000 4.501000
    endloop
  endfacet
  facet normal 0.276567 0.673574 0.685426
    outer loop
      vertex -87.322998 4.799000 3.662000
      vertex -88.379997 5.233000 3.662000
      vertex -88.584000 4.463000 4.501000
    endloop
  endfacet
  facet normal 0.736920 -0.096985 0.668986
    outer loop
      vertex -37.039001 0.073000 4.501000
      vertex -36.762001 0.674000 4.283000
      vertex -36.917000 1.000000 4.501000
    endloop
  endfacet
  facet normal 0.441449 0.579259 0.685260
    outer loop
      vertex -86.414001 4.106000 3.662000
      vertex -87.719002 4.108000 4.501000
      vertex -86.974998 3.541000 4.501000
    endloop
  endfacet
  facet normal -0.272275 0.208819 0.939288
    outer loop
      vertex -45.129002 -54.327000 3.028000
      vertex -44.279999 -53.220001 3.028000
      vertex -46.070999 -53.783001 2.634000
    endloop
  endfacet
  facet normal 0.441505 0.579115 0.685346
    outer loop
      vertex -87.719002 4.108000 4.501000
      vertex -86.414001 4.106000 3.662000
      vertex -87.322998 4.799000 3.662000
    endloop
  endfacet
  facet normal -0.272302 0.208928 0.939255
    outer loop
      vertex -46.070999 -53.783001 2.634000
      vertex -44.279999 -53.220001 3.028000
      vertex -45.049000 -52.451000 2.634000
    endloop
  endfacet
  facet normal 0.209338 0.509916 0.834364
    outer loop
      vertex -88.133003 6.169000 3.028000
      vertex -88.379997 5.233000 3.662000
      vertex -86.842003 5.639000 3.028000
    endloop
  endfacet
  facet normal 0.858159 -0.112941 0.500807
    outer loop
      vertex -37.500000 1.000000 5.500000
      vertex -37.039001 0.073000 4.501000
      vertex -36.917000 1.000000 4.501000
    endloop
  endfacet
  facet normal 0.813990 -0.001423 0.580877
    outer loop
      vertex -36.917000 1.000000 4.501000
      vertex -36.762001 0.674000 4.283000
      vertex -36.763000 1.327000 4.286000
    endloop
  endfacet
  facet normal -0.144673 0.082642 0.986022
    outer loop
      vertex -46.714001 -55.334999 2.634000
      vertex -45.162998 -51.021000 2.500000
      vertex -48.018002 -56.019001 2.500000
    endloop
  endfacet
  facet normal 0.858172 0.112802 0.500815
    outer loop
      vertex -37.500000 1.000000 5.500000
      vertex -36.917000 1.000000 4.501000
      vertex -37.602001 1.776000 5.500000
    endloop
  endfacet
  facet normal 0.209355 0.509880 0.834382
    outer loop
      vertex -86.842003 5.639000 3.028000
      vertex -88.379997 5.233000 3.662000
      vertex -87.322998 4.799000 3.662000
    endloop
  endfacet
  facet normal 0.858206 0.112948 0.500725
    outer loop
      vertex -37.602001 1.776000 5.500000
      vertex -36.917000 1.000000 4.501000
      vertex -37.039001 1.927000 4.501000
    endloop
  endfacet
  facet normal 0.686269 -0.527131 0.501167
    outer loop
      vertex -87.377998 -1.121000 5.500000
      vertex -86.958000 -1.524000 4.501000
      vertex -86.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal -0.176227 -0.037034 0.983653
    outer loop
      vertex -46.714001 -58.665001 2.634000
      vertex -48.018002 -56.019001 2.500000
      vertex -47.028000 -60.730000 2.500000
    endloop
  endfacet
  facet normal 0.858229 -0.112810 0.500717
    outer loop
      vertex -37.039001 0.073000 4.501000
      vertex -37.500000 1.000000 5.500000
      vertex -37.602001 0.224000 5.500000
    endloop
  endfacet
  facet normal -0.483275 0.200224 0.852265
    outer loop
      vertex -45.162998 -51.021000 2.500000
      vertex -46.714001 -55.334999 2.634000
      vertex -46.070999 -53.783001 2.634000
    endloop
  endfacet
  facet normal 0.733790 0.096573 0.672477
    outer loop
      vertex -36.763000 1.327000 4.286000
      vertex -37.039001 1.927000 4.501000
      vertex -36.917000 1.000000 4.501000
    endloop
  endfacet
  facet normal -0.317015 0.131341 0.939282
    outer loop
      vertex -46.714001 -55.334999 2.634000
      vertex -45.129002 -54.327000 3.028000
      vertex -46.070999 -53.783001 2.634000
    endloop
  endfacet
  facet normal 0.688718 -0.525578 0.499435
    outer loop
      vertex -86.901001 -0.500000 5.500000
      vertex -86.958000 -1.524000 4.501000
      vertex -86.390999 -0.781000 4.501000
    endloop
  endfacet
  facet normal 0.799383 -0.331239 0.501266
    outer loop
      vertex -86.600998 0.224000 5.500000
      vertex -86.901001 -0.500000 5.500000
      vertex -86.390999 -0.781000 4.501000
    endloop
  endfacet
  facet normal -0.437599 0.335613 0.834189
    outer loop
      vertex -43.596001 -53.903999 3.662000
      vertex -44.279999 -53.220001 3.028000
      vertex -45.129002 -54.327000 3.028000
    endloop
  endfacet
  facet normal 0.737328 0.099759 0.668129
    outer loop
      vertex -36.763000 1.327000 4.286000
      vertex -36.742001 1.654000 4.214000
      vertex -37.039001 1.927000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.633003 0.500000 5.500000
      vertex -87.377998 -1.121000 5.500000
      vertex -86.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -86.901001 -0.500000 5.500000
      vertex -86.600998 0.224000 5.500000
      vertex -88.532997 0.741000 5.500000
    endloop
  endfacet
  facet normal 0.130391 0.317612 0.939213
    outer loop
      vertex -86.301003 6.582000 2.634000
      vertex -88.133003 6.169000 3.028000
      vertex -86.842003 5.639000 3.028000
    endloop
  endfacet
  facet normal -0.109698 0.014429 0.993860
    outer loop
      vertex -48.018002 -56.019001 2.500000
      vertex -46.932999 -57.000000 2.634000
      vertex -46.714001 -55.334999 2.634000
    endloop
  endfacet
  facet normal 0.800022 0.330396 0.500803
    outer loop
      vertex -37.602001 1.776000 5.500000
      vertex -37.039001 1.927000 4.501000
      vertex -37.901001 2.500000 5.500000
    endloop
  endfacet
  facet normal 0.334138 0.438408 0.834356
    outer loop
      vertex -87.322998 4.799000 3.662000
      vertex -85.732002 4.793000 3.028000
      vertex -86.842003 5.639000 3.028000
    endloop
  endfacet
  facet normal -0.138791 -0.018255 0.990153
    outer loop
      vertex -48.018002 -56.019001 2.500000
      vertex -46.714001 -58.665001 2.634000
      vertex -46.932999 -57.000000 2.634000
    endloop
  endfacet
  facet normal 0.334156 0.438307 0.834402
    outer loop
      vertex -86.414001 4.106000 3.662000
      vertex -85.732002 4.793000 3.028000
      vertex -87.322998 4.799000 3.662000
    endloop
  endfacet
  facet normal 0.435958 0.337237 0.834393
    outer loop
      vertex -85.732002 4.793000 3.028000
      vertex -86.414001 4.106000 3.662000
      vertex -84.877998 3.689000 3.028000
    endloop
  endfacet
  facet normal 0.683116 -0.283049 0.673228
    outer loop
      vertex -37.039001 0.073000 4.501000
      vertex -37.396999 -0.791000 4.501000
      vertex -36.667999 -0.316000 3.961000
    endloop
  endfacet
  facet normal -0.437570 0.335293 0.834333
    outer loop
      vertex -43.596001 -53.903999 3.662000
      vertex -45.129002 -54.327000 3.028000
      vertex -44.291000 -54.811001 3.662000
    endloop
  endfacet
  facet normal 0.799984 -0.331473 0.500152
    outer loop
      vertex -37.396999 -0.791000 4.501000
      vertex -37.039001 0.073000 4.501000
      vertex -37.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.128884 0.983200 0.129255
    outer loop
      vertex -80.999001 18.034000 3.241000
      vertex -80.739998 17.966000 3.500000
      vertex -80.732002 17.999001 3.241000
    endloop
  endfacet
  facet normal 0.800022 -0.330396 0.500803
    outer loop
      vertex -37.039001 0.073000 4.501000
      vertex -37.602001 0.224000 5.500000
      vertex -37.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.129069 0.983200 0.129070
    outer loop
      vertex -80.999001 18.034000 3.241000
      vertex -80.999001 18.000000 3.500000
      vertex -80.739998 17.966000 3.500000
    endloop
  endfacet
  facet normal -0.721518 -0.097520 0.685494
    outer loop
      vertex -93.877998 -57.014999 3.662000
      vertex -93.724998 -58.146999 3.662000
      vertex -92.956001 -57.938999 4.501000
    endloop
  endfacet
  facet normal -0.671738 -0.280794 0.685509
    outer loop
      vertex -92.595001 -58.801998 4.501000
      vertex -93.724998 -58.146999 3.662000
      vertex -93.283997 -59.202000 3.662000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -37.602001 0.224000 5.500000
      vertex -37.500000 1.000000 5.500000
      vertex -39.534000 0.741000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.602001 1.776000 5.500000
      vertex -37.901001 2.500000 5.500000
      vertex -39.534000 1.259000 5.500000
    endloop
  endfacet
  facet normal 0.207922 0.273142 0.939235
    outer loop
      vertex -86.842003 5.639000 3.028000
      vertex -84.964996 5.565000 2.634000
      vertex -86.301003 6.582000 2.634000
    endloop
  endfacet
  facet normal -0.317185 0.131648 0.939182
    outer loop
      vertex -45.664001 -55.616001 3.028000
      vertex -45.129002 -54.327000 3.028000
      vertex -46.714001 -55.334999 2.634000
    endloop
  endfacet
  facet normal -0.671772 -0.281008 0.685388
    outer loop
      vertex -92.956001 -57.938999 4.501000
      vertex -93.724998 -58.146999 3.662000
      vertex -92.595001 -58.801998 4.501000
    endloop
  endfacet
  facet normal 0.207929 0.272815 0.939328
    outer loop
      vertex -84.964996 5.565000 2.634000
      vertex -86.842003 5.639000 3.028000
      vertex -85.732002 4.793000 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.000000 3.598000 5.500000
      vertex -39.723000 3.898000 5.500000
      vertex -40.241001 1.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.901001 2.500000 5.500000
      vertex -38.377998 3.121000 5.500000
      vertex -39.792000 1.707000 5.500000
    endloop
  endfacet
  facet normal -0.073778 0.546343 0.834306
    outer loop
      vertex -89.514000 5.378000 3.662000
      vertex -90.900002 6.159000 3.028000
      vertex -90.647003 5.225000 3.662000
    endloop
  endfacet
  facet normal -0.576188 -0.445198 0.685424
    outer loop
      vertex -93.283997 -59.202000 3.662000
      vertex -92.024002 -59.541000 4.501000
      vertex -92.595001 -58.801998 4.501000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -39.633999 1.500000 5.500000
      vertex -39.534000 1.259000 5.500000
      vertex -37.901001 2.500000 5.500000
    endloop
  endfacet
  facet normal -0.509162 0.211327 0.834323
    outer loop
      vertex -44.291000 -54.811001 3.662000
      vertex -45.129002 -54.327000 3.028000
      vertex -45.664001 -55.616001 3.028000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -39.792000 1.707000 5.500000
      vertex -39.633999 1.500000 5.500000
      vertex -37.901001 2.500000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -39.534000 1.259000 5.500000
      vertex -37.500000 1.000000 5.500000
      vertex -37.602001 1.776000 5.500000
    endloop
  endfacet
  facet normal 0.609155 0.793051 -0.000000
    outer loop
      vertex -89.999001 -57.866001 5.500000
      vertex -90.206001 -57.707001 0.000000
      vertex -90.206001 -57.707001 5.500000
    endloop
  endfacet
  facet normal 0.793058 0.609146 -0.000000
    outer loop
      vertex -90.206001 -57.707001 0.000000
      vertex -90.364998 -57.500000 5.500000
      vertex -90.206001 -57.707001 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.000000 1.866000 5.500000
      vertex -40.757999 1.966000 5.500000
      vertex -41.276001 3.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -42.620998 3.121000 5.500000
      vertex -43.098000 2.500000 5.500000
      vertex -41.366001 1.500000 5.500000
    endloop
  endfacet
  facet normal 0.923646 0.383248 -0.000000
    outer loop
      vertex -90.364998 -57.500000 5.500000
      vertex -90.464996 -57.258999 0.000000
      vertex -90.464996 -57.258999 5.500000
    endloop
  endfacet
  facet normal -0.437570 -0.335294 0.834332
    outer loop
      vertex -44.291000 -1.189000 3.662000
      vertex -45.129002 -1.673000 3.028000
      vertex -43.596001 -2.096000 3.662000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex -80.999001 18.000000 3.500000
      vertex -92.999001 18.000000 3.500000
      vertex -92.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal -0.272275 -0.208818 0.939288
    outer loop
      vertex -45.129002 -1.673000 3.028000
      vertex -46.070999 -2.217000 2.634000
      vertex -44.279999 -2.780000 3.028000
    endloop
  endfacet
  facet normal -0.437599 -0.335612 0.834189
    outer loop
      vertex -43.596001 -2.096000 3.662000
      vertex -45.129002 -1.673000 3.028000
      vertex -44.279999 -2.780000 3.028000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 80.000000 -82.000000 10.500000
      vertex 80.000000 -82.000000 2.500000
      vertex 25.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.092383 -0.722516 0.685154
    outer loop
      vertex -89.484001 -61.377998 3.662000
      vertex -89.487000 -60.582001 4.501000
      vertex -90.617996 -61.233002 3.662000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 25.000000 -82.000000 10.500000
      vertex 80.000000 -82.000000 2.500000
      vertex 25.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal -0.092625 -0.722321 0.685327
    outer loop
      vertex -90.617996 -61.233002 3.662000
      vertex -89.487000 -60.582001 4.501000
      vertex -90.415001 -60.463001 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex 25.000000 83.000000 10.500000
      vertex 25.000000 -82.000000 2.500000
      vertex 25.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 1.000000 -0.000000 0.000000
    outer loop
      vertex 25.000000 -82.000000 10.500000
      vertex 25.000000 -82.000000 2.500000
      vertex 25.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal -0.276400 -0.673805 0.685266
    outer loop
      vertex -90.617996 -61.233002 3.662000
      vertex -90.415001 -60.463001 4.501000
      vertex -91.676003 -60.799000 3.662000
    endloop
  endfacet
  facet normal 0.672141 0.281162 0.684963
    outer loop
      vertex -86.403000 2.802000 4.501000
      vertex -86.042000 1.939000 4.501000
      vertex -85.274002 2.147000 3.662000
    endloop
  endfacet
  facet normal -0.302303 -0.393910 0.868014
    outer loop
      vertex -45.049000 -3.549000 2.634000
      vertex -41.582001 -6.505000 2.500000
      vertex -43.716000 -4.572000 2.634000
    endloop
  endfacet
  facet normal 0.672106 0.280943 0.685087
    outer loop
      vertex -86.403000 2.802000 4.501000
      vertex -85.274002 2.147000 3.662000
      vertex -85.714996 3.202000 3.662000
    endloop
  endfacet
  facet normal -0.131291 -0.317165 0.939239
    outer loop
      vertex -43.716000 -4.572000 2.634000
      vertex -41.882999 -4.164000 3.028000
      vertex -43.173000 -3.630000 3.028000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex 23.000000 85.000000 10.500000
      vertex 23.000000 85.000000 0.000000
      vertex -92.999001 85.000000 0.000000
    endloop
  endfacet
  facet normal -0.131288 -0.317176 0.939235
    outer loop
      vertex -43.716000 -4.572000 2.634000
      vertex -42.165001 -5.214000 2.634000
      vertex -41.882999 -4.164000 3.028000
    endloop
  endfacet
  facet normal -0.044945 -0.340150 0.939297
    outer loop
      vertex -40.500000 -5.434000 2.634000
      vertex -40.500000 -4.346000 3.028000
      vertex -42.165001 -5.214000 2.634000
    endloop
  endfacet
  facet normal -0.209191 -0.509965 0.834371
    outer loop
      vertex -92.156998 -61.639000 3.028000
      vertex -90.617996 -61.233002 3.662000
      vertex -91.676003 -60.799000 3.662000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex -92.999001 85.000000 0.000000
      vertex -92.999001 85.000000 10.500000
      vertex 23.000000 85.000000 10.500000
    endloop
  endfacet
  facet normal 0.508427 0.212525 0.834467
    outer loop
      vertex -84.877998 3.689000 3.028000
      vertex -85.714996 3.202000 3.662000
      vertex -85.274002 2.147000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 24.000000 84.732002 10.500000
      vertex 23.000000 83.000000 10.500000
      vertex 25.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 -2.000000 5.500000
      vertex -89.239998 0.034000 5.500000
      vertex -89.499001 0.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 0.034000 5.500000
      vertex -90.276001 -1.898000 5.500000
      vertex -89.499001 -2.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.758003 0.034000 5.500000
      vertex -90.999001 -1.598000 5.500000
      vertex -90.276001 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.239998 0.034000 5.500000
      vertex -88.723000 -1.898000 5.500000
      vertex -87.999001 -1.598000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.999001 0.134000 5.500000
      vertex -87.999001 -1.598000 5.500000
      vertex -87.377998 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.377998 -1.121000 5.500000
      vertex -88.633003 0.500000 5.500000
      vertex -88.792000 0.293000 5.500000
    endloop
  endfacet
  facet normal -0.085333 -0.144771 0.985779
    outer loop
      vertex -46.541000 -3.582000 2.500000
      vertex -41.582001 -6.505000 2.500000
      vertex -45.049000 -3.549000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 83.000000 10.500000
      vertex 24.482000 84.931999 10.500000
      vertex 24.000000 84.732002 10.500000
    endloop
  endfacet
  facet normal 0.271482 0.210006 0.939252
    outer loop
      vertex -85.732002 4.793000 3.028000
      vertex -84.877998 3.689000 3.028000
      vertex -83.938004 4.236000 2.634000
    endloop
  endfacet
  facet normal 0.508601 0.212445 0.834381
    outer loop
      vertex -84.339996 2.401000 3.028000
      vertex -84.877998 3.689000 3.028000
      vertex -85.274002 2.147000 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 83.000000 10.500000
      vertex 25.000000 -82.000000 10.500000
      vertex 25.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 85.000000 10.500000
      vertex 25.000000 83.000000 10.500000
      vertex 80.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex 25.000000 83.000000 10.500000
      vertex 25.000000 85.000000 10.500000
      vertex 24.482000 84.931999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 83.000000 10.500000
      vertex 24.000000 84.732002 10.500000
      vertex 23.518000 84.931999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.518000 84.931999 10.500000
      vertex 23.000000 85.000000 10.500000
      vertex 23.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex 23.000000 83.000000 10.500000
      vertex 23.000000 85.000000 10.500000
      vertex -32.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal -0.052344 -0.126457 0.990590
    outer loop
      vertex -43.716000 -4.572000 2.634000
      vertex -41.582001 -6.505000 2.500000
      vertex -42.165001 -5.214000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 85.000000 10.500000
      vertex -35.000000 83.000000 10.500000
      vertex -32.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal -0.014495 -0.109704 0.993859
    outer loop
      vertex -40.500000 -5.434000 2.634000
      vertex -42.165001 -5.214000 2.634000
      vertex -41.582001 -6.505000 2.500000
    endloop
  endfacet
  facet normal -0.001624 -0.122533 0.992463
    outer loop
      vertex -40.500000 -5.434000 2.634000
      vertex -41.582001 -6.505000 2.500000
      vertex -39.619999 -6.531000 2.500000
    endloop
  endfacet
  facet normal 0.316655 0.132383 0.939257
    outer loop
      vertex -83.938004 4.236000 2.634000
      vertex -84.877998 3.689000 3.028000
      vertex -83.290001 2.686000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 83.000000 10.500000
      vertex -35.000000 18.000000 10.500000
      vertex -35.000000 14.000000 10.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 83.000000 10.500000
      vertex -35.000000 18.000000 10.500000
      vertex -32.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal -0.044796 -0.340398 0.939214
    outer loop
      vertex -40.500000 -4.346000 3.028000
      vertex -41.882999 -4.164000 3.028000
      vertex -42.165001 -5.214000 2.634000
    endloop
  endfacet
  facet normal 0.316573 0.132234 0.939306
    outer loop
      vertex -83.290001 2.686000 2.634000
      vertex -84.877998 3.689000 3.028000
      vertex -84.339996 2.401000 3.028000
    endloop
  endfacet
  facet normal -0.071916 -0.546482 0.834377
    outer loop
      vertex -40.500000 -3.378000 3.662000
      vertex -41.882999 -4.164000 3.028000
      vertex -40.500000 -4.346000 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 18.000000 10.500000
      vertex -48.999001 18.000000 10.500000
      vertex -37.000000 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 18.000000 10.500000
      vertex -36.481998 15.932000 10.500000
      vertex -36.000000 15.732000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -48.999001 18.000000 10.500000
      vertex -49.257999 16.034000 10.500000
      vertex -48.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -46.541000 -3.582000 2.500000
      vertex -47.514999 -1.878000 2.500000
      vertex -94.999001 -32.768002 2.500000
    endloop
  endfacet
  facet normal 0.109642 0.014759 0.993862
    outer loop
      vertex -83.290001 2.686000 2.634000
      vertex -83.066002 1.022000 2.634000
      vertex -81.975998 1.948000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.499001 17.865999 10.500000
      vertex -49.707001 17.707001 10.500000
      vertex -49.865002 17.500000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.499001 17.865999 10.500000
      vertex -49.865002 17.500000 10.500000
      vertex -49.965000 17.259001 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.499001 17.865999 10.500000
      vertex -49.965000 17.259001 10.500000
      vertex -49.999001 17.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.499001 17.865999 10.500000
      vertex -49.999001 17.000000 10.500000
      vertex -49.965000 16.740999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.499001 17.865999 10.500000
      vertex -49.965000 16.740999 10.500000
      vertex -49.865002 16.500000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.865002 16.500000 10.500000
      vertex -49.257999 17.966000 10.500000
      vertex -49.499001 17.865999 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -49.707001 16.292999 10.500000
      vertex -49.257999 17.966000 10.500000
      vertex -49.865002 16.500000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.257999 17.966000 10.500000
      vertex -49.707001 16.292999 10.500000
      vertex -49.499001 16.134001 10.500000
    endloop
  endfacet
  facet normal 0.125568 0.043613 0.991126
    outer loop
      vertex -83.290001 2.686000 2.634000
      vertex -81.975998 1.948000 2.500000
      vertex -82.903000 4.617000 2.500000
    endloop
  endfacet
  facet normal 0.111380 0.046564 0.992686
    outer loop
      vertex -82.903000 4.617000 2.500000
      vertex -83.938004 4.236000 2.634000
      vertex -83.290001 2.686000 2.634000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -35.068001 14.518000 10.500000
      vertex -35.000000 14.000000 10.500000
      vertex -35.000000 18.000000 10.500000
    endloop
  endfacet
  facet normal -0.923645 0.000000 0.383249
    outer loop
      vertex -35.034000 -5.103000 3.241000
      vertex -35.133999 -50.896999 3.000000
      vertex -35.034000 -50.896999 3.241000
    endloop
  endfacet
  facet normal 0.112773 -0.857959 0.501187
    outer loop
      vertex -89.499001 -2.000000 5.500000
      vertex -89.487000 -2.582000 4.501000
      vertex -88.723000 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 18.000000 10.500000
      vertex -35.268002 15.000000 10.500000
      vertex -35.068001 14.518000 10.500000
    endloop
  endfacet
  facet normal -0.794901 0.000000 0.606739
    outer loop
      vertex -35.133999 -50.896999 3.000000
      vertex -35.133999 -5.103000 3.000000
      vertex -35.292000 -5.103000 2.793000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -37.000000 16.000000 10.500000
      vertex -36.481998 15.932000 10.500000
      vertex -35.000000 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 18.000000 10.500000
      vertex -35.584999 15.414000 10.500000
      vertex -35.268002 15.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 18.000000 10.500000
      vertex -36.000000 15.732000 10.500000
      vertex -35.584999 15.414000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -81.975998 1.948000 2.500000
      vertex -81.975998 0.052000 2.500000
      vertex -48.018002 1.000000 2.500000
    endloop
  endfacet
  facet normal -0.607308 -0.000000 0.794467
    outer loop
      vertex -35.500000 -50.896999 2.634000
      vertex -35.292000 -50.896999 2.793000
      vertex -35.292000 -5.103000 2.793000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -48.999001 16.000000 10.500000
      vertex -37.000000 16.000000 10.500000
      vertex -48.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.097355 -0.721986 0.685024
    outer loop
      vertex -88.559998 -2.457000 4.501000
      vertex -89.487000 -2.582000 4.501000
      vertex -88.351997 -3.225000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 14.000000 10.500000
      vertex -35.000000 -65.536003 10.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.130158 0.000000 0.991493
    outer loop
      vertex -36.000000 -32.768002 2.500000
      vertex -35.741001 -5.103000 2.534000
      vertex -36.000000 -5.103000 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -49.499001 16.134001 10.500000
      vertex -49.257999 16.034000 10.500000
      vertex -48.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -48.999001 18.000000 10.500000
      vertex -49.257999 17.966000 10.500000
      vertex -49.499001 16.134001 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -35.000000 83.000000 10.500000
      vertex 23.000000 85.000000 10.500000
      vertex -92.999001 85.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -36.000000 -32.768002 2.500000
      vertex -36.000000 -5.103000 2.500000
      vertex -39.619999 -6.531000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.582001 -6.505000 2.500000
      vertex -84.654999 -51.167000 2.500000
      vertex -36.000000 -32.768002 2.500000
    endloop
  endfacet
  facet normal 0.115781 -0.858631 0.499347
    outer loop
      vertex -88.723000 -1.898000 5.500000
      vertex -89.487000 -2.582000 4.501000
      vertex -88.559998 -2.457000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 85.000000 10.500000
      vertex -92.999001 83.000000 10.500000
      vertex -35.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.721943 0.097577 0.685038
    outer loop
      vertex -85.121002 1.015000 3.662000
      vertex -85.274002 2.147000 3.662000
      vertex -86.042000 1.939000 4.501000
    endloop
  endfacet
  facet normal 0.721835 0.097335 0.685186
    outer loop
      vertex -85.121002 1.015000 3.662000
      vertex -86.042000 1.939000 4.501000
      vertex -85.917000 1.012000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -93.516998 84.931999 10.500000
      vertex -93.999001 84.732002 10.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -93.999001 84.732002 10.500000
      vertex -94.413002 84.414001 10.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.413002 84.414001 10.500000
      vertex -94.731003 84.000000 10.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.731003 84.000000 10.500000
      vertex -94.931000 83.517998 10.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.931000 83.517998 10.500000
      vertex -94.999001 83.000000 10.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -92.999001 83.000000 10.500000
      vertex -92.999001 85.000000 10.500000
      vertex -93.516998 84.931999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 18.000000 10.500000
      vertex -92.999001 83.000000 10.500000
      vertex -94.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -92.999001 83.000000 10.500000
      vertex -94.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.331223 -0.799351 0.501328
    outer loop
      vertex -88.723000 -1.898000 5.500000
      vertex -88.559998 -2.457000 4.501000
      vertex -87.999001 -1.598000 5.500000
    endloop
  endfacet
  facet normal 0.546243 0.073858 0.834364
    outer loop
      vertex -84.339996 2.401000 3.028000
      vertex -85.121002 1.015000 3.662000
      vertex -84.153000 1.018000 3.028000
    endloop
  endfacet
  facet normal -0.383253 0.000000 0.923643
    outer loop
      vertex -35.741001 -5.103000 2.534000
      vertex -35.741001 -50.896999 2.534000
      vertex -35.500000 -50.896999 2.634000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -80.032997 16.740999 10.500000
      vertex -79.999001 17.000000 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.999001 16.000000 10.500000
      vertex -80.133003 16.500000 10.500000
      vertex -80.032997 16.740999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -79.999001 17.000000 10.500000
      vertex -80.032997 17.259001 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.032997 17.259001 10.500000
      vertex -80.133003 17.500000 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.133003 17.500000 10.500000
      vertex -80.292000 17.707001 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.292000 17.707001 10.500000
      vertex -80.499001 17.865999 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.499001 17.865999 10.500000
      vertex -80.739998 17.966000 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.739998 17.966000 10.500000
      vertex -80.999001 18.000000 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.999001 18.000000 10.500000
      vertex -92.999001 18.000000 10.500000
      vertex -80.999001 16.000000 10.500000
    endloop
  endfacet
  facet normal -0.130158 0.000000 0.991493
    outer loop
      vertex -35.741001 -5.103000 2.534000
      vertex -36.000000 -32.768002 2.500000
      vertex -35.741001 -50.896999 2.534000
    endloop
  endfacet
  facet normal 0.546711 -0.069904 0.834398
    outer loop
      vertex -84.153000 1.018000 3.028000
      vertex -85.121002 1.015000 3.662000
      vertex -85.265999 -0.119000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.000000 -32.768002 2.500000
      vertex -39.619999 -6.531000 2.500000
      vertex -41.582001 -6.505000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -84.654999 -51.167000 2.500000
      vertex -41.582001 -6.505000 2.500000
      vertex -46.541000 -3.582000 2.500000
    endloop
  endfacet
  facet normal 0.334701 -0.799203 0.499248
    outer loop
      vertex -87.999001 -1.598000 5.500000
      vertex -88.559998 -2.457000 4.501000
      vertex -87.697998 -2.096000 4.501000
    endloop
  endfacet
  facet normal 0.546273 0.073834 0.834347
    outer loop
      vertex -85.121002 1.015000 3.662000
      vertex -84.339996 2.401000 3.028000
      vertex -85.274002 2.147000 3.662000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 -65.536003 10.500000
      vertex -35.000000 14.000000 10.500000
      vertex -35.000000 1.001000 4.946000
    endloop
  endfacet
  facet normal -1.000000 -0.000000 0.000000
    outer loop
      vertex -35.000000 1.001000 4.946000
      vertex -35.000000 -5.103000 3.500000
      vertex -35.000000 -65.536003 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -94.999001 18.000000 10.500000
      vertex -94.931000 17.482000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -94.931000 17.482000 10.500000
      vertex -94.731003 17.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -94.731003 17.000000 10.500000
      vertex -94.413002 16.586000 10.500000
    endloop
  endfacet
  facet normal 0.527194 -0.686350 0.500990
    outer loop
      vertex -87.999001 -1.598000 5.500000
      vertex -87.697998 -2.096000 4.501000
      vertex -87.377998 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.529880 -0.685507 0.499307
    outer loop
      vertex -87.377998 -1.121000 5.500000
      vertex -87.697998 -2.096000 4.501000
      vertex -86.958000 -1.524000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.999001 16.000000 10.500000
      vertex -80.739998 16.034000 10.500000
      vertex -80.499001 16.134001 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.999001 16.000000 10.500000
      vertex -80.499001 16.134001 10.500000
      vertex -80.292000 16.292999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -80.999001 16.000000 10.500000
      vertex -80.292000 16.292999 10.500000
      vertex -80.133003 16.500000 10.500000
    endloop
  endfacet
  facet normal 0.722368 -0.092364 0.685312
    outer loop
      vertex -86.036003 0.084000 4.501000
      vertex -85.265999 -0.119000 3.662000
      vertex -85.121002 1.015000 3.662000
    endloop
  endfacet
  facet normal 0.673765 -0.276513 0.685261
    outer loop
      vertex -85.265999 -0.119000 3.662000
      vertex -86.036003 0.084000 4.501000
      vertex -86.390999 -0.781000 4.501000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -93.516998 16.068001 10.500000
      vertex -92.999001 16.000000 10.500000
      vertex -92.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 16.000000 10.500000
      vertex -80.999001 16.000000 10.500000
      vertex -92.999001 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -93.999001 16.268000 10.500000
      vertex -93.516998 16.068001 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 18.000000 10.500000
      vertex -94.413002 16.586000 10.500000
      vertex -93.999001 16.268000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 -84.000000 10.500000
      vertex 82.998001 -84.000000 10.500000
      vertex 80.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.383253 0.000000 0.923643
    outer loop
      vertex -35.500000 -50.896999 2.634000
      vertex -35.500000 -5.103000 2.634000
      vertex -35.741001 -5.103000 2.534000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 -82.000000 10.500000
      vertex 24.000000 -83.732002 10.500000
      vertex 24.482000 -83.931999 10.500000
    endloop
  endfacet
  facet normal 0.547032 -0.070356 0.834150
    outer loop
      vertex -84.153000 1.018000 3.028000
      vertex -85.265999 -0.119000 3.662000
      vertex -84.331001 -0.366000 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 -82.000000 10.500000
      vertex -32.000000 -82.000000 10.500000
      vertex 23.000000 -84.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -42.527000 -49.759998 2.500000
      vertex -38.667999 -49.708000 2.500000
      vertex -36.000000 -32.768002 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.000000 -32.768002 2.500000
      vertex -84.654999 -51.167000 2.500000
      vertex -45.162998 -51.021000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 -82.000000 10.500000
      vertex 25.000000 -82.000000 10.500000
      vertex 23.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 -82.000000 10.500000
      vertex 23.000000 -84.000000 10.500000
      vertex 23.518000 -83.931999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 23.000000 -82.000000 10.500000
      vertex 23.518000 -83.931999 10.500000
      vertex 24.000000 -83.732002 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex 25.000000 -82.000000 10.500000
      vertex 23.000000 -82.000000 10.500000
      vertex 24.000000 -83.732002 10.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex 24.482000 -83.931999 10.500000
      vertex 25.000000 -84.000000 10.500000
      vertex 25.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal 0.340261 0.046007 0.939205
    outer loop
      vertex -83.066002 1.022000 2.634000
      vertex -84.339996 2.401000 3.028000
      vertex -84.153000 1.018000 3.028000
    endloop
  endfacet
  facet normal 0.510250 -0.209506 0.834118
    outer loop
      vertex -84.331001 -0.366000 3.028000
      vertex -85.265999 -0.119000 3.662000
      vertex -85.699997 -1.176000 3.662000
    endloop
  endfacet
  facet normal 0.340037 0.045774 0.939297
    outer loop
      vertex -84.339996 2.401000 3.028000
      vertex -83.066002 1.022000 2.634000
      vertex -83.290001 2.686000 2.634000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 14.000000 10.500000
      vertex -32.000000 -82.000000 10.500000
      vertex -32.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.991493 0.130159
    outer loop
      vertex -80.999001 18.000000 3.500000
      vertex -92.999001 18.034000 3.241000
      vertex -92.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.991493 0.130159
    outer loop
      vertex -80.999001 18.034000 3.241000
      vertex -92.999001 18.034000 3.241000
      vertex -80.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal -0.340442 -0.044769 0.939199
    outer loop
      vertex -45.846001 -57.000000 3.028000
      vertex -46.714001 -58.665001 2.634000
      vertex -45.664001 -58.383999 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.923642 0.383256
    outer loop
      vertex -80.999001 18.034000 3.241000
      vertex -80.999001 18.134001 3.000000
      vertex -92.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal -0.340429 -0.044777 0.939203
    outer loop
      vertex -46.714001 -58.665001 2.634000
      vertex -45.846001 -57.000000 3.028000
      vertex -46.932999 -57.000000 2.634000
    endloop
  endfacet
  facet normal -0.340442 0.044769 0.939199
    outer loop
      vertex -46.714001 -55.334999 2.634000
      vertex -45.846001 -57.000000 3.028000
      vertex -45.664001 -55.616001 3.028000
    endloop
  endfacet
  facet normal 0.991495 0.130144 -0.000000
    outer loop
      vertex -79.999001 17.000000 10.500000
      vertex -80.032997 17.259001 3.500000
      vertex -80.032997 17.259001 10.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 1.966000 5.500000
      vertex -40.000000 1.866000 5.500000
      vertex -39.000000 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -40.000000 1.866000 5.500000
      vertex -39.792000 1.707000 5.500000
      vertex -39.000000 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.340429 0.044777 0.939203
    outer loop
      vertex -46.932999 -57.000000 2.634000
      vertex -45.846001 -57.000000 3.028000
      vertex -46.714001 -55.334999 2.634000
    endloop
  endfacet
  facet normal -0.546483 0.071867 0.834381
    outer loop
      vertex -44.729000 -55.867001 3.662000
      vertex -45.846001 -57.000000 3.028000
      vertex -44.877998 -57.000000 3.662000
    endloop
  endfacet
  facet normal 0.340587 -0.043804 0.939192
    outer loop
      vertex -83.066002 1.022000 2.634000
      vertex -84.153000 1.018000 3.028000
      vertex -84.331001 -0.366000 3.028000
    endloop
  endfacet
  facet normal 0.509993 -0.208813 0.834448
    outer loop
      vertex -84.860001 -1.658000 3.028000
      vertex -84.331001 -0.366000 3.028000
      vertex -85.699997 -1.176000 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -39.792000 0.293000 5.500000
      vertex -37.901001 -0.500000 5.500000
      vertex -39.633999 0.500000 5.500000
    endloop
  endfacet
  facet normal 0.915211 0.382242 0.127590
    outer loop
      vertex -80.103996 17.517000 3.241000
      vertex -80.133003 17.500000 3.500000
      vertex -80.000000 17.268000 3.241000
    endloop
  endfacet
  facet normal -0.546481 0.071864 0.834382
    outer loop
      vertex -44.729000 -55.867001 3.662000
      vertex -45.664001 -55.616001 3.028000
      vertex -45.846001 -57.000000 3.028000
    endloop
  endfacet
  facet normal 0.991495 -0.130144 0.000000
    outer loop
      vertex -80.032997 16.740999 10.500000
      vertex -80.032997 16.740999 3.500000
      vertex -79.999001 17.000000 10.500000
    endloop
  endfacet
  facet normal 0.991495 0.130144 -0.000000
    outer loop
      vertex -80.032997 17.259001 3.500000
      vertex -79.999001 17.000000 10.500000
      vertex -79.999001 17.000000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.000000 -1.598000 5.500000
      vertex -40.000000 0.134000 5.500000
      vertex -40.241001 0.034000 5.500000
    endloop
  endfacet
  facet normal 0.915811 0.380029 0.129880
    outer loop
      vertex -80.032997 17.259001 3.500000
      vertex -80.000000 17.268000 3.241000
      vertex -80.133003 17.500000 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -81.975998 -57.000000 2.500000
      vertex -82.903000 -60.617001 2.500000
      vertex -47.028000 -60.730000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.500000 1.000000 5.500000
      vertex -39.534000 1.259000 5.500000
      vertex -39.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -39.500000 1.000000 5.500000
      vertex -39.534000 0.741000 5.500000
      vertex -37.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.534000 0.741000 5.500000
      vertex -39.633999 0.500000 5.500000
      vertex -37.901001 -0.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.534000 0.741000 5.500000
      vertex -37.901001 -0.500000 5.500000
      vertex -37.602001 0.224000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -48.018002 -56.019001 2.500000
      vertex -82.446999 -54.215000 2.500000
      vertex -81.975998 -57.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 0.034000 5.500000
      vertex -40.500000 -2.000000 5.500000
      vertex -39.723000 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 0.034000 5.500000
      vertex -40.500000 0.000000 5.500000
      vertex -40.500000 -2.000000 5.500000
    endloop
  endfacet
  facet normal 0.983199 0.128417 0.129723
    outer loop
      vertex -80.000000 17.268000 3.241000
      vertex -80.032997 17.259001 3.500000
      vertex -79.964996 17.000000 3.241000
    endloop
  endfacet
  facet normal 0.923634 -0.383275 -0.000000
    outer loop
      vertex -80.133003 16.500000 10.500000
      vertex -80.032997 16.740999 3.500000
      vertex -80.032997 16.740999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.500000 0.000000 5.500000
      vertex -40.757999 0.034000 5.500000
      vertex -41.276001 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.757999 0.034000 5.500000
      vertex -41.000000 0.134000 5.500000
      vertex -41.276001 -1.898000 5.500000
    endloop
  endfacet
  facet normal 0.130654 -0.991428 0.000000
    outer loop
      vertex -40.757999 1.966000 5.500000
      vertex -40.757999 1.966000 0.000000
      vertex -40.500000 2.000000 0.000000
    endloop
  endfacet
  facet normal 0.130654 -0.991428 0.000000
    outer loop
      vertex -40.500000 2.000000 0.000000
      vertex -40.500000 2.000000 5.500000
      vertex -40.757999 1.966000 5.500000
    endloop
  endfacet
  facet normal 0.122017 -0.000000 0.992528
    outer loop
      vertex -81.975998 0.052000 2.500000
      vertex -81.975998 1.948000 2.500000
      vertex -83.066002 1.022000 2.634000
    endloop
  endfacet
  facet normal 0.317452 -0.129978 0.939324
    outer loop
      vertex -84.860001 -1.658000 3.028000
      vertex -83.278999 -0.644000 2.634000
      vertex -84.331001 -0.366000 3.028000
    endloop
  endfacet
  facet normal -0.130158 -0.991493 -0.000000
    outer loop
      vertex -40.500000 2.000000 0.000000
      vertex -40.241001 1.966000 0.000000
      vertex -40.241001 1.966000 5.500000
    endloop
  endfacet
  facet normal -0.130158 -0.991493 -0.000000
    outer loop
      vertex -40.241001 1.966000 5.500000
      vertex -40.500000 2.000000 5.500000
      vertex -40.500000 2.000000 0.000000
    endloop
  endfacet
  facet normal -0.383252 -0.923644 -0.000000
    outer loop
      vertex -40.241001 1.966000 5.500000
      vertex -40.241001 1.966000 0.000000
      vertex -40.000000 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.273172 -0.208202 0.939164
    outer loop
      vertex -85.706001 -2.768000 3.028000
      vertex -83.917000 -2.198000 2.634000
      vertex -84.860001 -1.658000 3.028000
    endloop
  endfacet
  facet normal -0.607308 -0.794466 -0.000000
    outer loop
      vertex -40.000000 1.866000 5.500000
      vertex -39.792000 1.707000 0.000000
      vertex -39.792000 1.707000 5.500000
    endloop
  endfacet
  facet normal -0.794901 -0.606739 -0.000000
    outer loop
      vertex -39.633999 1.500000 0.000000
      vertex -39.792000 1.707000 5.500000
      vertex -39.792000 1.707000 0.000000
    endloop
  endfacet
  facet normal -0.794901 -0.606739 -0.000000
    outer loop
      vertex -39.633999 1.500000 5.500000
      vertex -39.792000 1.707000 5.500000
      vertex -39.633999 1.500000 0.000000
    endloop
  endfacet
  facet normal -0.923645 -0.383249 0.000000
    outer loop
      vertex -39.633999 1.500000 0.000000
      vertex -39.534000 1.259000 0.000000
      vertex -39.534000 1.259000 5.500000
    endloop
  endfacet
  facet normal -0.923645 -0.383249 0.000000
    outer loop
      vertex -39.534000 1.259000 5.500000
      vertex -39.633999 1.500000 5.500000
      vertex -39.633999 1.500000 0.000000
    endloop
  endfacet
  facet normal 0.112783 -0.105543 0.987998
    outer loop
      vertex -85.454002 -5.343000 2.500000
      vertex -82.903000 -2.617000 2.500000
      vertex -84.934998 -3.534000 2.634000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -39.534000 1.259000 5.500000
      vertex -39.534000 1.259000 0.000000
      vertex -39.500000 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.923645 0.383249 0.000000
    outer loop
      vertex -39.534000 0.741000 5.500000
      vertex -39.534000 0.741000 0.000000
      vertex -39.633999 0.500000 5.500000
    endloop
  endfacet
  facet normal 0.576110 0.445919 0.685021
    outer loop
      vertex -85.714996 3.202000 3.662000
      vertex -86.974998 3.541000 4.501000
      vertex -86.403000 2.802000 4.501000
    endloop
  endfacet
  facet normal -0.794901 0.606739 0.000000
    outer loop
      vertex -39.633999 0.500000 5.500000
      vertex -39.792000 0.293000 0.000000
      vertex -39.792000 0.293000 5.500000
    endloop
  endfacet
  facet normal 0.273156 -0.208138 0.939183
    outer loop
      vertex -83.917000 -2.198000 2.634000
      vertex -85.706001 -2.768000 3.028000
      vertex -84.934998 -3.534000 2.634000
    endloop
  endfacet
  facet normal -0.607308 0.794466 0.000000
    outer loop
      vertex -40.000000 0.134000 0.000000
      vertex -40.000000 0.134000 5.500000
      vertex -39.792000 0.293000 5.500000
    endloop
  endfacet
  facet normal -0.607308 0.794466 0.000000
    outer loop
      vertex -39.792000 0.293000 5.500000
      vertex -39.792000 0.293000 0.000000
      vertex -40.000000 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.383253 0.923643 -0.000000
    outer loop
      vertex -40.000000 0.134000 0.000000
      vertex -40.241001 0.034000 0.000000
      vertex -40.241001 0.034000 5.500000
    endloop
  endfacet
  facet normal -0.383253 0.923643 -0.000000
    outer loop
      vertex -40.241001 0.034000 5.500000
      vertex -40.000000 0.134000 5.500000
      vertex -40.000000 0.134000 0.000000
    endloop
  endfacet
  facet normal 0.576153 0.445502 0.685255
    outer loop
      vertex -86.974998 3.541000 4.501000
      vertex -85.714996 3.202000 3.662000
      vertex -86.414001 4.106000 3.662000
    endloop
  endfacet
  facet normal -0.130158 0.991493 0.000000
    outer loop
      vertex -40.500000 0.000000 0.000000
      vertex -40.500000 0.000000 5.500000
      vertex -40.241001 0.034000 5.500000
    endloop
  endfacet
  facet normal -0.130158 0.991493 0.000000
    outer loop
      vertex -40.241001 0.034000 5.500000
      vertex -40.241001 0.034000 0.000000
      vertex -40.500000 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.099712 -0.075978 0.992111
    outer loop
      vertex -84.934998 -3.534000 2.634000
      vertex -82.903000 -2.617000 2.500000
      vertex -83.917000 -2.198000 2.634000
    endloop
  endfacet
  facet normal 0.130654 0.991428 0.000000
    outer loop
      vertex -40.500000 0.000000 0.000000
      vertex -40.757999 0.034000 0.000000
      vertex -40.757999 0.034000 5.500000
    endloop
  endfacet
  facet normal 0.130654 0.991428 0.000000
    outer loop
      vertex -40.757999 0.034000 5.500000
      vertex -40.500000 0.000000 5.500000
      vertex -40.500000 0.000000 0.000000
    endloop
  endfacet
  facet normal 0.435945 0.337088 0.834460
    outer loop
      vertex -84.877998 3.689000 3.028000
      vertex -86.414001 4.106000 3.662000
      vertex -85.714996 3.202000 3.662000
    endloop
  endfacet
  facet normal 0.317708 -0.130436 0.939174
    outer loop
      vertex -83.278999 -0.644000 2.634000
      vertex -84.860001 -1.658000 3.028000
      vertex -83.917000 -2.198000 2.634000
    endloop
  endfacet
  facet normal 0.609154 -0.793052 -0.000000
    outer loop
      vertex -89.999001 1.866000 5.500000
      vertex -90.206001 1.707000 5.500000
      vertex -90.206001 1.707000 0.000000
    endloop
  endfacet
  facet normal 0.112149 -0.046043 0.992624
    outer loop
      vertex -83.917000 -2.198000 2.634000
      vertex -82.903000 -2.617000 2.500000
      vertex -83.278999 -0.644000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -33.000000 -84.000000 10.500000
      vertex 23.000000 -84.000000 10.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 -82.000000 10.500000
      vertex -34.000000 -83.732002 10.500000
      vertex -33.516998 -83.931999 10.500000
    endloop
  endfacet
  facet normal 0.383258 -0.923641 0.000000
    outer loop
      vertex -89.999001 1.866000 0.000000
      vertex -89.758003 1.966000 5.500000
      vertex -89.999001 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.340297 -0.043507 0.939311
    outer loop
      vertex -83.066002 1.022000 2.634000
      vertex -84.331001 -0.366000 3.028000
      vertex -83.278999 -0.644000 2.634000
    endloop
  endfacet
  facet normal 0.130156 -0.991494 0.000000
    outer loop
      vertex -89.499001 2.000000 0.000000
      vertex -89.499001 2.000000 5.500000
      vertex -89.758003 1.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 -82.000000 10.500000
      vertex -35.000000 -65.536003 10.500000
      vertex -35.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal 0.125151 -0.043468 0.991185
    outer loop
      vertex -81.975998 0.052000 2.500000
      vertex -83.278999 -0.644000 2.634000
      vertex -82.903000 -2.617000 2.500000
    endloop
  endfacet
  facet normal -0.130156 -0.991494 -0.000000
    outer loop
      vertex -89.499001 2.000000 5.500000
      vertex -89.499001 2.000000 0.000000
      vertex -89.239998 1.966000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 -82.000000 10.500000
      vertex -35.000000 -82.000000 10.500000
      vertex -34.931000 -82.517998 10.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -34.731998 -83.000000 10.500000
      vertex -34.414001 -83.414001 10.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 -82.000000 10.500000
      vertex -34.931000 -82.517998 10.500000
      vertex -34.731998 -83.000000 10.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -34.414001 -83.414001 10.500000
      vertex -34.000000 -83.732002 10.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -33.516998 -83.931999 10.500000
      vertex -33.000000 -84.000000 10.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal -0.383249 0.923645 0.000000
    outer loop
      vertex 24.482000 84.931999 10.500000
      vertex 24.482000 84.931999 0.000000
      vertex 24.000000 84.732002 0.000000
    endloop
  endfacet
  facet normal 0.109700 -0.014025 0.993866
    outer loop
      vertex -81.975998 0.052000 2.500000
      vertex -83.066002 1.022000 2.634000
      vertex -83.278999 -0.644000 2.634000
    endloop
  endfacet
  facet normal -0.130159 0.991493 0.000000
    outer loop
      vertex 25.000000 85.000000 10.500000
      vertex 25.000000 85.000000 0.000000
      vertex 24.482000 84.931999 0.000000
    endloop
  endfacet
  facet normal -0.130159 0.991493 0.000000
    outer loop
      vertex 25.000000 85.000000 10.500000
      vertex 24.482000 84.931999 0.000000
      vertex 24.482000 84.931999 10.500000
    endloop
  endfacet
  facet normal 0.130159 0.991493 0.000000
    outer loop
      vertex 23.518000 84.931999 10.500000
      vertex 23.518000 84.931999 0.000000
      vertex 23.000000 85.000000 0.000000
    endloop
  endfacet
  facet normal 0.130159 0.991493 -0.000000
    outer loop
      vertex 23.000000 85.000000 0.000000
      vertex 23.000000 85.000000 10.500000
      vertex 23.518000 84.931999 10.500000
    endloop
  endfacet
  facet normal -0.383249 0.923645 0.000000
    outer loop
      vertex 24.000000 84.732002 10.500000
      vertex 24.482000 84.931999 10.500000
      vertex 24.000000 84.732002 0.000000
    endloop
  endfacet
  facet normal 0.383249 0.923645 0.000000
    outer loop
      vertex 23.518000 84.931999 10.500000
      vertex 24.000000 84.732002 10.500000
      vertex 24.000000 84.732002 0.000000
    endloop
  endfacet
  facet normal -0.861201 -0.126221 0.492342
    outer loop
      vertex -35.032001 -58.483002 4.425000
      vertex -35.035999 -57.699001 4.619000
      vertex -35.305000 -57.615002 4.170000
    endloop
  endfacet
  facet normal 0.383249 0.923645 -0.000000
    outer loop
      vertex 23.518000 84.931999 0.000000
      vertex 23.518000 84.931999 10.500000
      vertex 24.000000 84.732002 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -47.514999 -1.878000 2.500000
      vertex -48.018002 1.000000 2.500000
      vertex -81.975998 0.052000 2.500000
    endloop
  endfacet
  facet normal -0.793057 0.609147 0.000000
    outer loop
      vertex -88.792000 0.293000 5.500000
      vertex -88.633003 0.500000 5.500000
      vertex -88.792000 0.293000 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex 23.000000 -82.000000 2.500000
      vertex 23.000000 83.000000 10.500000
      vertex 23.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.673788 -0.276653 0.685181
    outer loop
      vertex -86.390999 -0.781000 4.501000
      vertex -85.699997 -1.176000 3.662000
      vertex -85.265999 -0.119000 3.662000
    endloop
  endfacet
  facet normal -0.609154 0.793052 0.000000
    outer loop
      vertex -88.792000 0.293000 5.500000
      vertex -88.792000 0.293000 0.000000
      vertex -88.999001 0.134000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -32.000000 83.000000 10.500000
      vertex -32.000000 83.000000 2.500000
      vertex 23.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex 23.000000 83.000000 2.500000
      vertex 23.000000 83.000000 10.500000
      vertex -32.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.579216 -0.441096 0.685524
    outer loop
      vertex -85.699997 -1.176000 3.662000
      vertex -86.958000 -1.524000 4.501000
      vertex -86.392998 -2.086000 3.662000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -92.999001 83.000000 2.500000
      vertex -35.000000 83.000000 10.500000
      vertex -92.999001 83.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 -1.000000 0.000000
    outer loop
      vertex -35.000000 83.000000 2.500000
      vertex -35.000000 83.000000 10.500000
      vertex -92.999001 83.000000 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 19.000000 2.500000
      vertex -35.000000 83.000000 10.500000
      vertex -35.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.579133 -0.441950 0.685044
    outer loop
      vertex -86.958000 -1.524000 4.501000
      vertex -85.699997 -1.176000 3.662000
      vertex -86.390999 -0.781000 4.501000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 83.000000 10.500000
      vertex -35.000000 19.000000 2.500000
      vertex -35.000000 18.000000 3.500000
    endloop
  endfacet
  facet normal 0.445202 -0.575959 0.685613
    outer loop
      vertex -86.958000 -1.524000 4.501000
      vertex -87.697998 -2.096000 4.501000
      vertex -86.392998 -2.086000 3.662000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -32.000000 -82.000000 10.500000
      vertex -32.000000 -82.000000 2.500000
      vertex -32.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -32.000000 83.000000 2.500000
      vertex -32.000000 83.000000 10.500000
      vertex -32.000000 -82.000000 10.500000
    endloop
  endfacet
  facet normal 0.609154 0.793052 0.000000
    outer loop
      vertex -89.999001 0.134000 5.500000
      vertex -90.206001 0.293000 0.000000
      vertex -90.206001 0.293000 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 83.000000 2.500000
      vertex 23.000000 -82.000000 2.500000
      vertex 23.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -32.000000 83.000000 2.500000
      vertex -32.000000 -82.000000 2.500000
      vertex 23.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal 0.438331 -0.333806 0.834529
    outer loop
      vertex -86.392998 -2.086000 3.662000
      vertex -84.860001 -1.658000 3.028000
      vertex -85.699997 -1.176000 3.662000
    endloop
  endfacet
  facet normal -0.991495 -0.130145 0.000000
    outer loop
      vertex -88.499001 1.000000 5.500000
      vertex -88.532997 1.259000 5.500000
      vertex -88.532997 1.259000 0.000000
    endloop
  endfacet
  facet normal 0.445042 -0.576386 0.685359
    outer loop
      vertex -87.296997 -2.784000 3.662000
      vertex -86.392998 -2.086000 3.662000
      vertex -87.697998 -2.096000 4.501000
    endloop
  endfacet
  facet normal -0.991495 0.130145 0.000000
    outer loop
      vertex -88.499001 1.000000 5.500000
      vertex -88.499001 1.000000 0.000000
      vertex -88.532997 0.741000 0.000000
    endloop
  endfacet
  facet normal 0.438359 -0.334101 0.834397
    outer loop
      vertex -84.860001 -1.658000 3.028000
      vertex -86.392998 -2.086000 3.662000
      vertex -85.706001 -2.768000 3.028000
    endloop
  endfacet
  facet normal 0.609154 -0.793052 -0.000000
    outer loop
      vertex -90.206001 1.707000 0.000000
      vertex -89.999001 1.866000 0.000000
      vertex -89.999001 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.281319 -0.671736 0.685296
    outer loop
      vertex -87.697998 -2.096000 4.501000
      vertex -88.559998 -2.457000 4.501000
      vertex -87.296997 -2.784000 3.662000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 19.000000 2.500000
      vertex -35.000000 18.740999 2.534000
      vertex -35.000000 18.000000 3.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 18.740999 2.534000
      vertex -35.000000 18.500000 2.634000
      vertex -35.000000 18.000000 3.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 18.000000 3.500000
      vertex -35.000000 18.000000 10.500000
      vertex -35.000000 83.000000 10.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 18.292999 2.793000
      vertex -35.000000 18.000000 3.500000
      vertex -35.000000 18.500000 2.634000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 18.134001 3.000000
      vertex -35.000000 18.000000 3.500000
      vertex -35.000000 18.292999 2.793000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 18.034000 3.241000
      vertex -35.000000 18.000000 3.500000
      vertex -35.000000 18.134001 3.000000
    endloop
  endfacet
  facet normal 0.336875 -0.436296 0.834363
    outer loop
      vertex -85.706001 -2.768000 3.028000
      vertex -86.392998 -2.086000 3.662000
      vertex -87.296997 -2.784000 3.662000
    endloop
  endfacet
  facet normal -0.130156 -0.991494 0.000000
    outer loop
      vertex -89.239998 1.966000 0.000000
      vertex -89.239998 1.966000 5.500000
      vertex -89.499001 2.000000 5.500000
    endloop
  endfacet
  facet normal -0.383258 -0.923641 -0.000000
    outer loop
      vertex -89.239998 1.966000 0.000000
      vertex -88.999001 1.866000 0.000000
      vertex -88.999001 1.866000 5.500000
    endloop
  endfacet
  facet normal 0.336861 -0.436377 0.834326
    outer loop
      vertex -85.706001 -2.768000 3.028000
      vertex -87.296997 -2.784000 3.662000
      vertex -86.810997 -3.621000 3.028000
    endloop
  endfacet
  facet normal 0.280986 -0.672201 0.684977
    outer loop
      vertex -87.296997 -2.784000 3.662000
      vertex -88.559998 -2.457000 4.501000
      vertex -88.351997 -3.225000 3.662000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex -35.000000 18.000000 10.500000
      vertex -35.000000 18.000000 3.500000
      vertex -48.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal -0.991495 -0.130145 0.000000
    outer loop
      vertex -88.532997 1.259000 0.000000
      vertex -88.499001 1.000000 0.000000
      vertex -88.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.923635 0.383274 -0.000000
    outer loop
      vertex -88.532997 0.741000 0.000000
      vertex -88.633003 0.500000 0.000000
      vertex -88.633003 0.500000 5.500000
    endloop
  endfacet
  facet normal 0.212586 -0.508567 0.834366
    outer loop
      vertex -86.810997 -3.621000 3.028000
      vertex -87.296997 -2.784000 3.662000
      vertex -88.351997 -3.225000 3.662000
    endloop
  endfacet
  facet normal 0.094889 0.722180 0.685165
    outer loop
      vertex -40.500000 -52.622002 3.662000
      vertex -40.500000 -53.417999 4.501000
      vertex -39.366001 -52.771000 3.662000
    endloop
  endfacet
  facet normal 0.097560 -0.721818 0.685172
    outer loop
      vertex -88.351997 -3.225000 3.662000
      vertex -89.487000 -2.582000 4.501000
      vertex -89.484001 -3.378000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.130157 0.991493
    outer loop
      vertex -35.000000 19.000000 2.500000
      vertex -48.999001 18.740999 2.534000
      vertex -35.000000 18.740999 2.534000
    endloop
  endfacet
  facet normal -0.383258 0.923641 -0.000000
    outer loop
      vertex -88.999001 0.134000 5.500000
      vertex -89.239998 0.034000 0.000000
      vertex -89.239998 0.034000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.383256 0.923642
    outer loop
      vertex -35.000000 18.740999 2.534000
      vertex -48.999001 18.740999 2.534000
      vertex -48.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 0.000000 0.130157 0.991493
    outer loop
      vertex -35.000000 19.000000 2.500000
      vertex -48.999001 19.000000 2.500000
      vertex -48.999001 18.740999 2.534000
    endloop
  endfacet
  facet normal -0.991495 0.130145 0.000000
    outer loop
      vertex -88.532997 0.741000 0.000000
      vertex -88.532997 0.741000 5.500000
      vertex -88.499001 1.000000 5.500000
    endloop
  endfacet
  facet normal -0.929831 0.108890 0.351507
    outer loop
      vertex -35.203999 -53.703999 3.400000
      vertex -35.030998 -55.316002 4.357000
      vertex -35.018002 -52.261002 3.445000
    endloop
  endfacet
  facet normal -0.000000 0.383256 0.923642
    outer loop
      vertex -48.999001 18.500000 2.634000
      vertex -35.000000 18.500000 2.634000
      vertex -35.000000 18.740999 2.534000
    endloop
  endfacet
  facet normal -0.874450 0.174805 0.452526
    outer loop
      vertex -35.030998 -55.316002 4.357000
      vertex -35.203999 -53.703999 3.400000
      vertex -35.257999 -55.108002 3.838000
    endloop
  endfacet
  facet normal 0.209855 -0.271851 0.939179
    outer loop
      vertex -86.810997 -3.621000 3.028000
      vertex -84.934998 -3.534000 2.634000
      vertex -85.706001 -2.768000 3.028000
    endloop
  endfacet
  facet normal 0.212590 -0.508558 0.834370
    outer loop
      vertex -88.351997 -3.225000 3.662000
      vertex -88.098000 -4.159000 3.028000
      vertex -86.810997 -3.621000 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.609154 0.793052
    outer loop
      vertex -48.999001 18.500000 2.634000
      vertex -48.999001 18.292999 2.793000
      vertex -35.000000 18.292999 2.793000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -48.999001 19.000000 2.500000
      vertex -35.000000 19.000000 2.500000
      vertex -35.000000 83.000000 2.500000
    endloop
  endfacet
  facet normal 0.132324 -0.316546 0.939302
    outer loop
      vertex -87.813004 -5.209000 2.634000
      vertex -86.810997 -3.621000 3.028000
      vertex -88.098000 -4.159000 3.028000
    endloop
  endfacet
  facet normal 0.000000 1.000000 0.000000
    outer loop
      vertex -48.999001 18.000000 3.500000
      vertex -48.999001 18.000000 10.500000
      vertex -35.000000 18.000000 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.609154 0.793052
    outer loop
      vertex -35.000000 18.500000 2.634000
      vertex -48.999001 18.500000 2.634000
      vertex -35.000000 18.292999 2.793000
    endloop
  endfacet
  facet normal 0.383258 0.923641 0.000000
    outer loop
      vertex -89.999001 0.134000 5.500000
      vertex -89.758003 0.034000 5.500000
      vertex -89.999001 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.079751 0.607213 0.790526
    outer loop
      vertex -48.999001 18.500000 2.634000
      vertex -49.334000 18.249001 2.793000
      vertex -48.999001 18.292999 2.793000
    endloop
  endfacet
  facet normal 0.609154 0.793052 0.000000
    outer loop
      vertex -90.206001 0.293000 0.000000
      vertex -89.999001 0.134000 5.500000
      vertex -89.999001 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.445292 0.277304 0.851362
    outer loop
      vertex -35.386002 -55.148998 3.727000
      vertex -35.426998 -55.834999 3.929000
      vertex -35.305000 -56.379002 4.170000
    endloop
  endfacet
  facet normal 0.000000 0.793054 0.609151
    outer loop
      vertex -35.000000 18.292999 2.793000
      vertex -48.999001 18.292999 2.793000
      vertex -48.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.793054 0.609151
    outer loop
      vertex -35.000000 18.292999 2.793000
      vertex -48.999001 18.134001 3.000000
      vertex -35.000000 18.134001 3.000000
    endloop
  endfacet
  facet normal 0.383258 -0.923641 0.000000
    outer loop
      vertex -89.758003 1.966000 0.000000
      vertex -89.758003 1.966000 5.500000
      vertex -89.999001 1.866000 0.000000
    endloop
  endfacet
  facet normal -0.104628 0.788701 0.605808
    outer loop
      vertex -48.999001 18.292999 2.793000
      vertex -49.292999 18.094999 3.000000
      vertex -48.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal 0.130156 -0.991494 0.000000
    outer loop
      vertex -89.758003 1.966000 0.000000
      vertex -89.499001 2.000000 0.000000
      vertex -89.758003 1.966000 5.500000
    endloop
  endfacet
  facet normal -0.103506 0.788081 0.606808
    outer loop
      vertex -48.999001 18.292999 2.793000
      vertex -49.334000 18.249001 2.793000
      vertex -49.292999 18.094999 3.000000
    endloop
  endfacet
  facet normal -0.609154 -0.793052 0.000000
    outer loop
      vertex -88.999001 1.866000 0.000000
      vertex -88.792000 1.707000 0.000000
      vertex -88.792000 1.707000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.923642 0.383256
    outer loop
      vertex -48.999001 18.034000 3.241000
      vertex -35.000000 18.134001 3.000000
      vertex -48.999001 18.134001 3.000000
    endloop
  endfacet
  facet normal -0.793057 -0.609147 0.000000
    outer loop
      vertex -88.633003 1.500000 0.000000
      vertex -88.792000 1.707000 5.500000
      vertex -88.792000 1.707000 0.000000
    endloop
  endfacet
  facet normal -0.793057 -0.609147 -0.000000
    outer loop
      vertex -88.633003 1.500000 5.500000
      vertex -88.792000 1.707000 5.500000
      vertex -88.633003 1.500000 0.000000
    endloop
  endfacet
  facet normal 0.000000 0.923642 0.383256
    outer loop
      vertex -35.000000 18.134001 3.000000
      vertex -48.999001 18.034000 3.241000
      vertex -35.000000 18.034000 3.241000
    endloop
  endfacet
  facet normal 0.991495 -0.130144 0.000000
    outer loop
      vertex -79.999001 17.000000 3.500000
      vertex -79.999001 17.000000 10.500000
      vertex -80.032997 16.740999 3.500000
    endloop
  endfacet
  facet normal -0.908082 0.123339 0.400217
    outer loop
      vertex -35.018002 -52.261002 3.445000
      vertex -35.030998 -55.316002 4.357000
      vertex -35.000000 -56.999001 4.946000
    endloop
  endfacet
  facet normal 0.073834 -0.546275 0.834345
    outer loop
      vertex -88.098000 -4.159000 3.028000
      vertex -88.351997 -3.225000 3.662000
      vertex -89.484001 -3.378000 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.991493 0.130159
    outer loop
      vertex -48.999001 18.000000 3.500000
      vertex -35.000000 18.000000 3.500000
      vertex -35.000000 18.034000 3.241000
    endloop
  endfacet
  facet normal 0.983200 0.129055 0.129085
    outer loop
      vertex -80.032997 17.259001 3.500000
      vertex -79.999001 17.000000 3.500000
      vertex -79.964996 17.000000 3.241000
    endloop
  endfacet
  facet normal -0.247685 0.118634 0.961550
    outer loop
      vertex -35.467999 -56.931000 4.103000
      vertex -36.035999 -56.431000 3.895000
      vertex -36.060001 -56.935001 3.951000
    endloop
  endfacet
  facet normal 0.000000 0.991493 0.130159
    outer loop
      vertex -35.000000 18.034000 3.241000
      vertex -48.999001 18.034000 3.241000
      vertex -48.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal 0.073859 -0.546244 0.834363
    outer loop
      vertex -89.481003 -4.346000 3.028000
      vertex -88.098000 -4.159000 3.028000
      vertex -89.484001 -3.378000 3.662000
    endloop
  endfacet
  facet normal -0.119757 0.916995 0.380497
    outer loop
      vertex -48.999001 18.034000 3.241000
      vertex -48.999001 18.134001 3.000000
      vertex -49.266998 17.999001 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -35.000000 83.000000 2.500000
      vertex -92.999001 83.000000 2.500000
      vertex -48.999001 19.000000 2.500000
    endloop
  endfacet
  facet normal -0.617157 0.081392 0.782619
    outer loop
      vertex -35.313999 -56.928001 4.220000
      vertex -35.305000 -56.379002 4.170000
      vertex -35.455002 -56.401001 4.054000
    endloop
  endfacet
  facet normal -0.602567 -0.070670 0.794933
    outer loop
      vertex -35.467999 -56.931000 4.103000
      vertex -35.455002 -57.592999 4.054000
      vertex -35.313999 -56.928001 4.220000
    endloop
  endfacet
  facet normal -0.617619 0.198619 0.760984
    outer loop
      vertex -35.305000 -56.379002 4.170000
      vertex -35.426998 -55.834999 3.929000
      vertex -35.455002 -56.401001 4.054000
    endloop
  endfacet
  facet normal -0.923635 -0.383274 0.000000
    outer loop
      vertex -88.532997 1.259000 0.000000
      vertex -88.532997 1.259000 5.500000
      vertex -88.633003 1.500000 5.500000
    endloop
  endfacet
  facet normal -0.923635 -0.383274 -0.000000
    outer loop
      vertex -88.633003 1.500000 5.500000
      vertex -88.633003 1.500000 0.000000
      vertex -88.532997 1.259000 0.000000
    endloop
  endfacet
  facet normal -0.856279 0.060750 0.512929
    outer loop
      vertex -35.036999 -56.916000 4.681000
      vertex -35.305000 -56.379002 4.170000
      vertex -35.313999 -56.928001 4.220000
    endloop
  endfacet
  facet normal -0.923644 -0.383250 -0.000000
    outer loop
      vertex -49.865002 16.500000 10.500000
      vertex -49.965000 16.740999 10.500000
      vertex -49.865002 16.500000 3.500000
    endloop
  endfacet
  facet normal -0.923635 0.383274 -0.000000
    outer loop
      vertex -88.633003 0.500000 5.500000
      vertex -88.532997 0.741000 5.500000
      vertex -88.532997 0.741000 0.000000
    endloop
  endfacet
  facet normal -0.794902 -0.606738 -0.000000
    outer loop
      vertex -49.865002 16.500000 10.500000
      vertex -49.865002 16.500000 3.500000
      vertex -49.707001 16.292999 10.500000
    endloop
  endfacet
  facet normal -0.793057 0.609147 -0.000000
    outer loop
      vertex -88.792000 0.293000 0.000000
      vertex -88.633003 0.500000 5.500000
      vertex -88.633003 0.500000 0.000000
    endloop
  endfacet
  facet normal 0.045971 -0.339986 0.939306
    outer loop
      vertex -89.481003 -4.346000 3.028000
      vertex -87.813004 -5.209000 2.634000
      vertex -88.098000 -4.159000 3.028000
    endloop
  endfacet
  facet normal -0.130159 0.991493 0.000000
    outer loop
      vertex -49.257999 17.966000 10.500000
      vertex -48.999001 18.000000 10.500000
      vertex -49.257999 17.966000 3.500000
    endloop
  endfacet
  facet normal -0.609154 0.793052 -0.000000
    outer loop
      vertex -88.792000 0.293000 0.000000
      vertex -88.999001 0.134000 0.000000
      vertex -88.999001 0.134000 5.500000
    endloop
  endfacet
  facet normal -0.383254 0.923643 0.000000
    outer loop
      vertex -49.257999 17.966000 10.500000
      vertex -49.257999 17.966000 3.500000
      vertex -49.499001 17.865999 10.500000
    endloop
  endfacet
  facet normal -0.383258 0.923641 -0.000000
    outer loop
      vertex -89.239998 0.034000 0.000000
      vertex -88.999001 0.134000 5.500000
      vertex -88.999001 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.860971 0.051822 0.506007
    outer loop
      vertex -35.036999 -56.916000 4.681000
      vertex -35.035999 -56.293999 4.619000
      vertex -35.305000 -56.379002 4.170000
    endloop
  endfacet
  facet normal -0.855586 -0.048715 0.515363
    outer loop
      vertex -35.036999 -56.916000 4.681000
      vertex -35.313999 -56.928001 4.220000
      vertex -35.305000 -57.615002 4.170000
    endloop
  endfacet
  facet normal 0.007961 -0.120494 0.992682
    outer loop
      vertex -89.477997 -5.434000 2.634000
      vertex -89.947998 -6.569000 2.500000
      vertex -88.056000 -6.444000 2.500000
    endloop
  endfacet
  facet normal 0.923634 -0.383275 -0.000000
    outer loop
      vertex -80.032997 16.740999 3.500000
      vertex -80.133003 16.500000 10.500000
      vertex -80.133003 16.500000 3.500000
    endloop
  endfacet
  facet normal -0.860485 -0.041307 0.507799
    outer loop
      vertex -35.035999 -57.699001 4.619000
      vertex -35.036999 -56.916000 4.681000
      vertex -35.305000 -57.615002 4.170000
    endloop
  endfacet
  facet normal 0.209859 -0.271570 0.939260
    outer loop
      vertex -86.264000 -4.561000 2.634000
      vertex -84.934998 -3.534000 2.634000
      vertex -86.810997 -3.621000 3.028000
    endloop
  endfacet
  facet normal 0.917629 0.122147 0.378202
    outer loop
      vertex -80.000000 17.268000 3.241000
      vertex -79.864998 17.000000 3.000000
      vertex -79.903999 17.292999 3.000000
    endloop
  endfacet
  facet normal -0.991493 0.130159 0.000000
    outer loop
      vertex -49.999001 17.000000 10.500000
      vertex -49.965000 17.259001 3.500000
      vertex -49.999001 17.000000 3.500000
    endloop
  endfacet
  facet normal -0.991493 0.130159 0.000000
    outer loop
      vertex -49.965000 17.259001 10.500000
      vertex -49.965000 17.259001 3.500000
      vertex -49.999001 17.000000 10.500000
    endloop
  endfacet
  facet normal 0.132451 -0.316616 0.939261
    outer loop
      vertex -86.264000 -4.561000 2.634000
      vertex -86.810997 -3.621000 3.028000
      vertex -87.813004 -5.209000 2.634000
    endloop
  endfacet
  facet normal -0.861009 0.135711 0.490148
    outer loop
      vertex -35.305000 -56.379002 4.170000
      vertex -35.035999 -56.293999 4.619000
      vertex -35.030998 -55.316002 4.357000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -49.999001 17.000000 10.500000
      vertex -49.999001 17.000000 3.500000
      vertex -49.965000 16.740999 3.500000
    endloop
  endfacet
  facet normal -0.678035 0.209136 0.704649
    outer loop
      vertex -35.305000 -56.379002 4.170000
      vertex -35.257999 -55.108002 3.838000
      vertex -35.386002 -55.148998 3.727000
    endloop
  endfacet
  facet normal -0.923644 -0.383250 0.000000
    outer loop
      vertex -49.865002 16.500000 3.500000
      vertex -49.965000 16.740999 10.500000
      vertex -49.965000 16.740999 3.500000
    endloop
  endfacet
  facet normal -0.882632 0.149087 0.445797
    outer loop
      vertex -35.305000 -56.379002 4.170000
      vertex -35.030998 -55.316002 4.357000
      vertex -35.257999 -55.108002 3.838000
    endloop
  endfacet
  facet normal 0.045949 -0.340022 0.939294
    outer loop
      vertex -87.813004 -5.209000 2.634000
      vertex -89.481003 -4.346000 3.028000
      vertex -89.477997 -5.434000 2.634000
    endloop
  endfacet
  facet normal 0.130156 0.991494 -0.000000
    outer loop
      vertex -89.499001 0.000000 0.000000
      vertex -89.758003 0.034000 0.000000
      vertex -89.758003 0.034000 5.500000
    endloop
  endfacet
  facet normal -0.990828 -0.011923 0.134603
    outer loop
      vertex -35.035999 -57.699001 4.619000
      vertex -35.000000 -56.999001 4.946000
      vertex -35.036999 -56.916000 4.681000
    endloop
  endfacet
  facet normal 0.383258 0.923641 0.000000
    outer loop
      vertex -89.999001 0.134000 0.000000
      vertex -89.758003 0.034000 5.500000
      vertex -89.758003 0.034000 0.000000
    endloop
  endfacet
  facet normal -0.079592 0.607077 0.790647
    outer loop
      vertex -48.999001 18.500000 2.634000
      vertex -49.388000 18.448999 2.634000
      vertex -49.334000 18.249001 2.793000
    endloop
  endfacet
  facet normal -0.234869 0.565253 0.790775
    outer loop
      vertex -49.388000 18.448999 2.634000
      vertex -49.749001 18.299000 2.634000
      vertex -49.334000 18.249001 2.793000
    endloop
  endfacet
  facet normal -0.966316 -0.066451 0.248631
    outer loop
      vertex -35.000000 -56.999001 4.946000
      vertex -35.035999 -57.699001 4.619000
      vertex -35.032001 -58.483002 4.425000
    endloop
  endfacet
  facet normal 0.381901 0.924203 0.000000
    outer loop
      vertex -40.757999 0.034000 5.500000
      vertex -40.757999 0.034000 0.000000
      vertex -41.000000 0.134000 0.000000
    endloop
  endfacet
  facet normal -0.281156 0.671965 0.685138
    outer loop
      vertex -91.700996 4.784000 3.662000
      vertex -90.438004 4.457000 4.501000
      vertex -90.647003 5.225000 3.662000
    endloop
  endfacet
  facet normal -0.958304 0.078506 0.274755
    outer loop
      vertex -35.035999 -56.293999 4.619000
      vertex -35.000000 -56.999001 4.946000
      vertex -35.030998 -55.316002 4.357000
    endloop
  endfacet
  facet normal -0.209280 -0.509776 0.834464
    outer loop
      vertex -90.865997 -62.168999 3.028000
      vertex -90.617996 -61.233002 3.662000
      vertex -92.156998 -61.639000 3.028000
    endloop
  endfacet
  facet normal -0.991493 0.130159 -0.000000
    outer loop
      vertex -39.500000 1.000000 5.500000
      vertex -39.534000 0.741000 0.000000
      vertex -39.534000 0.741000 5.500000
    endloop
  endfacet
  facet normal -0.989577 0.015857 0.143129
    outer loop
      vertex -35.035999 -56.293999 4.619000
      vertex -35.036999 -56.916000 4.681000
      vertex -35.000000 -56.999001 4.946000
    endloop
  endfacet
  facet normal -0.441450 -0.579259 0.685260
    outer loop
      vertex -92.584999 -60.105999 3.662000
      vertex -91.279999 -60.108002 4.501000
      vertex -92.024002 -59.541000 4.501000
    endloop
  endfacet
  facet normal -0.115787 0.858681 0.499260
    outer loop
      vertex -90.438004 4.457000 4.501000
      vertex -90.276001 3.898000 5.500000
      vertex -89.511002 4.582000 4.501000
    endloop
  endfacet
  facet normal -0.342004 -0.304707 0.888925
    outer loop
      vertex -35.000000 -56.999001 4.946000
      vertex -35.032001 -58.483002 4.425000
      vertex -35.026001 -59.680000 4.017000
    endloop
  endfacet
  facet normal -0.441506 -0.579115 0.685346
    outer loop
      vertex -91.279999 -60.108002 4.501000
      vertex -92.584999 -60.105999 3.662000
      vertex -91.676003 -60.799000 3.662000
    endloop
  endfacet
  facet normal -0.331673 0.799332 0.501060
    outer loop
      vertex -90.276001 3.898000 5.500000
      vertex -90.438004 4.457000 4.501000
      vertex -90.999001 3.598000 5.500000
    endloop
  endfacet
  facet normal -0.444880 0.576818 0.685101
    outer loop
      vertex -91.700996 4.784000 3.662000
      vertex -92.606003 4.086000 3.662000
      vertex -91.301003 4.096000 4.501000
    endloop
  endfacet
  facet normal -0.281113 0.672025 0.685097
    outer loop
      vertex -91.301003 4.096000 4.501000
      vertex -90.438004 4.457000 4.501000
      vertex -91.700996 4.784000 3.662000
    endloop
  endfacet
  facet normal -0.334320 0.799220 0.499477
    outer loop
      vertex -90.999001 3.598000 5.500000
      vertex -90.438004 4.457000 4.501000
      vertex -91.301003 4.096000 4.501000
    endloop
  endfacet
  facet normal 0.014969 -0.110767 0.993734
    outer loop
      vertex -89.477997 -5.434000 2.634000
      vertex -88.056000 -6.444000 2.500000
      vertex -87.813004 -5.209000 2.634000
    endloop
  endfacet
  facet normal 0.049598 -0.118561 0.991707
    outer loop
      vertex -87.813004 -5.209000 2.634000
      vertex -85.454002 -5.343000 2.500000
      vertex -86.264000 -4.561000 2.634000
    endloop
  endfacet
  facet normal 0.073021 -0.094494 0.992844
    outer loop
      vertex -85.454002 -5.343000 2.500000
      vertex -84.934998 -3.534000 2.634000
      vertex -86.264000 -4.561000 2.634000
    endloop
  endfacet
  facet normal 0.686746 -0.527499 0.500124
    outer loop
      vertex -38.377998 -59.120998 5.500000
      vertex -37.396999 -58.791000 4.501000
      vertex -37.901001 -58.500000 5.500000
    endloop
  endfacet
  facet normal 0.049672 -0.117390 0.991843
    outer loop
      vertex -88.056000 -6.444000 2.500000
      vertex -85.454002 -5.343000 2.500000
      vertex -87.813004 -5.209000 2.634000
    endloop
  endfacet
  facet normal 0.983200 -0.129055 0.129085
    outer loop
      vertex -79.999001 17.000000 3.500000
      vertex -80.032997 16.740999 3.500000
      vertex -79.964996 17.000000 3.241000
    endloop
  endfacet
  facet normal 0.683115 -0.283048 0.673229
    outer loop
      vertex -37.039001 -57.926998 4.501000
      vertex -37.396999 -58.791000 4.501000
      vertex -36.667999 -58.316002 3.961000
    endloop
  endfacet
  facet normal 0.799984 -0.331472 0.500152
    outer loop
      vertex -37.901001 -58.500000 5.500000
      vertex -37.396999 -58.791000 4.501000
      vertex -37.039001 -57.926998 4.501000
    endloop
  endfacet
  facet normal 0.800022 -0.330396 0.500802
    outer loop
      vertex -37.901001 -58.500000 5.500000
      vertex -37.039001 -57.926998 4.501000
      vertex -37.602001 -57.776001 5.500000
    endloop
  endfacet
  facet normal 0.916996 0.119770 0.380491
    outer loop
      vertex -79.864998 17.000000 3.000000
      vertex -80.000000 17.268000 3.241000
      vertex -79.964996 17.000000 3.241000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -37.901001 -58.500000 5.500000
      vertex -37.602001 -57.776001 5.500000
      vertex -39.534000 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.983199 -0.128417 0.129723
    outer loop
      vertex -80.000000 16.732000 3.241000
      vertex -79.964996 17.000000 3.241000
      vertex -80.032997 16.740999 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 -32.768002 2.500000
      vertex -47.514999 -1.878000 2.500000
      vertex -85.454002 -5.343000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.056000 -6.444000 2.500000
      vertex -89.947998 -6.569000 2.500000
      vertex -94.999001 -32.768002 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -85.454002 -5.343000 2.500000
      vertex -88.056000 -6.444000 2.500000
      vertex -94.999001 -32.768002 2.500000
    endloop
  endfacet
  facet normal 0.915811 -0.380029 0.129880
    outer loop
      vertex -80.133003 16.500000 3.500000
      vertex -80.000000 16.732000 3.241000
      vertex -80.032997 16.740999 3.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.633999 -57.500000 5.500000
      vertex -39.792000 -57.707001 5.500000
      vertex -37.901001 -58.500000 5.500000
    endloop
  endfacet
  facet normal -0.991493 0.000000 0.130159
    outer loop
      vertex -35.034000 14.000000 3.241000
      vertex -35.034000 7.103000 3.241000
      vertex -35.000000 14.000000 3.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -82.903000 -2.617000 2.500000
      vertex -85.454002 -5.343000 2.500000
      vertex -47.514999 -1.878000 2.500000
    endloop
  endfacet
  facet normal 0.793058 -0.609146 0.000000
    outer loop
      vertex -80.292000 16.292999 3.500000
      vertex -80.133003 16.500000 10.500000
      vertex -80.292000 16.292999 10.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.792000 -57.707001 5.500000
      vertex -40.000000 -57.866001 5.500000
      vertex -39.000000 -59.598000 5.500000
    endloop
  endfacet
  facet normal -0.923645 0.000000 0.383249
    outer loop
      vertex -35.034000 14.000000 3.241000
      vertex -35.133999 14.000000 3.000000
      vertex -35.133999 7.103000 3.000000
    endloop
  endfacet
  facet normal -0.923645 0.000000 0.383249
    outer loop
      vertex -35.133999 7.103000 3.000000
      vertex -35.034000 7.103000 3.241000
      vertex -35.034000 14.000000 3.241000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.000000 -57.866001 5.500000
      vertex -40.241001 -57.966000 5.500000
      vertex -39.000000 -59.598000 5.500000
    endloop
  endfacet
  facet normal -0.794901 0.000000 0.606739
    outer loop
      vertex -35.133999 7.103000 3.000000
      vertex -35.133999 14.000000 3.000000
      vertex -35.292000 14.000000 2.793000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -38.377998 -59.120998 5.500000
      vertex -37.901001 -58.500000 5.500000
      vertex -39.792000 -57.707001 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.500000 -58.000000 5.500000
      vertex -40.757999 -57.966000 5.500000
      vertex -41.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal -0.607308 0.000000 0.794467
    outer loop
      vertex -35.500000 14.000000 2.634000
      vertex -35.500000 7.103000 2.634000
      vertex -35.292000 7.103000 2.793000
    endloop
  endfacet
  facet normal -0.799220 -0.334320 0.499477
    outer loop
      vertex -92.956001 0.061000 4.501000
      vertex -92.595001 -0.802000 4.501000
      vertex -92.097000 -0.500000 5.500000
    endloop
  endfacet
  facet normal -0.383253 0.000000 0.923643
    outer loop
      vertex -35.500000 7.103000 2.634000
      vertex -35.500000 14.000000 2.634000
      vertex -35.741001 7.103000 2.534000
    endloop
  endfacet
  facet normal -0.686169 -0.527054 0.501384
    outer loop
      vertex -92.097000 -0.500000 5.500000
      vertex -92.595001 -0.802000 4.501000
      vertex -91.620003 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.000000 -57.866001 5.500000
      vertex -42.000000 -59.598000 5.500000
      vertex -41.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -41.276001 -59.897999 5.500000
      vertex -40.500000 -60.000000 5.500000
      vertex -40.500000 -58.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 -57.966000 5.500000
      vertex -40.500000 -58.000000 5.500000
      vertex -40.500000 -60.000000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.757999 -57.966000 5.500000
      vertex -41.000000 -57.866001 5.500000
      vertex -41.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal 0.793058 -0.609146 -0.000000
    outer loop
      vertex -80.292000 16.292999 3.500000
      vertex -80.133003 16.500000 3.500000
      vertex -80.133003 16.500000 10.500000
    endloop
  endfacet
  facet normal -0.130158 0.000000 0.991493
    outer loop
      vertex -35.741001 7.103000 2.534000
      vertex -35.741001 14.000000 2.534000
      vertex -36.000000 7.103000 2.500000
    endloop
  endfacet
  facet normal -0.088210 -0.001598 0.996101
    outer loop
      vertex -36.133999 14.500000 2.500000
      vertex -36.000000 7.103000 2.500000
      vertex -35.741001 14.000000 2.534000
    endloop
  endfacet
  facet normal 0.786447 -0.604067 0.128857
    outer loop
      vertex -80.267998 16.268999 3.241000
      vertex -80.133003 16.500000 3.500000
      vertex -80.292000 16.292999 3.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -92.097000 -0.500000 5.500000
      vertex -90.464996 0.741000 5.500000
      vertex -92.397003 0.224000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.999001 0.134000 5.500000
      vertex -90.206001 0.293000 5.500000
      vertex -91.620003 -1.121000 5.500000
    endloop
  endfacet
  facet normal 0.856025 -0.353029 0.377613
    outer loop
      vertex -79.903999 16.707001 3.000000
      vertex -80.000000 16.732000 3.241000
      vertex -80.016998 16.433001 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.133999 14.500000 2.500000
      vertex -37.716999 8.053000 2.500000
      vertex -36.000000 7.103000 2.500000
    endloop
  endfacet
  facet normal 0.915211 -0.382242 0.127590
    outer loop
      vertex -80.000000 16.732000 3.241000
      vertex -80.133003 16.500000 3.500000
      vertex -80.103996 16.483000 3.241000
    endloop
  endfacet
  facet normal -0.112990 -0.858527 0.500164
    outer loop
      vertex -40.500000 -60.000000 5.500000
      vertex -41.426998 -60.459999 4.501000
      vertex -40.500000 -60.582001 4.501000
    endloop
  endfacet
  facet normal -0.671772 -0.281008 0.685388
    outer loop
      vertex -92.595001 -0.802000 4.501000
      vertex -92.956001 0.061000 4.501000
      vertex -93.724998 -0.147000 3.662000
    endloop
  endfacet
  facet normal -0.577442 -0.233174 -0.782427
    outer loop
      vertex -35.034000 7.103000 3.241000
      vertex -35.000000 5.539000 3.682000
      vertex -35.000000 4.029000 4.132000
    endloop
  endfacet
  facet normal -0.998805 0.003092 0.048782
    outer loop
      vertex -35.000000 4.029000 4.132000
      vertex -35.000000 14.000000 3.500000
      vertex -35.034000 7.103000 3.241000
    endloop
  endfacet
  facet normal 0.852861 -0.356201 0.381772
    outer loop
      vertex -80.016998 16.433001 3.000000
      vertex -80.000000 16.732000 3.241000
      vertex -80.103996 16.483000 3.241000
    endloop
  endfacet
  facet normal 0.787219 -0.603293 0.127764
    outer loop
      vertex -80.267998 16.268999 3.241000
      vertex -80.103996 16.483000 3.241000
      vertex -80.133003 16.500000 3.500000
    endloop
  endfacet
  facet normal 0.733692 -0.562272 0.381506
    outer loop
      vertex -80.016998 16.433001 3.000000
      vertex -80.103996 16.483000 3.241000
      vertex -80.267998 16.268999 3.241000
    endloop
  endfacet
  facet normal -0.685380 -0.529569 0.499812
    outer loop
      vertex -91.620003 -1.121000 5.500000
      vertex -92.595001 -0.802000 4.501000
      vertex -92.024002 -1.541000 4.501000
    endloop
  endfacet
  facet normal 0.122124 0.917456 0.378631
    outer loop
      vertex -80.706001 18.094999 3.000000
      vertex -80.999001 18.134001 3.000000
      vertex -80.732002 17.999001 3.241000
    endloop
  endfacet
  facet normal 0.737328 0.099759 0.668129
    outer loop
      vertex -36.763000 -56.673000 4.286000
      vertex -36.742001 -56.346001 4.214000
      vertex -37.039001 -56.073002 4.501000
    endloop
  endfacet
  facet normal 0.535985 0.072653 0.841096
    outer loop
      vertex -36.222000 -56.426998 3.920000
      vertex -36.763000 -56.673000 4.286000
      vertex -36.249001 -56.933998 3.981000
    endloop
  endfacet
  facet normal 0.352590 0.855795 0.378545
    outer loop
      vertex -80.431999 17.982000 3.000000
      vertex -80.732002 17.999001 3.241000
      vertex -80.482002 17.896000 3.241000
    endloop
  endfacet
  facet normal -0.526992 -0.686086 0.501562
    outer loop
      vertex -91.620003 -1.121000 5.500000
      vertex -92.024002 -1.541000 4.501000
      vertex -90.999001 -1.598000 5.500000
    endloop
  endfacet
  facet normal 0.756511 0.155123 0.635318
    outer loop
      vertex -37.039001 -56.073002 4.501000
      vertex -36.742001 -56.346001 4.214000
      vertex -36.667999 -55.682999 3.964000
    endloop
  endfacet
  facet normal 0.352832 0.855554 0.378863
    outer loop
      vertex -80.706001 18.094999 3.000000
      vertex -80.732002 17.999001 3.241000
      vertex -80.431999 17.982000 3.000000
    endloop
  endfacet
  facet normal 0.437942 0.273983 0.856236
    outer loop
      vertex -36.160999 -55.883999 3.769000
      vertex -36.667999 -55.682999 3.964000
      vertex -36.742001 -56.346001 4.214000
    endloop
  endfacet
  facet normal 0.505174 0.178076 0.844445
    outer loop
      vertex -36.742001 -56.346001 4.214000
      vertex -36.222000 -56.426998 3.920000
      vertex -36.160999 -55.883999 3.769000
    endloop
  endfacet
  facet normal -0.525117 -0.689045 0.499469
    outer loop
      vertex -90.999001 -1.598000 5.500000
      vertex -92.024002 -1.541000 4.501000
      vertex -91.279999 -2.108000 4.501000
    endloop
  endfacet
  facet normal 0.504391 0.154656 0.849512
    outer loop
      vertex -36.222000 -56.426998 3.920000
      vertex -36.742001 -56.346001 4.214000
      vertex -36.763000 -56.673000 4.286000
    endloop
  endfacet
  facet normal 0.736920 -0.096986 0.668986
    outer loop
      vertex -37.039001 -57.926998 4.501000
      vertex -36.762001 -57.326000 4.283000
      vertex -36.917000 -57.000000 4.501000
    endloop
  endfacet
  facet normal -0.331623 -0.799212 0.501285
    outer loop
      vertex -90.999001 -1.598000 5.500000
      vertex -91.279999 -2.108000 4.501000
      vertex -90.276001 -1.898000 5.500000
    endloop
  endfacet
  facet normal -0.245176 0.590058 0.769234
    outer loop
      vertex -49.388000 18.448999 2.634000
      vertex -48.999001 18.740999 2.534000
      vertex -49.749001 18.299000 2.634000
    endloop
  endfacet
  facet normal 0.509111 -0.003175 0.860695
    outer loop
      vertex -36.763000 -56.673000 4.286000
      vertex -36.762001 -57.326000 4.283000
      vertex -36.249001 -56.933998 3.981000
    endloop
  endfacet
  facet normal 0.103809 0.788026 0.606827
    outer loop
      vertex -80.999001 18.292999 2.793000
      vertex -80.706001 18.094999 3.000000
      vertex -80.665001 18.249001 2.793000
    endloop
  endfacet
  facet normal 0.737610 -0.097613 0.668134
    outer loop
      vertex -36.742001 -57.653999 4.213000
      vertex -36.762001 -57.326000 4.283000
      vertex -37.039001 -57.926998 4.501000
    endloop
  endfacet
  facet normal -0.129580 0.110803 0.985359
    outer loop
      vertex -50.831001 17.759001 2.500000
      vertex -50.049999 18.370001 2.534000
      vertex -49.999001 18.732000 2.500000
    endloop
  endfacet
  facet normal 0.538995 -0.057987 0.840311
    outer loop
      vertex -36.762001 -57.326000 4.283000
      vertex -36.222000 -57.567001 3.920000
      vertex -36.249001 -56.933998 3.981000
    endloop
  endfacet
  facet normal 0.104981 0.788672 0.605785
    outer loop
      vertex -80.999001 18.292999 2.793000
      vertex -80.999001 18.134001 3.000000
      vertex -80.706001 18.094999 3.000000
    endloop
  endfacet
  facet normal -0.328994 -0.801631 0.499151
    outer loop
      vertex -90.276001 -1.898000 5.500000
      vertex -91.279999 -2.108000 4.501000
      vertex -90.415001 -2.463000 4.501000
    endloop
  endfacet
  facet normal -0.050184 0.382773 0.922478
    outer loop
      vertex -48.999001 18.740999 2.534000
      vertex -49.388000 18.448999 2.634000
      vertex -48.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal -0.112646 -0.858095 0.500983
    outer loop
      vertex -90.276001 -1.898000 5.500000
      vertex -90.415001 -2.463000 4.501000
      vertex -89.499001 -2.000000 5.500000
    endloop
  endfacet
  facet normal -0.110200 -0.859374 0.499332
    outer loop
      vertex -89.499001 -2.000000 5.500000
      vertex -90.415001 -2.463000 4.501000
      vertex -89.487000 -2.582000 4.501000
    endloop
  endfacet
  facet normal -0.034699 0.098299 0.994552
    outer loop
      vertex -50.049999 18.370001 2.534000
      vertex -48.999001 18.740999 2.534000
      vertex -49.999001 18.732000 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -91.620003 -1.121000 5.500000
      vertex -90.999001 -1.598000 5.500000
      vertex -89.999001 0.134000 5.500000
    endloop
  endfacet
  facet normal 0.799984 0.331472 0.500152
    outer loop
      vertex -37.901001 -55.500000 5.500000
      vertex -37.039001 -56.073002 4.501000
      vertex -37.396999 -55.209000 4.501000
    endloop
  endfacet
  facet normal -0.034861 0.130078 0.990891
    outer loop
      vertex -48.999001 18.740999 2.534000
      vertex -48.999001 19.000000 2.500000
      vertex -49.999001 18.732000 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -50.831001 16.240999 2.500000
      vertex -50.831001 17.759001 2.500000
      vertex -79.032997 17.259001 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -49.999001 18.732000 2.500000
      vertex -92.999001 83.000000 2.500000
      vertex -50.831001 17.759001 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -92.999001 83.000000 2.500000
      vertex -49.999001 18.732000 2.500000
      vertex -48.999001 19.000000 2.500000
    endloop
  endfacet
  facet normal -0.130159 0.991493 -0.000000
    outer loop
      vertex -49.257999 17.966000 3.500000
      vertex -48.999001 18.000000 10.500000
      vertex -48.999001 18.000000 3.500000
    endloop
  endfacet
  facet normal -0.129071 0.983200 0.129070
    outer loop
      vertex -48.999001 18.000000 3.500000
      vertex -48.999001 18.034000 3.241000
      vertex -49.257999 17.966000 3.500000
    endloop
  endfacet
  facet normal 0.303273 0.735382 0.606002
    outer loop
      vertex -80.352997 18.120001 2.793000
      vertex -80.706001 18.094999 3.000000
      vertex -80.431999 17.982000 3.000000
    endloop
  endfacet
  facet normal -0.383254 0.923643 -0.000000
    outer loop
      vertex -49.257999 17.966000 3.500000
      vertex -49.499001 17.865999 3.500000
      vertex -49.499001 17.865999 10.500000
    endloop
  endfacet
  facet normal 0.443559 0.577641 0.685263
    outer loop
      vertex -37.403999 -53.903999 3.662000
      vertex -38.708000 -53.897999 4.501000
      vertex -37.966999 -54.466999 4.501000
    endloop
  endfacet
  facet normal 0.303733 0.734621 0.606694
    outer loop
      vertex -80.352997 18.120001 2.793000
      vertex -80.665001 18.249001 2.793000
      vertex -80.706001 18.094999 3.000000
    endloop
  endfacet
  facet normal -0.671738 -0.280794 0.685509
    outer loop
      vertex -93.724998 -0.147000 3.662000
      vertex -93.283997 -1.202000 3.662000
      vertex -92.595001 -0.802000 4.501000
    endloop
  endfacet
  facet normal -0.128403 0.983199 0.129737
    outer loop
      vertex -49.257999 17.966000 3.500000
      vertex -48.999001 18.034000 3.241000
      vertex -49.266998 17.999001 3.241000
    endloop
  endfacet
  facet normal 0.234060 0.566108 0.790403
    outer loop
      vertex -80.249001 18.299000 2.634000
      vertex -80.665001 18.249001 2.793000
      vertex -80.352997 18.120001 2.793000
    endloop
  endfacet
  facet normal -0.607304 0.794469 0.000000
    outer loop
      vertex -49.707001 17.707001 3.500000
      vertex -49.707001 17.707001 10.500000
      vertex -49.499001 17.865999 10.500000
    endloop
  endfacet
  facet normal 0.686733 0.527543 0.500096
    outer loop
      vertex -37.396999 -55.209000 4.501000
      vertex -37.966999 -54.466999 4.501000
      vertex -38.377998 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.380007 0.915818 0.129894
    outer loop
      vertex -49.266998 17.999001 3.241000
      vertex -49.499001 17.865999 3.500000
      vertex -49.257999 17.966000 3.500000
    endloop
  endfacet
  facet normal 0.372867 0.485666 0.790632
    outer loop
      vertex -80.249001 18.299000 2.634000
      vertex -80.352997 18.120001 2.793000
      vertex -79.939003 18.061001 2.634000
    endloop
  endfacet
  facet normal 0.527257 0.686639 0.500527
    outer loop
      vertex -39.000000 -54.402000 5.500000
      vertex -37.966999 -54.466999 4.501000
      vertex -38.708000 -53.897999 4.501000
    endloop
  endfacet
  facet normal -0.271582 -0.209835 0.939262
    outer loop
      vertex -94.999001 -2.200503 2.659568
      vertex -94.999001 -2.254950 2.647404
      vertex -93.266998 -2.793000 3.028000
    endloop
  endfacet
  facet normal -0.121717 0.917518 0.378611
    outer loop
      vertex -48.999001 18.134001 3.000000
      vertex -49.292999 18.094999 3.000000
      vertex -49.266998 17.999001 3.241000
    endloop
  endfacet
  facet normal 0.331813 0.799671 0.500426
    outer loop
      vertex -39.000000 -54.402000 5.500000
      vertex -38.708000 -53.897999 4.501000
      vertex -39.723000 -54.102001 5.500000
    endloop
  endfacet
  facet normal -0.092385 -0.722515 0.685155
    outer loop
      vertex -89.484001 -3.378000 3.662000
      vertex -89.487000 -2.582000 4.501000
      vertex -90.617996 -3.233000 3.662000
    endloop
  endfacet
  facet normal 0.235071 0.306183 0.922493
    outer loop
      vertex -79.767998 18.231001 2.534000
      vertex -80.249001 18.299000 2.634000
      vertex -79.939003 18.061001 2.634000
    endloop
  endfacet
  facet normal -0.092625 -0.722321 0.685327
    outer loop
      vertex -90.617996 -3.233000 3.662000
      vertex -89.487000 -2.582000 4.501000
      vertex -90.415001 -2.463000 4.501000
    endloop
  endfacet
  facet normal 0.526948 0.687132 0.500176
    outer loop
      vertex -39.000000 -54.402000 5.500000
      vertex -38.377998 -54.879002 5.500000
      vertex -37.966999 -54.466999 4.501000
    endloop
  endfacet
  facet normal -0.276399 -0.673806 0.685266
    outer loop
      vertex -90.617996 -3.233000 3.662000
      vertex -90.415001 -2.463000 4.501000
      vertex -91.676003 -2.799000 3.662000
    endloop
  endfacet
  facet normal 0.305853 0.235050 0.922608
    outer loop
      vertex -79.767998 18.231001 2.534000
      vertex -79.939003 18.061001 2.634000
      vertex -79.699997 17.750000 2.634000
    endloop
  endfacet
  facet normal -0.276485 -0.673687 0.685348
    outer loop
      vertex -91.676003 -2.799000 3.662000
      vertex -90.415001 -2.463000 4.501000
      vertex -91.279999 -2.108000 4.501000
    endloop
  endfacet
  facet normal 0.079791 0.607034 0.790660
    outer loop
      vertex -80.999001 18.500000 2.634000
      vertex -80.665001 18.249001 2.793000
      vertex -80.611000 18.448999 2.634000
    endloop
  endfacet
  facet normal -0.794902 0.606738 0.000000
    outer loop
      vertex -49.707001 17.707001 10.500000
      vertex -49.707001 17.707001 3.500000
      vertex -49.865002 17.500000 10.500000
    endloop
  endfacet
  facet normal 0.079988 0.607202 0.790511
    outer loop
      vertex -80.999001 18.292999 2.793000
      vertex -80.665001 18.249001 2.793000
      vertex -80.999001 18.500000 2.634000
    endloop
  endfacet
  facet normal 0.278724 0.672677 0.685433
    outer loop
      vertex -38.310001 -53.208000 3.662000
      vertex -39.571999 -53.540001 4.501000
      vertex -38.708000 -53.897999 4.501000
    endloop
  endfacet
  facet normal 0.234297 0.565438 0.790813
    outer loop
      vertex -80.249001 18.299000 2.634000
      vertex -80.611000 18.448999 2.634000
      vertex -80.665001 18.249001 2.793000
    endloop
  endfacet
  facet normal -0.112858 -0.858598 0.500073
    outer loop
      vertex -41.426998 -60.459999 4.501000
      vertex -40.500000 -60.000000 5.500000
      vertex -41.276001 -59.897999 5.500000
    endloop
  endfacet
  facet normal -0.923644 0.383250 0.000000
    outer loop
      vertex -49.865002 17.500000 10.500000
      vertex -49.865002 17.500000 3.500000
      vertex -49.965000 17.259001 3.500000
    endloop
  endfacet
  facet normal 0.562731 0.734677 0.378925
    outer loop
      vertex -80.196999 17.802000 3.000000
      vertex -80.431999 17.982000 3.000000
      vertex -80.482002 17.896000 3.241000
    endloop
  endfacet
  facet normal -0.915685 0.379948 0.130999
    outer loop
      vertex -49.865002 17.500000 3.500000
      vertex -49.895000 17.517000 3.241000
      vertex -49.965000 17.259001 3.500000
    endloop
  endfacet
  facet normal 0.112716 -0.858621 0.500065
    outer loop
      vertex -40.500000 -60.000000 5.500000
      vertex -39.571999 -60.459999 4.501000
      vertex -39.723000 -59.897999 5.500000
    endloop
  endfacet
  facet normal 0.483818 0.631651 0.605753
    outer loop
      vertex -80.431999 17.982000 3.000000
      vertex -80.196999 17.802000 3.000000
      vertex -80.352997 18.120001 2.793000
    endloop
  endfacet
  facet normal -0.794902 0.606738 -0.000000
    outer loop
      vertex -49.707001 17.707001 3.500000
      vertex -49.865002 17.500000 3.500000
      vertex -49.865002 17.500000 10.500000
    endloop
  endfacet
  facet normal 0.485506 0.631620 0.604433
    outer loop
      vertex -80.352997 18.120001 2.793000
      vertex -80.196999 17.802000 3.000000
      vertex -80.084999 17.914000 2.793000
    endloop
  endfacet
  facet normal 0.112870 -0.858539 0.500171
    outer loop
      vertex -40.500000 -60.000000 5.500000
      vertex -40.500000 -60.582001 4.501000
      vertex -39.571999 -60.459999 4.501000
    endloop
  endfacet
  facet normal 0.278724 -0.672677 0.685433
    outer loop
      vertex -38.708000 -60.102001 4.501000
      vertex -39.571999 -60.459999 4.501000
      vertex -38.310001 -60.792000 3.662000
    endloop
  endfacet
  facet normal 0.852861 0.356201 0.381772
    outer loop
      vertex -80.016998 17.566999 3.000000
      vertex -80.103996 17.517000 3.241000
      vertex -80.000000 17.268000 3.241000
    endloop
  endfacet
  facet normal 0.094938 0.722140 0.685201
    outer loop
      vertex -39.366001 -52.771000 3.662000
      vertex -40.500000 -53.417999 4.501000
      vertex -39.571999 -53.540001 4.501000
    endloop
  endfacet
  facet normal 0.331475 -0.799987 0.500146
    outer loop
      vertex -39.723000 -59.897999 5.500000
      vertex -39.571999 -60.459999 4.501000
      vertex -38.708000 -60.102001 4.501000
    endloop
  endfacet
  facet normal 0.331813 -0.799671 0.500425
    outer loop
      vertex -39.723000 -59.897999 5.500000
      vertex -38.708000 -60.102001 4.501000
      vertex -39.000000 -59.598000 5.500000
    endloop
  endfacet
  facet normal 0.331475 0.799987 0.500146
    outer loop
      vertex -39.723000 -54.102001 5.500000
      vertex -38.708000 -53.897999 4.501000
      vertex -39.571999 -53.540001 4.501000
    endloop
  endfacet
  facet normal -0.576156 -0.445500 0.685255
    outer loop
      vertex -93.283997 -59.202000 3.662000
      vertex -92.584999 -60.105999 3.662000
      vertex -92.024002 -59.541000 4.501000
    endloop
  endfacet
  facet normal -0.334156 -0.438306 0.834402
    outer loop
      vertex -93.266998 -60.792999 3.028000
      vertex -91.676003 -60.799000 3.662000
      vertex -92.584999 -60.105999 3.662000
    endloop
  endfacet
  facet normal -0.094972 0.722175 0.685160
    outer loop
      vertex -41.632999 -52.771000 3.662000
      vertex -40.500000 -53.417999 4.501000
      vertex -40.500000 -52.622002 3.662000
    endloop
  endfacet
  facet normal 0.526948 -0.687132 0.500176
    outer loop
      vertex -38.377998 -59.120998 5.500000
      vertex -39.000000 -59.598000 5.500000
      vertex -37.966999 -59.533001 4.501000
    endloop
  endfacet
  facet normal 0.527257 -0.686639 0.500527
    outer loop
      vertex -39.000000 -59.598000 5.500000
      vertex -38.708000 -60.102001 4.501000
      vertex -37.966999 -59.533001 4.501000
    endloop
  endfacet
  facet normal 0.112870 0.858539 0.500171
    outer loop
      vertex -40.500000 -54.000000 5.500000
      vertex -39.571999 -53.540001 4.501000
      vertex -40.500000 -53.417999 4.501000
    endloop
  endfacet
  facet normal 0.686733 -0.527543 0.500096
    outer loop
      vertex -38.377998 -59.120998 5.500000
      vertex -37.966999 -59.533001 4.501000
      vertex -37.396999 -58.791000 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 -57.966000 5.500000
      vertex -40.500000 -60.000000 5.500000
      vertex -39.723000 -59.897999 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -39.723000 -59.897999 5.500000
      vertex -39.000000 -59.598000 5.500000
      vertex -40.241001 -57.966000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -39.000000 -59.598000 5.500000
      vertex -38.377998 -59.120998 5.500000
      vertex -39.792000 -57.707001 5.500000
    endloop
  endfacet
  facet normal -0.436195 -0.337278 0.834253
    outer loop
      vertex -94.120003 -59.688999 3.028000
      vertex -92.584999 -60.105999 3.662000
      vertex -93.283997 -59.202000 3.662000
    endloop
  endfacet
  facet normal 0.112716 0.858621 0.500065
    outer loop
      vertex -39.723000 -54.102001 5.500000
      vertex -39.571999 -53.540001 4.501000
      vertex -40.500000 -54.000000 5.500000
    endloop
  endfacet
  facet normal -0.436172 -0.337008 0.834374
    outer loop
      vertex -93.266998 -60.792999 3.028000
      vertex -92.584999 -60.105999 3.662000
      vertex -94.120003 -59.688999 3.028000
    endloop
  endfacet
  facet normal 0.372909 0.485137 0.790937
    outer loop
      vertex -80.084999 17.914000 2.793000
      vertex -79.939003 18.061001 2.634000
      vertex -80.352997 18.120001 2.793000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 -82.000000 3.500000
      vertex -35.000000 -82.000000 10.500000
      vertex -35.000000 -65.536003 10.500000
    endloop
  endfacet
  facet normal 0.632820 0.484713 0.603814
    outer loop
      vertex -79.879997 17.646000 2.793000
      vertex -80.196999 17.802000 3.000000
      vertex -80.016998 17.566999 3.000000
    endloop
  endfacet
  facet normal -0.271592 -0.209877 0.939249
    outer loop
      vertex -94.999001 -60.314938 2.634000
      vertex -94.032997 -61.564999 2.634000
      vertex -93.266998 -60.792999 3.028000
    endloop
  endfacet
  facet normal 0.735341 0.307370 0.603985
    outer loop
      vertex -79.750000 17.334999 2.793000
      vertex -79.879997 17.646000 2.793000
      vertex -80.016998 17.566999 3.000000
    endloop
  endfacet
  facet normal -0.271594 -0.209882 0.939248
    outer loop
      vertex -93.266998 -60.792999 3.028000
      vertex -94.999001 -60.254951 2.647404
      vertex -94.999001 -60.307240 2.635720
    endloop
  endfacet
  facet normal 0.632832 0.484074 0.604314
    outer loop
      vertex -80.084999 17.914000 2.793000
      vertex -80.196999 17.802000 3.000000
      vertex -79.879997 17.646000 2.793000
    endloop
  endfacet
  facet normal -0.095038 0.722121 0.685208
    outer loop
      vertex -41.426998 -53.540001 4.501000
      vertex -40.500000 -53.417999 4.501000
      vertex -41.632999 -52.771000 3.662000
    endloop
  endfacet
  facet normal 0.856025 0.353029 0.377613
    outer loop
      vertex -79.903999 17.292999 3.000000
      vertex -80.016998 17.566999 3.000000
      vertex -80.000000 17.268000 3.241000
    endloop
  endfacet
  facet normal -0.247479 -0.076352 0.965880
    outer loop
      vertex -35.455002 -57.592999 4.054000
      vertex -35.467999 -56.931000 4.103000
      vertex -36.060001 -56.935001 3.951000
    endloop
  endfacet
  facet normal -0.112990 0.858527 0.500164
    outer loop
      vertex -40.500000 -54.000000 5.500000
      vertex -40.500000 -53.417999 4.501000
      vertex -41.426998 -53.540001 4.501000
    endloop
  endfacet
  facet normal -0.271583 -0.209838 0.939261
    outer loop
      vertex -93.266998 -60.792999 3.028000
      vertex -94.120003 -59.688999 3.028000
      vertex -94.999001 -60.200504 2.659568
    endloop
  endfacet
  facet normal -0.651223 -0.190956 0.734469
    outer loop
      vertex -35.305000 -57.615002 4.170000
      vertex -35.417000 -58.310001 3.890000
      vertex -35.278999 -58.346001 4.003000
    endloop
  endfacet
  facet normal 0.734212 0.302792 0.607659
    outer loop
      vertex -79.750000 17.334999 2.793000
      vertex -80.016998 17.566999 3.000000
      vertex -79.903999 17.292999 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.500000 -54.000000 5.500000
      vertex -40.500000 -56.000000 5.500000
      vertex -40.241001 -56.034000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.500000 -54.000000 5.500000
      vertex -41.276001 -54.102001 5.500000
      vertex -40.500000 -56.000000 5.500000
    endloop
  endfacet
  facet normal 0.485451 0.373072 0.790667
    outer loop
      vertex -79.939003 18.061001 2.634000
      vertex -80.084999 17.914000 2.793000
      vertex -79.699997 17.750000 2.634000
    endloop
  endfacet
  facet normal 0.793058 0.609146 0.000000
    outer loop
      vertex -90.364998 -57.500000 5.500000
      vertex -90.206001 -57.707001 0.000000
      vertex -90.364998 -57.500000 0.000000
    endloop
  endfacet
  facet normal -0.617340 -0.206360 0.759149
    outer loop
      vertex -35.455002 -57.592999 4.054000
      vertex -35.417000 -58.310001 3.890000
      vertex -35.305000 -57.615002 4.170000
    endloop
  endfacet
  facet normal 0.923646 0.383248 -0.000000
    outer loop
      vertex -90.464996 -57.258999 0.000000
      vertex -90.364998 -57.500000 5.500000
      vertex -90.364998 -57.500000 0.000000
    endloop
  endfacet
  facet normal 0.858159 -0.112942 0.500807
    outer loop
      vertex -37.500000 -57.000000 5.500000
      vertex -37.039001 -57.926998 4.501000
      vertex -36.917000 -57.000000 4.501000
    endloop
  endfacet
  facet normal 0.813990 -0.001423 0.580877
    outer loop
      vertex -36.763000 -56.673000 4.286000
      vertex -36.917000 -57.000000 4.501000
      vertex -36.762001 -57.326000 4.283000
    endloop
  endfacet
  facet normal 0.500331 0.075860 -0.862505
    outer loop
      vertex -94.999001 -57.344002 2.923744
      vertex -94.999001 -59.956860 2.693935
      vertex -95.059998 -60.236000 2.634000
    endloop
  endfacet
  facet normal 0.500353 0.075858 -0.862492
    outer loop
      vertex -95.059998 -60.236000 2.634000
      vertex -94.999001 -57.000000 2.954000
      vertex -94.999001 -57.344002 2.923744
    endloop
  endfacet
  facet normal 0.485077 0.371052 0.791846
    outer loop
      vertex -79.879997 17.646000 2.793000
      vertex -79.699997 17.750000 2.634000
      vertex -80.084999 17.914000 2.793000
    endloop
  endfacet
  facet normal 0.271612 0.209881 -0.939243
    outer loop
      vertex -95.059998 -60.236000 2.634000
      vertex -94.999001 -60.254951 2.647404
      vertex -94.999001 -60.307240 2.635720
    endloop
  endfacet
  facet normal 0.271611 0.209881 -0.939243
    outer loop
      vertex -94.999001 -60.307240 2.635720
      vertex -94.999001 -60.314938 2.634000
      vertex -95.059998 -60.236000 2.634000
    endloop
  endfacet
  facet normal 0.271600 0.209832 -0.939257
    outer loop
      vertex -94.999001 -60.200504 2.659568
      vertex -94.999001 -60.254951 2.647404
      vertex -95.059998 -60.236000 2.634000
    endloop
  endfacet
  facet normal 0.316610 0.132486 -0.939258
    outer loop
      vertex -94.999001 -59.956860 2.693935
      vertex -94.999001 -60.200504 2.659568
      vertex -95.059998 -60.236000 2.634000
    endloop
  endfacet
  facet normal 0.565520 0.236385 0.790132
    outer loop
      vertex -79.550003 17.388000 2.634000
      vertex -79.879997 17.646000 2.793000
      vertex -79.750000 17.334999 2.793000
    endloop
  endfacet
  facet normal -0.616409 -0.065186 0.784723
    outer loop
      vertex -35.305000 -57.615002 4.170000
      vertex -35.313999 -56.928001 4.220000
      vertex -35.455002 -57.592999 4.054000
    endloop
  endfacet
  facet normal 0.090430 0.069878 -0.993448
    outer loop
      vertex -94.999001 -60.371868 2.629996
      vertex -94.999001 -61.439999 2.554864
      vertex -95.059998 -60.236000 2.634000
    endloop
  endfacet
  facet normal 0.090432 0.069879 -0.993448
    outer loop
      vertex -95.059998 -60.236000 2.634000
      vertex -94.999001 -60.314938 2.634000
      vertex -94.999001 -60.371868 2.629996
    endloop
  endfacet
  facet normal 0.564299 0.233817 0.791768
    outer loop
      vertex -79.699997 17.750000 2.634000
      vertex -79.879997 17.646000 2.793000
      vertex -79.550003 17.388000 2.634000
    endloop
  endfacet
  facet normal 0.858229 -0.112810 0.500717
    outer loop
      vertex -37.039001 -57.926998 4.501000
      vertex -37.500000 -57.000000 5.500000
      vertex -37.602001 -57.776001 5.500000
    endloop
  endfacet
  facet normal -0.873657 -0.137685 0.466655
    outer loop
      vertex -35.278999 -58.346001 4.003000
      vertex -35.032001 -58.483002 4.425000
      vertex -35.305000 -57.615002 4.170000
    endloop
  endfacet
  facet normal -0.532855 -0.073321 0.843024
    outer loop
      vertex -94.999001 -61.439999 2.567839
      vertex -94.999001 -57.000000 2.954000
      vertex -95.059998 -60.236000 2.634000
    endloop
  endfacet
  facet normal 0.243519 0.587791 0.771493
    outer loop
      vertex -80.611000 18.448999 2.634000
      vertex -79.767998 18.231001 2.534000
      vertex -80.999001 18.740999 2.534000
    endloop
  endfacet
  facet normal 1.000000 -0.000000 0.000000
    outer loop
      vertex -94.999001 -61.439999 2.567839
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -60.371868 2.629996
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -59.956860 2.693935
      vertex -94.999001 -57.344002 2.923744
      vertex -94.999001 -61.439999 2.567839
    endloop
  endfacet
  facet normal 0.243493 0.587629 0.771624
    outer loop
      vertex -79.767998 18.231001 2.534000
      vertex -80.611000 18.448999 2.634000
      vertex -80.249001 18.299000 2.634000
    endloop
  endfacet
  facet normal 0.733790 0.096574 0.672477
    outer loop
      vertex -36.763000 -56.673000 4.286000
      vertex -37.039001 -56.073002 4.501000
      vertex -36.917000 -57.000000 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -60.371868 2.629996
      vertex -94.999001 -60.307240 2.635720
      vertex -94.999001 -60.254951 2.647404
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -60.371868 2.629996
      vertex -94.999001 -60.254951 2.647404
      vertex -94.999001 -61.439999 2.567839
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.439999 2.567839
      vertex -94.999001 -60.254951 2.647404
      vertex -94.999001 -60.200504 2.659568
    endloop
  endfacet
  facet normal 0.053845 0.129968 0.990055
    outer loop
      vertex -80.999001 18.740999 2.534000
      vertex -79.767998 18.231001 2.534000
      vertex -80.999001 19.000000 2.500000
    endloop
  endfacet
  facet normal -0.925506 0.107973 0.363016
    outer loop
      vertex -35.203999 4.296000 3.400000
      vertex -35.018002 5.739000 3.445000
      vertex -35.164001 5.671000 3.093000
    endloop
  endfacet
  facet normal 0.120199 0.916946 0.380477
    outer loop
      vertex -80.732002 17.999001 3.241000
      vertex -80.999001 18.134001 3.000000
      vertex -80.999001 18.034000 3.241000
    endloop
  endfacet
  facet normal 0.504308 -0.150710 0.850270
    outer loop
      vertex -36.222000 -57.567001 3.920000
      vertex -36.762001 -57.326000 4.283000
      vertex -36.742001 -57.653999 4.213000
    endloop
  endfacet
  facet normal 0.858172 0.112802 0.500815
    outer loop
      vertex -37.500000 -57.000000 5.500000
      vertex -36.917000 -57.000000 4.501000
      vertex -37.602001 -56.223999 5.500000
    endloop
  endfacet
  facet normal 0.757897 -0.156374 0.633355
    outer loop
      vertex -36.667999 -58.316002 3.961000
      vertex -36.742001 -57.653999 4.213000
      vertex -37.039001 -57.926998 4.501000
    endloop
  endfacet
  facet normal 0.858206 0.112948 0.500725
    outer loop
      vertex -37.602001 -56.223999 5.500000
      vertex -36.917000 -57.000000 4.501000
      vertex -37.039001 -56.073002 4.501000
    endloop
  endfacet
  facet normal 0.506690 -0.256660 0.823038
    outer loop
      vertex -36.667999 -58.316002 3.961000
      vertex -36.222000 -57.567001 3.920000
      vertex -36.742001 -57.653999 4.213000
    endloop
  endfacet
  facet normal -0.786913 0.603058 0.130728
    outer loop
      vertex -49.895000 17.517000 3.241000
      vertex -49.865002 17.500000 3.500000
      vertex -49.730999 17.731001 3.241000
    endloop
  endfacet
  facet normal 0.678273 0.268064 0.684170
    outer loop
      vertex -36.708000 -54.811001 3.662000
      vertex -37.396999 -55.209000 4.501000
      vertex -36.667999 -55.682999 3.964000
    endloop
  endfacet
  facet normal 0.424489 -0.204483 0.882041
    outer loop
      vertex -36.141998 -58.255001 3.722000
      vertex -36.222000 -57.567001 3.920000
      vertex -36.667999 -58.316002 3.961000
    endloop
  endfacet
  facet normal -0.922742 0.044198 0.382875
    outer loop
      vertex -35.164001 5.671000 3.093000
      vertex -35.034000 7.103000 3.241000
      vertex -35.133999 7.103000 3.000000
    endloop
  endfacet
  facet normal 0.681145 0.282231 0.675564
    outer loop
      vertex -36.667999 -55.682999 3.964000
      vertex -37.396999 -55.209000 4.501000
      vertex -37.039001 -56.073002 4.501000
    endloop
  endfacet
  facet normal 0.800022 0.330396 0.500802
    outer loop
      vertex -37.602001 -56.223999 5.500000
      vertex -37.039001 -56.073002 4.501000
      vertex -37.901001 -55.500000 5.500000
    endloop
  endfacet
  facet normal -0.925815 0.045264 0.375258
    outer loop
      vertex -35.018002 5.739000 3.445000
      vertex -35.034000 7.103000 3.241000
      vertex -35.164001 5.671000 3.093000
    endloop
  endfacet
  facet normal -0.997154 -0.000422 0.075384
    outer loop
      vertex -35.018002 5.739000 3.445000
      vertex -35.000000 5.539000 3.682000
      vertex -35.034000 7.103000 3.241000
    endloop
  endfacet
  facet normal -0.602091 0.787649 0.130751
    outer loop
      vertex -49.707001 17.707001 3.500000
      vertex -49.499001 17.865999 3.500000
      vertex -49.515999 17.896000 3.241000
    endloop
  endfacet
  facet normal 0.686746 0.527499 0.500124
    outer loop
      vertex -37.901001 -55.500000 5.500000
      vertex -37.396999 -55.209000 4.501000
      vertex -38.377998 -54.879002 5.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -60.200504 2.659568
      vertex -94.999001 -59.956860 2.693935
      vertex -94.999001 -61.439999 2.567839
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.500000 -57.000000 5.500000
      vertex -39.500000 -57.000000 5.500000
      vertex -39.534000 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.901001 -55.500000 5.500000
      vertex -39.792000 -56.292999 5.500000
      vertex -39.633999 -56.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -38.377998 -54.879002 5.500000
      vertex -39.000000 -54.402000 5.500000
      vertex -39.792000 -56.292999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.901001 -55.500000 5.500000
      vertex -38.377998 -54.879002 5.500000
      vertex -39.792000 -56.292999 5.500000
    endloop
  endfacet
  facet normal -0.788281 0.601685 0.128795
    outer loop
      vertex -49.865002 17.500000 3.500000
      vertex -49.707001 17.707001 3.500000
      vertex -49.730999 17.731001 3.241000
    endloop
  endfacet
  facet normal 0.129292 -0.241554 0.961736
    outer loop
      vertex -35.962002 -58.251999 3.713000
      vertex -36.035999 -57.563000 3.896000
      vertex -36.222000 -57.567001 3.920000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -60.254951 2.647404
      vertex -94.999001 -60.200504 2.659568
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -60.200504 2.659568
      vertex -94.999001 -59.956860 2.693935
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -59.956860 2.693935
      vertex -94.999001 -57.344002 2.923744
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -60.314938 2.634000
      vertex -94.999001 -60.307240 2.635720
      vertex -94.999001 -60.371868 2.629996
    endloop
  endfacet
  facet normal -0.603742 0.786699 0.128840
    outer loop
      vertex -49.730999 17.731001 3.241000
      vertex -49.707001 17.707001 3.500000
      vertex -49.515999 17.896000 3.241000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -41.000000 -56.133999 5.500000
      vertex -40.757999 -56.034000 5.500000
      vertex -41.276001 -54.102001 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -40.241001 -56.034000 5.500000
      vertex -39.723000 -54.102001 5.500000
      vertex -40.500000 -54.000000 5.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -60.307240 2.635720
      vertex -94.999001 -60.254951 2.647404
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -0.607304 0.794469 0.000000
    outer loop
      vertex -49.499001 17.865999 3.500000
      vertex -49.707001 17.707001 3.500000
      vertex -49.499001 17.865999 10.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -60.371868 2.629996
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -60.371868 2.629996
      vertex -94.999001 -60.314938 2.634000
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -60.314938 2.634000
      vertex -94.999001 -60.307240 2.635720
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -40.757999 -56.034000 5.500000
      vertex -40.500000 -56.000000 5.500000
      vertex -41.276001 -54.102001 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -40.241001 -56.034000 5.500000
      vertex -39.000000 -54.402000 5.500000
      vertex -39.723000 -54.102001 5.500000
    endloop
  endfacet
  facet normal 0.052576 -0.270532 0.961274
    outer loop
      vertex -36.141998 -58.255001 3.722000
      vertex -35.962002 -58.251999 3.713000
      vertex -36.222000 -57.567001 3.920000
    endloop
  endfacet
  facet normal -0.546357 -0.073482 0.834323
    outer loop
      vertex -94.845001 -57.018002 3.028000
      vertex -94.658997 -58.401001 3.028000
      vertex -93.724998 -58.146999 3.662000
    endloop
  endfacet
  facet normal -0.733692 0.562272 0.381506
    outer loop
      vertex -49.895000 17.517000 3.241000
      vertex -49.730999 17.731001 3.241000
      vertex -49.981998 17.566999 3.000000
    endloop
  endfacet
  facet normal -0.500309 -0.075861 0.862517
    outer loop
      vertex -94.658997 -58.401001 3.028000
      vertex -94.999001 -57.000000 2.954000
      vertex -94.999001 -57.344002 2.923744
    endloop
  endfacet
  facet normal -0.500310 -0.075861 0.862516
    outer loop
      vertex -94.999001 -57.344002 2.923744
      vertex -94.999001 -59.956860 2.693935
      vertex -94.658997 -58.401001 3.028000
    endloop
  endfacet
  facet normal -0.733061 0.564611 0.379257
    outer loop
      vertex -49.981998 17.566999 3.000000
      vertex -49.730999 17.731001 3.241000
      vertex -49.800999 17.802000 3.000000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -41.276001 -54.102001 5.500000
      vertex -42.000000 -54.402000 5.500000
      vertex -41.000000 -56.133999 5.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -40.000000 -56.133999 5.500000
      vertex -39.792000 -56.292999 5.500000
      vertex -39.000000 -54.402000 5.500000
    endloop
  endfacet
  facet normal -0.437947 -0.058901 0.897069
    outer loop
      vertex -94.999001 -57.000000 2.954000
      vertex -94.658997 -58.401001 3.028000
      vertex -94.845001 -57.018002 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.000000 -54.402000 5.500000
      vertex -40.241001 -56.034000 5.500000
      vertex -40.000000 -56.133999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.500000 -57.000000 5.500000
      vertex -37.602001 -56.223999 5.500000
      vertex -39.534000 -56.741001 5.500000
    endloop
  endfacet
  facet normal 0.129272 -0.081610 0.988245
    outer loop
      vertex -36.222000 -57.567001 3.920000
      vertex -36.035999 -57.563000 3.896000
      vertex -36.060001 -56.935001 3.951000
    endloop
  endfacet
  facet normal -0.563425 0.734165 0.378886
    outer loop
      vertex -49.515999 17.896000 3.241000
      vertex -49.566002 17.982000 3.000000
      vertex -49.730999 17.731001 3.241000
    endloop
  endfacet
  facet normal -0.266444 -0.228309 0.936420
    outer loop
      vertex -35.417000 -58.310001 3.890000
      vertex -35.455002 -57.592999 4.054000
      vertex -36.035999 -57.563000 3.896000
    endloop
  endfacet
  facet normal -0.378951 0.916100 0.130985
    outer loop
      vertex -49.515999 17.896000 3.241000
      vertex -49.499001 17.865999 3.500000
      vertex -49.266998 17.999001 3.241000
    endloop
  endfacet
  facet normal -0.794902 -0.606738 0.000000
    outer loop
      vertex -39.792000 -56.292999 5.500000
      vertex -39.633999 -56.500000 0.000000
      vertex -39.633999 -56.500000 5.500000
    endloop
  endfacet
  facet normal -0.316595 -0.132487 0.939263
    outer loop
      vertex -94.120003 -59.688999 3.028000
      vertex -94.658997 -58.401001 3.028000
      vertex -94.999001 -59.956860 2.693935
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.901001 -55.500000 5.500000
      vertex -39.633999 -56.500000 5.500000
      vertex -39.534000 -56.741001 5.500000
    endloop
  endfacet
  facet normal -0.353789 0.855272 0.378607
    outer loop
      vertex -49.566002 17.982000 3.000000
      vertex -49.515999 17.896000 3.241000
      vertex -49.266998 17.999001 3.241000
    endloop
  endfacet
  facet normal -0.923646 -0.383248 -0.000000
    outer loop
      vertex -39.534000 -56.741001 5.500000
      vertex -39.633999 -56.500000 5.500000
      vertex -39.633999 -56.500000 0.000000
    endloop
  endfacet
  facet normal -0.546637 -0.073883 0.834104
    outer loop
      vertex -93.724998 -58.146999 3.662000
      vertex -93.877998 -57.014999 3.662000
      vertex -94.845001 -57.018002 3.028000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.534000 -56.741001 5.500000
      vertex -37.602001 -56.223999 5.500000
      vertex -37.901001 -55.500000 5.500000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -39.534000 -56.741001 5.500000
      vertex -39.534000 -56.741001 0.000000
      vertex -39.500000 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.323330 -0.275198 0.905386
    outer loop
      vertex -35.417000 -58.310001 3.890000
      vertex -36.035999 -57.563000 3.896000
      vertex -35.962002 -58.251999 3.713000
    endloop
  endfacet
  facet normal -0.271593 -0.209882 0.939248
    outer loop
      vertex -94.999001 -60.307240 2.635720
      vertex -94.999001 -60.314938 2.634000
      vertex -93.266998 -60.792999 3.028000
    endloop
  endfacet
  facet normal -0.508661 -0.212861 0.834239
    outer loop
      vertex -93.283997 -59.202000 3.662000
      vertex -94.658997 -58.401001 3.028000
      vertex -94.120003 -59.688999 3.028000
    endloop
  endfacet
  facet normal -0.508560 -0.212584 0.834371
    outer loop
      vertex -93.283997 -59.202000 3.662000
      vertex -93.724998 -58.146999 3.662000
      vertex -94.658997 -58.401001 3.028000
    endloop
  endfacet
  facet normal -0.271581 -0.209834 0.939262
    outer loop
      vertex -94.999001 -60.200504 2.659568
      vertex -94.999001 -60.254951 2.647404
      vertex -93.266998 -60.792999 3.028000
    endloop
  endfacet
  facet normal -0.265774 -0.094184 0.959423
    outer loop
      vertex -36.060001 -56.935001 3.951000
      vertex -36.035999 -57.563000 3.896000
      vertex -35.455002 -57.592999 4.054000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.534000 -57.258999 5.500000
      vertex -39.633999 -57.500000 5.500000
      vertex -37.901001 -58.500000 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -37.602001 -57.776001 5.500000
      vertex -37.500000 -57.000000 5.500000
      vertex -39.534000 -57.258999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -39.534000 -56.741001 5.500000
      vertex -39.500000 -57.000000 5.500000
      vertex -37.500000 -57.000000 5.500000
    endloop
  endfacet
  facet normal -0.316596 -0.132487 0.939263
    outer loop
      vertex -94.999001 -59.956860 2.693935
      vertex -94.999001 -60.200504 2.659568
      vertex -94.120003 -59.688999 3.028000
    endloop
  endfacet
  facet normal -0.923646 0.383248 0.000000
    outer loop
      vertex -39.534000 -57.258999 5.500000
      vertex -39.534000 -57.258999 0.000000
      vertex -39.633999 -57.500000 5.500000
    endloop
  endfacet
  facet normal -0.090426 -0.069878 0.993449
    outer loop
      vertex -94.032997 -61.564999 2.634000
      vertex -94.999001 -60.371868 2.629996
      vertex -94.999001 -61.439999 2.554864
    endloop
  endfacet
  facet normal -0.090427 -0.069879 0.993448
    outer loop
      vertex -94.032997 -61.564999 2.634000
      vertex -94.999001 -60.314938 2.634000
      vertex -94.999001 -60.371868 2.629996
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.983948 2.516604
      vertex -94.999001 -61.983990 2.516601
      vertex -94.999001 -62.220001 2.500000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -61.983948 2.516604
    endloop
  endfacet
  facet normal 0.090426 0.069878 -0.993449
    outer loop
      vertex -94.999001 -62.220001 2.500000
      vertex -95.059998 -60.236000 2.634000
      vertex -94.999001 -61.439999 2.554864
    endloop
  endfacet
  facet normal 0.052634 -0.322369 0.945150
    outer loop
      vertex -35.962002 -58.251999 3.713000
      vertex -36.141998 -58.255001 3.722000
      vertex -35.819000 -59.418999 3.307000
    endloop
  endfacet
  facet normal -0.532852 -0.073320 0.843026
    outer loop
      vertex -95.059998 -60.236000 2.634000
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -61.439999 2.567839
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -61.983990 2.516601
      vertex -94.999001 -61.439999 2.567839
      vertex -94.999001 -62.220001 2.500000
    endloop
  endfacet
  facet normal 0.130655 -0.991428 0.000000
    outer loop
      vertex -40.757999 -56.034000 0.000000
      vertex -40.500000 -56.000000 0.000000
      vertex -40.500000 -56.000000 5.500000
    endloop
  endfacet
  facet normal 0.130655 -0.991428 0.000000
    outer loop
      vertex -40.500000 -56.000000 5.500000
      vertex -40.757999 -56.034000 5.500000
      vertex -40.757999 -56.034000 0.000000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.439999 2.567839
      vertex -94.999001 -61.983990 2.516601
      vertex -94.999001 -61.983948 2.516604
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.983948 2.516604
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -61.439999 2.567839
    endloop
  endfacet
  facet normal -0.130159 -0.991493 0.000000
    outer loop
      vertex -40.241001 -56.034000 5.500000
      vertex -40.500000 -56.000000 5.500000
      vertex -40.500000 -56.000000 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.983948 2.516604
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -61.983990 2.516601
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -61.983948 2.516604
    endloop
  endfacet
  facet normal -0.383248 -0.923646 -0.000000
    outer loop
      vertex -40.241001 -56.034000 5.500000
      vertex -40.000000 -56.133999 0.000000
      vertex -40.000000 -56.133999 5.500000
    endloop
  endfacet
  facet normal -0.069900 -0.546677 0.834421
    outer loop
      vertex -89.484001 -61.377998 3.662000
      vertex -90.617996 -61.233002 3.662000
      vertex -90.865997 -62.168999 3.028000
    endloop
  endfacet
  facet normal -0.607309 -0.794466 -0.000000
    outer loop
      vertex -39.792000 -56.292999 0.000000
      vertex -40.000000 -56.133999 5.500000
      vertex -40.000000 -56.133999 0.000000
    endloop
  endfacet
  facet normal -0.607309 -0.794466 -0.000000
    outer loop
      vertex -39.792000 -56.292999 5.500000
      vertex -40.000000 -56.133999 5.500000
      vertex -39.792000 -56.292999 0.000000
    endloop
  endfacet
  facet normal -0.794902 -0.606738 0.000000
    outer loop
      vertex -39.633999 -56.500000 0.000000
      vertex -39.792000 -56.292999 5.500000
      vertex -39.792000 -56.292999 0.000000
    endloop
  endfacet
  facet normal -0.923646 -0.383248 -0.000000
    outer loop
      vertex -39.633999 -56.500000 0.000000
      vertex -39.534000 -56.741001 0.000000
      vertex -39.534000 -56.741001 5.500000
    endloop
  endfacet
  facet normal -0.991493 0.130159 -0.000000
    outer loop
      vertex -39.500000 -57.000000 5.500000
      vertex -39.534000 -57.258999 0.000000
      vertex -39.534000 -57.258999 5.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 -50.896999 3.500000
      vertex -35.000000 -65.536003 10.500000
      vertex -35.000000 -5.103000 3.500000
    endloop
  endfacet
  facet normal -0.334138 -0.438408 0.834356
    outer loop
      vertex -91.676003 -60.799000 3.662000
      vertex -93.266998 -60.792999 3.028000
      vertex -92.156998 -61.639000 3.028000
    endloop
  endfacet
  facet normal -0.208033 -0.272951 0.939266
    outer loop
      vertex -92.156998 -61.639000 3.028000
      vertex -93.266998 -60.792999 3.028000
      vertex -94.032997 -61.564999 2.634000
    endloop
  endfacet
  facet normal 0.053709 0.120379 0.991274
    outer loop
      vertex -36.209000 -52.673000 2.727000
      vertex -36.000000 -50.896999 2.500000
      vertex -37.283001 -51.428001 2.634000
    endloop
  endfacet
  facet normal -0.090426 -0.069878 0.993449
    outer loop
      vertex -94.999001 -61.983990 2.516601
      vertex -94.999001 -62.220001 2.500000
      vertex -94.032997 -61.564999 2.634000
    endloop
  endfacet
  facet normal -0.091361 -0.067739 0.993511
    outer loop
      vertex -94.999001 -61.983948 2.516604
      vertex -94.999001 -61.983990 2.516601
      vertex -94.032997 -61.564999 2.634000
    endloop
  endfacet
  facet normal 0.053679 0.120451 0.991267
    outer loop
      vertex -36.000000 -50.896999 2.500000
      vertex -38.667999 -49.708000 2.500000
      vertex -37.283001 -51.428001 2.634000
    endloop
  endfacet
  facet normal -0.090426 -0.069878 0.993449
    outer loop
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -61.983948 2.516604
      vertex -94.032997 -61.564999 2.634000
    endloop
  endfacet
  facet normal 0.015618 0.124960 0.992039
    outer loop
      vertex -35.733002 -52.407001 2.686000
      vertex -36.000000 -50.896999 2.500000
      vertex -36.209000 -52.673000 2.727000
    endloop
  endfacet
  facet normal -0.129523 0.098633 0.986659
    outer loop
      vertex -35.741001 -50.896999 2.534000
      vertex -36.000000 -50.896999 2.500000
      vertex -35.733002 -52.407001 2.686000
    endloop
  endfacet
  facet normal -0.091351 -0.356814 0.929698
    outer loop
      vertex -35.819000 -59.418999 3.307000
      vertex -36.141998 -58.255001 3.722000
      vertex -35.980999 -59.414001 3.293000
    endloop
  endfacet
  facet normal -0.994441 0.030073 0.100912
    outer loop
      vertex -35.018002 5.739000 3.445000
      vertex -35.000000 4.029000 4.132000
      vertex -35.000000 5.539000 3.682000
    endloop
  endfacet
  facet normal -0.327225 0.092926 0.940366
    outer loop
      vertex -35.604000 -52.397999 2.730000
      vertex -35.741001 -50.896999 2.534000
      vertex -35.733002 -52.407001 2.686000
    endloop
  endfacet
  facet normal -0.381856 0.085316 0.920276
    outer loop
      vertex -35.500000 -50.896999 2.634000
      vertex -35.741001 -50.896999 2.534000
      vertex -35.604000 -52.397999 2.730000
    endloop
  endfacet
  facet normal -0.605044 0.086268 0.791505
    outer loop
      vertex -35.292000 -50.896999 2.793000
      vertex -35.500000 -50.896999 2.634000
      vertex -35.248001 -52.349998 2.985000
    endloop
  endfacet
  facet normal -0.793366 0.056074 0.606157
    outer loop
      vertex -35.164001 -52.328999 3.093000
      vertex -35.292000 -50.896999 2.793000
      vertex -35.248001 -52.349998 2.985000
    endloop
  endfacet
  facet normal 0.234790 0.291385 0.927345
    outer loop
      vertex -36.719002 4.780000 3.028000
      vertex -36.446999 3.727000 3.290000
      vertex -36.209000 5.327000 2.727000
    endloop
  endfacet
  facet normal -0.793655 0.055971 0.605788
    outer loop
      vertex -35.133999 -50.896999 3.000000
      vertex -35.292000 -50.896999 2.793000
      vertex -35.164001 -52.328999 3.093000
    endloop
  endfacet
  facet normal -0.075336 -0.092022 0.992903
    outer loop
      vertex -94.032997 -61.564999 2.634000
      vertex -94.999001 -62.220001 2.500000
      vertex -93.531998 -63.421001 2.500000
    endloop
  endfacet
  facet normal -0.922742 0.044198 0.382875
    outer loop
      vertex -35.034000 -50.896999 3.241000
      vertex -35.133999 -50.896999 3.000000
      vertex -35.164001 -52.328999 3.093000
    endloop
  endfacet
  facet normal -0.991463 0.007837 0.130155
    outer loop
      vertex -35.034000 -50.896999 3.241000
      vertex -35.018002 -52.261002 3.445000
      vertex -35.000000 -50.896999 3.500000
    endloop
  endfacet
  facet normal -0.043530 -0.340613 0.939195
    outer loop
      vertex -91.142998 -63.220001 2.634000
      vertex -89.481003 -62.346001 3.028000
      vertex -90.865997 -62.168999 3.028000
    endloop
  endfacet
  facet normal -0.991493 0.000000 0.130159
    outer loop
      vertex -35.034000 -50.896999 3.241000
      vertex -35.000000 -50.896999 3.500000
      vertex -35.000000 -5.103000 3.500000
    endloop
  endfacet
  facet normal -0.130431 -0.317711 0.939174
    outer loop
      vertex -92.696999 -62.582001 2.634000
      vertex -90.865997 -62.168999 3.028000
      vertex -92.156998 -61.639000 3.028000
    endloop
  endfacet
  facet normal -0.208026 -0.273276 0.939173
    outer loop
      vertex -92.696999 -62.582001 2.634000
      vertex -92.156998 -61.639000 3.028000
      vertex -94.032997 -61.564999 2.634000
    endloop
  endfacet
  facet normal -0.130434 -0.317702 0.939177
    outer loop
      vertex -90.865997 -62.168999 3.028000
      vertex -92.696999 -62.582001 2.634000
      vertex -91.142998 -63.220001 2.634000
    endloop
  endfacet
  facet normal -0.873677 -0.160878 0.459137
    outer loop
      vertex -35.026001 -59.680000 4.017000
      vertex -35.032001 -58.483002 4.425000
      vertex -35.278999 -58.346001 4.003000
    endloop
  endfacet
  facet normal -0.328292 0.242768 0.912846
    outer loop
      vertex -35.733002 5.593000 2.686000
      vertex -35.735001 4.184000 3.060000
      vertex -35.604000 5.602000 2.730000
    endloop
  endfacet
  facet normal -0.192167 0.252025 0.948449
    outer loop
      vertex -35.884998 4.175000 3.032000
      vertex -35.735001 4.184000 3.060000
      vertex -35.733002 5.593000 2.686000
    endloop
  endfacet
  facet normal -0.068727 -0.090284 0.993542
    outer loop
      vertex -93.531998 -63.421001 2.500000
      vertex -92.696999 -62.582001 2.634000
      vertex -94.032997 -61.564999 2.634000
    endloop
  endfacet
  facet normal -0.130158 0.000000 0.991493
    outer loop
      vertex -36.000000 -32.768002 2.500000
      vertex -36.000000 -50.896999 2.500000
      vertex -35.741001 -50.896999 2.534000
    endloop
  endfacet
  facet normal -0.651438 -0.260531 0.712567
    outer loop
      vertex -35.417000 -58.310001 3.890000
      vertex -35.347000 -59.497002 3.520000
      vertex -35.278999 -58.346001 4.003000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -36.000000 -32.768002 2.500000
      vertex -38.667999 -49.708000 2.500000
      vertex -36.000000 -50.896999 2.500000
    endloop
  endfacet
  facet normal -0.323394 -0.298927 0.897808
    outer loop
      vertex -35.417000 -58.310001 3.890000
      vertex -35.962002 -58.251999 3.713000
      vertex -35.347000 -59.497002 3.520000
    endloop
  endfacet
  facet normal -0.043734 -0.340276 0.939308
    outer loop
      vertex -89.477997 -63.433998 2.634000
      vertex -89.481003 -62.346001 3.028000
      vertex -91.142998 -63.220001 2.634000
    endloop
  endfacet
  facet normal -0.998806 0.011265 0.047537
    outer loop
      vertex -35.000000 -56.999001 4.946000
      vertex -35.000000 -50.896999 3.500000
      vertex -35.018002 -52.261002 3.445000
    endloop
  endfacet
  facet normal -0.588310 0.197457 0.784157
    outer loop
      vertex -35.604000 5.602000 2.730000
      vertex -35.307999 4.260000 3.290000
      vertex -35.248001 5.650000 2.985000
    endloop
  endfacet
  facet normal -0.493128 0.240149 0.836154
    outer loop
      vertex -35.307999 4.260000 3.290000
      vertex -35.604000 5.602000 2.730000
      vertex -35.735001 4.184000 3.060000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 -50.896999 3.500000
      vertex -35.000000 -56.999001 4.946000
      vertex -35.000000 -65.536003 10.500000
    endloop
  endfacet
  facet normal -0.046205 -0.112543 0.992572
    outer loop
      vertex -92.696999 -62.582001 2.634000
      vertex -93.531998 -63.421001 2.500000
      vertex -91.142998 -63.220001 2.634000
    endloop
  endfacet
  facet normal -0.033081 -0.177078 0.983641
    outer loop
      vertex -89.477997 -63.433998 2.634000
      vertex -93.531998 -63.421001 2.500000
      vertex -88.056000 -64.444000 2.500000
    endloop
  endfacet
  facet normal 0.521626 -0.297740 0.799536
    outer loop
      vertex -36.446999 -59.728001 3.291000
      vertex -36.667999 -58.316002 3.961000
      vertex -36.708000 -59.188999 3.662000
    endloop
  endfacet
  facet normal -0.032761 -0.254895 0.966414
    outer loop
      vertex -91.142998 -63.220001 2.634000
      vertex -93.531998 -63.421001 2.500000
      vertex -89.477997 -63.433998 2.634000
    endloop
  endfacet
  facet normal -0.794215 0.154323 0.587713
    outer loop
      vertex -35.248001 5.650000 2.985000
      vertex -35.203999 4.296000 3.400000
      vertex -35.164001 5.671000 3.093000
    endloop
  endfacet
  facet normal -0.743353 0.173817 0.645921
    outer loop
      vertex -35.203999 4.296000 3.400000
      vertex -35.248001 5.650000 2.985000
      vertex -35.307999 4.260000 3.290000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -93.531998 -63.421001 2.500000
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -82.000000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 -82.000000 2.500000
      vertex -88.056000 -64.444000 2.500000
      vertex -93.531998 -63.421001 2.500000
    endloop
  endfacet
  facet normal -0.051761 0.241966 0.968903
    outer loop
      vertex -35.733002 5.593000 2.686000
      vertex -36.209000 5.327000 2.727000
      vertex -35.884998 4.175000 3.032000
    endloop
  endfacet
  facet normal -0.763134 -0.211207 0.610752
    outer loop
      vertex -35.278999 -58.346001 4.003000
      vertex -35.347000 -59.497002 3.520000
      vertex -35.188000 -60.806000 3.266000
    endloop
  endfacet
  facet normal 0.015618 0.124960 0.992039
    outer loop
      vertex -36.209000 5.327000 2.727000
      vertex -35.733002 5.593000 2.686000
      vertex -36.000000 7.103000 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -94.999001 -82.000000 2.500000
      vertex -94.999001 -62.220001 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -82.000000 0.000000
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -62.220001 2.500000
      vertex -94.999001 -61.439999 2.554864
      vertex -94.999001 -51.779999 2.500000
    endloop
  endfacet
  facet normal -0.432688 -0.266002 0.861408
    outer loop
      vertex -35.284000 -60.775002 3.157000
      vertex -35.347000 -59.497002 3.520000
      vertex -35.819000 -59.418999 3.307000
    endloop
  endfacet
  facet normal -0.129523 0.098633 0.986659
    outer loop
      vertex -35.741001 7.103000 2.534000
      vertex -36.000000 7.103000 2.500000
      vertex -35.733002 5.593000 2.686000
    endloop
  endfacet
  facet normal -0.327224 0.092926 0.940367
    outer loop
      vertex -35.733002 5.593000 2.686000
      vertex -35.604000 5.602000 2.730000
      vertex -35.741001 7.103000 2.534000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -94.931000 -82.517998 2.500000
      vertex -94.731003 -83.000000 2.500000
      vertex -88.056000 -64.444000 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -94.731003 -83.000000 2.500000
      vertex -94.413002 -83.414001 2.500000
      vertex -88.056000 -64.444000 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -94.413002 -83.414001 2.500000
      vertex -93.999001 -83.732002 2.500000
      vertex -88.056000 -64.444000 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -93.516998 -83.931999 2.500000
      vertex -92.999001 -84.000000 2.500000
      vertex -88.056000 -64.444000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -88.056000 -64.444000 2.500000
      vertex -94.999001 -82.000000 2.500000
      vertex -94.931000 -82.517998 2.500000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 0.000000
    outer loop
      vertex -94.931000 -82.517998 0.000000
      vertex -94.999001 -82.000000 2.500000
      vertex -94.999001 -82.000000 0.000000
    endloop
  endfacet
  facet normal -0.991493 -0.130159 -0.000000
    outer loop
      vertex -94.931000 -82.517998 2.500000
      vertex -94.999001 -82.000000 2.500000
      vertex -94.931000 -82.517998 0.000000
    endloop
  endfacet
  facet normal -0.381856 0.085316 0.920276
    outer loop
      vertex -35.500000 7.103000 2.634000
      vertex -35.741001 7.103000 2.534000
      vertex -35.604000 5.602000 2.730000
    endloop
  endfacet
  facet normal -0.923646 -0.383248 -0.000000
    outer loop
      vertex -94.731003 -83.000000 2.500000
      vertex -94.931000 -82.517998 0.000000
      vertex -94.731003 -83.000000 0.000000
    endloop
  endfacet
  facet normal -0.923646 -0.383248 -0.000000
    outer loop
      vertex -94.931000 -82.517998 2.500000
      vertex -94.931000 -82.517998 0.000000
      vertex -94.731003 -83.000000 2.500000
    endloop
  endfacet
  facet normal -0.793051 -0.609155 -0.000000
    outer loop
      vertex -94.413002 -83.414001 2.500000
      vertex -94.731003 -83.000000 0.000000
      vertex -94.413002 -83.414001 0.000000
    endloop
  endfacet
  facet normal -0.793051 -0.609155 -0.000000
    outer loop
      vertex -94.731003 -83.000000 2.500000
      vertex -94.731003 -83.000000 0.000000
      vertex -94.413002 -83.414001 2.500000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 -0.000000
    outer loop
      vertex -93.999001 -83.732002 2.500000
      vertex -94.413002 -83.414001 0.000000
      vertex -93.999001 -83.732002 0.000000
    endloop
  endfacet
  facet normal -0.609155 -0.793051 -0.000000
    outer loop
      vertex -94.413002 -83.414001 2.500000
      vertex -94.413002 -83.414001 0.000000
      vertex -93.999001 -83.732002 2.500000
    endloop
  endfacet
  facet normal -0.588022 0.092137 0.803580
    outer loop
      vertex -35.500000 7.103000 2.634000
      vertex -35.604000 5.602000 2.730000
      vertex -35.248001 5.650000 2.985000
    endloop
  endfacet
  facet normal -0.383248 -0.923646 -0.000000
    outer loop
      vertex -93.516998 -83.931999 2.500000
      vertex -93.999001 -83.732002 0.000000
      vertex -93.516998 -83.931999 0.000000
    endloop
  endfacet
  facet normal -0.383248 -0.923646 -0.000000
    outer loop
      vertex -93.999001 -83.732002 2.500000
      vertex -93.999001 -83.732002 0.000000
      vertex -93.516998 -83.931999 2.500000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 -0.000000
    outer loop
      vertex -92.999001 -84.000000 2.500000
      vertex -93.516998 -83.931999 0.000000
      vertex -92.999001 -84.000000 0.000000
    endloop
  endfacet
  facet normal -0.130159 -0.991493 -0.000000
    outer loop
      vertex -93.516998 -83.931999 2.500000
      vertex -93.516998 -83.931999 0.000000
      vertex -92.999001 -84.000000 2.500000
    endloop
  endfacet
  facet normal -0.605044 0.086268 0.791505
    outer loop
      vertex -35.292000 7.103000 2.793000
      vertex -35.500000 7.103000 2.634000
      vertex -35.248001 5.650000 2.985000
    endloop
  endfacet
  facet normal -0.793366 0.056074 0.606157
    outer loop
      vertex -35.164001 5.671000 3.093000
      vertex -35.292000 7.103000 2.793000
      vertex -35.248001 5.650000 2.985000
    endloop
  endfacet
  facet normal -0.793655 0.055971 0.605788
    outer loop
      vertex -35.133999 7.103000 3.000000
      vertex -35.292000 7.103000 2.793000
      vertex -35.164001 5.671000 3.093000
    endloop
  endfacet
  facet normal 0.059299 0.107175 0.992470
    outer loop
      vertex -37.283001 6.572000 2.634000
      vertex -36.000000 7.103000 2.500000
      vertex -37.716999 8.053000 2.500000
    endloop
  endfacet
  facet normal -0.432883 -0.343061 0.833619
    outer loop
      vertex -35.819000 -59.418999 3.307000
      vertex -35.347000 -59.497002 3.520000
      vertex -35.962002 -58.251999 3.713000
    endloop
  endfacet
  facet normal 0.131288 0.317176 0.939235
    outer loop
      vertex -38.834000 7.214000 2.634000
      vertex -39.116001 6.164000 3.028000
      vertex -37.283001 6.572000 2.634000
    endloop
  endfacet
  facet normal -0.069906 -0.546712 0.834397
    outer loop
      vertex -89.481003 -4.346000 3.028000
      vertex -89.484001 -3.378000 3.662000
      vertex -90.617996 -3.233000 3.662000
    endloop
  endfacet
  facet normal 0.131291 0.317165 0.939239
    outer loop
      vertex -37.826000 5.630000 3.028000
      vertex -37.283001 6.572000 2.634000
      vertex -39.116001 6.164000 3.028000
    endloop
  endfacet
  facet normal 0.207647 -0.314065 0.926416
    outer loop
      vertex -35.980999 -59.414001 3.293000
      vertex -36.141998 -58.255001 3.722000
      vertex -36.446999 -59.728001 3.291000
    endloop
  endfacet
  facet normal 0.042360 0.102336 0.993848
    outer loop
      vertex -37.283001 6.572000 2.634000
      vertex -37.716999 8.053000 2.500000
      vertex -38.834000 7.214000 2.634000
    endloop
  endfacet
  facet normal 0.184667 -0.280061 0.942053
    outer loop
      vertex -36.446999 -59.728001 3.291000
      vertex -35.825001 -60.696999 2.881000
      vertex -35.980999 -59.414001 3.293000
    endloop
  endfacet
  facet normal 0.087785 0.664776 0.741867
    outer loop
      vertex -40.500000 7.434000 2.634000
      vertex -38.834000 7.214000 2.634000
      vertex -43.472000 7.976000 2.500000
    endloop
  endfacet
  facet normal 0.421750 -0.333979 0.842962
    outer loop
      vertex -36.667999 -58.316002 3.961000
      vertex -36.446999 -59.728001 3.291000
      vertex -36.141998 -58.255001 3.722000
    endloop
  endfacet
  facet normal -0.209191 -0.509966 0.834371
    outer loop
      vertex -92.156998 -3.639000 3.028000
      vertex -90.617996 -3.233000 3.662000
      vertex -91.676003 -2.799000 3.662000
    endloop
  endfacet
  facet normal -0.044945 0.340150 0.939297
    outer loop
      vertex -40.500000 7.434000 2.634000
      vertex -42.165001 7.214000 2.634000
      vertex -40.500000 6.346000 3.028000
    endloop
  endfacet
  facet normal 0.044764 0.340406 0.939212
    outer loop
      vertex -38.834000 7.214000 2.634000
      vertex -40.500000 6.346000 3.028000
      vertex -39.116001 6.164000 3.028000
    endloop
  endfacet
  facet normal -0.441449 -0.579259 0.685260
    outer loop
      vertex -92.024002 -1.541000 4.501000
      vertex -92.584999 -2.106000 3.662000
      vertex -91.279999 -2.108000 4.501000
    endloop
  endfacet
  facet normal 0.447704 -0.324102 0.833378
    outer loop
      vertex -36.719002 -60.779999 3.028000
      vertex -36.446999 -59.728001 3.291000
      vertex -37.403999 -60.096001 3.662000
    endloop
  endfacet
  facet normal 0.044918 0.340150 0.939298
    outer loop
      vertex -40.500000 7.434000 2.634000
      vertex -40.500000 6.346000 3.028000
      vertex -38.834000 7.214000 2.634000
    endloop
  endfacet
  facet normal -0.576325 -0.445306 0.685238
    outer loop
      vertex -92.584999 -2.106000 3.662000
      vertex -92.024002 -1.541000 4.501000
      vertex -92.595001 -0.802000 4.501000
    endloop
  endfacet
  facet normal -0.018748 0.141886 0.989705
    outer loop
      vertex -42.165001 7.214000 2.634000
      vertex -40.500000 7.434000 2.634000
      vertex -43.472000 7.976000 2.500000
    endloop
  endfacet
  facet normal -0.002147 0.160502 0.987033
    outer loop
      vertex -38.834000 7.214000 2.634000
      vertex -37.716999 8.053000 2.500000
      vertex -43.472000 7.976000 2.500000
    endloop
  endfacet
  facet normal -0.441505 -0.579115 0.685347
    outer loop
      vertex -91.279999 -2.108000 4.501000
      vertex -92.584999 -2.106000 3.662000
      vertex -91.676003 -2.799000 3.662000
    endloop
  endfacet
  facet normal -0.914794 -0.146600 0.376377
    outer loop
      vertex -35.278999 -58.346001 4.003000
      vertex -35.188000 -60.806000 3.266000
      vertex -35.021000 -60.910999 3.631000
    endloop
  endfacet
  facet normal -0.044796 0.340398 0.939214
    outer loop
      vertex -41.882999 6.164000 3.028000
      vertex -40.500000 6.346000 3.028000
      vertex -42.165001 7.214000 2.634000
    endloop
  endfacet
  facet normal -0.071916 0.546482 0.834377
    outer loop
      vertex -40.500000 6.346000 3.028000
      vertex -41.882999 6.164000 3.028000
      vertex -40.500000 5.378000 3.662000
    endloop
  endfacet
  facet normal -0.762518 -0.211277 0.611496
    outer loop
      vertex -35.284000 -60.775002 3.157000
      vertex -35.188000 -60.806000 3.266000
      vertex -35.347000 -59.497002 3.520000
    endloop
  endfacet
  facet normal -0.576043 -0.445412 0.685407
    outer loop
      vertex -92.595001 -0.802000 4.501000
      vertex -93.283997 -1.202000 3.662000
      vertex -92.584999 -2.106000 3.662000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -37.716999 8.053000 2.500000
      vertex -36.133999 14.500000 2.500000
      vertex -36.500000 14.866000 2.500000
    endloop
  endfacet
  facet normal -0.530266 -0.297054 0.794089
    outer loop
      vertex -35.819000 -59.418999 3.307000
      vertex -35.682999 -60.707001 2.916000
      vertex -35.284000 -60.775002 3.157000
    endloop
  endfacet
  facet normal 0.053709 0.120379 0.991274
    outer loop
      vertex -37.283001 6.572000 2.634000
      vertex -36.209000 5.327000 2.727000
      vertex -36.000000 7.103000 2.500000
    endloop
  endfacet
  facet normal -0.436195 -0.337278 0.834253
    outer loop
      vertex -94.120003 -1.689000 3.028000
      vertex -92.584999 -2.106000 3.662000
      vertex -93.283997 -1.202000 3.662000
    endloop
  endfacet
  facet normal 0.224014 0.263338 0.938334
    outer loop
      vertex -36.209000 5.327000 2.727000
      vertex -37.283001 6.572000 2.634000
      vertex -37.826000 5.630000 3.028000
    endloop
  endfacet
  facet normal 0.228286 0.297308 0.927089
    outer loop
      vertex -37.826000 5.630000 3.028000
      vertex -36.719002 4.780000 3.028000
      vertex -36.209000 5.327000 2.727000
    endloop
  endfacet
  facet normal -0.998459 -0.012793 0.054002
    outer loop
      vertex -35.021000 -60.910999 3.631000
      vertex -35.000000 -63.103001 3.500000
      vertex -35.000000 -56.999001 4.946000
    endloop
  endfacet
  facet normal 0.278500 0.672988 0.685219
    outer loop
      vertex -38.310001 4.792000 3.662000
      vertex -39.366001 5.229000 3.662000
      vertex -39.571999 4.460000 4.501000
    endloop
  endfacet
  facet normal 0.278725 0.672676 0.685433
    outer loop
      vertex -38.310001 4.792000 3.662000
      vertex -39.571999 4.460000 4.501000
      vertex -38.708000 4.102000 4.501000
    endloop
  endfacet
  facet normal 0.443622 0.577475 0.685362
    outer loop
      vertex -38.310001 4.792000 3.662000
      vertex -38.708000 4.102000 4.501000
      vertex -37.403999 4.096000 3.662000
    endloop
  endfacet
  facet normal -0.856953 -0.157374 0.490780
    outer loop
      vertex -35.021000 -60.910999 3.631000
      vertex -35.026001 -59.680000 4.017000
      vertex -35.278999 -58.346001 4.003000
    endloop
  endfacet
  facet normal -0.334138 -0.438408 0.834356
    outer loop
      vertex -92.156998 -3.639000 3.028000
      vertex -91.676003 -2.799000 3.662000
      vertex -93.266998 -2.793000 3.028000
    endloop
  endfacet
  facet normal -0.334156 -0.438307 0.834402
    outer loop
      vertex -91.676003 -2.799000 3.662000
      vertex -92.584999 -2.106000 3.662000
      vertex -93.266998 -2.793000 3.028000
    endloop
  endfacet
  facet normal 0.335789 0.437106 0.834377
    outer loop
      vertex -38.310001 4.792000 3.662000
      vertex -37.403999 4.096000 3.662000
      vertex -36.719002 4.780000 3.028000
    endloop
  endfacet
  facet normal -0.208033 -0.272951 0.939266
    outer loop
      vertex -94.032997 -3.565000 2.634000
      vertex -92.156998 -3.639000 3.028000
      vertex -93.266998 -2.793000 3.028000
    endloop
  endfacet
  facet normal -0.915664 -0.123645 0.382454
    outer loop
      vertex -35.021000 -60.910999 3.631000
      vertex -35.000000 -56.999001 4.946000
      vertex -35.026001 -59.680000 4.017000
    endloop
  endfacet
  facet normal -0.436172 -0.337008 0.834374
    outer loop
      vertex -94.120003 -1.689000 3.028000
      vertex -93.266998 -2.793000 3.028000
      vertex -92.584999 -2.106000 3.662000
    endloop
  endfacet
  facet normal -0.271592 -0.209877 0.939249
    outer loop
      vertex -93.266998 -2.793000 3.028000
      vertex -94.999001 -2.254950 2.647404
      vertex -94.999001 -2.314938 2.634000
    endloop
  endfacet
  facet normal -0.271592 -0.209877 0.939249
    outer loop
      vertex -94.032997 -3.565000 2.634000
      vertex -93.266998 -2.793000 3.028000
      vertex -94.999001 -2.314938 2.634000
    endloop
  endfacet
  facet normal 0.335759 0.437276 0.834299
    outer loop
      vertex -37.826000 5.630000 3.028000
      vertex -38.310001 4.792000 3.662000
      vertex -36.719002 4.780000 3.028000
    endloop
  endfacet
  facet normal -0.271583 -0.209838 0.939261
    outer loop
      vertex -93.266998 -2.793000 3.028000
      vertex -94.120003 -1.689000 3.028000
      vertex -94.999001 -2.200503 2.659568
    endloop
  endfacet
  facet normal 0.094889 0.722179 0.685167
    outer loop
      vertex -40.500000 4.582000 4.501000
      vertex -39.366001 5.229000 3.662000
      vertex -40.500000 5.378000 3.662000
    endloop
  endfacet
  facet normal -0.069865 -0.546683 0.834420
    outer loop
      vertex -90.617996 -3.233000 3.662000
      vertex -90.865997 -4.169000 3.028000
      vertex -89.481003 -4.346000 3.028000
    endloop
  endfacet
  facet normal 0.094936 0.722141 0.685200
    outer loop
      vertex -39.366001 5.229000 3.662000
      vertex -40.500000 4.582000 4.501000
      vertex -39.571999 4.460000 4.501000
    endloop
  endfacet
  facet normal 0.210850 0.509357 0.834324
    outer loop
      vertex -39.366001 5.229000 3.662000
      vertex -37.826000 5.630000 3.028000
      vertex -39.116001 6.164000 3.028000
    endloop
  endfacet
  facet normal 0.210816 0.509431 0.834288
    outer loop
      vertex -38.310001 4.792000 3.662000
      vertex -37.826000 5.630000 3.028000
      vertex -39.366001 5.229000 3.662000
    endloop
  endfacet
  facet normal 0.090400 0.069877 -0.993451
    outer loop
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -4.096000 2.508722
      vertex -95.059998 -2.236000 2.634000
    endloop
  endfacet
  facet normal 0.500332 0.075860 -0.862504
    outer loop
      vertex -95.059998 -2.236000 2.634000
      vertex -94.999001 0.000000 2.866047
      vertex -94.999001 -1.956860 2.693935
    endloop
  endfacet
  facet normal 0.271605 0.209876 -0.939246
    outer loop
      vertex -94.999001 -2.254950 2.647404
      vertex -94.999001 -2.314938 2.634000
      vertex -95.059998 -2.236000 2.634000
    endloop
  endfacet
  facet normal 0.071864 0.546484 0.834380
    outer loop
      vertex -40.500000 6.346000 3.028000
      vertex -40.500000 5.378000 3.662000
      vertex -39.116001 6.164000 3.028000
    endloop
  endfacet
  facet normal 0.271595 0.209835 -0.939258
    outer loop
      vertex -94.999001 -2.200503 2.659568
      vertex -94.999001 -2.254950 2.647404
      vertex -95.059998 -2.236000 2.634000
    endloop
  endfacet
  facet normal 0.316607 0.132487 -0.939259
    outer loop
      vertex -94.999001 -1.956860 2.693935
      vertex -94.999001 -2.200503 2.659568
      vertex -95.059998 -2.236000 2.634000
    endloop
  endfacet
  facet normal 0.071812 0.546546 0.834344
    outer loop
      vertex -39.116001 6.164000 3.028000
      vertex -40.500000 5.378000 3.662000
      vertex -39.366001 5.229000 3.662000
    endloop
  endfacet
  facet normal 0.090431 0.069878 -0.993448
    outer loop
      vertex -95.059998 -2.236000 2.634000
      vertex -94.999001 -2.314938 2.634000
      vertex -94.999001 -3.929617 2.520425
    endloop
  endfacet
  facet normal -0.532855 -0.073321 0.843024
    outer loop
      vertex -94.999001 -4.096000 2.510785
      vertex -94.999001 1.000000 2.954000
      vertex -95.059998 -2.236000 2.634000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -4.096000 2.510785
      vertex -94.999001 0.000000 2.866047
      vertex -94.999001 1.000000 2.954000
    endloop
  endfacet
  facet normal 1.000000 -0.000000 0.000000
    outer loop
      vertex -94.999001 -4.096000 2.510785
      vertex -94.999001 -4.096000 2.508722
      vertex -94.999001 -3.929617 2.520425
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -4.096000 2.510785
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -1.956860 2.693935
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -1.956860 2.693935
      vertex -94.999001 0.000000 2.866047
      vertex -94.999001 -4.096000 2.510785
    endloop
  endfacet
  facet normal 0.233808 -0.292281 0.927311
    outer loop
      vertex -36.719002 -60.779999 3.028000
      vertex -36.209000 -61.327000 2.727000
      vertex -36.446999 -59.728001 3.291000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -2.314938 2.634000
      vertex -94.999001 -2.254950 2.647404
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -2.254950 2.647404
      vertex -94.999001 -2.200503 2.659568
    endloop
  endfacet
  facet normal 0.448528 0.323193 0.833288
    outer loop
      vertex -36.719002 4.780000 3.028000
      vertex -37.403999 4.096000 3.662000
      vertex -36.446999 3.727000 3.290000
    endloop
  endfacet
  facet normal 1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -2.200503 2.659568
      vertex -94.999001 -1.956860 2.693935
      vertex -94.999001 -3.929617 2.520425
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 -2.254950 2.647404
      vertex -94.999001 -2.200503 2.659568
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 -2.200503 2.659568
      vertex -94.999001 -1.956860 2.693935
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -1.956860 2.693935
      vertex -94.999001 0.000000 2.866047
      vertex -94.999001 16.384001 0.000000
    endloop
  endfacet
  facet normal 0.577752 0.443825 0.684998
    outer loop
      vertex -36.708000 3.189000 3.662000
      vertex -37.966999 3.533000 4.501000
      vertex -37.396999 2.791000 4.501000
    endloop
  endfacet
  facet normal 0.577797 0.443380 0.685248
    outer loop
      vertex -36.708000 3.189000 3.662000
      vertex -37.403999 4.096000 3.662000
      vertex -37.966999 3.533000 4.501000
    endloop
  endfacet
  facet normal -1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -2.314938 2.634000
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 16.384001 0.000000
      vertex -94.999001 -2.314938 2.634000
      vertex -94.999001 -2.254950 2.647404
    endloop
  endfacet
  facet normal -0.091308 -0.298083 0.950163
    outer loop
      vertex -35.682999 -60.707001 2.916000
      vertex -35.819000 -59.418999 3.307000
      vertex -35.980999 -59.414001 3.293000
    endloop
  endfacet
  facet normal 0.453141 0.347724 0.820823
    outer loop
      vertex -37.403999 4.096000 3.662000
      vertex -36.708000 3.189000 3.662000
      vertex -36.446999 3.727000 3.290000
    endloop
  endfacet
  facet normal 0.134298 -0.311785 0.940614
    outer loop
      vertex -36.446999 -59.728001 3.291000
      vertex -36.209000 -61.327000 2.727000
      vertex -35.825001 -60.696999 2.881000
    endloop
  endfacet
  facet normal -0.500311 -0.075861 0.862516
    outer loop
      vertex -94.658997 -0.401000 3.028000
      vertex -94.999001 1.000000 2.954000
      vertex -94.999001 0.000000 2.866047
    endloop
  endfacet
  facet normal -0.500310 -0.075861 0.862516
    outer loop
      vertex -94.999001 0.000000 2.866047
      vertex -94.999001 -1.956860 2.693935
      vertex -94.658997 -0.401000 3.028000
    endloop
  endfacet
  facet normal -0.010943 0.338073 0.941056
    outer loop
      vertex -35.884998 4.175000 3.032000
      vertex -36.070000 2.780000 3.531000
      vertex -35.897999 2.780000 3.533000
    endloop
  endfacet
  facet normal -0.508560 -0.212584 0.834371
    outer loop
      vertex -94.658997 -0.401000 3.028000
      vertex -93.283997 -1.202000 3.662000
      vertex -93.724998 -0.147000 3.662000
    endloop
  endfacet
  facet normal -0.508661 -0.212861 0.834239
    outer loop
      vertex -94.658997 -0.401000 3.028000
      vertex -94.120003 -1.689000 3.028000
      vertex -93.283997 -1.202000 3.662000
    endloop
  endfacet
  facet normal -0.929831 0.108890 0.351506
    outer loop
      vertex -35.030998 2.684000 4.357000
      vertex -35.018002 5.739000 3.445000
      vertex -35.203999 4.296000 3.400000
    endloop
  endfacet
  facet normal -0.874450 0.174806 0.452526
    outer loop
      vertex -35.030998 2.684000 4.357000
      vertex -35.203999 4.296000 3.400000
      vertex -35.257999 2.892000 3.838000
    endloop
  endfacet
  facet normal -0.316596 -0.132487 0.939263
    outer loop
      vertex -94.120003 -1.689000 3.028000
      vertex -94.658997 -0.401000 3.028000
      vertex -94.999001 -1.956860 2.693935
    endloop
  endfacet
  facet normal -0.316595 -0.132488 0.939263
    outer loop
      vertex -94.999001 -1.956860 2.693935
      vertex -94.999001 -2.200503 2.659568
      vertex -94.120003 -1.689000 3.028000
    endloop
  endfacet
  facet normal 0.189373 0.300734 0.934717
    outer loop
      vertex -35.884998 4.175000 3.032000
      vertex -36.209000 5.327000 2.727000
      vertex -36.446999 3.727000 3.290000
    endloop
  endfacet
  facet normal -0.090426 -0.069878 0.993449
    outer loop
      vertex -94.032997 -3.565000 2.634000
      vertex -94.999001 -2.314938 2.634000
      vertex -94.999001 -3.929617 2.520425
    endloop
  endfacet
  facet normal -0.090427 -0.069877 0.993449
    outer loop
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -4.096000 2.508722
      vertex -94.032997 -3.565000 2.634000
    endloop
  endfacet
  facet normal -0.988833 0.046476 0.141594
    outer loop
      vertex -35.000000 4.029000 4.132000
      vertex -35.018002 5.739000 3.445000
      vertex -35.030998 2.684000 4.357000
    endloop
  endfacet
  facet normal 0.519715 0.300781 0.799642
    outer loop
      vertex -36.708000 3.189000 3.662000
      vertex -36.667999 2.317000 3.964000
      vertex -36.446999 3.727000 3.290000
    endloop
  endfacet
  facet normal 0.090449 0.069878 -0.993447
    outer loop
      vertex -95.059998 -2.236000 2.634000
      vertex -94.999001 -4.096000 2.508722
      vertex -94.999001 -4.220000 2.500000
    endloop
  endfacet
  facet normal -0.247865 -0.323395 0.913224
    outer loop
      vertex -35.682999 -60.707001 2.916000
      vertex -35.980999 -59.414001 3.293000
      vertex -35.825001 -60.696999 2.881000
    endloop
  endfacet
  facet normal -0.532852 -0.073321 0.843026
    outer loop
      vertex -95.059998 -2.236000 2.634000
      vertex -94.999001 -4.220000 2.500000
      vertex -94.999001 -4.096000 2.510785
    endloop
  endfacet
  facet normal 0.678273 0.268063 0.684170
    outer loop
      vertex -37.396999 2.791000 4.501000
      vertex -36.667999 2.317000 3.964000
      vertex -36.708000 3.189000 3.662000
    endloop
  endfacet
  facet normal 0.681146 0.282232 0.675563
    outer loop
      vertex -37.039001 1.927000 4.501000
      vertex -36.667999 2.317000 3.964000
      vertex -37.396999 2.791000 4.501000
    endloop
  endfacet
  facet normal 1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -4.220000 2.500000
      vertex -94.999001 -4.096000 2.508722
      vertex -94.999001 -4.096000 2.510785
    endloop
  endfacet
  facet normal -1.000000 0.000000 -0.000000
    outer loop
      vertex -94.999001 -4.096000 2.508722
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -8.192000 0.000000
    endloop
  endfacet
  facet normal -0.209280 -0.509775 0.834465
    outer loop
      vertex -90.865997 -4.169000 3.028000
      vertex -90.617996 -3.233000 3.662000
      vertex -92.156998 -3.639000 3.028000
    endloop
  endfacet
  facet normal -0.130431 -0.317711 0.939174
    outer loop
      vertex -90.865997 -4.169000 3.028000
      vertex -92.156998 -3.639000 3.028000
      vertex -92.696999 -4.582000 2.634000
    endloop
  endfacet
  facet normal -0.192294 0.333281 0.923010
    outer loop
      vertex -35.897999 2.780000 3.533000
      vertex -35.735001 4.184000 3.060000
      vertex -35.884998 4.175000 3.032000
    endloop
  endfacet
  facet normal -0.090426 -0.069879 0.993449
    outer loop
      vertex -94.999001 -4.096000 2.508722
      vertex -94.999001 -4.220000 2.500000
      vertex -94.032997 -3.565000 2.634000
    endloop
  endfacet
  facet normal -0.373901 0.282473 0.883406
    outer loop
      vertex -35.386002 2.851000 3.727000
      vertex -35.897999 2.780000 3.533000
      vertex -35.426998 2.165000 3.929000
    endloop
  endfacet
  facet normal -0.043530 -0.340614 0.939195
    outer loop
      vertex -91.142998 -5.220000 2.634000
      vertex -89.481003 -4.346000 3.028000
      vertex -90.865997 -4.169000 3.028000
    endloop
  endfacet
  facet normal -0.374121 0.334793 0.864839
    outer loop
      vertex -35.897999 2.780000 3.533000
      vertex -35.386002 2.851000 3.727000
      vertex -35.735001 4.184000 3.060000
    endloop
  endfacet
  facet normal -0.678038 0.209135 0.704647
    outer loop
      vertex -35.305000 1.621000 4.170000
      vertex -35.257999 2.892000 3.838000
      vertex -35.386002 2.851000 3.727000
    endloop
  endfacet
  facet normal -0.060093 -0.202310 0.977476
    outer loop
      vertex -35.708000 -61.872002 2.645000
      vertex -35.825001 -60.696999 2.881000
      vertex -36.209000 -61.327000 2.727000
    endloop
  endfacet
  facet normal -0.678816 0.251545 0.689879
    outer loop
      vertex -35.386002 2.851000 3.727000
      vertex -35.257999 2.892000 3.838000
      vertex -35.307999 4.260000 3.290000
    endloop
  endfacet
  facet normal -0.208026 -0.273277 0.939173
    outer loop
      vertex -94.032997 -3.565000 2.634000
      vertex -92.696999 -4.582000 2.634000
      vertex -92.156998 -3.639000 3.028000
    endloop
  endfacet
  facet normal -0.445294 0.277304 0.851361
    outer loop
      vertex -35.426998 2.165000 3.929000
      vertex -35.305000 1.621000 4.170000
      vertex -35.386002 2.851000 3.727000
    endloop
  endfacet
  facet normal -0.493394 0.282463 0.822665
    outer loop
      vertex -35.386002 2.851000 3.727000
      vertex -35.307999 4.260000 3.290000
      vertex -35.735001 4.184000 3.060000
    endloop
  endfacet
  facet normal 0.679548 -0.265388 0.683947
    outer loop
      vertex -36.667999 -58.316002 3.961000
      vertex -37.396999 -58.791000 4.501000
      vertex -36.708000 -59.188999 3.662000
    endloop
  endfacet
  facet normal -0.882632 0.149087 0.445797
    outer loop
      vertex -35.030998 2.684000 4.357000
      vertex -35.257999 2.892000 3.838000
      vertex -35.305000 1.621000 4.170000
    endloop
  endfacet
  facet normal 0.577752 -0.443825 0.684997
    outer loop
      vertex -36.708000 -59.188999 3.662000
      vertex -37.396999 -58.791000 4.501000
      vertex -37.966999 -59.533001 4.501000
    endloop
  endfacet
  facet normal -0.072834 -0.095679 0.992744
    outer loop
      vertex -92.696999 -4.582000 2.634000
      vertex -94.032997 -3.565000 2.634000
      vertex -94.999001 -4.220000 2.500000
    endloop
  endfacet
  facet normal -0.743706 0.224990 0.629508
    outer loop
      vertex -35.257999 2.892000 3.838000
      vertex -35.203999 4.296000 3.400000
      vertex -35.307999 4.260000 3.290000
    endloop
  endfacet
  facet normal 0.348753 0.359141 0.865673
    outer loop
      vertex -36.070000 2.780000 3.531000
      vertex -36.446999 3.727000 3.290000
      vertex -36.667999 2.317000 3.964000
    endloop
  endfacet
  facet normal -0.130434 -0.317703 0.939176
    outer loop
      vertex -91.142998 -5.220000 2.634000
      vertex -90.865997 -4.169000 3.028000
      vertex -92.696999 -4.582000 2.634000
    endloop
  endfacet
  facet normal -0.923646 0.383248 0.000000
    outer loop
      vertex -39.633999 -57.500000 0.000000
      vertex -39.633999 -57.500000 5.500000
      vertex -39.534000 -57.258999 0.000000
    endloop
  endfacet
  facet normal -0.077230 -0.166066 0.983086
    outer loop
      vertex -91.142998 -5.220000 2.634000
      vertex -94.999001 -4.220000 2.500000
      vertex -89.947998 -6.569000 2.500000
    endloop
  endfacet
  facet normal 0.756511 0.155123 0.635317
    outer loop
      vertex -36.667999 2.317000 3.964000
      vertex -37.039001 1.927000 4.501000
      vertex -36.742001 1.654000 4.214000
    endloop
  endfacet
  facet normal -0.794902 0.606738 0.000000
    outer loop
      vertex -39.633999 -57.500000 0.000000
      vertex -39.792000 -57.707001 5.500000
      vertex -39.633999 -57.500000 5.500000
    endloop
  endfacet
  facet normal -0.794902 0.606738 0.000000
    outer loop
      vertex -39.792000 -57.707001 0.000000
      vertex -39.792000 -57.707001 5.500000
      vertex -39.633999 -57.500000 0.000000
    endloop
  endfacet
  facet normal -0.607309 0.794466 0.000000
    outer loop
      vertex -39.792000 -57.707001 5.500000
      vertex -39.792000 -57.707001 0.000000
      vertex -40.000000 -57.866001 0.000000
    endloop
  endfacet
  facet normal -0.607309 0.794466 0.000000
    outer loop
      vertex -40.000000 -57.866001 0.000000
      vertex -40.000000 -57.866001 5.500000
      vertex -39.792000 -57.707001 5.500000
    endloop
  endfacet
  facet normal -0.310390 0.219618 0.924893
    outer loop
      vertex -35.980000 2.112000 3.756000
      vertex -35.455002 1.599000 4.054000
      vertex -35.426998 2.165000 3.929000
    endloop
  endfacet
  facet normal -0.383248 0.923646 0.000000
    outer loop
      vertex -40.000000 -57.866001 5.500000
      vertex -40.000000 -57.866001 0.000000
      vertex -40.241001 -57.966000 5.500000
    endloop
  endfacet
  facet normal -0.091566 -0.223030 0.970502
    outer loop
      vertex -92.696999 -4.582000 2.634000
      vertex -94.999001 -4.220000 2.500000
      vertex -91.142998 -5.220000 2.634000
    endloop
  endfacet
  facet normal -0.310411 0.335078 0.889588
    outer loop
      vertex -35.980000 2.112000 3.756000
      vertex -35.426998 2.165000 3.929000
      vertex -35.897999 2.780000 3.533000
    endloop
  endfacet
  facet normal -0.267237 0.264743 0.926550
    outer loop
      vertex -36.035999 1.569000 3.895000
      vertex -35.455002 1.599000 4.054000
      vertex -35.980000 2.112000 3.756000
    endloop
  endfacet
  facet normal -0.043735 -0.340275 0.939308
    outer loop
      vertex -89.477997 -5.434000 2.634000
      vertex -89.481003 -4.346000 3.028000
      vertex -91.142998 -5.220000 2.634000
    endloop
  endfacet
  facet normal -0.011025 0.317852 0.948076
    outer loop
      vertex -35.980000 2.112000 3.756000
      vertex -35.897999 2.780000 3.533000
      vertex -36.070000 2.780000 3.531000
    endloop
  endfacet
  facet normal 0.130655 0.991428 -0.000000
    outer loop
      vertex -40.757999 -57.966000 5.500000
      vertex -40.500000 -58.000000 5.500000
      vertex -40.500000 -58.000000 0.000000
    endloop
  endfacet
  facet normal -0.014316 -0.111387 0.993674
    outer loop
      vertex -91.142998 -5.220000 2.634000
      vertex -89.947998 -6.569000 2.500000
      vertex -89.477997 -5.434000 2.634000
    endloop
  endfacet
  facet normal 0.381896 0.924205 0.000000
    outer loop
      vertex -40.757999 -57.966000 5.500000
      vertex -40.757999 -57.966000 0.000000
      vertex -41.000000 -57.866001 0.000000
    endloop
  endfacet
  facet normal 0.437942 0.273983 0.856236
    outer loop
      vertex -36.160999 2.116000 3.769000
      vertex -36.667999 2.317000 3.964000
      vertex -36.742001 1.654000 4.214000
    endloop
  endfacet
  facet normal 0.432591 0.251090 0.865921
    outer loop
      vertex -36.160999 2.116000 3.769000
      vertex -36.070000 2.780000 3.531000
      vertex -36.667999 2.317000 3.964000
    endloop
  endfacet
  facet normal 0.443559 -0.577641 0.685263
    outer loop
      vertex -38.708000 -60.102001 4.501000
      vertex -37.403999 -60.096001 3.662000
      vertex -37.966999 -59.533001 4.501000
    endloop
  endfacet
  facet normal 0.443622 -0.577476 0.685362
    outer loop
      vertex -38.310001 -60.792000 3.662000
      vertex -37.403999 -60.096001 3.662000
      vertex -38.708000 -60.102001 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 -4.220000 2.500000
      vertex -94.999001 -32.768002 2.500000
      vertex -89.947998 -6.569000 2.500000
    endloop
  endfacet
  facet normal 0.181520 0.309781 0.933320
    outer loop
      vertex -36.070000 2.780000 3.531000
      vertex -35.884998 4.175000 3.032000
      vertex -36.446999 3.727000 3.290000
    endloop
  endfacet
  facet normal 0.577797 -0.443380 0.685248
    outer loop
      vertex -37.966999 -59.533001 4.501000
      vertex -37.403999 -60.096001 3.662000
      vertex -36.708000 -59.188999 3.662000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -94.999001 -4.220000 2.500000
      vertex -94.999001 -4.096000 2.508722
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -94.999001 -8.192000 0.000000
      vertex -94.999001 -3.929617 2.520425
      vertex -94.999001 -2.314938 2.634000
    endloop
  endfacet
  facet normal 0.074821 0.240045 0.967874
    outer loop
      vertex -36.160999 2.116000 3.769000
      vertex -36.035999 1.569000 3.895000
      vertex -35.980000 2.112000 3.756000
    endloop
  endfacet
  facet normal 0.074887 0.327356 0.941929
    outer loop
      vertex -36.160999 2.116000 3.769000
      vertex -35.980000 2.112000 3.756000
      vertex -36.070000 2.780000 3.531000
    endloop
  endfacet
  facet normal -1.000000 -0.000000 0.000000
    outer loop
      vertex -94.999001 -4.220000 2.500000
      vertex -94.999001 -8.192000 0.000000
      vertex -94.999001 -32.768002 2.500000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 -32.768002 2.500000
      vertex -87.154999 -49.852001 2.500000
      vertex -46.541000 -3.582000 2.500000
    endloop
  endfacet
  facet normal 0.134240 0.251467 0.958511
    outer loop
      vertex -36.160999 2.116000 3.769000
      vertex -36.222000 1.573000 3.920000
      vertex -36.035999 1.569000 3.895000
    endloop
  endfacet
  facet normal 0.505175 0.178076 0.844445
    outer loop
      vertex -36.160999 2.116000 3.769000
      vertex -36.742001 1.654000 4.214000
      vertex -36.222000 1.573000 3.920000
    endloop
  endfacet
  facet normal 0.335789 -0.437106 0.834376
    outer loop
      vertex -38.310001 -60.792000 3.662000
      vertex -36.719002 -60.779999 3.028000
      vertex -37.403999 -60.096001 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -87.154999 -49.852001 2.500000
      vertex -84.654999 -51.167000 2.500000
      vertex -46.541000 -3.582000 2.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -94.999001 -32.768002 2.500000
      vertex -90.879997 -49.605000 2.500000
      vertex -87.154999 -49.852001 2.500000
    endloop
  endfacet
  facet normal 0.451972 -0.346826 0.821847
    outer loop
      vertex -37.403999 -60.096001 3.662000
      vertex -36.446999 -59.728001 3.291000
      vertex -36.708000 -59.188999 3.662000
    endloop
  endfacet
  facet normal -0.000000 0.000000 1.000000
    outer loop
      vertex -85.454002 -63.342999 2.500000
      vertex -92.999001 -84.000000 2.500000
      vertex -47.028000 -60.730000 2.500000
    endloop
  endfacet
  facet normal -0.097475 0.721825 0.685177
    outer loop
      vertex -90.647003 -52.775002 3.662000
      vertex -89.511002 -53.417999 4.501000
      vertex -89.514000 -52.622002 3.662000
    endloop
  endfacet
  facet normal 0.094889 -0.722180 0.685165
    outer loop
      vertex -40.500000 -60.582001 4.501000
      vertex -40.500000 -61.377998 3.662000
      vertex -39.366001 -61.229000 3.662000
    endloop
  endfacet
  facet normal 0.094938 -0.722140 0.685201
    outer loop
      vertex -39.366001 -61.229000 3.662000
      vertex -39.571999 -60.459999 4.501000
      vertex -40.500000 -60.582001 4.501000
    endloop
  endfacet
  facet normal 0.071812 -0.546546 0.834344
    outer loop
      vertex -39.116001 -62.164001 3.028000
      vertex -39.366001 -61.229000 3.662000
      vertex -40.500000 -61.377998 3.662000
    endloop
  endfacet
  facet normal 0.278500 -0.672988 0.685219
    outer loop
      vertex -39.366001 -61.229000 3.662000
      vertex -38.310001 -60.792000 3.662000
      vertex -39.571999 -60.459999 4.501000
    endloop
  endfacet
  facet normal 0.210816 -0.509431 0.834288
    outer loop
      vertex -39.366001 -61.229000 3.662000
      vertex -37.826000 -61.630001 3.028000
      vertex -38.310001 -60.792000 3.662000
    endloop
  endfacet
  facet normal 0.210850 -0.509357 0.834325
    outer loop
      vertex -39.366001 -61.229000 3.662000
      vertex -39.116001 -62.164001 3.028000
      vertex -37.826000 -61.630001 3.028000
    endloop
  endfacet
  facet normal 0.228286 -0.297308 0.927089
    outer loop
      vertex -36.719002 -60.779999 3.028000
      vertex -37.826000 -61.630001 3.028000
      vertex -36.209000 -61.327000 2.727000
    endloop
  endfacet
  facet normal -0.094972 -0.722175 0.685160
    outer loop
      vertex -41.632999 -61.229000 3.662000
      vertex -40.500000 -61.377998 3.662000
      vertex -40.500000 -60.582001 4.501000
    endloop
  endfacet
  facet normal -0.383248 0.923646 0.000000
    outer loop
      vertex -40.241001 -57.966000 5.500000
      vertex -40.000000 -57.866001 0.000000
      vertex -40.241001 -57.966000 0.000000
    endloop
  endfacet
  facet normal -0.130159 0.991493 -0.000000
    outer loop
      vertex -40.500000 -58.000000 0.000000
      vertex -40.241001 -57.966000 5.500000
      vertex -40.241001 -57.966000 0.000000
    endloop
  endfacet
  facet normal -0.130159 0.991493 0.000000
    outer loop
      vertex -40.500000 -58.000000 5.500000
      vertex -40.241001 -57.966000 5.500000
      vertex -40.500000 -58.000000 0.000000
    endloop
  endfacet
  facet normal 0.130655 0.991428 -0.000000
    outer loop
      vertex -40.500000 -58.000000 0.000000
      vertex -40.757999 -57.966000 0.000000
      vertex -40.757999 -57.966000 5.500000
    endloop
  endfacet
  facet normal 0.672141 0.281162 0.684963
    outer loop
      vertex -85.274002 -55.853001 3.662000
      vertex -86.403000 -55.198002 4.501000
      vertex -86.042000 -56.061001 4.501000
    endloop
  endfacet
  facet normal 0.672106 0.280943 0.685088
    outer loop
      vertex -85.714996 -54.798000 3.662000
      vertex -86.403000 -55.198002 4.501000
      vertex -85.274002 -55.853001 3.662000
    endloop
  endfacet
  facet normal 0.799220 0.334321 0.499476
    outer loop
      vertex -86.403000 -55.198002 4.501000
      vertex -86.901001 -55.500000 5.500000
      vertex -86.042000 -56.061001 4.501000
    endloop
  endfacet
  facet normal -0.991482 -0.004827 0.130157
    outer loop
      vertex -35.018002 -61.993999 3.404000
      vertex -35.034000 -63.103001 3.241000
      vertex -35.000000 -63.103001 3.500000
    endloop
  endfacet
  facet normal 0.576110 0.445918 0.685022
    outer loop
      vertex -86.974998 -54.459000 4.501000
      vertex -86.403000 -55.198002 4.501000
      vertex -85.714996 -54.798000 3.662000
    endloop
  endfacet
  facet normal 0.576154 0.445503 0.685255
    outer loop
      vertex -86.974998 -54.459000 4.501000
      vertex -85.714996 -54.798000 3.662000
      vertex -86.414001 -53.894001 3.662000
    endloop
  endfacet
  facet normal -1.000000 -0.000000 0.000000
    outer loop
      vertex -35.000000 -56.999001 4.946000
      vertex -35.000000 -63.103001 3.500000
      vertex -35.000000 -65.536003 10.500000
    endloop
  endfacet
  facet normal -0.928869 -0.091215 0.359003
    outer loop
      vertex -35.158001 -61.938000 3.056000
      vertex -35.018002 -61.993999 3.404000
      vertex -35.188000 -60.806000 3.266000
    endloop
  endfacet
  facet normal 0.686168 0.527055 0.501384
    outer loop
      vertex -86.901001 -55.500000 5.500000
      vertex -86.403000 -55.198002 4.501000
      vertex -87.377998 -54.879002 5.500000
    endloop
  endfacet
  facet normal -0.998893 -0.012283 0.045409
    outer loop
      vertex -35.018002 -61.993999 3.404000
      vertex -35.000000 -63.103001 3.500000
      vertex -35.021000 -60.910999 3.631000
    endloop
  endfacet
  facet normal 0.441450 0.579259 0.685260
    outer loop
      vertex -86.414001 -53.894001 3.662000
      vertex -87.719002 -53.891998 4.501000
      vertex -86.974998 -54.459000 4.501000
    endloop
  endfacet
  facet normal -0.915078 -0.085155 0.394183
    outer loop
      vertex -35.188000 -60.806000 3.266000
      vertex -35.018002 -61.993999 3.404000
      vertex -35.021000 -60.910999 3.631000
    endloop
  endfacet
  facet normal 0.685145 0.530312 0.499345
    outer loop
      vertex -87.377998 -54.879002 5.500000
      vertex -86.403000 -55.198002 4.501000
      vertex -86.974998 -54.459000 4.501000
    endloop
  endfacet
  facet normal 0.053709 -0.120379 0.991274
    outer loop
      vertex -36.209000 -61.327000 2.727000
      vertex -37.283001 -62.571999 2.634000
      vertex -36.000000 -63.103001 2.500000
    endloop
  endfacet
  facet normal -0.929220 -0.040579 0.367292
    outer loop
      vertex -35.158001 -61.938000 3.056000
      vertex -35.034000 -63.103001 3.241000
      vertex -35.018002 -61.993999 3.404000
    endloop
  endfacet
  facet normal 0.441506 0.579115 0.685346
    outer loop
      vertex -87.322998 -53.201000 3.662000
      vertex -87.719002 -53.891998 4.501000
      vertex -86.414001 -53.894001 3.662000
    endloop
  endfacet
  facet normal 0.527132 0.686267 0.501169
    outer loop
      vertex -87.377998 -54.879002 5.500000
      vertex -86.974998 -54.459000 4.501000
      vertex -87.999001 -54.402000 5.500000
    endloop
  endfacet
  facet normal -0.802468 -0.042069 0.595210
    outer loop
      vertex -35.238998 -61.921001 2.948000
      vertex -35.292000 -63.103001 2.793000
      vertex -35.158001 -61.938000 3.056000
    endloop
  endfacet
  facet normal -0.802957 -0.129221 0.581860
    outer loop
      vertex -35.188000 -60.806000 3.266000
      vertex -35.238998 -61.921001 2.948000
      vertex -35.158001 -61.938000 3.056000
    endloop
  endfacet
  facet normal 0.525255 0.689225 0.499076
    outer loop
      vertex -87.999001 -54.402000 5.500000
      vertex -86.974998 -54.459000 4.501000
      vertex -87.719002 -53.891998 4.501000
    endloop
  endfacet
  facet normal -0.762595 -0.144921 0.630434
    outer loop
      vertex -35.238998 -61.921001 2.948000
      vertex -35.188000 -60.806000 3.266000
      vertex -35.284000 -60.775002 3.157000
    endloop
  endfacet
  facet normal -0.530633 -0.172194 0.829926
    outer loop
      vertex -35.284000 -60.775002 3.157000
      vertex -35.682999 -60.707001 2.916000
      vertex -35.238998 -61.921001 2.948000
    endloop
  endfacet
  facet normal 0.276485 0.673688 0.685347
    outer loop
      vertex -87.719002 -53.891998 4.501000
      vertex -87.322998 -53.201000 3.662000
      vertex -88.584000 -53.536999 4.501000
    endloop
  endfacet
  facet normal -0.128864 -0.140633 0.981640
    outer loop
      vertex -36.000000 -63.103001 2.500000
      vertex -35.741001 -63.103001 2.534000
      vertex -36.209000 -61.327000 2.727000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.239998 -56.034000 5.500000
      vertex -87.999001 -54.402000 5.500000
      vertex -88.723000 -54.102001 5.500000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -89.239998 -56.034000 5.500000
      vertex -88.723000 -54.102001 5.500000
      vertex -89.499001 -54.000000 5.500000
    endloop
  endfacet
  facet normal 0.331291 0.799517 0.501018
    outer loop
      vertex -87.999001 -54.402000 5.500000
      vertex -87.719002 -53.891998 4.501000
      vertex -88.723000 -54.102001 5.500000
    endloop
  endfacet
  facet normal -0.349312 -0.217825 0.911336
    outer loop
      vertex -35.825001 -60.696999 2.881000
      vertex -35.708000 -61.872002 2.645000
      vertex -35.583000 -61.880001 2.691000
    endloop
  endfacet
  facet normal -0.601618 -0.199645 0.773433
    outer loop
      vertex -35.583000 -61.880001 2.691000
      vertex -35.238998 -61.921001 2.948000
      vertex -35.682999 -60.707001 2.916000
    endloop
  endfacet
  facet normal -0.247783 -0.202839 0.947344
    outer loop
      vertex -35.825001 -60.696999 2.881000
      vertex -35.583000 -61.880001 2.691000
      vertex -35.682999 -60.707001 2.916000
    endloop
  endfacet
  facet normal 0.328993 0.801630 0.499152
    outer loop
      vertex -87.719002 -53.891998 4.501000
      vertex -88.584000 -53.536999 4.501000
      vertex -88.723000 -54.102001 5.500000
    endloop
  endfacet
  facet normal 0.063329 -0.091310 0.993807
    outer loop
      vertex -35.708000 -61.872002 2.645000
      vertex -36.209000 -61.327000 2.727000
      vertex -35.741001 -63.103001 2.534000
    endloop
  endfacet
  facet normal 0.050483 -0.127976 0.990492
    outer loop
      vertex -36.000000 -63.103001 2.500000
      vertex -37.283001 -62.571999 2.634000
      vertex -39.619999 -64.530998 2.500000
    endloop
  endfacet
  facet normal 0.092383 0.722516 0.685154
    outer loop
      vertex -89.511002 -53.417999 4.501000
      vertex -88.379997 -52.766998 3.662000
      vertex -89.514000 -52.622002 3.662000
    endloop
  endfacet
  facet normal 0.092715 0.722247 0.685393
    outer loop
      vertex -89.511002 -53.417999 4.501000
      vertex -88.584000 -53.536999 4.501000
      vertex -88.379997 -52.766998 3.662000
    endloop
  endfacet
  facet normal 0.112789 0.858071 0.500991
    outer loop
      vertex -88.723000 -54.102001 5.500000
      vertex -88.584000 -53.536999 4.501000
      vertex -89.499001 -54.000000 5.500000
    endloop
  endfacet
  facet normal -0.922998 -0.037426 0.382981
    outer loop
      vertex -35.158001 -61.938000 3.056000
      vertex -35.133999 -63.103001 3.000000
      vertex -35.034000 -63.103001 3.241000
    endloop
  endfacet
  facet normal -0.794078 -0.045495 0.606111
    outer loop
      vertex -35.158001 -61.938000 3.056000
      vertex -35.292000 -63.103001 2.793000
      vertex -35.133999 -63.103001 3.000000
    endloop
  endfacet
  facet normal 0.110317 0.859363 0.499325
    outer loop
      vertex -89.499001 -54.000000 5.500000
      vertex -88.584000 -53.536999 4.501000
      vertex -89.511002 -53.417999 4.501000
    endloop
  endfacet
  facet normal -0.605457 -0.078005 0.792046
    outer loop
      vertex -35.583000 -61.880001 2.691000
      vertex -35.500000 -63.103001 2.634000
      vertex -35.292000 -63.103001 2.793000
    endloop
  endfacet
  facet normal -0.097347 0.721930 0.685085
    outer loop
      vertex -90.438004 -53.542999 4.501000
      vertex -89.511002 -53.417999 4.501000
      vertex -90.647003 -52.775002 3.662000
    endloop
  endfacet
  facet normal -0.602607 -0.077138 0.794301
    outer loop
      vertex -35.583000 -61.880001 2.691000
      vertex -35.292000 -63.103001 2.793000
      vertex -35.238998 -61.921001 2.948000
    endloop
  endfacet
  facet normal -0.112631 0.857974 0.501194
    outer loop
      vertex -89.499001 -54.000000 5.500000
      vertex -89.511002 -53.417999 4.501000
      vertex -90.276001 -54.102001 5.500000
    endloop
  endfacet
  facet normal -0.115787 0.858680 0.499261
    outer loop
      vertex -90.276001 -54.102001 5.500000
      vertex -89.511002 -53.417999 4.501000
      vertex -90.438004 -53.542999 4.501000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 -54.000000 5.500000
      vertex -89.499001 -56.000000 5.500000
      vertex -89.239998 -56.034000 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -87.999001 -54.402000 5.500000
      vertex -89.239998 -56.034000 5.500000
      vertex -88.999001 -56.133999 5.500000
    endloop
  endfacet
  facet normal 0.000000 0.000000 1.000000
    outer loop
      vertex -89.499001 -54.000000 5.500000
      vertex -90.276001 -54.102001 5.500000
      vertex -89.758003 -56.034000 5.500000
    endloop
  endfacet
  facet normal -0.348605 -0.074898 0.934272
    outer loop
      vertex -35.741001 -63.103001 2.534000
      vertex -35.583000 -61.880001 2.691000
      vertex -35.708000 -61.872002 2.645000
    endloop
  endfacet
  facet normal 0.858026 -0.112779 0.501070
    outer loop
      vertex -86.036003 -57.916000 4.501000
      vertex -86.499001 -57.000000 5.500000
      vertex -86.600998 -57.776001 5.500000
    endloop
  endfacet
  facet normal -0.382343 -0.068894 0.921449
    outer loop
      vertex -35.741001 -63.103001 2.534000
      vertex -35.500000 -63.103001 2.634000
      vertex -35.583000 -61.880001 2.691000
    endloop
  endfacet
  facet normal 0.859373 -0.110203 0.499333
    outer loop
      vertex -86.036003 -57.916000 4.501000
      vertex -85.917000 -56.987999 4.501000
      vertex -86.499001 -57.000000 5.500000
    endloop
  endfacet
  facet normal -1.000000 0.000000 0.000000
    outer loop
      vertex -35.000000 -63.103001 3.500000
      vertex -35.000000 -82.000000 3.500000
      vertex -35.000000 -65.536003 10.500000
    endloop
  endfacet
  facet normal -0.991493 0.000000 0.130159
    outer loop
      vertex -35.000000 -82.000000 3.500000
      vertex -35.000000 -63.103001 3.500000
      vertex -35.034000 -63.103001 3.241000
    endloop
  endfacet
  facet normal -0.991493 0.000000 0.130159
    outer loop
      vertex -35.034000 -63.103001 3.241000
      vertex -35.034000 -82.000000 3.241000
      vertex -35.000000 -82.000000 3.500000
    endloop
  endfacet
  facet normal -0.923645 0.000000 0.383249
    outer loop
      vertex -35.034000 -63.103001 3.241000
      vertex -35.133999 -63.103001 3.000000
      vertex -35.133999 -82.000000 3.000000
    endloop
  endfacet
  facet normal -0.923645 0.000000 0.383249
    outer loop
      vertex -35.034000 -63.103001 3.241000
      vertex -35.133999 -82.000000 3.000000
      vertex -35.034000 -82.000000 3.241000
    endloop
  endfacet
  facet normal 0.857959 0.112770 0.501187
    outer loop
      vertex -86.499001 -57.000000 5.500000
      vertex -85.917000 -56.987999 4.501000
      vertex -86.600998 -56.223999 5.500000
    endloop
  endfacet
  facet normal -0.794901 0.000000 0.606739
    outer loop
      vertex -35.292000 -63.103001 2.793000
      vertex -35.133999 -82.000000 3.000000
      vertex -35.133999 -63.103001 3.000000
    endloop
  endfacet
  facet normal -0.607308 0.000000 0.794467
    outer loop
      vertex -35.500000 -63.103001 2.634000
      vertex -35.500000 -82.000000 2.634000
      vertex -35.292000 -63.103001 2.793000
    endloop
  endfacet
  facet normal 0.721943 0.097577 0.685038
    outer loop
      vertex -85.274002 -55.853001 3.662000
      vertex -86.042000 -56.061001 4.501000
      vertex -85.121002 -56.985001 3.662000
    endloop
  endfacet
  facet normal 0.721835 0.097335 0.685186
    outer loop
      vertex -85.121002 -56.985001 3.662000
      vertex -86.042000 -56.061001 4.501000
      vertex -85.917000 -56.987999 4.501000
    endloop
  endfacet
  facet normal -0.383253 0.000000 0.923643
    outer loop
      vertex -35.500000 -63.103001 2.634000
      vertex -35.741001 -82.000000 2.534000
      vertex -35.500000 -82.000000 2.634000
    endloop
  endfacet
  facet normal -0.383253 0.000000 0.923643
    outer loop
      vertex -35.741001 -63.103001 2.534000
      vertex -35.741001 -82.000000 2.534000
      vertex -35.500000 -63.103001 2.634000
    endloop
  endfacet
  facet normal -0.130158 0.000000 0.991493
    outer loop
      vertex -35.741001 -63.103001 2.534000
      vertex -36.000000 -63.103001 2.500000
      vertex -36.000000 -82.000000 2.500000
    endloop
  endfacet
  facet normal -0.130158 0.000000 0.991493
    outer loop
      vertex -36.000000 -82.000000 2.500000
      vertex -35.741001 -82.000000 2.534000
      vertex -35.741001 -63.103001 2.534000
    endloop
  endfacet
  facet normal 0.858632 0.115781 0.499345
    outer loop
      vertex -86.600998 -56.223999 5.500000
      vertex -85.917000 -56.987999 4.501000
      vertex -86.042000 -56.061001 4.501000
    endloop
  endfacet
  facet normal 0.000000 -0.000000 1.000000
    outer loop
      vertex -36.000000 -82.000000 2.500000
      vertex -36.000000 -63.103001 2.500000
      vertex -39.619999 -64.530998 2.500000
    endloop
  endfacet
  facet normal 0.335760 -0.437276 0.834299
    outer loop
      vertex -37.826000 -61.630001 3.028000
      vertex -36.719002 -60.779999 3.028000
      vertex -38.310001 -60.792000 3.662000
    endloop
  endfacet
  facet normal 0.224014 -0.263339 0.938334
    outer loop
      vertex -37.283001 -62.571999 2.634000
      vertex -36.209000 -61.327000 2.727000
      vertex -37.826000 -61.630001 3.028000
    endloop
  endfacet
  facet normal -0.044944 -0.340150 0.939296
    outer loop
      vertex -40.500000 -62.346001 3.028000
      vertex -42.165001 -63.214001 2.634000
      vertex -40.500000 -63.433998 2.634000
    endloop
  endfacet
  facet normal 0.014496 -0.109772 0.993851
    outer loop
      vertex -40.500000 -63.433998 2.634000
      vertex -39.619999 -64.530998 2.500000
      vertex -38.834000 -63.214001 2.634000
    endloop
  endfacet
  facet normal -0.071916 -0.546481 0.834378
    outer loop
      vertex -40.500000 -62.346001 3.028000
      vertex -40.500000 -61.377998 3.662000
      vertex -41.882999 -62.164001 3.028000
    endloop
  endfacet
  facet normal 0.055345 -0.133706 0.989474
    outer loop
      vertex -39.619999 -64.530998 2.500000
      vertex -37.283001 -62.571999 2.634000
      vertex -38.834000 -63.214001 2.634000
    endloop
  endfacet
  facet normal 0.071864 -0.546483 0.834381
    outer loop
      vertex -40.500000 -62.346001 3.028000
      vertex -39.116001 -62.164001 3.028000
      vertex -40.500000 -61.377998 3.662000
    endloop
  endfacet
  facet normal -0.071873 -0.546532 0.834348
    outer loop
      vertex -41.632999 -61.229000 3.662000
      vertex -41.882999 -62.164001 3.028000
      vertex -40.500000 -61.377998 3.662000
    endloop
  endfacet
  facet normal 0.044764 -0.340406 0.939212
    outer loop
      vertex -40.500000 -62.346001 3.028000
      vertex -38.834000 -63.214001 2.634000
      vertex -39.116001 -62.164001 3.028000
    endloop
  endfacet
  facet normal 0.131288 -0.317177 0.939235
    outer loop
      vertex -38.834000 -63.214001 2.634000
      vertex -37.283001 -62.571999 2.634000
      vertex -39.116001 -62.164001 3.028000
    endloop
  endfacet
  facet normal 0.131292 -0.317165 0.939238
    outer loop
      vertex -39.116001 -62.164001 3.028000
      vertex -37.283001 -62.571999 2.634000
      vertex -37.826000 -61.630001 3.028000
    endloop
  endfacet
endsolid Mesh
```