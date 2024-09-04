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
solid 
  facet normal 0 -1 0
    outer loop
      vertex 25 -84 0
      vertex 82.99800109863281 -84 0
      vertex 82.99800109863281 -84 10.5
    endloop
  endfacet
  facet normal 0.799350917339325 0.3312227725982666 0.5013278126716614
    outer loop
      vertex -86.04199981689453 -56.06100082397461 4.500999927520752
      vertex -86.9010009765625 -55.5 5.5
      vertex -86.60099792480469 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 82.99800109863281 -84 10.5
      vertex 25 -84 10.5
      vertex 25 -84 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -33 -84 10.5
      vertex -33 -84 3.5
      vertex 23 -84 10.5
    endloop
  endfacet
  facet normal -0.9156829118728638 -0.3799514174461365 0.13100256025791168
    outer loop
      vertex -49.8650016784668 16.5 3.5
      vertex -49.96500015258789 16.740999221801758 3.5
      vertex -49.89500045776367 16.482999801635742 3.240999937057495
    endloop
  endfacet
  facet normal 0 0.6091551780700684 0.7930510640144348
    outer loop
      vertex -80.9990005493164 18.5 2.634000062942505
      vertex -92.9990005493164 18.5 2.634000062942505
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 -56 5.5
      vertex -89.4990005493164 -54 5.5
      vertex -89.75800323486328 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -49.96500015258789 16.740999221801758 10.5
      vertex -49.999000549316406 17 10.5
      vertex -49.96500015258789 16.740999221801758 3.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.9990005493164 -56.13399887084961 5.5
      vertex -88.79199981689453 -56.292999267578125 5.5
      vertex -87.37799835205078 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.79199981689453 -56.292999267578125 5.5
      vertex -88.63300323486328 -56.5 5.5
      vertex -87.37799835205078 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.37799835205078 -54.87900161743164 5.5
      vertex -87.9990005493164 -54.402000427246094 5.5
      vertex -88.9990005493164 -56.13399887084961 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.9010009765625 -55.5 5.5
      vertex -87.37799835205078 -54.87900161743164 5.5
      vertex -88.63300323486328 -56.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.63300323486328 -56.5 5.5
      vertex -88.53299713134766 -56.74100112915039 5.5
      vertex -86.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -34.05799865722656 -84 2.8259999752044678
      vertex 23 -84 0
      vertex -33 -84 3.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 23 -84 0
      vertex 23 -84 10.5
      vertex -33 -84 3.5
    endloop
  endfacet
  facet normal -0.982714056968689 -0.13200636208057404 0.12979775667190552
    outer loop
      vertex -49.96500015258789 16.740999221801758 3.5
      vertex -50.034000396728516 17 3.240999937057495
      vertex -49.99800109863281 16.73200035095215 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.4990005493164 -57 5.5
      vertex -86.4990005493164 -57 5.5
      vertex -88.53299713134766 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.9162313342094421 -0.3790033161640167 0.12990990281105042
    outer loop
      vertex -49.89500045776367 16.482999801635742 3.240999937057495
      vertex -49.96500015258789 16.740999221801758 3.5
      vertex -49.99800109863281 16.73200035095215 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.60099792480469 -56.2239990234375 5.5
      vertex -88.53299713134766 -56.74100112915039 5.5
      vertex -86.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.60099792480469 -56.2239990234375 5.5
      vertex -86.9010009765625 -55.5 5.5
      vertex -88.53299713134766 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.4990005493164 -57 5.5
      vertex -88.53299713134766 -57.25899887084961 5.5
      vertex -86.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal 0.15638668835163116 0.10977073758840561 0.9815770983695984
    outer loop
      vertex -36.22200012207031 1.5729999542236328 3.9200000762939453
      vertex -36.249000549316406 1.065999984741211 3.9809999465942383
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -89.9990005493164 -56.13399887084961 5.5
      vertex -89.75800323486328 -56.034000396728516 0
      vertex -89.75800323486328 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal 0.7342099547386169 -0.30279460549354553 0.6076604127883911
    outer loop
      vertex -79.90399932861328 16.707000732421875 3
      vertex -80.01699829101562 16.433000564575195 3
      vertex -79.75 16.665000915527344 2.7929999828338623
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.75800323486328 -56.034000396728516 5.5
      vertex -89.75800323486328 -56.034000396728516 0
      vertex -89.4990005493164 -56 5.5
    endloop
  endfacet
  facet normal -0.982711672782898 -0.12900462746620178 0.13279888033866882
    outer loop
      vertex -50.034000396728516 17 3.240999937057495
      vertex -49.96500015258789 16.740999221801758 3.5
      vertex -49.999000549316406 17 3.5
    endloop
  endfacet
  facet normal 0.13467828929424286 0.10308811813592911 0.985512375831604
    outer loop
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
      vertex -36.0359992980957 1.569000005722046 3.8949999809265137
      vertex -36.22200012207031 1.5729999542236328 3.9200000762939453
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -88.63300323486328 -56.5 5.5
      vertex -88.53299713134766 -56.74100112915039 0
      vertex -88.53299713134766 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -88.53299713134766 -56.74100112915039 5.5
      vertex -88.53299713134766 -56.74100112915039 0
      vertex -88.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal -0.8541223406791687 -0.3533116579055786 0.38163578510284424
    outer loop
      vertex -49.981998443603516 16.433000564575195 3
      vertex -49.89500045776367 16.482999801635742 3.240999937057495
      vertex -49.99800109863281 16.73200035095215 3.240999937057495
    endloop
  endfacet
  facet normal 0 0.9236428737640381 0.3832542896270752
    outer loop
      vertex -92.9990005493164 18.034000396728516 3.240999937057495
      vertex -80.9990005493164 18.034000396728516 3.240999937057495
      vertex -92.9990005493164 18.134000778198242 3
    endloop
  endfacet
  facet normal 0 0.7930510640144348 0.6091551780700684
    outer loop
      vertex -92.9990005493164 18.134000778198242 3
      vertex -80.9990005493164 18.134000778198242 3
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal -0.982711672782898 0.12900462746620178 0.13279888033866882
    outer loop
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -50.034000396728516 17 3.240999937057495
      vertex -49.999000549316406 17 3.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -49.96500015258789 17.259000778198242 10.5
      vertex -49.8650016784668 17.5 10.5
      vertex -49.96500015258789 17.259000778198242 3.5
    endloop
  endfacet
  facet normal -0.9179369211196899 -0.12330496311187744 0.3770778179168701
    outer loop
      vertex -49.99800109863281 16.73200035095215 3.240999937057495
      vertex -50.034000396728516 17 3.240999937057495
      vertex -50.132999420166016 17 3
    endloop
  endfacet
  facet normal -0.982714056968689 0.13200636208057404 0.12979775667190552
    outer loop
      vertex -50.034000396728516 17 3.240999937057495
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -49.99800109863281 17.26799964904785 3.240999937057495
    endloop
  endfacet
  facet normal -0.44520196318626404 0.5759605765342712 0.6856125593185425
    outer loop
      vertex -91.3010025024414 4.0960001945495605 4.500999927520752
      vertex -92.60600280761719 4.085999965667725 3.6619999408721924
      vertex -92.04100036621094 3.5239999294281006 4.500999927520752
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 18.034000396728516 3.240999937057495
      vertex -92.9990005493164 18.134000778198242 3
      vertex -92.9990005493164 18 3.5
    endloop
  endfacet
  facet normal -0.5270562767982483 0.6861675977706909 0.5013838410377502
    outer loop
      vertex -91.3010025024414 4.0960001945495605 4.500999927520752
      vertex -91.62000274658203 3.121000051498413 5.5
      vertex -90.9990005493164 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -94.41300201416016 16.586000442504883 10.5
      vertex -94.73100280761719 17 10.5
      vertex -94.41300201416016 16.586000442504883 3.5
    endloop
  endfacet
  facet normal -0.5297383069992065 0.6853258013725281 0.49970582127571106
    outer loop
      vertex -91.3010025024414 4.0960001945495605 4.500999927520752
      vertex -92.04100036621094 3.5239999294281006 4.500999927520752
      vertex -91.62000274658203 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.9167643785476685 -0.11889776587486267 0.3813219368457794
    outer loop
      vertex -49.99800109863281 16.73200035095215 3.240999937057495
      vertex -50.132999420166016 17 3
      vertex -50.095001220703125 16.707000732421875 3
    endloop
  endfacet
  facet normal -0.6860305666923523 0.526951014995575 0.5016818046569824
    outer loop
      vertex -92.04100036621094 3.5239999294281006 4.500999927520752
      vertex -92.09700012207031 2.5 5.5
      vertex -91.62000274658203 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.6891447901725769 0.5249743461608887 0.49948111176490784
    outer loop
      vertex -92.04100036621094 3.5239999294281006 4.500999927520752
      vertex -92.60700225830078 2.7809998989105225 4.500999927520752
      vertex -92.09700012207031 2.5 5.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -34.62099838256836 -84 2.5969998836517334
      vertex 23 -84 0
      vertex -34.05799865722656 -84 2.8259999752044678
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -34.930999755859375 -84 2.5260000228881836
      vertex 23 -84 0
      vertex -34.62099838256836 -84 2.5969998836517334
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 18.292999267578125 2.7929999828338623
      vertex -92.9990005493164 18.5 2.634000062942505
      vertex -92.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 18.134000778198242 3
      vertex -92.9990005493164 18.292999267578125 2.7929999828338623
      vertex -92.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 18.5 2.634000062942505
      vertex -92.9990005493164 18.740999221801758 2.5339999198913574
      vertex -92.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 18.740999221801758 2.5339999198913574
      vertex -92.9990005493164 19 2.5
      vertex -92.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 19 2.5
      vertex -92.9990005493164 83 10.5
      vertex -92.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -34.930999755859375 -84 2.5260000228881836
      vertex -35.236000061035156 -84 2.5
      vertex 23 -84 0
    endloop
  endfacet
  facet normal 0 0.7930510640144348 0.6091551780700684
    outer loop
      vertex -92.9990005493164 18.292999267578125 2.7929999828338623
      vertex -92.9990005493164 18.134000778198242 3
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -92.9990005493164 -84 2.5
      vertex -92.9990005493164 -84 0
      vertex -35.236000061035156 -84 2.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -92.9990005493164 -84 0
      vertex 23 -84 0
      vertex -35.236000061035156 -84 2.5
    endloop
  endfacet
  facet normal 0 0.6091551780700684 0.7930510640144348
    outer loop
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
      vertex -92.9990005493164 18.5 2.634000062942505
      vertex -92.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0.13015742599964142 0.9914933443069458
    outer loop
      vertex -80.9990005493164 19 2.5
      vertex -92.9990005493164 19 2.5
      vertex -92.9990005493164 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -91.62000274658203 3.121000051498413 5.5
      vertex -92.09700012207031 2.5 5.5
      vertex -90.36499786376953 1.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.46499633789062 1.2589999437332153 5.5
      vertex -90.36499786376953 1.5 5.5
      vertex -92.09700012207031 2.5 5.5
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -93.9990005493164 16.26799964904785 3.5
      vertex -94.41300201416016 16.586000442504883 10.5
      vertex -94.41300201416016 16.586000442504883 3.5
    endloop
  endfacet
  facet normal -0.6040772199630737 -0.7864401340484619 0.1288510262966156
    outer loop
      vertex -94.41300201416016 16.586000442504883 3.5
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
      vertex -93.9990005493164 16.26799964904785 3.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.9990005493164 3.5980000495910645 5.5
      vertex -91.62000274658203 3.121000051498413 5.5
      vertex -89.9990005493164 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.36499786376953 1.5 5.5
      vertex -90.20600128173828 1.7070000171661377 5.5
      vertex -91.62000274658203 3.121000051498413 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.20600128173828 1.7070000171661377 5.5
      vertex -89.9990005493164 1.8660000562667847 5.5
      vertex -91.62000274658203 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -94.73100280761719 17 3.5
      vertex -94.41300201416016 16.586000442504883 3.5
      vertex -94.73100280761719 17 10.5
    endloop
  endfacet
  facet normal 0.538995623588562 -0.05798742547631264 0.8403101563453674
    outer loop
      vertex -36.249000549316406 1.065999984741211 3.9809999465942383
      vertex -36.762001037597656 0.6740000247955322 4.2829999923706055
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
    endloop
  endfacet
  facet normal -0.9255057573318481 0.1079753041267395 0.36301568150520325
    outer loop
      vertex -35.018001556396484 -52.26100158691406 3.444999933242798
      vertex -35.16400146484375 -52.32899856567383 3.0929999351501465
      vertex -35.20399856567383 -53.70399856567383 3.4000000953674316
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 82.99800109863281 85 0
      vertex -39.534000396728516 1.2589999437332153 0
      vertex 25 85 0
    endloop
  endfacet
  facet normal -0.9258143901824951 0.04526370391249657 0.3752584457397461
    outer loop
      vertex -35.034000396728516 -50.89699935913086 3.240999937057495
      vertex -35.16400146484375 -52.32899856567383 3.0929999351501465
      vertex -35.018001556396484 -52.26100158691406 3.444999933242798
    endloop
  endfacet
  facet normal 0.15570195019245148 -0.08816996216773987 0.9838612675666809
    outer loop
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
      vertex -36.249000549316406 1.065999984741211 3.9809999465942383
    endloop
  endfacet
  facet normal -0.26577356457710266 -0.09418291598558426 0.9594237804412842
    outer loop
      vertex -35.45500183105469 0.40700000524520874 4.053999900817871
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
      vertex -36.0359992980957 0.43700000643730164 3.8959999084472656
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 24 84.73200225830078 0
      vertex -39.79199981689453 1.7070000171661377 0
      vertex 23.51799964904785 84.93199920654297 0
    endloop
  endfacet
  facet normal 0.12927058339118958 -0.08160987496376038 0.9882453680038452
    outer loop
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
      vertex -36.0359992980957 0.43700000643730164 3.8959999084472656
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
    endloop
  endfacet
  facet normal -0.7858762741088867 -0.6048073768615723 0.12886643409729004
    outer loop
      vertex -94.41300201416016 16.586000442504883 3.5
      vertex -94.76100158691406 16.982999801635742 3.240999937057495
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
    endloop
  endfacet
  facet normal -0.7862470746040344 -0.6039289236068726 0.13071121275424957
    outer loop
      vertex -94.73100280761719 17 3.5
      vertex -94.76100158691406 16.982999801635742 3.240999937057495
      vertex -94.41300201416016 16.586000442504883 3.5
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -94.93099975585938 17.48200035095215 3.5
      vertex -94.73100280761719 17 3.5
      vertex -94.93099975585938 17.48200035095215 10.5
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -94.73100280761719 17 3.5
      vertex -94.73100280761719 17 10.5
      vertex -94.93099975585938 17.48200035095215 10.5
    endloop
  endfacet
  facet normal -0.915991485118866 -0.380079448223114 0.1284492462873459
    outer loop
      vertex -94.73100280761719 17 3.5
      vertex -94.93099975585938 17.48200035095215 3.5
      vertex -94.96399688720703 17.474000930786133 3.240999937057495
    endloop
  endfacet
  facet normal -0.9161697626113892 -0.3787830173969269 0.13098226487636566
    outer loop
      vertex -94.73100280761719 17 3.5
      vertex -94.96399688720703 17.474000930786133 3.240999937057495
      vertex -94.76100158691406 16.982999801635742 3.240999937057495
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -94.9990005493164 18 3.5
      vertex -94.93099975585938 17.48200035095215 10.5
      vertex -94.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 25 85 0
      vertex -39.534000396728516 1.2589999437332153 0
      vertex 24.48200035095215 84.93199920654297 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40 1.8660000562667847 0
      vertex 23 85 0
      vertex -39.79199981689453 1.7070000171661377 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 24 84.73200225830078 0
      vertex 24.48200035095215 84.93199920654297 0
      vertex -39.534000396728516 1.2589999437332153 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.24100112915039 1.965999960899353 0
      vertex 23 85 0
      vertex -40 1.8660000562667847 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.5 2 0
      vertex 23 85 0
      vertex -40.24100112915039 1.965999960899353 0
    endloop
  endfacet
  facet normal -0.9162313342094421 0.3790033161640167 0.12990990281105042
    outer loop
      vertex -49.99800109863281 17.26799964904785 3.240999937057495
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -49.89500045776367 17.517000198364258 3.240999937057495
    endloop
  endfacet
  facet normal -0.8541223406791687 0.3533116579055786 0.38163578510284424
    outer loop
      vertex -49.99800109863281 17.26799964904785 3.240999937057495
      vertex -49.89500045776367 17.517000198364258 3.240999937057495
      vertex -49.981998443603516 17.566999435424805 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -86.01599884033203 0 0
      vertex 23 85 0
      vertex -41 1.8660000562667847 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.757999420166016 1.965999960899353 0
      vertex 23 85 0
      vertex -40.5 2 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.79199981689453 1.7070000171661377 0
      vertex 24 84.73200225830078 0
      vertex -39.63399887084961 1.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.63399887084961 1.5 0
      vertex 24 84.73200225830078 0
      vertex -39.534000396728516 1.2589999437332153 0
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -94.93099975585938 17.48200035095215 3.5
      vertex -94.93099975585938 17.48200035095215 10.5
      vertex -94.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.79199981689453 0.2930000126361847 0
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -40 0.1340000033378601 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.24100112915039 0.03400000184774399 0
      vertex -40 0.1340000033378601 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal -0.9831759333610535 -0.12906557321548462 0.12925609946250916
    outer loop
      vertex -94.93099975585938 17.48200035095215 3.5
      vertex -94.9990005493164 18 3.5
      vertex -94.96399688720703 17.474000930786133 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.534000396728516 1.2589999437332153 0
      vertex 82.99800109863281 85 0
      vertex -39.5 1 0
    endloop
  endfacet
  facet normal -0.353948712348938 0.8551150560379028 0.3788120746612549
    outer loop
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
      vertex -49.292999267578125 18.094999313354492 3
      vertex -49.566001892089844 17.98200035095215 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.5 1 0
      vertex 82.99800109863281 85 0
      vertex -39.534000396728516 0.7409999966621399 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.63399887084961 0.5 0
      vertex -39.534000396728516 0.7409999966621399 0
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41 1.8660000562667847 0
      vertex 23 85 0
      vertex -40.757999420166016 1.965999960899353 0
    endloop
  endfacet
  facet normal -0.7334200143814087 -0.564437210559845 0.3788214921951294
    outer loop
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
      vertex -94.76100158691406 16.982999801635742 3.240999937057495
      vertex -94.84700012207031 16.933000564575195 3
    endloop
  endfacet
  facet normal -0.3039374053478241 0.7342912554740906 0.6069912314414978
    outer loop
      vertex -49.566001892089844 17.98200035095215 3
      vertex -49.292999267578125 18.094999313354492 3
      vertex -49.645999908447266 18.1200008392334 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41 0.1340000033378601 0
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -41.207000732421875 0.2930000126361847 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -86.01599884033203 0 0
      vertex -41.207000732421875 0.2930000126361847 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.46500015258789 0.7409999966621399 0
      vertex -41.36600112915039 0.5 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.5 1 0
      vertex -41.46500015258789 0.7409999966621399 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -86.01599884033203 0 0
      vertex -41.46500015258789 1.2589999437332153 0
      vertex -41.5 1 0
    endloop
  endfacet
  facet normal -0.7333889007568359 -0.5624860525131226 0.38177230954170227
    outer loop
      vertex -94.50800323486328 16.490999221801758 3
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
      vertex -94.84700012207031 16.933000564575195 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.46500015258789 1.2589999437332153 0
      vertex -86.01599884033203 0 0
      vertex -41.36600112915039 1.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.207000732421875 1.7070000171661377 0
      vertex -86.01599884033203 0 0
      vertex -41 1.8660000562667847 0
    endloop
  endfacet
  facet normal -0.6316993832588196 -0.4854111075401306 0.604426920413971
    outer loop
      vertex -94.62000274658203 16.378999710083008 2.7929999828338623
      vertex -94.50800323486328 16.490999221801758 3
      vertex -94.98500061035156 16.854000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.207000732421875 1.7070000171661377 0
      vertex -41.36600112915039 1.5 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 23.51799964904785 84.93199920654297 0
      vertex -39.79199981689453 1.7070000171661377 0
      vertex 23 85 0
    endloop
  endfacet
  facet normal -0.8036476969718933 -0.33226168155670166 0.49371299147605896
    outer loop
      vertex -94.76100158691406 16.982999801635742 3.240999937057495
      vertex -94.96399688720703 17.474000930786133 3.240999937057495
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.93099975585938 83.51799774169922 0
      vertex -94.73100280761719 84 0
      vertex -94.9990005493164 83 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 83 0
      vertex -94.73100280761719 84 0
      vertex -94.41300201416016 84.41400146484375 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 83 0
      vertex -94.41300201416016 84.41400146484375 0
      vertex -93.9990005493164 84.73200225830078 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 83 0
      vertex -93.9990005493164 84.73200225830078 0
      vertex -93.51699829101562 84.93199920654297 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -93.51699829101562 84.93199920654297 0
      vertex -92.9990005493164 85 0
      vertex -94.9990005493164 83 0
    endloop
  endfacet
  facet normal -0.6313655376434326 -0.48423734307289124 0.6057159304618835
    outer loop
      vertex -94.84700012207031 16.933000564575195 3
      vertex -94.98500061035156 16.854000091552734 2.7929999828338623
      vertex -94.50800323486328 16.490999221801758 3
    endloop
  endfacet
  facet normal 0.06740178167819977 0.08854353427886963 0.9937892556190491
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -86.3010025024414 -51.417999267578125 2.634000062942505
      vertex -84.96499633789062 -52.435001373291016 2.634000062942505
    endloop
  endfacet
  facet normal -0.42379462718963623 -0.8448598384857178 0.3265117406845093
    outer loop
      vertex -94.84700012207031 16.933000564575195 3
      vertex -94.76100158691406 16.982999801635742 3.240999937057495
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
    endloop
  endfacet
  facet normal -0.7163893580436707 -0.3420163691043854 0.6081209182739258
    outer loop
      vertex -94.84700012207031 16.933000564575195 3
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
      vertex -94.98500061035156 16.854000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal 0.06254056096076965 0.118898406624794 0.9909348487854004
    outer loop
      vertex -87.15499877929688 -49.85200119018555 2.5
      vertex -86.3010025024414 -51.417999267578125 2.634000062942505
      vertex -84.65499877929688 -51.16699981689453 2.5
    endloop
  endfacet
  facet normal -0.8779162168502808 -0.2572612166404724 0.403831422328949
    outer loop
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
      vertex -94.96399688720703 17.474000930786133 3.240999937057495
      vertex -94.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 16.384000778198242 0
      vertex -94.9990005493164 83 0
      vertex -92.9990005493164 85 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 18 3.5
      vertex -94.9990005493164 83 10.5
      vertex -94.9990005493164 83 0
    endloop
  endfacet
  facet normal -0.794902503490448 0.6067371964454651 0
    outer loop
      vertex -39.63399887084961 0.5 5.5
      vertex -39.63399887084961 0.5 0
      vertex -39.79199981689453 0.2930000126361847 0
    endloop
  endfacet
  facet normal 0.04494661092758179 0.10947810858488083 0.9929724931716919
    outer loop
      vertex -87.15499877929688 -49.85200119018555 2.5
      vertex -87.8550033569336 -50.779998779296875 2.634000062942505
      vertex -86.3010025024414 -51.417999267578125 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 16.384000778198242 0
      vertex 23 85 0
      vertex -89.23999786376953 1.965999960899353 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.9990005493164 1.8660000562667847 0
      vertex -89.23999786376953 1.965999960899353 0
      vertex 23 85 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 83 0
      vertex -94.9990005493164 16.384000778198242 0
      vertex -94.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 0.016762539744377136 0.13049715757369995 0.9913069605827332
    outer loop
      vertex -87.15499877929688 -49.85200119018555 2.5
      vertex -89.52100372314453 -50.566001892089844 2.634000062942505
      vertex -87.8550033569336 -50.779998779296875 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.9990005493164 1.8660000562667847 0
      vertex -94.9990005493164 16.384000778198242 0
      vertex -89.75800323486328 1.965999960899353 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.4990005493164 2 0
      vertex -94.9990005493164 16.384000778198242 0
      vertex -89.23999786376953 1.965999960899353 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.75800323486328 1.965999960899353 0
      vertex -94.9990005493164 16.384000778198242 0
      vertex -89.4990005493164 2 0
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -39.534000396728516 1.2589999437332153 0
      vertex -39.5 1 0
      vertex -39.5 1 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
      vertex -94.9990005493164 18 3.5
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -39.5 1 5.5
      vertex -39.5 1 0
      vertex -39.534000396728516 0.7409999966621399 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.79199981689453 1.7070000171661377 0
      vertex -88.9990005493164 1.8660000562667847 0
      vertex 23 85 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.79199981689453 1.7070000171661377 0
      vertex 23 85 0
      vertex -88.63300323486328 1.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.63300323486328 1.5 0
      vertex 23 85 0
      vertex -88.53299713134766 1.2589999437332153 0
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -40.24100112915039 1.965999960899353 0
      vertex -40 1.8660000562667847 0
      vertex -40 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -80.9990005493164 16 10.5
      vertex -80.73999786376953 16.034000396728516 3.5
      vertex -80.73999786376953 16.034000396728516 10.5
    endloop
  endfacet
  facet normal -0.6073083281517029 -0.7944662570953369 0
    outer loop
      vertex -40 1.8660000562667847 5.5
      vertex -40 1.8660000562667847 0
      vertex -39.79199981689453 1.7070000171661377 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.79199981689453 0.2930000126361847 0
      vertex -86.01599884033203 0 0
      vertex -88.9990005493164 0.1340000033378601 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.23999786376953 0.03400000184774399 0
      vertex -88.9990005493164 0.1340000033378601 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -39.63399887084961 0.5 5.5
      vertex -39.534000396728516 0.7409999966621399 0
      vertex -39.63399887084961 0.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.4990005493164 1 0
      vertex -88.53299713134766 1.2589999437332153 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.4990005493164 1 0
      vertex -86.01599884033203 0 0
      vertex -88.53299713134766 0.7409999966621399 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.53299713134766 0.7409999966621399 0
      vertex -86.01599884033203 0 0
      vertex -88.63300323486328 0.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -92.9990005493164 85 0
      vertex 23 85 0
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.20600128173828 0.2930000126361847 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -90.36499786376953 0.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.4990005493164 1 0
      vertex -94.9990005493164 16.384000778198242 0
      vertex -90.46499633789062 1.2589999437332153 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.46499633789062 0.7409999966621399 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -90.4990005493164 1 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.36499786376953 1.5 0
      vertex -90.46499633789062 1.2589999437332153 0
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.20600128173828 1.7070000171661377 0
      vertex -94.9990005493164 16.384000778198242 0
      vertex -89.9990005493164 1.8660000562667847 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.20600128173828 1.7070000171661377 0
      vertex -90.36499786376953 1.5 0
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal 0.06990589946508408 0.546712338924408 0.8343972563743591
    outer loop
      vertex -89.51399993896484 -52.62200164794922 3.6619999408721924
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 25 -84 0
      vertex 24.48200035095215 -83.93199920654297 0
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 24 -83.73200225830078 0
      vertex 82.99800109863281 85 0
      vertex 24.48200035095215 -83.93199920654297 0
    endloop
  endfacet
  facet normal 0.06992045789957047 0.5467227101325989 0.8343892693519592
    outer loop
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -88.13300323486328 -51.83100128173828 3.0280001163482666
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 82.99800109863281 -84 0
      vertex 25 -84 0
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 23.51799964904785 -83.93199920654297 0
      vertex 82.99800109863281 85 0
      vertex 24 -83.73200225830078 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 23 -84 0
      vertex 82.99800109863281 85 0
      vertex 23.51799964904785 -83.93199920654297 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 82.99800109863281 85 0
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -39.63399887084961 0.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.757999420166016 0.03400000184774399 0
      vertex -40.5 0 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.5 0 0
      vertex -40.24100112915039 0.03400000184774399 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.79199981689453 0.2930000126361847 0
      vertex -39.63399887084961 0.5 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0.08348225057125092 -0.03458647057414055 0.9959088563919067
    outer loop
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
      vertex -79.06700134277344 16.48200035095215 2.5
      vertex -79.25800323486328 17 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.36600112915039 0.5 0
      vertex -41.207000732421875 0.2930000126361847 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.757999420166016 0.03400000184774399 0
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -41 0.1340000033378601 0
    endloop
  endfacet
  facet normal -0.3314758837223053 0.7999864816665649 0.5001453757286072
    outer loop
      vertex -42.29100036621094 4.1020002365112305 4.500999927520752
      vertex -41.2760009765625 3.8980000019073486 5.5
      vertex -41.426998138427734 4.460000038146973 4.500999927520752
    endloop
  endfacet
  facet normal 0.04371333867311478 0.34031036496162415 0.939296543598175
    outer loop
      vertex -87.8550033569336 -50.779998779296875 2.634000062942505
      vertex -89.52100372314453 -50.566001892089844 2.634000062942505
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -80.9990005493164 16 10.5
      vertex -80.9990005493164 16 3.5
      vertex -80.73999786376953 16.034000396728516 3.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.63399887084961 -57.5 0
      vertex -39.534000396728516 -57.25899887084961 0
      vertex 23 -84 0
    endloop
  endfacet
  facet normal -0.33148324489593506 0.799979567527771 0.500151515007019
    outer loop
      vertex -42.29100036621094 4.1020002365112305 4.500999927520752
      vertex -42 3.5980000495910645 5.5
      vertex -41.2760009765625 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -90.4990005493164 1 5.5
      vertex -90.46499633789062 0.7409999966621399 5.5
      vertex -90.4990005493164 1 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.09700012207031 -0.5 5.5
      vertex -91.62000274658203 -1.121000051498413 5.5
      vertex -90.36499786376953 0.5 5.5
    endloop
  endfacet
  facet normal 0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -90.4990005493164 1 0
      vertex -90.46499633789062 1.2589999437332153 5.5
      vertex -90.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0.1290687471628189 -0.9832001328468323 0.1290687471628189
    outer loop
      vertex -80.73999786376953 16.034000396728516 3.5
      vertex -80.9990005493164 16 3.5
      vertex -80.9990005493164 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.5 -56 0
      vertex -40.757999420166016 -56.034000396728516 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.24100112915039 -56.034000396728516 0
      vertex -40.5 -56 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.09700012207031 -0.5 5.5
      vertex -90.36499786376953 0.5 5.5
      vertex -90.46499633789062 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.24100112915039 -56.034000396728516 0
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -40 -56.13399887084961 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 82.99800109863281 85 0
      vertex -40 -56.13399887084961 0
      vertex -40.959999084472656 -8.192000389099121 0
    endloop
  endfacet
  facet normal -0.5273966789245605 0.6868206262588501 0.5001301765441895
    outer loop
      vertex -42.29100036621094 4.1020002365112305 4.500999927520752
      vertex -43.03200149536133 3.5329999923706055 4.500999927520752
      vertex -42 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.63399887084961 -56.5 0
      vertex -39.79199981689453 -56.292999267578125 0
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.79199981689453 -56.292999267578125 0
      vertex -40 -56.13399887084961 0
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -80.4990005493164 16.134000778198242 10.5
      vertex -80.73999786376953 16.034000396728516 10.5
      vertex -80.73999786376953 16.034000396728516 3.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.534000396728516 -56.74100112915039 0
      vertex -39.63399887084961 -56.5 0
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -90.20600128173828 0.2930000126361847 5.5
      vertex -90.20600128173828 0.2930000126361847 0
      vertex -90.36499786376953 0.5 5.5
    endloop
  endfacet
  facet normal 0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -90.46499633789062 0.7409999966621399 0
      vertex -90.46499633789062 0.7409999966621399 5.5
      vertex -90.36499786376953 0.5 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -92.9990005493164 -84 0
      vertex -40.5 -58 0
      vertex 23 -84 0
    endloop
  endfacet
  facet normal -0.5274690985679626 0.6867050528526306 0.5002124905586243
    outer loop
      vertex -43.03200149536133 3.5329999923706055 4.500999927520752
      vertex -42.62099838256836 3.121000051498413 5.5
      vertex -42 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -41.5 -57 0
      vertex -41.46500015258789 -57.25899887084961 0
    endloop
  endfacet
  facet normal 0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -90.46499633789062 1.2589999437332153 5.5
      vertex -90.36499786376953 1.5 0
      vertex -90.36499786376953 1.5 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.46500015258789 -56.74100112915039 0
      vertex -41.5 -57 0
      vertex -43.928199768066406 -57.34400177001953 0
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -90.36499786376953 1.5 5.5
      vertex -90.36499786376953 1.5 0
      vertex -90.20600128173828 1.7070000171661377 5.5
    endloop
  endfacet
  facet normal 0.12888391315937042 -0.9832001328468323 0.1292535662651062
    outer loop
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
      vertex -80.73999786376953 16.034000396728516 3.5
      vertex -80.9990005493164 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -86.01599884033203 0 0
      vertex -41.46500015258789 -56.74100112915039 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.36600112915039 -56.5 0
      vertex -41.46500015258789 -56.74100112915039 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -80.4990005493164 16.134000778198242 3.5
      vertex -80.4990005493164 16.134000778198242 10.5
      vertex -80.73999786376953 16.034000396728516 3.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.959999084472656 -8.192000389099121 0
      vertex -40.757999420166016 -56.034000396728516 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.36600112915039 -56.5 0
      vertex -86.01599884033203 0 0
      vertex -41.207000732421875 -56.292999267578125 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41 -56.13399887084961 0
      vertex -86.01599884033203 0 0
      vertex -40.757999420166016 -56.034000396728516 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.207000732421875 -56.292999267578125 0
      vertex -86.01599884033203 0 0
      vertex -41 -56.13399887084961 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.534000396728516 -57.25899887084961 0
      vertex -39.5 -57 0
      vertex 23 -84 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 82.99800109863281 85 0
      vertex 23 -84 0
      vertex -39.534000396728516 -56.74100112915039 0
    endloop
  endfacet
  facet normal -0.30373790860176086 0.7346219420433044 0.6066909432411194
    outer loop
      vertex -49.292999267578125 18.094999313354492 3
      vertex -49.33399963378906 18.249000549316406 2.7929999828338623
      vertex -49.645999908447266 18.1200008392334 2.7929999828338623
    endloop
  endfacet
  facet normal -0.8579592704772949 -0.11277299374341965 0.501186728477478
    outer loop
      vertex -93.08100128173828 0.9879999756813049 4.500999927520752
      vertex -92.39700317382812 0.2240000069141388 5.5
      vertex -92.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.5 -57 0
      vertex -39.534000396728516 -56.74100112915039 0
      vertex 23 -84 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.63399887084961 -57.5 0
      vertex 23 -84 0
      vertex -39.79199981689453 -57.707000732421875 0
    endloop
  endfacet
  facet normal 0.380079448223114 -0.915991485118866 0.1284492462873459
    outer loop
      vertex -80.4990005493164 16.134000778198242 3.5
      vertex -80.73999786376953 16.034000396728516 3.5
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -39.79199981689453 -57.707000732421875 0
      vertex 23 -84 0
      vertex -40 -57.86600112915039 0
    endloop
  endfacet
  facet normal -0.799350917339325 -0.3312227725982666 0.5013278126716614
    outer loop
      vertex -92.09700012207031 -0.5 5.5
      vertex -92.39700317382812 0.2240000069141388 5.5
      vertex -92.95600128173828 0.061000000685453415 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40 -57.86600112915039 0
      vertex 23 -84 0
      vertex -40.24100112915039 -57.965999603271484 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.24100112915039 -57.965999603271484 0
      vertex 23 -84 0
      vertex -40.5 -58 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -40.757999420166016 -57.965999603271484 0
      vertex -40.5 -58 0
      vertex -92.9990005493164 -84 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.39700317382812 0.2240000069141388 5.5
      vertex -90.46499633789062 0.7409999966621399 5.5
      vertex -92.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.39700317382812 1.7760000228881836 5.5
      vertex -92.4990005493164 1 5.5
      vertex -90.46499633789062 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.4990005493164 1 5.5
      vertex -90.46499633789062 1.2589999437332153 5.5
      vertex -92.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.4990005493164 1 5.5
      vertex -92.4990005493164 1 5.5
      vertex -90.46499633789062 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -92.9990005493164 -84 0
      vertex -41 -57.86600112915039 0
      vertex -40.757999420166016 -57.965999603271484 0
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -80.4990005493164 16.134000778198242 10.5
      vertex -80.4990005493164 16.134000778198242 3.5
      vertex -80.29199981689453 16.292999267578125 10.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -92.9990005493164 -84 0
      vertex -41.207000732421875 -57.707000732421875 0
      vertex -41 -57.86600112915039 0
    endloop
  endfacet
  facet normal -0.23433411121368408 0.5667615532875061 0.7898536920547485
    outer loop
      vertex -49.645999908447266 18.1200008392334 2.7929999828338623
      vertex -49.33399963378906 18.249000549316406 2.7929999828338623
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal -0.23431620001792908 0.3061862885951996 0.9226840734481812
    outer loop
      vertex -50.060001373291016 18.06100082397461 2.634000062942505
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
      vertex -50.04999923706055 18.3700008392334 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.207000732421875 -57.707000732421875 0
      vertex -92.9990005493164 -84 0
      vertex -43.928199768066406 -57.34400177001953 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.46500015258789 -57.25899887084961 0
      vertex -41.36600112915039 -57.5 0
      vertex -43.928199768066406 -57.34400177001953 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -41.36600112915039 -57.5 0
      vertex -41.207000732421875 -57.707000732421875 0
      vertex -43.928199768066406 -57.34400177001953 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -86.01599884033203 0 0
      vertex -88.53299713134766 1.2589999437332153 0
      vertex 23 85 0
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -80.29199981689453 16.292999267578125 3.5
      vertex -80.29199981689453 16.292999267578125 10.5
      vertex -80.4990005493164 16.134000778198242 3.5
    endloop
  endfacet
  facet normal -0.5883092284202576 0.1974579244852066 0.7841572761535645
    outer loop
      vertex -35.30799865722656 -53.7400016784668 3.2899999618530273
      vertex -35.24800109863281 -52.349998474121094 2.984999895095825
      vertex -35.604000091552734 -52.39799880981445 2.7300000190734863
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.75800323486328 0.03400000184774399 0
      vertex -89.4990005493164 0 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.20600128173828 0.2930000126361847 0
      vertex -89.9990005493164 0.1340000033378601 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.4990005493164 0 0
      vertex -89.23999786376953 0.03400000184774399 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -88.9990005493164 0.1340000033378601 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.79199981689453 0.2930000126361847 0
      vertex -88.63300323486328 0.5 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0.6055121421813965 -0.7853309512138367 0.12888121604919434
    outer loop
      vertex -80.29199981689453 16.292999267578125 3.5
      vertex -80.48200225830078 16.104000091552734 3.240999937057495
      vertex -80.26799774169922 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 16.384000778198242 0
      vertex -90.4990005493164 1 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.75800323486328 0.03400000184774399 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -89.9990005493164 0.1340000033378601 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.36499786376953 0.5 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -90.46499633789062 0.7409999966621399 0
    endloop
  endfacet
  facet normal -0.6316038966178894 0.4864693880081177 0.6036754250526428
    outer loop
      vertex -49.981998443603516 17.566999435424805 3
      vertex -49.80099868774414 17.802000045776367 3
      vertex -50.11899948120117 17.645999908447266 2.7929999828338623
    endloop
  endfacet
  facet normal -0.799384593963623 0.33123672008514404 0.5012649297714233
    outer loop
      vertex -92.39700317382812 1.7760000228881836 5.5
      vertex -92.09700012207031 2.5 5.5
      vertex -92.60700225830078 2.7809998989105225 4.500999927520752
    endloop
  endfacet
  facet normal 0.6039289236068726 -0.7862470746040344 0.13071121275424957
    outer loop
      vertex -80.29199981689453 16.292999267578125 3.5
      vertex -80.4990005493164 16.134000778198242 3.5
      vertex -80.48200225830078 16.104000091552734 3.240999937057495
    endloop
  endfacet
  facet normal -0.7220473885536194 0.09296201169490814 0.6855695843696594
    outer loop
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
      vertex -93.87799835205078 0.9850000143051147 3.6619999408721924
      vertex -93.08100128173828 0.9879999756813049 4.500999927520752
    endloop
  endfacet
  facet normal 0.5643277764320374 -0.7319160103797913 0.3818809688091278
    outer loop
      vertex -80.26799774169922 16.268999099731445 3.240999937057495
      vertex -80.48200225830078 16.104000091552734 3.240999937057495
      vertex -80.1969985961914 16.197999954223633 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -88.79199981689453 -56.292999267578125 0
      vertex -86.01599884033203 0 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -92.9990005493164 -84 0
      vertex -88.79199981689453 -57.707000732421875 0
      vertex -43.928199768066406 -57.34400177001953 0
    endloop
  endfacet
  facet normal -0.8014991879463196 0.32893896102905273 0.499397873878479
    outer loop
      vertex -92.60700225830078 2.7809998989105225 4.500999927520752
      vertex -92.96199798583984 1.9160000085830688 4.500999927520752
      vertex -92.39700317382812 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.9990005493164 -56.13399887084961 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -89.75800323486328 -56.034000396728516 0
    endloop
  endfacet
  facet normal -0.6316648721694946 0.48317649960517883 0.6062507033348083
    outer loop
      vertex -49.80099868774414 17.802000045776367 3
      vertex -49.91400146484375 17.913999557495117 2.7929999828338623
      vertex -50.11899948120117 17.645999908447266 2.7929999828338623
    endloop
  endfacet
  facet normal -0.858024001121521 0.11278150230646133 0.5010740160942078
    outer loop
      vertex -92.96199798583984 1.9160000085830688 4.500999927520752
      vertex -92.4990005493164 1 5.5
      vertex -92.39700317382812 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.4990005493164 -56 0
      vertex -89.75800323486328 -56.034000396728516 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.23999786376953 -56.034000396728516 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -88.9990005493164 -56.13399887084961 0
    endloop
  endfacet
  facet normal 0.37765493988990784 -0.916638195514679 0.13096247613430023
    outer loop
      vertex -80.48200225830078 16.104000091552734 3.240999937057495
      vertex -80.4990005493164 16.134000778198242 3.5
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -86.01599884033203 0 0
      vertex -88.9990005493164 -56.13399887084961 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.9990005493164 -56.13399887084961 0
      vertex -86.01599884033203 0 0
      vertex -88.79199981689453 -56.292999267578125 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.63300323486328 -56.5 0
      vertex -88.79199981689453 -56.292999267578125 0
      vertex -43.928199768066406 -57.34400177001953 0
    endloop
  endfacet
  facet normal -0.8593736886978149 0.11019986122846603 0.4993324279785156
    outer loop
      vertex -92.96199798583984 1.9160000085830688 4.500999927520752
      vertex -93.08100128173828 0.9879999756813049 4.500999927520752
      vertex -92.4990005493164 1 5.5
    endloop
  endfacet
  facet normal -0.5625253319740295 0.7344080805778503 0.37974998354911804
    outer loop
      vertex -49.566001892089844 17.98200035095215 3
      vertex -49.80099868774414 17.802000045776367 3
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.53299713134766 -56.74100112915039 0
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -88.4990005493164 -57 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.63300323486328 -56.5 0
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -88.53299713134766 -56.74100112915039 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.4990005493164 -57 0
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -88.53299713134766 -57.25899887084961 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.4990005493164 -56 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -89.23999786376953 -56.034000396728516 0
    endloop
  endfacet
  facet normal -0.4848131239414215 0.6307277679443359 0.6059197783470154
    outer loop
      vertex -49.80099868774414 17.802000045776367 3
      vertex -49.645999908447266 18.1200008392334 2.7929999828338623
      vertex -49.91400146484375 17.913999557495117 2.7929999828338623
    endloop
  endfacet
  facet normal -0.8586313724517822 -0.11578092724084854 0.4993465542793274
    outer loop
      vertex -93.08100128173828 0.9879999756813049 4.500999927520752
      vertex -92.95600128173828 0.061000000685453415 4.500999927520752
      vertex -92.39700317382812 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.09700012207031 2.5 5.5
      vertex -92.39700317382812 1.7760000228881836 5.5
      vertex -90.46499633789062 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal -0.4831351041793823 0.6307597160339355 0.6072253584861755
    outer loop
      vertex -49.80099868774414 17.802000045776367 3
      vertex -49.566001892089844 17.98200035095215 3
      vertex -49.645999908447266 18.1200008392334 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.46499633789062 -57.25899887084961 0
      vertex -94.9990005493164 -82 0
      vertex -90.4990005493164 -57 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.46499633789062 -56.74100112915039 0
      vertex -90.4990005493164 -57 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.36499786376953 -56.5 0
      vertex -90.46499633789062 -56.74100112915039 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal -0.33691543340682983 0.43605464696884155 0.8344724774360657
    outer loop
      vertex -91.70099639892578 4.783999919891357 3.6619999408721924
      vertex -92.18800354003906 5.620999813079834 3.0280001163482666
      vertex -93.29199981689453 4.76800012588501 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.9990005493164 -56.13399887084961 0
      vertex -90.20600128173828 -56.292999267578125 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.20600128173828 -56.292999267578125 0
      vertex -90.36499786376953 -56.5 0
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal -0.3738528788089752 0.4863716959953308 0.7897319793701172
    outer loop
      vertex -49.91400146484375 17.913999557495117 2.7929999828338623
      vertex -49.645999908447266 18.1200008392334 2.7929999828338623
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal -0.37193357944488525 0.4860140383243561 0.7908576130867004
    outer loop
      vertex -49.91400146484375 17.913999557495117 2.7929999828338623
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
      vertex -50.060001373291016 18.06100082397461 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.79199981689453 -57.707000732421875 0
      vertex -92.9990005493164 -84 0
      vertex -88.9990005493164 -57.86600112915039 0
    endloop
  endfacet
  facet normal -0.3368067443370819 0.43669068813323975 0.8341836929321289
    outer loop
      vertex -91.70099639892578 4.783999919891357 3.6619999408721924
      vertex -93.29199981689453 4.76800012588501 3.0280001163482666
      vertex -92.60600280761719 4.085999965667725 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.53299713134766 -57.25899887084961 0
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -88.63300323486328 -57.5 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.63300323486328 -57.5 0
      vertex -43.928199768066406 -57.34400177001953 0
      vertex -88.79199981689453 -57.707000732421875 0
    endloop
  endfacet
  facet normal 0.7337559461593628 -0.5620258450508118 0.3817448616027832
    outer loop
      vertex -80.01699829101562 16.433000564575195 3
      vertex -80.26799774169922 16.268999099731445 3.240999937057495
      vertex -80.1969985961914 16.197999954223633 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -88.9990005493164 -57.86600112915039 0
      vertex -92.9990005493164 -84 0
      vertex -89.23999786376953 -57.965999603271484 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.23999786376953 -57.965999603271484 0
      vertex -92.9990005493164 -84 0
      vertex -89.4990005493164 -58 0
    endloop
  endfacet
  facet normal -0.21269163489341736 0.5083377957344055 0.8344788551330566
    outer loop
      vertex -91.70099639892578 4.783999919891357 3.6619999408721924
      vertex -90.64700317382812 5.224999904632568 3.6619999408721924
      vertex -92.18800354003906 5.620999813079834 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6328337788581848 -0.4840705990791321 0.6043154001235962
    outer loop
      vertex -80.1969985961914 16.197999954223633 3
      vertex -80.08499908447266 16.086000442504883 2.7929999828338623
      vertex -79.87999725341797 16.354000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal -0.21250410377979279 0.5087459087371826 0.8342779278755188
    outer loop
      vertex -90.64700317382812 5.224999904632568 3.6619999408721924
      vertex -90.9000015258789 6.158999919891357 3.0280001163482666
      vertex -92.18800354003906 5.620999813079834 3.0280001163482666
    endloop
  endfacet
  facet normal 0.4855012595653534 -0.6316229701042175 0.6044343709945679
    outer loop
      vertex -80.1969985961914 16.197999954223633 3
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
      vertex -80.08499908447266 16.086000442504883 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -93.9990005493164 -83.73200225830078 0
      vertex -94.41300201416016 -83.41400146484375 0
      vertex -89.4990005493164 -58 0
    endloop
  endfacet
  facet normal -0.17089857161045074 0.48413583636283875 0.8581411242485046
    outer loop
      vertex -50.04999923706055 18.3700008392334 2.5339999198913574
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal 0.6328216791152954 -0.4847145080566406 0.6038116812705994
    outer loop
      vertex -80.1969985961914 16.197999954223633 3
      vertex -79.87999725341797 16.354000091552734 2.7929999828338623
      vertex -80.01699829101562 16.433000564575195 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.73100280761719 -83 0
      vertex -94.93099975585938 -82.51799774169922 0
      vertex -89.4990005493164 -58 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.75800323486328 -57.965999603271484 0
      vertex -89.4990005493164 -58 0
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.46499633789062 -57.25899887084961 0
      vertex -90.36499786376953 -57.5 0
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.93099975585938 -82.51799774169922 0
      vertex -94.9990005493164 -82 0
      vertex -89.4990005493164 -58 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.41300201416016 -83.41400146484375 0
      vertex -94.73100280761719 -83 0
      vertex -89.4990005493164 -58 0
    endloop
  endfacet
  facet normal -0.2098587304353714 0.2715698480606079 0.9392598867416382
    outer loop
      vertex -92.18800354003906 5.620999813079834 3.0280001163482666
      vertex -92.73500061035156 6.560999870300293 2.634000062942505
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
    endloop
  endfacet
  facet normal 0.5627329349517822 -0.734679102897644 0.37891721725463867
    outer loop
      vertex -80.48200225830078 16.104000091552734 3.240999937057495
      vertex -80.43199920654297 16.01799964904785 3
      vertex -80.1969985961914 16.197999954223633 3
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -90.4990005493164 -57 0
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal -0.7942138910293579 0.1543249785900116 0.5877143144607544
    outer loop
      vertex -35.20399856567383 -53.70399856567383 3.4000000953674316
      vertex -35.16400146484375 -52.32899856567383 3.0929999351501465
      vertex -35.24800109863281 -52.349998474121094 2.984999895095825
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -92.9990005493164 -84 0
      vertex -93.51699829101562 -83.93199920654297 0
      vertex -89.4990005493164 -58 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -93.9990005493164 -83.73200225830078 0
      vertex -89.4990005493164 -58 0
      vertex -93.51699829101562 -83.93199920654297 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -89.9990005493164 -57.86600112915039 0
      vertex -89.75800323486328 -57.965999603271484 0
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.20600128173828 -57.707000732421875 0
      vertex -89.9990005493164 -57.86600112915039 0
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex -90.36499786376953 -57.5 0
      vertex -90.20600128173828 -57.707000732421875 0
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal -0.051760464906692505 0.24196618795394897 0.968903124332428
    outer loop
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
      vertex -35.8849983215332 -53.82500076293945 3.0320000648498535
      vertex -35.733001708984375 -52.40700149536133 2.686000108718872
    endloop
  endfacet
  facet normal -0.48625344038009644 0.37194758653640747 0.7907038331031799
    outer loop
      vertex -50.11899948120117 17.645999908447266 2.7929999828338623
      vertex -49.91400146484375 17.913999557495117 2.7929999828338623
      vertex -50.29800033569336 17.75 2.634000062942505
    endloop
  endfacet
  facet normal -0.20985817909240723 0.2716101109981537 0.9392483830451965
    outer loop
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
      vertex -93.29199981689453 4.76800012588501 3.0280001163482666
      vertex -92.18800354003906 5.620999813079834 3.0280001163482666
    endloop
  endfacet
  facet normal -0.486289918422699 0.3721446990966797 0.7905886769294739
    outer loop
      vertex -49.91400146484375 17.913999557495117 2.7929999828338623
      vertex -50.060001373291016 18.06100082397461 2.634000062942505
      vertex -50.29800033569336 17.75 2.634000062942505
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 82.62100219726562 85 2.5969998836517334
      vertex 82.93099975585938 85 2.5260000228881836
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal -0.1323351413011551 0.316542387008667 0.9393020272254944
    outer loop
      vertex -90.9000015258789 6.158999919891357 3.0280001163482666
      vertex -91.18499755859375 7.209000110626221 2.634000062942505
      vertex -92.73500061035156 6.560999870300293 2.634000062942505
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 82.99800109863281 85 2.5202884674072266
      vertex 82.99800109863281 85 0
      vertex 82.93099975585938 85 2.5260000228881836
    endloop
  endfacet
  facet normal -0.07385952025651932 0.5462444424629211 0.8343631029129028
    outer loop
      vertex -90.9000015258789 6.158999919891357 3.0280001163482666
      vertex -89.51399993896484 5.377999782562256 3.6619999408721924
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13228878378868103 0.31670624017715454 0.9392533302307129
    outer loop
      vertex -92.18800354003906 5.620999813079834 3.0280001163482666
      vertex -90.9000015258789 6.158999919891357 3.0280001163482666
      vertex -92.73500061035156 6.560999870300293 2.634000062942505
    endloop
  endfacet
  facet normal -0.384074330329895 0.2939218282699585 0.8752695918083191
    outer loop
      vertex -50.29800033569336 17.75 2.634000062942505
      vertex -50.060001373291016 18.06100082397461 2.634000062942505
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
    endloop
  endfacet
  facet normal 0.04491778090596199 -0.3401501178741455 0.9392977952957153
    outer loop
      vertex -40.5 -63.433998107910156 2.634000062942505
      vertex -38.83399963378906 -63.2140007019043 2.634000062942505
      vertex -40.5 -62.34600067138672 3.0280001163482666
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 25 85 0
      vertex 25 85 10.5
      vertex 81 85 3.5
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 82.05799865722656 85 2.8259999752044678
      vertex 82.99800109863281 85 0
      vertex 81 85 3.5
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 82.62100219726562 85 2.5969998836517334
      vertex 82.99800109863281 85 0
      vertex 82.05799865722656 85 2.8259999752044678
    endloop
  endfacet
  facet normal -0.3850242495536804 0.2954205870628357 0.8743472099304199
    outer loop
      vertex -50.04999923706055 18.3700008392334 2.5339999198913574
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
      vertex -50.060001373291016 18.06100082397461 2.634000062942505
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 25 85 0
      vertex 81 85 3.5
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal -0.10789510607719421 0.08278552442789078 0.9907094240188599
    outer loop
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
      vertex -50.04999923706055 18.3700008392334 2.5339999198913574
      vertex -50.83100128173828 17.759000778198242 2.5
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 81 85 10.5
      vertex 81 85 3.5
      vertex 25 85 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 82.41400146484375 84.41400146484375 10.5
      vertex 82 84.73200225830078 10.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 81.51699829101562 84.93199920654297 10.5
      vertex 80 83 10.5
      vertex 82 84.73200225830078 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 82.99800109863281 83.0150146484375 10.5
      vertex 82.93099975585938 83.51799774169922 10.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 81 85 10.5
      vertex 25 85 10.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 82.93099975585938 83.51799774169922 10.5
      vertex 82.73200225830078 84 10.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 82.73200225830078 84 10.5
      vertex 82.41400146484375 84.41400146484375 10.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 81.51699829101562 84.93199920654297 10.5
      vertex 81 85 10.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0.3525885343551636 -0.8557974100112915 0.37853944301605225
    outer loop
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
      vertex -80.43199920654297 16.01799964904785 3
      vertex -80.48200225830078 16.104000091552734 3.240999937057495
    endloop
  endfacet
  facet normal -0.6867327690124512 0.5275440216064453 0.5000954270362854
    outer loop
      vertex -43.03200149536133 3.5329999923706055 4.500999927520752
      vertex -43.60200119018555 2.7909998893737793 4.500999927520752
      vertex -42.62099838256836 3.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.48381996154785156 -0.6316538453102112 0.6057488322257996
    outer loop
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
      vertex -80.1969985961914 16.197999954223633 3
      vertex -80.43199920654297 16.01799964904785 3
    endloop
  endfacet
  facet normal 0.20933778584003448 0.5099152326583862 0.8343645334243774
    outer loop
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -86.84200286865234 -52.361000061035156 3.0280001163482666
      vertex -88.13300323486328 -51.83100128173828 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6867461204528809 0.5275006294250488 0.5001228451728821
    outer loop
      vertex -43.60200119018555 2.7909998893737793 4.500999927520752
      vertex -43.097999572753906 2.5 5.5
      vertex -42.62099838256836 3.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.35283663868904114 -0.8555507659912109 0.37886565923690796
    outer loop
      vertex -80.43199920654297 16.01799964904785 3
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
      vertex -80.70600128173828 15.904999732971191 3
    endloop
  endfacet
  facet normal 0.4850795865058899 -0.371049702167511 0.7918458580970764
    outer loop
      vertex -79.87999725341797 16.354000091552734 2.7929999828338623
      vertex -80.08499908447266 16.086000442504883 2.7929999828338623
      vertex -79.69999694824219 16.25 2.634000062942505
    endloop
  endfacet
  facet normal 0.48545223474502563 -0.3730645775794983 0.7906699180603027
    outer loop
      vertex -79.69999694824219 16.25 2.634000062942505
      vertex -80.08499908447266 16.086000442504883 2.7929999828338623
      vertex -79.93900299072266 15.939000129699707 2.634000062942505
    endloop
  endfacet
  facet normal -0.5880213975906372 0.09213721007108688 0.8035804629325867
    outer loop
      vertex -35.5 -50.89699935913086 2.634000062942505
      vertex -35.604000091552734 -52.39799880981445 2.7300000190734863
      vertex -35.24800109863281 -52.349998474121094 2.984999895095825
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42 3.5980000495910645 5.5
      vertex -41 1.8660000562667847 5.5
      vertex -41.2760009765625 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42.62099838256836 3.121000051498413 5.5
      vertex -41 1.8660000562667847 5.5
      vertex -42 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.30373790860176086 -0.7346219420433044 0.6066909432411194
    outer loop
      vertex -80.70600128173828 15.904999732971191 3
      vertex -80.66500091552734 15.75100040435791 2.7929999828338623
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
    endloop
  endfacet
  facet normal 0.04355567321181297 0.34057092666625977 0.9392094016075134
    outer loop
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
      vertex -88.13300323486328 -51.83100128173828 3.0280001163482666
      vertex -87.8550033569336 -50.779998779296875 2.634000062942505
    endloop
  endfacet
  facet normal 0.30327823758125305 -0.735382616519928 0.6059989333152771
    outer loop
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
      vertex -80.43199920654297 16.01799964904785 3
      vertex -80.70600128173828 15.904999732971191 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.097999572753906 2.5 5.5
      vertex -43.39699935913086 1.7760000228881836 5.5
      vertex -41.36600112915039 1.5 5.5
    endloop
  endfacet
  facet normal 0.3729042708873749 -0.48513758182525635 0.790938675403595
    outer loop
      vertex -80.08499908447266 16.086000442504883 2.7929999828338623
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
      vertex -79.93900299072266 15.939000129699707 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.207000732421875 1.7070000171661377 5.5
      vertex -42.62099838256836 3.121000051498413 5.5
      vertex -41.36600112915039 1.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41 1.8660000562667847 5.5
      vertex -42.62099838256836 3.121000051498413 5.5
      vertex -41.207000732421875 1.7070000171661377 5.5
    endloop
  endfacet
  facet normal 0.3058600127696991 -0.2350499927997589 0.9226056337356567
    outer loop
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
      vertex -79.69999694824219 16.25 2.634000062942505
      vertex -79.93900299072266 15.939000129699707 2.634000062942505
    endloop
  endfacet
  facet normal 0.2093544900417328 0.509879469871521 0.834382176399231
    outer loop
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -87.322998046875 -53.20100021362305 3.6619999408721924
      vertex -86.84200286865234 -52.361000061035156 3.0280001163482666
    endloop
  endfacet
  facet normal -0.8000219464302063 -0.33039578795433044 0.5008029341697693
    outer loop
      vertex -43.959999084472656 -57.926998138427734 4.500999927520752
      vertex -43.097999572753906 -58.5 5.5
      vertex -43.39699935913086 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal 0.13039080798625946 0.31761232018470764 0.9392127990722656
    outer loop
      vertex -88.13300323486328 -51.83100128173828 3.0280001163482666
      vertex -86.84200286865234 -52.361000061035156 3.0280001163482666
      vertex -86.3010025024414 -51.417999267578125 2.634000062942505
    endloop
  endfacet
  facet normal 0.3341374397277832 0.4384072721004486 0.8343567848205566
    outer loop
      vertex -87.322998046875 -53.20100021362305 3.6619999408721924
      vertex -85.73200225830078 -53.207000732421875 3.0280001163482666
      vertex -86.84200286865234 -52.361000061035156 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5777515769004822 -0.4438253343105316 0.6849979758262634
    outer loop
      vertex -44.29100036621094 -59.18899917602539 3.6619999408721924
      vertex -43.03200149536133 -59.53300094604492 4.500999927520752
      vertex -43.60200119018555 -58.79100036621094 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.5 1 5.5
      vertex -41.46500015258789 1.2589999437332153 5.5
      vertex -43.39699935913086 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0.20792272686958313 0.27314135432243347 0.939234733581543
    outer loop
      vertex -86.84200286865234 -52.361000061035156 3.0280001163482666
      vertex -84.96499633789062 -52.435001373291016 2.634000062942505
      vertex -86.3010025024414 -51.417999267578125 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.36600112915039 0.5 5.5
      vertex -41.46500015258789 0.7409999966621399 5.5
      vertex -43.39699935913086 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.46500015258789 1.2589999437332153 5.5
      vertex -41.36600112915039 1.5 5.5
      vertex -43.39699935913086 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.46500015258789 0.7409999966621399 5.5
      vertex -41.5 1 5.5
      vertex -43.39699935913086 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal 0.20792944729328156 0.2728152275085449 0.9393280744552612
    outer loop
      vertex -86.84200286865234 -52.361000061035156 3.0280001163482666
      vertex -85.73200225830078 -53.207000732421875 3.0280001163482666
      vertex -84.96499633789062 -52.435001373291016 2.634000062942505
    endloop
  endfacet
  facet normal -0.7999835014343262 -0.331474632024765 0.5001509785652161
    outer loop
      vertex -43.959999084472656 -57.926998138427734 4.500999927520752
      vertex -43.60200119018555 -58.79100036621094 4.500999927520752
      vertex -43.097999572753906 -58.5 5.5
    endloop
  endfacet
  facet normal -0.8548735976219177 -0.35255736112594604 0.3806500732898712
    outer loop
      vertex -49.99800109863281 16.73200035095215 3.240999937057495
      vertex -50.095001220703125 16.707000732421875 3
      vertex -49.981998443603516 16.433000564575195 3
    endloop
  endfacet
  facet normal -0.6867461204528809 -0.5275006294250488 0.5001228451728821
    outer loop
      vertex -43.60200119018555 -58.79100036621094 4.500999927520752
      vertex -42.62099838256836 -59.12099838256836 5.5
      vertex -43.097999572753906 -58.5 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -41.207000732421875 0.2930000126361847 5.5
      vertex -41.207000732421875 0.2930000126361847 0
      vertex -41.36600112915039 0.5 5.5
    endloop
  endfacet
  facet normal -0.04597144573926926 0.33998435735702515 0.9393067955970764
    outer loop
      vertex -91.18499755859375 -50.79100036621094 2.634000062942505
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
      vertex -89.52100372314453 -50.566001892089844 2.634000062942505
    endloop
  endfacet
  facet normal -0.6867327690124512 -0.5275440216064453 0.5000954270362854
    outer loop
      vertex -43.60200119018555 -58.79100036621094 4.500999927520752
      vertex -43.03200149536133 -59.53300094604492 4.500999927520752
      vertex -42.62099838256836 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0.9909924268722534 0.133917897939682 0
    outer loop
      vertex -41.5 1 0
      vertex -41.5 1 5.5
      vertex -41.46500015258789 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0.13039329648017883 0.3176037073135376 0.939215362071991
    outer loop
      vertex -87.8550033569336 -50.779998779296875 2.634000062942505
      vertex -88.13300323486328 -51.83100128173828 3.0280001163482666
      vertex -86.3010025024414 -51.417999267578125 2.634000062942505
    endloop
  endfacet
  facet normal 0.9909924268722534 -0.133917897939682 0
    outer loop
      vertex -41.5 1 0
      vertex -41.46500015258789 1.2589999437332153 5.5
      vertex -41.5 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.207000732421875 -57.707000732421875 5.5
      vertex -42.62099838256836 -59.12099838256836 5.5
      vertex -41 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal -0.735792875289917 -0.303447425365448 0.605415940284729
    outer loop
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
      vertex -49.981998443603516 16.433000564575195 3
      vertex -50.095001220703125 16.707000732421875 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.36600112915039 -57.5 5.5
      vertex -42.62099838256836 -59.12099838256836 5.5
      vertex -41.207000732421875 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal -0.9179369211196899 0.12330496311187744 0.3770778179168701
    outer loop
      vertex -50.034000396728516 17 3.240999937057495
      vertex -49.99800109863281 17.26799964904785 3.240999937057495
      vertex -50.132999420166016 17 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42.62099838256836 -59.12099838256836 5.5
      vertex -41.36600112915039 -57.5 5.5
      vertex -43.097999572753906 -58.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42 -59.597999572753906 5.5
      vertex -41 -57.86600112915039 5.5
      vertex -42.62099838256836 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal -0.7898967862129211 -0.10244394838809967 0.604622483253479
    outer loop
      vertex -50.095001220703125 16.707000732421875 3
      vertex -50.132999420166016 17 3
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 80 83 10.5
      vertex 80 -82 10.5
      vertex 82.99800109863281 83.0150146484375 10.5
    endloop
  endfacet
  facet normal -0.05243374779820442 0.1254202276468277 0.9907171726226807
    outer loop
      vertex -92.73500061035156 6.560999870300293 2.634000062942505
      vertex -91.18499755859375 7.209000110626221 2.634000062942505
      vertex -90.87999725341797 8.395000457763672 2.5
    endloop
  endfacet
  facet normal -0.08153501898050308 0.1544104516506195 0.9846367239952087
    outer loop
      vertex -90.87999725341797 8.395000457763672 2.5
      vertex -94.9990005493164 6.21999979019165 2.5
      vertex -92.73500061035156 6.560999870300293 2.634000062942505
    endloop
  endfacet
  facet normal -0.7999835014343262 0.331474632024765 0.5001509785652161
    outer loop
      vertex -43.959999084472656 1.9270000457763672 4.500999927520752
      vertex -43.097999572753906 2.5 5.5
      vertex -43.60200119018555 2.7909998893737793 4.500999927520752
    endloop
  endfacet
  facet normal -0.9167643785476685 0.11889776587486267 0.3813219368457794
    outer loop
      vertex -50.132999420166016 17 3
      vertex -49.99800109863281 17.26799964904785 3.240999937057495
      vertex -50.095001220703125 17.292999267578125 3
    endloop
  endfacet
  facet normal -0.8000219464302063 0.33039578795433044 0.5008029341697693
    outer loop
      vertex -43.959999084472656 1.9270000457763672 4.500999927520752
      vertex -43.39699935913086 1.7760000228881836 5.5
      vertex -43.097999572753906 2.5 5.5
    endloop
  endfacet
  facet normal -0.5274690985679626 -0.6867050528526306 0.5002124905586243
    outer loop
      vertex -43.03200149536133 -59.53300094604492 4.500999927520752
      vertex -42 -59.597999572753906 5.5
      vertex -42.62099838256836 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 82.99800109863281 -84 10.5
      vertex 82.99800109863281 83.0150146484375 10.5
      vertex 80 -82 10.5
    endloop
  endfacet
  facet normal -0.8584338426589966 0.11394160985946655 0.5001085996627808
    outer loop
      vertex -44.082000732421875 1 4.500999927520752
      vertex -43.5 1 5.5
      vertex -43.39699935913086 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal -0.8548735976219177 0.35255736112594604 0.3806500732898712
    outer loop
      vertex -49.99800109863281 17.26799964904785 3.240999937057495
      vertex -49.981998443603516 17.566999435424805 3
      vertex -50.095001220703125 17.292999267578125 3
    endloop
  endfacet
  facet normal -0.5273966789245605 -0.6868206262588501 0.5001301765441895
    outer loop
      vertex -43.03200149536133 -59.53300094604492 4.500999927520752
      vertex -42.29100036621094 -60.10200119018555 4.500999927520752
      vertex -42 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal -0.8582057952880859 0.11294617503881454 0.5007254481315613
    outer loop
      vertex -43.959999084472656 1.9270000457763672 4.500999927520752
      vertex -44.082000732421875 1 4.500999927520752
      vertex -43.39699935913086 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal -0.33148324489593506 -0.799979567527771 0.500151515007019
    outer loop
      vertex -42.29100036621094 -60.10200119018555 4.500999927520752
      vertex -41.2760009765625 -59.89799880981445 5.5
      vertex -42 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal -0.8582057952880859 -0.11294617503881454 0.5007254481315613
    outer loop
      vertex -44.082000732421875 1 4.500999927520752
      vertex -43.959999084472656 0.0729999989271164 4.500999927520752
      vertex -43.39699935913086 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 -82 10.5
      vertex 25 -84 10.5
      vertex 80 -82 10.5
    endloop
  endfacet
  facet normal -0.3314758837223053 -0.7999864816665649 0.5001453757286072
    outer loop
      vertex -42.29100036621094 -60.10200119018555 4.500999927520752
      vertex -41.426998138427734 -60.459999084472656 4.500999927520752
      vertex -41.2760009765625 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal -0.8584338426589966 -0.11394160985946655 0.5001085996627808
    outer loop
      vertex -44.082000732421875 1 4.500999927520752
      vertex -43.39699935913086 0.2240000069141388 5.5
      vertex -43.5 1 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex 82.73200225830078 84 10.5
      vertex 82.41400146484375 84.41400146484375 3.5
      vertex 82.41400146484375 84.41400146484375 10.5
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex 82.41400146484375 84.41400146484375 3.5
      vertex 82 84.73200225830078 10.5
      vertex 82.41400146484375 84.41400146484375 10.5
    endloop
  endfacet
  facet normal -0.7887835502624512 -0.10360142588615417 0.6058772206306458
    outer loop
      vertex -50.132999420166016 17 3
      vertex -50.29199981689453 17 2.7929999828338623
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7221212983131409 -0.09503646194934845 0.685207188129425
    outer loop
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
      vertex -43.959999084472656 -57.926998138427734 4.500999927520752
      vertex -44.082000732421875 -57 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.39699935913086 1.7760000228881836 5.5
      vertex -43.5 1 5.5
      vertex -41.5 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.39699935913086 0.2240000069141388 5.5
      vertex -41.5 1 5.5
      vertex -43.5 1 5.5
    endloop
  endfacet
  facet normal -0.672881543636322 -0.27880969643592834 0.6851974725723267
    outer loop
      vertex -43.60200119018555 -58.79100036621094 4.500999927520752
      vertex -43.959999084472656 -57.926998138427734 4.500999927520752
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6729307770729065 -0.2791133224964142 0.6850255131721497
    outer loop
      vertex -44.29100036621094 -59.18899917602539 3.6619999408721924
      vertex -43.60200119018555 -58.79100036621094 4.500999927520752
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5464816689491272 -0.07186391949653625 0.8343819975852966
    outer loop
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -45.66400146484375 -58.38399887084961 3.0280001163482666
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex 82 84.73200225830078 10.5
      vertex 82.41400146484375 84.41400146484375 3.5
      vertex 82 84.73200225830078 3.5
    endloop
  endfacet
  facet normal -0.1312878131866455 0.31717661023139954 0.9392350912094116
    outer loop
      vertex -42.165000915527344 7.214000225067139 2.634000062942505
      vertex -43.715999603271484 6.572000026702881 2.634000062942505
      vertex -41.882999420166016 6.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal 0.37928059697151184 0.9159626364707947 0.1309909224510193
    outer loop
      vertex 82.01699829101562 84.76200103759766 3.240999937057495
      vertex 81.51699829101562 84.93199920654297 3.5
      vertex 82 84.73200225830078 3.5
    endloop
  endfacet
  facet normal -0.04230673238635063 0.10220831632614136 0.9938629865646362
    outer loop
      vertex -43.47200012207031 7.97599983215332 2.5
      vertex -43.715999603271484 6.572000026702881 2.634000062942505
      vertex -42.165000915527344 7.214000225067139 2.634000062942505
    endloop
  endfacet
  facet normal -0.062223393470048904 0.10553636401891708 0.9924668073654175
    outer loop
      vertex -45.16299819946289 6.979000091552734 2.5
      vertex -43.715999603271484 6.572000026702881 2.634000062942505
      vertex -43.47200012207031 7.97599983215332 2.5
    endloop
  endfacet
  facet normal -0.6072732210159302 -0.07982199639081955 0.7904730439186096
    outer loop
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
      vertex -50.499000549316406 17 2.634000062942505
      vertex -50.448001861572266 16.61199951171875 2.634000062942505
    endloop
  endfacet
  facet normal -0.6072147488594055 -0.079753577709198 0.7905248999595642
    outer loop
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
      vertex -50.29199981689453 17 2.7929999828338623
      vertex -50.499000549316406 17 2.634000062942505
    endloop
  endfacet
  facet normal -0.7898967862129211 0.10244394838809967 0.604622483253479
    outer loop
      vertex -50.132999420166016 17 3
      vertex -50.095001220703125 17.292999267578125 3
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7887835502624512 0.10360142588615417 0.6058772206306458
    outer loop
      vertex -50.132999420166016 17 3
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
      vertex -50.29199981689453 17 2.7929999828338623
    endloop
  endfacet
  facet normal 0.6040772199630737 0.7864401340484619 0.1288510262966156
    outer loop
      vertex 82.41400146484375 84.41400146484375 3.5
      vertex 82.43800354003906 84.43800354003906 3.240999937057495
      vertex 82 84.73200225830078 3.5
    endloop
  endfacet
  facet normal -0.735792875289917 0.303447425365448 0.605415940284729
    outer loop
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
      vertex -50.095001220703125 17.292999267578125 3
      vertex -49.981998443603516 17.566999435424805 3
    endloop
  endfacet
  facet normal 0.7867811918258667 0.6036349534988403 0.12884165346622467
    outer loop
      vertex 82.41400146484375 84.41400146484375 3.5
      vertex 82.76100158691406 84.01699829101562 3.240999937057495
      vertex 82.43800354003906 84.43800354003906 3.240999937057495
    endloop
  endfacet
  facet normal 0.6046614646911621 0.7856866717338562 0.13069437444210052
    outer loop
      vertex 82 84.73200225830078 3.5
      vertex 82.43800354003906 84.43800354003906 3.240999937057495
      vertex 82.01699829101562 84.76200103759766 3.240999937057495
    endloop
  endfacet
  facet normal -0.13129131495952606 0.3171643912792206 0.9392387270927429
    outer loop
      vertex -43.715999603271484 6.572000026702881 2.634000062942505
      vertex -43.17300033569336 5.630000114440918 3.0280001163482666
      vertex -41.882999420166016 6.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal 0.37286287546157837 -0.48566174507141113 0.790636420249939
    outer loop
      vertex -79.93900299072266 15.939000129699707 2.634000062942505
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
      vertex -80.2490005493164 15.701000213623047 2.634000062942505
    endloop
  endfacet
  facet normal -0.4808216392993927 -0.06320077925920486 0.8745377063751221
    outer loop
      vertex -50.448001861572266 16.61199951171875 2.634000062942505
      vertex -50.499000549316406 17 2.634000062942505
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
    endloop
  endfacet
  facet normal 0.23406155407428741 -0.5661023259162903 0.7904070615768433
    outer loop
      vertex -80.35299682617188 15.880000114440918 2.7929999828338623
      vertex -80.66500091552734 15.75100040435791 2.7929999828338623
      vertex -80.2490005493164 15.701000213623047 2.634000062942505
    endloop
  endfacet
  facet normal 0.23507246375083923 -0.30618682503700256 0.9224914908409119
    outer loop
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
      vertex -79.93900299072266 15.939000129699707 2.634000062942505
      vertex -80.2490005493164 15.701000213623047 2.634000062942505
    endloop
  endfacet
  facet normal 0.234296977519989 -0.5654367208480835 0.790813684463501
    outer loop
      vertex -80.66500091552734 15.75100040435791 2.7929999828338623
      vertex -80.61100006103516 15.550999641418457 2.634000062942505
      vertex -80.2490005493164 15.701000213623047 2.634000062942505
    endloop
  endfacet
  facet normal 0.3788367807865143 0.9162998199462891 0.1299128383398056
    outer loop
      vertex 81.51699829101562 84.93199920654297 3.5
      vertex 82.01699829101562 84.76200103759766 3.240999937057495
      vertex 81.5260009765625 84.96499633789062 3.240999937057495
    endloop
  endfacet
  facet normal -0.6072147488594055 0.079753577709198 0.7905248999595642
    outer loop
      vertex -50.29199981689453 17 2.7929999828338623
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
      vertex -50.499000549316406 17 2.634000062942505
    endloop
  endfacet
  facet normal -0.6072732210159302 0.07982199639081955 0.7904730439186096
    outer loop
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
      vertex -50.448001861572266 17.38800048828125 2.634000062942505
      vertex -50.499000549316406 17 2.634000062942505
    endloop
  endfacet
  facet normal -0.7362745404243469 0.3054000735282898 0.6038464903831482
    outer loop
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
      vertex -49.981998443603516 17.566999435424805 3
      vertex -50.11899948120117 17.645999908447266 2.7929999828338623
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex 82.41400146484375 84.41400146484375 3.5
      vertex 82.73200225830078 84 10.5
      vertex 82.73200225830078 84 3.5
    endloop
  endfacet
  facet normal -0.07187410444021225 0.5465325713157654 0.8343477845191956
    outer loop
      vertex -41.882999420166016 6.164000034332275 3.0280001163482666
      vertex -41.632999420166016 5.229000091552734 3.6619999408721924
      vertex -40.5 5.377999782562256 3.6619999408721924
    endloop
  endfacet
  facet normal -0.07299062609672546 0.09445428103208542 0.9928498268127441
    outer loop
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
      vertex -92.73500061035156 6.560999870300293 2.634000062942505
      vertex -94.9990005493164 6.21999979019165 2.5
    endloop
  endfacet
  facet normal -0.4808216392993927 0.06320077925920486 0.8745377063751221
    outer loop
      vertex -50.499000549316406 17 2.634000062942505
      vertex -50.448001861572266 17.38800048828125 2.634000062942505
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
    endloop
  endfacet
  facet normal -0.5658850073814392 0.23448273539543152 0.7904378771781921
    outer loop
      vertex -50.11899948120117 17.645999908447266 2.7929999828338623
      vertex -50.29800033569336 17.75 2.634000062942505
      vertex -50.448001861572266 17.38800048828125 2.634000062942505
    endloop
  endfacet
  facet normal -0.5660281181335449 0.2347833514213562 0.7902461290359497
    outer loop
      vertex -50.448001861572266 17.38800048828125 2.634000062942505
      vertex -50.24800109863281 17.334999084472656 2.7929999828338623
      vertex -50.11899948120117 17.645999908447266 2.7929999828338623
    endloop
  endfacet
  facet normal -0.356097549200058 0.14755423367023468 0.9227254390716553
    outer loop
      vertex -50.448001861572266 17.38800048828125 2.634000062942505
      vertex -50.29800033569336 17.75 2.634000062942505
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
    endloop
  endfacet
  facet normal -0.2784997522830963 0.6729879975318909 0.6852189898490906
    outer loop
      vertex -41.426998138427734 4.460000038146973 4.500999927520752
      vertex -41.632999420166016 5.229000091552734 3.6619999408721924
      vertex -42.68899917602539 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7865555882453918 0.6041659116744995 0.12772561609745026
    outer loop
      vertex 82.73200225830078 84 3.5
      vertex 82.76100158691406 84.01699829101562 3.240999937057495
      vertex 82.41400146484375 84.41400146484375 3.5
    endloop
  endfacet
  facet normal -0.38053199648857117 0.08462663739919662 0.9208874702453613
    outer loop
      vertex -50.499000549316406 17 2.634000062942505
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
      vertex -50.74100112915039 17 2.5339999198913574
    endloop
  endfacet
  facet normal -0.3534005582332611 0 0.9354720711708069
    outer loop
      vertex -50.74100112915039 17 2.5339999198913574
      vertex -50.83100128173828 17.759000778198242 2.5
      vertex -50.83100128173828 16.240999221801758 2.5
    endloop
  endfacet
  facet normal -0.13020452857017517 0.028956227004528046 0.9910642504692078
    outer loop
      vertex -50.74100112915039 17 2.5339999198913574
      vertex -50.59400177001953 17.660999298095703 2.5339999198913574
      vertex -50.83100128173828 17.759000778198242 2.5
    endloop
  endfacet
  facet normal -0.20901815593242645 0.27221542596817017 0.9392604231834412
    outer loop
      vertex -43.17300033569336 5.630000114440918 3.0280001163482666
      vertex -45.04899978637695 5.548999786376953 2.634000062942505
      vertex -44.279998779296875 4.78000020980835 3.0280001163482666
    endloop
  endfacet
  facet normal -0.20901581645011902 0.2723539471626282 0.9392207860946655
    outer loop
      vertex -43.17300033569336 5.630000114440918 3.0280001163482666
      vertex -43.715999603271484 6.572000026702881 2.634000062942505
      vertex -45.04899978637695 5.548999786376953 2.634000062942505
    endloop
  endfacet
  facet normal 0.5646383762359619 0.2331591248512268 0.7917198538780212
    outer loop
      vertex 82.99800109863281 84.1308822631836 2.788181781768799
      vertex 82.99800109863281 84.15351104736328 2.7815165519714355
      vertex 82.98500061035156 84.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal -0.2787246108055115 0.672676146030426 0.6854337453842163
    outer loop
      vertex -42.29100036621094 4.1020002365112305 4.500999927520752
      vertex -41.426998138427734 4.460000038146973 4.500999927520752
      vertex -42.68899917602539 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6737651228904724 0.276516318321228 0.6852585673332214
    outer loop
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
      vertex -92.96199798583984 1.9160000085830688 4.500999927520752
      vertex -92.60700225830078 2.7809998989105225 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 83 2.5
      vertex -79.4260025024414 18.207000732421875 2.5
      vertex -50.83100128173828 17.759000778198242 2.5
    endloop
  endfacet
  facet normal 0.5654784440994263 0.23416738212108612 0.7908222079277039
    outer loop
      vertex 82.99800109863281 84.11460876464844 2.7929999828338623
      vertex 82.99800109863281 84.1308822631836 2.788181781768799
      vertex 82.98500061035156 84.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal 0.23923012614250183 -0.3752758204936981 0.8955093622207642
    outer loop
      vertex -80.2490005493164 15.701000213623047 2.634000062942505
      vertex -80.33899688720703 15.404999732971191 2.5339999198913574
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
    endloop
  endfacet
  facet normal 0.14775538444519043 -0.35658296942710876 0.922505795955658
    outer loop
      vertex -80.2490005493164 15.701000213623047 2.634000062942505
      vertex -80.61100006103516 15.550999641418457 2.634000062942505
      vertex -80.33899688720703 15.404999732971191 2.5339999198913574
    endloop
  endfacet
  facet normal 0.7364738583564758 0.3049774169921875 0.6038170456886292
    outer loop
      vertex 82.98500061035156 84.14600372314453 2.7929999828338623
      vertex 82.8479995727539 84.06700134277344 3
      vertex 82.99800109863281 84.11460876464844 2.7929999828338623
    endloop
  endfacet
  facet normal 0.4847888648509979 0.3715013563632965 0.7918121814727783
    outer loop
      vertex 82.99800109863281 84.3638916015625 2.6828105449676514
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
      vertex 82.99800109863281 84.15351104736328 2.7815165519714355
    endloop
  endfacet
  facet normal -0.5794787406921387 0.4414333701133728 0.6850846409797668
    outer loop
      vertex -92.60700225830078 2.7809998989105225 4.500999927520752
      vertex -92.04100036621094 3.5239999294281006 4.500999927520752
      vertex -93.2979965209961 3.1760001182556152 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 84.11460876464844 2.7929999828338623
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 84.1308822631836 2.788181781768799
    endloop
  endfacet
  facet normal 0.12211856991052628 -0.9174548983573914 0.3786338269710541
    outer loop
      vertex -80.70600128173828 15.904999732971191 3
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
      vertex -80.9990005493164 15.866000175476074 3
    endloop
  endfacet
  facet normal 0.12019895017147064 -0.916946291923523 0.38047564029693604
    outer loop
      vertex -80.73200225830078 16.000999450683594 3.240999937057495
      vertex -80.9990005493164 15.965999603271484 3.240999937057495
      vertex -80.9990005493164 15.866000175476074 3
    endloop
  endfacet
  facet normal -0.7939766049385071 -0.6079483032226562 0
    outer loop
      vertex -35.584999084472656 15.413999557495117 3.5
      vertex -35.268001556396484 15 10.5
      vertex -35.584999084472656 15.413999557495117 10.5
    endloop
  endfacet
  facet normal -0.6082307696342468 -0.7937602400779724 0
    outer loop
      vertex -35.584999084472656 15.413999557495117 3.5
      vertex -35.584999084472656 15.413999557495117 10.5
      vertex -36 15.732000350952148 10.5
    endloop
  endfacet
  facet normal 0 -0.7930510640144348 0.6091551780700684
    outer loop
      vertex -92.9990005493164 15.866000175476074 3
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
      vertex -80.9990005493164 15.866000175476074 3
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -37 16 3.5
      vertex -36.481998443603516 15.932000160217285 3.5
      vertex -37 16 10.5
    endloop
  endfacet
  facet normal 0.10497645288705826 -0.788669228553772 0.6057894229888916
    outer loop
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
      vertex -80.70600128173828 15.904999732971191 3
      vertex -80.9990005493164 15.866000175476074 3
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 84.15351104736328 2.7815165519714355
      vertex 82.99800109863281 84.1308822631836 2.788181781768799
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.87273406982422 2.915163993835449
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 84.11460876464844 2.7929999828338623
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 84.46735382080078 2.634000062942505
      vertex 82.99800109863281 84.3638916015625 2.6828105449676514
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 84.15351104736328 2.7815165519714355
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 84.3638916015625 2.6828105449676514
    endloop
  endfacet
  facet normal -0.6737880706787109 0.2766546905040741 0.685180127620697
    outer loop
      vertex -92.60700225830078 2.7809998989105225 4.500999927520752
      vertex -93.2979965209961 3.1760001182556152 3.6619999408721924
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
    endloop
  endfacet
  facet normal 0.10381203889846802 -0.7880277633666992 0.6068239808082581
    outer loop
      vertex -80.70600128173828 15.904999732971191 3
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
      vertex -80.66500091552734 15.75100040435791 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6082307696342468 -0.7937602400779724 0
    outer loop
      vertex -36 15.732000350952148 10.5
      vertex -36 15.732000350952148 3.5
      vertex -35.584999084472656 15.413999557495117 3.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -36 15.732000350952148 3.5
      vertex -36 15.732000350952148 10.5
      vertex -36.481998443603516 15.932000160217285 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -36 15.732000350952148 3.5
      vertex -36.481998443603516 15.932000160217285 10.5
      vertex -36.481998443603516 15.932000160217285 3.5
    endloop
  endfacet
  facet normal -0.5099067091941833 0.20936566591262817 0.8343627452850342
    outer loop
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
      vertex -93.2979965209961 3.1760001182556152 3.6619999408721924
      vertex -94.66799926757812 2.365999937057495 3.0280001163482666
    endloop
  endfacet
  facet normal 0.07999084144830704 -0.6072031855583191 0.790509819984436
    outer loop
      vertex -80.9990005493164 15.5 2.634000062942505
      vertex -80.66500091552734 15.75100040435791 2.7929999828338623
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal 0.07979033142328262 -0.607032299041748 0.7906612753868103
    outer loop
      vertex -80.61100006103516 15.550999641418457 2.634000062942505
      vertex -80.66500091552734 15.75100040435791 2.7929999828338623
      vertex -80.9990005493164 15.5 2.634000062942505
    endloop
  endfacet
  facet normal -0.43861106038093567 0.3342927396297455 0.8341874480247498
    outer loop
      vertex -94.13800048828125 3.6579999923706055 3.0280001163482666
      vertex -92.60600280761719 4.085999965667725 3.6619999408721924
      vertex -93.29199981689453 4.76800012588501 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5795491933822632 0.4407121241092682 0.685489296913147
    outer loop
      vertex -93.2979965209961 3.1760001182556152 3.6619999408721924
      vertex -92.04100036621094 3.5239999294281006 4.500999927520752
      vertex -92.60600280761719 4.085999965667725 3.6619999408721924
    endloop
  endfacet
  facet normal -0.38012513518333435 -0.9161015748977661 0.12752538919448853
    outer loop
      vertex -36 15.732000350952148 3.5
      vertex -36.481998443603516 15.932000160217285 3.5
      vertex -36.016998291015625 15.70300006866455 3.240999937057495
    endloop
  endfacet
  facet normal -0.43853506445884705 0.3334794044494629 0.8345528841018677
    outer loop
      vertex -94.13800048828125 3.6579999923706055 3.0280001163482666
      vertex -93.2979965209961 3.1760001182556152 3.6619999408721924
      vertex -92.60600280761719 4.085999965667725 3.6619999408721924
    endloop
  endfacet
  facet normal 0.05031241104006767 -0.3827689290046692 0.9224730730056763
    outer loop
      vertex -80.61100006103516 15.550999641418457 2.634000062942505
      vertex -80.9990005493164 15.5 2.634000062942505
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal -0.6031620502471924 -0.7871454358100891 0.12883158028125763
    outer loop
      vertex -35.584999084472656 15.413999557495117 3.5
      vertex -36 15.732000350952148 3.5
      vertex -35.60900115966797 15.390000343322754 3.240999937057495
    endloop
  endfacet
  facet normal -0.5091010928153992 -0.21116124093532562 0.8344022035598755
    outer loop
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
      vertex -45.66400146484375 -58.38399887084961 3.0280001163482666
      vertex -44.29100036621094 -59.18899917602539 3.6619999408721924
    endloop
  endfacet
  facet normal -0.27295053005218506 0.20803257822990417 0.9392659068107605
    outer loop
      vertex -94.13800048828125 3.6579999923706055 3.0280001163482666
      vertex -93.29199981689453 4.76800012588501 3.0280001163482666
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
    endloop
  endfacet
  facet normal -0.6036903858184814 -0.786919116973877 0.12773509323596954
    outer loop
      vertex -36 15.732000350952148 3.5
      vertex -36.016998291015625 15.70300006866455 3.240999937057495
      vertex -35.60900115966797 15.390000343322754 3.240999937057495
    endloop
  endfacet
  facet normal -0.7215167284011841 -0.09751948714256287 0.685495138168335
    outer loop
      vertex -93.7249984741211 -0.1469999998807907 3.6619999408721924
      vertex -92.95600128173828 0.061000000685453415 4.500999927520752
      vertex -93.87799835205078 0.9850000143051147 3.6619999408721924
    endloop
  endfacet
  facet normal -0.7223204970359802 0.09262514859437943 0.685327410697937
    outer loop
      vertex -93.08100128173828 0.9879999756813049 4.500999927520752
      vertex -92.96199798583984 1.9160000085830688 4.500999927520752
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -41.207000732421875 -57.707000732421875 0
      vertex -41.207000732421875 -57.707000732421875 5.5
      vertex -41 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -41.36600112915039 -57.5 5.5
      vertex -41.207000732421875 -57.707000732421875 5.5
      vertex -41.207000732421875 -57.707000732421875 0
    endloop
  endfacet
  facet normal -0.37888389825820923 -0.9162804484367371 0.12991200387477875
    outer loop
      vertex -36.481998443603516 15.932000160217285 3.5
      vertex -36.49100112915039 15.89900016784668 3.240999937057495
      vertex -36.016998291015625 15.70300006866455 3.240999937057495
    endloop
  endfacet
  facet normal -0.7214087247848511 -0.09727734327316284 0.6856431365013123
    outer loop
      vertex -93.87799835205078 0.9850000143051147 3.6619999408721924
      vertex -92.95600128173828 0.061000000685453415 4.500999927520752
      vertex -93.08100128173828 0.9879999756813049 4.500999927520752
    endloop
  endfacet
  facet normal 0.13129131495952606 0.3171643912792206 0.9392387270927429
    outer loop
      vertex -39.11600112915039 -51.83599853515625 3.0280001163482666
      vertex -37.82600021362305 -52.369998931884766 3.0280001163482666
      vertex -37.28300094604492 -51.428001403808594 2.634000062942505
    endloop
  endfacet
  facet normal -0.5778562426567078 -0.4427895247936249 0.685579776763916
    outer loop
      vertex -43.59600067138672 -60.09600067138672 3.6619999408721924
      vertex -43.03200149536133 -59.53300094604492 4.500999927520752
      vertex -44.29100036621094 -59.18899917602539 3.6619999408721924
    endloop
  endfacet
  facet normal 0.04798748344182968 0.11593238264322281 0.9920971989631653
    outer loop
      vertex -38.667999267578125 -49.70800018310547 2.5
      vertex -38.83399963378906 -50.7859992980957 2.634000062942505
      vertex -37.28300094604492 -51.428001403808594 2.634000062942505
    endloop
  endfacet
  facet normal 0.27148178219795227 0.21000492572784424 0.9392526745796204
    outer loop
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
      vertex -83.93800354003906 -53.763999938964844 2.634000062942505
      vertex -85.73200225830078 -53.207000732421875 3.0280001163482666
    endloop
  endfacet
  facet normal 0.2714167535305023 0.20974041521549225 0.9393305778503418
    outer loop
      vertex -83.93800354003906 -53.763999938964844 2.634000062942505
      vertex -84.96499633789062 -52.435001373291016 2.634000062942505
      vertex -85.73200225830078 -53.207000732421875 3.0280001163482666
    endloop
  endfacet
  facet normal -0.44339895248413086 -0.5774316787719727 0.6855435967445374
    outer loop
      vertex -43.59600067138672 -60.09600067138672 3.6619999408721924
      vertex -42.29100036621094 -60.10200119018555 4.500999927520752
      vertex -43.03200149536133 -59.53300094604492 4.500999927520752
    endloop
  endfacet
  facet normal 0.3166539967060089 0.13238179683685303 0.9392578601837158
    outer loop
      vertex -83.93800354003906 -53.763999938964844 2.634000062942505
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
      vertex -83.29000091552734 -55.31399917602539 2.634000062942505
    endloop
  endfacet
  facet normal -0.44330033659935 -0.5776916742324829 0.6853883266448975
    outer loop
      vertex -43.59600067138672 -60.09600067138672 3.6619999408721924
      vertex -42.68899917602539 -60.79199981689453 3.6619999408721924
      vertex -42.29100036621094 -60.10200119018555 4.500999927520752
    endloop
  endfacet
  facet normal -0.4375706613063812 -0.3352939486503601 0.8343319892883301
    outer loop
      vertex -44.29100036621094 -59.18899917602539 3.6619999408721924
      vertex -45.12900161743164 -59.67300033569336 3.0280001163482666
      vertex -43.59600067138672 -60.09600067138672 3.6619999408721924
    endloop
  endfacet
  facet normal 0.10224903374910355 0.04274669289588928 0.9938399791717529
    outer loop
      vertex -83.29000091552734 -55.31399917602539 2.634000062942505
      vertex -82.4469985961914 -54.21500015258789 2.5
      vertex -83.93800354003906 -53.763999938964844 2.634000062942505
    endloop
  endfacet
  facet normal 0.11394651979207993 0.08254393935203552 0.9900518655776978
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -83.93800354003906 -53.763999938964844 2.634000062942505
      vertex -82.4469985961914 -54.21500015258789 2.5
    endloop
  endfacet
  facet normal -0.5466386079788208 -0.07388313114643097 0.8341028094291687
    outer loop
      vertex -94.84500122070312 0.9819999933242798 3.0280001163482666
      vertex -93.7249984741211 -0.1469999998807907 3.6619999408721924
      vertex -93.87799835205078 0.9850000143051147 3.6619999408721924
    endloop
  endfacet
  facet normal 0.10300315916538239 0.0795968696475029 0.9914911389350891
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -84.96499633789062 -52.435001373291016 2.634000062942505
      vertex -83.93800354003906 -53.763999938964844 2.634000062942505
    endloop
  endfacet
  facet normal -0.4375992715358734 -0.33561134338378906 0.8341893553733826
    outer loop
      vertex -45.12900161743164 -59.67300033569336 3.0280001163482666
      vertex -44.279998779296875 -60.779998779296875 3.0280001163482666
      vertex -43.59600067138672 -60.09600067138672 3.6619999408721924
    endloop
  endfacet
  facet normal -0.2787246108055115 -0.672676146030426 0.6854337453842163
    outer loop
      vertex -42.68899917602539 -60.79199981689453 3.6619999408721924
      vertex -41.426998138427734 -60.459999084472656 4.500999927520752
      vertex -42.29100036621094 -60.10200119018555 4.500999927520752
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -35.268001556396484 15 3.5
      vertex -35.06800079345703 14.517999649047852 3.5
      vertex -35.268001556396484 15 10.5
    endloop
  endfacet
  facet normal 0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -90.46499633789062 0.7409999966621399 5.5
      vertex -90.46499633789062 0.7409999966621399 0
      vertex -90.4990005493164 1 0
    endloop
  endfacet
  facet normal -0.2784997522830963 -0.6729879975318909 0.6852189898490906
    outer loop
      vertex -42.68899917602539 -60.79199981689453 3.6619999408721924
      vertex -41.632999420166016 -61.229000091552734 3.6619999408721924
      vertex -41.426998138427734 -60.459999084472656 4.500999927520752
    endloop
  endfacet
  facet normal -0.7939766049385071 -0.6079483032226562 0
    outer loop
      vertex -35.268001556396484 15 3.5
      vertex -35.268001556396484 15 10.5
      vertex -35.584999084472656 15.413999557495117 3.5
    endloop
  endfacet
  facet normal 0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -90.46499633789062 1.2589999437332153 5.5
      vertex -90.4990005493164 1 0
      vertex -90.46499633789062 1.2589999437332153 0
    endloop
  endfacet
  facet normal 0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -90.46499633789062 1.2589999437332153 5.5
      vertex -90.46499633789062 1.2589999437332153 0
      vertex -90.36499786376953 1.5 0
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -90.20600128173828 1.7070000171661377 5.5
      vertex -90.36499786376953 1.5 0
      vertex -90.20600128173828 1.7070000171661377 0
    endloop
  endfacet
  facet normal -0.3357207775115967 -0.43749818205833435 0.8341983556747437
    outer loop
      vertex -44.279998779296875 -60.779998779296875 3.0280001163482666
      vertex -42.68899917602539 -60.79199981689453 3.6619999408721924
      vertex -43.59600067138672 -60.09600067138672 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9158178567886353 -0.38000741600990295 0.12989211082458496
    outer loop
      vertex -35.06800079345703 14.517999649047852 3.5
      vertex -35.268001556396484 15 3.5
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
    endloop
  endfacet
  facet normal 0.5084252953529358 0.2125266045331955 0.8344675898551941
    outer loop
      vertex -85.71499633789062 -54.79800033569336 3.6619999408721924
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
    endloop
  endfacet
  facet normal -0.09503646194934845 -0.7221212983131409 0.685207188129425
    outer loop
      vertex -41.632999420166016 -61.229000091552734 3.6619999408721924
      vertex -40.5 -60.582000732421875 4.500999927520752
      vertex -41.426998138427734 -60.459999084472656 4.500999927520752
    endloop
  endfacet
  facet normal -0.7874711751937866 -0.6029670238494873 0.12774942815303802
    outer loop
      vertex -35.268001556396484 15 3.5
      vertex -35.584999084472656 15.413999557495117 3.5
      vertex -35.297000885009766 14.982999801635742 3.240999937057495
    endloop
  endfacet
  facet normal -0.9165692329406738 -0.3790033161640167 0.1275041103363037
    outer loop
      vertex -35.268001556396484 15 3.5
      vertex -35.297000885009766 14.982999801635742 3.240999937057495
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -90.20600128173828 0.2930000126361847 0
      vertex -90.36499786376953 0.5 0
      vertex -90.36499786376953 0.5 5.5
    endloop
  endfacet
  facet normal 0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -90.36499786376953 0.5 0
      vertex -90.46499633789062 0.7409999966621399 0
      vertex -90.36499786376953 0.5 5.5
    endloop
  endfacet
  facet normal 0.5086036324501038 0.21244469285011292 0.8343797326087952
    outer loop
      vertex -84.33999633789062 -55.5989990234375 3.0280001163482666
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -35 14 10.5
      vertex -35.06800079345703 14.517999649047852 10.5
      vertex -35.06800079345703 14.517999649047852 3.5
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -35.268001556396484 15 10.5
      vertex -35.06800079345703 14.517999649047852 3.5
      vertex -35.06800079345703 14.517999649047852 10.5
    endloop
  endfacet
  facet normal 0.3819020092487335 0.9242027997970581 0
    outer loop
      vertex -41 -57.86600112915039 5.5
      vertex -40.757999420166016 -57.965999603271484 5.5
      vertex -41 -57.86600112915039 0
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 85 2.5202884674072266
      vertex 82.99800109863281 84.7852554321289 2.5569231510162354
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 84.7852554321289 2.5569231510162354
      vertex 82.99800109863281 84.46735382080078 2.634000062942505
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -41 -57.86600112915039 5.5
      vertex -41 -57.86600112915039 0
      vertex -41.207000732421875 -57.707000732421875 0
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -41.207000732421875 -57.707000732421875 0
      vertex -41.36600112915039 -57.5 0
      vertex -41.36600112915039 -57.5 5.5
    endloop
  endfacet
  facet normal 0.5632072687149048 0.7343292236328125 0.3788907527923584
    outer loop
      vertex 82.06700134277344 84.8479995727539 3
      vertex 82.01699829101562 84.76200103759766 3.240999937057495
      vertex 82.50900268554688 84.50900268554688 3
    endloop
  endfacet
  facet normal 0.5636794567108154 0.7324352860450745 0.3818429410457611
    outer loop
      vertex 82.43800354003906 84.43800354003906 3.240999937057495
      vertex 82.50900268554688 84.50900268554688 3
      vertex 82.01699829101562 84.76200103759766 3.240999937057495
    endloop
  endfacet
  facet normal 0.09609267115592957 -0.4343915283679962 0.8955836892127991
    outer loop
      vertex -80.61100006103516 15.550999641418457 2.634000062942505
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
      vertex -80.33899688720703 15.404999732971191 2.5339999198913574
    endloop
  endfacet
  facet normal 0.22401359677314758 0.2633378803730011 0.9383342266082764
    outer loop
      vertex -37.28300094604492 -51.428001403808594 2.634000062942505
      vertex -37.82600021362305 -52.369998931884766 3.0280001163482666
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
    endloop
  endfacet
  facet normal 0.22828583419322968 0.29730871319770813 0.9270884990692139
    outer loop
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
      vertex -37.82600021362305 -52.369998931884766 3.0280001163482666
      vertex -36.71900177001953 -53.220001220703125 3.0280001163482666
    endloop
  endfacet
  facet normal 0.21317864954471588 -0.16365939378738403 0.9632084369659424
    outer loop
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
      vertex -79.9990005493164 15.267999649047852 2.5
      vertex -79.06700134277344 16.48200035095215 2.5
    endloop
  endfacet
  facet normal 0.4848547875881195 0.632170557975769 0.6043808460235596
    outer loop
      vertex 82.06700134277344 84.8479995727539 3
      vertex 82.50900268554688 84.50900268554688 3
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
    endloop
  endfacet
  facet normal 0.060877081006765366 -0.09549673646688461 0.9935664534568787
    outer loop
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
      vertex -80.33899688720703 15.404999732971191 2.5339999198913574
      vertex -79.9990005493164 15.267999649047852 2.5
    endloop
  endfacet
  facet normal -0.7870236039161682 -0.603320300579071 0.12883496284484863
    outer loop
      vertex -35.584999084472656 15.413999557495117 3.5
      vertex -35.60900115966797 15.390000343322754 3.240999937057495
      vertex -35.297000885009766 14.982999801635742 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.9990005493164 15 2.5
      vertex -82.90299987792969 4.617000102996826 2.5
      vertex -79.9990005493164 15.267999649047852 2.5
    endloop
  endfacet
  facet normal 0.7333889007568359 0.5624860525131226 0.38177230954170227
    outer loop
      vertex 82.50900268554688 84.50900268554688 3
      vertex 82.43800354003906 84.43800354003906 3.240999937057495
      vertex 82.8479995727539 84.06700134277344 3
    endloop
  endfacet
  facet normal 0.1312878131866455 0.31717661023139954 0.9392350912094116
    outer loop
      vertex -38.83399963378906 -50.7859992980957 2.634000062942505
      vertex -39.11600112915039 -51.83599853515625 3.0280001163482666
      vertex -37.28300094604492 -51.428001403808594 2.634000062942505
    endloop
  endfacet
  facet normal -0.8541704416275024 -0.353201299905777 0.3816302716732025
    outer loop
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
      vertex -35.297000885009766 14.982999801635742 3.240999937057495
      vertex -35.38399887084961 14.932999610900879 3
    endloop
  endfacet
  facet normal 0.03947668895125389 -0.1473010778427124 0.9883036017417908
    outer loop
      vertex -80.33899688720703 15.404999732971191 2.5339999198913574
      vertex -80.9990005493164 15 2.5
      vertex -79.9990005493164 15.267999649047852 2.5
    endloop
  endfacet
  facet normal -0.8546422123908997 -0.35515132546424866 0.3787534832954407
    outer loop
      vertex -35.38399887084961 14.932999610900879 3
      vertex -35.196998596191406 14.482999801635742 3
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
    endloop
  endfacet
  facet normal 0.02878047339618206 -0.13010351359844208 0.9910826086997986
    outer loop
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
      vertex -80.9990005493164 15 2.5
      vertex -80.33899688720703 15.404999732971191 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -79.9990005493164 15.267999649047852 2.5
      vertex -50.83100128173828 16.240999221801758 2.5
      vertex -79.06700134277344 16.48200035095215 2.5
    endloop
  endfacet
  facet normal 0.48483628034591675 0.6309513449668884 0.6056683659553528
    outer loop
      vertex 82.14600372314453 84.98600006103516 2.7929999828338623
      vertex 82.06700134277344 84.8479995727539 3
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
    endloop
  endfacet
  facet normal 0.33575916290283203 0.4372769296169281 0.8342989087104797
    outer loop
      vertex -36.71900177001953 -53.220001220703125 3.0280001163482666
      vertex -37.82600021362305 -52.369998931884766 3.0280001163482666
      vertex -38.310001373291016 -53.20800018310547 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3530791401863098 -0.8542237281799316 0.38162413239479065
    outer loop
      vertex -36.516998291015625 15.802000045776367 3
      vertex -36.06700134277344 15.616000175476074 3
      vertex -36.016998291015625 15.70300006866455 3.240999937057495
    endloop
  endfacet
  facet normal 0.35363417863845825 0.8553417921066284 0.3785938024520874
    outer loop
      vertex 82.01699829101562 84.76200103759766 3.240999937057495
      vertex 82.06700134277344 84.8479995727539 3
      vertex 81.5260009765625 84.96499633789062 3.240999937057495
    endloop
  endfacet
  facet normal -0.35316500067710876 -0.8540827035903931 0.38186022639274597
    outer loop
      vertex -36.016998291015625 15.70300006866455 3.240999937057495
      vertex -36.49100112915039 15.89900016784668 3.240999937057495
      vertex -36.516998291015625 15.802000045776367 3
    endloop
  endfacet
  facet normal -0.5626438856124878 -0.7334144115447998 0.38149067759513855
    outer loop
      vertex -35.60900115966797 15.390000343322754 3.240999937057495
      vertex -36.016998291015625 15.70300006866455 3.240999937057495
      vertex -36.06700134277344 15.616000175476074 3
    endloop
  endfacet
  facet normal 0.3420163691043854 0.7163893580436707 0.6081209182739258
    outer loop
      vertex 82.05799865722656 85 2.8259999752044678
      vertex 82.06700134277344 84.8479995727539 3
      vertex 82.14600372314453 84.98600006103516 2.7929999828338623
    endloop
  endfacet
  facet normal 0.500314474105835 0.07586073130369186 -0.862514078617096
    outer loop
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.9990005493164 0 2.866046905517578
    endloop
  endfacet
  facet normal 0.3704967498779297 0.18178147077560425 0.9108719229698181
    outer loop
      vertex 82.62100219726562 85 2.5969998836517334
      vertex 82.05799865722656 85 2.8259999752044678
      vertex 82.14600372314453 84.98600006103516 2.7929999828338623
    endloop
  endfacet
  facet normal 0.015967486426234245 0.1209174171090126 0.9925341606140137
    outer loop
      vertex -38.667999267578125 -49.70800018310547 2.5
      vertex -40.5 -50.566001892089844 2.634000062942505
      vertex -38.83399963378906 -50.7859992980957 2.634000062942505
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.9990005493164 6.21999979019165 2.5
      vertex -94.9990005493164 0 2.866046905517578
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 16.384000778198242 0
      vertex -94.9990005493164 0 2.866046905517578
      vertex -94.9990005493164 6.21999979019165 2.5
    endloop
  endfacet
  facet normal 0 -0.9236428737640381 0.3832542896270752
    outer loop
      vertex -80.9990005493164 15.965999603271484 3.240999937057495
      vertex -92.9990005493164 15.965999603271484 3.240999937057495
      vertex -92.9990005493164 15.866000175476074 3
    endloop
  endfacet
  facet normal 0 -0.9236428737640381 0.3832542896270752
    outer loop
      vertex -80.9990005493164 15.866000175476074 3
      vertex -80.9990005493164 15.965999603271484 3.240999937057495
      vertex -92.9990005493164 15.866000175476074 3
    endloop
  endfacet
  facet normal -0.9386153817176819 0.21272751688957214 0.2715662121772766
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.66799926757812 2.365999937057495 3.0280001163482666
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
    endloop
  endfacet
  facet normal -0.5467227101325989 0.06992045789957047 0.8343892693519592
    outer loop
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
      vertex -94.66799926757812 2.365999937057495 3.0280001163482666
      vertex -94.84500122070312 0.9819999933242798 3.0280001163482666
    endloop
  endfacet
  facet normal 0.21085025370121002 0.5093573331832886 0.8343244194984436
    outer loop
      vertex -37.82600021362305 -52.369998931884766 3.0280001163482666
      vertex -39.11600112915039 -51.83599853515625 3.0280001163482666
      vertex -39.36600112915039 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5470884442329407 0.07043643295764923 0.8341060280799866
    outer loop
      vertex -94.84500122070312 0.9819999933242798 3.0280001163482666
      vertex -93.87799835205078 0.9850000143051147 3.6619999408721924
      vertex -93.73200225830078 2.11899995803833 3.6619999408721924
    endloop
  endfacet
  facet normal 0 -0.13015742599964142 0.9914933443069458
    outer loop
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
      vertex -92.9990005493164 15 2.5
      vertex -80.9990005493164 15 2.5
    endloop
  endfacet
  facet normal -0.42726847529411316 0.05464344099164009 0.9024720191955566
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.84500122070312 0.9819999933242798 3.0280001163482666
      vertex -94.66799926757812 2.365999937057495 3.0280001163482666
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -92.9990005493164 16 10.5
      vertex -80.9990005493164 16 3.5
      vertex -80.9990005493164 16 10.5
    endloop
  endfacet
  facet normal -0.5463566184043884 -0.07347963005304337 0.8343231678009033
    outer loop
      vertex -94.84500122070312 0.9819999933242798 3.0280001163482666
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
      vertex -93.7249984741211 -0.1469999998807907 3.6619999408721924
    endloop
  endfacet
  facet normal 0.044764354825019836 0.3404058516025543 0.939212441444397
    outer loop
      vertex -39.11600112915039 -51.83599853515625 3.0280001163482666
      vertex -38.83399963378906 -50.7859992980957 2.634000062942505
      vertex -40.5 -51.65399932861328 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5098221898078918 0.20913758873939514 0.834471583366394
    outer loop
      vertex -94.66799926757812 2.365999937057495 3.0280001163482666
      vertex -93.2979965209961 3.1760001182556152 3.6619999408721924
      vertex -94.13800048828125 3.6579999923706055 3.0280001163482666
    endloop
  endfacet
  facet normal -0.21081587672233582 0.5094314813613892 0.8342878222465515
    outer loop
      vertex -43.17300033569336 5.630000114440918 3.0280001163482666
      vertex -42.68899917602539 4.791999816894531 3.6619999408721924
      vertex -41.632999420166016 5.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.04491778090596199 0.3401501178741455 0.9392977952957153
    outer loop
      vertex -40.5 -51.65399932861328 3.0280001163482666
      vertex -38.83399963378906 -50.7859992980957 2.634000062942505
      vertex -40.5 -50.566001892089844 2.634000062942505
    endloop
  endfacet
  facet normal -0.48309147357940674 0.1981721967458725 0.8528484106063843
    outer loop
      vertex -94.66799926757812 2.365999937057495 3.0280001163482666
      vertex -94.13800048828125 3.6579999923706055 3.0280001163482666
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
    endloop
  endfacet
  facet normal -0.07895788550376892 0.08637557178735733 0.9931288361549377
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.06400299072266 5.533999919891357 2.634000062942505
      vertex -94.9990005493164 6.21999979019165 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.9990005493164 15 2.5
      vertex -92.9990005493164 15 2.5
      vertex -88.05599975585938 8.444000244140625 2.5
    endloop
  endfacet
  facet normal -0.437944233417511 -0.05889922380447388 0.8970706462860107
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
      vertex -94.84500122070312 0.9819999933242798 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex 24.48200035095215 -83.93199920654297 10.5
      vertex 24.48200035095215 -83.93199920654297 0
      vertex 25 -84 10.5
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex 25 -84 0
      vertex 25 -84 10.5
      vertex 24.48200035095215 -83.93199920654297 0
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex 24.48200035095215 -83.93199920654297 10.5
      vertex 24 -83.73200225830078 10.5
      vertex 24.48200035095215 -83.93199920654297 0
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex 24.48200035095215 -83.93199920654297 0
      vertex 24 -83.73200225830078 10.5
      vertex 24 -83.73200225830078 0
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex 23.51799964904785 -83.93199920654297 0
      vertex 24 -83.73200225830078 0
      vertex 23.51799964904785 -83.93199920654297 10.5
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex 24 -83.73200225830078 10.5
      vertex 23.51799964904785 -83.93199920654297 10.5
      vertex 24 -83.73200225830078 0
    endloop
  endfacet
  facet normal 0 -0.3832542896270752 0.9236428737640381
    outer loop
      vertex -80.9990005493164 15.5 2.634000062942505
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex 23.51799964904785 -83.93199920654297 10.5
      vertex 23 -84 10.5
      vertex 23 -84 0
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex 23.51799964904785 -83.93199920654297 10.5
      vertex 23 -84 0
      vertex 23.51799964904785 -83.93199920654297 0
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 23 -82 2.5
      vertex -32 -82 10.5
      vertex 23 -82 10.5
    endloop
  endfacet
  facet normal -0.21085025370121002 0.5093573331832886 0.8343244194984436
    outer loop
      vertex -43.17300033569336 5.630000114440918 3.0280001163482666
      vertex -41.632999420166016 5.229000091552734 3.6619999408721924
      vertex -41.882999420166016 6.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 23 83 10.5
      vertex 23 -82 2.5
      vertex 23 -82 10.5
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -93.9990005493164 16.26799964904785 10.5
      vertex -94.41300201416016 16.586000442504883 10.5
      vertex -93.9990005493164 16.26799964904785 3.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -93.9990005493164 16.26799964904785 10.5
      vertex -93.9990005493164 16.26799964904785 3.5
      vertex -93.51699829101562 16.06800079345703 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -93.51699829101562 16.06800079345703 3.5
      vertex -93.51699829101562 16.06800079345703 10.5
      vertex -93.9990005493164 16.26799964904785 3.5
    endloop
  endfacet
  facet normal 0.21081587672233582 0.5094314813613892 0.8342878222465515
    outer loop
      vertex -38.310001373291016 -53.20800018310547 3.6619999408721924
      vertex -37.82600021362305 -52.369998931884766 3.0280001163482666
      vertex -39.36600112915039 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal -0.44330033659935 0.5776916742324829 0.6853883266448975
    outer loop
      vertex -42.29100036621094 4.1020002365112305 4.500999927520752
      vertex -42.68899917602539 4.791999816894531 3.6619999408721924
      vertex -43.59600067138672 4.0960001945495605 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3357207775115967 0.43749818205833435 0.8341983556747437
    outer loop
      vertex -44.279998779296875 4.78000020980835 3.0280001163482666
      vertex -43.59600067138672 4.0960001945495605 3.6619999408721924
      vertex -42.68899917602539 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6046614646911621 -0.7856866717338562 0.13069437444210052
    outer loop
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
      vertex -94.01599884033203 16.238000869750977 3.240999937057495
      vertex -93.9990005493164 16.26799964904785 3.5
    endloop
  endfacet
  facet normal -0.33575916290283203 0.4372769296169281 0.8342989087104797
    outer loop
      vertex -44.279998779296875 4.78000020980835 3.0280001163482666
      vertex -42.68899917602539 4.791999816894531 3.6619999408721924
      vertex -43.17300033569336 5.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal 0.0718642920255661 0.5464845299720764 0.8343801498413086
    outer loop
      vertex -39.11600112915039 -51.83599853515625 3.0280001163482666
      vertex -40.5 -51.65399932861328 3.0280001163482666
      vertex -40.5 -52.62200164794922 3.6619999408721924
    endloop
  endfacet
  facet normal -0.37949734926223755 -0.9160280823707581 0.12990117073059082
    outer loop
      vertex -93.51699829101562 16.06800079345703 3.5
      vertex -94.01599884033203 16.238000869750977 3.240999937057495
      vertex -93.5260009765625 16.03499984741211 3.240999937057495
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -92.9990005493164 16 3.5
      vertex -92.9990005493164 16 10.5
      vertex -93.51699829101562 16.06800079345703 3.5
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -92.9990005493164 16 10.5
      vertex -93.51699829101562 16.06800079345703 10.5
      vertex -93.51699829101562 16.06800079345703 3.5
    endloop
  endfacet
  facet normal 0.07181254774332047 0.546546459197998 0.8343439698219299
    outer loop
      vertex -40.5 -52.62200164794922 3.6619999408721924
      vertex -39.36600112915039 -52.770999908447266 3.6619999408721924
      vertex -39.11600112915039 -51.83599853515625 3.0280001163482666
    endloop
  endfacet
  facet normal 0.37283676862716675 0.4851985573768616 0.7909330725669861
    outer loop
      vertex 82.14600372314453 84.98600006103516 2.7929999828338623
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
      vertex 82.76699829101562 84.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal 0.7364738583564758 0.3049774169921875 0.6038170456886292
    outer loop
      vertex 82.99800109863281 83.87273406982422 2.915163993835449
      vertex 82.99800109863281 84.11460876464844 2.7929999828338623
      vertex 82.8479995727539 84.06700134277344 3
    endloop
  endfacet
  facet normal -0.3799514174461365 -0.9156829118728638 0.13100256025791168
    outer loop
      vertex -94.01599884033203 16.238000869750977 3.240999937057495
      vertex -93.51699829101562 16.06800079345703 3.5
      vertex -93.9990005493164 16.26799964904785 3.5
    endloop
  endfacet
  facet normal 0.9249957203865051 0.3799774944782257 0
    outer loop
      vertex -41.36600112915039 -57.5 5.5
      vertex -41.36600112915039 -57.5 0
      vertex -41.46500015258789 -57.25899887084961 0
    endloop
  endfacet
  facet normal -0.1290687471628189 -0.9832001328468323 0.1290687471628189
    outer loop
      vertex -92.9990005493164 16 3.5
      vertex -93.51699829101562 16.06800079345703 3.5
      vertex -92.9990005493164 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal 0.632382333278656 0.48460453748703003 0.604360044002533
    outer loop
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
      vertex 82.50900268554688 84.50900268554688 3
      vertex 82.98500061035156 84.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal -0.3043098747730255 -0.7362335324287415 0.6044465899467468
    outer loop
      vertex -36.06700134277344 15.616000175476074 3
      vertex -36.516998291015625 15.802000045776367 3
      vertex -36.55799865722656 15.64900016784668 2.7929999828338623
    endloop
  endfacet
  facet normal 0.6325322389602661 0.4851321876049042 0.6037794947624207
    outer loop
      vertex 82.50900268554688 84.50900268554688 3
      vertex 82.8479995727539 84.06700134277344 3
      vertex 82.98500061035156 84.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal -0.304902583360672 -0.734619140625 0.6061098575592041
    outer loop
      vertex -36.06700134277344 15.616000175476074 3
      vertex -36.55799865722656 15.64900016784668 2.7929999828338623
      vertex -36.145999908447266 15.477999687194824 2.7929999828338623
    endloop
  endfacet
  facet normal 0.5462685823440552 0.07386278361082077 0.8343470096588135
    outer loop
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
      vertex -84.15299987792969 -56.981998443603516 3.0280001163482666
      vertex -84.33999633789062 -55.5989990234375 3.0280001163482666
    endloop
  endfacet
  facet normal 0.7333922982215881 0.5626739263534546 0.3814889192581177
    outer loop
      vertex 82.8479995727539 84.06700134277344 3
      vertex 82.43800354003906 84.43800354003906 3.240999937057495
      vertex 82.76100158691406 84.01699829101562 3.240999937057495
    endloop
  endfacet
  facet normal -0.23480144143104553 -0.5657204389572144 0.7904610633850098
    outer loop
      vertex -36.145999908447266 15.477999687194824 2.7929999828338623
      vertex -36.55799865722656 15.64900016784668 2.7929999828338623
      vertex -36.25 15.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal 0.3473118841648102 0.3568688631057739 0.8671903610229492
    outer loop
      vertex 82.14600372314453 84.98600006103516 2.7929999828338623
      vertex 82.76699829101562 84.76799774169922 2.634000062942505
      vertex 82.62100219726562 85 2.5969998836517334
    endloop
  endfacet
  facet normal -0.23514387011528015 -0.5659129023551941 0.7902214527130127
    outer loop
      vertex -36.55799865722656 15.64900016784668 2.7929999828338623
      vertex -36.611000061035156 15.449000358581543 2.634000062942505
      vertex -36.25 15.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal 0.4847888648509979 0.3715013563632965 0.7918121814727783
    outer loop
      vertex 82.98500061035156 84.14600372314453 2.7929999828338623
      vertex 82.99800109863281 84.15351104736328 2.7815165519714355
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
    endloop
  endfacet
  facet normal -0.11370406299829483 -0.047108061611652374 0.9923971891403198
    outer loop
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -46.07099914550781 -60.21699905395508 2.634000062942505
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
    endloop
  endfacet
  facet normal 0.5462456941604614 0.0738300308585167 0.8343648910522461
    outer loop
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
      vertex -85.12100219726562 -56.98500061035156 3.6619999408721924
      vertex -84.15299987792969 -56.981998443603516 3.0280001163482666
    endloop
  endfacet
  facet normal 0.485491007566452 0.37302204966545105 0.7906662225723267
    outer loop
      vertex 82.99800109863281 84.3638916015625 2.6828105449676514
      vertex 82.99800109863281 84.46735382080078 2.634000062942505
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
    endloop
  endfacet
  facet normal 0.21407334506511688 0.2837849259376526 0.9346864223480225
    outer loop
      vertex 82.93099975585938 85 2.5260000228881836
      vertex 82.62100219726562 85 2.5969998836517334
      vertex 82.76699829101562 84.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal 0.3165718615055084 0.132232666015625 0.9393065571784973
    outer loop
      vertex -83.29000091552734 -55.31399917602539 2.634000062942505
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
      vertex -84.33999633789062 -55.5989990234375 3.0280001163482666
    endloop
  endfacet
  facet normal 0.29319244623184204 0.22527141869068146 0.9291345477104187
    outer loop
      vertex 82.93099975585938 85 2.5260000228881836
      vertex 82.76699829101562 84.76799774169922 2.634000062942505
      vertex 82.99800109863281 84.7852554321289 2.5569231510162354
    endloop
  endfacet
  facet normal -0.3170148432254791 -0.13134054839611053 0.9392822980880737
    outer loop
      vertex -45.12900161743164 -59.67300033569336 3.0280001163482666
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
      vertex -46.07099914550781 -60.21699905395508 2.634000062942505
    endloop
  endfacet
  facet normal -0.06735207140445709 0.087761789560318 0.993861973285675
    outer loop
      vertex -45.16299819946289 6.979000091552734 2.5
      vertex -45.04899978637695 5.548999786376953 2.634000062942505
      vertex -43.715999603271484 6.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal -0.12140267342329025 -0.9162108302116394 0.38186272978782654
    outer loop
      vertex -36.516998291015625 15.802000045776367 3
      vertex -36.49100112915039 15.89900016784668 3.240999937057495
      vertex -37 15.866000175476074 3
    endloop
  endfacet
  facet normal 0.34026017785072327 0.04600770026445389 0.9392051696777344
    outer loop
      vertex -84.33999633789062 -55.5989990234375 3.0280001163482666
      vertex -84.15299987792969 -56.981998443603516 3.0280001163482666
      vertex -83.06600189208984 -56.97800064086914 2.634000062942505
    endloop
  endfacet
  facet normal -0.10365473479032516 -0.7899205684661865 0.6043849587440491
    outer loop
      vertex -36.55799865722656 15.64900016784668 2.7929999828338623
      vertex -36.516998291015625 15.802000045776367 3
      vertex -37 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.10217751562595367 0.08473146706819534 0.9911510348320007
    outer loop
      vertex -45.16299819946289 6.979000091552734 2.5
      vertex -47.02799987792969 4.730000019073486 2.5
      vertex -45.04899978637695 5.548999786376953 2.634000062942505
    endloop
  endfacet
  facet normal 0.34003591537475586 0.04577406495809555 0.9392977952957153
    outer loop
      vertex -83.29000091552734 -55.31399917602539 2.634000062942505
      vertex -84.33999633789062 -55.5989990234375 3.0280001163482666
      vertex -83.06600189208984 -56.97800064086914 2.634000062942505
    endloop
  endfacet
  facet normal -0.27227458357810974 0.20881763100624084 0.9392879009246826
    outer loop
      vertex -45.12900161743164 3.6730000972747803 3.0280001163482666
      vertex -44.279998779296875 4.78000020980835 3.0280001163482666
      vertex -46.07099914550781 4.2170000076293945 2.634000062942505
    endloop
  endfacet
  facet normal -0.2723022699356079 0.20892861485481262 0.9392551779747009
    outer loop
      vertex -46.07099914550781 4.2170000076293945 2.634000062942505
      vertex -44.279998779296875 4.78000020980835 3.0280001163482666
      vertex -45.04899978637695 5.548999786376953 2.634000062942505
    endloop
  endfacet
  facet normal -0.0984477698802948 0.07553575187921524 0.9922713041305542
    outer loop
      vertex -47.02799987792969 4.730000019073486 2.5
      vertex -46.07099914550781 4.2170000076293945 2.634000062942505
      vertex -45.04899978637695 5.548999786376953 2.634000062942505
    endloop
  endfacet
  facet normal -0.07969111949205399 -0.6073012948036194 0.7904646992683411
    outer loop
      vertex -37 15.706999778747559 2.7929999828338623
      vertex -36.611000061035156 15.449000358581543 2.634000062942505
      vertex -36.55799865722656 15.64900016784668 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -45.16299819946289 6.979000091552734 2.5
      vertex -48.999000549316406 15 2.5
      vertex -47.02799987792969 4.730000019073486 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.47200012207031 7.97599983215332 2.5
      vertex -48.999000549316406 15 2.5
      vertex -45.16299819946289 6.979000091552734 2.5
    endloop
  endfacet
  facet normal -0.733528196811676 -0.5623115301132202 0.38176190853118896
    outer loop
      vertex -35.297000885009766 14.982999801635742 3.240999937057495
      vertex -35.60900115966797 15.390000343322754 3.240999937057495
      vertex -35.68000030517578 15.319000244140625 3
    endloop
  endfacet
  facet normal 0.12232806533575058 0.01646723970770836 0.992353081703186
    outer loop
      vertex -81.97599792480469 -57 2.5
      vertex -83.29000091552734 -55.31399917602539 2.634000062942505
      vertex -83.06600189208984 -56.97800064086914 2.634000062942505
    endloop
  endfacet
  facet normal -0.7335240244865417 -0.5624951124191284 0.38149935007095337
    outer loop
      vertex -35.297000885009766 14.982999801635742 3.240999937057495
      vertex -35.68000030517578 15.319000244140625 3
      vertex -35.38399887084961 14.932999610900879 3
    endloop
  endfacet
  facet normal -0.5778562426567078 0.4427895247936249 0.685579776763916
    outer loop
      vertex -43.03200149536133 3.5329999923706055 4.500999927520752
      vertex -43.59600067138672 4.0960001945495605 3.6619999408721924
      vertex -44.29100036621094 3.188999891281128 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5777515769004822 0.4438253343105316 0.6849979758262634
    outer loop
      vertex -43.03200149536133 3.5329999923706055 4.500999927520752
      vertex -44.29100036621094 3.188999891281128 3.6619999408721924
      vertex -43.60200119018555 2.7909998893737793 4.500999927520752
    endloop
  endfacet
  facet normal 0.12911927700042725 0.021836688742041588 0.9913886189460754
    outer loop
      vertex -83.29000091552734 -55.31399917602539 2.634000062942505
      vertex -81.97599792480469 -57 2.5
      vertex -82.4469985961914 -54.21500015258789 2.5
    endloop
  endfacet
  facet normal -0.44339895248413086 0.5774316787719727 0.6855435967445374
    outer loop
      vertex -43.03200149536133 3.5329999923706055 4.500999927520752
      vertex -42.29100036621094 4.1020002365112305 4.500999927520752
      vertex -43.59600067138672 4.0960001945495605 3.6619999408721924
    endloop
  endfacet
  facet normal -0.4375992715358734 0.33561134338378906 0.8341893553733826
    outer loop
      vertex -44.279998779296875 4.78000020980835 3.0280001163482666
      vertex -45.12900161743164 3.6730000972747803 3.0280001163482666
      vertex -43.59600067138672 4.0960001945495605 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6323212385177612 -0.48543643951416016 0.6037560105323792
    outer loop
      vertex -35.38399887084961 14.932999610900879 3
      vertex -35.79199981689453 15.206999778747559 2.7929999828338623
      vertex -35.520999908447266 14.854000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal 0.2765670120716095 0.6735744476318359 0.6854255199432373
    outer loop
      vertex -87.322998046875 -53.20100021362305 3.6619999408721924
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -88.58399963378906 -53.5369987487793 4.500999927520752
    endloop
  endfacet
  facet normal 0.5272573828697205 -0.6866392493247986 0.5005258917808533
    outer loop
      vertex -39 -1.5980000495910645 5.5
      vertex -38.70800018310547 -2.1019999980926514 4.500999927520752
      vertex -37.96699905395508 -1.5329999923706055 4.500999927520752
    endloop
  endfacet
  facet normal -0.4375706613063812 0.3352939486503601 0.8343319892883301
    outer loop
      vertex -45.12900161743164 3.6730000972747803 3.0280001163482666
      vertex -44.29100036621094 3.188999891281128 3.6619999408721924
      vertex -43.59600067138672 4.0960001945495605 3.6619999408721924
    endloop
  endfacet
  facet normal 0.6867327690124512 -0.5275440216064453 0.5000954270362854
    outer loop
      vertex -37.96699905395508 -1.5329999923706055 4.500999927520752
      vertex -37.39699935913086 -0.7910000085830688 4.500999927520752
      vertex -38.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.6867461204528809 -0.5275006294250488 0.5001228451728821
    outer loop
      vertex -37.39699935913086 -0.7910000085830688 4.500999927520752
      vertex -37.9010009765625 -0.5 5.5
      vertex -38.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.3341551423072815 0.43830737471580505 0.8344021439552307
    outer loop
      vertex -86.41400146484375 -53.89400100708008 3.6619999408721924
      vertex -85.73200225830078 -53.207000732421875 3.0280001163482666
      vertex -87.322998046875 -53.20100021362305 3.6619999408721924
    endloop
  endfacet
  facet normal -0.7433530688285828 0.173817977309227 0.6459206938743591
    outer loop
      vertex -35.20399856567383 -53.70399856567383 3.4000000953674316
      vertex -35.24800109863281 -52.349998474121094 2.984999895095825
      vertex -35.30799865722656 -53.7400016784668 3.2899999618530273
    endloop
  endfacet
  facet normal -0.4843055009841919 -0.632635235786438 0.6043350696563721
    outer loop
      vertex -35.68000030517578 15.319000244140625 3
      vertex -36.145999908447266 15.477999687194824 2.7929999828338623
      vertex -35.79199981689453 15.206999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7437066435813904 0.22498908638954163 0.6295080184936523
    outer loop
      vertex -35.30799865722656 -53.7400016784668 3.2899999618530273
      vertex -35.257999420166016 -55.108001708984375 3.8380000591278076
      vertex -35.20399856567383 -53.70399856567383 3.4000000953674316
    endloop
  endfacet
  facet normal -0.672881543636322 0.27880969643592834 0.6851974725723267
    outer loop
      vertex -43.959999084472656 1.9270000457763672 4.500999927520752
      vertex -43.60200119018555 2.7909998893737793 4.500999927520752
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5627014636993408 -0.7332170605659485 0.381785124540329
    outer loop
      vertex -35.60900115966797 15.390000343322754 3.240999937057495
      vertex -36.06700134277344 15.616000175476074 3
      vertex -35.68000030517578 15.319000244140625 3
    endloop
  endfacet
  facet normal 0.43595877289772034 0.337236225605011 0.8343930244445801
    outer loop
      vertex -86.41400146484375 -53.89400100708008 3.6619999408721924
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
      vertex -85.73200225830078 -53.207000732421875 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6729307770729065 0.2791133224964142 0.6850255131721497
    outer loop
      vertex -43.60200119018555 2.7909998893737793 4.500999927520752
      vertex -44.29100036621094 3.188999891281128 3.6619999408721924
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
    endloop
  endfacet
  facet normal -0.4844326972961426 -0.6312304735183716 0.6057004332542419
    outer loop
      vertex -35.68000030517578 15.319000244140625 3
      vertex -36.06700134277344 15.616000175476074 3
      vertex -36.145999908447266 15.477999687194824 2.7929999828338623
    endloop
  endfacet
  facet normal 0.43594586849212646 0.3370864689350128 0.8344602584838867
    outer loop
      vertex -86.41400146484375 -53.89400100708008 3.6619999408721924
      vertex -85.71499633789062 -54.79800033569336 3.6619999408721924
      vertex -84.87799835205078 -54.31100082397461 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6322124004364014 -0.4848053455352783 0.6043767333030701
    outer loop
      vertex -35.38399887084961 14.932999610900879 3
      vertex -35.68000030517578 15.319000244140625 3
      vertex -35.79199981689453 15.206999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7360524535179138 -0.3058706820011139 0.6038790941238403
    outer loop
      vertex -35.196998596191406 14.482999801635742 3
      vertex -35.38399887084961 14.932999610900879 3
      vertex -35.520999908447266 14.854000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7348140478134155 -0.30319997668266296 0.6067273616790771
    outer loop
      vertex -35.196998596191406 14.482999801635742 3
      vertex -35.520999908447266 14.854000091552734 2.7929999828338623
      vertex -35.35100173950195 14.442000389099121 2.7929999828338623
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -89.9990005493164 -56.13399887084961 5.5
      vertex -89.9990005493164 -56.13399887084961 0
      vertex -89.75800323486328 -56.034000396728516 0
    endloop
  endfacet
  facet normal -0.31718528270721436 -0.13164788484573364 0.9391817450523376
    outer loop
      vertex -45.66400146484375 -58.38399887084961 3.0280001163482666
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
      vertex -45.12900161743164 -59.67300033569336 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 -56 5.5
      vertex -89.4990005493164 -56 0
      vertex -89.23999786376953 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal -0.5091621279716492 -0.21132797002792358 0.8343227505683899
    outer loop
      vertex -45.66400146484375 -58.38399887084961 3.0280001163482666
      vertex -45.12900161743164 -59.67300033569336 3.0280001163482666
      vertex -44.29100036621094 -59.18899917602539 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -89.23999786376953 -56.034000396728516 0
      vertex -88.9990005493164 -56.13399887084961 0
      vertex -89.23999786376953 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal -0.7221735119819641 0.09497250616550446 0.6851610541343689
    outer loop
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
      vertex -44.87799835205078 1 3.6619999408721924
      vertex -44.082000732421875 1 4.500999927520752
    endloop
  endfacet
  facet normal -0.7221212983131409 0.09503646194934845 0.685207188129425
    outer loop
      vertex -44.082000732421875 1 4.500999927520752
      vertex -43.959999084472656 1.9270000457763672 4.500999927520752
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -88.63300323486328 -56.5 5.5
      vertex -88.63300323486328 -56.5 0
      vertex -88.53299713134766 -56.74100112915039 0
    endloop
  endfacet
  facet normal -0.7221735119819641 -0.09497250616550446 0.6851610541343689
    outer loop
      vertex -44.082000732421875 1 4.500999927520752
      vertex -44.87799835205078 1 3.6619999408721924
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 -56 5.5
      vertex -89.75800323486328 -56.034000396728516 0
      vertex -89.4990005493164 -56 0
    endloop
  endfacet
  facet normal -0.7221212983131409 -0.09503646194934845 0.685207188129425
    outer loop
      vertex -44.082000732421875 1 4.500999927520752
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
      vertex -43.959999084472656 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.23999786376953 -56.034000396728516 0
      vertex -89.23999786376953 -56.034000396728516 5.5
      vertex -89.4990005493164 -56 0
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -88.9990005493164 -56.13399887084961 5.5
      vertex -89.23999786376953 -56.034000396728516 5.5
      vertex -88.9990005493164 -56.13399887084961 0
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -88.79199981689453 -56.292999267578125 0
      vertex -88.79199981689453 -56.292999267578125 5.5
      vertex -88.9990005493164 -56.13399887084961 0
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -88.9990005493164 -56.13399887084961 5.5
      vertex -88.9990005493164 -56.13399887084961 0
      vertex -88.79199981689453 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -88.63300323486328 -56.5 5.5
      vertex -88.79199981689453 -56.292999267578125 5.5
      vertex -88.63300323486328 -56.5 0
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -88.79199981689453 -56.292999267578125 0
      vertex -88.63300323486328 -56.5 0
      vertex -88.79199981689453 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -88.4990005493164 -57 5.5
      vertex -88.53299713134766 -56.74100112915039 0
      vertex -88.4990005493164 -57 0
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -41.207000732421875 0.2930000126361847 0
      vertex -41.207000732421875 0.2930000126361847 5.5
      vertex -41 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -88.53299713134766 -57.25899887084961 0
      vertex -88.53299713134766 -57.25899887084961 5.5
      vertex -88.4990005493164 -57 0
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -88.4990005493164 -57 5.5
      vertex -88.4990005493164 -57 0
      vertex -88.53299713134766 -57.25899887084961 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.79199981689453 0.2930000126361847 5.5
      vertex -40 0.1340000033378601 5.5
      vertex -39 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -41.207000732421875 0.2930000126361847 0
      vertex -41.36600112915039 0.5 0
      vertex -41.36600112915039 0.5 5.5
    endloop
  endfacet
  facet normal 0.9249957203865051 0.3799774944782257 0
    outer loop
      vertex -41.36600112915039 0.5 0
      vertex -41.46500015258789 0.7409999966621399 0
      vertex -41.36600112915039 0.5 5.5
    endloop
  endfacet
  facet normal 0.9909924268722534 0.133917897939682 0
    outer loop
      vertex -41.46500015258789 0.7409999966621399 5.5
      vertex -41.46500015258789 0.7409999966621399 0
      vertex -41.5 1 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -80.9990005493164 16 3.5
      vertex -92.9990005493164 16 10.5
      vertex -92.9990005493164 16 3.5
    endloop
  endfacet
  facet normal 0.5269486308097839 -0.6871321797370911 0.5001745223999023
    outer loop
      vertex -38.37799835205078 -1.121000051498413 5.5
      vertex -39 -1.5980000495910645 5.5
      vertex -37.96699905395508 -1.5329999923706055 4.500999927520752
    endloop
  endfacet
  facet normal -0.0984477698802948 -0.07553575187921524 0.9922713041305542
    outer loop
      vertex -45.04899978637695 -61.54899978637695 2.634000062942505
      vertex -46.07099914550781 -60.21699905395508 2.634000062942505
      vertex -47.02799987792969 -60.72999954223633 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.722999572753906 -1.8980000019073486 5.5
      vertex -39 -1.5980000495910645 5.5
      vertex -40.24100112915039 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.9010009765625 -0.5 5.5
      vertex -39.79199981689453 0.2930000126361847 5.5
      vertex -38.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39 -1.5980000495910645 5.5
      vertex -38.37799835205078 -1.121000051498413 5.5
      vertex -39.79199981689453 0.2930000126361847 5.5
    endloop
  endfacet
  facet normal 0.3819020092487335 -0.9242027997970581 0
    outer loop
      vertex -40.757999420166016 1.965999960899353 0
      vertex -40.757999420166016 1.965999960899353 5.5
      vertex -41 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal -0.12872453033924103 -0.9831569194793701 0.1297401487827301
    outer loop
      vertex -93.51699829101562 16.06800079345703 3.5
      vertex -93.5260009765625 16.03499984741211 3.240999937057495
      vertex -92.9990005493164 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal 0.3819020092487335 0.9242027997970581 0
    outer loop
      vertex -41 0.1340000033378601 5.5
      vertex -40.757999420166016 0.03400000184774399 5.5
      vertex -41 0.1340000033378601 0
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -41 0.1340000033378601 5.5
      vertex -41 0.1340000033378601 0
      vertex -41.207000732421875 0.2930000126361847 0
    endloop
  endfacet
  facet normal -0.3741196393966675 0.33479389548301697 0.8648396134376526
    outer loop
      vertex -35.38600158691406 -55.14899826049805 3.7269999980926514
      vertex -35.73500061035156 -53.816001892089844 3.059999942779541
      vertex -35.89799880981445 -55.220001220703125 3.5329999923706055
    endloop
  endfacet
  facet normal 0 -0.9914933443069458 0.13015742599964142
    outer loop
      vertex -92.9990005493164 16 3.5
      vertex -92.9990005493164 15.965999603271484 3.240999937057495
      vertex -80.9990005493164 16 3.5
    endloop
  endfacet
  facet normal 0 -0.9914933443069458 0.13015742599964142
    outer loop
      vertex -80.9990005493164 15.965999603271484 3.240999937057495
      vertex -80.9990005493164 16 3.5
      vertex -92.9990005493164 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal 0.9249957203865051 0.3799774944782257 0
    outer loop
      vertex -41.46500015258789 0.7409999966621399 5.5
      vertex -41.36600112915039 0.5 5.5
      vertex -41.46500015258789 0.7409999966621399 0
    endloop
  endfacet
  facet normal 0.11286836862564087 -0.8585397005081177 0.5001702904701233
    outer loop
      vertex -39.571998596191406 -2.4600000381469727 4.500999927520752
      vertex -40.5 -2 5.5
      vertex -40.5 -2.5820000171661377 4.500999927520752
    endloop
  endfacet
  facet normal -0.6788224577903748 0.2515423595905304 0.6898742318153381
    outer loop
      vertex -35.30799865722656 -53.7400016784668 3.2899999618530273
      vertex -35.38600158691406 -55.14899826049805 3.7269999980926514
      vertex -35.257999420166016 -55.108001708984375 3.8380000591278076
    endloop
  endfacet
  facet normal 0.9909924268722534 -0.133917897939682 0
    outer loop
      vertex -41.46500015258789 1.2589999437332153 5.5
      vertex -41.5 1 0
      vertex -41.46500015258789 1.2589999437332153 0
    endloop
  endfacet
  facet normal 0.9249957203865051 -0.3799774944782257 0
    outer loop
      vertex -41.36600112915039 1.5 0
      vertex -41.36600112915039 1.5 5.5
      vertex -41.46500015258789 1.2589999437332153 0
    endloop
  endfacet
  facet normal 0.9249957203865051 -0.3799774944782257 0
    outer loop
      vertex -41.46500015258789 1.2589999437332153 5.5
      vertex -41.46500015258789 1.2589999437332153 0
      vertex -41.36600112915039 1.5 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -41.207000732421875 1.7070000171661377 5.5
      vertex -41.36600112915039 1.5 5.5
      vertex -41.207000732421875 1.7070000171661377 0
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -41.36600112915039 1.5 0
      vertex -41.207000732421875 1.7070000171661377 0
      vertex -41.36600112915039 1.5 5.5
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -41 1.8660000562667847 0
      vertex -41 1.8660000562667847 5.5
      vertex -41.207000732421875 1.7070000171661377 0
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -41.207000732421875 1.7070000171661377 5.5
      vertex -41.207000732421875 1.7070000171661377 0
      vertex -41 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal -0.4933954179286957 0.28246206045150757 0.8226640224456787
    outer loop
      vertex -35.30799865722656 -53.7400016784668 3.2899999618530273
      vertex -35.73500061035156 -53.816001892089844 3.059999942779541
      vertex -35.38600158691406 -55.14899826049805 3.7269999980926514
    endloop
  endfacet
  facet normal 0.1127147451043129 -0.8586211800575256 0.5000650882720947
    outer loop
      vertex -39.571998596191406 -2.4600000381469727 4.500999927520752
      vertex -39.722999572753906 -1.8980000019073486 5.5
      vertex -40.5 -2 5.5
    endloop
  endfacet
  facet normal 0.3819020092487335 -0.9242027997970581 0
    outer loop
      vertex -41 1.8660000562667847 5.5
      vertex -41 1.8660000562667847 0
      vertex -40.757999420166016 1.965999960899353 0
    endloop
  endfacet
  facet normal -0.3170148432254791 0.13134054839611053 0.9392822980880737
    outer loop
      vertex -46.07099914550781 4.2170000076293945 2.634000062942505
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
      vertex -45.12900161743164 3.6730000972747803 3.0280001163482666
    endloop
  endfacet
  facet normal 0.3314758837223053 -0.7999864816665649 0.5001453757286072
    outer loop
      vertex -39.571998596191406 -2.4600000381469727 4.500999927520752
      vertex -38.70800018310547 -2.1019999980926514 4.500999927520752
      vertex -39.722999572753906 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0.3318139612674713 -0.7996716499328613 0.5004246234893799
    outer loop
      vertex -39 -1.5980000495910645 5.5
      vertex -39.722999572753906 -1.8980000019073486 5.5
      vertex -38.70800018310547 -2.1019999980926514 4.500999927520752
    endloop
  endfacet
  facet normal 0.4435596466064453 -0.577640950679779 0.6852633357048035
    outer loop
      vertex -37.40399932861328 -2.0959999561309814 3.6619999408721924
      vertex -37.96699905395508 -1.5329999923706055 4.500999927520752
      vertex -38.70800018310547 -2.1019999980926514 4.500999927520752
    endloop
  endfacet
  facet normal -0.11370406299829483 0.047108061611652374 0.9923971891403198
    outer loop
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
      vertex -46.07099914550781 4.2170000076293945 2.634000062942505
      vertex -47.02799987792969 4.730000019073486 2.5
    endloop
  endfacet
  facet normal -0.48481395840644836 -0.6295940279960632 0.6070970296859741
    outer loop
      vertex -94.14600372314453 16.013999938964844 2.7929999828338623
      vertex -94.06600189208984 16.152000427246094 3
      vertex -94.62000274658203 16.378999710083008 2.7929999828338623
    endloop
  endfacet
  facet normal 0.0748867392539978 0.3273560106754303 0.9419288635253906
    outer loop
      vertex -36.1609992980957 -55.88399887084961 3.7690000534057617
      vertex -35.97999954223633 -55.88800048828125 3.75600004196167
      vertex -36.06999969482422 -55.220001220703125 3.5309998989105225
    endloop
  endfacet
  facet normal -0.3404421806335449 0.044769130647182465 0.9391990303993225
    outer loop
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -45.66400146484375 2.384000062942505 3.0280001163482666
    endloop
  endfacet
  facet normal -0.4848547875881195 -0.632170557975769 0.6043808460235596
    outer loop
      vertex -94.62000274658203 16.378999710083008 2.7929999828338623
      vertex -94.06600189208984 16.152000427246094 3
      vertex -94.50800323486328 16.490999221801758 3
    endloop
  endfacet
  facet normal -0.3404288589954376 0.04477712884545326 0.9392035007476807
    outer loop
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
      vertex -46.93299865722656 1 2.634000062942505
    endloop
  endfacet
  facet normal 0.42448896169662476 -0.20448386669158936 0.8820405006408691
    outer loop
      vertex -36.141998291015625 -0.2549999952316284 3.7219998836517334
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
    endloop
  endfacet
  facet normal 0.2347913682460785 0.291384220123291 0.9273447394371033
    outer loop
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
      vertex -36.71900177001953 -53.220001220703125 3.0280001163482666
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
    endloop
  endfacet
  facet normal -0.07978200167417526 -0.6072818040847778 0.7904704809188843
    outer loop
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -93.59300231933594 15.78499984741211 2.7929999828338623
      vertex -93.64600372314453 15.585000038146973 2.634000062942505
    endloop
  endfacet
  facet normal -0.31718528270721436 0.13164788484573364 0.9391817450523376
    outer loop
      vertex -45.12900161743164 3.6730000972747803 3.0280001163482666
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
      vertex -45.66400146484375 2.384000062942505 3.0280001163482666
    endloop
  endfacet
  facet normal -0.07973539084196091 -0.6072156429290771 0.7905260324478149
    outer loop
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -92.9990005493164 15.706999778747559 2.7929999828338623
      vertex -93.59300231933594 15.78499984741211 2.7929999828338623
    endloop
  endfacet
  facet normal -0.3282952606678009 0.242768332362175 0.9128448963165283
    outer loop
      vertex -35.604000091552734 -52.39799880981445 2.7300000190734863
      vertex -35.733001708984375 -52.40700149536133 2.686000108718872
      vertex -35.73500061035156 -53.816001892089844 3.059999942779541
    endloop
  endfacet
  facet normal -0.15346558392047882 0.04073215276002884 0.9873141646385193
    outer loop
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
      vertex -47.02799987792969 4.730000019073486 2.5
      vertex -48.018001556396484 1 2.5
    endloop
  endfacet
  facet normal -0.19216535985469818 0.2520257234573364 0.9484490156173706
    outer loop
      vertex -35.73500061035156 -53.816001892089844 3.059999942779541
      vertex -35.733001708984375 -52.40700149536133 2.686000108718872
      vertex -35.8849983215332 -53.82500076293945 3.0320000648498535
    endloop
  endfacet
  facet normal -0.19229206442832947 0.3332815170288086 0.9230098724365234
    outer loop
      vertex -35.89799880981445 -55.220001220703125 3.5329999923706055
      vertex -35.73500061035156 -53.816001892089844 3.059999942779541
      vertex -35.8849983215332 -53.82500076293945 3.0320000648498535
    endloop
  endfacet
  facet normal -0.010942515917122364 0.3380727469921112 0.9410563707351685
    outer loop
      vertex -35.89799880981445 -55.220001220703125 3.5329999923706055
      vertex -35.8849983215332 -53.82500076293945 3.0320000648498535
      vertex -36.06999969482422 -55.220001220703125 3.5309998989105225
    endloop
  endfacet
  facet normal -0.12255513668060303 0.01611986570060253 0.99233078956604
    outer loop
      vertex -48.018001556396484 1 2.5
      vertex -46.93299865722656 1 2.634000062942505
      vertex -46.7140007019043 2.6649999618530273 2.634000062942505
    endloop
  endfacet
  facet normal -0.4931298494338989 0.2401484251022339 0.8361529111862183
    outer loop
      vertex -35.604000091552734 -52.39799880981445 2.7300000190734863
      vertex -35.73500061035156 -53.816001892089844 3.059999942779541
      vertex -35.30799865722656 -53.7400016784668 3.2899999618530273
    endloop
  endfacet
  facet normal 0.0525725893676281 -0.2705326974391937 0.961274266242981
    outer loop
      vertex -36.141998291015625 -0.2549999952316284 3.7219998836517334
      vertex -35.96200180053711 -0.25200000405311584 3.7130000591278076
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
    endloop
  endfacet
  facet normal 0.29319244623184204 0.22527141869068146 0.9291345477104187
    outer loop
      vertex 82.99800109863281 84.7852554321289 2.5569231510162354
      vertex 82.76699829101562 84.76799774169922 2.634000062942505
      vertex 82.99800109863281 84.46735382080078 2.634000062942505
    endloop
  endfacet
  facet normal -0.23468473553657532 -0.5660595893859863 0.7902528643608093
    outer loop
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -93.64600372314453 15.585000038146973 2.634000062942505
      vertex -93.59300231933594 15.78499984741211 2.7929999828338623
    endloop
  endfacet
  facet normal 0.485491007566452 0.37302204966545105 0.7906662225723267
    outer loop
      vertex 82.76699829101562 84.76799774169922 2.634000062942505
      vertex 82.62100219726562 84.62100219726562 2.7929999828338623
      vertex 82.99800109863281 84.46735382080078 2.634000062942505
    endloop
  endfacet
  facet normal -0.2346349060535431 -0.5666074156761169 0.7898749709129333
    outer loop
      vertex -94.14600372314453 16.013999938964844 2.7929999828338623
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -93.59300231933594 15.78499984741211 2.7929999828338623
    endloop
  endfacet
  facet normal 0.08373674750328064 0.16757655143737793 0.9822964072227478
    outer loop
      vertex 82.99800109863281 85 2.5202884674072266
      vertex 82.93099975585938 85 2.5260000228881836
      vertex 82.99800109863281 84.7852554321289 2.5569231510162354
    endloop
  endfacet
  facet normal -0.26644349098205566 -0.2283092886209488 0.9364201426506042
    outer loop
      vertex -35.45500183105469 0.40700000524520874 4.053999900817871
      vertex -36.0359992980957 0.43700000643730164 3.8959999084472656
      vertex -35.41699981689453 -0.3100000023841858 3.890000104904175
    endloop
  endfacet
  facet normal 0.9912446141242981 0.13203836977481842 0
    outer loop
      vertex 82.93099975585938 83.51799774169922 3.5
      vertex 82.93099975585938 83.51799774169922 10.5
      vertex 82.99800109863281 83.0150146484375 3.5
    endloop
  endfacet
  facet normal 0.9912446141242981 0.13203836977481842 0
    outer loop
      vertex 82.99800109863281 83.0150146484375 10.5
      vertex 82.99800109863281 83.0150146484375 3.5
      vertex 82.93099975585938 83.51799774169922 10.5
    endloop
  endfacet
  facet normal 0.1292896717786789 -0.24155335128307343 0.9617360234260559
    outer loop
      vertex -36.0359992980957 0.43700000643730164 3.8959999084472656
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
      vertex -35.96200180053711 -0.25200000405311584 3.7130000591278076
    endloop
  endfacet
  facet normal -0.27227458357810974 -0.20881763100624084 0.9392879009246826
    outer loop
      vertex -45.12900161743164 -59.67300033569336 3.0280001163482666
      vertex -46.07099914550781 -60.21699905395508 2.634000062942505
      vertex -44.279998779296875 -60.779998779296875 3.0280001163482666
    endloop
  endfacet
  facet normal -0.3038784861564636 -0.7338200807571411 0.6075902581214905
    outer loop
      vertex -94.14600372314453 16.013999938964844 2.7929999828338623
      vertex -93.59300231933594 15.78499984741211 2.7929999828338623
      vertex -93.5510025024414 15.939000129699707 3
    endloop
  endfacet
  facet normal -0.30373644828796387 -0.7343862652778625 0.6069769263267517
    outer loop
      vertex -93.5510025024414 15.939000129699707 3
      vertex -94.06600189208984 16.152000427246094 3
      vertex -94.14600372314453 16.013999938964844 2.7929999828338623
    endloop
  endfacet
  facet normal -0.3544151186943054 -0.8554847836494446 0.3775390684604645
    outer loop
      vertex -93.5260009765625 16.03499984741211 3.240999937057495
      vertex -94.01599884033203 16.238000869750977 3.240999937057495
      vertex -93.5510025024414 15.939000129699707 3
    endloop
  endfacet
  facet normal -0.3537430763244629 -0.8552942872047424 0.3785994350910187
    outer loop
      vertex -93.5510025024414 15.939000129699707 3
      vertex -94.01599884033203 16.238000869750977 3.240999937057495
      vertex -94.06600189208984 16.152000427246094 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -48.018001556396484 -56.01900100708008 2.5
      vertex -81.97599792480469 -57 2.5
      vertex -47.02799987792969 -60.72999954223633 2.5
    endloop
  endfacet
  facet normal -0.3233299255371094 -0.2751988470554352 0.9053857326507568
    outer loop
      vertex -35.96200180053711 -0.25200000405311584 3.7130000591278076
      vertex -35.41699981689453 -0.3100000023841858 3.890000104904175
      vertex -36.0359992980957 0.43700000643730164 3.8959999084472656
    endloop
  endfacet
  facet normal 0.9829576015472412 0.13093450665473938 0.12903690338134766
    outer loop
      vertex 82.93099975585938 83.51799774169922 3.5
      vertex 82.99800109863281 83.0150146484375 3.5
      vertex 82.99800109863281 83.18104553222656 3.33152437210083
    endloop
  endfacet
  facet normal -0.2723022699356079 -0.20892861485481262 0.9392551779747009
    outer loop
      vertex -46.07099914550781 -60.21699905395508 2.634000062942505
      vertex -45.04899978637695 -61.54899978637695 2.634000062942505
      vertex -44.279998779296875 -60.779998779296875 3.0280001163482666
    endloop
  endfacet
  facet normal -0.20901815593242645 -0.27221542596817017 0.9392604231834412
    outer loop
      vertex -44.279998779296875 -60.779998779296875 3.0280001163482666
      vertex -45.04899978637695 -61.54899978637695 2.634000062942505
      vertex -43.17300033569336 -61.630001068115234 3.0280001163482666
    endloop
  endfacet
  facet normal 0.9829422235488892 0.13080979883670807 0.1292801946401596
    outer loop
      vertex 82.99800109863281 83.18104553222656 3.33152437210083
      vertex 82.99800109863281 83.27051544189453 3.240999937057495
      vertex 82.93099975585938 83.51799774169922 3.5
    endloop
  endfacet
  facet normal -0.10430604219436646 -0.7887251377105713 0.6058323979377747
    outer loop
      vertex -92.9990005493164 15.706999778747559 2.7929999828338623
      vertex -92.9990005493164 15.866000175476074 3
      vertex -93.5510025024414 15.939000129699707 3
    endloop
  endfacet
  facet normal 0.9243202805519104 0.3816176950931549 0
    outer loop
      vertex 82.73200225830078 84 3.5
      vertex 82.73200225830078 84 10.5
      vertex 82.93099975585938 83.51799774169922 3.5
    endloop
  endfacet
  facet normal -0.20901581645011902 -0.2723539471626282 0.9392207860946655
    outer loop
      vertex -43.715999603271484 -62.571998596191406 2.634000062942505
      vertex -43.17300033569336 -61.630001068115234 3.0280001163482666
      vertex -45.04899978637695 -61.54899978637695 2.634000062942505
    endloop
  endfacet
  facet normal 0.9243202805519104 0.3816176950931549 0
    outer loop
      vertex 82.93099975585938 83.51799774169922 10.5
      vertex 82.93099975585938 83.51799774169922 3.5
      vertex 82.73200225830078 84 10.5
    endloop
  endfacet
  facet normal -0.10345472395420074 -0.7878475189208984 0.6071189045906067
    outer loop
      vertex -92.9990005493164 15.706999778747559 2.7929999828338623
      vertex -93.5510025024414 15.939000129699707 3
      vertex -93.59300231933594 15.78499984741211 2.7929999828338623
    endloop
  endfacet
  facet normal -0.10217751562595367 -0.08473146706819534 0.9911510348320007
    outer loop
      vertex -45.04899978637695 -61.54899978637695 2.634000062942505
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -45.16299819946289 -62.979000091552734 2.5
    endloop
  endfacet
  facet normal -0.6512255668640137 -0.19095462560653687 0.7344669103622437
    outer loop
      vertex -35.41699981689453 -0.3100000023841858 3.890000104904175
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
    endloop
  endfacet
  facet normal 0.9165888428688049 0.37895628809928894 0.12750321626663208
    outer loop
      vertex 82.73200225830078 84 3.5
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
      vertex 82.76100158691406 84.01699829101562 3.240999937057495
    endloop
  endfacet
  facet normal -0.12136876583099365 -0.9177473783493042 0.3781658411026001
    outer loop
      vertex -92.9990005493164 15.866000175476074 3
      vertex -93.5260009765625 16.03499984741211 3.240999937057495
      vertex -93.5510025024414 15.939000129699707 3
    endloop
  endfacet
  facet normal -0.06735207140445709 -0.087761789560318 0.993861973285675
    outer loop
      vertex -45.16299819946289 -62.979000091552734 2.5
      vertex -43.715999603271484 -62.571998596191406 2.634000062942505
      vertex -45.04899978637695 -61.54899978637695 2.634000062942505
    endloop
  endfacet
  facet normal -0.1312878131866455 -0.31717661023139954 0.9392350912094116
    outer loop
      vertex -41.882999420166016 -62.16400146484375 3.0280001163482666
      vertex -43.715999603271484 -62.571998596191406 2.634000062942505
      vertex -42.165000915527344 -63.2140007019043 2.634000062942505
    endloop
  endfacet
  facet normal 0.9166591167449951 0.37845468521118164 0.1284841150045395
    outer loop
      vertex 82.73200225830078 84 3.5
      vertex 82.93099975585938 83.51799774169922 3.5
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal 0 -0.6091551780700684 0.7930510640144348
    outer loop
      vertex -92.9990005493164 15.706999778747559 2.7929999828338623
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal 0.9162461161613464 0.12117023020982742 0.38185185194015503
    outer loop
      vertex 82.99800109863281 83.4207992553711 3.1928000450134277
      vertex 82.99800109863281 83.53511047363281 3.1565258502960205
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal -0.6173408031463623 -0.20635885000228882 0.7591484785079956
    outer loop
      vertex -35.45500183105469 0.40700000524520874 4.053999900817871
      vertex -35.41699981689453 -0.3100000023841858 3.890000104904175
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
    endloop
  endfacet
  facet normal -0.12005765736103058 -0.9169620871543884 0.38048219680786133
    outer loop
      vertex -92.9990005493164 15.866000175476074 3
      vertex -92.9990005493164 15.965999603271484 3.240999937057495
      vertex -93.5260009765625 16.03499984741211 3.240999937057495
    endloop
  endfacet
  facet normal -0.05457376688718796 -0.13184410333633423 0.9897670745849609
    outer loop
      vertex -45.16299819946289 -62.979000091552734 2.5
      vertex -42.165000915527344 -63.2140007019043 2.634000062942505
      vertex -43.715999603271484 -62.571998596191406 2.634000062942505
    endloop
  endfacet
  facet normal 0.9167433381080627 0.1220000609755516 0.3803914189338684
    outer loop
      vertex 82.99800109863281 83.27051544189453 3.240999937057495
      vertex 82.99800109863281 83.4207992553711 3.1928000450134277
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 83.7043228149414 3
      vertex 82.99800109863281 83.4207992553711 3.1928000450134277
    endloop
  endfacet
  facet normal 0 -0.7930510640144348 0.6091551780700684
    outer loop
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
      vertex -92.9990005493164 15.866000175476074 3
      vertex -92.9990005493164 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal 0.9829422235488892 0.13080979883670807 0.1292801946401596
    outer loop
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
      vertex 82.93099975585938 83.51799774169922 3.5
      vertex 82.99800109863281 83.27051544189453 3.240999937057495
    endloop
  endfacet
  facet normal -0.33575916290283203 -0.4372769296169281 0.8342989087104797
    outer loop
      vertex -44.279998779296875 -60.779998779296875 3.0280001163482666
      vertex -43.17300033569336 -61.630001068115234 3.0280001163482666
      vertex -42.68899917602539 -60.79199981689453 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.4207992553711 3.1928000450134277
      vertex 82.99800109863281 83.27051544189453 3.240999937057495
      vertex 82.99800109863281 85 0
    endloop
  endfacet
  facet normal -0.0435299314558506 -0.15546804666519165 0.9868813753128052
    outer loop
      vertex -39.619998931884766 -64.53099822998047 2.5
      vertex -40.5 -63.433998107910156 2.634000062942505
      vertex -45.16299819946289 -62.979000091552734 2.5
    endloop
  endfacet
  facet normal -0.08418598026037216 -0.6371347904205322 0.7661409378051758
    outer loop
      vertex -45.16299819946289 -62.979000091552734 2.5
      vertex -40.5 -63.433998107910156 2.634000062942505
      vertex -42.165000915527344 -63.2140007019043 2.634000062942505
    endloop
  endfacet
  facet normal 0 -0.6091551780700684 0.7930510640144348
    outer loop
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -80.9990005493164 15.5 2.634000062942505
      vertex -80.9990005493164 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal 0.7361740469932556 0.304475873708725 0.6044354438781738
    outer loop
      vertex 82.99800109863281 83.7043228149414 3
      vertex 82.99800109863281 83.87273406982422 2.915163993835449
      vertex 82.8479995727539 84.06700134277344 3
    endloop
  endfacet
  facet normal -0.13129131495952606 -0.3171643912792206 0.9392387270927429
    outer loop
      vertex -43.17300033569336 -61.630001068115234 3.0280001163482666
      vertex -43.715999603271484 -62.571998596191406 2.634000062942505
      vertex -41.882999420166016 -62.16400146484375 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 15 2.5
      vertex -94.4020004272461 15.347999572753906 2.5
      vertex -94.9990005493164 6.21999979019165 2.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.53511047363281 3.1565258502960205
      vertex 82.99800109863281 83.4207992553711 3.1928000450134277
      vertex 82.99800109863281 83.7043228149414 3
    endloop
  endfacet
  facet normal -0.05028655380010605 -0.3827694058418274 0.9224743247032166
    outer loop
      vertex -92.9990005493164 15.258999824523926 2.5339999198913574
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -93.64600372314453 15.585000038146973 2.634000062942505
    endloop
  endfacet
  facet normal 0.8541894555091858 0.35315775871276855 0.3816280961036682
    outer loop
      vertex 82.8479995727539 84.06700134277344 3
      vertex 82.76100158691406 84.01699829101562 3.240999937057495
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal -0.0447956807911396 -0.3403979539871216 0.9392138123512268
    outer loop
      vertex -40.5 -62.34600067138672 3.0280001163482666
      vertex -41.882999420166016 -62.16400146484375 3.0280001163482666
      vertex -42.165000915527344 -63.2140007019043 2.634000062942505
    endloop
  endfacet
  facet normal -0.21085025370121002 -0.5093573331832886 0.8343244194984436
    outer loop
      vertex -43.17300033569336 -61.630001068115234 3.0280001163482666
      vertex -41.882999420166016 -62.16400146484375 3.0280001163482666
      vertex -41.632999420166016 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal -0.05009318143129349 -0.3824318051338196 0.9226248264312744
    outer loop
      vertex -93.70899963378906 15.35200023651123 2.5339999198913574
      vertex -92.9990005493164 15.258999824523926 2.5339999198913574
      vertex -93.64600372314453 15.585000038146973 2.634000062942505
    endloop
  endfacet
  facet normal 0.8540567755699158 0.3532312512397766 0.38185691833496094
    outer loop
      vertex 82.96399688720703 83.5260009765625 3.240999937057495
      vertex 82.99800109863281 83.53511047363281 3.1565258502960205
      vertex 82.8479995727539 84.06700134277344 3
    endloop
  endfacet
  facet normal 0.8540567755699158 0.3532312512397766 0.38185691833496094
    outer loop
      vertex 82.99800109863281 83.7043228149414 3
      vertex 82.8479995727539 84.06700134277344 3
      vertex 82.99800109863281 83.53511047363281 3.1565258502960205
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.7043228149414 3
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 83.87273406982422 2.915163993835449
    endloop
  endfacet
  facet normal -0.21081587672233582 -0.5094314813613892 0.8342878222465515
    outer loop
      vertex -43.17300033569336 -61.630001068115234 3.0280001163482666
      vertex -41.632999420166016 -61.229000091552734 3.6619999408721924
      vertex -42.68899917602539 -60.79199981689453 3.6619999408721924
    endloop
  endfacet
  facet normal 0.521631121635437 -0.29773834347724915 0.7995328903198242
    outer loop
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
      vertex -36.70800018310547 -1.1890000104904175 3.6619999408721924
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 -84 2.5
      vertex -36 -82 2.5
      vertex -45.16299819946289 -62.979000091552734 2.5
    endloop
  endfacet
  facet normal -0.8569499850273132 -0.1573743373155594 0.4907851219177246
    outer loop
      vertex -35.020999908447266 -2.9110000133514404 3.63100004196167
      vertex -35.0260009765625 -1.6799999475479126 4.017000198364258
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -48.018001556396484 -56.01900100708008 2.5
      vertex -45.16299819946289 -51.020999908447266 2.5
      vertex -82.4469985961914 -54.21500015258789 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -82.4469985961914 -54.21500015258789 2.5
      vertex -45.16299819946289 -51.020999908447266 2.5
    endloop
  endfacet
  facet normal 0.3825770616531372 0.9239236116409302 0
    outer loop
      vertex 81.51699829101562 84.93199920654297 3.5
      vertex 81.51699829101562 84.93199920654297 10.5
      vertex 82 84.73200225830078 10.5
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 23 -82 2.5
      vertex -32 -82 2.5
      vertex -32 -82 10.5
    endloop
  endfacet
  facet normal 0.13040490448474884 0.9914608001708984 0
    outer loop
      vertex 81 85 10.5
      vertex 81.51699829101562 84.93199920654297 10.5
      vertex 81.51699829101562 84.93199920654297 3.5
    endloop
  endfacet
  facet normal -0.3316732943058014 0.7993326187133789 0.5010590553283691
    outer loop
      vertex -90.43800354003906 -53.542999267578125 4.500999927520752
      vertex -90.9990005493164 -54.402000427246094 5.5
      vertex -90.2760009765625 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal 0.3825770616531372 0.9239236116409302 0
    outer loop
      vertex 82 84.73200225830078 3.5
      vertex 81.51699829101562 84.93199920654297 3.5
      vertex 82 84.73200225830078 10.5
    endloop
  endfacet
  facet normal 0.41223397850990295 0.6966024041175842 0.5872037410736084
    outer loop
      vertex 82.05799865722656 85 2.8259999752044678
      vertex 81.5260009765625 84.96499633789062 3.240999937057495
      vertex 82.06700134277344 84.8479995727539 3
    endloop
  endfacet
  facet normal 0.13040490448474884 0.9914608001708984 0
    outer loop
      vertex 81 85 3.5
      vertex 81 85 10.5
      vertex 81.51699829101562 84.93199920654297 3.5
    endloop
  endfacet
  facet normal 0.12930254638195038 0.9830796718597412 0.12975040078163147
    outer loop
      vertex 81 85 3.5
      vertex 81.51699829101562 84.93199920654297 3.5
      vertex 81.5260009765625 84.96499633789062 3.240999937057495
    endloop
  endfacet
  facet normal -0.5091621279716492 0.21132797002792358 0.8343227505683899
    outer loop
      vertex -45.66400146484375 2.384000062942505 3.0280001163482666
      vertex -44.29100036621094 3.188999891281128 3.6619999408721924
      vertex -45.12900161743164 3.6730000972747803 3.0280001163482666
    endloop
  endfacet
  facet normal 0.2572612166404724 0.8779162168502808 0.403831422328949
    outer loop
      vertex 81 85 3.5
      vertex 81.5260009765625 84.96499633789062 3.240999937057495
      vertex 82.05799865722656 85 2.8259999752044678
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 25 83 10.5
      vertex 80 83 2.5
      vertex 80 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.619998931884766 -64.53099822998047 2.5
      vertex -45.16299819946289 -62.979000091552734 2.5
      vertex -36 -82 2.5
    endloop
  endfacet
  facet normal 0 -0.3832542896270752 0.9236428737640381
    outer loop
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
      vertex -92.9990005493164 15.5 2.634000062942505
      vertex -92.9990005493164 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal -0.017046311870217323 -0.13013851642608643 0.9913492798805237
    outer loop
      vertex -92.9990005493164 15 2.5
      vertex -92.9990005493164 15.258999824523926 2.5339999198913574
      vertex -93.70899963378906 15.35200023651123 2.5339999198913574
    endloop
  endfacet
  facet normal -0.12255513668060303 -0.01611986570060253 0.99233078956604
    outer loop
      vertex -46.93299865722656 1 2.634000062942505
      vertex -48.018001556396484 1 2.5
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
    endloop
  endfacet
  facet normal -0.8736749887466431 -0.16087840497493744 0.45914068818092346
    outer loop
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
      vertex -35.0260009765625 -1.6799999475479126 4.017000198364258
      vertex -35.03200149536133 -0.4830000102519989 4.425000190734863
    endloop
  endfacet
  facet normal -0.5091010928153992 0.21116124093532562 0.8344022035598755
    outer loop
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
      vertex -44.29100036621094 3.188999891281128 3.6619999408721924
      vertex -45.66400146484375 2.384000062942505 3.0280001163482666
    endloop
  endfacet
  facet normal -0.047022826969623566 -0.18957765400409698 0.9807391166687012
    outer loop
      vertex -93.70899963378906 15.35200023651123 2.5339999198913574
      vertex -94.4020004272461 15.347999572753906 2.5
      vertex -92.9990005493164 15 2.5
    endloop
  endfacet
  facet normal -0.3404288589954376 -0.04477712884545326 0.9392035007476807
    outer loop
      vertex -46.93299865722656 1 2.634000062942505
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
      vertex -45.84600067138672 1 3.0280001163482666
    endloop
  endfacet
  facet normal 0 -0.13015742599964142 0.9914933443069458
    outer loop
      vertex -80.9990005493164 15.258999824523926 2.5339999198913574
      vertex -92.9990005493164 15.258999824523926 2.5339999198913574
      vertex -92.9990005493164 15 2.5
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -34.41400146484375 -83.41400146484375 10.5
      vertex -34.41400146484375 -83.41400146484375 3.5
      vertex -34 -83.73200225830078 10.5
    endloop
  endfacet
  facet normal -0.3825770616531372 -0.9239236116409302 0
    outer loop
      vertex -34 -83.73200225830078 10.5
      vertex -34 -83.73200225830078 3.5
      vertex -33.516998291015625 -83.93199920654297 10.5
    endloop
  endfacet
  facet normal -0.4328811764717102 -0.34306079149246216 0.833620548248291
    outer loop
      vertex -35.819000244140625 -1.4190000295639038 3.306999921798706
      vertex -35.34700012207031 -1.496999979019165 3.5199999809265137
      vertex -35.96200180053711 -0.25200000405311584 3.7130000591278076
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.4020004272461 15.347999572753906 2.5
      vertex -94.9990005493164 15.763999938964844 2.5
      vertex -94.9990005493164 6.21999979019165 2.5
    endloop
  endfacet
  facet normal -0.13110344111919403 -0.0229134913533926 0.9911038875579834
    outer loop
      vertex -48.018001556396484 1 2.5
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
    endloop
  endfacet
  facet normal -0.13040490448474884 -0.9914608001708984 0
    outer loop
      vertex -33.516998291015625 -83.93199920654297 10.5
      vertex -33.516998291015625 -83.93199920654297 3.5
      vertex -33 -84 10.5
    endloop
  endfacet
  facet normal -0.5464843511581421 0.07186775654554367 0.8343799114227295
    outer loop
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -44.87799835205078 1 3.6619999408721924
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
    endloop
  endfacet
  facet normal -0.651441216468811 -0.2605305314064026 0.7125645279884338
    outer loop
      vertex -35.34700012207031 -1.496999979019165 3.5199999809265137
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
      vertex -35.41699981689453 -0.3100000023841858 3.890000104904175
    endloop
  endfacet
  facet normal -0.5464843511581421 -0.07186775654554367 0.8343799114227295
    outer loop
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
      vertex -44.87799835205078 1 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -34 -83.73200225830078 3.5
      vertex -34 -83.73200225830078 10.5
      vertex -34.41400146484375 -83.41400146484375 3.5
    endloop
  endfacet
  facet normal -0.3233940601348877 -0.29892709851264954 0.8978078365325928
    outer loop
      vertex -35.34700012207031 -1.496999979019165 3.5199999809265137
      vertex -35.41699981689453 -0.3100000023841858 3.890000104904175
      vertex -35.96200180053711 -0.25200000405311584 3.7130000591278076
    endloop
  endfacet
  facet normal -0.5464816689491272 0.07186391949653625 0.8343819975852966
    outer loop
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -44.729000091552734 2.132999897003174 3.6619999408721924
      vertex -45.66400146484375 2.384000062942505 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5624860525131226 -0.7333889007568359 0.38177230954170227
    outer loop
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
      vertex -94.50800323486328 16.490999221801758 3
      vertex -94.06600189208984 16.152000427246094 3
    endloop
  endfacet
  facet normal -0.6040772199630737 -0.7864401340484619 0.1288510262966156
    outer loop
      vertex -34.41400146484375 -83.41400146484375 3.5
      vertex -34.4379997253418 -83.43800354003906 3.240999937057495
      vertex -34 -83.73200225830078 3.5
    endloop
  endfacet
  facet normal -0.564437210559845 -0.7334200143814087 0.3788214921951294
    outer loop
      vertex -94.43699645996094 16.562000274658203 3.240999937057495
      vertex -94.06600189208984 16.152000427246094 3
      vertex -94.01599884033203 16.238000869750977 3.240999937057495
    endloop
  endfacet
  facet normal -0.3404421806335449 -0.044769130647182465 0.9391990303993225
    outer loop
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
      vertex -45.66400146484375 -0.3840000033378601 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5464816689491272 -0.07186391949653625 0.8343819975852966
    outer loop
      vertex -45.84600067138672 1 3.0280001163482666
      vertex -45.66400146484375 -0.3840000033378601 3.0280001163482666
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6046614646911621 -0.7856866717338562 0.13069437444210052
    outer loop
      vertex -34.016998291015625 -83.76200103759766 3.240999937057495
      vertex -34 -83.73200225830078 3.5
      vertex -34.4379997253418 -83.43800354003906 3.240999937057495
    endloop
  endfacet
  facet normal -0.09135701507329941 -0.35681501030921936 0.9296972155570984
    outer loop
      vertex -36.141998291015625 -0.2549999952316284 3.7219998836517334
      vertex -35.98099899291992 -1.4140000343322754 3.2929999828338623
      vertex -35.819000244140625 -1.4190000295639038 3.306999921798706
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -47.02799987792969 4.730000019073486 2.5
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -48.018001556396484 1 2.5
    endloop
  endfacet
  facet normal 0.052630309015512466 -0.3223690688610077 0.945149838924408
    outer loop
      vertex -35.819000244140625 -1.4190000295639038 3.306999921798706
      vertex -35.96200180053711 -0.25200000405311584 3.7130000591278076
      vertex -36.141998291015625 -0.2549999952316284 3.7219998836517334
    endloop
  endfacet
  facet normal -0.1476350575685501 -0.3560957610607147 0.9227132201194763
    outer loop
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -93.70899963378906 15.35200023651123 2.5339999198913574
      vertex -93.64600372314453 15.585000038146973 2.634000062942505
    endloop
  endfacet
  facet normal 0.20764705538749695 -0.3140648305416107 0.9264156818389893
    outer loop
      vertex -35.98099899291992 -1.4140000343322754 3.2929999828338623
      vertex -36.141998291015625 -0.2549999952316284 3.7219998836517334
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -82.90299987792969 -2.617000102996826 2.5
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -81.97599792480469 0.052000001072883606 2.5
    endloop
  endfacet
  facet normal -0.3726082146167755 -0.48388025164604187 0.791847825050354
    outer loop
      vertex -94.76699829101562 16.23200035095215 2.634000062942505
      vertex -94.14600372314453 16.013999938964844 2.7929999828338623
      vertex -94.62000274658203 16.378999710083008 2.7929999828338623
    endloop
  endfacet
  facet normal 0.18466722965240479 -0.28006061911582947 0.9420530796051025
    outer loop
      vertex -35.98099899291992 -1.4140000343322754 3.2929999828338623
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
      vertex -35.82500076293945 -2.697000026702881 2.88100004196167
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -34.731998443603516 -83 3.5
      vertex -34.41400146484375 -83.41400146484375 10.5
      vertex -34.731998443603516 -83 10.5
    endloop
  endfacet
  facet normal 0.4217502474784851 -0.3339785933494568 0.8429620862007141
    outer loop
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
      vertex -36.141998291015625 -0.2549999952316284 3.7219998836517334
    endloop
  endfacet
  facet normal -0.04597868025302887 -0.2515598237514496 0.9667490124702454
    outer loop
      vertex -93.70899963378906 15.35200023651123 2.5339999198913574
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -94.4020004272461 15.347999572753906 2.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -49.499000549316406 16.134000778198242 10.5
      vertex -49.499000549316406 16.134000778198242 3.5
      vertex -49.257999420166016 16.034000396728516 10.5
    endloop
  endfacet
  facet normal -0.48429983854293823 -0.3721461892127991 0.7918086051940918
    outer loop
      vertex -94.76699829101562 16.23200035095215 2.634000062942505
      vertex -94.62000274658203 16.378999710083008 2.7929999828338623
      vertex -94.98500061035156 16.854000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7867811918258667 -0.6036349534988403 0.12884165346622467
    outer loop
      vertex -34.41400146484375 -83.41400146484375 3.5
      vertex -34.76100158691406 -83.01699829101562 3.240999937057495
      vertex -34.4379997253418 -83.43800354003906 3.240999937057495
    endloop
  endfacet
  facet normal -0.9147943258285522 -0.14660008251667023 0.3763771057128906
    outer loop
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
      vertex -35.020999908447266 -2.9110000133514404 3.63100004196167
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
    endloop
  endfacet
  facet normal -0.3825770616531372 -0.9239236116409302 0
    outer loop
      vertex -34 -83.73200225830078 3.5
      vertex -33.516998291015625 -83.93199920654297 3.5
      vertex -33.516998291015625 -83.93199920654297 10.5
    endloop
  endfacet
  facet normal -0.1675473302602768 -0.08401062339544296 0.9822779893875122
    outer loop
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -94.9990005493164 16.06800079345703 2.5260000228881836
      vertex -94.9990005493164 15.763999938964844 2.5
    endloop
  endfacet
  facet normal -0.7625223994255066 -0.21127575635910034 0.6114917397499084
    outer loop
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
      vertex -35.34700012207031 -1.496999979019165 3.5199999809265137
      vertex -35.284000396728516 -2.7750000953674316 3.1570000648498535
    endloop
  endfacet
  facet normal -0.6073083281517029 -0.7944662570953369 0
    outer loop
      vertex -49.499000549316406 16.134000778198242 10.5
      vertex -49.707000732421875 16.292999267578125 10.5
      vertex -49.499000549316406 16.134000778198242 3.5
    endloop
  endfacet
  facet normal -0.6073083281517029 -0.7944662570953369 0
    outer loop
      vertex -49.499000549316406 16.134000778198242 3.5
      vertex -49.707000732421875 16.292999267578125 10.5
      vertex -49.707000732421875 16.292999267578125 3.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -49.257999420166016 16.034000396728516 3.5
      vertex -49.257999420166016 16.034000396728516 10.5
      vertex -49.499000549316406 16.134000778198242 3.5
    endloop
  endfacet
  facet normal -0.7631368041038513 -0.21120622754096985 0.610748827457428
    outer loop
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
      vertex -35.34700012207031 -1.496999979019165 3.5199999809265137
    endloop
  endfacet
  facet normal -0.3343205153942108 0.7992205023765564 0.4994760751724243
    outer loop
      vertex -90.43800354003906 -53.542999267578125 4.500999927520752
      vertex -91.3010025024414 -53.90399932861328 4.500999927520752
      vertex -90.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -34.41400146484375 -83.41400146484375 3.5
      vertex -34.41400146484375 -83.41400146484375 10.5
      vertex -34.731998443603516 -83 3.5
    endloop
  endfacet
  facet normal -0.4326868951320648 -0.2660020589828491 0.8614087104797363
    outer loop
      vertex -35.284000396728516 -2.7750000953674316 3.1570000648498535
      vertex -35.34700012207031 -1.496999979019165 3.5199999809265137
      vertex -35.819000244140625 -1.4190000295639038 3.306999921798706
    endloop
  endfacet
  facet normal -0.5270562767982483 0.6861675977706909 0.5013838410377502
    outer loop
      vertex -91.3010025024414 -53.90399932861328 4.500999927520752
      vertex -91.62000274658203 -54.87900161743164 5.5
      vertex -90.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.5297383069992065 0.6853258013725281 0.49970582127571106
    outer loop
      vertex -91.3010025024414 -53.90399932861328 4.500999927520752
      vertex -92.04100036621094 -54.47600173950195 4.500999927520752
      vertex -91.62000274658203 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal -0.15166135132312775 -0.21764862537384033 0.9641721248626709
    outer loop
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -94.9990005493164 15.763999938964844 2.5
      vertex -94.4020004272461 15.347999572753906 2.5
    endloop
  endfacet
  facet normal -0.18178147077560425 -0.3704967498779297 0.9108719229698181
    outer loop
      vertex -94.98500061035156 16.854000091552734 2.7929999828338623
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
      vertex -94.9990005493164 16.378999710083008 2.5969998836517334
    endloop
  endfacet
  facet normal -0.35815566778182983 -0.3470914363861084 0.8667479753494263
    outer loop
      vertex -94.76699829101562 16.23200035095215 2.634000062942505
      vertex -94.98500061035156 16.854000091552734 2.7929999828338623
      vertex -94.9990005493164 16.378999710083008 2.5969998836517334
    endloop
  endfacet
  facet normal -0.28427407145500183 -0.2133869081735611 0.934694766998291
    outer loop
      vertex -94.9990005493164 16.378999710083008 2.5969998836517334
      vertex -94.9990005493164 16.06800079345703 2.5260000228881836
      vertex -94.76699829101562 16.23200035095215 2.634000062942505
    endloop
  endfacet
  facet normal -0.22498823702335358 -0.29356148838996887 0.9290866255760193
    outer loop
      vertex -94.9990005493164 16.06800079345703 2.5260000228881836
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -94.76699829101562 16.23200035095215 2.634000062942505
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 16.378999710083008 2.5969998836517334
      vertex -94.9990005493164 16.941999435424805 2.8259999752044678
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -0.3731207847595215 -0.48684272170066833 0.7897879481315613
    outer loop
      vertex -94.76699829101562 16.23200035095215 2.634000062942505
      vertex -94.2490005493164 15.835000038146973 2.634000062942505
      vertex -94.14600372314453 16.013999938964844 2.7929999828338623
    endloop
  endfacet
  facet normal -0.35363417863845825 -0.8553417921066284 0.3785938024520874
    outer loop
      vertex -34.016998291015625 -83.76200103759766 3.240999937057495
      vertex -34.06700134277344 -83.8479995727539 3
      vertex -33.5260009765625 -83.96499633789062 3.240999937057495
    endloop
  endfacet
  facet normal -0.3788367807865143 -0.9162998199462891 0.1299128383398056
    outer loop
      vertex -33.516998291015625 -83.93199920654297 3.5
      vertex -34.016998291015625 -83.76200103759766 3.240999937057495
      vertex -33.5260009765625 -83.96499633789062 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -91.62000274658203 -54.87900161743164 5.5
      vertex -89.9990005493164 -56.13399887084961 5.5
      vertex -90.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.09700012207031 -55.5 5.5
      vertex -90.36499786376953 -56.5 5.5
      vertex -91.62000274658203 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal -0.6860305666923523 0.526951014995575 0.5016818046569824
    outer loop
      vertex -92.04100036621094 -54.47600173950195 4.500999927520752
      vertex -92.09700012207031 -55.5 5.5
      vertex -91.62000274658203 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal -0.37928059697151184 -0.9159626364707947 0.1309909224510193
    outer loop
      vertex -33.516998291015625 -83.93199920654297 3.5
      vertex -34 -83.73200225830078 3.5
      vertex -34.016998291015625 -83.76200103759766 3.240999937057495
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 6.21999979019165 2.5
      vertex -94.9990005493164 15.763999938964844 2.5
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 16.06800079345703 2.5260000228881836
      vertex -94.9990005493164 16.378999710083008 2.5969998836517334
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 15.763999938964844 2.5
      vertex -94.9990005493164 16.06800079345703 2.5260000228881836
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -0.9988933801651001 -0.012282892130315304 0.04539952054619789
    outer loop
      vertex -35 -5.103000164031982 3.5
      vertex -35.020999908447266 -2.9110000133514404 3.63100004196167
      vertex -35.018001556396484 -3.99399995803833 3.4040000438690186
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.05599975585938 8.444000244140625 2.5
      vertex -92.9990005493164 15 2.5
      vertex -90.87999725341797 8.395000457763672 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.87999725341797 8.395000457763672 2.5
      vertex -92.9990005493164 15 2.5
      vertex -94.9990005493164 6.21999979019165 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.46499633789062 -56.74100112915039 5.5
      vertex -92.4990005493164 -57 5.5
      vertex -90.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.46499633789062 -57.25899887084961 5.5
      vertex -90.4990005493164 -57 5.5
      vertex -92.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.36499786376953 -56.5 5.5
      vertex -92.09700012207031 -55.5 5.5
      vertex -90.46499633789062 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.20600128173828 -56.292999267578125 5.5
      vertex -91.62000274658203 -54.87900161743164 5.5
      vertex -90.36499786376953 -56.5 5.5
    endloop
  endfacet
  facet normal -0.9150784015655518 -0.08515667170286179 0.39418256282806396
    outer loop
      vertex -35.018001556396484 -3.99399995803833 3.4040000438690186
      vertex -35.020999908447266 -2.9110000133514404 3.63100004196167
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.2760009765625 -54.10200119018555 5.5
      vertex -90.9990005493164 -54.402000427246094 5.5
      vertex -89.75800323486328 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.9990005493164 -56.13399887084961 5.5
      vertex -89.75800323486328 -56.034000396728516 5.5
      vertex -90.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.9990005493164 -56.13399887084961 5.5
      vertex -91.62000274658203 -54.87900161743164 5.5
      vertex -90.20600128173828 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.39700317382812 -56.2239990234375 5.5
      vertex -90.46499633789062 -56.74100112915039 5.5
      vertex -92.09700012207031 -55.5 5.5
    endloop
  endfacet
  facet normal -0.7865555882453918 -0.6041659116744995 0.12772561609745026
    outer loop
      vertex -34.41400146484375 -83.41400146484375 3.5
      vertex -34.731998443603516 -83 3.5
      vertex -34.76100158691406 -83.01699829101562 3.240999937057495
    endloop
  endfacet
  facet normal -0.6891447901725769 0.5249743461608887 0.49948111176490784
    outer loop
      vertex -92.09700012207031 -55.5 5.5
      vertex -92.04100036621094 -54.47600173950195 4.500999927520752
      vertex -92.60700225830078 -55.21900177001953 4.500999927520752
    endloop
  endfacet
  facet normal -0.799384593963623 0.33123672008514404 0.5012649297714233
    outer loop
      vertex -92.09700012207031 -55.5 5.5
      vertex -92.60700225830078 -55.21900177001953 4.500999927520752
      vertex -92.39700317382812 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal -0.9243202805519104 -0.3816176950931549 0
    outer loop
      vertex -34.731998443603516 -83 3.5
      vertex -34.731998443603516 -83 10.5
      vertex -34.930999755859375 -82.51799774169922 3.5
    endloop
  endfacet
  facet normal -0.9165888428688049 -0.37895628809928894 0.12750321626663208
    outer loop
      vertex -34.731998443603516 -83 3.5
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
      vertex -34.76100158691406 -83.01699829101562 3.240999937057495
    endloop
  endfacet
  facet normal -0.9166591167449951 -0.37845468521118164 0.1284841150045395
    outer loop
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
      vertex -34.731998443603516 -83 3.5
      vertex -34.930999755859375 -82.51799774169922 3.5
    endloop
  endfacet
  facet normal -0.6737651228904724 0.276516318321228 0.6852585673332214
    outer loop
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
      vertex -92.96199798583984 -56.08399963378906 4.500999927520752
      vertex -92.60700225830078 -55.21900177001953 4.500999927520752
    endloop
  endfacet
  facet normal -0.5632072687149048 -0.7343292236328125 0.3788907527923584
    outer loop
      vertex -34.06700134277344 -83.8479995727539 3
      vertex -34.016998291015625 -83.76200103759766 3.240999937057495
      vertex -34.50899887084961 -83.50900268554688 3
    endloop
  endfacet
  facet normal 0.23381000757217407 -0.2922804355621338 0.9273106455802917
    outer loop
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
      vertex -36.71900177001953 -2.7799999713897705 3.0280001163482666
    endloop
  endfacet
  facet normal -0.8014991879463196 0.32893896102905273 0.499397873878479
    outer loop
      vertex -92.96199798583984 -56.08399963378906 4.500999927520752
      vertex -92.39700317382812 -56.2239990234375 5.5
      vertex -92.60700225830078 -55.21900177001953 4.500999927520752
    endloop
  endfacet
  facet normal -0.5636794567108154 -0.7324352860450745 0.3818429410457611
    outer loop
      vertex -34.50899887084961 -83.50900268554688 3
      vertex -34.016998291015625 -83.76200103759766 3.240999937057495
      vertex -34.4379997253418 -83.43800354003906 3.240999937057495
    endloop
  endfacet
  facet normal -0.7223204970359802 0.09262514859437943 0.685327410697937
    outer loop
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
      vertex -93.08100128173828 -57.012001037597656 4.500999927520752
      vertex -92.96199798583984 -56.08399963378906 4.500999927520752
    endloop
  endfacet
  facet normal -0.4848547875881195 -0.632170557975769 0.6043808460235596
    outer loop
      vertex -34.06700134277344 -83.8479995727539 3
      vertex -34.50899887084961 -83.50900268554688 3
      vertex -34.62099838256836 -83.62100219726562 2.7929999828338623
    endloop
  endfacet
  facet normal -0.858024001121521 0.11278150230646133 0.5010740160942078
    outer loop
      vertex -92.96199798583984 -56.08399963378906 4.500999927520752
      vertex -92.4990005493164 -57 5.5
      vertex -92.39700317382812 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal -0.8593736886978149 0.11019986122846603 0.4993324279785156
    outer loop
      vertex -92.96199798583984 -56.08399963378906 4.500999927520752
      vertex -93.08100128173828 -57.012001037597656 4.500999927520752
      vertex -92.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal -0.24786481261253357 -0.32339468598365784 0.913224458694458
    outer loop
      vertex -35.98099899291992 -1.4140000343322754 3.2929999828338623
      vertex -35.82500076293945 -2.697000026702881 2.88100004196167
      vertex -35.68299865722656 -2.7070000171661377 2.9159998893737793
    endloop
  endfacet
  facet normal -0.8579592704772949 -0.11277299374341965 0.501186728477478
    outer loop
      vertex -93.08100128173828 -57.012001037597656 4.500999927520752
      vertex -92.39700317382812 -57.7760009765625 5.5
      vertex -92.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal 0.13429638743400574 -0.3117847144603729 0.9406140446662903
    outer loop
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
      vertex -35.82500076293945 -2.697000026702881 2.88100004196167
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.4990005493164 -57 5.5
      vertex -90.46499633789062 -56.74100112915039 5.5
      vertex -92.39700317382812 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0.010083490051329136 0.1520688235759735 0.9883184432983398
    outer loop
      vertex -90.87999725341797 -49.60499954223633 2.5
      vertex -89.52100372314453 -50.566001892089844 2.634000062942505
      vertex -87.15499877929688 -49.85200119018555 2.5
    endloop
  endfacet
  facet normal -0.9288679361343384 -0.0912163257598877 0.35900402069091797
    outer loop
      vertex -35.15800094604492 -3.937999963760376 3.055999994277954
      vertex -35.018001556396484 -3.99399995803833 3.4040000438690186
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
    endloop
  endfacet
  facet normal -0.632382333278656 -0.48460453748703003 0.604360044002533
    outer loop
      vertex -34.62099838256836 -83.62100219726562 2.7929999828338623
      vertex -34.50899887084961 -83.50900268554688 3
      vertex -34.98500061035156 -83.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal -0.015718501061201096 0.11624705046415329 0.9930959343910217
    outer loop
      vertex -90.87999725341797 -49.60499954223633 2.5
      vertex -91.18499755859375 -50.79100036621094 2.634000062942505
      vertex -89.52100372314453 -50.566001892089844 2.634000062942505
    endloop
  endfacet
  facet normal -0.7333889007568359 -0.5624860525131226 0.38177230954170227
    outer loop
      vertex -34.50899887084961 -83.50900268554688 3
      vertex -34.4379997253418 -83.43800354003906 3.240999937057495
      vertex -34.847999572753906 -83.06700134277344 3
    endloop
  endfacet
  facet normal -0.05243374779820442 0.1254202276468277 0.9907171726226807
    outer loop
      vertex -90.87999725341797 -49.60499954223633 2.5
      vertex -92.73500061035156 -51.43899917602539 2.634000062942505
      vertex -91.18499755859375 -50.79100036621094 2.634000062942505
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.0150146484375 3.5
      vertex 82.99800109863281 83.0150146484375 10.5
      vertex 82.99800109863281 -84 10.5
    endloop
  endfacet
  facet normal -0.7625980973243713 -0.1449187695980072 0.6304305791854858
    outer loop
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
      vertex -35.284000396728516 -2.7750000953674316 3.1570000648498535
      vertex -35.23899841308594 -3.9210000038146973 2.947999954223633
    endloop
  endfacet
  facet normal 0.18152017891407013 0.30978161096572876 0.9333197474479675
    outer loop
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
      vertex -36.06999969482422 -55.220001220703125 3.5309998989105225
      vertex -35.8849983215332 -53.82500076293945 3.0320000648498535
    endloop
  endfacet
  facet normal -0.8029491305351257 -0.12922383844852448 0.5818710327148438
    outer loop
      vertex -35.23899841308594 -3.9210000038146973 2.947999954223633
      vertex -35.15800094604492 -3.937999963760376 3.055999994277954
      vertex -35.1879997253418 -2.805999994277954 3.2660000324249268
    endloop
  endfacet
  facet normal 0.18937385082244873 0.300734281539917 0.9347172975540161
    outer loop
      vertex -35.8849983215332 -53.82500076293945 3.0320000648498535
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -93.53199768066406 -50.57899856567383 2.5
      vertex -90.87999725341797 -49.60499954223633 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0.5197185277938843 0.3007798492908478 0.7996399998664856
    outer loop
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
      vertex -36.70800018310547 -54.81100082397461 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5302640795707703 -0.2970536947250366 0.7940900921821594
    outer loop
      vertex -35.284000396728516 -2.7750000953674316 3.1570000648498535
      vertex -35.819000244140625 -1.4190000295639038 3.306999921798706
      vertex -35.68299865722656 -2.7070000171661377 2.9159998893737793
    endloop
  endfacet
  facet normal -0.33691543340682983 0.43605464696884155 0.8344724774360657
    outer loop
      vertex -91.70099639892578 -53.215999603271484 3.6619999408721924
      vertex -92.18800354003906 -52.37900161743164 3.0280001163482666
      vertex -93.29199981689453 -53.231998443603516 3.0280001163482666
    endloop
  endfacet
  facet normal -0.09131289273500443 -0.2980838119983673 0.9501621127128601
    outer loop
      vertex -35.98099899291992 -1.4140000343322754 3.2929999828338623
      vertex -35.68299865722656 -2.7070000171661377 2.9159998893737793
      vertex -35.819000244140625 -1.4190000295639038 3.306999921798706
    endloop
  endfacet
  facet normal -0.5306309461593628 -0.17219312489032745 0.829927921295166
    outer loop
      vertex -35.284000396728516 -2.7750000953674316 3.1570000648498535
      vertex -35.68299865722656 -2.7070000171661377 2.9159998893737793
      vertex -35.23899841308594 -3.9210000038146973 2.947999954223633
    endloop
  endfacet
  facet normal -0.2811545133590698 0.6719656586647034 0.6851381659507751
    outer loop
      vertex -91.70099639892578 -53.215999603271484 3.6619999408721924
      vertex -90.43800354003906 -53.542999267578125 4.500999927520752
      vertex -90.64700317382812 -52.775001525878906 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 -84 10.5
      vertex 82.99800109863281 -84 0
      vertex 82.99800109863281 83.0150146484375 3.5
    endloop
  endfacet
  facet normal -0.060092490166425705 -0.20231077075004578 0.9774759411811829
    outer loop
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
      vertex -35.70800018310547 -3.871999979019165 2.6449999809265137
      vertex -35.82500076293945 -2.697000026702881 2.88100004196167
    endloop
  endfacet
  facet normal -0.21269163489341736 0.5083377957344055 0.8344788551330566
    outer loop
      vertex -91.70099639892578 -53.215999603271484 3.6619999408721924
      vertex -90.64700317382812 -52.775001525878906 3.6619999408721924
      vertex -92.18800354003906 -52.37900161743164 3.0280001163482666
    endloop
  endfacet
  facet normal -0.31041207909584045 0.33507779240608215 0.8895882368087769
    outer loop
      vertex -35.426998138427734 -55.834999084472656 3.928999900817871
      vertex -35.89799880981445 -55.220001220703125 3.5329999923706055
      vertex -35.97999954223633 -55.88800048828125 3.75600004196167
    endloop
  endfacet
  facet normal -0.37389957904815674 0.28247517347335815 0.883406400680542
    outer loop
      vertex -35.89799880981445 -55.220001220703125 3.5329999923706055
      vertex -35.426998138427734 -55.834999084472656 3.928999900817871
      vertex -35.38600158691406 -55.14899826049805 3.7269999980926514
    endloop
  endfacet
  facet normal -0.3486056327819824 -0.0748986303806305 0.934272050857544
    outer loop
      vertex -35.70800018310547 -3.871999979019165 2.6449999809265137
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
    endloop
  endfacet
  facet normal -0.2098587304353714 0.2715698480606079 0.9392598867416382
    outer loop
      vertex -92.18800354003906 -52.37900161743164 3.0280001163482666
      vertex -92.73500061035156 -51.43899917602539 2.634000062942505
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
    endloop
  endfacet
  facet normal -0.3493123948574066 -0.21782536804676056 0.911335825920105
    outer loop
      vertex -35.70800018310547 -3.871999979019165 2.6449999809265137
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
      vertex -35.82500076293945 -2.697000026702881 2.88100004196167
    endloop
  endfacet
  facet normal -0.20985817909240723 0.2716101109981537 0.9392483830451965
    outer loop
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
      vertex -93.29199981689453 -53.231998443603516 3.0280001163482666
      vertex -92.18800354003906 -52.37900161743164 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6016197800636292 -0.1996452957391739 0.7734309434890747
    outer loop
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
      vertex -35.23899841308594 -3.9210000038146973 2.947999954223633
      vertex -35.68299865722656 -2.7070000171661377 2.9159998893737793
    endloop
  endfacet
  facet normal -0.21250410377979279 0.5087459087371826 0.8342779278755188
    outer loop
      vertex -92.18800354003906 -52.37900161743164 3.0280001163482666
      vertex -90.64700317382812 -52.775001525878906 3.6619999408721924
      vertex -90.9000015258789 -51.840999603271484 3.0280001163482666
    endloop
  endfacet
  facet normal -0.24778452515602112 -0.2028394341468811 0.947343111038208
    outer loop
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
      vertex -35.68299865722656 -2.7070000171661377 2.9159998893737793
      vertex -35.82500076293945 -2.697000026702881 2.88100004196167
    endloop
  endfacet
  facet normal -0.07385952025651932 0.5462444424629211 0.8343631029129028
    outer loop
      vertex -89.51399993896484 -52.62200164794922 3.6619999408721924
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
      vertex -90.9000015258789 -51.840999603271484 3.0280001163482666
    endloop
  endfacet
  facet normal 0.34875234961509705 0.3591412603855133 0.865672767162323
    outer loop
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
      vertex -36.06999969482422 -55.220001220703125 3.5309998989105225
    endloop
  endfacet
  facet normal -0.07377797365188599 0.5463427305221558 0.8343059420585632
    outer loop
      vertex -90.64700317382812 -52.775001525878906 3.6619999408721924
      vertex -89.51399993896484 -52.62200164794922 3.6619999408721924
      vertex -90.9000015258789 -51.840999603271484 3.0280001163482666
    endloop
  endfacet
  facet normal 0.06332989782094955 -0.09130986034870148 0.9938067197799683
    outer loop
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
      vertex -35.70800018310547 -3.871999979019165 2.6449999809265137
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
    endloop
  endfacet
  facet normal -0.1323351413011551 0.316542387008667 0.9393020272254944
    outer loop
      vertex -91.18499755859375 -50.79100036621094 2.634000062942505
      vertex -92.73500061035156 -51.43899917602539 2.634000062942505
      vertex -90.9000015258789 -51.840999603271484 3.0280001163482666
    endloop
  endfacet
  facet normal 0.2784997522830963 -0.6729879975318909 0.6852189898490906
    outer loop
      vertex -38.310001373291016 -2.7920000553131104 3.6619999408721924
      vertex -39.571998596191406 -2.4600000381469727 4.500999927520752
      vertex -39.36600112915039 -3.2290000915527344 3.6619999408721924
    endloop
  endfacet
  facet normal 0.2787246108055115 -0.672676146030426 0.6854337453842163
    outer loop
      vertex -38.310001373291016 -2.7920000553131104 3.6619999408721924
      vertex -38.70800018310547 -2.1019999980926514 4.500999927520752
      vertex -39.571998596191406 -2.4600000381469727 4.500999927520752
    endloop
  endfacet
  facet normal -0.13228878378868103 0.31670624017715454 0.9392533302307129
    outer loop
      vertex -92.18800354003906 -52.37900161743164 3.0280001163482666
      vertex -90.9000015258789 -51.840999603271484 3.0280001163482666
      vertex -92.73500061035156 -51.43899917602539 2.634000062942505
    endloop
  endfacet
  facet normal 0.44362279772758484 -0.5774745345115662 0.685362696647644
    outer loop
      vertex -38.70800018310547 -2.1019999980926514 4.500999927520752
      vertex -38.310001373291016 -2.7920000553131104 3.6619999408721924
      vertex -37.40399932861328 -2.0959999561309814 3.6619999408721924
    endloop
  endfacet
  facet normal -0.045970600098371506 0.33998578786849976 0.9393063187599182
    outer loop
      vertex -90.9000015258789 -51.840999603271484 3.0280001163482666
      vertex -89.51699829101562 -51.65399932861328 3.0280001163482666
      vertex -91.18499755859375 -50.79100036621094 2.634000062942505
    endloop
  endfacet
  facet normal 0.5777965784072876 -0.44338083267211914 0.6852477788925171
    outer loop
      vertex -37.40399932861328 -2.0959999561309814 3.6619999408721924
      vertex -36.70800018310547 -1.1890000104904175 3.6619999408721924
      vertex -37.96699905395508 -1.5329999923706055 4.500999927520752
    endloop
  endfacet
  facet normal 0.3357890248298645 -0.4371047019958496 0.834377110004425
    outer loop
      vertex -37.40399932861328 -2.0959999561309814 3.6619999408721924
      vertex -38.310001373291016 -2.7920000553131104 3.6619999408721924
      vertex -36.71900177001953 -2.7799999713897705 3.0280001163482666
    endloop
  endfacet
  facet normal -0.011024143546819687 0.3178517818450928 0.9480763077735901
    outer loop
      vertex -35.89799880981445 -55.220001220703125 3.5329999923706055
      vertex -36.06999969482422 -55.220001220703125 3.5309998989105225
      vertex -35.97999954223633 -55.88800048828125 3.75600004196167
    endloop
  endfacet
  facet normal -0.04237050563097 0.11536610126495361 0.9924189448356628
    outer loop
      vertex -93.53199768066406 -50.57899856567383 2.5
      vertex -92.73500061035156 -51.43899917602539 2.634000062942505
      vertex -90.87999725341797 -49.60499954223633 2.5
    endloop
  endfacet
  facet normal 0.43259090185165405 0.251089483499527 0.8659210205078125
    outer loop
      vertex -36.06999969482422 -55.220001220703125 3.5309998989105225
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
      vertex -36.1609992980957 -55.88399887084961 3.7690000534057617
    endloop
  endfacet
  facet normal 0.679547905921936 -0.2653864026069641 0.6839479207992554
    outer loop
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
      vertex -37.39699935913086 -0.7910000085830688 4.500999927520752
      vertex -36.70800018310547 -1.1890000104904175 3.6619999408721924
    endloop
  endfacet
  facet normal 0.5777515769004822 -0.4438253343105316 0.6849979758262634
    outer loop
      vertex -37.39699935913086 -0.7910000085830688 4.500999927520752
      vertex -37.96699905395508 -1.5329999923706055 4.500999927520752
      vertex -36.70800018310547 -1.1890000104904175 3.6619999408721924
    endloop
  endfacet
  facet normal 0.45197242498397827 -0.34682780504226685 0.8218463063240051
    outer loop
      vertex -36.70800018310547 -1.1890000104904175 3.6619999408721924
      vertex -37.40399932861328 -2.0959999561309814 3.6619999408721924
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
    endloop
  endfacet
  facet normal -0.06970368325710297 0.09020077437162399 0.9934813380241394
    outer loop
      vertex -92.73500061035156 -51.43899917602539 2.634000062942505
      vertex -93.53199768066406 -50.57899856567383 2.5
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
    endloop
  endfacet
  facet normal 0.44770383834838867 -0.3241007924079895 0.8333786725997925
    outer loop
      vertex -36.71900177001953 -2.7799999713897705 3.0280001163482666
      vertex -36.446998596191406 -1.7280000448226929 3.2909998893737793
      vertex -37.40399932861328 -2.0959999561309814 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5647135376930237 -0.2330128699541092 0.791709303855896
    outer loop
      vertex -35.35100173950195 14.442000389099121 2.7929999828338623
      vertex -35.520999908447266 14.854000091552734 2.7929999828338623
      vertex -35.70100021362305 14.75 2.634000062942505
    endloop
  endfacet
  facet normal -0.9386153817176819 0.21272751688957214 0.2715662121772766
    outer loop
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.66799926757812 -55.63399887084961 3.0280001163482666
    endloop
  endfacet
  facet normal -0.0750485211610794 0.09167042374610901 0.992957353591919
    outer loop
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
      vertex -93.53199768066406 -50.57899856567383 2.5
    endloop
  endfacet
  facet normal -0.5654367208480835 -0.234296977519989 0.790813684463501
    outer loop
      vertex -35.70100021362305 14.75 2.634000062942505
      vertex -35.55099868774414 14.387999534606934 2.634000062942505
      vertex -35.35100173950195 14.442000389099121 2.7929999828338623
    endloop
  endfacet
  facet normal 0.09493660926818848 -0.7221407890319824 0.6852005124092102
    outer loop
      vertex -39.36600112915039 -3.2290000915527344 3.6619999408721924
      vertex -39.571998596191406 -2.4600000381469727 4.500999927520752
      vertex -40.5 -2.5820000171661377 4.500999927520752
    endloop
  endfacet
  facet normal -0.07895788550376892 0.08637557178735733 0.9931288361549377
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
      vertex -94.9990005493164 -51.779998779296875 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -93.53199768066406 -50.57899856567383 2.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0.21081587672233582 -0.5094314813613892 0.8342878222465515
    outer loop
      vertex -37.82600021362305 -3.630000114440918 3.0280001163482666
      vertex -38.310001373291016 -2.7920000553131104 3.6619999408721924
      vertex -39.36600112915039 -3.2290000915527344 3.6619999408721924
    endloop
  endfacet
  facet normal -0.44520196318626404 0.5759605765342712 0.6856125593185425
    outer loop
      vertex -92.60600280761719 -53.91400146484375 3.6619999408721924
      vertex -92.04100036621094 -54.47600173950195 4.500999927520752
      vertex -91.3010025024414 -53.90399932861328 4.500999927520752
    endloop
  endfacet
  facet normal 0.33575916290283203 -0.4372769296169281 0.8342989087104797
    outer loop
      vertex -36.71900177001953 -2.7799999713897705 3.0280001163482666
      vertex -38.310001373291016 -2.7920000553131104 3.6619999408721924
      vertex -37.82600021362305 -3.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal 0.15638668835163116 0.10977073758840561 0.9815770983695984
    outer loop
      vertex -36.22200012207031 -56.426998138427734 3.9200000762939453
      vertex -36.249000549316406 -56.933998107910156 3.9809999465942383
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
    endloop
  endfacet
  facet normal -0.4448806345462799 0.576815128326416 0.6851025819778442
    outer loop
      vertex -91.70099639892578 -53.215999603271484 3.6619999408721924
      vertex -92.60600280761719 -53.91400146484375 3.6619999408721924
      vertex -91.3010025024414 -53.90399932861328 4.500999927520752
    endloop
  endfacet
  facet normal -0.3572516143321991 -0.14803244173526764 0.9222026467323303
    outer loop
      vertex -35.909000396728516 14.628999710083008 2.5339999198913574
      vertex -35.55099868774414 14.387999534606934 2.634000062942505
      vertex -35.70100021362305 14.75 2.634000062942505
    endloop
  endfacet
  facet normal -0.28111302852630615 0.6720236539840698 0.6850982904434204
    outer loop
      vertex -91.3010025024414 -53.90399932861328 4.500999927520752
      vertex -90.43800354003906 -53.542999267578125 4.500999927520752
      vertex -91.70099639892578 -53.215999603271484 3.6619999408721924
    endloop
  endfacet
  facet normal 0.13467828929424286 0.10308811813592911 0.985512375831604
    outer loop
      vertex -36.0359992980957 -56.430999755859375 3.8949999809265137
      vertex -36.22200012207031 -56.426998138427734 3.9200000762939453
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
    endloop
  endfacet
  facet normal 0.22828583419322968 -0.29730871319770813 0.9270884990692139
    outer loop
      vertex -36.71900177001953 -2.7799999713897705 3.0280001163482666
      vertex -37.82600021362305 -3.630000114440918 3.0280001163482666
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
    endloop
  endfacet
  facet normal -0.5795491933822632 0.4407121241092682 0.685489296913147
    outer loop
      vertex -92.60600280761719 -53.91400146484375 3.6619999408721924
      vertex -93.2979965209961 -54.82400131225586 3.6619999408721924
      vertex -92.04100036621094 -54.47600173950195 4.500999927520752
    endloop
  endfacet
  facet normal 0.09488951414823532 -0.7221792340278625 0.6851664781570435
    outer loop
      vertex -39.36600112915039 -3.2290000915527344 3.6619999408721924
      vertex -40.5 -2.5820000171661377 4.500999927520752
      vertex -40.5 -3.378000020980835 3.6619999408721924
    endloop
  endfacet
  facet normal -0.48309147357940674 0.1981721967458725 0.8528484106063843
    outer loop
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
      vertex -94.66799926757812 -55.63399887084961 3.0280001163482666
      vertex -94.13800048828125 -54.34199905395508 3.0280001163482666
    endloop
  endfacet
  facet normal -0.3368067443370819 0.43669068813323975 0.8341836929321289
    outer loop
      vertex -92.60600280761719 -53.91400146484375 3.6619999408721924
      vertex -91.70099639892578 -53.215999603271484 3.6619999408721924
      vertex -93.29199981689453 -53.231998443603516 3.0280001163482666
    endloop
  endfacet
  facet normal 0.15570195019245148 -0.08816996216773987 0.9838612675666809
    outer loop
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
      vertex -36.249000549316406 -56.933998107910156 3.9809999465942383
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
    endloop
  endfacet
  facet normal -0.5794787406921387 0.4414333701133728 0.6850846409797668
    outer loop
      vertex -92.60700225830078 -55.21900177001953 4.500999927520752
      vertex -92.04100036621094 -54.47600173950195 4.500999927520752
      vertex -93.2979965209961 -54.82400131225586 3.6619999408721924
    endloop
  endfacet
  facet normal -0.37894925475120544 -0.9161006212234497 0.13098515570163727
    outer loop
      vertex -49.499000549316406 16.134000778198242 3.5
      vertex -49.51599884033203 16.104000091552734 3.240999937057495
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
    endloop
  endfacet
  facet normal 0.07181254774332047 -0.546546459197998 0.8343439698219299
    outer loop
      vertex -39.11600112915039 -4.164000034332275 3.0280001163482666
      vertex -39.36600112915039 -3.2290000915527344 3.6619999408721924
      vertex -40.5 -3.378000020980835 3.6619999408721924
    endloop
  endfacet
  facet normal -0.37214648723602295 -0.4861249327659607 0.7906892895698547
    outer loop
      vertex -36.145999908447266 15.477999687194824 2.7929999828338623
      vertex -36.25 15.298999786376953 2.634000062942505
      vertex -35.79199981689453 15.206999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.38000741600990295 -0.9158178567886353 0.12989211082458496
    outer loop
      vertex -49.257999420166016 16.034000396728516 3.5
      vertex -49.499000549316406 16.134000778198242 3.5
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
    endloop
  endfacet
  facet normal -0.43861106038093567 0.3342927396297455 0.8341874480247498
    outer loop
      vertex -93.29199981689453 -53.231998443603516 3.0280001163482666
      vertex -94.13800048828125 -54.34199905395508 3.0280001163482666
      vertex -92.60600280761719 -53.91400146484375 3.6619999408721924
    endloop
  endfacet
  facet normal -0.794902503490448 -0.6067371964454651 0
    outer loop
      vertex -49.8650016784668 16.5 3.5
      vertex -49.707000732421875 16.292999267578125 3.5
      vertex -49.707000732421875 16.292999267578125 10.5
    endloop
  endfacet
  facet normal 0.21085025370121002 -0.5093573331832886 0.8343244194984436
    outer loop
      vertex -37.82600021362305 -3.630000114440918 3.0280001163482666
      vertex -39.36600112915039 -3.2290000915527344 3.6619999408721924
      vertex -39.11600112915039 -4.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal -0.43853506445884705 0.3334794044494629 0.8345528841018677
    outer loop
      vertex -94.13800048828125 -54.34199905395508 3.0280001163482666
      vertex -93.2979965209961 -54.82400131225586 3.6619999408721924
      vertex -92.60600280761719 -53.91400146484375 3.6619999408721924
    endloop
  endfacet
  facet normal -0.08597089350223541 -0.3204832077026367 0.9433448314666748
    outer loop
      vertex -37 15.258999824523926 2.5339999198913574
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
      vertex -36.611000061035156 15.449000358581543 2.634000062942505
    endloop
  endfacet
  facet normal -0.27295053005218506 0.20803257822990417 0.9392659068107605
    outer loop
      vertex -93.29199981689453 -53.231998443603516 3.0280001163482666
      vertex -94.06400299072266 -52.465999603271484 2.634000062942505
      vertex -94.13800048828125 -54.34199905395508 3.0280001163482666
    endloop
  endfacet
  facet normal -0.9236428737640381 0 0.3832542896270752
    outer loop
      vertex -35.13399887084961 -5.103000164031982 3
      vertex -35.13399887084961 -50.89699935913086 3
      vertex -35.034000396728516 -5.103000164031982 3.240999937057495
    endloop
  endfacet
  facet normal -0.9914817810058594 -0.0048257033340632915 0.13015590608119965
    outer loop
      vertex -35.034000396728516 -5.103000164031982 3.240999937057495
      vertex -35 -5.103000164031982 3.5
      vertex -35.018001556396484 -3.99399995803833 3.4040000438690186
    endloop
  endfacet
  facet normal -0.26733165979385376 0.09520923346281052 0.9588894248008728
    outer loop
      vertex -35.45500183105469 -56.4010009765625 4.053999900817871
      vertex -36.0359992980957 -56.430999755859375 3.8949999809265137
      vertex -35.46799850463867 -56.930999755859375 4.103000164031982
    endloop
  endfacet
  facet normal -0.7220473885536194 0.09296201169490814 0.6855695843696594
    outer loop
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
      vertex -93.87799835205078 -57.01499938964844 3.6619999408721924
      vertex -93.08100128173828 -57.012001037597656 4.500999927520752
    endloop
  endfacet
  facet normal -0.9292193055152893 -0.04057837277650833 0.3672940135002136
    outer loop
      vertex -35.034000396728516 -5.103000164031982 3.240999937057495
      vertex -35.018001556396484 -3.99399995803833 3.4040000438690186
      vertex -35.15800094604492 -3.937999963760376 3.055999994277954
    endloop
  endfacet
  facet normal -0.14808054268360138 -0.35638049244880676 0.9225319027900696
    outer loop
      vertex -36.25 15.298999786376953 2.634000062942505
      vertex -36.611000061035156 15.449000358581543 2.634000062942505
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
    endloop
  endfacet
  facet normal -0.6020945906639099 -0.7876457571983337 0.1307528167963028
    outer loop
      vertex -49.51599884033203 16.104000091552734 3.240999937057495
      vertex -49.499000549316406 16.134000778198242 3.5
      vertex -49.707000732421875 16.292999267578125 3.5
    endloop
  endfacet
  facet normal -0.2792457342147827 -0.2792457342147827 0.9187184572219849
    outer loop
      vertex -35.70100021362305 14.75 2.634000062942505
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
      vertex -35.909000396728516 14.628999710083008 2.5339999198913574
    endloop
  endfacet
  facet normal -0.3721446990966797 -0.486289918422699 0.7905886769294739
    outer loop
      vertex -35.79199981689453 15.206999778747559 2.7929999828338623
      vertex -36.25 15.298999786376953 2.634000062942505
      vertex -35.93899917602539 15.060999870300293 2.634000062942505
    endloop
  endfacet
  facet normal -0.35378825664520264 -0.8552745580673218 0.3786017596721649
    outer loop
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
      vertex -49.51599884033203 16.104000091552734 3.240999937057495
      vertex -49.566001892089844 16.01799964904785 3
    endloop
  endfacet
  facet normal -0.4853837788105011 -0.3726317286491394 0.7909160256385803
    outer loop
      vertex -35.520999908447266 14.854000091552734 2.7929999828338623
      vertex -35.79199981689453 15.206999778747559 2.7929999828338623
      vertex -35.93899917602539 15.060999870300293 2.634000062942505
    endloop
  endfacet
  facet normal -0.26723554730415344 0.26474350690841675 0.9265506267547607
    outer loop
      vertex -35.45500183105469 -56.4010009765625 4.053999900817871
      vertex -35.97999954223633 -55.88800048828125 3.75600004196167
      vertex -36.0359992980957 -56.430999755859375 3.8949999809265137
    endloop
  endfacet
  facet normal -0.6037442088127136 -0.7866969704627991 0.1288439780473709
    outer loop
      vertex -49.51599884033203 16.104000091552734 3.240999937057495
      vertex -49.707000732421875 16.292999267578125 3.5
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal -0.48500680923461914 -0.3711627721786499 0.7918374538421631
    outer loop
      vertex -35.93899917602539 15.060999870300293 2.634000062942505
      vertex -35.70100021362305 14.75 2.634000062942505
      vertex -35.520999908447266 14.854000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal -0.23465722799301147 -0.3066319227218628 0.9224493503570557
    outer loop
      vertex -35.93899917602539 15.060999870300293 2.634000062942505
      vertex -36.25 15.298999786376953 2.634000062942505
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
    endloop
  endfacet
  facet normal 0.07482068240642548 0.2400451898574829 0.9678740501403809
    outer loop
      vertex -35.97999954223633 -55.88800048828125 3.75600004196167
      vertex -36.1609992980957 -55.88399887084961 3.7690000534057617
      vertex -36.0359992980957 -56.430999755859375 3.8949999809265137
    endloop
  endfacet
  facet normal 0.134240061044693 0.2514669597148895 0.9585113525390625
    outer loop
      vertex -36.0359992980957 -56.430999755859375 3.8949999809265137
      vertex -36.1609992980957 -55.88399887084961 3.7690000534057617
      vertex -36.22200012207031 -56.426998138427734 3.9200000762939453
    endloop
  endfacet
  facet normal -0.2337752878665924 -0.17890198528766632 0.9556899070739746
    outer loop
      vertex -35.93899917602539 15.060999870300293 2.634000062942505
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
      vertex -35.70100021362305 14.75 2.634000062942505
    endloop
  endfacet
  facet normal -0.6737880706787109 0.2766546905040741 0.685180127620697
    outer loop
      vertex -93.2979965209961 -54.82400131225586 3.6619999408721924
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
      vertex -92.60700225830078 -55.21900177001953 4.500999927520752
    endloop
  endfacet
  facet normal -0.5634292364120483 -0.7341653108596802 0.37887832522392273
    outer loop
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
      vertex -49.566001892089844 16.01799964904785 3
      vertex -49.51599884033203 16.104000091552734 3.240999937057495
    endloop
  endfacet
  facet normal -0.353948712348938 -0.8551150560379028 0.3788120746612549
    outer loop
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
      vertex -49.566001892089844 16.01799964904785 3
      vertex -49.292999267578125 15.904999732971191 3
    endloop
  endfacet
  facet normal -0.6036890745162964 0.08806166052818298 0.7923412919044495
    outer loop
      vertex -35.45500183105469 -56.4010009765625 4.053999900817871
      vertex -35.46799850463867 -56.930999755859375 4.103000164031982
      vertex -35.31399917602539 -56.928001403808594 4.21999979019165
    endloop
  endfacet
  facet normal -0.05018339678645134 -0.38277140259742737 0.9224790930747986
    outer loop
      vertex -36.611000061035156 15.449000358581543 2.634000062942505
      vertex -37 15.5 2.634000062942505
      vertex -37 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal -0.7869138717651367 -0.603055477142334 0.13073112070560455
    outer loop
      vertex -49.8650016784668 16.5 3.5
      vertex -49.89500045776367 16.482999801635742 3.240999937057495
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal 0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -90.46499633789062 -57.25899887084961 5.5
      vertex -90.4990005493164 -57 0
      vertex -90.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal -0.7882814407348633 -0.6016834378242493 0.12879984080791473
    outer loop
      vertex -49.707000732421875 16.292999267578125 3.5
      vertex -49.8650016784668 16.5 3.5
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal -0.034910790622234344 -0.13014081120491028 0.9908807277679443
    outer loop
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
      vertex -37 15.258999824523926 2.5339999198913574
      vertex -36.5 14.866000175476074 2.5
    endloop
  endfacet
  facet normal 0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -90.46499633789062 -56.74100112915039 0
      vertex -90.46499633789062 -56.74100112915039 5.5
      vertex -90.4990005493164 -57 0
    endloop
  endfacet
  facet normal 0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -90.4990005493164 -57 5.5
      vertex -90.4990005493164 -57 0
      vertex -90.46499633789062 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.5625253319740295 -0.7344080805778503 0.37974998354911804
    outer loop
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
      vertex -49.80099868774414 16.197999954223633 3
      vertex -49.566001892089844 16.01799964904785 3
    endloop
  endfacet
  facet normal 0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -90.46499633789062 -56.74100112915039 0
      vertex -90.36499786376953 -56.5 0
      vertex -90.46499633789062 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.09517128765583038 -0.09517128765583038 0.9909010529518127
    outer loop
      vertex -36.5 14.866000175476074 2.5
      vertex -36.13399887084961 14.5 2.5
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
    endloop
  endfacet
  facet normal -0.09517128765583038 -0.09517128765583038 0.9909010529518127
    outer loop
      vertex -35.909000396728516 14.628999710083008 2.5339999198913574
      vertex -36.369998931884766 15.09000015258789 2.5339999198913574
      vertex -36.13399887084961 14.5 2.5
    endloop
  endfacet
  facet normal -0.31039074063301086 0.21961577236652374 0.9248927235603333
    outer loop
      vertex -35.426998138427734 -55.834999084472656 3.928999900817871
      vertex -35.97999954223633 -55.88800048828125 3.75600004196167
      vertex -35.45500183105469 -56.4010009765625 4.053999900817871
    endloop
  endfacet
  facet normal 0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -90.46499633789062 -57.25899887084961 5.5
      vertex -90.46499633789062 -57.25899887084961 0
      vertex -90.4990005493164 -57 0
    endloop
  endfacet
  facet normal -0.7330592274665833 -0.5646116137504578 0.3792596459388733
    outer loop
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
      vertex -49.981998443603516 16.433000564575195 3
      vertex -49.80099868774414 16.197999954223633 3
    endloop
  endfacet
  facet normal 0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -90.36499786376953 -56.5 5.5
      vertex -90.46499633789062 -56.74100112915039 5.5
      vertex -90.36499786376953 -56.5 0
    endloop
  endfacet
  facet normal -0.7336912155151367 -0.5622680187225342 0.3815126121044159
    outer loop
      vertex -49.89500045776367 16.482999801635742 3.240999937057495
      vertex -49.981998443603516 16.433000564575195 3
      vertex -49.73099899291992 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -90.20600128173828 -56.292999267578125 0
      vertex -90.20600128173828 -56.292999267578125 5.5
      vertex -90.36499786376953 -56.5 0
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -90.36499786376953 -56.5 5.5
      vertex -90.36499786376953 -56.5 0
      vertex -90.20600128173828 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -89.9990005493164 -56.13399887084961 0
      vertex -89.9990005493164 -56.13399887084961 5.5
      vertex -90.20600128173828 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -90.20600128173828 -56.292999267578125 0
      vertex -89.9990005493164 -56.13399887084961 0
      vertex -90.20600128173828 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal 0.5777515769004822 0.4438253343105316 0.6849979758262634
    outer loop
      vertex -37.96699905395508 -54.46699905395508 4.500999927520752
      vertex -37.39699935913086 -55.20899963378906 4.500999927520752
      vertex -36.70800018310547 -54.81100082397461 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
    endloop
  endfacet
  facet normal 0.5777965784072876 0.44338083267211914 0.6852477788925171
    outer loop
      vertex -36.70800018310547 -54.81100082397461 3.6619999408721924
      vertex -37.40399932861328 -53.90399932861328 3.6619999408721924
      vertex -37.96699905395508 -54.46699905395508 4.500999927520752
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -94.9990005493164 -82 0
      vertex -94.9990005493164 -51.779998779296875 2.5
    endloop
  endfacet
  facet normal 0.44852784276008606 0.32319197058677673 0.8332884907722473
    outer loop
      vertex -37.40399932861328 -53.90399932861328 3.6619999408721924
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
      vertex -36.71900177001953 -53.220001220703125 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5099067091941833 0.20936566591262817 0.8343627452850342
    outer loop
      vertex -93.2979965209961 -54.82400131225586 3.6619999408721924
      vertex -94.66799926757812 -55.63399887084961 3.0280001163482666
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5467227101325989 0.06992045789957047 0.8343892693519592
    outer loop
      vertex -94.66799926757812 -55.63399887084961 3.0280001163482666
      vertex -94.84500122070312 -57.018001556396484 3.0280001163482666
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5470884442329407 0.07043643295764923 0.8341060280799866
    outer loop
      vertex -94.84500122070312 -57.018001556396484 3.0280001163482666
      vertex -93.87799835205078 -57.01499938964844 3.6619999408721924
      vertex -93.73200225830078 -55.88100051879883 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3357890248298645 0.4371047019958496 0.834377110004425
    outer loop
      vertex -36.71900177001953 -53.220001220703125 3.0280001163482666
      vertex -38.310001373291016 -53.20800018310547 3.6619999408721924
      vertex -37.40399932861328 -53.90399932861328 3.6619999408721924
    endloop
  endfacet
  facet normal 0.4531416893005371 0.3477250337600708 0.8208227157592773
    outer loop
      vertex -37.40399932861328 -53.90399932861328 3.6619999408721924
      vertex -36.70800018310547 -54.81100082397461 3.6619999408721924
      vertex -36.446998596191406 -54.27299880981445 3.2899999618530273
    endloop
  endfacet
  facet normal -0.9831556081771851 -0.1294134110212326 0.12906289100646973
    outer loop
      vertex -35.034000396728516 14 3.240999937057495
      vertex -35 14 3.5
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
    endloop
  endfacet
  facet normal 0.2784997522830963 0.6729879975318909 0.6852189898490906
    outer loop
      vertex -39.571998596191406 -53.540000915527344 4.500999927520752
      vertex -38.310001373291016 -53.20800018310547 3.6619999408721924
      vertex -39.36600112915039 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -35 14 3.5
      vertex -35 14 10.5
      vertex -35.06800079345703 14.517999649047852 3.5
    endloop
  endfacet
  facet normal -0.9831125140190125 -0.12905724346637726 0.12974604964256287
    outer loop
      vertex -35 14 3.5
      vertex -35.06800079345703 14.517999649047852 3.5
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
    endloop
  endfacet
  facet normal -0.42726847529411316 0.05464344099164009 0.9024720191955566
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.84500122070312 -57.018001556396484 3.0280001163482666
      vertex -94.66799926757812 -55.63399887084961 3.0280001163482666
    endloop
  endfacet
  facet normal -0.9168911576271057 -0.1206909790635109 0.3804527521133423
    outer loop
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
      vertex -35.13399887084961 14 3
      vertex -35.034000396728516 14 3.240999937057495
    endloop
  endfacet
  facet normal 0.44362279772758484 0.5774745345115662 0.685362696647644
    outer loop
      vertex -37.40399932861328 -53.90399932861328 3.6619999408721924
      vertex -38.310001373291016 -53.20800018310547 3.6619999408721924
      vertex -38.70800018310547 -53.89799880981445 4.500999927520752
    endloop
  endfacet
  facet normal -0.9178187251091003 -0.11971548199653625 0.3785195052623749
    outer loop
      vertex -35.196998596191406 14.482999801635742 3
      vertex -35.13399887084961 14 3
      vertex -35.10100173950195 14.508999824523926 3.240999937057495
    endloop
  endfacet
  facet normal -0.7877839803695679 -0.10515668243169785 0.6069089770317078
    outer loop
      vertex -35.196998596191406 14.482999801635742 3
      vertex -35.35100173950195 14.442000389099121 2.7929999828338623
      vertex -35.29199981689453 14 2.7929999828338623
    endloop
  endfacet
  facet normal -0.5098221898078918 0.20913758873939514 0.834471583366394
    outer loop
      vertex -94.66799926757812 -55.63399887084961 3.0280001163482666
      vertex -93.2979965209961 -54.82400131225586 3.6619999408721924
      vertex -94.13800048828125 -54.34199905395508 3.0280001163482666
    endloop
  endfacet
  facet normal -0.3039374053478241 -0.7342912554740906 0.6069912314414978
    outer loop
      vertex -49.292999267578125 15.904999732971191 3
      vertex -49.566001892089844 16.01799964904785 3
      vertex -49.645999908447266 15.880000114440918 2.7929999828338623
    endloop
  endfacet
  facet normal -0.79066401720047 -0.10313008725643158 0.6035019755363464
    outer loop
      vertex -35.29199981689453 14 2.7929999828338623
      vertex -35.13399887084961 14 3
      vertex -35.196998596191406 14.482999801635742 3
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -40.24100112915039 -56.034000396728516 5.5
      vertex -40.5 -56 0
      vertex -40.24100112915039 -56.034000396728516 0
    endloop
  endfacet
  facet normal -0.6053225994110107 -0.08080098032951355 0.7918685078620911
    outer loop
      vertex -35.35100173950195 14.442000389099121 2.7929999828338623
      vertex -35.5 14 2.634000062942505
      vertex -35.29199981689453 14 2.7929999828338623
    endloop
  endfacet
  facet normal -0.4831351041793823 -0.6307597160339355 0.6072253584861755
    outer loop
      vertex -49.566001892089844 16.01799964904785 3
      vertex -49.80099868774414 16.197999954223633 3
      vertex -49.645999908447266 15.880000114440918 2.7929999828338623
    endloop
  endfacet
  facet normal -0.607032299041748 -0.07979033142328262 0.7906612753868103
    outer loop
      vertex -35.35100173950195 14.442000389099121 2.7929999828338623
      vertex -35.55099868774414 14.387999534606934 2.634000062942505
      vertex -35.5 14 2.634000062942505
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -40 -56.13399887084961 0
      vertex -40.24100112915039 -56.034000396728516 5.5
      vertex -40.24100112915039 -56.034000396728516 0
    endloop
  endfacet
  facet normal -0.32119220495224 -0.08578742295503616 0.9431204199790955
    outer loop
      vertex -35.55099868774414 14.387999534606934 2.634000062942505
      vertex -35.909000396728516 14.628999710083008 2.5339999198913574
      vertex -35.74100112915039 14 2.5339999198913574
    endloop
  endfacet
  facet normal -0.3827689290046692 -0.05031241104006767 0.9224730730056763
    outer loop
      vertex -35.5 14 2.634000062942505
      vertex -35.55099868774414 14.387999534606934 2.634000062942505
      vertex -35.74100112915039 14 2.5339999198913574
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -39.534000396728516 -56.74100112915039 0
      vertex -39.5 -57 0
      vertex -39.5 -57 5.5
    endloop
  endfacet
  facet normal -0.12985500693321228 -0.03468305617570877 0.990926206111908
    outer loop
      vertex -35.909000396728516 14.628999710083008 2.5339999198913574
      vertex -36.13399887084961 14.5 2.5
      vertex -35.74100112915039 14 2.5339999198913574
    endloop
  endfacet
  facet normal -0.4848131239414215 -0.6307277679443359 0.6059197783470154
    outer loop
      vertex -49.80099868774414 16.197999954223633 3
      vertex -49.91400146484375 16.086000442504883 2.7929999828338623
      vertex -49.645999908447266 15.880000114440918 2.7929999828338623
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -39.5 -57 5.5
      vertex -39.5 -57 0
      vertex -39.534000396728516 -57.25899887084961 0
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -36.481998443603516 15.932000160217285 10.5
      vertex -37 16 10.5
      vertex -36.481998443603516 15.932000160217285 3.5
    endloop
  endfacet
  facet normal -0.12905724346637726 -0.9831125140190125 0.12974604964256287
    outer loop
      vertex -37 16 3.5
      vertex -36.49100112915039 15.89900016784668 3.240999937057495
      vertex -36.481998443603516 15.932000160217285 3.5
    endloop
  endfacet
  facet normal -0.1294134110212326 -0.9831556081771851 0.12906289100646973
    outer loop
      vertex -37 16 3.5
      vertex -37 15.965999603271484 3.240999937057495
      vertex -36.49100112915039 15.89900016784668 3.240999937057495
    endloop
  endfacet
  facet normal -0.1206909790635109 -0.9168911576271057 0.3804527521133423
    outer loop
      vertex -37 15.866000175476074 3
      vertex -36.49100112915039 15.89900016784668 3.240999937057495
      vertex -37 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal 0.3312917649745941 0.7995174527168274 0.5010166168212891
    outer loop
      vertex -87.71900177001953 4.107999801635742 4.500999927520752
      vertex -88.7229995727539 3.8980000019073486 5.5
      vertex -87.9990005493164 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal -0.1128569096326828 0.8585976958274841 0.5000733733177185
    outer loop
      vertex -41.426998138427734 -53.540000915527344 4.500999927520752
      vertex -41.2760009765625 -54.10200119018555 5.5
      vertex -40.5 -54 5.5
    endloop
  endfacet
  facet normal -0.6316038966178894 -0.4864693880081177 0.6036754250526428
    outer loop
      vertex -49.80099868774414 16.197999954223633 3
      vertex -49.981998443603516 16.433000564575195 3
      vertex -50.11899948120117 16.354000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal 0 -0.9236428737640381 0.3832542896270752
    outer loop
      vertex -48.999000549316406 15.965999603271484 3.240999937057495
      vertex -37 15.866000175476074 3
      vertex -37 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal -0.6316648721694946 -0.48317649960517883 0.6062507033348083
    outer loop
      vertex -49.80099868774414 16.197999954223633 3
      vertex -50.11899948120117 16.354000091552734 2.7929999828338623
      vertex -49.91400146484375 16.086000442504883 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7362745404243469 -0.3054000735282898 0.6038464903831482
    outer loop
      vertex -49.981998443603516 16.433000564575195 3
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
      vertex -50.11899948120117 16.354000091552734 2.7929999828338623
    endloop
  endfacet
  facet normal 0.3289930522441864 0.801630973815918 0.49915066361427307
    outer loop
      vertex -87.71900177001953 4.107999801635742 4.500999927520752
      vertex -88.58399963378906 4.4629998207092285 4.500999927520752
      vertex -88.7229995727539 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal -0.3314758837223053 0.7999864816665649 0.5001453757286072
    outer loop
      vertex -41.426998138427734 -53.540000915527344 4.500999927520752
      vertex -42.29100036621094 -53.89799880981445 4.500999927520752
      vertex -41.2760009765625 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal 0.1127878800034523 0.8580725193023682 0.5009894967079163
    outer loop
      vertex -88.58399963378906 4.4629998207092285 4.500999927520752
      vertex -89.4990005493164 4 5.5
      vertex -88.7229995727539 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal -0.1045079380273819 -0.7887083292007446 0.6058194637298584
    outer loop
      vertex -36.516998291015625 15.802000045776367 3
      vertex -37 15.866000175476074 3
      vertex -37 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.5660281181335449 -0.2347833514213562 0.7902461290359497
    outer loop
      vertex -50.11899948120117 16.354000091552734 2.7929999828338623
      vertex -50.24800109863281 16.665000915527344 2.7929999828338623
      vertex -50.448001861572266 16.61199951171875 2.634000062942505
    endloop
  endfacet
  facet normal -0.33148324489593506 0.799979567527771 0.500151515007019
    outer loop
      vertex -42.29100036621094 -53.89799880981445 4.500999927520752
      vertex -42 -54.402000427246094 5.5
      vertex -41.2760009765625 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal -0.07961004972457886 -0.607221782207489 0.7905339598655701
    outer loop
      vertex -37 15.706999778747559 2.7929999828338623
      vertex -37 15.5 2.634000062942505
      vertex -36.611000061035156 15.449000358581543 2.634000062942505
    endloop
  endfacet
  facet normal 0.11031737178564072 0.8593630194664001 0.4993247985839844
    outer loop
      vertex -88.58399963378906 4.4629998207092285 4.500999927520752
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
      vertex -89.4990005493164 4 5.5
    endloop
  endfacet
  facet normal -0.03486098721623421 -0.13007831573486328 0.9908906817436218
    outer loop
      vertex -36.5 14.866000175476074 2.5
      vertex -37 15.258999824523926 2.5339999198913574
      vertex -37 15 2.5
    endloop
  endfacet
  facet normal -0.5273966789245605 0.6868206262588501 0.5001301765441895
    outer loop
      vertex -42.29100036621094 -53.89799880981445 4.500999927520752
      vertex -43.03200149536133 -54.46699905395508 4.500999927520752
      vertex -42 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.0973474532365799 0.7219287157058716 0.685085654258728
    outer loop
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
      vertex -90.64700317382812 5.224999904632568 3.6619999408721924
      vertex -90.43800354003906 4.456999778747559 4.500999927520752
    endloop
  endfacet
  facet normal -0.5274690985679626 0.6867050528526306 0.5002124905586243
    outer loop
      vertex -43.03200149536133 -54.46699905395508 4.500999927520752
      vertex -42.62099838256836 -54.87900161743164 5.5
      vertex -42 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.1035093292593956 -0.7880824208259583 0.6068047285079956
    outer loop
      vertex -49.292999267578125 15.904999732971191 3
      vertex -49.33399963378906 15.75100040435791 2.7929999828338623
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal 0 -0.7930510640144348 0.6091551780700684
    outer loop
      vertex -37 15.706999778747559 2.7929999828338623
      vertex -37 15.866000175476074 3
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.30373790860176086 -0.7346219420433044 0.6066909432411194
    outer loop
      vertex -49.292999267578125 15.904999732971191 3
      vertex -49.645999908447266 15.880000114440918 2.7929999828338623
      vertex -49.33399963378906 15.75100040435791 2.7929999828338623
    endloop
  endfacet
  facet normal 0 -0.6091551780700684 0.7930510640144348
    outer loop
      vertex -37 15.5 2.634000062942505
      vertex -37 15.706999778747559 2.7929999828338623
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6867327690124512 0.5275440216064453 0.5000954270362854
    outer loop
      vertex -43.03200149536133 -54.46699905395508 4.500999927520752
      vertex -43.60200119018555 -55.20899963378906 4.500999927520752
      vertex -42.62099838256836 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal -0.07959090173244476 -0.6070756912231445 0.7906481027603149
    outer loop
      vertex -49.33399963378906 15.75100040435791 2.7929999828338623
      vertex -49.38800048828125 15.550999641418457 2.634000062942505
      vertex -48.999000549316406 15.5 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42.62099838256836 -54.87900161743164 5.5
      vertex -41 -56.13399887084961 5.5
      vertex -42 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal 0.9249957203865051 0.3799774944782257 0
    outer loop
      vertex -41.46500015258789 -57.25899887084961 5.5
      vertex -41.36600112915039 -57.5 5.5
      vertex -41.46500015258789 -57.25899887084961 0
    endloop
  endfacet
  facet normal 0.9909924268722534 0.133917897939682 0
    outer loop
      vertex -41.5 -57 5.5
      vertex -41.46500015258789 -57.25899887084961 5.5
      vertex -41.46500015258789 -57.25899887084961 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.46500015258789 -57.25899887084961 5.5
      vertex -43.39699935913086 -57.7760009765625 5.5
      vertex -41.36600112915039 -57.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.5 -57 5.5
      vertex -43.39699935913086 -57.7760009765625 5.5
      vertex -41.46500015258789 -57.25899887084961 5.5
    endloop
  endfacet
  facet normal 0 -0.13015742599964142 0.9914933443069458
    outer loop
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
      vertex -48.999000549316406 15 2.5
      vertex -37 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.46500015258789 -56.74100112915039 5.5
      vertex -43.39699935913086 -56.2239990234375 5.5
      vertex -41.5 -57 5.5
    endloop
  endfacet
  facet normal -0.23433411121368408 -0.5667615532875061 0.7898536920547485
    outer loop
      vertex -49.645999908447266 15.880000114440918 2.7929999828338623
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
      vertex -49.33399963378906 15.75100040435791 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.097999572753906 -58.5 5.5
      vertex -41.36600112915039 -57.5 5.5
      vertex -43.39699935913086 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.207000732421875 -56.292999267578125 5.5
      vertex -42.62099838256836 -54.87900161743164 5.5
      vertex -41.36600112915039 -56.5 5.5
    endloop
  endfacet
  facet normal -0.37193357944488525 -0.4860140383243561 0.7908576130867004
    outer loop
      vertex -49.91400146484375 16.086000442504883 2.7929999828338623
      vertex -50.060001373291016 15.939000129699707 2.634000062942505
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
    endloop
  endfacet
  facet normal -0.3738528788089752 -0.4863716959953308 0.7897319793701172
    outer loop
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
      vertex -49.645999908447266 15.880000114440918 2.7929999828338623
      vertex -49.91400146484375 16.086000442504883 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.36600112915039 -56.5 5.5
      vertex -43.39699935913086 -56.2239990234375 5.5
      vertex -41.46500015258789 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41 -56.13399887084961 5.5
      vertex -42.62099838256836 -54.87900161743164 5.5
      vertex -41.207000732421875 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal 0.3819020092487335 -0.9242027997970581 0
    outer loop
      vertex -40.757999420166016 -56.034000396728516 0
      vertex -40.757999420166016 -56.034000396728516 5.5
      vertex -41 -56.13399887084961 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 0 0.6067371964454651
    outer loop
      vertex -35.29199981689453 7.103000164031982 2.7929999828338623
      vertex -35.13399887084961 7.103000164031982 3
      vertex -35.29199981689453 14 2.7929999828338623
    endloop
  endfacet
  facet normal -0.23486930131912231 -0.5652521252632141 0.7907758951187134
    outer loop
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
      vertex -49.38800048828125 15.550999641418457 2.634000062942505
      vertex -49.33399963378906 15.75100040435791 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6073083281517029 0 0.7944662570953369
    outer loop
      vertex -35.29199981689453 14 2.7929999828338623
      vertex -35.5 14 2.634000062942505
      vertex -35.29199981689453 7.103000164031982 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42.62099838256836 -54.87900161743164 5.5
      vertex -43.097999572753906 -55.5 5.5
      vertex -41.36600112915039 -56.5 5.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0 0.9236428737640381
    outer loop
      vertex -35.74100112915039 7.103000164031982 2.5339999198913574
      vertex -35.5 14 2.634000062942505
      vertex -35.74100112915039 14 2.5339999198913574
    endloop
  endfacet
  facet normal -0.23431620001792908 -0.3061862885951996 0.9226840734481812
    outer loop
      vertex -50.060001373291016 15.939000129699707 2.634000062942505
      vertex -50.04999923706055 15.630000114440918 2.5339999198913574
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
    endloop
  endfacet
  facet normal -0.6867461204528809 0.5275006294250488 0.5001228451728821
    outer loop
      vertex -43.097999572753906 -55.5 5.5
      vertex -42.62099838256836 -54.87900161743164 5.5
      vertex -43.60200119018555 -55.20899963378906 4.500999927520752
    endloop
  endfacet
  facet normal -0.3850242495536804 -0.2954205870628357 0.8743472099304199
    outer loop
      vertex -50.04999923706055 15.630000114440918 2.5339999198913574
      vertex -50.060001373291016 15.939000129699707 2.634000062942505
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37 15 2.5
      vertex -37.71699905395508 8.053000450134277 2.5
      vertex -36.5 14.866000175476074 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -49.257999420166016 16.034000396728516 10.5
      vertex -49.257999420166016 16.034000396728516 3.5
      vertex -48.999000549316406 16 10.5
    endloop
  endfacet
  facet normal -0.7999835014343262 0.331474632024765 0.5001509785652161
    outer loop
      vertex -43.097999572753906 -55.5 5.5
      vertex -43.60200119018555 -55.20899963378906 4.500999927520752
      vertex -43.959999084472656 -56.073001861572266 4.500999927520752
    endloop
  endfacet
  facet normal -0.10789510607719421 -0.08278552442789078 0.9907094240188599
    outer loop
      vertex -50.04999923706055 15.630000114440918 2.5339999198913574
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
      vertex -50.83100128173828 16.240999221801758 2.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -37 16 3.5
      vertex -37 16 10.5
      vertex -48.999000549316406 16 10.5
    endloop
  endfacet
  facet normal 0 -0.9914933443069458 0.13015742599964142
    outer loop
      vertex -37 16 3.5
      vertex -48.999000549316406 16 3.5
      vertex -37 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal -0.48625344038009644 -0.37194758653640747 0.7907038331031799
    outer loop
      vertex -50.11899948120117 16.354000091552734 2.7929999828338623
      vertex -50.29800033569336 16.25 2.634000062942505
      vertex -49.91400146484375 16.086000442504883 2.7929999828338623
    endloop
  endfacet
  facet normal 0.7992205023765564 0.3343205153942108 0.4994760751724243
    outer loop
      vertex -86.04199981689453 1.9390000104904175 4.500999927520752
      vertex -86.40299987792969 2.802000045776367 4.500999927520752
      vertex -86.9010009765625 2.5 5.5
    endloop
  endfacet
  facet normal -0.8000219464302063 0.33039578795433044 0.5008029341697693
    outer loop
      vertex -43.959999084472656 -56.073001861572266 4.500999927520752
      vertex -43.39699935913086 -56.2239990234375 5.5
      vertex -43.097999572753906 -55.5 5.5
    endloop
  endfacet
  facet normal 0 -0.9236428737640381 0.3832542896270752
    outer loop
      vertex -48.999000549316406 15.866000175476074 3
      vertex -37 15.866000175476074 3
      vertex -48.999000549316406 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal -0.5658850073814392 -0.23448273539543152 0.7904378771781921
    outer loop
      vertex -50.11899948120117 16.354000091552734 2.7929999828338623
      vertex -50.448001861572266 16.61199951171875 2.634000062942505
      vertex -50.29800033569336 16.25 2.634000062942505
    endloop
  endfacet
  facet normal 0 -0.7930510640144348 0.6091551780700684
    outer loop
      vertex -37 15.866000175476074 3
      vertex -48.999000549316406 15.866000175476074 3
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.486289918422699 -0.3721446990966797 0.7905886769294739
    outer loop
      vertex -49.91400146484375 16.086000442504883 2.7929999828338623
      vertex -50.29800033569336 16.25 2.634000062942505
      vertex -50.060001373291016 15.939000129699707 2.634000062942505
    endloop
  endfacet
  facet normal 0.6861675977706909 0.5270562767982483 0.5013838410377502
    outer loop
      vertex -86.40299987792969 2.802000045776367 4.500999927520752
      vertex -87.37799835205078 3.121000051498413 5.5
      vertex -86.9010009765625 2.5 5.5
    endloop
  endfacet
  facet normal 0 -0.13015742599964142 0.9914933443069458
    outer loop
      vertex -37 15 2.5
      vertex -37 15.258999824523926 2.5339999198913574
      vertex -48.999000549316406 15 2.5
    endloop
  endfacet
  facet normal -0.8584338426589966 0.11394160985946655 0.5001085996627808
    outer loop
      vertex -44.082000732421875 -57 4.500999927520752
      vertex -43.5 -57 5.5
      vertex -43.39699935913086 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -48.999000549316406 15 2.5
      vertex -43.47200012207031 7.97599983215332 2.5
      vertex -37 15 2.5
    endloop
  endfacet
  facet normal -0.8584338426589966 -0.11394160985946655 0.5001085996627808
    outer loop
      vertex -44.082000732421875 -57 4.500999927520752
      vertex -43.39699935913086 -57.7760009765625 5.5
      vertex -43.5 -57 5.5
    endloop
  endfacet
  facet normal -0.384074330329895 -0.2939218282699585 0.8752695918083191
    outer loop
      vertex -50.29800033569336 16.25 2.634000062942505
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
      vertex -50.060001373291016 15.939000129699707 2.634000062942505
    endloop
  endfacet
  facet normal 0.6851438283920288 0.5303142666816711 0.4993442893028259
    outer loop
      vertex -86.40299987792969 2.802000045776367 4.500999927520752
      vertex -86.9749984741211 3.5409998893737793 4.500999927520752
      vertex -87.37799835205078 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.356097549200058 -0.14755423367023468 0.9227254390716553
    outer loop
      vertex -50.448001861572266 16.61199951171875 2.634000062942505
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
      vertex -50.29800033569336 16.25 2.634000062942505
    endloop
  endfacet
  facet normal -0.8582057952880859 0.11294617503881454 0.5007254481315613
    outer loop
      vertex -43.959999084472656 -56.073001861572266 4.500999927520752
      vertex -44.082000732421875 -57 4.500999927520752
      vertex -43.39699935913086 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0.527132511138916 0.6862668991088867 0.5011676549911499
    outer loop
      vertex -86.9749984741211 3.5409998893737793 4.500999927520752
      vertex -87.9990005493164 3.5980000495910645 5.5
      vertex -87.37799835205078 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.8582057952880859 -0.11294617503881454 0.5007254481315613
    outer loop
      vertex -44.082000732421875 -57 4.500999927520752
      vertex -43.959999084472656 -57.926998138427734 4.500999927520752
      vertex -43.39699935913086 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal 0 -0.6091551780700684 0.7930510640144348
    outer loop
      vertex -37 15.5 2.634000062942505
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
      vertex -48.999000549316406 15.5 2.634000062942505
    endloop
  endfacet
  facet normal 0.5252557396888733 0.6892244815826416 0.49907517433166504
    outer loop
      vertex -86.9749984741211 3.5409998893737793 4.500999927520752
      vertex -87.71900177001953 4.107999801635742 4.500999927520752
      vertex -87.9990005493164 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.097999572753906 -55.5 5.5
      vertex -43.39699935913086 -56.2239990234375 5.5
      vertex -41.36600112915039 -56.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.5 -57 5.5
      vertex -41.5 -57 5.5
      vertex -43.39699935913086 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.39699935913086 -57.7760009765625 5.5
      vertex -41.5 -57 5.5
      vertex -43.5 -57 5.5
    endloop
  endfacet
  facet normal -0.38053199648857117 -0.08462663739919662 0.9208874702453613
    outer loop
      vertex -50.499000549316406 17 2.634000062942505
      vertex -50.74100112915039 17 2.5339999198913574
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -48.999000549316406 16 3.5
      vertex -48.999000549316406 16 10.5
      vertex -49.257999420166016 16.034000396728516 3.5
    endloop
  endfacet
  facet normal -0.044944703578948975 0.3401497006416321 0.9392966032028198
    outer loop
      vertex -40.5 -50.566001892089844 2.634000062942505
      vertex -42.165000915527344 -50.7859992980957 2.634000062942505
      vertex -40.5 -51.65399932861328 3.0280001163482666
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -37 16 3.5
      vertex -48.999000549316406 16 10.5
      vertex -48.999000549316406 16 3.5
    endloop
  endfacet
  facet normal -0.1284029483795166 -0.9831997156143188 0.12973442673683167
    outer loop
      vertex -49.257999420166016 16.034000396728516 3.5
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
      vertex -48.999000549316406 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal -0.1290687471628189 -0.9832001328468323 0.1290687471628189
    outer loop
      vertex -48.999000549316406 15.965999603271484 3.240999937057495
      vertex -48.999000549316406 16 3.5
      vertex -49.257999420166016 16.034000396728516 3.5
    endloop
  endfacet
  facet normal -0.2784997522830963 0.6729879975318909 0.6852189898490906
    outer loop
      vertex -42.68899917602539 -53.20800018310547 3.6619999408721924
      vertex -41.426998138427734 -53.540000915527344 4.500999927520752
      vertex -41.632999420166016 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal -0.13020452857017517 -0.028956227004528046 0.9910642504692078
    outer loop
      vertex -50.59400177001953 16.339000701904297 2.5339999198913574
      vertex -50.74100112915039 17 2.5339999198913574
      vertex -50.83100128173828 16.240999221801758 2.5
    endloop
  endfacet
  facet normal -0.11262979358434677 0.8579740524291992 0.501193642616272
    outer loop
      vertex -90.2760009765625 3.8980000019073486 5.5
      vertex -89.4990005493164 4 5.5
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 2 5.5
      vertex -89.4990005493164 4 5.5
      vertex -89.75800323486328 1.965999960899353 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.2760009765625 3.8980000019073486 5.5
      vertex -89.75800323486328 1.965999960899353 5.5
      vertex -89.4990005493164 4 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.7229995727539 3.8980000019073486 5.5
      vertex -89.23999786376953 1.965999960899353 5.5
      vertex -87.9990005493164 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 4 5.5
      vertex -89.23999786376953 1.965999960899353 5.5
      vertex -88.7229995727539 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.9990005493164 1.8660000562667847 5.5
      vertex -87.9990005493164 3.5980000495910645 5.5
      vertex -89.23999786376953 1.965999960899353 5.5
    endloop
  endfacet
  facet normal -0.0021393417846411467 0.1587638556957245 0.9873142838478088
    outer loop
      vertex -40.5 -50.566001892089844 2.634000062942505
      vertex -38.667999267578125 -49.70800018310547 2.5
      vertex -42.527000427246094 -49.7599983215332 2.5
    endloop
  endfacet
  facet normal 0 -0.9914933443069458 0.13015742599964142
    outer loop
      vertex -48.999000549316406 15.965999603271484 3.240999937057495
      vertex -37 15.965999603271484 3.240999937057495
      vertex -48.999000549316406 16 3.5
    endloop
  endfacet
  facet normal -0.1312878131866455 0.31717661023139954 0.9392350912094116
    outer loop
      vertex -41.882999420166016 -51.83599853515625 3.0280001163482666
      vertex -42.165000915527344 -50.7859992980957 2.634000062942505
      vertex -43.715999603271484 -51.428001403808594 2.634000062942505
    endloop
  endfacet
  facet normal -0.11975689232349396 -0.916995644569397 0.3804961144924164
    outer loop
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
      vertex -48.999000549316406 15.866000175476074 3
      vertex -48.999000549316406 15.965999603271484 3.240999937057495
    endloop
  endfacet
  facet normal -0.12171142548322678 -0.9175169467926025 0.378614604473114
    outer loop
      vertex -49.266998291015625 16.000999450683594 3.240999937057495
      vertex -49.292999267578125 15.904999732971191 3
      vertex -48.999000549316406 15.866000175476074 3
    endloop
  endfacet
  facet normal -0.0447956807911396 0.3403979539871216 0.9392138123512268
    outer loop
      vertex -41.882999420166016 -51.83599853515625 3.0280001163482666
      vertex -40.5 -51.65399932861328 3.0280001163482666
      vertex -42.165000915527344 -50.7859992980957 2.634000062942505
    endloop
  endfacet
  facet normal 0.722497820854187 -0.09264788776636124 0.6851374506950378
    outer loop
      vertex -86.03600311279297 0.08399999886751175 4.500999927520752
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
      vertex -85.91699981689453 1.0119999647140503 4.500999927520752
    endloop
  endfacet
  facet normal -0.0346994549036026 -0.0982995331287384 0.9945517182350159
    outer loop
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
      vertex -50.04999923706055 15.630000114440918 2.5339999198913574
      vertex -49.999000549316406 15.267999649047852 2.5
    endloop
  endfacet
  facet normal -0.12958140671253204 -0.11080342531204224 0.9853584170341492
    outer loop
      vertex -50.04999923706055 15.630000114440918 2.5339999198913574
      vertex -50.83100128173828 16.240999221801758 2.5
      vertex -49.999000549316406 15.267999649047852 2.5
    endloop
  endfacet
  facet normal -0.10462330281734467 -0.7886987328529358 0.6058120727539062
    outer loop
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
      vertex -48.999000549316406 15.866000175476074 3
      vertex -49.292999267578125 15.904999732971191 3
    endloop
  endfacet
  facet normal 0.8014991879463196 -0.32893896102905273 0.499397873878479
    outer loop
      vertex -86.03600311279297 0.08399999886751175 4.500999927520752
      vertex -86.60099792480469 0.2240000069141388 5.5
      vertex -86.39099884033203 -0.781000018119812 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -50.83100128173828 16.240999221801758 2.5
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -49.999000549316406 15.267999649047852 2.5
    endloop
  endfacet
  facet normal -0.48483628034591675 -0.6309513449668884 0.6056683659553528
    outer loop
      vertex -34.145999908447266 -83.98600006103516 2.7929999828338623
      vertex -34.06700134277344 -83.8479995727539 3
      vertex -34.62099838256836 -83.62100219726562 2.7929999828338623
    endloop
  endfacet
  facet normal -0.079753577709198 -0.6072147488594055 0.7905248999595642
    outer loop
      vertex -49.33399963378906 15.75100040435791 2.7929999828338623
      vertex -48.999000549316406 15.5 2.634000062942505
      vertex -48.999000549316406 15.706999778747559 2.7929999828338623
    endloop
  endfacet
  facet normal -0.13040490448474884 -0.9914608001708984 0
    outer loop
      vertex -33 -84 3.5
      vertex -33 -84 10.5
      vertex -33.516998291015625 -83.93199920654297 3.5
    endloop
  endfacet
  facet normal 0.858024001121521 -0.11278150230646133 0.5010740160942078
    outer loop
      vertex -86.03600311279297 0.08399999886751175 4.500999927520752
      vertex -86.4990005493164 1 5.5
      vertex -86.60099792480469 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal -0.41223397850990295 -0.6966024041175842 0.5872037410736084
    outer loop
      vertex -33.5260009765625 -83.96499633789062 3.240999937057495
      vertex -34.06700134277344 -83.8479995727539 3
      vertex -34.05799865722656 -84 2.8259999752044678
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -82.90299987792969 4.617000102996826 2.5
      vertex -50.83100128173828 16.240999221801758 2.5
      vertex -79.9990005493164 15.267999649047852 2.5
    endloop
  endfacet
  facet normal 0.8593736886978149 -0.11019986122846603 0.4993324279785156
    outer loop
      vertex -85.91699981689453 1.0119999647140503 4.500999927520752
      vertex -86.4990005493164 1 5.5
      vertex -86.03600311279297 0.08399999886751175 4.500999927520752
    endloop
  endfacet
  facet normal -0.05018339678645134 -0.38277140259742737 0.9224790930747986
    outer loop
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
      vertex -48.999000549316406 15.5 2.634000062942505
      vertex -49.38800048828125 15.550999641418457 2.634000062942505
    endloop
  endfacet
  facet normal -0.12930254638195038 -0.9830796718597412 0.12975040078163147
    outer loop
      vertex -33 -84 3.5
      vertex -33.516998291015625 -83.93199920654297 3.5
      vertex -33.5260009765625 -83.96499633789062 3.240999937057495
    endloop
  endfacet
  facet normal -0.2572612166404724 -0.8779162168502808 0.403831422328949
    outer loop
      vertex -33.5260009765625 -83.96499633789062 3.240999937057495
      vertex -34.05799865722656 -84 2.8259999752044678
      vertex -33 -84 3.5
    endloop
  endfacet
  facet normal -0.2451765388250351 -0.5900582075119019 0.769233226776123
    outer loop
      vertex -49.38800048828125 15.550999641418457 2.634000062942505
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal -0.3420163691043854 -0.7163893580436707 0.6081209182739258
    outer loop
      vertex -34.05799865722656 -84 2.8259999752044678
      vertex -34.06700134277344 -83.8479995727539 3
      vertex -34.145999908447266 -83.98600006103516 2.7929999828338623
    endloop
  endfacet
  facet normal -0.3704967498779297 -0.18178147077560425 0.9108719229698181
    outer loop
      vertex -34.62099838256836 -84 2.5969998836517334
      vertex -34.05799865722656 -84 2.8259999752044678
      vertex -34.145999908447266 -83.98600006103516 2.7929999828338623
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -94.73100280761719 84 10.5
      vertex -94.73100280761719 84 0
      vertex -94.93099975585938 83.51799774169922 10.5
    endloop
  endfacet
  facet normal 0 -0.3832542896270752 0.9236428737640381
    outer loop
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
      vertex -37 15.258999824523926 2.5339999198913574
      vertex -48.999000549316406 15.5 2.634000062942505
    endloop
  endfacet
  facet normal -0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -94.41300201416016 84.41400146484375 10.5
      vertex -94.73100280761719 84 0
      vertex -94.73100280761719 84 10.5
    endloop
  endfacet
  facet normal -0.03486098721623421 -0.13007831573486328 0.9908906817436218
    outer loop
      vertex -49.999000549316406 15.267999649047852 2.5
      vertex -48.999000549316406 15 2.5
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal -0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -93.9990005493164 84.73200225830078 10.5
      vertex -93.9990005493164 84.73200225830078 0
      vertex -94.41300201416016 84.41400146484375 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -93.9990005493164 84.73200225830078 0
      vertex -93.9990005493164 84.73200225830078 10.5
      vertex -93.51699829101562 84.93199920654297 10.5
    endloop
  endfacet
  facet normal -0.17089857161045074 -0.48413583636283875 0.8581411242485046
    outer loop
      vertex -49.749000549316406 15.701000213623047 2.634000062942505
      vertex -50.04999923706055 15.630000114440918 2.5339999198913574
      vertex -48.999000549316406 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal 0 -0.3832542896270752 0.9236428737640381
    outer loop
      vertex -37 15.5 2.634000062942505
      vertex -48.999000549316406 15.5 2.634000062942505
      vertex -37 15.258999824523926 2.5339999198913574
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -94.9990005493164 83 0
      vertex -94.9990005493164 83 10.5
      vertex -94.93099975585938 83.51799774169922 0
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -94.93099975585938 83.51799774169922 10.5
      vertex -94.93099975585938 83.51799774169922 0
      vertex -94.9990005493164 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.999000549316406 15.267999649047852 2.5
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -47.02799987792969 4.730000019073486 2.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -94.73100280761719 84 0
      vertex -94.93099975585938 83.51799774169922 0
      vertex -94.93099975585938 83.51799774169922 10.5
    endloop
  endfacet
  facet normal -0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -94.41300201416016 84.41400146484375 10.5
      vertex -94.41300201416016 84.41400146484375 0
      vertex -94.73100280761719 84 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -48.999000549316406 15 2.5
      vertex -49.999000549316406 15.267999649047852 2.5
      vertex -47.02799987792969 4.730000019073486 2.5
    endloop
  endfacet
  facet normal -0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -93.9990005493164 84.73200225830078 0
      vertex -94.41300201416016 84.41400146484375 0
      vertex -94.41300201416016 84.41400146484375 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -93.51699829101562 84.93199920654297 10.5
      vertex -93.51699829101562 84.93199920654297 0
      vertex -93.9990005493164 84.73200225830078 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.71699905395508 8.053000450134277 2.5
      vertex -37 15 2.5
      vertex -43.47200012207031 7.97599983215332 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -93.51699829101562 84.93199920654297 10.5
      vertex -92.9990005493164 85 10.5
      vertex -93.51699829101562 84.93199920654297 0
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -92.9990005493164 85 0
      vertex -93.51699829101562 84.93199920654297 0
      vertex -92.9990005493164 85 10.5
    endloop
  endfacet
  facet normal -0.37283676862716675 -0.4851985573768616 0.7909330725669861
    outer loop
      vertex -34.145999908447266 -83.98600006103516 2.7929999828338623
      vertex -34.62099838256836 -83.62100219726562 2.7929999828338623
      vertex -34.766998291015625 -83.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 19 2.5
      vertex -80.9990005493164 19 2.5
      vertex -92.9990005493164 83 2.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 83 2.5
      vertex -92.9990005493164 83 10.5
      vertex -92.9990005493164 19 2.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -92.9990005493164 18 10.5
      vertex -92.9990005493164 18 3.5
      vertex -92.9990005493164 83 10.5
    endloop
  endfacet
  facet normal -0.3473118841648102 -0.3568688631057739 0.8671903610229492
    outer loop
      vertex -34.62099838256836 -84 2.5969998836517334
      vertex -34.145999908447266 -83.98600006103516 2.7929999828338623
      vertex -34.766998291015625 -83.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 18 10.5
      vertex -94.9990005493164 83 10.5
      vertex -94.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 0.799384593963623 -0.33123672008514404 0.5012649297714233
    outer loop
      vertex -86.39099884033203 -58.78099822998047 4.500999927520752
      vertex -86.60099792480469 -57.7760009765625 5.5
      vertex -86.9010009765625 -58.5 5.5
    endloop
  endfacet
  facet normal -0.9912446141242981 -0.13203836977481842 0
    outer loop
      vertex -34.930999755859375 -82.51799774169922 3.5
      vertex -34.930999755859375 -82.51799774169922 10.5
      vertex -35 -82 3.5
    endloop
  endfacet
  facet normal -0.9912446141242981 -0.13203836977481842 0
    outer loop
      vertex -35 -82 10.5
      vertex -35 -82 3.5
      vertex -34.930999755859375 -82.51799774169922 10.5
    endloop
  endfacet
  facet normal 0.8014991879463196 -0.32893896102905273 0.499397873878479
    outer loop
      vertex -86.39099884033203 -58.78099822998047 4.500999927520752
      vertex -86.03600311279297 -57.91600036621094 4.500999927520752
      vertex -86.60099792480469 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal -0.9229958057403564 -0.03742412477731705 0.38298583030700684
    outer loop
      vertex -35.034000396728516 -5.103000164031982 3.240999937057495
      vertex -35.15800094604492 -3.937999963760376 3.055999994277954
      vertex -35.13399887084961 -5.103000164031982 3
    endloop
  endfacet
  facet normal -0.7940794825553894 -0.04549357295036316 0.6061089634895325
    outer loop
      vertex -35.15800094604492 -3.937999963760376 3.055999994277954
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
      vertex -35.13399887084961 -5.103000164031982 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.9010009765625 -58.5 5.5
      vertex -88.63300323486328 -57.5 5.5
      vertex -87.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.60099792480469 -57.7760009765625 5.5
      vertex -88.53299713134766 -57.25899887084961 5.5
      vertex -86.9010009765625 -58.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.63300323486328 -57.5 5.5
      vertex -86.9010009765625 -58.5 5.5
      vertex -88.53299713134766 -57.25899887084961 5.5
    endloop
  endfacet
  facet normal -0.6054578423500061 -0.07800457626581192 0.7920454740524292
    outer loop
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
      vertex -35.5 -5.103000164031982 2.634000062942505
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.4990005493164 -57 5.5
      vertex -88.53299713134766 -57.25899887084961 5.5
      vertex -86.60099792480469 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.79199981689453 -57.707000732421875 5.5
      vertex -87.37799835205078 -59.12099838256836 5.5
      vertex -88.63300323486328 -57.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.9990005493164 -57.86600112915039 5.5
      vertex -87.37799835205078 -59.12099838256836 5.5
      vertex -88.79199981689453 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal -0.9243202805519104 -0.3816176950931549 0
    outer loop
      vertex -34.930999755859375 -82.51799774169922 3.5
      vertex -34.731998443603516 -83 10.5
      vertex -34.930999755859375 -82.51799774169922 10.5
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -80.9990005493164 18 10.5
      vertex -80.9990005493164 18 3.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.9990005493164 19 2.5
      vertex -80.48200225830078 18.93199920654297 2.5
      vertex -92.9990005493164 83 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.23999786376953 -57.965999603271484 5.5
      vertex -87.9990005493164 -59.597999572753906 5.5
      vertex -88.9990005493164 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal -0.9829576015472412 -0.13093450665473938 0.12903690338134766
    outer loop
      vertex -34.930999755859375 -82.51799774169922 3.5
      vertex -35 -82 3.5
      vertex -35.034000396728516 -82 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -79.4260025024414 18.207000732421875 2.5
      vertex -92.9990005493164 83 2.5
      vertex -80.48200225830078 18.93199920654297 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.75800323486328 -57.965999603271484 5.5
      vertex -89.4990005493164 -60 5.5
      vertex -89.4990005493164 -58 5.5
    endloop
  endfacet
  facet normal -0.8541894555091858 -0.35315775871276855 0.3816280961036682
    outer loop
      vertex -34.847999572753906 -83.06700134277344 3
      vertex -34.76100158691406 -83.01699829101562 3.240999937057495
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal 0.05031241104006767 0.3827689290046692 0.9224730730056763
    outer loop
      vertex -80.9990005493164 18.740999221801758 2.5339999198913574
      vertex -80.9990005493164 18.5 2.634000062942505
      vertex -80.61100006103516 18.448999404907227 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.9990005493164 -57.86600112915039 5.5
      vertex -90.9990005493164 -59.597999572753906 5.5
      vertex -89.75800323486328 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -91.62000274658203 -59.12099838256836 5.5
      vertex -90.9990005493164 -59.597999572753906 5.5
      vertex -89.9990005493164 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal 0 0.3832542896270752 0.9236428737640381
    outer loop
      vertex -80.9990005493164 18.740999221801758 2.5339999198913574
      vertex -92.9990005493164 18.740999221801758 2.5339999198913574
      vertex -80.9990005493164 18.5 2.634000062942505
    endloop
  endfacet
  facet normal 0 0.3832542896270752 0.9236428737640381
    outer loop
      vertex -92.9990005493164 18.5 2.634000062942505
      vertex -80.9990005493164 18.5 2.634000062942505
      vertex -92.9990005493164 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal 0.007354500237852335 0.05591583251953125 0.9984083771705627
    outer loop
      vertex -80.9990005493164 19 2.5
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
      vertex -80.48200225830078 18.93199920654297 2.5
    endloop
  endfacet
  facet normal -0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -88.9990005493164 -57.86600112915039 0
      vertex -88.9990005493164 -57.86600112915039 5.5
      vertex -88.79199981689453 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal -0.9167433381080627 -0.1220000609755516 0.3803914189338684
    outer loop
      vertex -35.034000396728516 -82 3.240999937057495
      vertex -35.13399887084961 -82 3
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal -0.9829422235488892 -0.13080979883670807 0.1292801946401596
    outer loop
      vertex -35.034000396728516 -82 3.240999937057495
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
      vertex -34.930999755859375 -82.51799774169922 3.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -89.23999786376953 -57.965999603271484 5.5
      vertex -88.9990005493164 -57.86600112915039 5.5
      vertex -89.23999786376953 -57.965999603271484 0
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -88.9990005493164 -57.86600112915039 0
      vertex -89.23999786376953 -57.965999603271484 0
      vertex -88.9990005493164 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.23999786376953 -57.965999603271484 5.5
      vertex -89.23999786376953 -57.965999603271484 0
      vertex -89.4990005493164 -58 5.5
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.75800323486328 -57.965999603271484 0
      vertex -89.75800323486328 -57.965999603271484 5.5
      vertex -89.4990005493164 -58 5.5
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -89.75800323486328 -57.965999603271484 5.5
      vertex -89.75800323486328 -57.965999603271484 0
      vertex -89.9990005493164 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 0 0.6067371964454651
    outer loop
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
      vertex -35.29199981689453 -82 2.7929999828338623
      vertex -35.13399887084961 -82 3
    endloop
  endfacet
  facet normal 0 0.13015742599964142 0.9914933443069458
    outer loop
      vertex -92.9990005493164 18.740999221801758 2.5339999198913574
      vertex -80.9990005493164 18.740999221801758 2.5339999198913574
      vertex -80.9990005493164 19 2.5
    endloop
  endfacet
  facet normal -0.9162461161613464 -0.12117023020982742 0.38185185194015503
    outer loop
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
      vertex -35.13399887084961 -82 3
      vertex -35.06100082397461 -82.552001953125 3
    endloop
  endfacet
  facet normal -0.6073083281517029 0 0.7944662570953369
    outer loop
      vertex -35.5 -82 2.634000062942505
      vertex -35.29199981689453 -82 2.7929999828338623
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6053798794746399 -0.07962838560342789 0.7919434905052185
    outer loop
      vertex -35.5 -82 2.634000062942505
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
      vertex -35.29199981689453 -82 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7897775173187256 -0.10444521903991699 0.6044358015060425
    outer loop
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
      vertex -35.06100082397461 -82.552001953125 3
      vertex -35.13399887084961 -82 3
    endloop
  endfacet
  facet normal -0.7361740469932556 -0.304475873708725 0.6044354438781738
    outer loop
      vertex -34.847999572753906 -83.06700134277344 3
      vertex -35.06100082397461 -82.552001953125 3
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
    endloop
  endfacet
  facet normal 0.11277299374341965 -0.8579592704772949 0.501186728477478
    outer loop
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -88.7229995727539 -59.89799880981445 5.5
      vertex -89.4990005493164 -60 5.5
    endloop
  endfacet
  facet normal -0.7905927896499634 -0.10399028658866882 0.6034476161003113
    outer loop
      vertex -35.13399887084961 -82 3
      vertex -35.29199981689453 -82 2.7929999828338623
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
    endloop
  endfacet
  facet normal 0.11578092724084854 -0.8586313724517822 0.4993465542793274
    outer loop
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -88.55999755859375 -60.457000732421875 4.500999927520752
      vertex -88.7229995727539 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0.3312227725982666 -0.799350917339325 0.5013278126716614
    outer loop
      vertex -88.55999755859375 -60.457000732421875 4.500999927520752
      vertex -87.9990005493164 -59.597999572753906 5.5
      vertex -88.7229995727539 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal -0.3827579617500305 -0.050876639783382416 0.9224466681480408
    outer loop
      vertex -35.74100112915039 -82 2.5339999198913574
      vertex -35.41400146484375 -82.64700317382812 2.634000062942505
      vertex -35.5 -82 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -79.03299713134766 17.259000778198242 2.5
      vertex -50.83100128173828 17.759000778198242 2.5
      vertex -79.4260025024414 18.207000732421875 2.5
    endloop
  endfacet
  facet normal -0.6068424582481384 -0.08066221326589584 0.7907185554504395
    outer loop
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
      vertex -35.5 -82 2.634000062942505
      vertex -35.41400146484375 -82.64700317382812 2.634000062942505
    endloop
  endfacet
  facet normal 0.3347013294696808 -0.7992037534713745 0.49924781918525696
    outer loop
      vertex -87.697998046875 -60.09600067138672 4.500999927520752
      vertex -87.9990005493164 -59.597999572753906 5.5
      vertex -88.55999755859375 -60.457000732421875 4.500999927520752
    endloop
  endfacet
  facet normal 0.10867348313331604 0.15828855335712433 0.9813942909240723
    outer loop
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
      vertex -79.4260025024414 18.207000732421875 2.5
      vertex -80.48200225830078 18.93199920654297 2.5
    endloop
  endfacet
  facet normal 0.10177073627710342 0.042189765721559525 0.9939128160476685
    outer loop
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
      vertex -79.03299713134766 17.259000778198242 2.5
      vertex -79.4260025024414 18.207000732421875 2.5
    endloop
  endfacet
  facet normal 0.5271956324577332 -0.686349093914032 0.5009887218475342
    outer loop
      vertex -87.697998046875 -60.09600067138672 4.500999927520752
      vertex -87.37799835205078 -59.12099838256836 5.5
      vertex -87.9990005493164 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal 0.44520196318626404 -0.5759605765342712 0.6856125593185425
    outer loop
      vertex -87.697998046875 -60.09600067138672 4.500999927520752
      vertex -86.39299774169922 -60.08599853515625 3.6619999408721924
      vertex -86.95800018310547 -59.52399826049805 4.500999927520752
    endloop
  endfacet
  facet normal -0.13013805449008942 -0.017253845930099487 0.9913457632064819
    outer loop
      vertex -36 -82 2.5
      vertex -35.64699935913086 -82.70899963378906 2.5339999198913574
      vertex -35.74100112915039 -82 2.5339999198913574
    endloop
  endfacet
  facet normal 0.5298786759376526 -0.6855073571205139 0.4993078112602234
    outer loop
      vertex -87.697998046875 -60.09600067138672 4.500999927520752
      vertex -86.95800018310547 -59.52399826049805 4.500999927520752
      vertex -87.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal -0.18829242885112762 -0.046704038977622986 0.9810018539428711
    outer loop
      vertex -36 -82 2.5
      vertex -35.652000427246094 -83.40299987792969 2.5
      vertex -35.64699935913086 -82.70899963378906 2.5339999198913574
    endloop
  endfacet
  facet normal 0.916995644569397 -0.11975689232349396 0.3804961144924164
    outer loop
      vertex -79.96499633789062 17 3.240999937057495
      vertex -80 16.73200035095215 3.240999937057495
      vertex -79.86499786376953 17 3
    endloop
  endfacet
  facet normal -0.38246336579322815 -0.050707411020994186 0.9225782155990601
    outer loop
      vertex -35.74100112915039 -82 2.5339999198913574
      vertex -35.64699935913086 -82.70899963378906 2.5339999198913574
      vertex -35.41400146484375 -82.64700317382812 2.634000062942505
    endloop
  endfacet
  facet normal 0.6862668991088867 -0.527132511138916 0.5011676549911499
    outer loop
      vertex -86.95800018310547 -59.52399826049805 4.500999927520752
      vertex -86.9010009765625 -58.5 5.5
      vertex -87.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0.7875946760177612 0.10483341664075851 0.6072105169296265
    outer loop
      vertex -79.75 17.334999084472656 2.7929999828338623
      vertex -79.90399932861328 17.292999267578125 3
      vertex -79.86499786376953 17 3
    endloop
  endfacet
  facet normal 0.6887195110321045 -0.5255773067474365 0.49943360686302185
    outer loop
      vertex -86.95800018310547 -59.52399826049805 4.500999927520752
      vertex -86.39099884033203 -58.78099822998047 4.500999927520752
      vertex -86.9010009765625 -58.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.7229995727539 -59.89799880981445 5.5
      vertex -89.23999786376953 -57.965999603271484 5.5
      vertex -89.4990005493164 -60 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 -58 5.5
      vertex -89.4990005493164 -60 5.5
      vertex -89.23999786376953 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.7229995727539 -59.89799880981445 5.5
      vertex -87.9990005493164 -59.597999572753906 5.5
      vertex -89.23999786376953 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.37799835205078 -59.12099838256836 5.5
      vertex -88.9990005493164 -57.86600112915039 5.5
      vertex -87.9990005493164 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 80 -82 10.5
      vertex 80 83 10.5
      vertex 80 83 2.5
    endloop
  endfacet
  facet normal 0.7223699688911438 -0.0923665314912796 0.6853101849555969
    outer loop
      vertex -86.03600311279297 -57.91600036621094 4.500999927520752
      vertex -85.26599884033203 -58.11899948120117 3.6619999408721924
      vertex -85.12100219726562 -56.98500061035156 3.6619999408721924
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 25 83 10.5
      vertex 25 83 2.5
      vertex 80 83 2.5
    endloop
  endfacet
  facet normal 0.6737651228904724 -0.276516318321228 0.6852585673332214
    outer loop
      vertex -86.03600311279297 -57.91600036621094 4.500999927520752
      vertex -86.39099884033203 -58.78099822998047 4.500999927520752
      vertex -85.26599884033203 -58.11899948120117 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 -84 2.5
      vertex -35.652000427246094 -83.40299987792969 2.5
      vertex -36 -82 2.5
    endloop
  endfacet
  facet normal 0.5876343846321106 0.243494912981987 0.7716191411018372
    outer loop
      vertex -79.69999694824219 17.75 2.634000062942505
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 80 -82 2.5
      vertex 80 83 2.5
      vertex 25 -82 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 -82 2.5
      vertex 80 83 2.5
      vertex 25 83 2.5
    endloop
  endfacet
  facet normal 0.722497820854187 -0.09264788776636124 0.6851374506950378
    outer loop
      vertex -86.03600311279297 -57.91600036621094 4.500999927520752
      vertex -85.12100219726562 -56.98500061035156 3.6619999408721924
      vertex -85.91699981689453 -56.987998962402344 4.500999927520752
    endloop
  endfacet
  facet normal 0.546712338924408 -0.06990589946508408 0.8343972563743591
    outer loop
      vertex -85.26599884033203 -58.11899948120117 3.6619999408721924
      vertex -84.15299987792969 -56.981998443603516 3.0280001163482666
      vertex -85.12100219726562 -56.98500061035156 3.6619999408721924
    endloop
  endfacet
  facet normal -0.802459180355072 -0.04207196831703186 0.5952219367027283
    outer loop
      vertex -35.15800094604492 -3.937999963760376 3.055999994277954
      vertex -35.23899841308594 -3.9210000038146973 2.947999954223633
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
    endloop
  endfacet
  facet normal -0.602609395980835 -0.07713884115219116 0.7942993640899658
    outer loop
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
      vertex -35.23899841308594 -3.9210000038146973 2.947999954223633
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
    endloop
  endfacet
  facet normal 0.5470308661460876 -0.070355124771595 0.8341507315635681
    outer loop
      vertex -85.26599884033203 -58.11899948120117 3.6619999408721924
      vertex -84.33100128173828 -58.36600112915039 3.0280001163482666
      vertex -84.15299987792969 -56.981998443603516 3.0280001163482666
    endloop
  endfacet
  facet normal -0.1288638859987259 -0.14063329994678497 0.9816396236419678
    outer loop
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
      vertex -36 -5.103000164031982 2.5
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
    endloop
  endfacet
  facet normal 0.6737880706787109 -0.2766546905040741 0.685180127620697
    outer loop
      vertex -85.26599884033203 -58.11899948120117 3.6619999408721924
      vertex -86.39099884033203 -58.78099822998047 4.500999927520752
      vertex -85.69999694824219 -59.17599868774414 3.6619999408721924
    endloop
  endfacet
  facet normal 0.9176308512687683 -0.12214198708534241 0.37819963693618774
    outer loop
      vertex -79.86499786376953 17 3
      vertex -80 16.73200035095215 3.240999937057495
      vertex -79.90399932861328 16.707000732421875 3
    endloop
  endfacet
  facet normal -0.38234367966651917 -0.06889376789331436 0.921448290348053
    outer loop
      vertex -35.5 -5.103000164031982 2.634000062942505
      vertex -35.58300018310547 -3.880000114440918 2.690999984741211
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
    endloop
  endfacet
  facet normal 0.5102490186691284 -0.20950622856616974 0.834118127822876
    outer loop
      vertex -85.26599884033203 -58.11899948120117 3.6619999408721924
      vertex -85.69999694824219 -59.17599868774414 3.6619999408721924
      vertex -84.33100128173828 -58.36600112915039 3.0280001163482666
    endloop
  endfacet
  facet normal 0.7887835502624512 0.10360142588615417 0.6058772206306458
    outer loop
      vertex -79.75 17.334999084472656 2.7929999828338623
      vertex -79.86499786376953 17 3
      vertex -79.70600128173828 17 2.7929999828338623
    endloop
  endfacet
  facet normal -0.9914933443069458 0 0.13015742599964142
    outer loop
      vertex -35.034000396728516 -50.89699935913086 3.240999937057495
      vertex -35 -5.103000164031982 3.5
      vertex -35.034000396728516 -5.103000164031982 3.240999937057495
    endloop
  endfacet
  facet normal 0.6072859168052673 0.07976292818784714 0.7904692888259888
    outer loop
      vertex -79.75 17.334999084472656 2.7929999828338623
      vertex -79.70600128173828 17 2.7929999828338623
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
    endloop
  endfacet
  facet normal -0.794902503490448 0 0.6067371964454651
    outer loop
      vertex -35.29199981689453 -50.89699935913086 2.7929999828338623
      vertex -35.13399887084961 -50.89699935913086 3
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6073083281517029 0 0.7944662570953369
    outer loop
      vertex -35.5 -5.103000164031982 2.634000062942505
      vertex -35.5 -50.89699935913086 2.634000062942505
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
    endloop
  endfacet
  facet normal 0.3405860364437103 -0.04380369558930397 0.9391924142837524
    outer loop
      vertex -83.06600189208984 -56.97800064086914 2.634000062942505
      vertex -84.15299987792969 -56.981998443603516 3.0280001163482666
      vertex -84.33100128173828 -58.36600112915039 3.0280001163482666
    endloop
  endfacet
  facet normal 0.5099919438362122 -0.20881249010562897 0.834449291229248
    outer loop
      vertex -84.33100128173828 -58.36600112915039 3.0280001163482666
      vertex -85.69999694824219 -59.17599868774414 3.6619999408721924
      vertex -84.86000061035156 -59.65800094604492 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6072118282318115 0.07981392741203308 0.7905210256576538
    outer loop
      vertex -79.70600128173828 17 2.7929999828338623
      vertex -79.4990005493164 17 2.634000062942505
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
    endloop
  endfacet
  facet normal 0.4383305609226227 -0.3338055908679962 0.8345298767089844
    outer loop
      vertex -85.69999694824219 -59.17599868774414 3.6619999408721924
      vertex -86.39299774169922 -60.08599853515625 3.6619999408721924
      vertex -84.86000061035156 -59.65800094604492 3.0280001163482666
    endloop
  endfacet
  facet normal 0.7887835502624512 -0.10360142588615417 0.6058772206306458
    outer loop
      vertex -79.86499786376953 17 3
      vertex -79.75 16.665000915527344 2.7929999828338623
      vertex -79.70600128173828 17 2.7929999828338623
    endloop
  endfacet
  facet normal 0.22401359677314758 -0.2633378803730011 0.9383342266082764
    outer loop
      vertex -37.28300094604492 -4.572000026702881 2.634000062942505
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
      vertex -37.82600021362305 -3.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal 0.7875946760177612 -0.10483341664075851 0.6072105169296265
    outer loop
      vertex -79.86499786376953 17 3
      vertex -79.90399932861328 16.707000732421875 3
      vertex -79.75 16.665000915527344 2.7929999828338623
    endloop
  endfacet
  facet normal 0.7353399395942688 -0.30737683176994324 0.6039823293685913
    outer loop
      vertex -80.01699829101562 16.433000564575195 3
      vertex -79.87999725341797 16.354000091552734 2.7929999828338623
      vertex -79.75 16.665000915527344 2.7929999828338623
    endloop
  endfacet
  facet normal -0.016359256580471992 0.1238098219037056 0.9921711087226868
    outer loop
      vertex -42.527000427246094 -49.7599983215332 2.5
      vertex -42.165000915527344 -50.7859992980957 2.634000062942505
      vertex -40.5 -50.566001892089844 2.634000062942505
    endloop
  endfacet
  facet normal 0.6072859168052673 -0.07976292818784714 0.7904692888259888
    outer loop
      vertex -79.70600128173828 17 2.7929999828338623
      vertex -79.75 16.665000915527344 2.7929999828338623
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
    endloop
  endfacet
  facet normal -0.04681670665740967 0.11310391128063202 0.9924795627593994
    outer loop
      vertex -42.527000427246094 -49.7599983215332 2.5
      vertex -43.715999603271484 -51.428001403808594 2.634000062942505
      vertex -42.165000915527344 -50.7859992980957 2.634000062942505
    endloop
  endfacet
  facet normal 0.5655145049095154 -0.236388698220253 0.7901352643966675
    outer loop
      vertex -79.75 16.665000915527344 2.7929999828338623
      vertex -79.87999725341797 16.354000091552734 2.7929999828338623
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
    endloop
  endfacet
  facet normal 0.6072118282318115 -0.07981392741203308 0.7905210256576538
    outer loop
      vertex -79.70600128173828 17 2.7929999828338623
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
      vertex -79.4990005493164 17 2.634000062942505
    endloop
  endfacet
  facet normal -0.057791486382484436 0.12080758064985275 0.9909922480583191
    outer loop
      vertex -43.715999603271484 -51.428001403808594 2.634000062942505
      vertex -42.527000427246094 -49.7599983215332 2.5
      vertex -45.16299819946289 -51.020999908447266 2.5
    endloop
  endfacet
  facet normal -0.07187410444021225 0.5465325713157654 0.8343477845191956
    outer loop
      vertex -41.882999420166016 -51.83599853515625 3.0280001163482666
      vertex -41.632999420166016 -52.770999908447266 3.6619999408721924
      vertex -40.5 -52.62200164794922 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3827689290046692 -0.05031241104006767 0.9224730730056763
    outer loop
      vertex -79.4990005493164 17 2.634000062942505
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
      vertex -79.25800323486328 17 2.5339999198913574
    endloop
  endfacet
  facet normal -0.20901581645011902 0.2723539471626282 0.9392207860946655
    outer loop
      vertex -45.04899978637695 -52.45100021362305 2.634000062942505
      vertex -43.17300033569336 -52.369998931884766 3.0280001163482666
      vertex -43.715999603271484 -51.428001403808594 2.634000062942505
    endloop
  endfacet
  facet normal 0.5877912640571594 -0.2435203492641449 0.7714915871620178
    outer loop
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
      vertex -79.25800323486328 17 2.5339999198913574
    endloop
  endfacet
  facet normal 0.5876343846321106 -0.243494912981987 0.7716191411018372
    outer loop
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
      vertex -79.69999694824219 16.25 2.634000062942505
      vertex -79.76799774169922 15.769000053405762 2.5339999198913574
    endloop
  endfacet
  facet normal 0.2731724679470062 -0.20820172131061554 0.9391639232635498
    outer loop
      vertex -84.86000061035156 -59.65800094604492 3.0280001163482666
      vertex -85.70600128173828 -60.768001556396484 3.0280001163482666
      vertex -83.91699981689453 -60.198001861572266 2.634000062942505
    endloop
  endfacet
  facet normal 0.5642961859703064 -0.23382438719272614 0.7917675971984863
    outer loop
      vertex -79.55000305175781 16.61199951171875 2.634000062942505
      vertex -79.87999725341797 16.354000091552734 2.7929999828338623
      vertex -79.69999694824219 16.25 2.634000062942505
    endloop
  endfacet
  facet normal 0.5877912640571594 0.2435203492641449 0.7714915871620178
    outer loop
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
      vertex -79.25800323486328 17 2.5339999198913574
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
    endloop
  endfacet
  facet normal -0.07191598415374756 0.5464824438095093 0.8343769907951355
    outer loop
      vertex -40.5 -52.62200164794922 3.6619999408721924
      vertex -40.5 -51.65399932861328 3.0280001163482666
      vertex -41.882999420166016 -51.83599853515625 3.0280001163482666
    endloop
  endfacet
  facet normal 0.3402978181838989 -0.04350746423006058 0.9393106698989868
    outer loop
      vertex -83.27899932861328 -58.64400100708008 2.634000062942505
      vertex -83.06600189208984 -56.97800064086914 2.634000062942505
      vertex -84.33100128173828 -58.36600112915039 3.0280001163482666
    endloop
  endfacet
  facet normal 0.31745216250419617 -0.1299784779548645 0.9393240809440613
    outer loop
      vertex -84.33100128173828 -58.36600112915039 3.0280001163482666
      vertex -84.86000061035156 -59.65800094604492 3.0280001163482666
      vertex -83.27899932861328 -58.64400100708008 2.634000062942505
    endloop
  endfacet
  facet normal 0.3827689290046692 0.05031241104006767 0.9224730730056763
    outer loop
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
      vertex -79.4990005493164 17 2.634000062942505
      vertex -79.25800323486328 17 2.5339999198913574
    endloop
  endfacet
  facet normal -0.13129131495952606 0.3171643912792206 0.9392387270927429
    outer loop
      vertex -41.882999420166016 -51.83599853515625 3.0280001163482666
      vertex -43.715999603271484 -51.428001403808594 2.634000062942505
      vertex -43.17300033569336 -52.369998931884766 3.0280001163482666
    endloop
  endfacet
  facet normal 0.3177083432674408 -0.1304362416267395 0.9391739964485168
    outer loop
      vertex -84.86000061035156 -59.65800094604492 3.0280001163482666
      vertex -83.91699981689453 -60.198001861572266 2.634000062942505
      vertex -83.27899932861328 -58.64400100708008 2.634000062942505
    endloop
  endfacet
  facet normal 0.1016944944858551 0.042131755501031876 0.9939231276512146
    outer loop
      vertex -79.03299713134766 17.259000778198242 2.5
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
      vertex -79.25800323486328 17 2.5339999198913574
    endloop
  endfacet
  facet normal -0.09497250616550446 0.7221735119819641 0.6851610541343689
    outer loop
      vertex -40.5 5.377999782562256 3.6619999408721924
      vertex -41.632999420166016 5.229000091552734 3.6619999408721924
      vertex -40.5 4.581999778747559 4.500999927520752
    endloop
  endfacet
  facet normal 0.11214938759803772 -0.046043314039707184 0.992624044418335
    outer loop
      vertex -82.90299987792969 -60.617000579833984 2.5
      vertex -83.27899932861328 -58.64400100708008 2.634000062942505
      vertex -83.91699981689453 -60.198001861572266 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -79.06700134277344 16.48200035095215 2.5
      vertex -50.83100128173828 16.240999221801758 2.5
      vertex -79.03299713134766 17.259000778198242 2.5
    endloop
  endfacet
  facet normal -0.06735207140445709 0.087761789560318 0.993861973285675
    outer loop
      vertex -45.16299819946289 -51.020999908447266 2.5
      vertex -45.04899978637695 -52.45100021362305 2.634000062942505
      vertex -43.715999603271484 -51.428001403808594 2.634000062942505
    endloop
  endfacet
  facet normal 0.15714548528194427 -0.006876378785818815 0.9875515103340149
    outer loop
      vertex -79.25800323486328 17 2.5339999198913574
      vertex -79.06700134277344 16.48200035095215 2.5
      vertex -79.03299713134766 17.259000778198242 2.5
    endloop
  endfacet
  facet normal 0.15014921128749847 -0.0384817011654377 0.9879141449928284
    outer loop
      vertex -81.97599792480469 -57 2.5
      vertex -83.27899932861328 -58.64400100708008 2.634000062942505
      vertex -82.90299987792969 -60.617000579833984 2.5
    endloop
  endfacet
  facet normal -0.10957454144954681 0.08407296240329742 0.9904166460037231
    outer loop
      vertex -45.16299819946289 -51.020999908447266 2.5
      vertex -46.07099914550781 -53.78300094604492 2.634000062942505
      vertex -45.04899978637695 -52.45100021362305 2.634000062942505
    endloop
  endfacet
  facet normal 0.12169307470321655 -0.015558598563075066 0.9924458265304565
    outer loop
      vertex -81.97599792480469 -57 2.5
      vertex -83.06600189208984 -56.97800064086914 2.634000062942505
      vertex -83.27899932861328 -58.64400100708008 2.634000062942505
    endloop
  endfacet
  facet normal -0.21081587672233582 0.5094314813613892 0.8342878222465515
    outer loop
      vertex -43.17300033569336 -52.369998931884766 3.0280001163482666
      vertex -42.68899917602539 -53.20800018310547 3.6619999408721924
      vertex -41.632999420166016 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal -0.09503646194934845 0.7221212983131409 0.685207188129425
    outer loop
      vertex -40.5 4.581999778747559 4.500999927520752
      vertex -41.632999420166016 5.229000091552734 3.6619999408721924
      vertex -41.426998138427734 4.460000038146973 4.500999927520752
    endloop
  endfacet
  facet normal -0.11298856884241104 0.8585278987884521 0.5001633763313293
    outer loop
      vertex -41.426998138427734 4.460000038146973 4.500999927520752
      vertex -40.5 4 5.5
      vertex -40.5 4.581999778747559 4.500999927520752
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -80.73999786376953 17.965999603271484 3.5
      vertex -80.73999786376953 17.965999603271484 10.5
      vertex -80.4990005493164 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -80.9990005493164 18 3.5
      vertex -80.9990005493164 18 10.5
      vertex -80.73999786376953 17.965999603271484 3.5
    endloop
  endfacet
  facet normal 0.5792171359062195 -0.44109615683555603 0.6855229139328003
    outer loop
      vertex -86.95800018310547 -59.52399826049805 4.500999927520752
      vertex -86.39299774169922 -60.08599853515625 3.6619999408721924
      vertex -85.69999694824219 -59.17599868774414 3.6619999408721924
    endloop
  endfacet
  facet normal 0.5791335701942444 -0.44194984436035156 0.6850435137748718
    outer loop
      vertex -86.39099884033203 -58.78099822998047 4.500999927520752
      vertex -86.95800018310547 -59.52399826049805 4.500999927520752
      vertex -85.69999694824219 -59.17599868774414 3.6619999408721924
    endloop
  endfacet
  facet normal -0.21085025370121002 0.5093573331832886 0.8343244194984436
    outer loop
      vertex -43.17300033569336 -52.369998931884766 3.0280001163482666
      vertex -41.632999420166016 -52.770999908447266 3.6619999408721924
      vertex -41.882999420166016 -51.83599853515625 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -80.29199981689453 17.707000732421875 10.5
      vertex -80.29199981689453 17.707000732421875 3.5
      vertex -80.4990005493164 17.865999221801758 10.5
    endloop
  endfacet
  facet normal -0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -88.79199981689453 -57.707000732421875 5.5
      vertex -88.79199981689453 -57.707000732421875 0
      vertex -88.9990005493164 -57.86600112915039 0
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -80.4990005493164 17.865999221801758 3.5
      vertex -80.73999786376953 17.965999603271484 3.5
      vertex -80.4990005493164 17.865999221801758 10.5
    endloop
  endfacet
  facet normal -0.20901815593242645 0.27221542596817017 0.9392604231834412
    outer loop
      vertex -43.17300033569336 -52.369998931884766 3.0280001163482666
      vertex -45.04899978637695 -52.45100021362305 2.634000062942505
      vertex -44.279998779296875 -53.220001220703125 3.0280001163482666
    endloop
  endfacet
  facet normal 0.8579592704772949 0.11277299374341965 0.501186728477478
    outer loop
      vertex -86.60099792480469 1.7760000228881836 5.5
      vertex -86.4990005493164 1 5.5
      vertex -85.91699981689453 1.0119999647140503 4.500999927520752
    endloop
  endfacet
  facet normal 0.8586313724517822 0.11578092724084854 0.4993465542793274
    outer loop
      vertex -86.04199981689453 1.9390000104904175 4.500999927520752
      vertex -86.60099792480469 1.7760000228881836 5.5
      vertex -85.91699981689453 1.0119999647140503 4.500999927520752
    endloop
  endfacet
  facet normal -0.33575916290283203 0.4372769296169281 0.8342989087104797
    outer loop
      vertex -43.17300033569336 -52.369998931884766 3.0280001163482666
      vertex -44.279998779296875 -53.220001220703125 3.0280001163482666
      vertex -42.68899917602539 -53.20800018310547 3.6619999408721924
    endloop
  endfacet
  facet normal 0.799350917339325 0.3312227725982666 0.5013278126716614
    outer loop
      vertex -86.04199981689453 1.9390000104904175 4.500999927520752
      vertex -86.9010009765625 2.5 5.5
      vertex -86.60099792480469 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0.43835803866386414 -0.3340999186038971 0.8343976736068726
    outer loop
      vertex -86.39299774169922 -60.08599853515625 3.6619999408721924
      vertex -85.70600128173828 -60.768001556396484 3.0280001163482666
      vertex -84.86000061035156 -59.65800094604492 3.0280001163482666
    endloop
  endfacet
  facet normal 0.44504186511039734 -0.576386570930481 0.685358464717865
    outer loop
      vertex -87.697998046875 -60.09600067138672 4.500999927520752
      vertex -87.2969970703125 -60.784000396728516 3.6619999408721924
      vertex -86.39299774169922 -60.08599853515625 3.6619999408721924
    endloop
  endfacet
  facet normal 0.28131869435310364 -0.6717360615730286 0.6852958798408508
    outer loop
      vertex -88.55999755859375 -60.457000732421875 4.500999927520752
      vertex -87.2969970703125 -60.784000396728516 3.6619999408721924
      vertex -87.697998046875 -60.09600067138672 4.500999927520752
    endloop
  endfacet
  facet normal 0.2809862792491913 -0.6722007393836975 0.6849765181541443
    outer loop
      vertex -88.35199737548828 -61.224998474121094 3.6619999408721924
      vertex -87.2969970703125 -60.784000396728516 3.6619999408721924
      vertex -88.55999755859375 -60.457000732421875 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.4990005493164 1 5.5
      vertex -86.60099792480469 1.7760000228881836 5.5
      vertex -88.53299713134766 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.9010009765625 2.5 5.5
      vertex -88.53299713134766 1.2589999437332153 5.5
      vertex -86.60099792480469 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0.3368742763996124 -0.43629562854766846 0.8343631625175476
    outer loop
      vertex -86.39299774169922 -60.08599853515625 3.6619999408721924
      vertex -87.2969970703125 -60.784000396728516 3.6619999408721924
      vertex -85.70600128173828 -60.768001556396484 3.0280001163482666
    endloop
  endfacet
  facet normal -0.958304762840271 0.07850386947393417 0.2747528851032257
    outer loop
      vertex -35 1.0010000467300415 4.946000099182129
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
      vertex -35.0359992980957 1.7059999704360962 4.61899995803833
    endloop
  endfacet
  facet normal 0.33686017990112305 -0.4363780915737152 0.8343257308006287
    outer loop
      vertex -87.2969970703125 -60.784000396728516 3.6619999408721924
      vertex -86.81099700927734 -61.62099838256836 3.0280001163482666
      vertex -85.70600128173828 -60.768001556396484 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.79199981689453 1.7070000171661377 5.5
      vertex -87.37799835205078 3.121000051498413 5.5
      vertex -88.9990005493164 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 14 3.5
      vertex -35 4.0289998054504395 4.131999969482422
      vertex -35 14 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.9990005493164 3.5980000495910645 5.5
      vertex -88.9990005493164 1.8660000562667847 5.5
      vertex -87.37799835205078 3.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.0973551943898201 -0.7219861149787903 0.685024082660675
    outer loop
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -88.35199737548828 -61.224998474121094 3.6619999408721924
      vertex -88.55999755859375 -60.457000732421875 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42.527000427246094 -49.7599983215332 2.5
      vertex -36 -32.768001556396484 2.5
      vertex -45.16299819946289 -51.020999908447266 2.5
    endloop
  endfacet
  facet normal -0.24768595397472382 0.11863341927528381 0.961549699306488
    outer loop
      vertex -36.0359992980957 1.569000005722046 3.8949999809265137
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
      vertex -35.46799850463867 1.069000005722046 4.103000164031982
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.53299713134766 1.2589999437332153 5.5
      vertex -86.9010009765625 2.5 5.5
      vertex -88.63300323486328 1.5 5.5
    endloop
  endfacet
  facet normal -0.26733165979385376 0.09520923346281052 0.9588894248008728
    outer loop
      vertex -35.45500183105469 1.5989999771118164 4.053999900817871
      vertex -36.0359992980957 1.569000005722046 3.8949999809265137
      vertex -35.46799850463867 1.069000005722046 4.103000164031982
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.63300323486328 1.5 5.5
      vertex -87.37799835205078 3.121000051498413 5.5
      vertex -88.79199981689453 1.7070000171661377 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.37799835205078 3.121000051498413 5.5
      vertex -88.63300323486328 1.5 5.5
      vertex -86.9010009765625 2.5 5.5
    endloop
  endfacet
  facet normal 0.21258606016635895 -0.5085675716400146 0.834365725517273
    outer loop
      vertex -87.2969970703125 -60.784000396728516 3.6619999408721924
      vertex -88.35199737548828 -61.224998474121094 3.6619999408721924
      vertex -86.81099700927734 -61.62099838256836 3.0280001163482666
    endloop
  endfacet
  facet normal 0.09756017476320267 -0.7218177318572998 0.6851723790168762
    outer loop
      vertex -88.35199737548828 -61.224998474121094 3.6619999408721924
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -89.48400115966797 -61.37799835205078 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6036890745162964 0.08806166052818298 0.7923412919044495
    outer loop
      vertex -35.46799850463867 1.069000005722046 4.103000164031982
      vertex -35.31399917602539 1.0720000267028809 4.21999979019165
      vertex -35.45500183105469 1.5989999771118164 4.053999900817871
    endloop
  endfacet
  facet normal -0.44339895248413086 0.5774316787719727 0.6855435967445374
    outer loop
      vertex -42.29100036621094 -53.89799880981445 4.500999927520752
      vertex -43.59600067138672 -53.90399932861328 3.6619999408721924
      vertex -43.03200149536133 -54.46699905395508 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.9990005493164 1.8660000562667847 5.5
      vertex -89.75800323486328 1.965999960899353 5.5
      vertex -90.9990005493164 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal -0.6171607375144958 0.08139388263225555 0.7826159000396729
    outer loop
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.45500183105469 1.5989999771118164 4.053999900817871
      vertex -35.31399917602539 1.0720000267028809 4.21999979019165
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.2760009765625 3.8980000019073486 5.5
      vertex -90.9990005493164 3.5980000495910645 5.5
      vertex -89.75800323486328 1.965999960899353 5.5
    endloop
  endfacet
  facet normal -0.44330033659935 0.5776916742324829 0.6853883266448975
    outer loop
      vertex -42.29100036621094 -53.89799880981445 4.500999927520752
      vertex -42.68899917602539 -53.20800018310547 3.6619999408721924
      vertex -43.59600067138672 -53.90399932861328 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.23999786376953 1.965999960899353 5.5
      vertex -89.4990005493164 4 5.5
      vertex -89.4990005493164 2 5.5
    endloop
  endfacet
  facet normal -0.6176230311393738 0.1986152082681656 0.760982096195221
    outer loop
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.426998138427734 2.1649999618530273 3.928999900817871
      vertex -35.45500183105469 1.5989999771118164 4.053999900817871
    endloop
  endfacet
  facet normal -0.2787246108055115 0.672676146030426 0.6854337453842163
    outer loop
      vertex -42.29100036621094 -53.89799880981445 4.500999927520752
      vertex -41.426998138427734 -53.540000915527344 4.500999927520752
      vertex -42.68899917602539 -53.20800018310547 3.6619999408721924
    endloop
  endfacet
  facet normal -0.8562787175178528 0.06075218319892883 0.5129287838935852
    outer loop
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.31399917602539 1.0720000267028809 4.21999979019165
      vertex -35.0369987487793 1.0839999914169312 4.681000232696533
    endloop
  endfacet
  facet normal 0.07385952025651932 -0.5462444424629211 0.8343631029129028
    outer loop
      vertex -89.48400115966797 -61.37799835205078 3.6619999408721924
      vertex -89.48100280761719 -62.34600067138672 3.0280001163482666
      vertex -88.0979995727539 -62.159000396728516 3.0280001163482666
    endloop
  endfacet
  facet normal -0.8609719276428223 0.05182207003235817 0.5060057044029236
    outer loop
      vertex -35.0359992980957 1.7059999704360962 4.61899995803833
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.0369987487793 1.0839999914169312 4.681000232696533
    endloop
  endfacet
  facet normal -0.3357207775115967 0.43749818205833435 0.8341983556747437
    outer loop
      vertex -44.279998779296875 -53.220001220703125 3.0280001163482666
      vertex -43.59600067138672 -53.90399932861328 3.6619999408721924
      vertex -42.68899917602539 -53.20800018310547 3.6619999408721924
    endloop
  endfacet
  facet normal -0.8555865287780762 -0.04871673882007599 0.5153623819351196
    outer loop
      vertex -35.0369987487793 1.0839999914169312 4.681000232696533
      vertex -35.31399917602539 1.0720000267028809 4.21999979019165
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.9990005493164 0.1340000033378601 5.5
      vertex -89.23999786376953 0.03400000184774399 5.5
      vertex -87.9990005493164 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -88.53299713134766 -57.25899887084961 5.5
      vertex -88.53299713134766 -57.25899887084961 0
      vertex -88.63300323486328 -57.5 5.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -88.63300323486328 -57.5 0
      vertex -88.63300323486328 -57.5 5.5
      vertex -88.53299713134766 -57.25899887084961 0
    endloop
  endfacet
  facet normal -0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -88.63300323486328 -57.5 5.5
      vertex -88.63300323486328 -57.5 0
      vertex -88.79199981689453 -57.707000732421875 0
    endloop
  endfacet
  facet normal -0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -88.63300323486328 -57.5 5.5
      vertex -88.79199981689453 -57.707000732421875 0
      vertex -88.79199981689453 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal -0.5777515769004822 0.4438253343105316 0.6849979758262634
    outer loop
      vertex -44.29100036621094 -54.81100082397461 3.6619999408721924
      vertex -43.60200119018555 -55.20899963378906 4.500999927520752
      vertex -43.03200149536133 -54.46699905395508 4.500999927520752
    endloop
  endfacet
  facet normal -0.8610098958015442 0.13570939004421234 0.49014782905578613
    outer loop
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.0359992980957 1.7059999704360962 4.61899995803833
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.4990005493164 1 5.5
      vertex -86.4990005493164 1 5.5
      vertex -88.53299713134766 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.23999786376953 -57.965999603271484 0
      vertex -89.4990005493164 -58 0
      vertex -89.4990005493164 -58 5.5
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 -58 5.5
      vertex -89.4990005493164 -58 0
      vertex -89.75800323486328 -57.965999603271484 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.53299713134766 0.7409999966621399 5.5
      vertex -86.4990005493164 1 5.5
      vertex -88.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.60099792480469 0.2240000069141388 5.5
      vertex -86.4990005493164 1 5.5
      vertex -88.53299713134766 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.63300323486328 0.5 5.5
      vertex -86.9010009765625 -0.5 5.5
      vertex -88.53299713134766 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.79199981689453 0.2930000126361847 5.5
      vertex -88.9990005493164 0.1340000033378601 5.5
      vertex -87.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -89.75800323486328 -57.965999603271484 0
      vertex -89.9990005493164 -57.86600112915039 0
      vertex -89.9990005493164 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -89.9990005493164 -57.86600112915039 5.5
      vertex -89.9990005493164 -57.86600112915039 0
      vertex -90.20600128173828 -57.707000732421875 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 4.0289998054504395 4.131999969482422
      vertex -35 1.0010000467300415 4.946000099182129
      vertex -35 14 10.5
    endloop
  endfacet
  facet normal 0.13129131495952606 -0.3171643912792206 0.9392387270927429
    outer loop
      vertex -37.82600021362305 -3.630000114440918 3.0280001163482666
      vertex -39.11600112915039 -4.164000034332275 3.0280001163482666
      vertex -37.28300094604492 -4.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal -0.9734699130058289 0.05940207466483116 0.22096988558769226
    outer loop
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
      vertex -35 1.0010000467300415 4.946000099182129
      vertex -35 4.0289998054504395 4.131999969482422
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 -2 5.5
      vertex -88.7229995727539 -1.8980000019073486 5.5
      vertex -89.23999786376953 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 0 5.5
      vertex -89.75800323486328 0.03400000184774399 5.5
      vertex -89.4990005493164 -2 5.5
    endloop
  endfacet
  facet normal 0.209854856133461 -0.2718518376350403 0.9391791820526123
    outer loop
      vertex -85.70600128173828 -60.768001556396484 3.0280001163482666
      vertex -86.81099700927734 -61.62099838256836 3.0280001163482666
      vertex -84.93499755859375 -61.534000396728516 2.634000062942505
    endloop
  endfacet
  facet normal 0.0718642920255661 -0.5464845299720764 0.8343801498413086
    outer loop
      vertex -40.5 -4.3460001945495605 3.0280001163482666
      vertex -39.11600112915039 -4.164000034332275 3.0280001163482666
      vertex -40.5 -3.378000020980835 3.6619999408721924
    endloop
  endfacet
  facet normal 0.2731564939022064 -0.20813870429992676 0.9391825199127197
    outer loop
      vertex -83.91699981689453 -60.198001861572266 2.634000062942505
      vertex -85.70600128173828 -60.768001556396484 3.0280001163482666
      vertex -84.93499755859375 -61.534000396728516 2.634000062942505
    endloop
  endfacet
  facet normal 0.053709447383880615 -0.12037945538759232 0.9912739396095276
    outer loop
      vertex -36 -5.103000164031982 2.5
      vertex -36.20899963378906 -3.3269999027252197 2.7269999980926514
      vertex -37.28300094604492 -4.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal -0.9895762205123901 0.015858355909585953 0.143134206533432
    outer loop
      vertex -35.0359992980957 1.7059999704360962 4.61899995803833
      vertex -35.0369987487793 1.0839999914169312 4.681000232696533
      vertex -35 1.0010000467300415 4.946000099182129
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.75800323486328 0.03400000184774399 5.5
      vertex -89.9990005493164 0.1340000033378601 5.5
      vertex -90.9990005493164 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.20600128173828 0.2930000126361847 5.5
      vertex -90.36499786376953 0.5 5.5
      vertex -91.62000274658203 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.11278249323368073 -0.10554223507642746 0.9879984259605408
    outer loop
      vertex -84.93499755859375 -61.534000396728516 2.634000062942505
      vertex -85.4540023803711 -63.34299850463867 2.5
      vertex -82.90299987792969 -60.617000579833984 2.5
    endloop
  endfacet
  facet normal 0.044764354825019836 -0.3404058516025543 0.939212441444397
    outer loop
      vertex -38.83399963378906 -5.214000225067139 2.634000062942505
      vertex -39.11600112915039 -4.164000034332275 3.0280001163482666
      vertex -40.5 -4.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.099712073802948 -0.07597821205854416 0.9921112656593323
    outer loop
      vertex -82.90299987792969 -60.617000579833984 2.5
      vertex -83.91699981689453 -60.198001861572266 2.634000062942505
      vertex -84.93499755859375 -61.534000396728516 2.634000062942505
    endloop
  endfacet
  facet normal 0.04491778090596199 -0.3401501178741455 0.9392977952957153
    outer loop
      vertex -38.83399963378906 -5.214000225067139 2.634000062942505
      vertex -40.5 -4.3460001945495605 3.0280001163482666
      vertex -40.5 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0.5359854698181152 0.07265324890613556 0.8410951495170593
    outer loop
      vertex -36.76300048828125 1.3270000219345093 4.285999774932861
      vertex -36.249000549316406 1.065999984741211 3.9809999465942383
      vertex -36.22200012207031 1.5729999542236328 3.9200000762939453
    endloop
  endfacet
  facet normal 0.1312878131866455 -0.31717661023139954 0.9392350912094116
    outer loop
      vertex -38.83399963378906 -5.214000225067139 2.634000062942505
      vertex -37.28300094604492 -4.572000026702881 2.634000062942505
      vertex -39.11600112915039 -4.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal 0.014495695941150188 -0.10977195203304291 0.9938510656356812
    outer loop
      vertex -39.619998931884766 -6.531000137329102 2.5
      vertex -38.83399963378906 -5.214000225067139 2.634000062942505
      vertex -40.5 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -85.4540023803711 -63.34299850463867 2.5
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -82.90299987792969 -60.617000579833984 2.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -89.23999786376953 1.965999960899353 5.5
      vertex -89.23999786376953 1.965999960899353 0
      vertex -88.9990005493164 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -92.9990005493164 -84 2.5
      vertex -85.4540023803711 -63.34299850463867 2.5
    endloop
  endfacet
  facet normal 0.051966167986392975 -0.1317349672317505 0.9899219274520874
    outer loop
      vertex -36 -5.103000164031982 2.5
      vertex -38.83399963378906 -5.214000225067139 2.634000062942505
      vertex -39.619998931884766 -6.531000137329102 2.5
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -88.9990005493164 1.8660000562667847 0
      vertex -88.79199981689453 1.7070000171661377 5.5
      vertex -88.9990005493164 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal 0.0517444983124733 -0.12500891089439392 0.9908053874969482
    outer loop
      vertex -38.83399963378906 -5.214000225067139 2.634000062942505
      vertex -36 -5.103000164031982 2.5
      vertex -37.28300094604492 -4.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal 0.5043916702270508 0.15465636551380157 0.8495119214057922
    outer loop
      vertex -36.742000579833984 1.6540000438690186 4.214000225067139
      vertex -36.76300048828125 1.3270000219345093 4.285999774932861
      vertex -36.22200012207031 1.5729999542236328 3.9200000762939453
    endloop
  endfacet
  facet normal -0.5646383762359619 -0.2331591248512268 0.7917198538780212
    outer loop
      vertex -35.41400146484375 -82.64700317382812 2.634000062942505
      vertex -35.165000915527344 -83.25 2.634000062942505
      vertex -34.98500061035156 -83.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 0 5.5
      vertex -89.23999786376953 0.03400000184774399 5.5
      vertex -89.4990005493164 0 0
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.23999786376953 0.03400000184774399 0
      vertex -89.4990005493164 0 0
      vertex -89.23999786376953 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal -0.5654784440994263 -0.23416738212108612 0.7908222079277039
    outer loop
      vertex -35.41400146484375 -82.64700317382812 2.634000062942505
      vertex -34.98500061035156 -83.14600372314453 2.7929999828338623
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
    endloop
  endfacet
  facet normal -0.4847888648509979 -0.3715013563632965 0.7918121814727783
    outer loop
      vertex -34.62099838256836 -83.62100219726562 2.7929999828338623
      vertex -34.98500061035156 -83.14600372314453 2.7929999828338623
      vertex -35.165000915527344 -83.25 2.634000062942505
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 0 0
      vertex -89.75800323486328 0.03400000184774399 5.5
      vertex -89.4990005493164 0 5.5
    endloop
  endfacet
  facet normal 0.5091115236282349 -0.0031745368614792824 0.8606947064399719
    outer loop
      vertex -36.762001037597656 0.6740000247955322 4.2829999923706055
      vertex -36.249000549316406 1.065999984741211 3.9809999465942383
      vertex -36.76300048828125 1.3270000219345093 4.285999774932861
    endloop
  endfacet
  facet normal -0.8000219464302063 -0.33039578795433044 0.5008029341697693
    outer loop
      vertex -43.097999572753906 -0.5 5.5
      vertex -43.39699935913086 0.2240000069141388 5.5
      vertex -43.959999084472656 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal -0.7364738583564758 -0.3049774169921875 0.6038170456886292
    outer loop
      vertex -35.2140007019043 -82.59300231933594 2.7929999828338623
      vertex -34.98500061035156 -83.14600372314453 2.7929999828338623
      vertex -34.847999572753906 -83.06700134277344 3
    endloop
  endfacet
  facet normal 0.7376112937927246 -0.09761299192905426 0.6681326627731323
    outer loop
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
      vertex -36.742000579833984 0.34599998593330383 4.2129998207092285
      vertex -36.762001037597656 0.6740000247955322 4.2829999923706055
    endloop
  endfacet
  facet normal -0.6325322389602661 -0.4851321876049042 0.6037794947624207
    outer loop
      vertex -34.50899887084961 -83.50900268554688 3
      vertex -34.847999572753906 -83.06700134277344 3
      vertex -34.98500061035156 -83.14600372314453 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7999835014343262 -0.331474632024765 0.5001509785652161
    outer loop
      vertex -43.959999084472656 0.0729999989271164 4.500999927520752
      vertex -43.60200119018555 -0.7910000085830688 4.500999927520752
      vertex -43.097999572753906 -0.5 5.5
    endloop
  endfacet
  facet normal 0.7578991055488586 -0.15637518465518951 0.6333528161048889
    outer loop
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
      vertex -36.742000579833984 0.34599998593330383 4.2129998207092285
    endloop
  endfacet
  facet normal -0.8540567755699158 -0.3532312512397766 0.38185691833496094
    outer loop
      vertex -35.06100082397461 -82.552001953125 3
      vertex -34.847999572753906 -83.06700134277344 3
      vertex -34.9640007019043 -82.5260009765625 3.240999937057495
    endloop
  endfacet
  facet normal 0.07383401691913605 -0.5462751984596252 0.8343452215194702
    outer loop
      vertex -88.35199737548828 -61.224998474121094 3.6619999408721924
      vertex -89.48400115966797 -61.37799835205078 3.6619999408721924
      vertex -88.0979995727539 -62.159000396728516 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6867461204528809 -0.5275006294250488 0.5001228451728821
    outer loop
      vertex -43.60200119018555 -0.7910000085830688 4.500999927520752
      vertex -42.62099838256836 -1.121000051498413 5.5
      vertex -43.097999572753906 -0.5 5.5
    endloop
  endfacet
  facet normal -0.6867327690124512 -0.5275440216064453 0.5000954270362854
    outer loop
      vertex -43.60200119018555 -0.7910000085830688 4.500999927520752
      vertex -43.03200149536133 -1.5329999923706055 4.500999927520752
      vertex -42.62099838256836 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.06986882537603378 -0.5467137098312378 0.8343994617462158
    outer loop
      vertex -89.48100280761719 -62.34600067138672 3.0280001163482666
      vertex -89.48400115966797 -61.37799835205078 3.6619999408721924
      vertex -90.86599731445312 -62.16899871826172 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5274690985679626 -0.6867050528526306 0.5002124905586243
    outer loop
      vertex -43.03200149536133 -1.5329999923706055 4.500999927520752
      vertex -42 -1.5980000495910645 5.5
      vertex -42.62099838256836 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.2787246108055115 -0.672676146030426 0.6854337453842163
    outer loop
      vertex -42.68899917602539 -2.7920000553131104 3.6619999408721924
      vertex -41.426998138427734 -2.4600000381469727 4.500999927520752
      vertex -42.29100036621094 -2.1019999980926514 4.500999927520752
    endloop
  endfacet
  facet normal -0.5273966789245605 -0.6868206262588501 0.5001301765441895
    outer loop
      vertex -43.03200149536133 -1.5329999923706055 4.500999927520752
      vertex -42.29100036621094 -2.1019999980926514 4.500999927520752
      vertex -42 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal -0.33148324489593506 -0.799979567527771 0.500151515007019
    outer loop
      vertex -42.29100036621094 -2.1019999980926514 4.500999927520752
      vertex -41.2760009765625 -1.8980000019073486 5.5
      vertex -42 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.2714167535305023 0.20974041521549225 0.9393305778503418
    outer loop
      vertex -85.73200225830078 4.793000221252441 3.0280001163482666
      vertex -83.93800354003906 4.236000061035156 2.634000062942505
      vertex -84.96499633789062 5.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal 0.04967215284705162 -0.11739049851894379 0.9918428063392639
    outer loop
      vertex -85.4540023803711 -63.34299850463867 2.5
      vertex -87.81300354003906 -63.20899963378906 2.634000062942505
      vertex -88.05599975585938 -64.44400024414062 2.5
    endloop
  endfacet
  facet normal 0.0999877005815506 0.0772666409611702 0.9919840097427368
    outer loop
      vertex -82.90299987792969 4.617000102996826 2.5
      vertex -84.96499633789062 5.565000057220459 2.634000062942505
      vertex -83.93800354003906 4.236000061035156 2.634000062942505
    endloop
  endfacet
  facet normal -0.3314758837223053 -0.7999864816665649 0.5001453757286072
    outer loop
      vertex -42.29100036621094 -2.1019999980926514 4.500999927520752
      vertex -41.426998138427734 -2.4600000381469727 4.500999927520752
      vertex -41.2760009765625 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0.11268971115350723 0.1054554134607315 0.9880183339118958
    outer loop
      vertex -85.4540023803711 7.3429999351501465 2.5
      vertex -84.96499633789062 5.565000057220459 2.634000062942505
      vertex -82.90299987792969 4.617000102996826 2.5
    endloop
  endfacet
  facet normal -0.11298856884241104 -0.8585278987884521 0.5001633763313293
    outer loop
      vertex -41.426998138427734 -2.4600000381469727 4.500999927520752
      vertex -40.5 -2.5820000171661377 4.500999927520752
      vertex -40.5 -2 5.5
    endloop
  endfacet
  facet normal 0.21259057521820068 -0.5085577368736267 0.8343705534934998
    outer loop
      vertex -88.35199737548828 -61.224998474121094 3.6619999408721924
      vertex -88.0979995727539 -62.159000396728516 3.0280001163482666
      vertex -86.81099700927734 -61.62099838256836 3.0280001163482666
    endloop
  endfacet
  facet normal -0.1128569096326828 -0.8585976958274841 0.5000733733177185
    outer loop
      vertex -41.426998138427734 -2.4600000381469727 4.500999927520752
      vertex -40.5 -2 5.5
      vertex -41.2760009765625 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.207000732421875 0.2930000126361847 5.5
      vertex -42.62099838256836 -1.121000051498413 5.5
      vertex -41 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.39699935913086 0.2240000069141388 5.5
      vertex -43.097999572753906 -0.5 5.5
      vertex -41.36600112915039 0.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.097999572753906 -0.5 5.5
      vertex -42.62099838256836 -1.121000051498413 5.5
      vertex -41.36600112915039 0.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.207000732421875 0.2930000126361847 5.5
      vertex -41.36600112915039 0.5 5.5
      vertex -42.62099838256836 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42 -1.5980000495910645 5.5
      vertex -41 0.1340000033378601 5.5
      vertex -42.62099838256836 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.2760009765625 -1.8980000019073486 5.5
      vertex -41 0.1340000033378601 5.5
      vertex -42 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -2 5.5
      vertex -40.5 0 5.5
      vertex -41.2760009765625 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0.045970600098371506 -0.33998578786849976 0.9393063187599182
    outer loop
      vertex -88.0979995727539 -62.159000396728516 3.0280001163482666
      vertex -89.48100280761719 -62.34600067138672 3.0280001163482666
      vertex -87.81300354003906 -63.20899963378906 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -50.83100128173828 16.240999221801758 2.5
      vertex -82.90299987792969 4.617000102996826 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -82.90299987792969 4.617000102996826 2.5
      vertex -80.9990005493164 15 2.5
      vertex -85.4540023803711 7.3429999351501465 2.5
    endloop
  endfacet
  facet normal 0.04594893753528595 -0.34002211689949036 0.9392942190170288
    outer loop
      vertex -87.81300354003906 -63.20899963378906 2.634000062942505
      vertex -89.48100280761719 -62.34600067138672 3.0280001163482666
      vertex -89.47799682617188 -63.433998107910156 2.634000062942505
    endloop
  endfacet
  facet normal -0.672881543636322 -0.27880969643592834 0.6851974725723267
    outer loop
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
      vertex -43.60200119018555 -0.7910000085830688 4.500999927520752
      vertex -43.959999084472656 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal -0.6729307770729065 -0.2791133224964142 0.6850255131721497
    outer loop
      vertex -44.29100036621094 -1.1890000104904175 3.6619999408721924
      vertex -43.60200119018555 -0.7910000085830688 4.500999927520752
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
    endloop
  endfacet
  facet normal 0.014968560077250004 -0.11076734215021133 0.9937336444854736
    outer loop
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -87.81300354003906 -63.20899963378906 2.634000062942505
      vertex -89.47799682617188 -63.433998107910156 2.634000062942505
    endloop
  endfacet
  facet normal 0.2098587304353714 -0.2715698480606079 0.9392598867416382
    outer loop
      vertex -84.93499755859375 -61.534000396728516 2.634000062942505
      vertex -86.81099700927734 -61.62099838256836 3.0280001163482666
      vertex -86.26399993896484 -62.56100082397461 2.634000062942505
    endloop
  endfacet
  facet normal 0.132411390542984 -0.31652042269706726 0.939298689365387
    outer loop
      vertex -88.0979995727539 -62.159000396728516 3.0280001163482666
      vertex -87.81300354003906 -63.20899963378906 2.634000062942505
      vertex -86.26399993896484 -62.56100082397461 2.634000062942505
    endloop
  endfacet
  facet normal 0.13237202167510986 -0.31665948033332825 0.9392573833465576
    outer loop
      vertex -86.81099700927734 -61.62099838256836 3.0280001163482666
      vertex -88.0979995727539 -62.159000396728516 3.0280001163482666
      vertex -86.26399993896484 -62.56100082397461 2.634000062942505
    endloop
  endfacet
  facet normal 0.04959798976778984 -0.11856062710285187 0.9917073249816895
    outer loop
      vertex -85.4540023803711 -63.34299850463867 2.5
      vertex -86.26399993896484 -62.56100082397461 2.634000062942505
      vertex -87.81300354003906 -63.20899963378906 2.634000062942505
    endloop
  endfacet
  facet normal -0.5778562426567078 -0.4427895247936249 0.685579776763916
    outer loop
      vertex -43.59600067138672 -2.0959999561309814 3.6619999408721924
      vertex -43.03200149536133 -1.5329999923706055 4.500999927520752
      vertex -44.29100036621094 -1.1890000104904175 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5777515769004822 -0.4438253343105316 0.6849979758262634
    outer loop
      vertex -44.29100036621094 -1.1890000104904175 3.6619999408721924
      vertex -43.03200149536133 -1.5329999923706055 4.500999927520752
      vertex -43.60200119018555 -0.7910000085830688 4.500999927520752
    endloop
  endfacet
  facet normal 0.04355567321181297 0.34057092666625977 0.9392094016075134
    outer loop
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
      vertex -88.13300323486328 6.169000148773193 3.0280001163482666
      vertex -87.8550033569336 7.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal -0.5091010928153992 -0.21116124093532562 0.8344022035598755
    outer loop
      vertex -45.66400146484375 -0.3840000033378601 3.0280001163482666
      vertex -44.29100036621094 -1.1890000104904175 3.6619999408721924
      vertex -44.729000091552734 -0.13300000131130219 3.6619999408721924
    endloop
  endfacet
  facet normal 0.0730210468173027 -0.09449364244937897 0.9928438067436218
    outer loop
      vertex -86.26399993896484 -62.56100082397461 2.634000062942505
      vertex -85.4540023803711 -63.34299850463867 2.5
      vertex -84.93499755859375 -61.534000396728516 2.634000062942505
    endloop
  endfacet
  facet normal 0.5043092370033264 -0.15070946514606476 0.8502698540687561
    outer loop
      vertex -36.762001037597656 0.6740000247955322 4.2829999923706055
      vertex -36.742000579833984 0.34599998593330383 4.2129998207092285
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -93.9990005493164 -83.73200225830078 2.5
      vertex -93.51699829101562 -83.93199920654297 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
    endloop
  endfacet
  facet normal 0.13039329648017883 0.3176037073135376 0.939215362071991
    outer loop
      vertex -86.3010025024414 6.581999778747559 2.634000062942505
      vertex -87.8550033569336 7.21999979019165 2.634000062942505
      vertex -88.13300323486328 6.169000148773193 3.0280001163482666
    endloop
  endfacet
  facet normal 0.5066909193992615 -0.2566617429256439 0.8230364918708801
    outer loop
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
      vertex -36.22200012207031 0.43299999833106995 3.9200000762939453
      vertex -36.742000579833984 0.34599998593330383 4.2129998207092285
    endloop
  endfacet
  facet normal 0.0720466747879982 0.09464538842439651 0.992900550365448
    outer loop
      vertex -85.4540023803711 7.3429999351501465 2.5
      vertex -86.3010025024414 6.581999778747559 2.634000062942505
      vertex -84.96499633789062 5.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal -0.24748027324676514 -0.07635249942541122 0.9658797979354858
    outer loop
      vertex -35.46799850463867 1.069000005722046 4.103000164031982
      vertex -36.060001373291016 1.065000057220459 3.9509999752044678
      vertex -35.45500183105469 0.40700000524520874 4.053999900817871
    endloop
  endfacet
  facet normal -0.6025662422180176 -0.07067236304283142 0.7949334979057312
    outer loop
      vertex -35.45500183105469 0.40700000524520874 4.053999900817871
      vertex -35.31399917602539 1.0720000267028809 4.21999979019165
      vertex -35.46799850463867 1.069000005722046 4.103000164031982
    endloop
  endfacet
  facet normal -0.8586313724517822 -0.11578092724084854 0.4993465542793274
    outer loop
      vertex -92.39700317382812 -57.7760009765625 5.5
      vertex -93.08100128173828 -57.012001037597656 4.500999927520752
      vertex -92.95600128173828 -57.93899917602539 4.500999927520752
    endloop
  endfacet
  facet normal -0.799350917339325 -0.3312227725982666 0.5013278126716614
    outer loop
      vertex -92.95600128173828 -57.93899917602539 4.500999927520752
      vertex -92.09700012207031 -58.5 5.5
      vertex -92.39700317382812 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal -0.045970600098371506 0.33998578786849976 0.9393063187599182
    outer loop
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
      vertex -91.18499755859375 7.209000110626221 2.634000062942505
      vertex -90.9000015258789 6.158999919891357 3.0280001163482666
    endloop
  endfacet
  facet normal -0.8612021207809448 -0.1262229084968567 0.49233996868133545
    outer loop
      vertex -35.0359992980957 0.3009999990463257 4.61899995803833
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
      vertex -35.03200149536133 -0.4830000102519989 4.425000190734863
    endloop
  endfacet
  facet normal -0.44339895248413086 -0.5774316787719727 0.6855435967445374
    outer loop
      vertex -42.29100036621094 -2.1019999980926514 4.500999927520752
      vertex -43.03200149536133 -1.5329999923706055 4.500999927520752
      vertex -43.59600067138672 -2.0959999561309814 3.6619999408721924
    endloop
  endfacet
  facet normal -0.44330033659935 -0.5776916742324829 0.6853883266448975
    outer loop
      vertex -43.59600067138672 -2.0959999561309814 3.6619999408721924
      vertex -42.68899917602539 -2.7920000553131104 3.6619999408721924
      vertex -42.29100036621094 -2.1019999980926514 4.500999927520752
    endloop
  endfacet
  facet normal -0.8736547827720642 -0.13768404722213745 0.4666588008403778
    outer loop
      vertex -35.27899932861328 -0.34599998593330383 4.002999782562256
      vertex -35.03200149536133 -0.4830000102519989 4.425000190734863
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
    endloop
  endfacet
  facet normal -0.7992205023765564 -0.3343205153942108 0.4994760751724243
    outer loop
      vertex -92.59500122070312 -58.801998138427734 4.500999927520752
      vertex -92.09700012207031 -58.5 5.5
      vertex -92.95600128173828 -57.93899917602539 4.500999927520752
    endloop
  endfacet
  facet normal -0.6164117455482483 -0.06518742442131042 0.7847210764884949
    outer loop
      vertex -35.31399917602539 1.0720000267028809 4.21999979019165
      vertex -35.45500183105469 0.40700000524520874 4.053999900817871
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
    endloop
  endfacet
  facet normal -0.6861675977706909 -0.5270562767982483 0.5013838410377502
    outer loop
      vertex -91.62000274658203 -59.12099838256836 5.5
      vertex -92.09700012207031 -58.5 5.5
      vertex -92.59500122070312 -58.801998138427734 4.500999927520752
    endloop
  endfacet
  facet normal 0.04938158020377159 0.11670378595590591 0.9919383525848389
    outer loop
      vertex -88.05599975585938 8.444000244140625 2.5
      vertex -87.8550033569336 7.21999979019165 2.634000062942505
      vertex -85.4540023803711 7.3429999351501465 2.5
    endloop
  endfacet
  facet normal -0.860485851764679 -0.041307661682367325 0.5077970027923584
    outer loop
      vertex -35.0369987487793 1.0839999914169312 4.681000232696533
      vertex -35.30500030517578 0.38499999046325684 4.170000076293945
      vertex -35.0359992980957 0.3009999990463257 4.61899995803833
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -91.62000274658203 -59.12099838256836 5.5
      vertex -90.36499786376953 -57.5 5.5
      vertex -92.09700012207031 -58.5 5.5
    endloop
  endfacet
  facet normal -0.9908272624015808 -0.011923979967832565 0.1346072405576706
    outer loop
      vertex -35 1.0010000467300415 4.946000099182129
      vertex -35.0369987487793 1.0839999914169312 4.681000232696533
      vertex -35.0359992980957 0.3009999990463257 4.61899995803833
    endloop
  endfacet
  facet normal -0.20901581645011902 -0.2723539471626282 0.9392207860946655
    outer loop
      vertex -45.04899978637695 -3.5490000247955322 2.634000062942505
      vertex -43.715999603271484 -4.572000026702881 2.634000062942505
      vertex -43.17300033569336 -3.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal -0.9663116335868835 -0.06645756959915161 0.2486468404531479
    outer loop
      vertex -35.0359992980957 0.3009999990463257 4.61899995803833
      vertex -35.03200149536133 -0.4830000102519989 4.425000190734863
      vertex -35 1.0010000467300415 4.946000099182129
    endloop
  endfacet
  facet normal 0.04920056462287903 0.1198396235704422 0.9915733933448792
    outer loop
      vertex -86.3010025024414 6.581999778747559 2.634000062942505
      vertex -85.4540023803711 7.3429999351501465 2.5
      vertex -87.8550033569336 7.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal -0.20901815593242645 -0.27221542596817017 0.9392604231834412
    outer loop
      vertex -45.04899978637695 -3.5490000247955322 2.634000062942505
      vertex -43.17300033569336 -3.630000114440918 3.0280001163482666
      vertex -44.279998779296875 -2.7799999713897705 3.0280001163482666
    endloop
  endfacet
  facet normal -0.04597144573926926 0.33998435735702515 0.9393067955970764
    outer loop
      vertex -89.52100372314453 7.434000015258789 2.634000062942505
      vertex -91.18499755859375 7.209000110626221 2.634000062942505
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.04371333867311478 0.34031036496162415 0.939296543598175
    outer loop
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
      vertex -87.8550033569336 7.21999979019165 2.634000062942505
      vertex -89.52100372314453 7.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal -0.9156789779663086 -0.12363388389348984 0.3824220597743988
    outer loop
      vertex -35.0260009765625 -1.6799999475479126 4.017000198364258
      vertex -35.020999908447266 -2.9110000133514404 3.63100004196167
      vertex -35 1.0010000467300415 4.946000099182129
    endloop
  endfacet
  facet normal -0.3420412838459015 -0.3047020137310028 0.8889119625091553
    outer loop
      vertex -35.03200149536133 -0.4830000102519989 4.425000190734863
      vertex -35.0260009765625 -1.6799999475479126 4.017000198364258
      vertex -35 1.0010000467300415 4.946000099182129
    endloop
  endfacet
  facet normal 0.014275052584707737 0.111131951212883 0.9937031269073486
    outer loop
      vertex -88.05599975585938 8.444000244140625 2.5
      vertex -89.52100372314453 7.434000015258789 2.634000062942505
      vertex -87.8550033569336 7.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal -0.9984588623046875 -0.012792868539690971 0.054002538323402405
    outer loop
      vertex -35 -5.103000164031982 3.5
      vertex -35 1.0010000467300415 4.946000099182129
      vertex -35.020999908447266 -2.9110000133514404 3.63100004196167
    endloop
  endfacet
  facet normal -0.7214087247848511 -0.09727734327316284 0.6856431365013123
    outer loop
      vertex -93.87799835205078 -57.01499938964844 3.6619999408721924
      vertex -92.95600128173828 -57.93899917602539 4.500999927520752
      vertex -93.08100128173828 -57.012001037597656 4.500999927520752
    endloop
  endfacet
  facet normal -0.002339906059205532 0.1348550021648407 0.9908626079559326
    outer loop
      vertex -90.87999725341797 8.395000457763672 2.5
      vertex -89.52100372314453 7.434000015258789 2.634000062942505
      vertex -88.05599975585938 8.444000244140625 2.5
    endloop
  endfacet
  facet normal -0.33575916290283203 -0.4372769296169281 0.8342989087104797
    outer loop
      vertex -44.279998779296875 -2.7799999713897705 3.0280001163482666
      vertex -43.17300033569336 -3.630000114440918 3.0280001163482666
      vertex -42.68899917602539 -2.7920000553131104 3.6619999408721924
    endloop
  endfacet
  facet normal -0.015718501061201096 0.11624705046415329 0.9930959343910217
    outer loop
      vertex -90.87999725341797 8.395000457763672 2.5
      vertex -91.18499755859375 7.209000110626221 2.634000062942505
      vertex -89.52100372314453 7.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal -0.21081587672233582 -0.5094314813613892 0.8342878222465515
    outer loop
      vertex -43.17300033569336 -3.630000114440918 3.0280001163482666
      vertex -41.632999420166016 -3.2290000915527344 3.6619999408721924
      vertex -42.68899917602539 -2.7920000553131104 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3357207775115967 -0.43749818205833435 0.8341983556747437
    outer loop
      vertex -44.279998779296875 -2.7799999713897705 3.0280001163482666
      vertex -42.68899917602539 -2.7920000553131104 3.6619999408721924
      vertex -43.59600067138672 -2.0959999561309814 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.36499786376953 -57.5 5.5
      vertex -91.62000274658203 -59.12099838256836 5.5
      vertex -90.20600128173828 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.9990005493164 15 2.5
      vertex -88.05599975585938 8.444000244140625 2.5
      vertex -85.4540023803711 7.3429999351501465 2.5
    endloop
  endfacet
  facet normal -0.2784997522830963 -0.6729879975318909 0.6852189898490906
    outer loop
      vertex -41.426998138427734 -2.4600000381469727 4.500999927520752
      vertex -42.68899917602539 -2.7920000553131104 3.6619999408721924
      vertex -41.632999420166016 -3.2290000915527344 3.6619999408721924
    endloop
  endfacet
  facet normal -0.09503646194934845 -0.7221212983131409 0.685207188129425
    outer loop
      vertex -41.632999420166016 -3.2290000915527344 3.6619999408721924
      vertex -40.5 -2.5820000171661377 4.500999927520752
      vertex -41.426998138427734 -2.4600000381469727 4.500999927520752
    endloop
  endfacet
  facet normal -0.09747490286827087 0.7218239307403564 0.6851779222488403
    outer loop
      vertex -89.51399993896484 5.377999782562256 3.6619999408721924
      vertex -90.64700317382812 5.224999904632568 3.6619999408721924
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
    endloop
  endfacet
  facet normal -0.09497250616550446 -0.7221735119819641 0.6851610541343689
    outer loop
      vertex -41.632999420166016 -3.2290000915527344 3.6619999408721924
      vertex -40.5 -3.378000020980835 3.6619999408721924
      vertex -40.5 -2.5820000171661377 4.500999927520752
    endloop
  endfacet
  facet normal -0.21085025370121002 -0.5093573331832886 0.8343244194984436
    outer loop
      vertex -41.632999420166016 -3.2290000915527344 3.6619999408721924
      vertex -43.17300033569336 -3.630000114440918 3.0280001163482666
      vertex -41.882999420166016 -4.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal 0.380079448223114 0.915991485118866 0.1284492462873459
    outer loop
      vertex -80.73999786376953 17.965999603271484 3.5
      vertex -80.4990005493164 17.865999221801758 3.5
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
    endloop
  endfacet
  facet normal -0.7333922982215881 -0.5626739263534546 0.3814889192581177
    outer loop
      vertex -34.847999572753906 -83.06700134277344 3
      vertex -34.4379997253418 -83.43800354003906 3.240999937057495
      vertex -34.76100158691406 -83.01699829101562 3.240999937057495
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -80.4990005493164 17.865999221801758 10.5
      vertex -80.29199981689453 17.707000732421875 3.5
      vertex -80.4990005493164 17.865999221801758 3.5
    endloop
  endfacet
  facet normal -0.21764862537384033 -0.15166135132312775 0.9641721248626709
    outer loop
      vertex -35.652000427246094 -83.40299987792969 2.5
      vertex -35.236000061035156 -84 2.5
      vertex -35.165000915527344 -83.25 2.634000062942505
    endloop
  endfacet
  facet normal -0.21407334506511688 -0.2837849259376526 0.9346864223480225
    outer loop
      vertex -34.930999755859375 -84 2.5260000228881836
      vertex -34.62099838256836 -84 2.5969998836517334
      vertex -34.766998291015625 -83.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal -0.07187410444021225 -0.5465325713157654 0.8343477845191956
    outer loop
      vertex -40.5 -3.378000020980835 3.6619999408721924
      vertex -41.632999420166016 -3.2290000915527344 3.6619999408721924
      vertex -41.882999420166016 -4.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal -0.29319244623184204 -0.22527141869068146 0.9291345477104187
    outer loop
      vertex -35.165000915527344 -83.25 2.634000062942505
      vertex -34.930999755859375 -84 2.5260000228881836
      vertex -34.766998291015625 -83.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal -0.485491007566452 -0.37302204966545105 0.7906662225723267
    outer loop
      vertex -34.62099838256836 -83.62100219726562 2.7929999828338623
      vertex -35.165000915527344 -83.25 2.634000062942505
      vertex -34.766998291015625 -83.76799774169922 2.634000062942505
    endloop
  endfacet
  facet normal 0.37765493988990784 0.916638195514679 0.13096247613430023
    outer loop
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
      vertex -80.4990005493164 17.865999221801758 3.5
      vertex -80.48200225830078 17.895999908447266 3.240999937057495
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -80.29199981689453 17.707000732421875 10.5
      vertex -80.13300323486328 17.5 10.5
      vertex -80.29199981689453 17.707000732421875 3.5
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -80.29199981689453 17.707000732421875 3.5
      vertex -80.13300323486328 17.5 10.5
      vertex -80.13300323486328 17.5 3.5
    endloop
  endfacet
  facet normal 0.6039289236068726 0.7862470746040344 0.13071121275424957
    outer loop
      vertex -80.4990005493164 17.865999221801758 3.5
      vertex -80.29199981689453 17.707000732421875 3.5
      vertex -80.48200225830078 17.895999908447266 3.240999937057495
    endloop
  endfacet
  facet normal -0.08373674750328064 -0.16757655143737793 0.9822964072227478
    outer loop
      vertex -35.165000915527344 -83.25 2.634000062942505
      vertex -35.236000061035156 -84 2.5
      vertex -34.930999755859375 -84 2.5260000228881836
    endloop
  endfacet
  facet normal 0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -80.03299713134766 17.259000778198242 10.5
      vertex -80.03299713134766 17.259000778198242 3.5
      vertex -80.13300323486328 17.5 10.5
    endloop
  endfacet
  facet normal -0.25169122219085693 -0.04554832726716995 0.9667351841926575
    outer loop
      vertex -35.652000427246094 -83.40299987792969 2.5
      vertex -35.165000915527344 -83.25 2.634000062942505
      vertex -35.64699935913086 -82.70899963378906 2.5339999198913574
    endloop
  endfacet
  facet normal -0.10216563194990158 -0.0423276424407959 0.9938664436340332
    outer loop
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -46.07099914550781 -2.2170000076293945 2.634000062942505
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
    endloop
  endfacet
  facet normal -0.3567332327365875 -0.14730775356292725 0.9225192666053772
    outer loop
      vertex -35.41400146484375 -82.64700317382812 2.634000062942505
      vertex -35.64699935913086 -82.70899963378906 2.5339999198913574
      vertex -35.165000915527344 -83.25 2.634000062942505
    endloop
  endfacet
  facet normal -0.10637283325195312 -0.060802310705184937 0.9924655556678772
    outer loop
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -46.54100036621094 -3.5820000171661377 2.5
      vertex -46.07099914550781 -2.2170000076293945 2.634000062942505
    endloop
  endfacet
  facet normal -0.3170148432254791 -0.13134054839611053 0.9392822980880737
    outer loop
      vertex -45.12900161743164 -1.6729999780654907 3.0280001163482666
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
      vertex -46.07099914550781 -2.2170000076293945 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35.652000427246094 -83.40299987792969 2.5
      vertex -92.9990005493164 -84 2.5
      vertex -35.236000061035156 -84 2.5
    endloop
  endfacet
  facet normal 0.7999835014343262 0.331474632024765 0.5001509785652161
    outer loop
      vertex -37.39699935913086 2.7909998893737793 4.500999927520752
      vertex -37.9010009765625 2.5 5.5
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -45.16299819946289 -62.979000091552734 2.5
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -92.9990005493164 -84 2.5
    endloop
  endfacet
  facet normal 0.09238508343696594 0.7225150465965271 0.6851547360420227
    outer loop
      vertex -89.51399993896484 5.377999782562256 3.6619999408721924
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
    endloop
  endfacet
  facet normal -0.2723022699356079 -0.20892861485481262 0.9392551779747009
    outer loop
      vertex -44.279998779296875 -2.7799999713897705 3.0280001163482666
      vertex -46.07099914550781 -2.2170000076293945 2.634000062942505
      vertex -45.04899978637695 -3.5490000247955322 2.634000062942505
    endloop
  endfacet
  facet normal 0.09271565079689026 0.7222471237182617 0.6853924989700317
    outer loop
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
      vertex -88.58399963378906 4.4629998207092285 4.500999927520752
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
    endloop
  endfacet
  facet normal -0.08777151256799698 -0.06734421104192734 0.9938616156578064
    outer loop
      vertex -45.04899978637695 -3.5490000247955322 2.634000062942505
      vertex -46.07099914550781 -2.2170000076293945 2.634000062942505
      vertex -46.54100036621094 -3.5820000171661377 2.5
    endloop
  endfacet
  facet normal 0.06990589946508408 0.546712338924408 0.8343972563743591
    outer loop
      vertex -89.51399993896484 5.377999782562256 3.6619999408721924
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6867461204528809 0.5275006294250488 0.5001228451728821
    outer loop
      vertex -37.39699935913086 2.7909998893737793 4.500999927520752
      vertex -38.37799835205078 3.121000051498413 5.5
      vertex -37.9010009765625 2.5 5.5
    endloop
  endfacet
  facet normal 0.06992045789957047 0.5467227101325989 0.8343892693519592
    outer loop
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
      vertex -88.13300323486328 6.169000148773193 3.0280001163482666
      vertex -89.51699829101562 6.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6867327690124512 0.5275440216064453 0.5000954270362854
    outer loop
      vertex -37.39699935913086 2.7909998893737793 4.500999927520752
      vertex -37.96699905395508 3.5329999923706055 4.500999927520752
      vertex -38.37799835205078 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.31718528270721436 -0.13164788484573364 0.9391817450523376
    outer loop
      vertex -45.66400146484375 -0.3840000033378601 3.0280001163482666
      vertex -46.7140007019043 -0.6650000214576721 2.634000062942505
      vertex -45.12900161743164 -1.6729999780654907 3.0280001163482666
    endloop
  endfacet
  facet normal 0.4435596466064453 0.577640950679779 0.6852633357048035
    outer loop
      vertex -37.96699905395508 3.5329999923706055 4.500999927520752
      vertex -37.40399932861328 4.0960001945495605 3.6619999408721924
      vertex -38.70800018310547 4.1020002365112305 4.500999927520752
    endloop
  endfacet
  facet normal -0.5091621279716492 -0.21132797002792358 0.8343227505683899
    outer loop
      vertex -45.66400146484375 -0.3840000033378601 3.0280001163482666
      vertex -45.12900161743164 -1.6729999780654907 3.0280001163482666
      vertex -44.29100036621094 -1.1890000104904175 3.6619999408721924
    endloop
  endfacet
  facet normal 0.5272573828697205 0.6866392493247986 0.5005258917808533
    outer loop
      vertex -37.96699905395508 3.5329999923706055 4.500999927520752
      vertex -38.70800018310547 4.1020002365112305 4.500999927520752
      vertex -39 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.4990005493164 -57 5.5
      vertex -92.39700317382812 -57.7760009765625 5.5
      vertex -90.46499633789062 -57.25899887084961 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.09700012207031 -58.5 5.5
      vertex -90.46499633789062 -57.25899887084961 5.5
      vertex -92.39700317382812 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.9990005493164 -57.86600112915039 5.5
      vertex -90.20600128173828 -57.707000732421875 5.5
      vertex -91.62000274658203 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.46499633789062 -57.25899887084961 5.5
      vertex -92.09700012207031 -58.5 5.5
      vertex -90.36499786376953 -57.5 5.5
    endloop
  endfacet
  facet normal -0.5778562426567078 0.4427895247936249 0.685579776763916
    outer loop
      vertex -43.03200149536133 -54.46699905395508 4.500999927520752
      vertex -43.59600067138672 -53.90399932861328 3.6619999408721924
      vertex -44.29100036621094 -54.81100082397461 3.6619999408721924
    endloop
  endfacet
  facet normal 0.6055121421813965 0.7853309512138367 0.12888121604919434
    outer loop
      vertex -80.29199981689453 17.707000732421875 3.5
      vertex -80.26799774169922 17.731000900268555 3.240999937057495
      vertex -80.48200225830078 17.895999908447266 3.240999937057495
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 80 83 2.5
      vertex 80 -82 2.5
      vertex 80 -82 10.5
    endloop
  endfacet
  facet normal 0.7864401340484619 0.6040772199630737 0.1288510262966156
    outer loop
      vertex -80.26799774169922 17.731000900268555 3.240999937057495
      vertex -80.29199981689453 17.707000732421875 3.5
      vertex -80.13300323486328 17.5 3.5
    endloop
  endfacet
  facet normal -0.6853792071342468 -0.5295690298080444 0.49981197714805603
    outer loop
      vertex -92.02400207519531 -59.54100036621094 4.500999927520752
      vertex -91.62000274658203 -59.12099838256836 5.5
      vertex -92.59500122070312 -58.801998138427734 4.500999927520752
    endloop
  endfacet
  facet normal -0.7221735119819641 0.09497250616550446 0.6851610541343689
    outer loop
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
      vertex -44.87799835205078 -57 3.6619999408721924
      vertex -44.082000732421875 -57 4.500999927520752
    endloop
  endfacet
  facet normal 0.7872229814529419 0.6032924056053162 0.12774300575256348
    outer loop
      vertex -80.13300323486328 17.5 3.5
      vertex -80.10399627685547 17.517000198364258 3.240999937057495
      vertex -80.26799774169922 17.731000900268555 3.240999937057495
    endloop
  endfacet
  facet normal -0.7221212983131409 0.09503646194934845 0.685207188129425
    outer loop
      vertex -44.082000732421875 -57 4.500999927520752
      vertex -43.959999084472656 -56.073001861572266 4.500999927520752
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.18104553222656 3.33152437210083
      vertex 82.99800109863281 83.0150146484375 3.5
      vertex 82.99800109863281 -84 0
    endloop
  endfacet
  facet normal -0.672881543636322 0.27880969643592834 0.6851974725723267
    outer loop
      vertex -43.60200119018555 -55.20899963378906 4.500999927520752
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
      vertex -43.959999084472656 -56.073001861572266 4.500999927520752
    endloop
  endfacet
  facet normal -0.6729307770729065 0.2791133224964142 0.6850255131721497
    outer loop
      vertex -43.60200119018555 -55.20899963378906 4.500999927520752
      vertex -44.29100036621094 -54.81100082397461 3.6619999408721924
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5091010928153992 0.21116124093532562 0.8344022035598755
    outer loop
      vertex -45.66400146484375 -55.61600112915039 3.0280001163482666
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
      vertex -44.29100036621094 -54.81100082397461 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 85 0
      vertex 82.99800109863281 83.27051544189453 3.240999937057495
      vertex 82.99800109863281 -84 0
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 82.99800109863281 83.27051544189453 3.240999937057495
      vertex 82.99800109863281 83.18104553222656 3.33152437210083
      vertex 82.99800109863281 -84 0
    endloop
  endfacet
  facet normal -0.5269930958747864 -0.6860854029655457 0.5015626549720764
    outer loop
      vertex -92.02400207519531 -59.54100036621094 4.500999927520752
      vertex -90.9990005493164 -59.597999572753906 5.5
      vertex -91.62000274658203 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -80.13300323486328 17.5 3.5
      vertex -80.13300323486328 17.5 10.5
      vertex -80.03299713134766 17.259000778198242 3.5
    endloop
  endfacet
  facet normal 0.5269486308097839 0.6871321797370911 0.5001745223999023
    outer loop
      vertex -37.96699905395508 3.5329999923706055 4.500999927520752
      vertex -39 3.5980000495910645 5.5
      vertex -38.37799835205078 3.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.7221735119819641 -0.09497250616550446 0.6851610541343689
    outer loop
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
      vertex -44.082000732421875 -57 4.500999927520752
      vertex -44.87799835205078 -57 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5251178741455078 -0.6890435814857483 0.4994698464870453
    outer loop
      vertex -92.02400207519531 -59.54100036621094 4.500999927520752
      vertex -91.27999877929688 -60.108001708984375 4.500999927520752
      vertex -90.9990005493164 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal 0.5643277764320374 0.7319160103797913 0.3818809688091278
    outer loop
      vertex -80.1969985961914 17.802000045776367 3
      vertex -80.48200225830078 17.895999908447266 3.240999937057495
      vertex -80.26799774169922 17.731000900268555 3.240999937057495
    endloop
  endfacet
  facet normal -0.5464843511581421 -0.07186775654554367 0.8343799114227295
    outer loop
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -44.729000091552734 -58.132999420166016 3.6619999408721924
      vertex -44.87799835205078 -57 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3318139612674713 0.7996716499328613 0.5004246234893799
    outer loop
      vertex -38.70800018310547 4.1020002365112305 4.500999927520752
      vertex -39.722999572753906 3.8980000019073486 5.5
      vertex -39 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.9909924268722534 0.133917897939682 0
    outer loop
      vertex -41.46500015258789 -57.25899887084961 0
      vertex -41.5 -57 0
      vertex -41.5 -57 5.5
    endloop
  endfacet
  facet normal 0.9909924268722534 -0.133917897939682 0
    outer loop
      vertex -41.46500015258789 -56.74100112915039 0
      vertex -41.46500015258789 -56.74100112915039 5.5
      vertex -41.5 -57 0
    endloop
  endfacet
  facet normal 0.9909924268722534 -0.133917897939682 0
    outer loop
      vertex -41.5 -57 5.5
      vertex -41.5 -57 0
      vertex -41.46500015258789 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal 0.9249957203865051 -0.3799774944782257 0
    outer loop
      vertex -41.46500015258789 -56.74100112915039 5.5
      vertex -41.46500015258789 -56.74100112915039 0
      vertex -41.36600112915039 -56.5 0
    endloop
  endfacet
  facet normal 0.9249957203865051 -0.3799774944782257 0
    outer loop
      vertex -41.46500015258789 -56.74100112915039 5.5
      vertex -41.36600112915039 -56.5 0
      vertex -41.36600112915039 -56.5 5.5
    endloop
  endfacet
  facet normal 0.3314758837223053 0.7999864816665649 0.5001453757286072
    outer loop
      vertex -39.571998596191406 4.460000038146973 4.500999927520752
      vertex -39.722999572753906 3.8980000019073486 5.5
      vertex -38.70800018310547 4.1020002365112305 4.500999927520752
    endloop
  endfacet
  facet normal -0.3316230773925781 -0.7992116212844849 0.5012853145599365
    outer loop
      vertex -91.27999877929688 -60.108001708984375 4.500999927520752
      vertex -90.2760009765625 -59.89799880981445 5.5
      vertex -90.9990005493164 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -41.207000732421875 -56.292999267578125 0
      vertex -41.207000732421875 -56.292999267578125 5.5
      vertex -41.36600112915039 -56.5 0
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -41.36600112915039 -56.5 5.5
      vertex -41.36600112915039 -56.5 0
      vertex -41.207000732421875 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal 0.11286836862564087 0.8585397005081177 0.5001702904701233
    outer loop
      vertex -39.571998596191406 4.460000038146973 4.500999927520752
      vertex -40.5 4.581999778747559 4.500999927520752
      vertex -40.5 4 5.5
    endloop
  endfacet
  facet normal 0.7336912155151367 0.5622680187225342 0.3815126121044159
    outer loop
      vertex -80.26799774169922 17.731000900268555 3.240999937057495
      vertex -80.10399627685547 17.517000198364258 3.240999937057495
      vertex -80.01699829101562 17.566999435424805 3
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -41.207000732421875 -56.292999267578125 5.5
      vertex -41.207000732421875 -56.292999267578125 0
      vertex -41 -56.13399887084961 5.5
    endloop
  endfacet
  facet normal 0.1127147451043129 0.8586211800575256 0.5000650882720947
    outer loop
      vertex -40.5 4 5.5
      vertex -39.722999572753906 3.8980000019073486 5.5
      vertex -39.571998596191406 4.460000038146973 4.500999927520752
    endloop
  endfacet
  facet normal -0.2764846384525299 -0.6736879348754883 0.6853471994400024
    outer loop
      vertex -91.27999877929688 -60.108001708984375 4.500999927520752
      vertex -91.6760025024414 -60.79899978637695 3.6619999408721924
      vertex -90.41500091552734 -60.4630012512207 4.500999927520752
    endloop
  endfacet
  facet normal -0.1128569096326828 0.8585976958274841 0.5000733733177185
    outer loop
      vertex -41.426998138427734 4.460000038146973 4.500999927520752
      vertex -41.2760009765625 3.8980000019073486 5.5
      vertex -40.5 4 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.2760009765625 3.8980000019073486 5.5
      vertex -40.5 2 5.5
      vertex -40.5 4 5.5
    endloop
  endfacet
  facet normal 0.7337559461593628 0.5620258450508118 0.3817448616027832
    outer loop
      vertex -80.26799774169922 17.731000900268555 3.240999937057495
      vertex -80.01699829101562 17.566999435424805 3
      vertex -80.1969985961914 17.802000045776367 3
    endloop
  endfacet
  facet normal -0.3289930522441864 -0.801630973815918 0.49915066361427307
    outer loop
      vertex -91.27999877929688 -60.108001708984375 4.500999927520752
      vertex -90.41500091552734 -60.4630012512207 4.500999927520752
      vertex -90.2760009765625 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal -0.1126457080245018 -0.8580952286720276 0.5009825229644775
    outer loop
      vertex -90.41500091552734 -60.4630012512207 4.500999927520752
      vertex -89.4990005493164 -60 5.5
      vertex -90.2760009765625 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 2 5.5
      vertex -41.2760009765625 3.8980000019073486 5.5
      vertex -40.757999420166016 1.965999960899353 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.24100112915039 1.965999960899353 5.5
      vertex -40.5 4 5.5
      vertex -40.5 2 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39 3.5980000495910645 5.5
      vertex -39.79199981689453 1.7070000171661377 5.5
      vertex -38.37799835205078 3.121000051498413 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 4 5.5
      vertex -40.24100112915039 1.965999960899353 5.5
      vertex -39.722999572753906 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -41.207000732421875 -56.292999267578125 0
      vertex -41 -56.13399887084961 0
      vertex -41 -56.13399887084961 5.5
    endloop
  endfacet
  facet normal -0.11019986122846603 -0.8593736886978149 0.4993324279785156
    outer loop
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -89.4990005493164 -60 5.5
      vertex -90.41500091552734 -60.4630012512207 4.500999927520752
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -80.73999786376953 17.965999603271484 10.5
      vertex -80.73999786376953 17.965999603271484 3.5
      vertex -80.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0.3819020092487335 -0.9242027997970581 0
    outer loop
      vertex -40.757999420166016 -56.034000396728516 0
      vertex -41 -56.13399887084961 5.5
      vertex -41 -56.13399887084961 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 -60 5.5
      vertex -89.75800323486328 -57.965999603271484 5.5
      vertex -90.2760009765625 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.9990005493164 -59.597999572753906 5.5
      vertex -90.2760009765625 -59.89799880981445 5.5
      vertex -89.75800323486328 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0.2764846384525299 0.6736879348754883 0.6853471994400024
    outer loop
      vertex -88.58399963378906 4.4629998207092285 4.500999927520752
      vertex -87.71900177001953 4.107999801635742 4.500999927520752
      vertex -87.322998046875 4.798999786376953 3.6619999408721924
    endloop
  endfacet
  facet normal 0.2765670120716095 0.6735744476318359 0.6854255199432373
    outer loop
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
      vertex -88.58399963378906 4.4629998207092285 4.500999927520752
      vertex -87.322998046875 4.798999786376953 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7369192242622375 -0.09698397666215897 0.6689873933792114
    outer loop
      vertex -36.762001037597656 0.6740000247955322 4.2829999923706055
      vertex -36.91699981689453 1 4.500999927520752
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal 0.44145017862319946 0.5792573690414429 0.6852610111236572
    outer loop
      vertex -87.71900177001953 4.107999801635742 4.500999927520752
      vertex -86.9749984741211 3.5409998893737793 4.500999927520752
      vertex -86.41400146484375 4.105999946594238 3.6619999408721924
    endloop
  endfacet
  facet normal -0.27227458357810974 0.20881763100624084 0.9392879009246826
    outer loop
      vertex -44.279998779296875 -53.220001220703125 3.0280001163482666
      vertex -46.07099914550781 -53.78300094604492 2.634000062942505
      vertex -45.12900161743164 -54.32699966430664 3.0280001163482666
    endloop
  endfacet
  facet normal 0.4415043294429779 0.5791160464286804 0.6853455305099487
    outer loop
      vertex -86.41400146484375 4.105999946594238 3.6619999408721924
      vertex -87.322998046875 4.798999786376953 3.6619999408721924
      vertex -87.71900177001953 4.107999801635742 4.500999927520752
    endloop
  endfacet
  facet normal -0.2723022699356079 0.20892861485481262 0.9392551779747009
    outer loop
      vertex -44.279998779296875 -53.220001220703125 3.0280001163482666
      vertex -45.04899978637695 -52.45100021362305 2.634000062942505
      vertex -46.07099914550781 -53.78300094604492 2.634000062942505
    endloop
  endfacet
  facet normal 0.20933778584003448 0.5099152326583862 0.8343645334243774
    outer loop
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
      vertex -86.84200286865234 5.638999938964844 3.0280001163482666
      vertex -88.13300323486328 6.169000148773193 3.0280001163482666
    endloop
  endfacet
  facet normal 0.8581587672233582 -0.1129399910569191 0.5008074045181274
    outer loop
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
      vertex -36.91699981689453 1 4.500999927520752
      vertex -37.5 1 5.5
    endloop
  endfacet
  facet normal 0.8139881491661072 -0.0014221301535144448 0.5808797478675842
    outer loop
      vertex -36.762001037597656 0.6740000247955322 4.2829999923706055
      vertex -36.76300048828125 1.3270000219345093 4.285999774932861
      vertex -36.91699981689453 1 4.500999927520752
    endloop
  endfacet
  facet normal -0.14467309415340424 0.08264139294624329 0.9860223531723022
    outer loop
      vertex -45.16299819946289 -51.020999908447266 2.5
      vertex -48.018001556396484 -56.01900100708008 2.5
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
    endloop
  endfacet
  facet normal 0.8581724166870117 0.11280101537704468 0.5008153319358826
    outer loop
      vertex -36.91699981689453 1 4.500999927520752
      vertex -37.60200119018555 1.7760000228881836 5.5
      vertex -37.5 1 5.5
    endloop
  endfacet
  facet normal 0.2093544900417328 0.509879469871521 0.834382176399231
    outer loop
      vertex -88.37999725341797 5.232999801635742 3.6619999408721924
      vertex -87.322998046875 4.798999786376953 3.6619999408721924
      vertex -86.84200286865234 5.638999938964844 3.0280001163482666
    endloop
  endfacet
  facet normal 0.8582057952880859 0.11294617503881454 0.5007254481315613
    outer loop
      vertex -36.91699981689453 1 4.500999927520752
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
      vertex -37.60200119018555 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0.6862668991088867 -0.527132511138916 0.5011676549911499
    outer loop
      vertex -86.95800018310547 -1.5240000486373901 4.500999927520752
      vertex -86.9010009765625 -0.5 5.5
      vertex -87.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.17622704803943634 -0.03703349083662033 0.983652651309967
    outer loop
      vertex -48.018001556396484 -56.01900100708008 2.5
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
    endloop
  endfacet
  facet normal 0.8582285642623901 -0.11280839145183563 0.5007174611091614
    outer loop
      vertex -37.5 1 5.5
      vertex -37.60200119018555 0.2240000069141388 5.5
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal -0.4832805395126343 0.2002251148223877 0.8522616028785706
    outer loop
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
      vertex -46.07099914550781 -53.78300094604492 2.634000062942505
      vertex -45.16299819946289 -51.020999908447266 2.5
    endloop
  endfacet
  facet normal 0.7337898015975952 0.09657212346792221 0.6724777221679688
    outer loop
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
      vertex -36.91699981689453 1 4.500999927520752
      vertex -36.76300048828125 1.3270000219345093 4.285999774932861
    endloop
  endfacet
  facet normal -0.3170148432254791 0.13134054839611053 0.9392822980880737
    outer loop
      vertex -45.12900161743164 -54.32699966430664 3.0280001163482666
      vertex -46.07099914550781 -53.78300094604492 2.634000062942505
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
    endloop
  endfacet
  facet normal 0.6887195110321045 -0.5255773067474365 0.49943360686302185
    outer loop
      vertex -86.95800018310547 -1.5240000486373901 4.500999927520752
      vertex -86.39099884033203 -0.781000018119812 4.500999927520752
      vertex -86.9010009765625 -0.5 5.5
    endloop
  endfacet
  facet normal 0.799384593963623 -0.33123672008514404 0.5012649297714233
    outer loop
      vertex -86.9010009765625 -0.5 5.5
      vertex -86.39099884033203 -0.781000018119812 4.500999927520752
      vertex -86.60099792480469 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal -0.4375992715358734 0.33561134338378906 0.8341893553733826
    outer loop
      vertex -44.279998779296875 -53.220001220703125 3.0280001163482666
      vertex -45.12900161743164 -54.32699966430664 3.0280001163482666
      vertex -43.59600067138672 -53.90399932861328 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7373291254043579 0.09975915402173996 0.668127179145813
    outer loop
      vertex -36.742000579833984 1.6540000438690186 4.214000225067139
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
      vertex -36.76300048828125 1.3270000219345093 4.285999774932861
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.37799835205078 -1.121000051498413 5.5
      vertex -86.9010009765625 -0.5 5.5
      vertex -88.63300323486328 0.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -86.60099792480469 0.2240000069141388 5.5
      vertex -88.53299713134766 0.7409999966621399 5.5
      vertex -86.9010009765625 -0.5 5.5
    endloop
  endfacet
  facet normal 0.13039080798625946 0.31761232018470764 0.9392127990722656
    outer loop
      vertex -88.13300323486328 6.169000148773193 3.0280001163482666
      vertex -86.84200286865234 5.638999938964844 3.0280001163482666
      vertex -86.3010025024414 6.581999778747559 2.634000062942505
    endloop
  endfacet
  facet normal -0.10969828069210052 0.014428782276809216 0.9938601851463318
    outer loop
      vertex -46.93299865722656 -57 2.634000062942505
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
      vertex -48.018001556396484 -56.01900100708008 2.5
    endloop
  endfacet
  facet normal 0.8000219464302063 0.33039578795433044 0.5008029341697693
    outer loop
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
      vertex -37.9010009765625 2.5 5.5
      vertex -37.60200119018555 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0.3341374397277832 0.4384072721004486 0.8343567848205566
    outer loop
      vertex -85.73200225830078 4.793000221252441 3.0280001163482666
      vertex -86.84200286865234 5.638999938964844 3.0280001163482666
      vertex -87.322998046875 4.798999786376953 3.6619999408721924
    endloop
  endfacet
  facet normal -0.13879188895225525 -0.018255509436130524 0.9901533126831055
    outer loop
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
      vertex -46.93299865722656 -57 2.634000062942505
      vertex -48.018001556396484 -56.01900100708008 2.5
    endloop
  endfacet
  facet normal 0.3341551423072815 0.43830737471580505 0.8344021439552307
    outer loop
      vertex -85.73200225830078 4.793000221252441 3.0280001163482666
      vertex -87.322998046875 4.798999786376953 3.6619999408721924
      vertex -86.41400146484375 4.105999946594238 3.6619999408721924
    endloop
  endfacet
  facet normal 0.43595877289772034 0.337236225605011 0.8343930244445801
    outer loop
      vertex -86.41400146484375 4.105999946594238 3.6619999408721924
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
      vertex -85.73200225830078 4.793000221252441 3.0280001163482666
    endloop
  endfacet
  facet normal 0.68311607837677 -0.28305041790008545 0.6732271909713745
    outer loop
      vertex -37.39699935913086 -0.7910000085830688 4.500999927520752
      vertex -36.667999267578125 -0.3160000145435333 3.9609999656677246
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal -0.4375706613063812 0.3352939486503601 0.8343319892883301
    outer loop
      vertex -45.12900161743164 -54.32699966430664 3.0280001163482666
      vertex -44.29100036621094 -54.81100082397461 3.6619999408721924
      vertex -43.59600067138672 -53.90399932861328 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7999835014343262 -0.331474632024765 0.5001509785652161
    outer loop
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
      vertex -37.9010009765625 -0.5 5.5
      vertex -37.39699935913086 -0.7910000085830688 4.500999927520752
    endloop
  endfacet
  facet normal 0.12888391315937042 0.9832001328468323 0.1292535662651062
    outer loop
      vertex -80.73999786376953 17.965999603271484 3.5
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
      vertex -80.9990005493164 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal 0.8000219464302063 -0.33039578795433044 0.5008029341697693
    outer loop
      vertex -37.60200119018555 0.2240000069141388 5.5
      vertex -37.9010009765625 -0.5 5.5
      vertex -37.03900146484375 0.0729999989271164 4.500999927520752
    endloop
  endfacet
  facet normal 0.1290687471628189 0.9832001328468323 0.1290687471628189
    outer loop
      vertex -80.9990005493164 18 3.5
      vertex -80.73999786376953 17.965999603271484 3.5
      vertex -80.9990005493164 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal -0.7215167284011841 -0.09751948714256287 0.685495138168335
    outer loop
      vertex -93.7249984741211 -58.14699935913086 3.6619999408721924
      vertex -92.95600128173828 -57.93899917602539 4.500999927520752
      vertex -93.87799835205078 -57.01499938964844 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6717368960380554 -0.28079238533973694 0.6855109333992004
    outer loop
      vertex -93.7249984741211 -58.14699935913086 3.6619999408721924
      vertex -93.28399658203125 -59.20199966430664 3.6619999408721924
      vertex -92.59500122070312 -58.801998138427734 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.5 1 5.5
      vertex -39.534000396728516 0.7409999966621399 5.5
      vertex -37.60200119018555 0.2240000069141388 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.9010009765625 2.5 5.5
      vertex -39.534000396728516 1.2589999437332153 5.5
      vertex -37.60200119018555 1.7760000228881836 5.5
    endloop
  endfacet
  facet normal 0.20792272686958313 0.27314135432243347 0.939234733581543
    outer loop
      vertex -84.96499633789062 5.565000057220459 2.634000062942505
      vertex -86.3010025024414 6.581999778747559 2.634000062942505
      vertex -86.84200286865234 5.638999938964844 3.0280001163482666
    endloop
  endfacet
  facet normal -0.31718528270721436 0.13164788484573364 0.9391817450523376
    outer loop
      vertex -45.12900161743164 -54.32699966430664 3.0280001163482666
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
      vertex -45.66400146484375 -55.61600112915039 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6717711687088013 -0.28100740909576416 0.6853892207145691
    outer loop
      vertex -93.7249984741211 -58.14699935913086 3.6619999408721924
      vertex -92.59500122070312 -58.801998138427734 4.500999927520752
      vertex -92.95600128173828 -57.93899917602539 4.500999927520752
    endloop
  endfacet
  facet normal 0.20792944729328156 0.2728152275085449 0.9393280744552612
    outer loop
      vertex -86.84200286865234 5.638999938964844 3.0280001163482666
      vertex -85.73200225830078 4.793000221252441 3.0280001163482666
      vertex -84.96499633789062 5.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.722999572753906 3.8980000019073486 5.5
      vertex -40.24100112915039 1.965999960899353 5.5
      vertex -39 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -38.37799835205078 3.121000051498413 5.5
      vertex -39.79199981689453 1.7070000171661377 5.5
      vertex -37.9010009765625 2.5 5.5
    endloop
  endfacet
  facet normal -0.07377797365188599 0.5463427305221558 0.8343059420585632
    outer loop
      vertex -90.9000015258789 6.158999919891357 3.0280001163482666
      vertex -90.64700317382812 5.224999904632568 3.6619999408721924
      vertex -89.51399993896484 5.377999782562256 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5761858820915222 -0.4451991021633148 0.6854251623153687
    outer loop
      vertex -92.02400207519531 -59.54100036621094 4.500999927520752
      vertex -92.59500122070312 -58.801998138427734 4.500999927520752
      vertex -93.28399658203125 -59.20199966430664 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.534000396728516 1.2589999437332153 5.5
      vertex -37.9010009765625 2.5 5.5
      vertex -39.63399887084961 1.5 5.5
    endloop
  endfacet
  facet normal -0.5091621279716492 0.21132797002792358 0.8343227505683899
    outer loop
      vertex -45.12900161743164 -54.32699966430664 3.0280001163482666
      vertex -45.66400146484375 -55.61600112915039 3.0280001163482666
      vertex -44.29100036621094 -54.81100082397461 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.63399887084961 1.5 5.5
      vertex -37.9010009765625 2.5 5.5
      vertex -39.79199981689453 1.7070000171661377 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.5 1 5.5
      vertex -37.60200119018555 1.7760000228881836 5.5
      vertex -39.534000396728516 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -90.20600128173828 -57.707000732421875 0
      vertex -90.20600128173828 -57.707000732421875 5.5
      vertex -89.9990005493164 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -90.36499786376953 -57.5 5.5
      vertex -90.20600128173828 -57.707000732421875 5.5
      vertex -90.20600128173828 -57.707000732421875 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.757999420166016 1.965999960899353 5.5
      vertex -41.2760009765625 3.8980000019073486 5.5
      vertex -41 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -43.097999572753906 2.5 5.5
      vertex -41.36600112915039 1.5 5.5
      vertex -42.62099838256836 3.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -90.46499633789062 -57.25899887084961 0
      vertex -90.46499633789062 -57.25899887084961 5.5
      vertex -90.36499786376953 -57.5 5.5
    endloop
  endfacet
  facet normal -0.4375706613063812 -0.3352939486503601 0.8343319892883301
    outer loop
      vertex -45.12900161743164 -1.6729999780654907 3.0280001163482666
      vertex -43.59600067138672 -2.0959999561309814 3.6619999408721924
      vertex -44.29100036621094 -1.1890000104904175 3.6619999408721924
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -92.9990005493164 18 3.5
      vertex -92.9990005493164 18 10.5
      vertex -80.9990005493164 18 3.5
    endloop
  endfacet
  facet normal -0.27227458357810974 -0.20881763100624084 0.9392879009246826
    outer loop
      vertex -46.07099914550781 -2.2170000076293945 2.634000062942505
      vertex -44.279998779296875 -2.7799999713897705 3.0280001163482666
      vertex -45.12900161743164 -1.6729999780654907 3.0280001163482666
    endloop
  endfacet
  facet normal -0.4375992715358734 -0.33561134338378906 0.8341893553733826
    outer loop
      vertex -45.12900161743164 -1.6729999780654907 3.0280001163482666
      vertex -44.279998779296875 -2.7799999713897705 3.0280001163482666
      vertex -43.59600067138672 -2.0959999561309814 3.6619999408721924
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 80 -82 2.5
      vertex 25 -82 10.5
      vertex 80 -82 10.5
    endloop
  endfacet
  facet normal -0.09238508343696594 -0.7225150465965271 0.6851547360420227
    outer loop
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -90.61799621582031 -61.233001708984375 3.6619999408721924
      vertex -89.48400115966797 -61.37799835205078 3.6619999408721924
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 80 -82 2.5
      vertex 25 -82 2.5
      vertex 25 -82 10.5
    endloop
  endfacet
  facet normal -0.09262514859437943 -0.7223204970359802 0.685327410697937
    outer loop
      vertex -89.48699951171875 -60.582000732421875 4.500999927520752
      vertex -90.41500091552734 -60.4630012512207 4.500999927520752
      vertex -90.61799621582031 -61.233001708984375 3.6619999408721924
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 25 -82 2.5
      vertex 25 83 2.5
      vertex 25 83 10.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex 25 -82 2.5
      vertex 25 83 10.5
      vertex 25 -82 10.5
    endloop
  endfacet
  facet normal -0.27639999985694885 -0.6738045811653137 0.6852666735649109
    outer loop
      vertex -90.41500091552734 -60.4630012512207 4.500999927520752
      vertex -91.6760025024414 -60.79899978637695 3.6619999408721924
      vertex -90.61799621582031 -61.233001708984375 3.6619999408721924
    endloop
  endfacet
  facet normal 0.6721398830413818 0.2811616361141205 0.6849642992019653
    outer loop
      vertex -86.04199981689453 1.9390000104904175 4.500999927520752
      vertex -85.27400207519531 2.1470000743865967 3.6619999408721924
      vertex -86.40299987792969 2.802000045776367 4.500999927520752
    endloop
  endfacet
  facet normal -0.30230391025543213 -0.3939111828804016 0.8680128455162048
    outer loop
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -43.715999603271484 -4.572000026702881 2.634000062942505
      vertex -45.04899978637695 -3.5490000247955322 2.634000062942505
    endloop
  endfacet
  facet normal 0.6721056699752808 0.2809465229511261 0.685086190700531
    outer loop
      vertex -85.27400207519531 2.1470000743865967 3.6619999408721924
      vertex -85.71499633789062 3.2019999027252197 3.6619999408721924
      vertex -86.40299987792969 2.802000045776367 4.500999927520752
    endloop
  endfacet
  facet normal -0.13129131495952606 -0.3171643912792206 0.9392387270927429
    outer loop
      vertex -41.882999420166016 -4.164000034332275 3.0280001163482666
      vertex -43.17300033569336 -3.630000114440918 3.0280001163482666
      vertex -43.715999603271484 -4.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex 23 85 0
      vertex -92.9990005493164 85 0
      vertex 23 85 10.5
    endloop
  endfacet
  facet normal -0.1312878131866455 -0.31717661023139954 0.9392350912094116
    outer loop
      vertex -42.165000915527344 -5.214000225067139 2.634000062942505
      vertex -41.882999420166016 -4.164000034332275 3.0280001163482666
      vertex -43.715999603271484 -4.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal -0.044944703578948975 -0.3401497006416321 0.9392966032028198
    outer loop
      vertex -40.5 -4.3460001945495605 3.0280001163482666
      vertex -42.165000915527344 -5.214000225067139 2.634000062942505
      vertex -40.5 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal -0.2091914862394333 -0.5099644660949707 0.8343710899353027
    outer loop
      vertex -90.61799621582031 -61.233001708984375 3.6619999408721924
      vertex -91.6760025024414 -60.79899978637695 3.6619999408721924
      vertex -92.15699768066406 -61.638999938964844 3.0280001163482666
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -92.9990005493164 85 10.5
      vertex 23 85 10.5
      vertex -92.9990005493164 85 0
    endloop
  endfacet
  facet normal 0.5084252953529358 0.2125266045331955 0.8344675898551941
    outer loop
      vertex -85.71499633789062 3.2019999027252197 3.6619999408721924
      vertex -85.27400207519531 2.1470000743865967 3.6619999408721924
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 83 10.5
      vertex 25 83 10.5
      vertex 24 84.73200225830078 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.23999786376953 0.03400000184774399 5.5
      vertex -89.4990005493164 0 5.5
      vertex -89.4990005493164 -2 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.2760009765625 -1.8980000019073486 5.5
      vertex -89.4990005493164 -2 5.5
      vertex -89.75800323486328 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.9990005493164 -1.5980000495910645 5.5
      vertex -90.2760009765625 -1.8980000019073486 5.5
      vertex -89.75800323486328 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.7229995727539 -1.8980000019073486 5.5
      vertex -87.9990005493164 -1.5980000495910645 5.5
      vertex -89.23999786376953 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.9990005493164 -1.5980000495910645 5.5
      vertex -87.37799835205078 -1.121000051498413 5.5
      vertex -88.9990005493164 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.63300323486328 0.5 5.5
      vertex -88.79199981689453 0.2930000126361847 5.5
      vertex -87.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal -0.08533303439617157 -0.14477130770683289 0.9857786297798157
    outer loop
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -45.04899978637695 -3.5490000247955322 2.634000062942505
      vertex -46.54100036621094 -3.5820000171661377 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 24.48200035095215 84.93199920654297 10.5
      vertex 24 84.73200225830078 10.5
      vertex 25 83 10.5
    endloop
  endfacet
  facet normal 0.27148178219795227 0.21000492572784424 0.9392526745796204
    outer loop
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
      vertex -83.93800354003906 4.236000061035156 2.634000062942505
      vertex -85.73200225830078 4.793000221252441 3.0280001163482666
    endloop
  endfacet
  facet normal 0.5086036324501038 0.21244469285011292 0.8343797326087952
    outer loop
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
      vertex -85.27400207519531 2.1470000743865967 3.6619999408721924
      vertex -84.33999633789062 2.4010000228881836 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 -82 10.5
      vertex 25 83 10.5
      vertex 23 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 83 10.5
      vertex 80 83 10.5
      vertex 25 85 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 85 10.5
      vertex 24.48200035095215 84.93199920654297 10.5
      vertex 25 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 24 84.73200225830078 10.5
      vertex 23.51799964904785 84.93199920654297 10.5
      vertex 23 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 85 10.5
      vertex 23 83 10.5
      vertex 23.51799964904785 84.93199920654297 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 85 10.5
      vertex -32 83 10.5
      vertex 23 83 10.5
    endloop
  endfacet
  facet normal -0.052343741059303284 -0.1264566034078598 0.9905901551246643
    outer loop
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -42.165000915527344 -5.214000225067139 2.634000062942505
      vertex -43.715999603271484 -4.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 83 10.5
      vertex -32 83 10.5
      vertex 23 85 10.5
    endloop
  endfacet
  facet normal -0.01449542585760355 -0.10970401763916016 0.9938585758209229
    outer loop
      vertex -42.165000915527344 -5.214000225067139 2.634000062942505
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -40.5 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal -0.0016237841919064522 -0.12253325432538986 0.9924630522727966
    outer loop
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -39.619998931884766 -6.531000137329102 2.5
      vertex -40.5 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0.3166539967060089 0.13238179683685303 0.9392578601837158
    outer loop
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
      vertex -83.29000091552734 2.686000108718872 2.634000062942505
      vertex -83.93800354003906 4.236000061035156 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 18 10.5
      vertex -35 14 10.5
      vertex -32 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 18 10.5
      vertex -32 83 10.5
      vertex -35 83 10.5
    endloop
  endfacet
  facet normal -0.0447956807911396 -0.3403979539871216 0.9392138123512268
    outer loop
      vertex -41.882999420166016 -4.164000034332275 3.0280001163482666
      vertex -42.165000915527344 -5.214000225067139 2.634000062942505
      vertex -40.5 -4.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.3165718615055084 0.132232666015625 0.9393065571784973
    outer loop
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
      vertex -84.33999633789062 2.4010000228881836 3.0280001163482666
      vertex -83.29000091552734 2.686000108718872 2.634000062942505
    endloop
  endfacet
  facet normal -0.07191598415374756 -0.5464824438095093 0.8343769907951355
    outer loop
      vertex -41.882999420166016 -4.164000034332275 3.0280001163482666
      vertex -40.5 -4.3460001945495605 3.0280001163482666
      vertex -40.5 -3.378000020980835 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -48.999000549316406 18 10.5
      vertex -37 16 10.5
      vertex -35 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -36.481998443603516 15.932000160217285 10.5
      vertex -36 15.732000350952148 10.5
      vertex -35 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.257999420166016 16.034000396728516 10.5
      vertex -48.999000549316406 16 10.5
      vertex -48.999000549316406 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -46.54100036621094 -3.5820000171661377 2.5
    endloop
  endfacet
  facet normal 0.10964230448007584 0.014759540557861328 0.9938614964485168
    outer loop
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -83.29000091552734 2.686000108718872 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.707000732421875 17.707000732421875 10.5
      vertex -49.8650016784668 17.5 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.8650016784668 17.5 10.5
      vertex -49.96500015258789 17.259000778198242 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.96500015258789 17.259000778198242 10.5
      vertex -49.999000549316406 17 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.999000549316406 17 10.5
      vertex -49.96500015258789 16.740999221801758 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.96500015258789 16.740999221801758 10.5
      vertex -49.8650016784668 16.5 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.257999420166016 17.965999603271484 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
      vertex -49.8650016784668 16.5 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.257999420166016 17.965999603271484 10.5
      vertex -49.8650016784668 16.5 10.5
      vertex -49.707000732421875 16.292999267578125 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.707000732421875 16.292999267578125 10.5
      vertex -49.499000549316406 16.134000778198242 10.5
      vertex -49.257999420166016 17.965999603271484 10.5
    endloop
  endfacet
  facet normal 0.1255684494972229 0.04361257329583168 0.9911258816719055
    outer loop
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -82.90299987792969 4.617000102996826 2.5
      vertex -83.29000091552734 2.686000108718872 2.634000062942505
    endloop
  endfacet
  facet normal 0.11138064414262772 0.04656429588794708 0.9926863312721252
    outer loop
      vertex -83.93800354003906 4.236000061035156 2.634000062942505
      vertex -83.29000091552734 2.686000108718872 2.634000062942505
      vertex -82.90299987792969 4.617000102996826 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 14 10.5
      vertex -35 18 10.5
      vertex -35.06800079345703 14.517999649047852 10.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0 0.3832542896270752
    outer loop
      vertex -35.13399887084961 -50.89699935913086 3
      vertex -35.034000396728516 -50.89699935913086 3.240999937057495
      vertex -35.034000396728516 -5.103000164031982 3.240999937057495
    endloop
  endfacet
  facet normal 0.11277299374341965 -0.8579592704772949 0.501186728477478
    outer loop
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -88.7229995727539 -1.8980000019073486 5.5
      vertex -89.4990005493164 -2 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35.268001556396484 15 10.5
      vertex -35.06800079345703 14.517999649047852 10.5
      vertex -35 18 10.5
    endloop
  endfacet
  facet normal -0.794902503490448 0 0.6067371964454651
    outer loop
      vertex -35.13399887084961 -5.103000164031982 3
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
      vertex -35.13399887084961 -50.89699935913086 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -36.481998443603516 15.932000160217285 10.5
      vertex -35 18 10.5
      vertex -37 16 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35.584999084472656 15.413999557495117 10.5
      vertex -35.268001556396484 15 10.5
      vertex -35 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -36 15.732000350952148 10.5
      vertex -35.584999084472656 15.413999557495117 10.5
      vertex -35 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -81.97599792480469 0.052000001072883606 2.5
      vertex -48.018001556396484 1 2.5
      vertex -81.97599792480469 1.9479999542236328 2.5
    endloop
  endfacet
  facet normal -0.6073083281517029 0 0.7944662570953369
    outer loop
      vertex -35.29199981689453 -50.89699935913086 2.7929999828338623
      vertex -35.29199981689453 -5.103000164031982 2.7929999828338623
      vertex -35.5 -50.89699935913086 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37 16 10.5
      vertex -48.999000549316406 18 10.5
      vertex -48.999000549316406 16 10.5
    endloop
  endfacet
  facet normal 0.0973551943898201 -0.7219861149787903 0.685024082660675
    outer loop
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -88.35199737548828 -3.2249999046325684 3.6619999408721924
      vertex -88.55999755859375 -2.4570000171661377 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 -65.53600311279297 10.5
      vertex -32 -82 10.5
      vertex -35 14 10.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0 0.9914933443069458
    outer loop
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
      vertex -36 -5.103000164031982 2.5
      vertex -36 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.257999420166016 16.034000396728516 10.5
      vertex -48.999000549316406 18 10.5
      vertex -49.499000549316406 16.134000778198242 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.257999420166016 17.965999603271484 10.5
      vertex -49.499000549316406 16.134000778198242 10.5
      vertex -48.999000549316406 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 85 10.5
      vertex -92.9990005493164 85 10.5
      vertex -35 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -36 -5.103000164031982 2.5
      vertex -39.619998931884766 -6.531000137329102 2.5
      vertex -36 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -36 -32.768001556396484 2.5
      vertex -41.582000732421875 -6.505000114440918 2.5
    endloop
  endfacet
  facet normal 0.11578092724084854 -0.8586313724517822 0.4993465542793274
    outer loop
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -88.55999755859375 -2.4570000171661377 4.500999927520752
      vertex -88.7229995727539 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 83 10.5
      vertex -35 83 10.5
      vertex -92.9990005493164 85 10.5
    endloop
  endfacet
  facet normal 0.7219421863555908 0.09757699072360992 0.6850388646125793
    outer loop
      vertex -85.27400207519531 2.1470000743865967 3.6619999408721924
      vertex -86.04199981689453 1.9390000104904175 4.500999927520752
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7218341827392578 0.09733470529317856 0.6851871013641357
    outer loop
      vertex -86.04199981689453 1.9390000104904175 4.500999927520752
      vertex -85.91699981689453 1.0119999647140503 4.500999927520752
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -93.9990005493164 84.73200225830078 10.5
      vertex -92.9990005493164 83 10.5
      vertex -93.51699829101562 84.93199920654297 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.41300201416016 84.41400146484375 10.5
      vertex -92.9990005493164 83 10.5
      vertex -93.9990005493164 84.73200225830078 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.73100280761719 84 10.5
      vertex -92.9990005493164 83 10.5
      vertex -94.41300201416016 84.41400146484375 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.93099975585938 83.51799774169922 10.5
      vertex -92.9990005493164 83 10.5
      vertex -94.73100280761719 84 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.9990005493164 83 10.5
      vertex -92.9990005493164 83 10.5
      vertex -94.93099975585938 83.51799774169922 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 85 10.5
      vertex -93.51699829101562 84.93199920654297 10.5
      vertex -92.9990005493164 83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 83 10.5
      vertex -94.9990005493164 83 10.5
      vertex -94.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 83 10.5
      vertex -94.9990005493164 18 10.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0.3312227725982666 -0.799350917339325 0.5013278126716614
    outer loop
      vertex -88.55999755859375 -2.4570000171661377 4.500999927520752
      vertex -87.9990005493164 -1.5980000495910645 5.5
      vertex -88.7229995727539 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal 0.5462444424629211 0.07385952025651932 0.8343631029129028
    outer loop
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
      vertex -84.15299987792969 1.0180000066757202 3.0280001163482666
      vertex -84.33999633789062 2.4010000228881836 3.0280001163482666
    endloop
  endfacet
  facet normal -0.3832542896270752 0 0.9236428737640381
    outer loop
      vertex -35.74100112915039 -50.89699935913086 2.5339999198913574
      vertex -35.5 -50.89699935913086 2.634000062942505
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -79.9990005493164 17 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.03299713134766 16.740999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.13300323486328 16.5 10.5
      vertex -80.03299713134766 16.740999221801758 10.5
      vertex -80.9990005493164 16 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.03299713134766 17.259000778198242 10.5
      vertex -80.9990005493164 16 10.5
      vertex -79.9990005493164 17 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.13300323486328 17.5 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.03299713134766 17.259000778198242 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.29199981689453 17.707000732421875 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.13300323486328 17.5 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.4990005493164 17.865999221801758 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.29199981689453 17.707000732421875 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.73999786376953 17.965999603271484 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.4990005493164 17.865999221801758 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.9990005493164 18 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.73999786376953 17.965999603271484 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 18 10.5
      vertex -80.9990005493164 16 10.5
      vertex -80.9990005493164 18 10.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0 0.9914933443069458
    outer loop
      vertex -36 -32.768001556396484 2.5
      vertex -35.74100112915039 -50.89699935913086 2.5339999198913574
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
    endloop
  endfacet
  facet normal 0.546712338924408 -0.06990589946508408 0.8343972563743591
    outer loop
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
      vertex -85.26599884033203 -0.11900000274181366 3.6619999408721924
      vertex -84.15299987792969 1.0180000066757202 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.619998931884766 -6.531000137329102 2.5
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -36 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.582000732421875 -6.505000114440918 2.5
      vertex -46.54100036621094 -3.5820000171661377 2.5
      vertex -84.65499877929688 -51.16699981689453 2.5
    endloop
  endfacet
  facet normal 0.3347013294696808 -0.7992037534713745 0.49924781918525696
    outer loop
      vertex -88.55999755859375 -2.4570000171661377 4.500999927520752
      vertex -87.697998046875 -2.0959999561309814 4.500999927520752
      vertex -87.9990005493164 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.5462751984596252 0.07383401691913605 0.8343452215194702
    outer loop
      vertex -84.33999633789062 2.4010000228881836 3.0280001163482666
      vertex -85.27400207519531 2.1470000743865967 3.6619999408721924
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 14 10.5
      vertex -35 1.0010000467300415 4.946000099182129
      vertex -35 -65.53600311279297 10.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 -5.103000164031982 3.5
      vertex -35 -65.53600311279297 10.5
      vertex -35 1.0010000467300415 4.946000099182129
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.9990005493164 18 10.5
      vertex -94.93099975585938 17.48200035095215 10.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.93099975585938 17.48200035095215 10.5
      vertex -94.73100280761719 17 10.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.73100280761719 17 10.5
      vertex -94.41300201416016 16.586000442504883 10.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0.5271956324577332 -0.686349093914032 0.5009887218475342
    outer loop
      vertex -87.697998046875 -2.0959999561309814 4.500999927520752
      vertex -87.37799835205078 -1.121000051498413 5.5
      vertex -87.9990005493164 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.5298786759376526 -0.6855073571205139 0.4993078112602234
    outer loop
      vertex -87.697998046875 -2.0959999561309814 4.500999927520752
      vertex -86.95800018310547 -1.5240000486373901 4.500999927520752
      vertex -87.37799835205078 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.73999786376953 16.034000396728516 10.5
      vertex -80.4990005493164 16.134000778198242 10.5
      vertex -80.9990005493164 16 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.4990005493164 16.134000778198242 10.5
      vertex -80.29199981689453 16.292999267578125 10.5
      vertex -80.9990005493164 16 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.29199981689453 16.292999267578125 10.5
      vertex -80.13300323486328 16.5 10.5
      vertex -80.9990005493164 16 10.5
    endloop
  endfacet
  facet normal 0.7223699688911438 -0.0923665314912796 0.6853101849555969
    outer loop
      vertex -85.26599884033203 -0.11900000274181366 3.6619999408721924
      vertex -85.12100219726562 1.0149999856948853 3.6619999408721924
      vertex -86.03600311279297 0.08399999886751175 4.500999927520752
    endloop
  endfacet
  facet normal 0.6737651228904724 -0.276516318321228 0.6852585673332214
    outer loop
      vertex -86.03600311279297 0.08399999886751175 4.500999927520752
      vertex -86.39099884033203 -0.781000018119812 4.500999927520752
      vertex -85.26599884033203 -0.11900000274181366 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 16 10.5
      vertex -92.9990005493164 18 10.5
      vertex -93.51699829101562 16.06800079345703 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -80.9990005493164 16 10.5
      vertex -92.9990005493164 18 10.5
      vertex -92.9990005493164 16 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -93.9990005493164 16.26799964904785 10.5
      vertex -93.51699829101562 16.06800079345703 10.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.41300201416016 16.586000442504883 10.5
      vertex -93.9990005493164 16.26799964904785 10.5
      vertex -92.9990005493164 18 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 82.99800109863281 -84 10.5
      vertex 80 -82 10.5
      vertex 25 -84 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0 0.9236428737640381
    outer loop
      vertex -35.5 -5.103000164031982 2.634000062942505
      vertex -35.74100112915039 -5.103000164031982 2.5339999198913574
      vertex -35.5 -50.89699935913086 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 24 -83.73200225830078 10.5
      vertex 24.48200035095215 -83.93199920654297 10.5
      vertex 25 -82 10.5
    endloop
  endfacet
  facet normal 0.5470308661460876 -0.070355124771595 0.8341507315635681
    outer loop
      vertex -85.26599884033203 -0.11900000274181366 3.6619999408721924
      vertex -84.33100128173828 -0.3659999966621399 3.0280001163482666
      vertex -84.15299987792969 1.0180000066757202 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -32 -82 10.5
      vertex 23 -84 10.5
      vertex 23 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -38.667999267578125 -49.70800018310547 2.5
      vertex -36 -32.768001556396484 2.5
      vertex -42.527000427246094 -49.7599983215332 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -45.16299819946289 -51.020999908447266 2.5
      vertex -36 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 -82 10.5
      vertex 23 83 10.5
      vertex 23 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 -84 10.5
      vertex 23.51799964904785 -83.93199920654297 10.5
      vertex 23 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23.51799964904785 -83.93199920654297 10.5
      vertex 24 -83.73200225830078 10.5
      vertex 23 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 -82 10.5
      vertex 24 -83.73200225830078 10.5
      vertex 25 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 25 -84 10.5
      vertex 25 -82 10.5
      vertex 24.48200035095215 -83.93199920654297 10.5
    endloop
  endfacet
  facet normal 0.34026017785072327 0.04600770026445389 0.9392051696777344
    outer loop
      vertex -84.33999633789062 2.4010000228881836 3.0280001163482666
      vertex -84.15299987792969 1.0180000066757202 3.0280001163482666
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
    endloop
  endfacet
  facet normal 0.5102490186691284 -0.20950622856616974 0.834118127822876
    outer loop
      vertex -85.26599884033203 -0.11900000274181366 3.6619999408721924
      vertex -85.69999694824219 -1.1759999990463257 3.6619999408721924
      vertex -84.33100128173828 -0.3659999966621399 3.0280001163482666
    endloop
  endfacet
  facet normal 0.34003591537475586 0.04577406495809555 0.9392977952957153
    outer loop
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
      vertex -83.29000091552734 2.686000108718872 2.634000062942505
      vertex -84.33999633789062 2.4010000228881836 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -32 -82 10.5
      vertex -32 83 10.5
      vertex -35 14 10.5
    endloop
  endfacet
  facet normal 0 0.9914933443069458 0.13015742599964142
    outer loop
      vertex -92.9990005493164 18.034000396728516 3.240999937057495
      vertex -92.9990005493164 18 3.5
      vertex -80.9990005493164 18 3.5
    endloop
  endfacet
  facet normal 0 0.9914933443069458 0.13015742599964142
    outer loop
      vertex -92.9990005493164 18.034000396728516 3.240999937057495
      vertex -80.9990005493164 18 3.5
      vertex -80.9990005493164 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal -0.3404421806335449 -0.044769130647182465 0.9391990303993225
    outer loop
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
      vertex -45.66400146484375 -58.38399887084961 3.0280001163482666
      vertex -45.84600067138672 -57 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0.9236428737640381 0.3832542896270752
    outer loop
      vertex -80.9990005493164 18.134000778198242 3
      vertex -92.9990005493164 18.134000778198242 3
      vertex -80.9990005493164 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal -0.3404288589954376 -0.04477712884545326 0.9392035007476807
    outer loop
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -46.93299865722656 -57 2.634000062942505
      vertex -46.7140007019043 -58.665000915527344 2.634000062942505
    endloop
  endfacet
  facet normal -0.3404421806335449 0.044769130647182465 0.9391990303993225
    outer loop
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -45.66400146484375 -55.61600112915039 3.0280001163482666
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
    endloop
  endfacet
  facet normal 0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -80.03299713134766 17.259000778198242 3.5
      vertex -80.03299713134766 17.259000778198242 10.5
      vertex -79.9990005493164 17 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40 1.8660000562667847 5.5
      vertex -39 3.5980000495910645 5.5
      vertex -40.24100112915039 1.965999960899353 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.79199981689453 1.7070000171661377 5.5
      vertex -39 3.5980000495910645 5.5
      vertex -40 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal -0.3404288589954376 0.04477712884545326 0.9392035007476807
    outer loop
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -46.7140007019043 -55.334999084472656 2.634000062942505
      vertex -46.93299865722656 -57 2.634000062942505
    endloop
  endfacet
  facet normal -0.5464843511581421 0.07186775654554367 0.8343799114227295
    outer loop
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -44.87799835205078 -57 3.6619999408721924
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3405860364437103 -0.04380369558930397 0.9391924142837524
    outer loop
      vertex -84.15299987792969 1.0180000066757202 3.0280001163482666
      vertex -84.33100128173828 -0.3659999966621399 3.0280001163482666
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
    endloop
  endfacet
  facet normal 0.5099919438362122 -0.20881249010562897 0.834449291229248
    outer loop
      vertex -84.33100128173828 -0.3659999966621399 3.0280001163482666
      vertex -85.69999694824219 -1.1759999990463257 3.6619999408721924
      vertex -84.86000061035156 -1.6579999923706055 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.9010009765625 -0.5 5.5
      vertex -39.63399887084961 0.5 5.5
      vertex -39.79199981689453 0.2930000126361847 5.5
    endloop
  endfacet
  facet normal 0.9152089953422546 0.3822559714317322 0.12756529450416565
    outer loop
      vertex -80.13300323486328 17.5 3.5
      vertex -80 17.26799964904785 3.240999937057495
      vertex -80.10399627685547 17.517000198364258 3.240999937057495
    endloop
  endfacet
  facet normal -0.5464816689491272 0.07186391949653625 0.8343819975852966
    outer loop
      vertex -45.66400146484375 -55.61600112915039 3.0280001163482666
      vertex -45.84600067138672 -57 3.0280001163482666
      vertex -44.729000091552734 -55.867000579833984 3.6619999408721924
    endloop
  endfacet
  facet normal 0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -80.03299713134766 16.740999221801758 3.5
      vertex -79.9990005493164 17 10.5
      vertex -80.03299713134766 16.740999221801758 10.5
    endloop
  endfacet
  facet normal 0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -79.9990005493164 17 10.5
      vertex -79.9990005493164 17 3.5
      vertex -80.03299713134766 17.259000778198242 3.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40 0.1340000033378601 5.5
      vertex -40.24100112915039 0.03400000184774399 5.5
      vertex -39 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.9158178567886353 0.38000741600990295 0.12989211082458496
    outer loop
      vertex -80 17.26799964904785 3.240999937057495
      vertex -80.13300323486328 17.5 3.5
      vertex -80.03299713134766 17.259000778198242 3.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -82.90299987792969 -60.617000579833984 2.5
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -81.97599792480469 -57 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.534000396728516 1.2589999437332153 5.5
      vertex -39.5 1 5.5
      vertex -37.5 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.534000396728516 0.7409999966621399 5.5
      vertex -37.5 1 5.5
      vertex -39.5 1 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.63399887084961 0.5 5.5
      vertex -37.9010009765625 -0.5 5.5
      vertex -39.534000396728516 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.9010009765625 -0.5 5.5
      vertex -37.60200119018555 0.2240000069141388 5.5
      vertex -39.534000396728516 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -82.4469985961914 -54.21500015258789 2.5
      vertex -81.97599792480469 -57 2.5
      vertex -48.018001556396484 -56.01900100708008 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -2 5.5
      vertex -39.722999572753906 -1.8980000019073486 5.5
      vertex -40.24100112915039 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 0 5.5
      vertex -40.5 -2 5.5
      vertex -40.24100112915039 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0.9831997156143188 0.1284029483795166 0.12973442673683167
    outer loop
      vertex -80.03299713134766 17.259000778198242 3.5
      vertex -79.96499633789062 17 3.240999937057495
      vertex -80 17.26799964904785 3.240999937057495
    endloop
  endfacet
  facet normal 0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -80.03299713134766 16.740999221801758 3.5
      vertex -80.03299713134766 16.740999221801758 10.5
      vertex -80.13300323486328 16.5 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.757999420166016 0.03400000184774399 5.5
      vertex -41.2760009765625 -1.8980000019073486 5.5
      vertex -40.5 0 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41 0.1340000033378601 5.5
      vertex -41.2760009765625 -1.8980000019073486 5.5
      vertex -40.757999420166016 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0.13065332174301147 -0.9914281368255615 0
    outer loop
      vertex -40.757999420166016 1.965999960899353 0
      vertex -40.5 2 0
      vertex -40.757999420166016 1.965999960899353 5.5
    endloop
  endfacet
  facet normal 0.13065332174301147 -0.9914281368255615 0
    outer loop
      vertex -40.5 2 5.5
      vertex -40.757999420166016 1.965999960899353 5.5
      vertex -40.5 2 0
    endloop
  endfacet
  facet normal 0.12201720476150513 0 0.992527961730957
    outer loop
      vertex -81.97599792480469 1.9479999542236328 2.5
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
      vertex -81.97599792480469 0.052000001072883606 2.5
    endloop
  endfacet
  facet normal 0.31745216250419617 -0.1299784779548645 0.9393240809440613
    outer loop
      vertex -83.27899932861328 -0.6439999938011169 2.634000062942505
      vertex -84.33100128173828 -0.3659999966621399 3.0280001163482666
      vertex -84.86000061035156 -1.6579999923706055 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -40.24100112915039 1.965999960899353 0
      vertex -40.24100112915039 1.965999960899353 5.5
      vertex -40.5 2 0
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -40.5 2 5.5
      vertex -40.5 2 0
      vertex -40.24100112915039 1.965999960899353 5.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -40.24100112915039 1.965999960899353 0
      vertex -40 1.8660000562667847 5.5
      vertex -40.24100112915039 1.965999960899353 5.5
    endloop
  endfacet
  facet normal 0.2731724679470062 -0.20820172131061554 0.9391639232635498
    outer loop
      vertex -83.91699981689453 -2.197999954223633 2.634000062942505
      vertex -84.86000061035156 -1.6579999923706055 3.0280001163482666
      vertex -85.70600128173828 -2.7679998874664307 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6073083281517029 -0.7944662570953369 0
    outer loop
      vertex -39.79199981689453 1.7070000171661377 0
      vertex -39.79199981689453 1.7070000171661377 5.5
      vertex -40 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 -0.6067371964454651 0
    outer loop
      vertex -39.79199981689453 1.7070000171661377 5.5
      vertex -39.79199981689453 1.7070000171661377 0
      vertex -39.63399887084961 1.5 0
    endloop
  endfacet
  facet normal -0.794902503490448 -0.6067371964454651 0
    outer loop
      vertex -39.79199981689453 1.7070000171661377 5.5
      vertex -39.63399887084961 1.5 0
      vertex -39.63399887084961 1.5 5.5
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -39.534000396728516 1.2589999437332153 0
      vertex -39.534000396728516 1.2589999437332153 5.5
      vertex -39.63399887084961 1.5 0
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -39.63399887084961 1.5 5.5
      vertex -39.63399887084961 1.5 0
      vertex -39.534000396728516 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal 0.11278249323368073 -0.10554223507642746 0.9879984259605408
    outer loop
      vertex -82.90299987792969 -2.617000102996826 2.5
      vertex -84.93499755859375 -3.5339999198913574 2.634000062942505
      vertex -85.4540023803711 -5.3429999351501465 2.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -39.534000396728516 1.2589999437332153 0
      vertex -39.5 1 5.5
      vertex -39.534000396728516 1.2589999437332153 5.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -39.534000396728516 0.7409999966621399 0
      vertex -39.63399887084961 0.5 5.5
      vertex -39.534000396728516 0.7409999966621399 5.5
    endloop
  endfacet
  facet normal 0.5761100649833679 0.44592010974884033 0.6850200295448303
    outer loop
      vertex -86.9749984741211 3.5409998893737793 4.500999927520752
      vertex -86.40299987792969 2.802000045776367 4.500999927520752
      vertex -85.71499633789062 3.2019999027252197 3.6619999408721924
    endloop
  endfacet
  facet normal -0.794902503490448 0.6067371964454651 0
    outer loop
      vertex -39.79199981689453 0.2930000126361847 0
      vertex -39.79199981689453 0.2930000126361847 5.5
      vertex -39.63399887084961 0.5 5.5
    endloop
  endfacet
  facet normal 0.2731564939022064 -0.20813870429992676 0.9391825199127197
    outer loop
      vertex -85.70600128173828 -2.7679998874664307 3.0280001163482666
      vertex -84.93499755859375 -3.5339999198913574 2.634000062942505
      vertex -83.91699981689453 -2.197999954223633 2.634000062942505
    endloop
  endfacet
  facet normal -0.6073083281517029 0.7944662570953369 0
    outer loop
      vertex -40 0.1340000033378601 5.5
      vertex -39.79199981689453 0.2930000126361847 5.5
      vertex -40 0.1340000033378601 0
    endloop
  endfacet
  facet normal -0.6073083281517029 0.7944662570953369 0
    outer loop
      vertex -39.79199981689453 0.2930000126361847 0
      vertex -40 0.1340000033378601 0
      vertex -39.79199981689453 0.2930000126361847 5.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -40.24100112915039 0.03400000184774399 0
      vertex -40.24100112915039 0.03400000184774399 5.5
      vertex -40 0.1340000033378601 0
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -40 0.1340000033378601 5.5
      vertex -40 0.1340000033378601 0
      vertex -40.24100112915039 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0.5761542916297913 0.44549983739852905 0.6852562427520752
    outer loop
      vertex -85.71499633789062 3.2019999027252197 3.6619999408721924
      vertex -86.41400146484375 4.105999946594238 3.6619999408721924
      vertex -86.9749984741211 3.5409998893737793 4.500999927520752
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -40.5 0 5.5
      vertex -40.24100112915039 0.03400000184774399 5.5
      vertex -40.5 0 0
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -40.24100112915039 0.03400000184774399 0
      vertex -40.5 0 0
      vertex -40.24100112915039 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0.099712073802948 -0.07597821205854416 0.9921112656593323
    outer loop
      vertex -82.90299987792969 -2.617000102996826 2.5
      vertex -83.91699981689453 -2.197999954223633 2.634000062942505
      vertex -84.93499755859375 -3.5339999198913574 2.634000062942505
    endloop
  endfacet
  facet normal 0.13065332174301147 0.9914281368255615 0
    outer loop
      vertex -40.757999420166016 0.03400000184774399 0
      vertex -40.757999420166016 0.03400000184774399 5.5
      vertex -40.5 0 0
    endloop
  endfacet
  facet normal 0.13065332174301147 0.9914281368255615 0
    outer loop
      vertex -40.5 0 5.5
      vertex -40.5 0 0
      vertex -40.757999420166016 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal 0.43594586849212646 0.3370864689350128 0.8344602584838867
    outer loop
      vertex -86.41400146484375 4.105999946594238 3.6619999408721924
      vertex -85.71499633789062 3.2019999027252197 3.6619999408721924
      vertex -84.87799835205078 3.688999891281128 3.0280001163482666
    endloop
  endfacet
  facet normal 0.3177083432674408 -0.1304362416267395 0.9391739964485168
    outer loop
      vertex -84.86000061035156 -1.6579999923706055 3.0280001163482666
      vertex -83.91699981689453 -2.197999954223633 2.634000062942505
      vertex -83.27899932861328 -0.6439999938011169 2.634000062942505
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -90.20600128173828 1.7070000171661377 5.5
      vertex -90.20600128173828 1.7070000171661377 0
      vertex -89.9990005493164 1.8660000562667847 5.5
    endloop
  endfacet
  facet normal 0.11214938759803772 -0.046043314039707184 0.992624044418335
    outer loop
      vertex -82.90299987792969 -2.617000102996826 2.5
      vertex -83.27899932861328 -0.6439999938011169 2.634000062942505
      vertex -83.91699981689453 -2.197999954223633 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 -84 10.5
      vertex -32 -82 10.5
      vertex -33 -84 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -34 -83.73200225830078 10.5
      vertex -33.516998291015625 -83.93199920654297 10.5
      vertex -32 -82 10.5
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -89.75800323486328 1.965999960899353 5.5
      vertex -89.9990005493164 1.8660000562667847 5.5
      vertex -89.9990005493164 1.8660000562667847 0
    endloop
  endfacet
  facet normal 0.3402978181838989 -0.04350746423006058 0.9393106698989868
    outer loop
      vertex -84.33100128173828 -0.3659999966621399 3.0280001163482666
      vertex -83.27899932861328 -0.6439999938011169 2.634000062942505
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 2 5.5
      vertex -89.75800323486328 1.965999960899353 5.5
      vertex -89.4990005493164 2 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 -65.53600311279297 10.5
      vertex -35 -82 10.5
      vertex -32 -82 10.5
    endloop
  endfacet
  facet normal 0.12515144050121307 -0.04346773773431778 0.9911850094795227
    outer loop
      vertex -83.27899932861328 -0.6439999938011169 2.634000062942505
      vertex -82.90299987792969 -2.617000102996826 2.5
      vertex -81.97599792480469 0.052000001072883606 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 2 0
      vertex -89.23999786376953 1.965999960899353 0
      vertex -89.4990005493164 2 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 -82 10.5
      vertex -34.930999755859375 -82.51799774169922 10.5
      vertex -32 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -34.41400146484375 -83.41400146484375 10.5
      vertex -32 -82 10.5
      vertex -34.731998443603516 -83 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -34.930999755859375 -82.51799774169922 10.5
      vertex -34.731998443603516 -83 10.5
      vertex -32 -82 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -34 -83.73200225830078 10.5
      vertex -32 -82 10.5
      vertex -34.41400146484375 -83.41400146484375 10.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -33 -84 10.5
      vertex -32 -82 10.5
      vertex -33.516998291015625 -83.93199920654297 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex 24.48200035095215 84.93199920654297 0
      vertex 24 84.73200225830078 0
      vertex 24.48200035095215 84.93199920654297 10.5
    endloop
  endfacet
  facet normal 0.10970041155815125 -0.014025322161614895 0.9938657283782959
    outer loop
      vertex -83.06600189208984 1.0219999551773071 2.634000062942505
      vertex -83.27899932861328 -0.6439999938011169 2.634000062942505
      vertex -81.97599792480469 0.052000001072883606 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex 25 85 0
      vertex 24.48200035095215 84.93199920654297 0
      vertex 25 85 10.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex 24.48200035095215 84.93199920654297 0
      vertex 24.48200035095215 84.93199920654297 10.5
      vertex 25 85 10.5
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex 23.51799964904785 84.93199920654297 0
      vertex 23 85 0
      vertex 23.51799964904785 84.93199920654297 10.5
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex 23 85 10.5
      vertex 23.51799964904785 84.93199920654297 10.5
      vertex 23 85 0
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex 24.48200035095215 84.93199920654297 10.5
      vertex 24 84.73200225830078 0
      vertex 24 84.73200225830078 10.5
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex 24 84.73200225830078 10.5
      vertex 24 84.73200225830078 0
      vertex 23.51799964904785 84.93199920654297 10.5
    endloop
  endfacet
  facet normal -0.8612021207809448 -0.1262229084968567 0.49233996868133545
    outer loop
      vertex -35.0359992980957 -57.69900131225586 4.61899995803833
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
      vertex -35.03200149536133 -58.483001708984375 4.425000190734863
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex 23.51799964904785 84.93199920654297 10.5
      vertex 24 84.73200225830078 0
      vertex 23.51799964904785 84.93199920654297 0
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -48.018001556396484 1 2.5
      vertex -81.97599792480469 0.052000001072883606 2.5
      vertex -47.51499938964844 -1.878000020980835 2.5
    endloop
  endfacet
  facet normal -0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -88.63300323486328 0.5 5.5
      vertex -88.79199981689453 0.2930000126361847 0
      vertex -88.79199981689453 0.2930000126361847 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 23 83 10.5
      vertex 23 83 2.5
      vertex 23 -82 2.5
    endloop
  endfacet
  facet normal 0.6737880706787109 -0.2766546905040741 0.685180127620697
    outer loop
      vertex -85.69999694824219 -1.1759999990463257 3.6619999408721924
      vertex -85.26599884033203 -0.11900000274181366 3.6619999408721924
      vertex -86.39099884033203 -0.781000018119812 4.500999927520752
    endloop
  endfacet
  facet normal -0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -88.79199981689453 0.2930000126361847 0
      vertex -88.9990005493164 0.1340000033378601 5.5
      vertex -88.79199981689453 0.2930000126361847 5.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -32 83 2.5
      vertex 23 83 2.5
      vertex -32 83 10.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 23 83 10.5
      vertex -32 83 10.5
      vertex 23 83 2.5
    endloop
  endfacet
  facet normal 0.5792171359062195 -0.44109615683555603 0.6855229139328003
    outer loop
      vertex -86.95800018310547 -1.5240000486373901 4.500999927520752
      vertex -86.39299774169922 -2.0859999656677246 3.6619999408721924
      vertex -85.69999694824219 -1.1759999990463257 3.6619999408721924
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -35 83 10.5
      vertex -92.9990005493164 83 10.5
      vertex -92.9990005493164 83 2.5
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex -35 83 10.5
      vertex -92.9990005493164 83 2.5
      vertex -35 83 2.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 83 10.5
      vertex -35 83 2.5
      vertex -35 19 2.5
    endloop
  endfacet
  facet normal 0.5791335701942444 -0.44194984436035156 0.6850435137748718
    outer loop
      vertex -85.69999694824219 -1.1759999990463257 3.6619999408721924
      vertex -86.39099884033203 -0.781000018119812 4.500999927520752
      vertex -86.95800018310547 -1.5240000486373901 4.500999927520752
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 19 2.5
      vertex -35 18 3.5
      vertex -35 83 10.5
    endloop
  endfacet
  facet normal 0.44520196318626404 -0.5759605765342712 0.6856125593185425
    outer loop
      vertex -87.697998046875 -2.0959999561309814 4.500999927520752
      vertex -86.39299774169922 -2.0859999656677246 3.6619999408721924
      vertex -86.95800018310547 -1.5240000486373901 4.500999927520752
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -32 -82 2.5
      vertex -32 83 2.5
      vertex -32 -82 10.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -32 83 10.5
      vertex -32 -82 10.5
      vertex -32 83 2.5
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -90.20600128173828 0.2930000126361847 0
      vertex -90.20600128173828 0.2930000126361847 5.5
      vertex -89.9990005493164 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex 23 -82 2.5
      vertex 23 83 2.5
      vertex -32 83 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -32 -82 2.5
      vertex 23 -82 2.5
      vertex -32 83 2.5
    endloop
  endfacet
  facet normal 0.4383305609226227 -0.3338055908679962 0.8345298767089844
    outer loop
      vertex -84.86000061035156 -1.6579999923706055 3.0280001163482666
      vertex -85.69999694824219 -1.1759999990463257 3.6619999408721924
      vertex -86.39299774169922 -2.0859999656677246 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -88.53299713134766 1.2589999437332153 5.5
      vertex -88.53299713134766 1.2589999437332153 0
      vertex -88.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0.44504186511039734 -0.576386570930481 0.685358464717865
    outer loop
      vertex -86.39299774169922 -2.0859999656677246 3.6619999408721924
      vertex -87.697998046875 -2.0959999561309814 4.500999927520752
      vertex -87.2969970703125 -2.7839999198913574 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -88.4990005493164 1 0
      vertex -88.53299713134766 0.7409999966621399 0
      vertex -88.4990005493164 1 5.5
    endloop
  endfacet
  facet normal 0.43835803866386414 -0.3340999186038971 0.8343976736068726
    outer loop
      vertex -86.39299774169922 -2.0859999656677246 3.6619999408721924
      vertex -85.70600128173828 -2.7679998874664307 3.0280001163482666
      vertex -84.86000061035156 -1.6579999923706055 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -89.9990005493164 1.8660000562667847 0
      vertex -89.9990005493164 1.8660000562667847 5.5
      vertex -90.20600128173828 1.7070000171661377 0
    endloop
  endfacet
  facet normal 0.28131869435310364 -0.6717360615730286 0.6852958798408508
    outer loop
      vertex -88.55999755859375 -2.4570000171661377 4.500999927520752
      vertex -87.2969970703125 -2.7839999198913574 3.6619999408721924
      vertex -87.697998046875 -2.0959999561309814 4.500999927520752
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 18.740999221801758 2.5339999198913574
      vertex -35 18 3.5
      vertex -35 19 2.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 18.5 2.634000062942505
      vertex -35 18 3.5
      vertex -35 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 18 10.5
      vertex -35 83 10.5
      vertex -35 18 3.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 18 3.5
      vertex -35 18.5 2.634000062942505
      vertex -35 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 18 3.5
      vertex -35 18.292999267578125 2.7929999828338623
      vertex -35 18.134000778198242 3
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 18 3.5
      vertex -35 18.134000778198242 3
      vertex -35 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal 0.3368742763996124 -0.43629562854766846 0.8343631625175476
    outer loop
      vertex -86.39299774169922 -2.0859999656677246 3.6619999408721924
      vertex -87.2969970703125 -2.7839999198913574 3.6619999408721924
      vertex -85.70600128173828 -2.7679998874664307 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.23999786376953 1.965999960899353 5.5
      vertex -89.4990005493164 2 5.5
      vertex -89.23999786376953 1.965999960899353 0
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -88.9990005493164 1.8660000562667847 0
      vertex -88.9990005493164 1.8660000562667847 5.5
      vertex -89.23999786376953 1.965999960899353 0
    endloop
  endfacet
  facet normal 0.33686017990112305 -0.4363780915737152 0.8343257308006287
    outer loop
      vertex -87.2969970703125 -2.7839999198913574 3.6619999408721924
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
      vertex -85.70600128173828 -2.7679998874664307 3.0280001163482666
    endloop
  endfacet
  facet normal 0.2809862792491913 -0.6722007393836975 0.6849765181541443
    outer loop
      vertex -88.55999755859375 -2.4570000171661377 4.500999927520752
      vertex -88.35199737548828 -3.2249999046325684 3.6619999408721924
      vertex -87.2969970703125 -2.7839999198913574 3.6619999408721924
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -35 18 3.5
      vertex -48.999000549316406 18 3.5
      vertex -35 18 10.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -88.4990005493164 1 0
      vertex -88.4990005493164 1 5.5
      vertex -88.53299713134766 1.2589999437332153 0
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -88.63300323486328 0.5 0
      vertex -88.63300323486328 0.5 5.5
      vertex -88.53299713134766 0.7409999966621399 0
    endloop
  endfacet
  facet normal 0.21258606016635895 -0.5085675716400146 0.834365725517273
    outer loop
      vertex -87.2969970703125 -2.7839999198913574 3.6619999408721924
      vertex -88.35199737548828 -3.2249999046325684 3.6619999408721924
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
    endloop
  endfacet
  facet normal 0.09488951414823532 0.7221792340278625 0.6851664781570435
    outer loop
      vertex -40.5 -53.417999267578125 4.500999927520752
      vertex -39.36600112915039 -52.770999908447266 3.6619999408721924
      vertex -40.5 -52.62200164794922 3.6619999408721924
    endloop
  endfacet
  facet normal 0.09756017476320267 -0.7218177318572998 0.6851723790168762
    outer loop
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -89.48400115966797 -3.378000020980835 3.6619999408721924
      vertex -88.35199737548828 -3.2249999046325684 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0.13015742599964142 0.9914933443069458
    outer loop
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
      vertex -35 18.740999221801758 2.5339999198913574
      vertex -35 19 2.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -89.23999786376953 0.03400000184774399 0
      vertex -89.23999786376953 0.03400000184774399 5.5
      vertex -88.9990005493164 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal 0 0.3832542896270752 0.9236428737640381
    outer loop
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
      vertex -48.999000549316406 18.5 2.634000062942505
      vertex -35 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0.13015742599964142 0.9914933443069458
    outer loop
      vertex -48.999000549316406 19 2.5
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
      vertex -35 19 2.5
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -88.53299713134766 0.7409999966621399 5.5
      vertex -88.4990005493164 1 5.5
      vertex -88.53299713134766 0.7409999966621399 0
    endloop
  endfacet
  facet normal -0.9298302531242371 0.1088915690779686 0.3515087068080902
    outer loop
      vertex -35.03099822998047 -55.316001892089844 4.35699987411499
      vertex -35.018001556396484 -52.26100158691406 3.444999933242798
      vertex -35.20399856567383 -53.70399856567383 3.4000000953674316
    endloop
  endfacet
  facet normal 0 0.3832542896270752 0.9236428737640381
    outer loop
      vertex -35 18.5 2.634000062942505
      vertex -35 18.740999221801758 2.5339999198913574
      vertex -48.999000549316406 18.5 2.634000062942505
    endloop
  endfacet
  facet normal -0.8744515180587769 0.1748047173023224 0.4525238573551178
    outer loop
      vertex -35.20399856567383 -53.70399856567383 3.4000000953674316
      vertex -35.257999420166016 -55.108001708984375 3.8380000591278076
      vertex -35.03099822998047 -55.316001892089844 4.35699987411499
    endloop
  endfacet
  facet normal 0.209854856133461 -0.2718518376350403 0.9391791820526123
    outer loop
      vertex -84.93499755859375 -3.5339999198913574 2.634000062942505
      vertex -85.70600128173828 -2.7679998874664307 3.0280001163482666
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
    endloop
  endfacet
  facet normal 0.21259057521820068 -0.5085577368736267 0.8343705534934998
    outer loop
      vertex -88.0979995727539 -4.158999919891357 3.0280001163482666
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
      vertex -88.35199737548828 -3.2249999046325684 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0.6091551780700684 0.7930510640144348
    outer loop
      vertex -48.999000549316406 18.292999267578125 2.7929999828338623
      vertex -35 18.292999267578125 2.7929999828338623
      vertex -48.999000549316406 18.5 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -35 19 2.5
      vertex -35 83 2.5
      vertex -48.999000549316406 19 2.5
    endloop
  endfacet
  facet normal 0.13232436776161194 -0.3165454864501953 0.9393025040626526
    outer loop
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
      vertex -88.0979995727539 -4.158999919891357 3.0280001163482666
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
    endloop
  endfacet
  facet normal 0 1 0
    outer loop
      vertex -48.999000549316406 18 10.5
      vertex -35 18 10.5
      vertex -48.999000549316406 18 3.5
    endloop
  endfacet
  facet normal 0 0.6091551780700684 0.7930510640144348
    outer loop
      vertex -48.999000549316406 18.5 2.634000062942505
      vertex -35 18.292999267578125 2.7929999828338623
      vertex -35 18.5 2.634000062942505
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -89.75800323486328 0.03400000184774399 5.5
      vertex -89.9990005493164 0.1340000033378601 0
      vertex -89.9990005493164 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal -0.079753577709198 0.6072147488594055 0.7905248999595642
    outer loop
      vertex -49.33399963378906 18.249000549316406 2.7929999828338623
      vertex -48.999000549316406 18.292999267578125 2.7929999828338623
      vertex -48.999000549316406 18.5 2.634000062942505
    endloop
  endfacet
  facet normal 0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -89.9990005493164 0.1340000033378601 5.5
      vertex -89.9990005493164 0.1340000033378601 0
      vertex -90.20600128173828 0.2930000126361847 0
    endloop
  endfacet
  facet normal -0.4452815651893616 0.27730700373649597 0.8513666391372681
    outer loop
      vertex -35.426998138427734 -55.834999084472656 3.928999900817871
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
      vertex -35.38600158691406 -55.14899826049805 3.7269999980926514
    endloop
  endfacet
  facet normal 0 0.7930510640144348 0.6091551780700684
    outer loop
      vertex -48.999000549316406 18.292999267578125 2.7929999828338623
      vertex -48.999000549316406 18.134000778198242 3
      vertex -35 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0.7930510640144348 0.6091551780700684
    outer loop
      vertex -48.999000549316406 18.134000778198242 3
      vertex -35 18.134000778198242 3
      vertex -35 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -89.75800323486328 1.965999960899353 5.5
      vertex -89.9990005493164 1.8660000562667847 0
      vertex -89.75800323486328 1.965999960899353 0
    endloop
  endfacet
  facet normal -0.10462330281734467 0.7886987328529358 0.6058120727539062
    outer loop
      vertex -49.292999267578125 18.094999313354492 3
      vertex -48.999000549316406 18.134000778198242 3
      vertex -48.999000549316406 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -89.4990005493164 2 0
      vertex -89.75800323486328 1.965999960899353 5.5
      vertex -89.75800323486328 1.965999960899353 0
    endloop
  endfacet
  facet normal -0.1035093292593956 0.7880824208259583 0.6068047285079956
    outer loop
      vertex -49.33399963378906 18.249000549316406 2.7929999828338623
      vertex -49.292999267578125 18.094999313354492 3
      vertex -48.999000549316406 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -88.79199981689453 1.7070000171661377 0
      vertex -88.79199981689453 1.7070000171661377 5.5
      vertex -88.9990005493164 1.8660000562667847 0
    endloop
  endfacet
  facet normal 0 0.9236428737640381 0.3832542896270752
    outer loop
      vertex -35 18.134000778198242 3
      vertex -48.999000549316406 18.134000778198242 3
      vertex -48.999000549316406 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -88.79199981689453 1.7070000171661377 5.5
      vertex -88.79199981689453 1.7070000171661377 0
      vertex -88.63300323486328 1.5 0
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -88.79199981689453 1.7070000171661377 5.5
      vertex -88.63300323486328 1.5 0
      vertex -88.63300323486328 1.5 5.5
    endloop
  endfacet
  facet normal 0 0.9236428737640381 0.3832542896270752
    outer loop
      vertex -48.999000549316406 18.034000396728516 3.240999937057495
      vertex -35 18.034000396728516 3.240999937057495
      vertex -35 18.134000778198242 3
    endloop
  endfacet
  facet normal 0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -79.9990005493164 17 10.5
      vertex -80.03299713134766 16.740999221801758 3.5
      vertex -79.9990005493164 17 3.5
    endloop
  endfacet
  facet normal -0.9080660939216614 0.12334983050823212 0.40025094151496887
    outer loop
      vertex -35.03099822998047 -55.316001892089844 4.35699987411499
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35.018001556396484 -52.26100158691406 3.444999933242798
    endloop
  endfacet
  facet normal 0.07383401691913605 -0.5462751984596252 0.8343452215194702
    outer loop
      vertex -88.35199737548828 -3.2249999046325684 3.6619999408721924
      vertex -89.48400115966797 -3.378000020980835 3.6619999408721924
      vertex -88.0979995727539 -4.158999919891357 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0.9914933443069458 0.13015742599964142
    outer loop
      vertex -35 18 3.5
      vertex -35 18.034000396728516 3.240999937057495
      vertex -48.999000549316406 18 3.5
    endloop
  endfacet
  facet normal 0.9832001328468323 0.1290687471628189 0.1290687471628189
    outer loop
      vertex -79.9990005493164 17 3.5
      vertex -79.96499633789062 17 3.240999937057495
      vertex -80.03299713134766 17.259000778198242 3.5
    endloop
  endfacet
  facet normal -0.24768595397472382 0.11863341927528381 0.961549699306488
    outer loop
      vertex -36.0359992980957 -56.430999755859375 3.8949999809265137
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
      vertex -35.46799850463867 -56.930999755859375 4.103000164031982
    endloop
  endfacet
  facet normal 0 0.9914933443069458 0.13015742599964142
    outer loop
      vertex -48.999000549316406 18.034000396728516 3.240999937057495
      vertex -48.999000549316406 18 3.5
      vertex -35 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal 0.07385952025651932 -0.5462444424629211 0.8343631029129028
    outer loop
      vertex -88.0979995727539 -4.158999919891357 3.0280001163482666
      vertex -89.48400115966797 -3.378000020980835 3.6619999408721924
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal -0.11975689232349396 0.916995644569397 0.3804961144924164
    outer loop
      vertex -48.999000549316406 18.134000778198242 3
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
      vertex -48.999000549316406 18.034000396728516 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 83 2.5
      vertex -48.999000549316406 19 2.5
      vertex -35 83 2.5
    endloop
  endfacet
  facet normal -0.6171607375144958 0.08139388263225555 0.7826159000396729
    outer loop
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
      vertex -35.45500183105469 -56.4010009765625 4.053999900817871
      vertex -35.31399917602539 -56.928001403808594 4.21999979019165
    endloop
  endfacet
  facet normal -0.6025662422180176 -0.07067236304283142 0.7949334979057312
    outer loop
      vertex -35.45500183105469 -57.59299850463867 4.053999900817871
      vertex -35.31399917602539 -56.928001403808594 4.21999979019165
      vertex -35.46799850463867 -56.930999755859375 4.103000164031982
    endloop
  endfacet
  facet normal -0.6176230311393738 0.1986152082681656 0.760982096195221
    outer loop
      vertex -35.426998138427734 -55.834999084472656 3.928999900817871
      vertex -35.45500183105469 -56.4010009765625 4.053999900817871
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -88.53299713134766 1.2589999437332153 5.5
      vertex -88.63300323486328 1.5 5.5
      vertex -88.53299713134766 1.2589999437332153 0
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -88.63300323486328 1.5 0
      vertex -88.53299713134766 1.2589999437332153 0
      vertex -88.63300323486328 1.5 5.5
    endloop
  endfacet
  facet normal -0.8562787175178528 0.06075218319892883 0.5129287838935852
    outer loop
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
      vertex -35.31399917602539 -56.928001403808594 4.21999979019165
      vertex -35.0369987487793 -56.91600036621094 4.681000232696533
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -49.96500015258789 16.740999221801758 10.5
      vertex -49.8650016784668 16.5 3.5
      vertex -49.8650016784668 16.5 10.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -88.53299713134766 0.7409999966621399 5.5
      vertex -88.53299713134766 0.7409999966621399 0
      vertex -88.63300323486328 0.5 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 -0.6067371964454651 0
    outer loop
      vertex -49.8650016784668 16.5 3.5
      vertex -49.707000732421875 16.292999267578125 10.5
      vertex -49.8650016784668 16.5 10.5
    endloop
  endfacet
  facet normal -0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -88.63300323486328 0.5 5.5
      vertex -88.63300323486328 0.5 0
      vertex -88.79199981689453 0.2930000126361847 0
    endloop
  endfacet
  facet normal 0.045970600098371506 -0.33998578786849976 0.9393063187599182
    outer loop
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
      vertex -88.0979995727539 -4.158999919891357 3.0280001163482666
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -48.999000549316406 18 10.5
      vertex -49.257999420166016 17.965999603271484 3.5
      vertex -49.257999420166016 17.965999603271484 10.5
    endloop
  endfacet
  facet normal -0.6091551780700684 0.7930510640144348 0
    outer loop
      vertex -88.9990005493164 0.1340000033378601 0
      vertex -88.9990005493164 0.1340000033378601 5.5
      vertex -88.79199981689453 0.2930000126361847 0
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -49.257999420166016 17.965999603271484 3.5
      vertex -49.499000549316406 17.865999221801758 10.5
      vertex -49.257999420166016 17.965999603271484 10.5
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -88.9990005493164 0.1340000033378601 5.5
      vertex -88.9990005493164 0.1340000033378601 0
      vertex -89.23999786376953 0.03400000184774399 0
    endloop
  endfacet
  facet normal -0.8609719276428223 0.05182207003235817 0.5060057044029236
    outer loop
      vertex -35.0359992980957 -56.29399871826172 4.61899995803833
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
      vertex -35.0369987487793 -56.91600036621094 4.681000232696533
    endloop
  endfacet
  facet normal -0.8555865287780762 -0.04871673882007599 0.5153623819351196
    outer loop
      vertex -35.31399917602539 -56.928001403808594 4.21999979019165
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
      vertex -35.0369987487793 -56.91600036621094 4.681000232696533
    endloop
  endfacet
  facet normal 0.007960772141814232 -0.12049423903226852 0.9926820993423462
    outer loop
      vertex -89.947998046875 -6.568999767303467 2.5
      vertex -88.05599975585938 -6.443999767303467 2.5
      vertex -89.47799682617188 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -80.13300323486328 16.5 10.5
      vertex -80.13300323486328 16.5 3.5
      vertex -80.03299713134766 16.740999221801758 3.5
    endloop
  endfacet
  facet normal -0.860485851764679 -0.041307661682367325 0.5077970027923584
    outer loop
      vertex -35.0369987487793 -56.91600036621094 4.681000232696533
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
      vertex -35.0359992980957 -57.69900131225586 4.61899995803833
    endloop
  endfacet
  facet normal 0.2098587304353714 -0.2715698480606079 0.9392598867416382
    outer loop
      vertex -84.93499755859375 -3.5339999198913574 2.634000062942505
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
      vertex -86.26399993896484 -4.560999870300293 2.634000062942505
    endloop
  endfacet
  facet normal 0.9176308512687683 0.12214198708534241 0.37819963693618774
    outer loop
      vertex -79.86499786376953 17 3
      vertex -79.90399932861328 17.292999267578125 3
      vertex -80 17.26799964904785 3.240999937057495
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -49.999000549316406 17 3.5
      vertex -49.999000549316406 17 10.5
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -49.999000549316406 17 10.5
      vertex -49.96500015258789 17.259000778198242 10.5
    endloop
  endfacet
  facet normal 0.13245099782943726 -0.31661513447761536 0.9392611980438232
    outer loop
      vertex -86.81099700927734 -3.621000051498413 3.0280001163482666
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
      vertex -86.26399993896484 -4.560999870300293 2.634000062942505
    endloop
  endfacet
  facet normal -0.8610098958015442 0.13570939004421234 0.49014782905578613
    outer loop
      vertex -35.0359992980957 -56.29399871826172 4.61899995803833
      vertex -35.03099822998047 -55.316001892089844 4.35699987411499
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -49.999000549316406 17 3.5
      vertex -49.96500015258789 16.740999221801758 3.5
      vertex -49.999000549316406 17 10.5
    endloop
  endfacet
  facet normal -0.6780441403388977 0.20913371443748474 0.7046411633491516
    outer loop
      vertex -35.257999420166016 -55.108001708984375 3.8380000591278076
      vertex -35.38600158691406 -55.14899826049805 3.7269999980926514
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -49.96500015258789 16.740999221801758 10.5
      vertex -49.96500015258789 16.740999221801758 3.5
      vertex -49.8650016784668 16.5 3.5
    endloop
  endfacet
  facet normal -0.8826327919960022 0.1490854173898697 0.44579464197158813
    outer loop
      vertex -35.03099822998047 -55.316001892089844 4.35699987411499
      vertex -35.257999420166016 -55.108001708984375 3.8380000591278076
      vertex -35.30500030517578 -56.37900161743164 4.170000076293945
    endloop
  endfacet
  facet normal 0.04594893753528595 -0.34002211689949036 0.9392942190170288
    outer loop
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
      vertex -89.47799682617188 -5.434000015258789 2.634000062942505
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
    endloop
  endfacet
  facet normal 0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -89.75800323486328 0.03400000184774399 0
      vertex -89.75800323486328 0.03400000184774399 5.5
      vertex -89.4990005493164 0 0
    endloop
  endfacet
  facet normal -0.9908272624015808 -0.011923979967832565 0.1346072405576706
    outer loop
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35.0369987487793 -56.91600036621094 4.681000232696533
      vertex -35.0359992980957 -57.69900131225586 4.61899995803833
    endloop
  endfacet
  facet normal 0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -89.75800323486328 0.03400000184774399 5.5
      vertex -89.75800323486328 0.03400000184774399 0
      vertex -89.9990005493164 0.1340000033378601 0
    endloop
  endfacet
  facet normal -0.07959090173244476 0.6070756912231445 0.7906481027603149
    outer loop
      vertex -49.38800048828125 18.448999404907227 2.634000062942505
      vertex -49.33399963378906 18.249000549316406 2.7929999828338623
      vertex -48.999000549316406 18.5 2.634000062942505
    endloop
  endfacet
  facet normal -0.23486930131912231 0.5652521252632141 0.7907758951187134
    outer loop
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
      vertex -49.33399963378906 18.249000549316406 2.7929999828338623
      vertex -49.38800048828125 18.448999404907227 2.634000062942505
    endloop
  endfacet
  facet normal -0.9663116335868835 -0.06645756959915161 0.2486468404531479
    outer loop
      vertex -35.0359992980957 -57.69900131225586 4.61899995803833
      vertex -35.03200149536133 -58.483001708984375 4.425000190734863
      vertex -35 -56.999000549316406 4.946000099182129
    endloop
  endfacet
  facet normal 0.3819020092487335 0.9242027997970581 0
    outer loop
      vertex -40.757999420166016 0.03400000184774399 0
      vertex -41 0.1340000033378601 0
      vertex -40.757999420166016 0.03400000184774399 5.5
    endloop
  endfacet
  facet normal -0.2811545133590698 0.6719656586647034 0.6851381659507751
    outer loop
      vertex -90.43800354003906 4.456999778747559 4.500999927520752
      vertex -90.64700317382812 5.224999904632568 3.6619999408721924
      vertex -91.70099639892578 4.783999919891357 3.6619999408721924
    endloop
  endfacet
  facet normal -0.958304762840271 0.07850386947393417 0.2747528851032257
    outer loop
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35.03099822998047 -55.316001892089844 4.35699987411499
      vertex -35.0359992980957 -56.29399871826172 4.61899995803833
    endloop
  endfacet
  facet normal -0.2092801183462143 -0.5097748041152954 0.8344647884368896
    outer loop
      vertex -90.61799621582031 -61.233001708984375 3.6619999408721924
      vertex -92.15699768066406 -61.638999938964844 3.0280001163482666
      vertex -90.86599731445312 -62.16899871826172 3.0280001163482666
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -39.534000396728516 0.7409999966621399 0
      vertex -39.534000396728516 0.7409999966621399 5.5
      vertex -39.5 1 5.5
    endloop
  endfacet
  facet normal -0.9895762205123901 0.015858355909585953 0.143134206533432
    outer loop
      vertex -35.0369987487793 -56.91600036621094 4.681000232696533
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35.0359992980957 -56.29399871826172 4.61899995803833
    endloop
  endfacet
  facet normal -0.44145017862319946 -0.5792573690414429 0.6852610111236572
    outer loop
      vertex -91.27999877929688 -60.108001708984375 4.500999927520752
      vertex -92.02400207519531 -59.54100036621094 4.500999927520752
      vertex -92.58499908447266 -60.10599899291992 3.6619999408721924
    endloop
  endfacet
  facet normal -0.11578762531280518 0.8586810231208801 0.4992595613002777
    outer loop
      vertex -90.2760009765625 3.8980000019073486 5.5
      vertex -89.51100158691406 4.581999778747559 4.500999927520752
      vertex -90.43800354003906 4.456999778747559 4.500999927520752
    endloop
  endfacet
  facet normal -0.3420412838459015 -0.3047020137310028 0.8889119625091553
    outer loop
      vertex -35.03200149536133 -58.483001708984375 4.425000190734863
      vertex -35.0260009765625 -59.68000030517578 4.017000198364258
      vertex -35 -56.999000549316406 4.946000099182129
    endloop
  endfacet
  facet normal -0.4415043294429779 -0.5791160464286804 0.6853455305099487
    outer loop
      vertex -92.58499908447266 -60.10599899291992 3.6619999408721924
      vertex -91.6760025024414 -60.79899978637695 3.6619999408721924
      vertex -91.27999877929688 -60.108001708984375 4.500999927520752
    endloop
  endfacet
  facet normal -0.3316732943058014 0.7993326187133789 0.5010590553283691
    outer loop
      vertex -90.43800354003906 4.456999778747559 4.500999927520752
      vertex -90.9990005493164 3.5980000495910645 5.5
      vertex -90.2760009765625 3.8980000019073486 5.5
    endloop
  endfacet
  facet normal -0.4448806345462799 0.576815128326416 0.6851025819778442
    outer loop
      vertex -92.60600280761719 4.085999965667725 3.6619999408721924
      vertex -91.3010025024414 4.0960001945495605 4.500999927520752
      vertex -91.70099639892578 4.783999919891357 3.6619999408721924
    endloop
  endfacet
  facet normal -0.28111302852630615 0.6720236539840698 0.6850982904434204
    outer loop
      vertex -90.43800354003906 4.456999778747559 4.500999927520752
      vertex -91.70099639892578 4.783999919891357 3.6619999408721924
      vertex -91.3010025024414 4.0960001945495605 4.500999927520752
    endloop
  endfacet
  facet normal -0.3343205153942108 0.7992205023765564 0.4994760751724243
    outer loop
      vertex -90.43800354003906 4.456999778747559 4.500999927520752
      vertex -91.3010025024414 4.0960001945495605 4.500999927520752
      vertex -90.9990005493164 3.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.014968560077250004 -0.11076734215021133 0.9937336444854736
    outer loop
      vertex -88.05599975585938 -6.443999767303467 2.5
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
      vertex -89.47799682617188 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0.04959798976778984 -0.11856062710285187 0.9917073249816895
    outer loop
      vertex -85.4540023803711 -5.3429999351501465 2.5
      vertex -86.26399993896484 -4.560999870300293 2.634000062942505
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
    endloop
  endfacet
  facet normal 0.0730210468173027 -0.09449364244937897 0.9928438067436218
    outer loop
      vertex -84.93499755859375 -3.5339999198913574 2.634000062942505
      vertex -86.26399993896484 -4.560999870300293 2.634000062942505
      vertex -85.4540023803711 -5.3429999351501465 2.5
    endloop
  endfacet
  facet normal 0.6867461204528809 -0.5275006294250488 0.5001228451728821
    outer loop
      vertex -37.39699935913086 -58.79100036621094 4.500999927520752
      vertex -37.9010009765625 -58.5 5.5
      vertex -38.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0.04967215284705162 -0.11739049851894379 0.9918428063392639
    outer loop
      vertex -85.4540023803711 -5.3429999351501465 2.5
      vertex -87.81300354003906 -5.209000110626221 2.634000062942505
      vertex -88.05599975585938 -6.443999767303467 2.5
    endloop
  endfacet
  facet normal 0.9832001328468323 -0.1290687471628189 0.1290687471628189
    outer loop
      vertex -80.03299713134766 16.740999221801758 3.5
      vertex -79.96499633789062 17 3.240999937057495
      vertex -79.9990005493164 17 3.5
    endloop
  endfacet
  facet normal 0.68311607837677 -0.28305041790008545 0.6732271909713745
    outer loop
      vertex -37.39699935913086 -58.79100036621094 4.500999927520752
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
    endloop
  endfacet
  facet normal 0.7999835014343262 -0.331474632024765 0.5001509785652161
    outer loop
      vertex -37.39699935913086 -58.79100036621094 4.500999927520752
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
      vertex -37.9010009765625 -58.5 5.5
    endloop
  endfacet
  facet normal 0.8000219464302063 -0.33039578795433044 0.5008029341697693
    outer loop
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
      vertex -37.60200119018555 -57.7760009765625 5.5
      vertex -37.9010009765625 -58.5 5.5
    endloop
  endfacet
  facet normal 0.916995644569397 0.11975689232349396 0.3804961144924164
    outer loop
      vertex -80 17.26799964904785 3.240999937057495
      vertex -79.96499633789062 17 3.240999937057495
      vertex -79.86499786376953 17 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.60200119018555 -57.7760009765625 5.5
      vertex -39.534000396728516 -57.25899887084961 5.5
      vertex -37.9010009765625 -58.5 5.5
    endloop
  endfacet
  facet normal 0.9831997156143188 -0.1284029483795166 0.12973442673683167
    outer loop
      vertex -79.96499633789062 17 3.240999937057495
      vertex -80.03299713134766 16.740999221801758 3.5
      vertex -80 16.73200035095215 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -85.4540023803711 -5.3429999351501465 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.947998046875 -6.568999767303467 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -88.05599975585938 -6.443999767303467 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.05599975585938 -6.443999767303467 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -85.4540023803711 -5.3429999351501465 2.5
    endloop
  endfacet
  facet normal 0.9158178567886353 -0.38000741600990295 0.12989211082458496
    outer loop
      vertex -80 16.73200035095215 3.240999937057495
      vertex -80.03299713134766 16.740999221801758 3.5
      vertex -80.13300323486328 16.5 3.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.79199981689453 -57.707000732421875 5.5
      vertex -37.9010009765625 -58.5 5.5
      vertex -39.63399887084961 -57.5 5.5
    endloop
  endfacet
  facet normal -0.9914933443069458 0 0.13015742599964142
    outer loop
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
      vertex -35 14 3.5
      vertex -35.034000396728516 14 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -85.4540023803711 -5.3429999351501465 2.5
      vertex -47.51499938964844 -1.878000020980835 2.5
      vertex -82.90299987792969 -2.617000102996826 2.5
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -80.13300323486328 16.5 10.5
      vertex -80.29199981689453 16.292999267578125 10.5
      vertex -80.29199981689453 16.292999267578125 3.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40 -57.86600112915039 5.5
      vertex -39 -59.597999572753906 5.5
      vertex -39.79199981689453 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal -0.9236428737640381 0 0.3832542896270752
    outer loop
      vertex -35.13399887084961 14 3
      vertex -35.13399887084961 7.103000164031982 3
      vertex -35.034000396728516 14 3.240999937057495
    endloop
  endfacet
  facet normal -0.9236428737640381 0 0.3832542896270752
    outer loop
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
      vertex -35.034000396728516 14 3.240999937057495
      vertex -35.13399887084961 7.103000164031982 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.24100112915039 -57.965999603271484 5.5
      vertex -39 -59.597999572753906 5.5
      vertex -40 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 0 0.6067371964454651
    outer loop
      vertex -35.13399887084961 14 3
      vertex -35.29199981689453 14 2.7929999828338623
      vertex -35.13399887084961 7.103000164031982 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.9010009765625 -58.5 5.5
      vertex -39.79199981689453 -57.707000732421875 5.5
      vertex -38.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.757999420166016 -57.965999603271484 5.5
      vertex -41.2760009765625 -59.89799880981445 5.5
      vertex -40.5 -58 5.5
    endloop
  endfacet
  facet normal -0.6073083281517029 0 0.7944662570953369
    outer loop
      vertex -35.5 7.103000164031982 2.634000062942505
      vertex -35.29199981689453 7.103000164031982 2.7929999828338623
      vertex -35.5 14 2.634000062942505
    endloop
  endfacet
  facet normal -0.7992205023765564 -0.3343205153942108 0.4994760751724243
    outer loop
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
      vertex -92.09700012207031 -0.5 5.5
      vertex -92.95600128173828 0.061000000685453415 4.500999927520752
    endloop
  endfacet
  facet normal -0.3832542896270752 0 0.9236428737640381
    outer loop
      vertex -35.5 14 2.634000062942505
      vertex -35.74100112915039 7.103000164031982 2.5339999198913574
      vertex -35.5 7.103000164031982 2.634000062942505
    endloop
  endfacet
  facet normal -0.6861675977706909 -0.5270562767982483 0.5013838410377502
    outer loop
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
      vertex -91.62000274658203 -1.121000051498413 5.5
      vertex -92.09700012207031 -0.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42 -59.597999572753906 5.5
      vertex -41.2760009765625 -59.89799880981445 5.5
      vertex -41 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -60 5.5
      vertex -40.5 -58 5.5
      vertex -41.2760009765625 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -58 5.5
      vertex -40.5 -60 5.5
      vertex -40.24100112915039 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41 -57.86600112915039 5.5
      vertex -41.2760009765625 -59.89799880981445 5.5
      vertex -40.757999420166016 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -80.13300323486328 16.5 3.5
      vertex -80.13300323486328 16.5 10.5
      vertex -80.29199981689453 16.292999267578125 3.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0 0.9914933443069458
    outer loop
      vertex -35.74100112915039 14 2.5339999198913574
      vertex -36 7.103000164031982 2.5
      vertex -35.74100112915039 7.103000164031982 2.5339999198913574
    endloop
  endfacet
  facet normal -0.08820967376232147 -0.0015979581512510777 0.996100664138794
    outer loop
      vertex -36 7.103000164031982 2.5
      vertex -35.74100112915039 14 2.5339999198913574
      vertex -36.13399887084961 14.5 2.5
    endloop
  endfacet
  facet normal 0.7864401340484619 -0.6040772199630737 0.1288510262966156
    outer loop
      vertex -80.13300323486328 16.5 3.5
      vertex -80.29199981689453 16.292999267578125 3.5
      vertex -80.26799774169922 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.46499633789062 0.7409999966621399 5.5
      vertex -92.39700317382812 0.2240000069141388 5.5
      vertex -92.09700012207031 -0.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.20600128173828 0.2930000126361847 5.5
      vertex -91.62000274658203 -1.121000051498413 5.5
      vertex -89.9990005493164 0.1340000033378601 5.5
    endloop
  endfacet
  facet normal 0.8560248017311096 -0.35303211212158203 0.3776107132434845
    outer loop
      vertex -80 16.73200035095215 3.240999937057495
      vertex -80.01699829101562 16.433000564575195 3
      vertex -79.90399932861328 16.707000732421875 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.71699905395508 8.053000450134277 2.5
      vertex -36 7.103000164031982 2.5
      vertex -36.13399887084961 14.5 2.5
    endloop
  endfacet
  facet normal 0.9152089953422546 -0.3822559714317322 0.12756529450416565
    outer loop
      vertex -80.13300323486328 16.5 3.5
      vertex -80.10399627685547 16.482999801635742 3.240999937057495
      vertex -80 16.73200035095215 3.240999937057495
    endloop
  endfacet
  facet normal -0.11298856884241104 -0.8585278987884521 0.5001633763313293
    outer loop
      vertex -41.426998138427734 -60.459999084472656 4.500999927520752
      vertex -40.5 -60.582000732421875 4.500999927520752
      vertex -40.5 -60 5.5
    endloop
  endfacet
  facet normal -0.6717711687088013 -0.28100740909576416 0.6853892207145691
    outer loop
      vertex -92.95600128173828 0.061000000685453415 4.500999927520752
      vertex -93.7249984741211 -0.1469999998807907 3.6619999408721924
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
    endloop
  endfacet
  facet normal -0.577445387840271 -0.2331727147102356 -0.7824240326881409
    outer loop
      vertex -35 5.539000034332275 3.681999921798706
      vertex -35 4.0289998054504395 4.131999969482422
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
    endloop
  endfacet
  facet normal -0.9988046884536743 0.0030919320415705442 0.048781100660562515
    outer loop
      vertex -35 14 3.5
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
      vertex -35 4.0289998054504395 4.131999969482422
    endloop
  endfacet
  facet normal 0.8528528213500977 -0.3562116324901581 0.38177916407585144
    outer loop
      vertex -80 16.73200035095215 3.240999937057495
      vertex -80.10399627685547 16.482999801635742 3.240999937057495
      vertex -80.01699829101562 16.433000564575195 3
    endloop
  endfacet
  facet normal 0.7872229814529419 -0.6032924056053162 0.12774300575256348
    outer loop
      vertex -80.10399627685547 16.482999801635742 3.240999937057495
      vertex -80.13300323486328 16.5 3.5
      vertex -80.26799774169922 16.268999099731445 3.240999937057495
    endloop
  endfacet
  facet normal 0.7336912155151367 -0.5622680187225342 0.3815126121044159
    outer loop
      vertex -80.10399627685547 16.482999801635742 3.240999937057495
      vertex -80.26799774169922 16.268999099731445 3.240999937057495
      vertex -80.01699829101562 16.433000564575195 3
    endloop
  endfacet
  facet normal -0.6853792071342468 -0.5295690298080444 0.49981197714805603
    outer loop
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
      vertex -92.02400207519531 -1.5410000085830688 4.500999927520752
      vertex -91.62000274658203 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.12211856991052628 0.9174548983573914 0.3786338269710541
    outer loop
      vertex -80.9990005493164 18.134000778198242 3
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
      vertex -80.70600128173828 18.094999313354492 3
    endloop
  endfacet
  facet normal 0.7373291254043579 0.09975915402173996 0.668127179145813
    outer loop
      vertex -36.742000579833984 -56.34600067138672 4.214000225067139
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
      vertex -36.76300048828125 -56.67300033569336 4.285999774932861
    endloop
  endfacet
  facet normal 0.5359854698181152 0.07265324890613556 0.8410951495170593
    outer loop
      vertex -36.76300048828125 -56.67300033569336 4.285999774932861
      vertex -36.249000549316406 -56.933998107910156 3.9809999465942383
      vertex -36.22200012207031 -56.426998138427734 3.9200000762939453
    endloop
  endfacet
  facet normal 0.3525885343551636 0.8557974100112915 0.37853944301605225
    outer loop
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
      vertex -80.48200225830078 17.895999908447266 3.240999937057495
      vertex -80.43199920654297 17.98200035095215 3
    endloop
  endfacet
  facet normal -0.5269930958747864 -0.6860854029655457 0.5015626549720764
    outer loop
      vertex -92.02400207519531 -1.5410000085830688 4.500999927520752
      vertex -90.9990005493164 -1.5980000495910645 5.5
      vertex -91.62000274658203 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.7565125226974487 0.1551235318183899 0.6353152990341187
    outer loop
      vertex -36.742000579833984 -56.34600067138672 4.214000225067139
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
    endloop
  endfacet
  facet normal 0.35283663868904114 0.8555507659912109 0.37886565923690796
    outer loop
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
      vertex -80.43199920654297 17.98200035095215 3
      vertex -80.70600128173828 18.094999313354492 3
    endloop
  endfacet
  facet normal 0.43794217705726624 0.2739837169647217 0.856235682964325
    outer loop
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
      vertex -36.742000579833984 -56.34600067138672 4.214000225067139
      vertex -36.1609992980957 -55.88399887084961 3.7690000534057617
    endloop
  endfacet
  facet normal 0.5051749348640442 0.17807641625404358 0.8444448113441467
    outer loop
      vertex -36.22200012207031 -56.426998138427734 3.9200000762939453
      vertex -36.1609992980957 -55.88399887084961 3.7690000534057617
      vertex -36.742000579833984 -56.34600067138672 4.214000225067139
    endloop
  endfacet
  facet normal -0.5251178741455078 -0.6890435814857483 0.4994698464870453
    outer loop
      vertex -92.02400207519531 -1.5410000085830688 4.500999927520752
      vertex -91.27999877929688 -2.1080000400543213 4.500999927520752
      vertex -90.9990005493164 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal 0.5043916702270508 0.15465636551380157 0.8495119214057922
    outer loop
      vertex -36.742000579833984 -56.34600067138672 4.214000225067139
      vertex -36.76300048828125 -56.67300033569336 4.285999774932861
      vertex -36.22200012207031 -56.426998138427734 3.9200000762939453
    endloop
  endfacet
  facet normal 0.7369192242622375 -0.09698397666215897 0.6689873933792114
    outer loop
      vertex -36.762001037597656 -57.32600021362305 4.2829999923706055
      vertex -36.91699981689453 -57 4.500999927520752
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
    endloop
  endfacet
  facet normal -0.3316230773925781 -0.7992116212844849 0.5012853145599365
    outer loop
      vertex -91.27999877929688 -2.1080000400543213 4.500999927520752
      vertex -90.2760009765625 -1.8980000019073486 5.5
      vertex -90.9990005493164 -1.5980000495910645 5.5
    endloop
  endfacet
  facet normal -0.2451765388250351 0.5900582075119019 0.769233226776123
    outer loop
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
      vertex -49.749000549316406 18.298999786376953 2.634000062942505
      vertex -49.38800048828125 18.448999404907227 2.634000062942505
    endloop
  endfacet
  facet normal 0.5091115236282349 -0.0031745368614792824 0.8606947064399719
    outer loop
      vertex -36.762001037597656 -57.32600021362305 4.2829999923706055
      vertex -36.249000549316406 -56.933998107910156 3.9809999465942383
      vertex -36.76300048828125 -56.67300033569336 4.285999774932861
    endloop
  endfacet
  facet normal 0.10381203889846802 0.7880277633666992 0.6068239808082581
    outer loop
      vertex -80.70600128173828 18.094999313354492 3
      vertex -80.66500091552734 18.249000549316406 2.7929999828338623
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0.7376112937927246 -0.09761299192905426 0.6681326627731323
    outer loop
      vertex -36.762001037597656 -57.32600021362305 4.2829999923706055
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
      vertex -36.742000579833984 -57.65399932861328 4.2129998207092285
    endloop
  endfacet
  facet normal -0.12958140671253204 0.11080342531204224 0.9853584170341492
    outer loop
      vertex -50.04999923706055 18.3700008392334 2.5339999198913574
      vertex -49.999000549316406 18.73200035095215 2.5
      vertex -50.83100128173828 17.759000778198242 2.5
    endloop
  endfacet
  facet normal 0.538995623588562 -0.05798742547631264 0.8403101563453674
    outer loop
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
      vertex -36.249000549316406 -56.933998107910156 3.9809999465942383
      vertex -36.762001037597656 -57.32600021362305 4.2829999923706055
    endloop
  endfacet
  facet normal 0.10497645288705826 0.788669228553772 0.6057894229888916
    outer loop
      vertex -80.9990005493164 18.134000778198242 3
      vertex -80.70600128173828 18.094999313354492 3
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal -0.3289930522441864 -0.801630973815918 0.49915066361427307
    outer loop
      vertex -91.27999877929688 -2.1080000400543213 4.500999927520752
      vertex -90.41500091552734 -2.4630000591278076 4.500999927520752
      vertex -90.2760009765625 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal -0.05018339678645134 0.38277140259742737 0.9224790930747986
    outer loop
      vertex -49.38800048828125 18.448999404907227 2.634000062942505
      vertex -48.999000549316406 18.5 2.634000062942505
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal -0.1126457080245018 -0.8580952286720276 0.5009825229644775
    outer loop
      vertex -90.41500091552734 -2.4630000591278076 4.500999927520752
      vertex -89.4990005493164 -2 5.5
      vertex -90.2760009765625 -1.8980000019073486 5.5
    endloop
  endfacet
  facet normal -0.11019986122846603 -0.8593736886978149 0.4993324279785156
    outer loop
      vertex -90.41500091552734 -2.4630000591278076 4.500999927520752
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -89.4990005493164 -2 5.5
    endloop
  endfacet
  facet normal -0.0346994549036026 0.0982995331287384 0.9945517182350159
    outer loop
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
      vertex -49.999000549316406 18.73200035095215 2.5
      vertex -50.04999923706055 18.3700008392334 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.9990005493164 -1.5980000495910645 5.5
      vertex -89.9990005493164 0.1340000033378601 5.5
      vertex -91.62000274658203 -1.121000051498413 5.5
    endloop
  endfacet
  facet normal 0.7999835014343262 0.331474632024765 0.5001509785652161
    outer loop
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
      vertex -37.39699935913086 -55.20899963378906 4.500999927520752
      vertex -37.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal -0.03486098721623421 0.13007831573486328 0.9908906817436218
    outer loop
      vertex -48.999000549316406 19 2.5
      vertex -49.999000549316406 18.73200035095215 2.5
      vertex -48.999000549316406 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -50.83100128173828 17.759000778198242 2.5
      vertex -79.03299713134766 17.259000778198242 2.5
      vertex -50.83100128173828 16.240999221801758 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 83 2.5
      vertex -50.83100128173828 17.759000778198242 2.5
      vertex -49.999000549316406 18.73200035095215 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -49.999000549316406 18.73200035095215 2.5
      vertex -48.999000549316406 19 2.5
      vertex -92.9990005493164 83 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -48.999000549316406 18 10.5
      vertex -48.999000549316406 18 3.5
      vertex -49.257999420166016 17.965999603271484 3.5
    endloop
  endfacet
  facet normal -0.1290687471628189 0.9832001328468323 0.1290687471628189
    outer loop
      vertex -48.999000549316406 18.034000396728516 3.240999937057495
      vertex -49.257999420166016 17.965999603271484 3.5
      vertex -48.999000549316406 18 3.5
    endloop
  endfacet
  facet normal 0.30327823758125305 0.735382616519928 0.6059989333152771
    outer loop
      vertex -80.70600128173828 18.094999313354492 3
      vertex -80.43199920654297 17.98200035095215 3
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -49.499000549316406 17.865999221801758 3.5
      vertex -49.499000549316406 17.865999221801758 10.5
      vertex -49.257999420166016 17.965999603271484 3.5
    endloop
  endfacet
  facet normal 0.4435596466064453 0.577640950679779 0.6852633357048035
    outer loop
      vertex -38.70800018310547 -53.89799880981445 4.500999927520752
      vertex -37.96699905395508 -54.46699905395508 4.500999927520752
      vertex -37.40399932861328 -53.90399932861328 3.6619999408721924
    endloop
  endfacet
  facet normal 0.30373790860176086 0.7346219420433044 0.6066909432411194
    outer loop
      vertex -80.66500091552734 18.249000549316406 2.7929999828338623
      vertex -80.70600128173828 18.094999313354492 3
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6717368960380554 -0.28079238533973694 0.6855109333992004
    outer loop
      vertex -93.28399658203125 -1.2020000219345093 3.6619999408721924
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
      vertex -93.7249984741211 -0.1469999998807907 3.6619999408721924
    endloop
  endfacet
  facet normal -0.1284029483795166 0.9831997156143188 0.12973442673683167
    outer loop
      vertex -48.999000549316406 18.034000396728516 3.240999937057495
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
      vertex -49.257999420166016 17.965999603271484 3.5
    endloop
  endfacet
  facet normal 0.23406155407428741 0.5661023259162903 0.7904070615768433
    outer loop
      vertex -80.66500091552734 18.249000549316406 2.7929999828338623
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
      vertex -80.2490005493164 18.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal -0.6073083281517029 0.7944662570953369 0
    outer loop
      vertex -49.707000732421875 17.707000732421875 10.5
      vertex -49.499000549316406 17.865999221801758 10.5
      vertex -49.707000732421875 17.707000732421875 3.5
    endloop
  endfacet
  facet normal 0.6867327690124512 0.5275440216064453 0.5000954270362854
    outer loop
      vertex -37.96699905395508 -54.46699905395508 4.500999927520752
      vertex -38.37799835205078 -54.87900161743164 5.5
      vertex -37.39699935913086 -55.20899963378906 4.500999927520752
    endloop
  endfacet
  facet normal -0.38000741600990295 0.9158178567886353 0.12989211082458496
    outer loop
      vertex -49.499000549316406 17.865999221801758 3.5
      vertex -49.257999420166016 17.965999603271484 3.5
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
    endloop
  endfacet
  facet normal 0.37286287546157837 0.48566174507141113 0.790636420249939
    outer loop
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
      vertex -79.93900299072266 18.06100082397461 2.634000062942505
      vertex -80.2490005493164 18.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal 0.5272573828697205 0.6866392493247986 0.5005258917808533
    outer loop
      vertex -37.96699905395508 -54.46699905395508 4.500999927520752
      vertex -38.70800018310547 -53.89799880981445 4.500999927520752
      vertex -39 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.27158287167549133 -0.20983712375164032 0.9392609596252441
    outer loop
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
    endloop
  endfacet
  facet normal -0.12171142548322678 0.9175169467926025 0.378614604473114
    outer loop
      vertex -49.292999267578125 18.094999313354492 3
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
      vertex -48.999000549316406 18.134000778198242 3
    endloop
  endfacet
  facet normal 0.3318139612674713 0.7996716499328613 0.5004246234893799
    outer loop
      vertex -38.70800018310547 -53.89799880981445 4.500999927520752
      vertex -39.722999572753906 -54.10200119018555 5.5
      vertex -39 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.09238508343696594 -0.7225150465965271 0.6851547360420227
    outer loop
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
      vertex -89.48400115966797 -3.378000020980835 3.6619999408721924
    endloop
  endfacet
  facet normal 0.23507246375083923 0.30618682503700256 0.9224914908409119
    outer loop
      vertex -80.2490005493164 18.298999786376953 2.634000062942505
      vertex -79.93900299072266 18.06100082397461 2.634000062942505
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
    endloop
  endfacet
  facet normal -0.09262514859437943 -0.7223204970359802 0.685327410697937
    outer loop
      vertex -89.48699951171875 -2.5820000171661377 4.500999927520752
      vertex -90.41500091552734 -2.4630000591278076 4.500999927520752
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
    endloop
  endfacet
  facet normal 0.5269486308097839 0.6871321797370911 0.5001745223999023
    outer loop
      vertex -38.37799835205078 -54.87900161743164 5.5
      vertex -37.96699905395508 -54.46699905395508 4.500999927520752
      vertex -39 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.27639999985694885 -0.6738045811653137 0.6852666735649109
    outer loop
      vertex -90.41500091552734 -2.4630000591278076 4.500999927520752
      vertex -91.6760025024414 -2.7990000247955322 3.6619999408721924
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3058600127696991 0.2350499927997589 0.9226056337356567
    outer loop
      vertex -79.93900299072266 18.06100082397461 2.634000062942505
      vertex -79.69999694824219 17.75 2.634000062942505
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
    endloop
  endfacet
  facet normal -0.2764846384525299 -0.6736879348754883 0.6853471994400024
    outer loop
      vertex -90.41500091552734 -2.4630000591278076 4.500999927520752
      vertex -91.27999877929688 -2.1080000400543213 4.500999927520752
      vertex -91.6760025024414 -2.7990000247955322 3.6619999408721924
    endloop
  endfacet
  facet normal 0.07979033142328262 0.607032299041748 0.7906612753868103
    outer loop
      vertex -80.66500091552734 18.249000549316406 2.7929999828338623
      vertex -80.61100006103516 18.448999404907227 2.634000062942505
      vertex -80.9990005493164 18.5 2.634000062942505
    endloop
  endfacet
  facet normal -0.794902503490448 0.6067371964454651 0
    outer loop
      vertex -49.707000732421875 17.707000732421875 3.5
      vertex -49.8650016784668 17.5 10.5
      vertex -49.707000732421875 17.707000732421875 10.5
    endloop
  endfacet
  facet normal 0.07999084144830704 0.6072031855583191 0.790509819984436
    outer loop
      vertex -80.66500091552734 18.249000549316406 2.7929999828338623
      vertex -80.9990005493164 18.5 2.634000062942505
      vertex -80.9990005493164 18.292999267578125 2.7929999828338623
    endloop
  endfacet
  facet normal 0.2787246108055115 0.672676146030426 0.6854337453842163
    outer loop
      vertex -39.571998596191406 -53.540000915527344 4.500999927520752
      vertex -38.70800018310547 -53.89799880981445 4.500999927520752
      vertex -38.310001373291016 -53.20800018310547 3.6619999408721924
    endloop
  endfacet
  facet normal 0.234296977519989 0.5654367208480835 0.790813684463501
    outer loop
      vertex -80.61100006103516 18.448999404907227 2.634000062942505
      vertex -80.66500091552734 18.249000549316406 2.7929999828338623
      vertex -80.2490005493164 18.298999786376953 2.634000062942505
    endloop
  endfacet
  facet normal -0.1128569096326828 -0.8585976958274841 0.5000733733177185
    outer loop
      vertex -40.5 -60 5.5
      vertex -41.2760009765625 -59.89799880981445 5.5
      vertex -41.426998138427734 -60.459999084472656 4.500999927520752
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -49.8650016784668 17.5 3.5
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -49.8650016784668 17.5 10.5
    endloop
  endfacet
  facet normal 0.5627329349517822 0.734679102897644 0.37891721725463867
    outer loop
      vertex -80.43199920654297 17.98200035095215 3
      vertex -80.48200225830078 17.895999908447266 3.240999937057495
      vertex -80.1969985961914 17.802000045776367 3
    endloop
  endfacet
  facet normal -0.9156829118728638 0.3799514174461365 0.13100256025791168
    outer loop
      vertex -49.89500045776367 17.517000198364258 3.240999937057495
      vertex -49.96500015258789 17.259000778198242 3.5
      vertex -49.8650016784668 17.5 3.5
    endloop
  endfacet
  facet normal 0.1127147451043129 -0.8586211800575256 0.5000650882720947
    outer loop
      vertex -39.571998596191406 -60.459999084472656 4.500999927520752
      vertex -39.722999572753906 -59.89799880981445 5.5
      vertex -40.5 -60 5.5
    endloop
  endfacet
  facet normal 0.48381996154785156 0.6316538453102112 0.6057488322257996
    outer loop
      vertex -80.1969985961914 17.802000045776367 3
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
      vertex -80.43199920654297 17.98200035095215 3
    endloop
  endfacet
  facet normal -0.794902503490448 0.6067371964454651 0
    outer loop
      vertex -49.8650016784668 17.5 3.5
      vertex -49.8650016784668 17.5 10.5
      vertex -49.707000732421875 17.707000732421875 3.5
    endloop
  endfacet
  facet normal 0.4855012595653534 0.6316229701042175 0.6044343709945679
    outer loop
      vertex -80.1969985961914 17.802000045776367 3
      vertex -80.08499908447266 17.913999557495117 2.7929999828338623
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
    endloop
  endfacet
  facet normal 0.11286836862564087 -0.8585397005081177 0.5001702904701233
    outer loop
      vertex -40.5 -60.582000732421875 4.500999927520752
      vertex -39.571998596191406 -60.459999084472656 4.500999927520752
      vertex -40.5 -60 5.5
    endloop
  endfacet
  facet normal 0.2787246108055115 -0.672676146030426 0.6854337453842163
    outer loop
      vertex -39.571998596191406 -60.459999084472656 4.500999927520752
      vertex -38.310001373291016 -60.79199981689453 3.6619999408721924
      vertex -38.70800018310547 -60.10200119018555 4.500999927520752
    endloop
  endfacet
  facet normal 0.8528528213500977 0.3562116324901581 0.38177916407585144
    outer loop
      vertex -80.10399627685547 17.517000198364258 3.240999937057495
      vertex -80 17.26799964904785 3.240999937057495
      vertex -80.01699829101562 17.566999435424805 3
    endloop
  endfacet
  facet normal 0.09493660926818848 0.7221407890319824 0.6852005124092102
    outer loop
      vertex -40.5 -53.417999267578125 4.500999927520752
      vertex -39.571998596191406 -53.540000915527344 4.500999927520752
      vertex -39.36600112915039 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3314758837223053 -0.7999864816665649 0.5001453757286072
    outer loop
      vertex -39.571998596191406 -60.459999084472656 4.500999927520752
      vertex -38.70800018310547 -60.10200119018555 4.500999927520752
      vertex -39.722999572753906 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0.3318139612674713 -0.7996716499328613 0.5004246234893799
    outer loop
      vertex -38.70800018310547 -60.10200119018555 4.500999927520752
      vertex -39 -59.597999572753906 5.5
      vertex -39.722999572753906 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0.3314758837223053 0.7999864816665649 0.5001453757286072
    outer loop
      vertex -38.70800018310547 -53.89799880981445 4.500999927520752
      vertex -39.571998596191406 -53.540000915527344 4.500999927520752
      vertex -39.722999572753906 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal -0.5761542916297913 -0.44549983739852905 0.6852562427520752
    outer loop
      vertex -92.58499908447266 -60.10599899291992 3.6619999408721924
      vertex -92.02400207519531 -59.54100036621094 4.500999927520752
      vertex -93.28399658203125 -59.20199966430664 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3341551423072815 -0.43830737471580505 0.8344021439552307
    outer loop
      vertex -91.6760025024414 -60.79899978637695 3.6619999408721924
      vertex -92.58499908447266 -60.10599899291992 3.6619999408721924
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
    endloop
  endfacet
  facet normal -0.09497250616550446 0.7221735119819641 0.6851610541343689
    outer loop
      vertex -40.5 -53.417999267578125 4.500999927520752
      vertex -40.5 -52.62200164794922 3.6619999408721924
      vertex -41.632999420166016 -52.770999908447266 3.6619999408721924
    endloop
  endfacet
  facet normal 0.5269486308097839 -0.6871321797370911 0.5001745223999023
    outer loop
      vertex -39 -59.597999572753906 5.5
      vertex -37.96699905395508 -59.53300094604492 4.500999927520752
      vertex -38.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0.5272573828697205 -0.6866392493247986 0.5005258917808533
    outer loop
      vertex -38.70800018310547 -60.10200119018555 4.500999927520752
      vertex -37.96699905395508 -59.53300094604492 4.500999927520752
      vertex -39 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal 0.11286836862564087 0.8585397005081177 0.5001702904701233
    outer loop
      vertex -39.571998596191406 -53.540000915527344 4.500999927520752
      vertex -40.5 -53.417999267578125 4.500999927520752
      vertex -40.5 -54 5.5
    endloop
  endfacet
  facet normal 0.6867327690124512 -0.5275440216064453 0.5000954270362854
    outer loop
      vertex -37.96699905395508 -59.53300094604492 4.500999927520752
      vertex -37.39699935913086 -58.79100036621094 4.500999927520752
      vertex -38.37799835205078 -59.12099838256836 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -60 5.5
      vertex -39.722999572753906 -59.89799880981445 5.5
      vertex -40.24100112915039 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39 -59.597999572753906 5.5
      vertex -40.24100112915039 -57.965999603271484 5.5
      vertex -39.722999572753906 -59.89799880981445 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -38.37799835205078 -59.12099838256836 5.5
      vertex -39.79199981689453 -57.707000732421875 5.5
      vertex -39 -59.597999572753906 5.5
    endloop
  endfacet
  facet normal -0.43619611859321594 -0.3372799754142761 0.8342512845993042
    outer loop
      vertex -92.58499908447266 -60.10599899291992 3.6619999408721924
      vertex -93.28399658203125 -59.20199966430664 3.6619999408721924
      vertex -94.12000274658203 -59.68899917602539 3.0280001163482666
    endloop
  endfacet
  facet normal 0.1127147451043129 0.8586211800575256 0.5000650882720947
    outer loop
      vertex -39.571998596191406 -53.540000915527344 4.500999927520752
      vertex -40.5 -54 5.5
      vertex -39.722999572753906 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal -0.43617257475852966 -0.33700650930404663 0.8343740701675415
    outer loop
      vertex -92.58499908447266 -60.10599899291992 3.6619999408721924
      vertex -94.12000274658203 -59.68899917602539 3.0280001163482666
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
    endloop
  endfacet
  facet normal 0.3729042708873749 0.48513758182525635 0.790938675403595
    outer loop
      vertex -79.93900299072266 18.06100082397461 2.634000062942505
      vertex -80.35299682617188 18.1200008392334 2.7929999828338623
      vertex -80.08499908447266 17.913999557495117 2.7929999828338623
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 -82 10.5
      vertex -35 -65.53600311279297 10.5
      vertex -35 -82 3.5
    endloop
  endfacet
  facet normal 0.6328216791152954 0.4847145080566406 0.6038116812705994
    outer loop
      vertex -80.1969985961914 17.802000045776367 3
      vertex -80.01699829101562 17.566999435424805 3
      vertex -79.87999725341797 17.645999908447266 2.7929999828338623
    endloop
  endfacet
  facet normal -0.27159249782562256 -0.20987620949745178 0.9392494559288025
    outer loop
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
    endloop
  endfacet
  facet normal 0.7353399395942688 0.30737683176994324 0.6039823293685913
    outer loop
      vertex -79.87999725341797 17.645999908447266 2.7929999828338623
      vertex -80.01699829101562 17.566999435424805 3
      vertex -79.75 17.334999084472656 2.7929999828338623
    endloop
  endfacet
  facet normal -0.27159249782562256 -0.20987620949745178 0.9392494559288025
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
    endloop
  endfacet
  facet normal 0.6328337788581848 0.4840705990791321 0.6043154001235962
    outer loop
      vertex -80.1969985961914 17.802000045776367 3
      vertex -79.87999725341797 17.645999908447266 2.7929999828338623
      vertex -80.08499908447266 17.913999557495117 2.7929999828338623
    endloop
  endfacet
  facet normal -0.09503646194934845 0.7221212983131409 0.685207188129425
    outer loop
      vertex -40.5 -53.417999267578125 4.500999927520752
      vertex -41.632999420166016 -52.770999908447266 3.6619999408721924
      vertex -41.426998138427734 -53.540000915527344 4.500999927520752
    endloop
  endfacet
  facet normal 0.8560248017311096 0.35303211212158203 0.3776107132434845
    outer loop
      vertex -80.01699829101562 17.566999435424805 3
      vertex -80 17.26799964904785 3.240999937057495
      vertex -79.90399932861328 17.292999267578125 3
    endloop
  endfacet
  facet normal -0.24748027324676514 -0.07635249942541122 0.9658797979354858
    outer loop
      vertex -35.46799850463867 -56.930999755859375 4.103000164031982
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
      vertex -35.45500183105469 -57.59299850463867 4.053999900817871
    endloop
  endfacet
  facet normal -0.11298856884241104 0.8585278987884521 0.5001633763313293
    outer loop
      vertex -40.5 -53.417999267578125 4.500999927520752
      vertex -41.426998138427734 -53.540000915527344 4.500999927520752
      vertex -40.5 -54 5.5
    endloop
  endfacet
  facet normal -0.27158287167549133 -0.20983712375164032 0.9392609596252441
    outer loop
      vertex -94.12000274658203 -59.68899917602539 3.0280001163482666
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
    endloop
  endfacet
  facet normal -0.6512255668640137 -0.19095462560653687 0.7344669103622437
    outer loop
      vertex -35.41699981689453 -58.310001373291016 3.890000104904175
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
    endloop
  endfacet
  facet normal 0.7342099547386169 0.30279460549354553 0.6076604127883911
    outer loop
      vertex -80.01699829101562 17.566999435424805 3
      vertex -79.90399932861328 17.292999267578125 3
      vertex -79.75 17.334999084472656 2.7929999828338623
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -56 5.5
      vertex -40.24100112915039 -56.034000396728516 5.5
      vertex -40.5 -54 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -41.2760009765625 -54.10200119018555 5.5
      vertex -40.5 -56 5.5
      vertex -40.5 -54 5.5
    endloop
  endfacet
  facet normal 0.48545223474502563 0.3730645775794983 0.7906699180603027
    outer loop
      vertex -80.08499908447266 17.913999557495117 2.7929999828338623
      vertex -79.69999694824219 17.75 2.634000062942505
      vertex -79.93900299072266 18.06100082397461 2.634000062942505
    endloop
  endfacet
  facet normal 0.7930510640144348 0.6091551780700684 0
    outer loop
      vertex -90.20600128173828 -57.707000732421875 0
      vertex -90.36499786376953 -57.5 0
      vertex -90.36499786376953 -57.5 5.5
    endloop
  endfacet
  facet normal -0.6173408031463623 -0.20635885000228882 0.7591484785079956
    outer loop
      vertex -35.41699981689453 -58.310001373291016 3.890000104904175
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
      vertex -35.45500183105469 -57.59299850463867 4.053999900817871
    endloop
  endfacet
  facet normal 0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -90.36499786376953 -57.5 5.5
      vertex -90.36499786376953 -57.5 0
      vertex -90.46499633789062 -57.25899887084961 0
    endloop
  endfacet
  facet normal 0.8581587672233582 -0.1129399910569191 0.5008074045181274
    outer loop
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
      vertex -36.91699981689453 -57 4.500999927520752
      vertex -37.5 -57 5.5
    endloop
  endfacet
  facet normal 0.8139881491661072 -0.0014221301535144448 0.5808797478675842
    outer loop
      vertex -36.91699981689453 -57 4.500999927520752
      vertex -36.762001037597656 -57.32600021362305 4.2829999923706055
      vertex -36.76300048828125 -56.67300033569336 4.285999774932861
    endloop
  endfacet
  facet normal 0.500314474105835 0.07586073130369186 -0.862514078617096
    outer loop
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
    endloop
  endfacet
  facet normal 0.500314474105835 0.07586073130369186 -0.862514078617096
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
    endloop
  endfacet
  facet normal 0.4850795865058899 0.371049702167511 0.7918458580970764
    outer loop
      vertex -79.69999694824219 17.75 2.634000062942505
      vertex -80.08499908447266 17.913999557495117 2.7929999828338623
      vertex -79.87999725341797 17.645999908447266 2.7929999828338623
    endloop
  endfacet
  facet normal 0.27159249782562256 0.20987620949745178 -0.9392494559288025
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
    endloop
  endfacet
  facet normal 0.27159249782562256 0.20987620949745178 -0.9392494559288025
    outer loop
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
    endloop
  endfacet
  facet normal 0.27158287167549133 0.20983712375164032 -0.9392609596252441
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
    endloop
  endfacet
  facet normal 0.3165944218635559 0.13248787820339203 -0.9392629861831665
    outer loop
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
    endloop
  endfacet
  facet normal 0.5655145049095154 0.236388698220253 0.7901352643966675
    outer loop
      vertex -79.87999725341797 17.645999908447266 2.7929999828338623
      vertex -79.75 17.334999084472656 2.7929999828338623
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
    endloop
  endfacet
  facet normal -0.6164117455482483 -0.06518742442131042 0.7847210764884949
    outer loop
      vertex -35.31399917602539 -56.928001403808594 4.21999979019165
      vertex -35.45500183105469 -57.59299850463867 4.053999900817871
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
    endloop
  endfacet
  facet normal 0.5642961859703064 0.23382438719272614 0.7917675971984863
    outer loop
      vertex -79.87999725341797 17.645999908447266 2.7929999828338623
      vertex -79.55000305175781 17.38800048828125 2.634000062942505
      vertex -79.69999694824219 17.75 2.634000062942505
    endloop
  endfacet
  facet normal 0.8582285642623901 -0.11280839145183563 0.5007174611091614
    outer loop
      vertex -37.5 -57 5.5
      vertex -37.60200119018555 -57.7760009765625 5.5
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
    endloop
  endfacet
  facet normal -0.8736547827720642 -0.13768404722213745 0.4666588008403778
    outer loop
      vertex -35.03200149536133 -58.483001708984375 4.425000190734863
      vertex -35.30500030517578 -57.6150016784668 4.170000076293945
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
    endloop
  endfacet
  facet normal -0.5328369736671448 -0.07332147657871246 0.8430354595184326
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
    endloop
  endfacet
  facet normal 0.2435203492641449 0.5877912640571594 0.7714915871620178
    outer loop
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
      vertex -80.9990005493164 18.740999221801758 2.5339999198913574
      vertex -80.61100006103516 18.448999404907227 2.634000062942505
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
    endloop
  endfacet
  facet normal 0.243494912981987 0.5876343846321106 0.7716191411018372
    outer loop
      vertex -80.61100006103516 18.448999404907227 2.634000062942505
      vertex -80.2490005493164 18.298999786376953 2.634000062942505
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
    endloop
  endfacet
  facet normal 0.7337898015975952 0.09657212346792221 0.6724777221679688
    outer loop
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
      vertex -36.91699981689453 -57 4.500999927520752
      vertex -36.76300048828125 -56.67300033569336 4.285999774932861
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
    endloop
  endfacet
  facet normal 0.05384564399719238 0.12996859848499298 0.9900549650192261
    outer loop
      vertex -79.76799774169922 18.231000900268555 2.5339999198913574
      vertex -80.9990005493164 19 2.5
      vertex -80.9990005493164 18.740999221801758 2.5339999198913574
    endloop
  endfacet
  facet normal -0.9255057573318481 0.1079753041267395 0.36301568150520325
    outer loop
      vertex -35.018001556396484 5.738999843597412 3.444999933242798
      vertex -35.16400146484375 5.671000003814697 3.0929999351501465
      vertex -35.20399856567383 4.296000003814697 3.4000000953674316
    endloop
  endfacet
  facet normal 0.12019895017147064 0.916946291923523 0.38047564029693604
    outer loop
      vertex -80.9990005493164 18.134000778198242 3
      vertex -80.9990005493164 18.034000396728516 3.240999937057495
      vertex -80.73200225830078 17.999000549316406 3.240999937057495
    endloop
  endfacet
  facet normal 0.5043092370033264 -0.15070946514606476 0.8502698540687561
    outer loop
      vertex -36.762001037597656 -57.32600021362305 4.2829999923706055
      vertex -36.742000579833984 -57.65399932861328 4.2129998207092285
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
    endloop
  endfacet
  facet normal 0.8581724166870117 0.11280101537704468 0.5008153319358826
    outer loop
      vertex -36.91699981689453 -57 4.500999927520752
      vertex -37.60200119018555 -56.2239990234375 5.5
      vertex -37.5 -57 5.5
    endloop
  endfacet
  facet normal 0.7578991055488586 -0.15637518465518951 0.6333528161048889
    outer loop
      vertex -36.742000579833984 -57.65399932861328 4.2129998207092285
      vertex -37.03900146484375 -57.926998138427734 4.500999927520752
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
    endloop
  endfacet
  facet normal 0.8582057952880859 0.11294617503881454 0.5007254481315613
    outer loop
      vertex -36.91699981689453 -57 4.500999927520752
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
      vertex -37.60200119018555 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0.5066909193992615 -0.2566617429256439 0.8230364918708801
    outer loop
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
      vertex -36.742000579833984 -57.65399932861328 4.2129998207092285
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
    endloop
  endfacet
  facet normal -0.7869138717651367 0.603055477142334 0.13073112070560455
    outer loop
      vertex -49.8650016784668 17.5 3.5
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
      vertex -49.89500045776367 17.517000198364258 3.240999937057495
    endloop
  endfacet
  facet normal 0.6782727837562561 0.2680622339248657 0.6841700673103333
    outer loop
      vertex -37.39699935913086 -55.20899963378906 4.500999927520752
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
      vertex -36.70800018310547 -54.81100082397461 3.6619999408721924
    endloop
  endfacet
  facet normal 0.42448896169662476 -0.20448386669158936 0.8820405006408691
    outer loop
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
      vertex -36.141998291015625 -58.255001068115234 3.7219998836517334
    endloop
  endfacet
  facet normal -0.9227403402328491 0.044196948409080505 0.3828797936439514
    outer loop
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
      vertex -35.13399887084961 7.103000164031982 3
      vertex -35.16400146484375 5.671000003814697 3.0929999351501465
    endloop
  endfacet
  facet normal 0.6811462640762329 0.28223422169685364 0.6755616664886475
    outer loop
      vertex -37.39699935913086 -55.20899963378906 4.500999927520752
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
      vertex -36.667999267578125 -55.68299865722656 3.9639999866485596
    endloop
  endfacet
  facet normal 0.8000219464302063 0.33039578795433044 0.5008029341697693
    outer loop
      vertex -37.03900146484375 -56.073001861572266 4.500999927520752
      vertex -37.9010009765625 -55.5 5.5
      vertex -37.60200119018555 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal -0.9258143901824951 0.04526370391249657 0.3752584457397461
    outer loop
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
      vertex -35.16400146484375 5.671000003814697 3.0929999351501465
      vertex -35.018001556396484 5.738999843597412 3.444999933242798
    endloop
  endfacet
  facet normal -0.9971551299095154 -0.00042361830128356814 0.07537581771612167
    outer loop
      vertex -35 5.539000034332275 3.681999921798706
      vertex -35.034000396728516 7.103000164031982 3.240999937057495
      vertex -35.018001556396484 5.738999843597412 3.444999933242798
    endloop
  endfacet
  facet normal -0.6020945906639099 0.7876457571983337 0.1307528167963028
    outer loop
      vertex -49.499000549316406 17.865999221801758 3.5
      vertex -49.51599884033203 17.895999908447266 3.240999937057495
      vertex -49.707000732421875 17.707000732421875 3.5
    endloop
  endfacet
  facet normal 0.6867461204528809 0.5275006294250488 0.5001228451728821
    outer loop
      vertex -37.39699935913086 -55.20899963378906 4.500999927520752
      vertex -38.37799835205078 -54.87900161743164 5.5
      vertex -37.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.5 -57 5.5
      vertex -39.534000396728516 -57.25899887084961 5.5
      vertex -37.5 -57 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.79199981689453 -56.292999267578125 5.5
      vertex -39.63399887084961 -56.5 5.5
      vertex -37.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39 -54.402000427246094 5.5
      vertex -39.79199981689453 -56.292999267578125 5.5
      vertex -38.37799835205078 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -38.37799835205078 -54.87900161743164 5.5
      vertex -39.79199981689453 -56.292999267578125 5.5
      vertex -37.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal -0.7882814407348633 0.6016834378242493 0.12879984080791473
    outer loop
      vertex -49.707000732421875 17.707000732421875 3.5
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
      vertex -49.8650016784668 17.5 3.5
    endloop
  endfacet
  facet normal 0.1292896717786789 -0.24155335128307343 0.9617360234260559
    outer loop
      vertex -36.0359992980957 -57.5629997253418 3.8959999084472656
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
      vertex -35.96200180053711 -58.25199890136719 3.7130000591278076
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
    endloop
  endfacet
  facet normal -0.6037442088127136 0.7866969704627991 0.1288439780473709
    outer loop
      vertex -49.707000732421875 17.707000732421875 3.5
      vertex -49.51599884033203 17.895999908447266 3.240999937057495
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.757999420166016 -56.034000396728516 5.5
      vertex -41.2760009765625 -54.10200119018555 5.5
      vertex -41 -56.13399887084961 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.722999572753906 -54.10200119018555 5.5
      vertex -40.5 -54 5.5
      vertex -40.24100112915039 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
    endloop
  endfacet
  facet normal -0.6073083281517029 0.7944662570953369 0
    outer loop
      vertex -49.707000732421875 17.707000732421875 3.5
      vertex -49.499000549316406 17.865999221801758 10.5
      vertex -49.499000549316406 17.865999221801758 3.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.5 -56 5.5
      vertex -41.2760009765625 -54.10200119018555 5.5
      vertex -40.757999420166016 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39 -54.402000427246094 5.5
      vertex -39.722999572753906 -54.10200119018555 5.5
      vertex -40.24100112915039 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal 0.0525725893676281 -0.2705326974391937 0.961274266242981
    outer loop
      vertex -35.96200180053711 -58.25199890136719 3.7130000591278076
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
      vertex -36.141998291015625 -58.255001068115234 3.7219998836517334
    endloop
  endfacet
  facet normal -0.5463566184043884 -0.07347963005304337 0.8343231678009033
    outer loop
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
      vertex -93.7249984741211 -58.14699935913086 3.6619999408721924
      vertex -94.84500122070312 -57.018001556396484 3.0280001163482666
    endloop
  endfacet
  facet normal -0.7336912155151367 0.5622680187225342 0.3815126121044159
    outer loop
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
      vertex -49.981998443603516 17.566999435424805 3
      vertex -49.89500045776367 17.517000198364258 3.240999937057495
    endloop
  endfacet
  facet normal -0.500314474105835 -0.07586073130369186 0.862514078617096
    outer loop
      vertex -94.9990005493164 -57 2.9539999961853027
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
    endloop
  endfacet
  facet normal -0.500314474105835 -0.07586073130369186 0.862514078617096
    outer loop
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
      vertex -94.9990005493164 -57.34400177001953 2.9237442016601562
    endloop
  endfacet
  facet normal -0.7330592274665833 0.5646116137504578 0.3792596459388733
    outer loop
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
      vertex -49.80099868774414 17.802000045776367 3
      vertex -49.981998443603516 17.566999435424805 3
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -42 -54.402000427246094 5.5
      vertex -41 -56.13399887084961 5.5
      vertex -41.2760009765625 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.79199981689453 -56.292999267578125 5.5
      vertex -39 -54.402000427246094 5.5
      vertex -40 -56.13399887084961 5.5
    endloop
  endfacet
  facet normal -0.437944233417511 -0.05889922380447388 0.8970706462860107
    outer loop
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
      vertex -94.84500122070312 -57.018001556396484 3.0280001163482666
      vertex -94.9990005493164 -57 2.9539999961853027
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -40.24100112915039 -56.034000396728516 5.5
      vertex -40 -56.13399887084961 5.5
      vertex -39 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.60200119018555 -56.2239990234375 5.5
      vertex -39.534000396728516 -56.74100112915039 5.5
      vertex -37.5 -57 5.5
    endloop
  endfacet
  facet normal 0.12927058339118958 -0.08160987496376038 0.9882453680038452
    outer loop
      vertex -36.0359992980957 -57.5629997253418 3.8959999084472656
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
      vertex -36.22200012207031 -57.56700134277344 3.9200000762939453
    endloop
  endfacet
  facet normal -0.5634292364120483 0.7341653108596802 0.37887832522392273
    outer loop
      vertex -49.566001892089844 17.98200035095215 3
      vertex -49.73099899291992 17.731000900268555 3.240999937057495
      vertex -49.51599884033203 17.895999908447266 3.240999937057495
    endloop
  endfacet
  facet normal -0.26644349098205566 -0.2283092886209488 0.9364201426506042
    outer loop
      vertex -35.45500183105469 -57.59299850463867 4.053999900817871
      vertex -36.0359992980957 -57.5629997253418 3.8959999084472656
      vertex -35.41699981689453 -58.310001373291016 3.890000104904175
    endloop
  endfacet
  facet normal -0.37894925475120544 0.9161006212234497 0.13098515570163727
    outer loop
      vertex -49.499000549316406 17.865999221801758 3.5
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
      vertex -49.51599884033203 17.895999908447266 3.240999937057495
    endloop
  endfacet
  facet normal -0.794902503490448 -0.6067371964454651 0
    outer loop
      vertex -39.63399887084961 -56.5 0
      vertex -39.63399887084961 -56.5 5.5
      vertex -39.79199981689453 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal -0.3165944218635559 -0.13248787820339203 0.9392629861831665
    outer loop
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
      vertex -94.12000274658203 -59.68899917602539 3.0280001163482666
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.63399887084961 -56.5 5.5
      vertex -39.534000396728516 -56.74100112915039 5.5
      vertex -37.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal -0.35378825664520264 0.8552745580673218 0.3786017596721649
    outer loop
      vertex -49.51599884033203 17.895999908447266 3.240999937057495
      vertex -49.266998291015625 17.999000549316406 3.240999937057495
      vertex -49.566001892089844 17.98200035095215 3
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -39.63399887084961 -56.5 5.5
      vertex -39.63399887084961 -56.5 0
      vertex -39.534000396728516 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.5466386079788208 -0.07388313114643097 0.8341028094291687
    outer loop
      vertex -93.87799835205078 -57.01499938964844 3.6619999408721924
      vertex -94.84500122070312 -57.018001556396484 3.0280001163482666
      vertex -93.7249984741211 -58.14699935913086 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.60200119018555 -56.2239990234375 5.5
      vertex -37.9010009765625 -55.5 5.5
      vertex -39.534000396728516 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -39.534000396728516 -56.74100112915039 0
      vertex -39.5 -57 5.5
      vertex -39.534000396728516 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.3233299255371094 -0.2751988470554352 0.9053857326507568
    outer loop
      vertex -36.0359992980957 -57.5629997253418 3.8959999084472656
      vertex -35.96200180053711 -58.25199890136719 3.7130000591278076
      vertex -35.41699981689453 -58.310001373291016 3.890000104904175
    endloop
  endfacet
  facet normal -0.27159249782562256 -0.20987620949745178 0.9392494559288025
    outer loop
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
      vertex -94.9990005493164 -60.3072395324707 2.6357202529907227
    endloop
  endfacet
  facet normal -0.5086621642112732 -0.21286405622959137 0.8342371582984924
    outer loop
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
      vertex -94.12000274658203 -59.68899917602539 3.0280001163482666
      vertex -93.28399658203125 -59.20199966430664 3.6619999408721924
    endloop
  endfacet
  facet normal -0.5085601210594177 -0.21258296072483063 0.834371030330658
    outer loop
      vertex -93.7249984741211 -58.14699935913086 3.6619999408721924
      vertex -94.65899658203125 -58.4010009765625 3.0280001163482666
      vertex -93.28399658203125 -59.20199966430664 3.6619999408721924
    endloop
  endfacet
  facet normal -0.27158287167549133 -0.20983712375164032 0.9392609596252441
    outer loop
      vertex -94.9990005493164 -60.25495147705078 2.647404432296753
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
    endloop
  endfacet
  facet normal -0.26577356457710266 -0.09418291598558426 0.9594237804412842
    outer loop
      vertex -36.0359992980957 -57.5629997253418 3.8959999084472656
      vertex -35.45500183105469 -57.59299850463867 4.053999900817871
      vertex -36.060001373291016 -56.935001373291016 3.9509999752044678
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.63399887084961 -57.5 5.5
      vertex -37.9010009765625 -58.5 5.5
      vertex -39.534000396728516 -57.25899887084961 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -37.5 -57 5.5
      vertex -39.534000396728516 -57.25899887084961 5.5
      vertex -37.60200119018555 -57.7760009765625 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -39.5 -57 5.5
      vertex -37.5 -57 5.5
      vertex -39.534000396728516 -56.74100112915039 5.5
    endloop
  endfacet
  facet normal -0.3165944218635559 -0.13248787820339203 0.9392629861831665
    outer loop
      vertex -94.9990005493164 -60.200504302978516 2.6595680713653564
      vertex -94.12000274658203 -59.68899917602539 3.0280001163482666
      vertex -94.9990005493164 -59.95685958862305 2.6939351558685303
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -39.534000396728516 -57.25899887084961 0
      vertex -39.63399887084961 -57.5 5.5
      vertex -39.534000396728516 -57.25899887084961 5.5
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -60.314937591552734 2.634000062942505
      vertex -94.9990005493164 -60.37186813354492 2.629995584487915
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -61.98398971557617 2.5166008472442627
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
      vertex -94.9990005493164 -62.220001220703125 2.5
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -94.9990005493164 -62.220001220703125 2.5
    endloop
  endfacet
  facet normal 0.052630309015512466 -0.3223690688610077 0.945149838924408
    outer loop
      vertex -36.141998291015625 -58.255001068115234 3.7219998836517334
      vertex -35.819000244140625 -59.41899871826172 3.306999921798706
      vertex -35.96200180053711 -58.25199890136719 3.7130000591278076
    endloop
  endfacet
  facet normal -0.5328369736671448 -0.07332147657871246 0.8430354595184326
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -95.05999755859375 -60.236000061035156 2.634000062942505
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -61.98398971557617 2.5166008472442627
    endloop
  endfacet
  facet normal 0.13065332174301147 -0.9914281368255615 0
    outer loop
      vertex -40.5 -56 0
      vertex -40.5 -56 5.5
      vertex -40.757999420166016 -56.034000396728516 0
    endloop
  endfacet
  facet normal 0.13065332174301147 -0.9914281368255615 0
    outer loop
      vertex -40.757999420166016 -56.034000396728516 5.5
      vertex -40.757999420166016 -56.034000396728516 0
      vertex -40.5 -56 5.5
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -61.98398971557617 2.5166008472442627
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -94.9990005493164 -61.439998626708984 2.5678391456604004
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -40.5 -56 5.5
      vertex -40.5 -56 0
      vertex -40.24100112915039 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -61.98398971557617 2.5166008472442627
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -40 -56.13399887084961 0
      vertex -40 -56.13399887084961 5.5
      vertex -40.24100112915039 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal -0.06990115344524384 -0.5466752648353577 0.8344219326972961
    outer loop
      vertex -90.61799621582031 -61.233001708984375 3.6619999408721924
      vertex -90.86599731445312 -62.16899871826172 3.0280001163482666
      vertex -89.48400115966797 -61.37799835205078 3.6619999408721924
    endloop
  endfacet
  facet normal -0.6073083281517029 -0.7944662570953369 0
    outer loop
      vertex -40 -56.13399887084961 5.5
      vertex -40 -56.13399887084961 0
      vertex -39.79199981689453 -56.292999267578125 0
    endloop
  endfacet
  facet normal -0.6073083281517029 -0.7944662570953369 0
    outer loop
      vertex -40 -56.13399887084961 5.5
      vertex -39.79199981689453 -56.292999267578125 0
      vertex -39.79199981689453 -56.292999267578125 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 -0.6067371964454651 0
    outer loop
      vertex -39.79199981689453 -56.292999267578125 5.5
      vertex -39.79199981689453 -56.292999267578125 0
      vertex -39.63399887084961 -56.5 0
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -39.534000396728516 -56.74100112915039 0
      vertex -39.534000396728516 -56.74100112915039 5.5
      vertex -39.63399887084961 -56.5 0
    endloop
  endfacet
  facet normal -0.9914933443069458 0.13015742599964142 0
    outer loop
      vertex -39.534000396728516 -57.25899887084961 0
      vertex -39.534000396728516 -57.25899887084961 5.5
      vertex -39.5 -57 5.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 -65.53600311279297 10.5
      vertex -35 -5.103000164031982 3.5
      vertex -35 -50.89699935913086 3.5
    endloop
  endfacet
  facet normal -0.3341374397277832 -0.4384072721004486 0.8343567848205566
    outer loop
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
      vertex -92.15699768066406 -61.638999938964844 3.0280001163482666
      vertex -91.6760025024414 -60.79899978637695 3.6619999408721924
    endloop
  endfacet
  facet normal -0.20803257822990417 -0.27295053005218506 0.9392659068107605
    outer loop
      vertex -93.26699829101562 -60.792999267578125 3.0280001163482666
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -92.15699768066406 -61.638999938964844 3.0280001163482666
    endloop
  endfacet
  facet normal 0.053709447383880615 0.12037945538759232 0.9912739396095276
    outer loop
      vertex -36 -50.89699935913086 2.5
      vertex -37.28300094604492 -51.428001403808594 2.634000062942505
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -94.9990005493164 -61.98398971557617 2.5166008472442627
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -61.98398971557617 2.5166008472442627
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
    endloop
  endfacet
  facet normal 0.053679171949625015 0.12045083194971085 0.9912669658660889
    outer loop
      vertex -38.667999267578125 -49.70800018310547 2.5
      vertex -37.28300094604492 -51.428001403808594 2.634000062942505
      vertex -36 -50.89699935913086 2.5
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -61.98394775390625 2.516603708267212
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
    endloop
  endfacet
  facet normal 0.015618247911334038 0.1249598041176796 0.9920388460159302
    outer loop
      vertex -36 -50.89699935913086 2.5
      vertex -36.20899963378906 -52.67300033569336 2.7269999980926514
      vertex -35.733001708984375 -52.40700149536133 2.686000108718872
    endloop
  endfacet
  facet normal -0.12952275574207306 0.09863307327032089 0.9866586923599243
    outer loop
      vertex -36 -50.89699935913086 2.5
      vertex -35.733001708984375 -52.40700149536133 2.686000108718872
      vertex -35.74100112915039 -50.89699935913086 2.5339999198913574
    endloop
  endfacet
  facet normal -0.09135701507329941 -0.35681501030921936 0.9296972155570984
    outer loop
      vertex -36.141998291015625 -58.255001068115234 3.7219998836517334
      vertex -35.98099899291992 -59.41400146484375 3.2929999828338623
      vertex -35.819000244140625 -59.41899871826172 3.306999921798706
    endloop
  endfacet
  facet normal -0.9944416880607605 0.03007047437131405 0.10090314596891403
    outer loop
      vertex -35 4.0289998054504395 4.131999969482422
      vertex -35 5.539000034332275 3.681999921798706
      vertex -35.018001556396484 5.738999843597412 3.444999933242798
    endloop
  endfacet
  facet normal -0.327227920293808 0.09292562305927277 0.940365195274353
    outer loop
      vertex -35.74100112915039 -50.89699935913086 2.5339999198913574
      vertex -35.733001708984375 -52.40700149536133 2.686000108718872
      vertex -35.604000091552734 -52.39799880981445 2.7300000190734863
    endloop
  endfacet
  facet normal -0.38185691833496094 0.08531615138053894 0.9202752113342285
    outer loop
      vertex -35.74100112915039 -50.89699935913086 2.5339999198913574
      vertex -35.604000091552734 -52.39799880981445 2.7300000190734863
      vertex -35.5 -50.89699935913086 2.634000062942505
    endloop
  endfacet
  facet normal -0.6050443053245544 0.08626765757799149 0.791504442691803
    outer loop
      vertex -35.5 -50.89699935913086 2.634000062942505
      vertex -35.24800109863281 -52.349998474121094 2.984999895095825
      vertex -35.29199981689453 -50.89699935913086 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7933648228645325 0.056073203682899475 0.606158435344696
    outer loop
      vertex -35.29199981689453 -50.89699935913086 2.7929999828338623
      vertex -35.24800109863281 -52.349998474121094 2.984999895095825
      vertex -35.16400146484375 -52.32899856567383 3.0929999351501465
    endloop
  endfacet
  facet normal 0.2347913682460785 0.291384220123291 0.9273447394371033
    outer loop
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
      vertex -36.71900177001953 4.78000020980835 3.0280001163482666
    endloop
  endfacet
  facet normal -0.7936564683914185 0.05596913769841194 0.605786144733429
    outer loop
      vertex -35.29199981689453 -50.89699935913086 2.7929999828338623
      vertex -35.16400146484375 -52.32899856567383 3.0929999351501465
      vertex -35.13399887084961 -50.89699935913086 3
    endloop
  endfacet
  facet normal -0.07533617317676544 -0.09202178567647934 0.9929030537605286
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -93.53199768066406 -63.42100143432617 2.5
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
    endloop
  endfacet
  facet normal -0.9227403402328491 0.044196948409080505 0.3828797936439514
    outer loop
      vertex -35.13399887084961 -50.89699935913086 3
      vertex -35.16400146484375 -52.32899856567383 3.0929999351501465
      vertex -35.034000396728516 -50.89699935913086 3.240999937057495
    endloop
  endfacet
  facet normal -0.9914628863334656 0.007835699245333672 0.13015343248844147
    outer loop
      vertex -35.018001556396484 -52.26100158691406 3.444999933242798
      vertex -35 -50.89699935913086 3.5
      vertex -35.034000396728516 -50.89699935913086 3.240999937057495
    endloop
  endfacet
  facet normal -0.043529707938432693 -0.34061381220817566 0.9391950964927673
    outer loop
      vertex -89.48100280761719 -62.34600067138672 3.0280001163482666
      vertex -90.86599731445312 -62.16899871826172 3.0280001163482666
      vertex -91.14299774169922 -63.220001220703125 2.634000062942505
    endloop
  endfacet
  facet normal -0.9914933443069458 0 0.13015742599964142
    outer loop
      vertex -35 -50.89699935913086 3.5
      vertex -35 -5.103000164031982 3.5
      vertex -35.034000396728516 -50.89699935913086 3.240999937057495
    endloop
  endfacet
  facet normal -0.13043133914470673 -0.3177110552787781 0.9391737580299377
    outer loop
      vertex -90.86599731445312 -62.16899871826172 3.0280001163482666
      vertex -92.15699768066406 -61.638999938964844 3.0280001163482666
      vertex -92.6969985961914 -62.582000732421875 2.634000062942505
    endloop
  endfacet
  facet normal -0.20802582800388336 -0.27327680587768555 0.9391725063323975
    outer loop
      vertex -92.15699768066406 -61.638999938964844 3.0280001163482666
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -92.6969985961914 -62.582000732421875 2.634000062942505
    endloop
  endfacet
  facet normal -0.1304338276386261 -0.3177024722099304 0.9391763210296631
    outer loop
      vertex -92.6969985961914 -62.582000732421875 2.634000062942505
      vertex -91.14299774169922 -63.220001220703125 2.634000062942505
      vertex -90.86599731445312 -62.16899871826172 3.0280001163482666
    endloop
  endfacet
  facet normal -0.8736749887466431 -0.16087840497493744 0.45914068818092346
    outer loop
      vertex -35.03200149536133 -58.483001708984375 4.425000190734863
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
      vertex -35.0260009765625 -59.68000030517578 4.017000198364258
    endloop
  endfacet
  facet normal -0.3282952606678009 0.242768332362175 0.9128448963165283
    outer loop
      vertex -35.73500061035156 4.184000015258789 3.059999942779541
      vertex -35.604000091552734 5.6020002365112305 2.7300000190734863
      vertex -35.733001708984375 5.5929999351501465 2.686000108718872
    endloop
  endfacet
  facet normal -0.19216535985469818 0.2520257234573364 0.9484490156173706
    outer loop
      vertex -35.73500061035156 4.184000015258789 3.059999942779541
      vertex -35.733001708984375 5.5929999351501465 2.686000108718872
      vertex -35.8849983215332 4.175000190734863 3.0320000648498535
    endloop
  endfacet
  facet normal -0.06872645020484924 -0.09028370678424835 0.9935418963432312
    outer loop
      vertex -92.6969985961914 -62.582000732421875 2.634000062942505
      vertex -94.03299713134766 -61.564998626708984 2.634000062942505
      vertex -93.53199768066406 -63.42100143432617 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0 0.9914933443069458
    outer loop
      vertex -36 -50.89699935913086 2.5
      vertex -35.74100112915039 -50.89699935913086 2.5339999198913574
      vertex -36 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal -0.651441216468811 -0.2605305314064026 0.7125645279884338
    outer loop
      vertex -35.34700012207031 -59.49700164794922 3.5199999809265137
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
      vertex -35.41699981689453 -58.310001373291016 3.890000104904175
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -38.667999267578125 -49.70800018310547 2.5
      vertex -36 -50.89699935913086 2.5
      vertex -36 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal -0.3233940601348877 -0.29892709851264954 0.8978078365325928
    outer loop
      vertex -35.96200180053711 -58.25199890136719 3.7130000591278076
      vertex -35.34700012207031 -59.49700164794922 3.5199999809265137
      vertex -35.41699981689453 -58.310001373291016 3.890000104904175
    endloop
  endfacet
  facet normal -0.043734993785619736 -0.3402746021747589 0.9393085241317749
    outer loop
      vertex -89.48100280761719 -62.34600067138672 3.0280001163482666
      vertex -91.14299774169922 -63.220001220703125 2.634000062942505
      vertex -89.47799682617188 -63.433998107910156 2.634000062942505
    endloop
  endfacet
  facet normal -0.9988061189651489 0.011264056898653507 0.04753338545560837
    outer loop
      vertex -35 -50.89699935913086 3.5
      vertex -35.018001556396484 -52.26100158691406 3.444999933242798
      vertex -35 -56.999000549316406 4.946000099182129
    endloop
  endfacet
  facet normal -0.5883092284202576 0.1974579244852066 0.7841572761535645
    outer loop
      vertex -35.30799865722656 4.260000228881836 3.2899999618530273
      vertex -35.24800109863281 5.650000095367432 2.984999895095825
      vertex -35.604000091552734 5.6020002365112305 2.7300000190734863
    endloop
  endfacet
  facet normal -0.4931298494338989 0.2401484251022339 0.8361529111862183
    outer loop
      vertex -35.604000091552734 5.6020002365112305 2.7300000190734863
      vertex -35.73500061035156 4.184000015258789 3.059999942779541
      vertex -35.30799865722656 4.260000228881836 3.2899999618530273
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35 -65.53600311279297 10.5
      vertex -35 -50.89699935913086 3.5
    endloop
  endfacet
  facet normal -0.04620490223169327 -0.11254297196865082 0.992572009563446
    outer loop
      vertex -93.53199768066406 -63.42100143432617 2.5
      vertex -91.14299774169922 -63.220001220703125 2.634000062942505
      vertex -92.6969985961914 -62.582000732421875 2.634000062942505
    endloop
  endfacet
  facet normal -0.033080875873565674 -0.17707808315753937 0.9836406707763672
    outer loop
      vertex -93.53199768066406 -63.42100143432617 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -89.47799682617188 -63.433998107910156 2.634000062942505
    endloop
  endfacet
  facet normal 0.521631121635437 -0.29773834347724915 0.7995328903198242
    outer loop
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
      vertex -36.70800018310547 -59.18899917602539 3.6619999408721924
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
    endloop
  endfacet
  facet normal -0.03276100382208824 -0.25489285588264465 0.9664141535758972
    outer loop
      vertex -93.53199768066406 -63.42100143432617 2.5
      vertex -89.47799682617188 -63.433998107910156 2.634000062942505
      vertex -91.14299774169922 -63.220001220703125 2.634000062942505
    endloop
  endfacet
  facet normal -0.7942138910293579 0.1543249785900116 0.5877143144607544
    outer loop
      vertex -35.20399856567383 4.296000003814697 3.4000000953674316
      vertex -35.16400146484375 5.671000003814697 3.0929999351501465
      vertex -35.24800109863281 5.650000095367432 2.984999895095825
    endloop
  endfacet
  facet normal -0.7433530688285828 0.173817977309227 0.6459206938743591
    outer loop
      vertex -35.24800109863281 5.650000095367432 2.984999895095825
      vertex -35.30799865722656 4.260000228881836 3.2899999618530273
      vertex -35.20399856567383 4.296000003814697 3.4000000953674316
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -82 2.5
      vertex -93.53199768066406 -63.42100143432617 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -93.53199768066406 -63.42100143432617 2.5
      vertex -94.9990005493164 -82 2.5
    endloop
  endfacet
  facet normal -0.051760464906692505 0.24196618795394897 0.968903124332428
    outer loop
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
      vertex -35.8849983215332 4.175000190734863 3.0320000648498535
      vertex -35.733001708984375 5.5929999351501465 2.686000108718872
    endloop
  endfacet
  facet normal -0.7631368041038513 -0.21120622754096985 0.610748827457428
    outer loop
      vertex -35.34700012207031 -59.49700164794922 3.5199999809265137
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
    endloop
  endfacet
  facet normal 0.015618247911334038 0.1249598041176796 0.9920388460159302
    outer loop
      vertex -35.733001708984375 5.5929999351501465 2.686000108718872
      vertex -36 7.103000164031982 2.5
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -82 2.5
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -62.220001220703125 2.5
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -82 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -61.439998626708984 2.5548644065856934
      vertex -94.9990005493164 -51.779998779296875 2.5
      vertex -94.9990005493164 -62.220001220703125 2.5
    endloop
  endfacet
  facet normal -0.4326868951320648 -0.2660020589828491 0.8614087104797363
    outer loop
      vertex -35.34700012207031 -59.49700164794922 3.5199999809265137
      vertex -35.819000244140625 -59.41899871826172 3.306999921798706
      vertex -35.284000396728516 -60.775001525878906 3.1570000648498535
    endloop
  endfacet
  facet normal -0.12952275574207306 0.09863307327032089 0.9866586923599243
    outer loop
      vertex -36 7.103000164031982 2.5
      vertex -35.733001708984375 5.5929999351501465 2.686000108718872
      vertex -35.74100112915039 7.103000164031982 2.5339999198913574
    endloop
  endfacet
  facet normal -0.327227920293808 0.09292562305927277 0.940365195274353
    outer loop
      vertex -35.604000091552734 5.6020002365112305 2.7300000190734863
      vertex -35.74100112915039 7.103000164031982 2.5339999198913574
      vertex -35.733001708984375 5.5929999351501465 2.686000108718872
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.73100280761719 -83 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -94.93099975585938 -82.51799774169922 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.41300201416016 -83.41400146484375 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -94.73100280761719 -83 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -93.9990005493164 -83.73200225830078 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -94.41300201416016 -83.41400146484375 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 -84 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
      vertex -93.51699829101562 -83.93199920654297 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.9990005493164 -82 2.5
      vertex -94.93099975585938 -82.51799774169922 2.5
      vertex -88.05599975585938 -64.44400024414062 2.5
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -94.9990005493164 -82 2.5
      vertex -94.9990005493164 -82 0
      vertex -94.93099975585938 -82.51799774169922 0
    endloop
  endfacet
  facet normal -0.9914933443069458 -0.13015742599964142 0
    outer loop
      vertex -94.9990005493164 -82 2.5
      vertex -94.93099975585938 -82.51799774169922 0
      vertex -94.93099975585938 -82.51799774169922 2.5
    endloop
  endfacet
  facet normal -0.38185691833496094 0.08531615138053894 0.9202752113342285
    outer loop
      vertex -35.74100112915039 7.103000164031982 2.5339999198913574
      vertex -35.604000091552734 5.6020002365112305 2.7300000190734863
      vertex -35.5 7.103000164031982 2.634000062942505
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -94.93099975585938 -82.51799774169922 0
      vertex -94.73100280761719 -83 0
      vertex -94.73100280761719 -83 2.5
    endloop
  endfacet
  facet normal -0.9236428737640381 -0.3832542896270752 0
    outer loop
      vertex -94.93099975585938 -82.51799774169922 0
      vertex -94.73100280761719 -83 2.5
      vertex -94.93099975585938 -82.51799774169922 2.5
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -94.73100280761719 -83 0
      vertex -94.41300201416016 -83.41400146484375 0
      vertex -94.41300201416016 -83.41400146484375 2.5
    endloop
  endfacet
  facet normal -0.7930510640144348 -0.6091551780700684 0
    outer loop
      vertex -94.73100280761719 -83 0
      vertex -94.41300201416016 -83.41400146484375 2.5
      vertex -94.73100280761719 -83 2.5
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -94.41300201416016 -83.41400146484375 0
      vertex -93.9990005493164 -83.73200225830078 0
      vertex -93.9990005493164 -83.73200225830078 2.5
    endloop
  endfacet
  facet normal -0.6091551780700684 -0.7930510640144348 0
    outer loop
      vertex -94.41300201416016 -83.41400146484375 0
      vertex -93.9990005493164 -83.73200225830078 2.5
      vertex -94.41300201416016 -83.41400146484375 2.5
    endloop
  endfacet
  facet normal -0.5880213975906372 0.09213721007108688 0.8035804629325867
    outer loop
      vertex -35.604000091552734 5.6020002365112305 2.7300000190734863
      vertex -35.24800109863281 5.650000095367432 2.984999895095825
      vertex -35.5 7.103000164031982 2.634000062942505
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -93.9990005493164 -83.73200225830078 0
      vertex -93.51699829101562 -83.93199920654297 0
      vertex -93.51699829101562 -83.93199920654297 2.5
    endloop
  endfacet
  facet normal -0.3832542896270752 -0.9236428737640381 0
    outer loop
      vertex -93.9990005493164 -83.73200225830078 0
      vertex -93.51699829101562 -83.93199920654297 2.5
      vertex -93.9990005493164 -83.73200225830078 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -93.51699829101562 -83.93199920654297 0
      vertex -92.9990005493164 -84 0
      vertex -92.9990005493164 -84 2.5
    endloop
  endfacet
  facet normal -0.13015742599964142 -0.9914933443069458 0
    outer loop
      vertex -93.51699829101562 -83.93199920654297 0
      vertex -92.9990005493164 -84 2.5
      vertex -93.51699829101562 -83.93199920654297 2.5
    endloop
  endfacet
  facet normal -0.6050443053245544 0.08626765757799149 0.791504442691803
    outer loop
      vertex -35.5 7.103000164031982 2.634000062942505
      vertex -35.24800109863281 5.650000095367432 2.984999895095825
      vertex -35.29199981689453 7.103000164031982 2.7929999828338623
    endloop
  endfacet
  facet normal -0.7933648228645325 0.056073203682899475 0.606158435344696
    outer loop
      vertex -35.29199981689453 7.103000164031982 2.7929999828338623
      vertex -35.24800109863281 5.650000095367432 2.984999895095825
      vertex -35.16400146484375 5.671000003814697 3.0929999351501465
    endloop
  endfacet
  facet normal -0.7936564683914185 0.05596913769841194 0.605786144733429
    outer loop
      vertex -35.29199981689453 7.103000164031982 2.7929999828338623
      vertex -35.16400146484375 5.671000003814697 3.0929999351501465
      vertex -35.13399887084961 7.103000164031982 3
    endloop
  endfacet
  facet normal 0.05929917097091675 0.10717545449733734 0.9924701452255249
    outer loop
      vertex -36 7.103000164031982 2.5
      vertex -37.71699905395508 8.053000450134277 2.5
      vertex -37.28300094604492 6.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal -0.4328811764717102 -0.34306079149246216 0.833620548248291
    outer loop
      vertex -35.34700012207031 -59.49700164794922 3.5199999809265137
      vertex -35.96200180053711 -58.25199890136719 3.7130000591278076
      vertex -35.819000244140625 -59.41899871826172 3.306999921798706
    endloop
  endfacet
  facet normal 0.1312878131866455 0.31717661023139954 0.9392350912094116
    outer loop
      vertex -39.11600112915039 6.164000034332275 3.0280001163482666
      vertex -37.28300094604492 6.572000026702881 2.634000062942505
      vertex -38.83399963378906 7.214000225067139 2.634000062942505
    endloop
  endfacet
  facet normal -0.06990589946508408 -0.546712338924408 0.8343972563743591
    outer loop
      vertex -89.48400115966797 -3.378000020980835 3.6619999408721924
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.13129131495952606 0.3171643912792206 0.9392387270927429
    outer loop
      vertex -37.28300094604492 6.572000026702881 2.634000062942505
      vertex -39.11600112915039 6.164000034332275 3.0280001163482666
      vertex -37.82600021362305 5.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal 0.20764705538749695 -0.3140648305416107 0.9264156818389893
    outer loop
      vertex -36.141998291015625 -58.255001068115234 3.7219998836517334
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
      vertex -35.98099899291992 -59.41400146484375 3.2929999828338623
    endloop
  endfacet
  facet normal 0.04235958680510521 0.10233601182699203 0.9938475489616394
    outer loop
      vertex -37.71699905395508 8.053000450134277 2.5
      vertex -38.83399963378906 7.214000225067139 2.634000062942505
      vertex -37.28300094604492 6.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal 0.18466722965240479 -0.28006061911582947 0.9420530796051025
    outer loop
      vertex -35.82500076293945 -60.696998596191406 2.88100004196167
      vertex -35.98099899291992 -59.41400146484375 3.2929999828338623
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
    endloop
  endfacet
  facet normal 0.08778565376996994 0.6647768020629883 0.7418662309646606
    outer loop
      vertex -38.83399963378906 7.214000225067139 2.634000062942505
      vertex -43.47200012207031 7.97599983215332 2.5
      vertex -40.5 7.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0.4217502474784851 -0.3339785933494568 0.8429620862007141
    outer loop
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
      vertex -36.141998291015625 -58.255001068115234 3.7219998836517334
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
    endloop
  endfacet
  facet normal -0.2091914862394333 -0.5099644660949707 0.8343710899353027
    outer loop
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
      vertex -91.6760025024414 -2.7990000247955322 3.6619999408721924
      vertex -92.15699768066406 -3.6389999389648438 3.0280001163482666
    endloop
  endfacet
  facet normal -0.044944703578948975 0.3401497006416321 0.9392966032028198
    outer loop
      vertex -42.165000915527344 7.214000225067139 2.634000062942505
      vertex -40.5 6.3460001945495605 3.0280001163482666
      vertex -40.5 7.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal 0.044764354825019836 0.3404058516025543 0.939212441444397
    outer loop
      vertex -40.5 6.3460001945495605 3.0280001163482666
      vertex -39.11600112915039 6.164000034332275 3.0280001163482666
      vertex -38.83399963378906 7.214000225067139 2.634000062942505
    endloop
  endfacet
  facet normal -0.44145017862319946 -0.5792573690414429 0.6852610111236572
    outer loop
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
      vertex -91.27999877929688 -2.1080000400543213 4.500999927520752
      vertex -92.02400207519531 -1.5410000085830688 4.500999927520752
    endloop
  endfacet
  facet normal 0.44770383834838867 -0.3241007924079895 0.8333786725997925
    outer loop
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
      vertex -37.40399932861328 -60.09600067138672 3.6619999408721924
      vertex -36.71900177001953 -60.779998779296875 3.0280001163482666
    endloop
  endfacet
  facet normal 0.04491778090596199 0.3401501178741455 0.9392977952957153
    outer loop
      vertex -40.5 6.3460001945495605 3.0280001163482666
      vertex -38.83399963378906 7.214000225067139 2.634000062942505
      vertex -40.5 7.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal -0.5763242244720459 -0.4453060030937195 0.685239315032959
    outer loop
      vertex -92.02400207519531 -1.5410000085830688 4.500999927520752
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
    endloop
  endfacet
  facet normal -0.0187477208673954 0.1418861597776413 0.9897054433822632
    outer loop
      vertex -40.5 7.434000015258789 2.634000062942505
      vertex -43.47200012207031 7.97599983215332 2.5
      vertex -42.165000915527344 7.214000225067139 2.634000062942505
    endloop
  endfacet
  facet normal -0.0021474636159837246 0.16050198674201965 0.9870331883430481
    outer loop
      vertex -37.71699905395508 8.053000450134277 2.5
      vertex -43.47200012207031 7.97599983215332 2.5
      vertex -38.83399963378906 7.214000225067139 2.634000062942505
    endloop
  endfacet
  facet normal -0.4415043294429779 -0.5791160464286804 0.6853455305099487
    outer loop
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
      vertex -91.6760025024414 -2.7990000247955322 3.6619999408721924
      vertex -91.27999877929688 -2.1080000400543213 4.500999927520752
    endloop
  endfacet
  facet normal -0.9147943258285522 -0.14660008251667023 0.3763771057128906
    outer loop
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
      vertex -35.020999908447266 -60.9109992980957 3.63100004196167
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
    endloop
  endfacet
  facet normal -0.0447956807911396 0.3403979539871216 0.9392138123512268
    outer loop
      vertex -40.5 6.3460001945495605 3.0280001163482666
      vertex -42.165000915527344 7.214000225067139 2.634000062942505
      vertex -41.882999420166016 6.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal -0.07191598415374756 0.5464824438095093 0.8343769907951355
    outer loop
      vertex -41.882999420166016 6.164000034332275 3.0280001163482666
      vertex -40.5 5.377999782562256 3.6619999408721924
      vertex -40.5 6.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal -0.7625223994255066 -0.21127575635910034 0.6114917397499084
    outer loop
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
      vertex -35.34700012207031 -59.49700164794922 3.5199999809265137
      vertex -35.284000396728516 -60.775001525878906 3.1570000648498535
    endloop
  endfacet
  facet normal -0.5760412216186523 -0.44541242718696594 0.6854081153869629
    outer loop
      vertex -93.28399658203125 -1.2020000219345093 3.6619999408721924
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
      vertex -92.59500122070312 -0.8019999861717224 4.500999927520752
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -36.13399887084961 14.5 2.5
      vertex -36.5 14.866000175476074 2.5
      vertex -37.71699905395508 8.053000450134277 2.5
    endloop
  endfacet
  facet normal -0.5302640795707703 -0.2970536947250366 0.7940900921821594
    outer loop
      vertex -35.68299865722656 -60.707000732421875 2.9159998893737793
      vertex -35.284000396728516 -60.775001525878906 3.1570000648498535
      vertex -35.819000244140625 -59.41899871826172 3.306999921798706
    endloop
  endfacet
  facet normal 0.053709447383880615 0.12037945538759232 0.9912739396095276
    outer loop
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
      vertex -36 7.103000164031982 2.5
      vertex -37.28300094604492 6.572000026702881 2.634000062942505
    endloop
  endfacet
  facet normal -0.43619611859321594 -0.3372799754142761 0.8342512845993042
    outer loop
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
      vertex -93.28399658203125 -1.2020000219345093 3.6619999408721924
      vertex -94.12000274658203 -1.6890000104904175 3.0280001163482666
    endloop
  endfacet
  facet normal 0.22401359677314758 0.2633378803730011 0.9383342266082764
    outer loop
      vertex -37.28300094604492 6.572000026702881 2.634000062942505
      vertex -37.82600021362305 5.630000114440918 3.0280001163482666
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
    endloop
  endfacet
  facet normal 0.22828583419322968 0.29730871319770813 0.9270884990692139
    outer loop
      vertex -36.71900177001953 4.78000020980835 3.0280001163482666
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
      vertex -37.82600021362305 5.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal -0.9984588623046875 -0.012792868539690971 0.054002538323402405
    outer loop
      vertex -35 -63.10300064086914 3.5
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35.020999908447266 -60.9109992980957 3.63100004196167
    endloop
  endfacet
  facet normal 0.2784997522830963 0.6729879975318909 0.6852189898490906
    outer loop
      vertex -39.36600112915039 5.229000091552734 3.6619999408721924
      vertex -39.571998596191406 4.460000038146973 4.500999927520752
      vertex -38.310001373291016 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal 0.2787246108055115 0.672676146030426 0.6854337453842163
    outer loop
      vertex -39.571998596191406 4.460000038146973 4.500999927520752
      vertex -38.70800018310547 4.1020002365112305 4.500999927520752
      vertex -38.310001373291016 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal 0.44362279772758484 0.5774745345115662 0.685362696647644
    outer loop
      vertex -38.70800018310547 4.1020002365112305 4.500999927520752
      vertex -37.40399932861328 4.0960001945495605 3.6619999408721924
      vertex -38.310001373291016 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal -0.8569499850273132 -0.1573743373155594 0.4907851219177246
    outer loop
      vertex -35.0260009765625 -59.68000030517578 4.017000198364258
      vertex -35.27899932861328 -58.34600067138672 4.002999782562256
      vertex -35.020999908447266 -60.9109992980957 3.63100004196167
    endloop
  endfacet
  facet normal -0.3341374397277832 -0.4384072721004486 0.8343567848205566
    outer loop
      vertex -91.6760025024414 -2.7990000247955322 3.6619999408721924
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
      vertex -92.15699768066406 -3.6389999389648438 3.0280001163482666
    endloop
  endfacet
  facet normal -0.3341551423072815 -0.43830737471580505 0.8344021439552307
    outer loop
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
      vertex -91.6760025024414 -2.7990000247955322 3.6619999408721924
    endloop
  endfacet
  facet normal 0.3357890248298645 0.4371047019958496 0.834377110004425
    outer loop
      vertex -37.40399932861328 4.0960001945495605 3.6619999408721924
      vertex -36.71900177001953 4.78000020980835 3.0280001163482666
      vertex -38.310001373291016 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal -0.20803257822990417 -0.27295053005218506 0.9392659068107605
    outer loop
      vertex -92.15699768066406 -3.6389999389648438 3.0280001163482666
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal -0.9156789779663086 -0.12363388389348984 0.3824220597743988
    outer loop
      vertex -35 -56.999000549316406 4.946000099182129
      vertex -35.0260009765625 -59.68000030517578 4.017000198364258
      vertex -35.020999908447266 -60.9109992980957 3.63100004196167
    endloop
  endfacet
  facet normal -0.43617257475852966 -0.33700650930404663 0.8343740701675415
    outer loop
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
      vertex -92.58499908447266 -2.1059999465942383 3.6619999408721924
      vertex -94.12000274658203 -1.6890000104904175 3.0280001163482666
    endloop
  endfacet
  facet normal -0.27159249782562256 -0.20987620949745178 0.9392494559288025
    outer loop
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
    endloop
  endfacet
  facet normal -0.27159249782562256 -0.20987620949745178 0.9392494559288025
    outer loop
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal 0.33575916290283203 0.4372769296169281 0.8342989087104797
    outer loop
      vertex -38.310001373291016 4.791999816894531 3.6619999408721924
      vertex -36.71900177001953 4.78000020980835 3.0280001163482666
      vertex -37.82600021362305 5.630000114440918 3.0280001163482666
    endloop
  endfacet
  facet normal -0.27158287167549133 -0.20983712375164032 0.9392609596252441
    outer loop
      vertex -94.12000274658203 -1.6890000104904175 3.0280001163482666
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
      vertex -93.26699829101562 -2.7929999828338623 3.0280001163482666
    endloop
  endfacet
  facet normal 0.09488951414823532 0.7221792340278625 0.6851664781570435
    outer loop
      vertex -39.36600112915039 5.229000091552734 3.6619999408721924
      vertex -40.5 5.377999782562256 3.6619999408721924
      vertex -40.5 4.581999778747559 4.500999927520752
    endloop
  endfacet
  facet normal -0.06986494362354279 -0.5466833114624023 0.8344197273254395
    outer loop
      vertex -90.86599731445312 -4.169000148773193 3.0280001163482666
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
    endloop
  endfacet
  facet normal 0.09493660926818848 0.7221407890319824 0.6852005124092102
    outer loop
      vertex -40.5 4.581999778747559 4.500999927520752
      vertex -39.571998596191406 4.460000038146973 4.500999927520752
      vertex -39.36600112915039 5.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.21085025370121002 0.5093573331832886 0.8343244194984436
    outer loop
      vertex -37.82600021362305 5.630000114440918 3.0280001163482666
      vertex -39.11600112915039 6.164000034332275 3.0280001163482666
      vertex -39.36600112915039 5.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.21081587672233582 0.5094314813613892 0.8342878222465515
    outer loop
      vertex -37.82600021362305 5.630000114440918 3.0280001163482666
      vertex -39.36600112915039 5.229000091552734 3.6619999408721924
      vertex -38.310001373291016 4.791999816894531 3.6619999408721924
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
    endloop
  endfacet
  facet normal 0.500314474105835 0.07586073130369186 -0.862514078617096
    outer loop
      vertex -94.9990005493164 0 2.866046905517578
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
    endloop
  endfacet
  facet normal 0.27159249782562256 0.20987620949745178 -0.9392494559288025
    outer loop
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
    endloop
  endfacet
  facet normal 0.0718642920255661 0.5464845299720764 0.8343801498413086
    outer loop
      vertex -40.5 5.377999782562256 3.6619999408721924
      vertex -39.11600112915039 6.164000034332275 3.0280001163482666
      vertex -40.5 6.3460001945495605 3.0280001163482666
    endloop
  endfacet
  facet normal 0.27158287167549133 0.20983712375164032 -0.9392609596252441
    outer loop
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
    endloop
  endfacet
  facet normal 0.3165944218635559 0.13248787820339203 -0.9392629861831665
    outer loop
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
    endloop
  endfacet
  facet normal 0.07181254774332047 0.546546459197998 0.8343439698219299
    outer loop
      vertex -40.5 5.377999782562256 3.6619999408721924
      vertex -39.36600112915039 5.229000091552734 3.6619999408721924
      vertex -39.11600112915039 6.164000034332275 3.0280001163482666
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
    endloop
  endfacet
  facet normal -0.5328369736671448 -0.07332147657871246 0.8430354595184326
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 0 2.866046905517578
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 0 2.866046905517578
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
    endloop
  endfacet
  facet normal 0.23381000757217407 -0.2922804355621338 0.9273106455802917
    outer loop
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
      vertex -36.71900177001953 -60.779998779296875 3.0280001163482666
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
    endloop
  endfacet
  facet normal 0.44852784276008606 0.32319197058677673 0.8332884907722473
    outer loop
      vertex -37.40399932861328 4.0960001945495605 3.6619999408721924
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -36.71900177001953 4.78000020980835 3.0280001163482666
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 0 2.866046905517578
      vertex -94.9990005493164 16.384000778198242 0
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
    endloop
  endfacet
  facet normal 0.5777515769004822 0.4438253343105316 0.6849979758262634
    outer loop
      vertex -37.96699905395508 3.5329999923706055 4.500999927520752
      vertex -37.39699935913086 2.7909998893737793 4.500999927520752
      vertex -36.70800018310547 3.188999891281128 3.6619999408721924
    endloop
  endfacet
  facet normal 0.5777965784072876 0.44338083267211914 0.6852477788925171
    outer loop
      vertex -37.40399932861328 4.0960001945495605 3.6619999408721924
      vertex -37.96699905395508 3.5329999923706055 4.500999927520752
      vertex -36.70800018310547 3.188999891281128 3.6619999408721924
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 16.384000778198242 0
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -94.9990005493164 -2.2549498081207275 2.647404432296753
      vertex -94.9990005493164 16.384000778198242 0
    endloop
  endfacet
  facet normal -0.09131289273500443 -0.2980838119983673 0.9501621127128601
    outer loop
      vertex -35.819000244140625 -59.41899871826172 3.306999921798706
      vertex -35.98099899291992 -59.41400146484375 3.2929999828338623
      vertex -35.68299865722656 -60.707000732421875 2.9159998893737793
    endloop
  endfacet
  facet normal 0.4531416893005371 0.3477250337600708 0.8208227157592773
    outer loop
      vertex -36.70800018310547 3.188999891281128 3.6619999408721924
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -37.40399932861328 4.0960001945495605 3.6619999408721924
    endloop
  endfacet
  facet normal 0.13429638743400574 -0.3117847144603729 0.9406140446662903
    outer loop
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -35.82500076293945 -60.696998596191406 2.88100004196167
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
    endloop
  endfacet
  facet normal -0.500314474105835 -0.07586073130369186 0.862514078617096
    outer loop
      vertex -94.9990005493164 1 2.9539999961853027
      vertex -94.9990005493164 0 2.866046905517578
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
    endloop
  endfacet
  facet normal -0.500314474105835 -0.07586073130369186 0.862514078617096
    outer loop
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
      vertex -94.9990005493164 0 2.866046905517578
    endloop
  endfacet
  facet normal -0.010942515917122364 0.3380727469921112 0.9410563707351685
    outer loop
      vertex -36.06999969482422 2.7799999713897705 3.5309998989105225
      vertex -35.89799880981445 2.7799999713897705 3.5329999923706055
      vertex -35.8849983215332 4.175000190734863 3.0320000648498535
    endloop
  endfacet
  facet normal -0.5085601210594177 -0.21258296072483063 0.834371030330658
    outer loop
      vertex -93.28399658203125 -1.2020000219345093 3.6619999408721924
      vertex -93.7249984741211 -0.1469999998807907 3.6619999408721924
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
    endloop
  endfacet
  facet normal -0.5086621642112732 -0.21286405622959137 0.8342371582984924
    outer loop
      vertex -94.12000274658203 -1.6890000104904175 3.0280001163482666
      vertex -93.28399658203125 -1.2020000219345093 3.6619999408721924
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
    endloop
  endfacet
  facet normal -0.9298302531242371 0.1088915690779686 0.3515087068080902
    outer loop
      vertex -35.018001556396484 5.738999843597412 3.444999933242798
      vertex -35.20399856567383 4.296000003814697 3.4000000953674316
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
    endloop
  endfacet
  facet normal -0.8744515180587769 0.1748047173023224 0.4525238573551178
    outer loop
      vertex -35.20399856567383 4.296000003814697 3.4000000953674316
      vertex -35.257999420166016 2.8919999599456787 3.8380000591278076
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
    endloop
  endfacet
  facet normal -0.3165944218635559 -0.13248787820339203 0.9392629861831665
    outer loop
      vertex -94.65899658203125 -0.4009999930858612 3.0280001163482666
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
      vertex -94.12000274658203 -1.6890000104904175 3.0280001163482666
    endloop
  endfacet
  facet normal -0.3165944218635559 -0.13248787820339203 0.9392629861831665
    outer loop
      vertex -94.9990005493164 -2.20050311088562 2.6595680713653564
      vertex -94.12000274658203 -1.6890000104904175 3.0280001163482666
      vertex -94.9990005493164 -1.9568603038787842 2.6939351558685303
    endloop
  endfacet
  facet normal 0.18937385082244873 0.300734281539917 0.9347172975540161
    outer loop
      vertex -36.20899963378906 5.327000141143799 2.7269999980926514
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -35.8849983215332 4.175000190734863 3.0320000648498535
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
    endloop
  endfacet
  facet normal -0.9888328313827515 0.04647797718644142 0.14159582555294037
    outer loop
      vertex -35.018001556396484 5.738999843597412 3.444999933242798
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
      vertex -35 4.0289998054504395 4.131999969482422
    endloop
  endfacet
  facet normal 0.5197185277938843 0.3007798492908478 0.7996399998664856
    outer loop
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -36.70800018310547 3.188999891281128 3.6619999408721924
    endloop
  endfacet
  facet normal 0.09042646735906601 0.06987808644771576 -0.9934486150741577
    outer loop
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
    endloop
  endfacet
  facet normal -0.24786481261253357 -0.32339468598365784 0.913224458694458
    outer loop
      vertex -35.98099899291992 -59.41400146484375 3.2929999828338623
      vertex -35.82500076293945 -60.696998596191406 2.88100004196167
      vertex -35.68299865722656 -60.707000732421875 2.9159998893737793
    endloop
  endfacet
  facet normal -0.5328369736671448 -0.07332147657871246 0.8430354595184326
    outer loop
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
      vertex -95.05999755859375 -2.2360000610351562 2.634000062942505
    endloop
  endfacet
  facet normal 0.6782727837562561 0.2680622339248657 0.6841700673103333
    outer loop
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
      vertex -36.70800018310547 3.188999891281128 3.6619999408721924
      vertex -37.39699935913086 2.7909998893737793 4.500999927520752
    endloop
  endfacet
  facet normal 0.6811462640762329 0.28223422169685364 0.6755616664886475
    outer loop
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
      vertex -37.39699935913086 2.7909998893737793 4.500999927520752
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
    endloop
  endfacet
  facet normal 1 0 0
    outer loop
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
      vertex -94.9990005493164 -4.0960001945495605 2.51078462600708
      vertex -94.9990005493164 -4.21999979019165 2.5
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
    endloop
  endfacet
  facet normal -0.2092801183462143 -0.5097748041152954 0.8344647884368896
    outer loop
      vertex -90.61799621582031 -3.2330000400543213 3.6619999408721924
      vertex -92.15699768066406 -3.6389999389648438 3.0280001163482666
      vertex -90.86599731445312 -4.169000148773193 3.0280001163482666
    endloop
  endfacet
  facet normal -0.13043133914470673 -0.3177110552787781 0.9391737580299377
    outer loop
      vertex -92.15699768066406 -3.6389999389648438 3.0280001163482666
      vertex -92.6969985961914 -4.581999778747559 2.634000062942505
      vertex -90.86599731445312 -4.169000148773193 3.0280001163482666
    endloop
  endfacet
  facet normal -0.19229206442832947 0.3332815170288086 0.9230098724365234
    outer loop
      vertex -35.73500061035156 4.184000015258789 3.059999942779541
      vertex -35.8849983215332 4.175000190734863 3.0320000648498535
      vertex -35.89799880981445 2.7799999713897705 3.5329999923706055
    endloop
  endfacet
  facet normal -0.09042646735906601 -0.06987808644771576 0.9934486150741577
    outer loop
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
    endloop
  endfacet
  facet normal -0.37389957904815674 0.28247517347335815 0.883406400680542
    outer loop
      vertex -35.89799880981445 2.7799999713897705 3.5329999923706055
      vertex -35.426998138427734 2.1649999618530273 3.928999900817871
      vertex -35.38600158691406 2.8510000705718994 3.7269999980926514
    endloop
  endfacet
  facet normal -0.043529707938432693 -0.34061381220817566 0.9391950964927673
    outer loop
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
      vertex -90.86599731445312 -4.169000148773193 3.0280001163482666
      vertex -91.14299774169922 -5.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal -0.3741196393966675 0.33479389548301697 0.8648396134376526
    outer loop
      vertex -35.38600158691406 2.8510000705718994 3.7269999980926514
      vertex -35.73500061035156 4.184000015258789 3.059999942779541
      vertex -35.89799880981445 2.7799999713897705 3.5329999923706055
    endloop
  endfacet
  facet normal -0.6780441403388977 0.20913371443748474 0.7046411633491516
    outer loop
      vertex -35.257999420166016 2.8919999599456787 3.8380000591278076
      vertex -35.38600158691406 2.8510000705718994 3.7269999980926514
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
    endloop
  endfacet
  facet normal -0.060092490166425705 -0.20231077075004578 0.9774759411811829
    outer loop
      vertex -35.82500076293945 -60.696998596191406 2.88100004196167
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -35.70800018310547 -61.87200164794922 2.6449999809265137
    endloop
  endfacet
  facet normal -0.6788224577903748 0.2515423595905304 0.6898742318153381
    outer loop
      vertex -35.257999420166016 2.8919999599456787 3.8380000591278076
      vertex -35.30799865722656 4.260000228881836 3.2899999618530273
      vertex -35.38600158691406 2.8510000705718994 3.7269999980926514
    endloop
  endfacet
  facet normal -0.20802582800388336 -0.27327680587768555 0.9391725063323975
    outer loop
      vertex -92.6969985961914 -4.581999778747559 2.634000062942505
      vertex -92.15699768066406 -3.6389999389648438 3.0280001163482666
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
    endloop
  endfacet
  facet normal -0.4452815651893616 0.27730700373649597 0.8513666391372681
    outer loop
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.38600158691406 2.8510000705718994 3.7269999980926514
      vertex -35.426998138427734 2.1649999618530273 3.928999900817871
    endloop
  endfacet
  facet normal -0.4933954179286957 0.28246206045150757 0.8226640224456787
    outer loop
      vertex -35.30799865722656 4.260000228881836 3.2899999618530273
      vertex -35.73500061035156 4.184000015258789 3.059999942779541
      vertex -35.38600158691406 2.8510000705718994 3.7269999980926514
    endloop
  endfacet
  facet normal 0.679547905921936 -0.2653864026069641 0.6839479207992554
    outer loop
      vertex -37.39699935913086 -58.79100036621094 4.500999927520752
      vertex -36.70800018310547 -59.18899917602539 3.6619999408721924
      vertex -36.667999267578125 -58.316001892089844 3.9609999656677246
    endloop
  endfacet
  facet normal -0.8826327919960022 0.1490854173898697 0.44579464197158813
    outer loop
      vertex -35.257999420166016 2.8919999599456787 3.8380000591278076
      vertex -35.30500030517578 1.621000051498413 4.170000076293945
      vertex -35.03099822998047 2.684000015258789 4.35699987411499
    endloop
  endfacet
  facet normal 0.5777515769004822 -0.4438253343105316 0.6849979758262634
    outer loop
      vertex -37.39699935913086 -58.79100036621094 4.500999927520752
      vertex -37.96699905395508 -59.53300094604492 4.500999927520752
      vertex -36.70800018310547 -59.18899917602539 3.6619999408721924
    endloop
  endfacet
  facet normal -0.07283392548561096 -0.09567957371473312 0.992743968963623
    outer loop
      vertex -94.03299713134766 -3.565000057220459 2.634000062942505
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -92.6969985961914 -4.581999778747559 2.634000062942505
    endloop
  endfacet
  facet normal -0.7437066435813904 0.22498908638954163 0.6295080184936523
    outer loop
      vertex -35.20399856567383 4.296000003814697 3.4000000953674316
      vertex -35.30799865722656 4.260000228881836 3.2899999618530273
      vertex -35.257999420166016 2.8919999599456787 3.8380000591278076
    endloop
  endfacet
  facet normal 0.34875234961509705 0.3591412603855133 0.865672767162323
    outer loop
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
      vertex -36.06999969482422 2.7799999713897705 3.5309998989105225
    endloop
  endfacet
  facet normal -0.1304338276386261 -0.3177024722099304 0.9391763210296631
    outer loop
      vertex -90.86599731445312 -4.169000148773193 3.0280001163482666
      vertex -92.6969985961914 -4.581999778747559 2.634000062942505
      vertex -91.14299774169922 -5.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal -0.9236428737640381 0.3832542896270752 0
    outer loop
      vertex -39.63399887084961 -57.5 5.5
      vertex -39.534000396728516 -57.25899887084961 0
      vertex -39.63399887084961 -57.5 0
    endloop
  endfacet
  facet normal -0.07723027467727661 -0.1660664677619934 0.9830856323242188
    outer loop
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -89.947998046875 -6.568999767303467 2.5
      vertex -91.14299774169922 -5.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal 0.7565125226974487 0.1551235318183899 0.6353152990341187
    outer loop
      vertex -37.03900146484375 1.9270000457763672 4.500999927520752
      vertex -36.742000579833984 1.6540000438690186 4.214000225067139
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
    endloop
  endfacet
  facet normal -0.794902503490448 0.6067371964454651 0
    outer loop
      vertex -39.79199981689453 -57.707000732421875 5.5
      vertex -39.63399887084961 -57.5 5.5
      vertex -39.63399887084961 -57.5 0
    endloop
  endfacet
  facet normal -0.794902503490448 0.6067371964454651 0
    outer loop
      vertex -39.79199981689453 -57.707000732421875 5.5
      vertex -39.63399887084961 -57.5 0
      vertex -39.79199981689453 -57.707000732421875 0
    endloop
  endfacet
  facet normal -0.6073083281517029 0.7944662570953369 0
    outer loop
      vertex -39.79199981689453 -57.707000732421875 0
      vertex -40 -57.86600112915039 0
      vertex -39.79199981689453 -57.707000732421875 5.5
    endloop
  endfacet
  facet normal -0.6073083281517029 0.7944662570953369 0
    outer loop
      vertex -40 -57.86600112915039 5.5
      vertex -39.79199981689453 -57.707000732421875 5.5
      vertex -40 -57.86600112915039 0
    endloop
  endfacet
  facet normal -0.31039074063301086 0.21961577236652374 0.9248927235603333
    outer loop
      vertex -35.45500183105469 1.5989999771118164 4.053999900817871
      vertex -35.426998138427734 2.1649999618530273 3.928999900817871
      vertex -35.97999954223633 2.111999988555908 3.75600004196167
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -40 -57.86600112915039 0
      vertex -40.24100112915039 -57.965999603271484 5.5
      vertex -40 -57.86600112915039 5.5
    endloop
  endfacet
  facet normal -0.0915655717253685 -0.22302962839603424 0.9705016613006592
    outer loop
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -91.14299774169922 -5.21999979019165 2.634000062942505
      vertex -92.6969985961914 -4.581999778747559 2.634000062942505
    endloop
  endfacet
  facet normal -0.31041207909584045 0.33507779240608215 0.8895882368087769
    outer loop
      vertex -35.426998138427734 2.1649999618530273 3.928999900817871
      vertex -35.89799880981445 2.7799999713897705 3.5329999923706055
      vertex -35.97999954223633 2.111999988555908 3.75600004196167
    endloop
  endfacet
  facet normal -0.26723554730415344 0.26474350690841675 0.9265506267547607
    outer loop
      vertex -35.45500183105469 1.5989999771118164 4.053999900817871
      vertex -35.97999954223633 2.111999988555908 3.75600004196167
      vertex -36.0359992980957 1.569000005722046 3.8949999809265137
    endloop
  endfacet
  facet normal -0.043734993785619736 -0.3402746021747589 0.9393085241317749
    outer loop
      vertex -89.48100280761719 -4.3460001945495605 3.0280001163482666
      vertex -91.14299774169922 -5.21999979019165 2.634000062942505
      vertex -89.47799682617188 -5.434000015258789 2.634000062942505
    endloop
  endfacet
  facet normal -0.011024143546819687 0.3178517818450928 0.9480763077735901
    outer loop
      vertex -35.89799880981445 2.7799999713897705 3.5329999923706055
      vertex -36.06999969482422 2.7799999713897705 3.5309998989105225
      vertex -35.97999954223633 2.111999988555908 3.75600004196167
    endloop
  endfacet
  facet normal 0.13065332174301147 0.9914281368255615 0
    outer loop
      vertex -40.5 -58 5.5
      vertex -40.5 -58 0
      vertex -40.757999420166016 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal -0.014316339045763016 -0.11138647049665451 0.9936740398406982
    outer loop
      vertex -89.947998046875 -6.568999767303467 2.5
      vertex -89.47799682617188 -5.434000015258789 2.634000062942505
      vertex -91.14299774169922 -5.21999979019165 2.634000062942505
    endloop
  endfacet
  facet normal 0.3819020092487335 0.9242027997970581 0
    outer loop
      vertex -40.757999420166016 -57.965999603271484 0
      vertex -41 -57.86600112915039 0
      vertex -40.757999420166016 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal 0.43794217705726624 0.2739837169647217 0.856235682964325
    outer loop
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
      vertex -36.742000579833984 1.6540000438690186 4.214000225067139
      vertex -36.1609992980957 2.115999937057495 3.7690000534057617
    endloop
  endfacet
  facet normal 0.43259090185165405 0.251089483499527 0.8659210205078125
    outer loop
      vertex -36.06999969482422 2.7799999713897705 3.5309998989105225
      vertex -36.667999267578125 2.316999912261963 3.9639999866485596
      vertex -36.1609992980957 2.115999937057495 3.7690000534057617
    endloop
  endfacet
  facet normal 0.4435596466064453 -0.577640950679779 0.6852633357048035
    outer loop
      vertex -37.40399932861328 -60.09600067138672 3.6619999408721924
      vertex -37.96699905395508 -59.53300094604492 4.500999927520752
      vertex -38.70800018310547 -60.10200119018555 4.500999927520752
    endloop
  endfacet
  facet normal 0.44362279772758484 -0.5774745345115662 0.685362696647644
    outer loop
      vertex -37.40399932861328 -60.09600067138672 3.6619999408721924
      vertex -38.70800018310547 -60.10200119018555 4.500999927520752
      vertex -38.310001373291016 -60.79199981689453 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -89.947998046875 -6.568999767303467 2.5
      vertex -94.9990005493164 -4.21999979019165 2.5
    endloop
  endfacet
  facet normal 0.18152017891407013 0.30978161096572876 0.9333197474479675
    outer loop
      vertex -35.8849983215332 4.175000190734863 3.0320000648498535
      vertex -36.446998596191406 3.7269999980926514 3.2899999618530273
      vertex -36.06999969482422 2.7799999713897705 3.5309998989105225
    endloop
  endfacet
  facet normal 0.5777965784072876 -0.44338083267211914 0.6852477788925171
    outer loop
      vertex -37.40399932861328 -60.09600067138672 3.6619999408721924
      vertex -36.70800018310547 -59.18899917602539 3.6619999408721924
      vertex -37.96699905395508 -59.53300094604492 4.500999927520752
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -4.21999979019165 2.5
      vertex -94.9990005493164 -4.0960001945495605 2.5087220668792725
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -3.929617404937744 2.5204250812530518
      vertex -94.9990005493164 -2.3149375915527344 2.634000062942505
      vertex -94.9990005493164 -8.192000389099121 0
    endloop
  endfacet
  facet normal 0.07482068240642548 0.2400451898574829 0.9678740501403809
    outer loop
      vertex -36.0359992980957 1.569000005722046 3.8949999809265137
      vertex -35.97999954223633 2.111999988555908 3.75600004196167
      vertex -36.1609992980957 2.115999937057495 3.7690000534057617
    endloop
  endfacet
  facet normal 0.0748867392539978 0.3273560106754303 0.9419288635253906
    outer loop
      vertex -35.97999954223633 2.111999988555908 3.75600004196167
      vertex -36.06999969482422 2.7799999713897705 3.5309998989105225
      vertex -36.1609992980957 2.115999937057495 3.7690000534057617
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -94.9990005493164 -8.192000389099121 0
      vertex -94.9990005493164 -32.768001556396484 2.5
      vertex -94.9990005493164 -4.21999979019165 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.15499877929688 -49.85200119018555 2.5
      vertex -46.54100036621094 -3.5820000171661377 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0.134240061044693 0.2514669597148895 0.9585113525390625
    outer loop
      vertex -36.22200012207031 1.5729999542236328 3.9200000762939453
      vertex -36.0359992980957 1.569000005722046 3.8949999809265137
      vertex -36.1609992980957 2.115999937057495 3.7690000534057617
    endloop
  endfacet
  facet normal 0.5051749348640442 0.17807641625404358 0.8444448113441467
    outer loop
      vertex -36.742000579833984 1.6540000438690186 4.214000225067139
      vertex -36.22200012207031 1.5729999542236328 3.9200000762939453
      vertex -36.1609992980957 2.115999937057495 3.7690000534057617
    endloop
  endfacet
  facet normal 0.3357890248298645 -0.4371047019958496 0.834377110004425
    outer loop
      vertex -36.71900177001953 -60.779998779296875 3.0280001163482666
      vertex -37.40399932861328 -60.09600067138672 3.6619999408721924
      vertex -38.310001373291016 -60.79199981689453 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -84.65499877929688 -51.16699981689453 2.5
      vertex -46.54100036621094 -3.5820000171661377 2.5
      vertex -87.15499877929688 -49.85200119018555 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.87999725341797 -49.60499954223633 2.5
      vertex -87.15499877929688 -49.85200119018555 2.5
      vertex -94.9990005493164 -32.768001556396484 2.5
    endloop
  endfacet
  facet normal 0.45197242498397827 -0.34682780504226685 0.8218463063240051
    outer loop
      vertex -36.446998596191406 -59.72800064086914 3.2909998893737793
      vertex -36.70800018310547 -59.18899917602539 3.6619999408721924
      vertex -37.40399932861328 -60.09600067138672 3.6619999408721924
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -92.9990005493164 -84 2.5
      vertex -47.02799987792969 -60.72999954223633 2.5
      vertex -85.4540023803711 -63.34299850463867 2.5
    endloop
  endfacet
  facet normal -0.09747490286827087 0.7218239307403564 0.6851779222488403
    outer loop
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
      vertex -89.51399993896484 -52.62200164794922 3.6619999408721924
      vertex -90.64700317382812 -52.775001525878906 3.6619999408721924
    endloop
  endfacet
  facet normal 0.09488951414823532 -0.7221792340278625 0.6851664781570435
    outer loop
      vertex -40.5 -61.37799835205078 3.6619999408721924
      vertex -39.36600112915039 -61.229000091552734 3.6619999408721924
      vertex -40.5 -60.582000732421875 4.500999927520752
    endloop
  endfacet
  facet normal 0.09493660926818848 -0.7221407890319824 0.6852005124092102
    outer loop
      vertex -39.571998596191406 -60.459999084472656 4.500999927520752
      vertex -40.5 -60.582000732421875 4.500999927520752
      vertex -39.36600112915039 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.07181254774332047 -0.546546459197998 0.8343439698219299
    outer loop
      vertex -39.36600112915039 -61.229000091552734 3.6619999408721924
      vertex -40.5 -61.37799835205078 3.6619999408721924
      vertex -39.11600112915039 -62.16400146484375 3.0280001163482666
    endloop
  endfacet
  facet normal 0.2784997522830963 -0.6729879975318909 0.6852189898490906
    outer loop
      vertex -38.310001373291016 -60.79199981689453 3.6619999408721924
      vertex -39.571998596191406 -60.459999084472656 4.500999927520752
      vertex -39.36600112915039 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.21081587672233582 -0.5094314813613892 0.8342878222465515
    outer loop
      vertex -37.82600021362305 -61.630001068115234 3.0280001163482666
      vertex -38.310001373291016 -60.79199981689453 3.6619999408721924
      vertex -39.36600112915039 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.21085025370121002 -0.5093573331832886 0.8343244194984436
    outer loop
      vertex -39.11600112915039 -62.16400146484375 3.0280001163482666
      vertex -37.82600021362305 -61.630001068115234 3.0280001163482666
      vertex -39.36600112915039 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.22828583419322968 -0.29730871319770813 0.9270884990692139
    outer loop
      vertex -37.82600021362305 -61.630001068115234 3.0280001163482666
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -36.71900177001953 -60.779998779296875 3.0280001163482666
    endloop
  endfacet
  facet normal -0.09497250616550446 -0.7221735119819641 0.6851610541343689
    outer loop
      vertex -40.5 -61.37799835205078 3.6619999408721924
      vertex -40.5 -60.582000732421875 4.500999927520752
      vertex -41.632999420166016 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3832542896270752 0.9236428737640381 0
    outer loop
      vertex -40 -57.86600112915039 0
      vertex -40.24100112915039 -57.965999603271484 0
      vertex -40.24100112915039 -57.965999603271484 5.5
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -40.24100112915039 -57.965999603271484 5.5
      vertex -40.24100112915039 -57.965999603271484 0
      vertex -40.5 -58 0
    endloop
  endfacet
  facet normal -0.13015742599964142 0.9914933443069458 0
    outer loop
      vertex -40.24100112915039 -57.965999603271484 5.5
      vertex -40.5 -58 0
      vertex -40.5 -58 5.5
    endloop
  endfacet
  facet normal 0.13065332174301147 0.9914281368255615 0
    outer loop
      vertex -40.757999420166016 -57.965999603271484 0
      vertex -40.757999420166016 -57.965999603271484 5.5
      vertex -40.5 -58 0
    endloop
  endfacet
  facet normal 0.6721398830413818 0.2811616361141205 0.6849642992019653
    outer loop
      vertex -86.40299987792969 -55.198001861572266 4.500999927520752
      vertex -86.04199981689453 -56.06100082397461 4.500999927520752
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
    endloop
  endfacet
  facet normal 0.6721056699752808 0.2809465229511261 0.685086190700531
    outer loop
      vertex -86.40299987792969 -55.198001861572266 4.500999927520752
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
      vertex -85.71499633789062 -54.79800033569336 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7992205023765564 0.3343205153942108 0.4994760751724243
    outer loop
      vertex -86.9010009765625 -55.5 5.5
      vertex -86.04199981689453 -56.06100082397461 4.500999927520752
      vertex -86.40299987792969 -55.198001861572266 4.500999927520752
    endloop
  endfacet
  facet normal -0.9914817810058594 -0.0048257033340632915 0.13015590608119965
    outer loop
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
      vertex -35 -63.10300064086914 3.5
      vertex -35.018001556396484 -61.99399948120117 3.4040000438690186
    endloop
  endfacet
  facet normal 0.5761100649833679 0.44592010974884033 0.6850200295448303
    outer loop
      vertex -86.40299987792969 -55.198001861572266 4.500999927520752
      vertex -85.71499633789062 -54.79800033569336 3.6619999408721924
      vertex -86.9749984741211 -54.45899963378906 4.500999927520752
    endloop
  endfacet
  facet normal 0.5761542916297913 0.44549983739852905 0.6852562427520752
    outer loop
      vertex -85.71499633789062 -54.79800033569336 3.6619999408721924
      vertex -86.41400146484375 -53.89400100708008 3.6619999408721924
      vertex -86.9749984741211 -54.45899963378906 4.500999927520752
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 -63.10300064086914 3.5
      vertex -35 -65.53600311279297 10.5
      vertex -35 -56.999000549316406 4.946000099182129
    endloop
  endfacet
  facet normal -0.9288679361343384 -0.0912163257598877 0.35900402069091797
    outer loop
      vertex -35.018001556396484 -61.99399948120117 3.4040000438690186
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
      vertex -35.15800094604492 -61.9379997253418 3.055999994277954
    endloop
  endfacet
  facet normal 0.6861675977706909 0.5270562767982483 0.5013838410377502
    outer loop
      vertex -86.40299987792969 -55.198001861572266 4.500999927520752
      vertex -87.37799835205078 -54.87900161743164 5.5
      vertex -86.9010009765625 -55.5 5.5
    endloop
  endfacet
  facet normal -0.9988933801651001 -0.012282892130315304 0.04539952054619789
    outer loop
      vertex -35 -63.10300064086914 3.5
      vertex -35.020999908447266 -60.9109992980957 3.63100004196167
      vertex -35.018001556396484 -61.99399948120117 3.4040000438690186
    endloop
  endfacet
  facet normal 0.44145017862319946 0.5792573690414429 0.6852610111236572
    outer loop
      vertex -87.71900177001953 -53.891998291015625 4.500999927520752
      vertex -86.9749984741211 -54.45899963378906 4.500999927520752
      vertex -86.41400146484375 -53.89400100708008 3.6619999408721924
    endloop
  endfacet
  facet normal -0.9150784015655518 -0.08515667170286179 0.39418256282806396
    outer loop
      vertex -35.018001556396484 -61.99399948120117 3.4040000438690186
      vertex -35.020999908447266 -60.9109992980957 3.63100004196167
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
    endloop
  endfacet
  facet normal 0.6851438283920288 0.5303142666816711 0.4993442893028259
    outer loop
      vertex -86.40299987792969 -55.198001861572266 4.500999927520752
      vertex -86.9749984741211 -54.45899963378906 4.500999927520752
      vertex -87.37799835205078 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal 0.053709447383880615 -0.12037945538759232 0.9912739396095276
    outer loop
      vertex -37.28300094604492 -62.571998596191406 2.634000062942505
      vertex -36 -63.10300064086914 2.5
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
    endloop
  endfacet
  facet normal -0.9292193055152893 -0.04057837277650833 0.3672940135002136
    outer loop
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
      vertex -35.018001556396484 -61.99399948120117 3.4040000438690186
      vertex -35.15800094604492 -61.9379997253418 3.055999994277954
    endloop
  endfacet
  facet normal 0.4415043294429779 0.5791160464286804 0.6853455305099487
    outer loop
      vertex -87.71900177001953 -53.891998291015625 4.500999927520752
      vertex -86.41400146484375 -53.89400100708008 3.6619999408721924
      vertex -87.322998046875 -53.20100021362305 3.6619999408721924
    endloop
  endfacet
  facet normal 0.527132511138916 0.6862668991088867 0.5011676549911499
    outer loop
      vertex -86.9749984741211 -54.45899963378906 4.500999927520752
      vertex -87.9990005493164 -54.402000427246094 5.5
      vertex -87.37799835205078 -54.87900161743164 5.5
    endloop
  endfacet
  facet normal -0.802459180355072 -0.04207196831703186 0.5952219367027283
    outer loop
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
      vertex -35.15800094604492 -61.9379997253418 3.055999994277954
      vertex -35.23899841308594 -61.92100143432617 2.947999954223633
    endloop
  endfacet
  facet normal -0.8029491305351257 -0.12922383844852448 0.5818710327148438
    outer loop
      vertex -35.23899841308594 -61.92100143432617 2.947999954223633
      vertex -35.15800094604492 -61.9379997253418 3.055999994277954
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
    endloop
  endfacet
  facet normal 0.5252557396888733 0.6892244815826416 0.49907517433166504
    outer loop
      vertex -86.9749984741211 -54.45899963378906 4.500999927520752
      vertex -87.71900177001953 -53.891998291015625 4.500999927520752
      vertex -87.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.7625980973243713 -0.1449187695980072 0.6304305791854858
    outer loop
      vertex -35.1879997253418 -60.805999755859375 3.2660000324249268
      vertex -35.284000396728516 -60.775001525878906 3.1570000648498535
      vertex -35.23899841308594 -61.92100143432617 2.947999954223633
    endloop
  endfacet
  facet normal -0.5306309461593628 -0.17219312489032745 0.829927921295166
    outer loop
      vertex -35.68299865722656 -60.707000732421875 2.9159998893737793
      vertex -35.23899841308594 -61.92100143432617 2.947999954223633
      vertex -35.284000396728516 -60.775001525878906 3.1570000648498535
    endloop
  endfacet
  facet normal 0.2764846384525299 0.6736879348754883 0.6853471994400024
    outer loop
      vertex -87.322998046875 -53.20100021362305 3.6619999408721924
      vertex -88.58399963378906 -53.5369987487793 4.500999927520752
      vertex -87.71900177001953 -53.891998291015625 4.500999927520752
    endloop
  endfacet
  facet normal -0.1288638859987259 -0.14063329994678497 0.9816396236419678
    outer loop
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -36 -63.10300064086914 2.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -87.9990005493164 -54.402000427246094 5.5
      vertex -88.7229995727539 -54.10200119018555 5.5
      vertex -89.23999786376953 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -88.7229995727539 -54.10200119018555 5.5
      vertex -89.4990005493164 -54 5.5
      vertex -89.23999786376953 -56.034000396728516 5.5
    endloop
  endfacet
  facet normal 0.3312917649745941 0.7995174527168274 0.5010166168212891
    outer loop
      vertex -87.71900177001953 -53.891998291015625 4.500999927520752
      vertex -88.7229995727539 -54.10200119018555 5.5
      vertex -87.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal -0.3493123948574066 -0.21782536804676056 0.911335825920105
    outer loop
      vertex -35.70800018310547 -61.87200164794922 2.6449999809265137
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
      vertex -35.82500076293945 -60.696998596191406 2.88100004196167
    endloop
  endfacet
  facet normal -0.6016197800636292 -0.1996452957391739 0.7734309434890747
    outer loop
      vertex -35.23899841308594 -61.92100143432617 2.947999954223633
      vertex -35.68299865722656 -60.707000732421875 2.9159998893737793
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
    endloop
  endfacet
  facet normal -0.24778452515602112 -0.2028394341468811 0.947343111038208
    outer loop
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
      vertex -35.68299865722656 -60.707000732421875 2.9159998893737793
      vertex -35.82500076293945 -60.696998596191406 2.88100004196167
    endloop
  endfacet
  facet normal 0.3289930522441864 0.801630973815918 0.49915066361427307
    outer loop
      vertex -88.58399963378906 -53.5369987487793 4.500999927520752
      vertex -88.7229995727539 -54.10200119018555 5.5
      vertex -87.71900177001953 -53.891998291015625 4.500999927520752
    endloop
  endfacet
  facet normal 0.06332989782094955 -0.09130986034870148 0.9938067197799683
    outer loop
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
      vertex -35.70800018310547 -61.87200164794922 2.6449999809265137
    endloop
  endfacet
  facet normal 0.05048352852463722 -0.1279764473438263 0.990491509437561
    outer loop
      vertex -37.28300094604492 -62.571998596191406 2.634000062942505
      vertex -39.619998931884766 -64.53099822998047 2.5
      vertex -36 -63.10300064086914 2.5
    endloop
  endfacet
  facet normal 0.09238508343696594 0.7225150465965271 0.6851547360420227
    outer loop
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -89.51399993896484 -52.62200164794922 3.6619999408721924
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
    endloop
  endfacet
  facet normal 0.09271565079689026 0.7222471237182617 0.6853924989700317
    outer loop
      vertex -88.58399963378906 -53.5369987487793 4.500999927520752
      vertex -88.37999725341797 -52.766998291015625 3.6619999408721924
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
    endloop
  endfacet
  facet normal 0.1127878800034523 0.8580725193023682 0.5009894967079163
    outer loop
      vertex -88.58399963378906 -53.5369987487793 4.500999927520752
      vertex -89.4990005493164 -54 5.5
      vertex -88.7229995727539 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal -0.9229958057403564 -0.03742412477731705 0.38298583030700684
    outer loop
      vertex -35.13399887084961 -63.10300064086914 3
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
      vertex -35.15800094604492 -61.9379997253418 3.055999994277954
    endloop
  endfacet
  facet normal -0.7940794825553894 -0.04549357295036316 0.6061089634895325
    outer loop
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
      vertex -35.13399887084961 -63.10300064086914 3
      vertex -35.15800094604492 -61.9379997253418 3.055999994277954
    endloop
  endfacet
  facet normal 0.11031737178564072 0.8593630194664001 0.4993247985839844
    outer loop
      vertex -88.58399963378906 -53.5369987487793 4.500999927520752
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
      vertex -89.4990005493164 -54 5.5
    endloop
  endfacet
  facet normal -0.6054578423500061 -0.07800457626581192 0.7920454740524292
    outer loop
      vertex -35.5 -63.10300064086914 2.634000062942505
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
    endloop
  endfacet
  facet normal -0.0973474532365799 0.7219287157058716 0.685085654258728
    outer loop
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
      vertex -90.64700317382812 -52.775001525878906 3.6619999408721924
      vertex -90.43800354003906 -53.542999267578125 4.500999927520752
    endloop
  endfacet
  facet normal -0.602609395980835 -0.07713884115219116 0.7942993640899658
    outer loop
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
      vertex -35.23899841308594 -61.92100143432617 2.947999954223633
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
    endloop
  endfacet
  facet normal -0.11262979358434677 0.8579740524291992 0.501193642616272
    outer loop
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
      vertex -90.2760009765625 -54.10200119018555 5.5
      vertex -89.4990005493164 -54 5.5
    endloop
  endfacet
  facet normal -0.11578762531280518 0.8586810231208801 0.4992595613002777
    outer loop
      vertex -89.51100158691406 -53.417999267578125 4.500999927520752
      vertex -90.43800354003906 -53.542999267578125 4.500999927520752
      vertex -90.2760009765625 -54.10200119018555 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.4990005493164 -56 5.5
      vertex -89.23999786376953 -56.034000396728516 5.5
      vertex -89.4990005493164 -54 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -89.23999786376953 -56.034000396728516 5.5
      vertex -88.9990005493164 -56.13399887084961 5.5
      vertex -87.9990005493164 -54.402000427246094 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -90.2760009765625 -54.10200119018555 5.5
      vertex -89.75800323486328 -56.034000396728516 5.5
      vertex -89.4990005493164 -54 5.5
    endloop
  endfacet
  facet normal -0.3486056327819824 -0.0748986303806305 0.934272050857544
    outer loop
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
      vertex -35.70800018310547 -61.87200164794922 2.6449999809265137
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
    endloop
  endfacet
  facet normal 0.858024001121521 -0.11278150230646133 0.5010740160942078
    outer loop
      vertex -86.4990005493164 -57 5.5
      vertex -86.60099792480469 -57.7760009765625 5.5
      vertex -86.03600311279297 -57.91600036621094 4.500999927520752
    endloop
  endfacet
  facet normal -0.38234367966651917 -0.06889376789331436 0.921448290348053
    outer loop
      vertex -35.5 -63.10300064086914 2.634000062942505
      vertex -35.58300018310547 -61.880001068115234 2.690999984741211
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
    endloop
  endfacet
  facet normal 0.8593736886978149 -0.11019986122846603 0.4993324279785156
    outer loop
      vertex -85.91699981689453 -56.987998962402344 4.500999927520752
      vertex -86.4990005493164 -57 5.5
      vertex -86.03600311279297 -57.91600036621094 4.500999927520752
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex -35 -82 3.5
      vertex -35 -65.53600311279297 10.5
      vertex -35 -63.10300064086914 3.5
    endloop
  endfacet
  facet normal -0.9914933443069458 0 0.13015742599964142
    outer loop
      vertex -35 -63.10300064086914 3.5
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
      vertex -35 -82 3.5
    endloop
  endfacet
  facet normal -0.9914933443069458 0 0.13015742599964142
    outer loop
      vertex -35.034000396728516 -82 3.240999937057495
      vertex -35 -82 3.5
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
    endloop
  endfacet
  facet normal -0.9236428737640381 0 0.3832542896270752
    outer loop
      vertex -35.13399887084961 -63.10300064086914 3
      vertex -35.13399887084961 -82 3
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
    endloop
  endfacet
  facet normal -0.9236428737640381 0 0.3832542896270752
    outer loop
      vertex -35.13399887084961 -82 3
      vertex -35.034000396728516 -82 3.240999937057495
      vertex -35.034000396728516 -63.10300064086914 3.240999937057495
    endloop
  endfacet
  facet normal 0.8579592704772949 0.11277299374341965 0.501186728477478
    outer loop
      vertex -85.91699981689453 -56.987998962402344 4.500999927520752
      vertex -86.60099792480469 -56.2239990234375 5.5
      vertex -86.4990005493164 -57 5.5
    endloop
  endfacet
  facet normal -0.794902503490448 0 0.6067371964454651
    outer loop
      vertex -35.13399887084961 -82 3
      vertex -35.13399887084961 -63.10300064086914 3
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
    endloop
  endfacet
  facet normal -0.6073083281517029 0 0.7944662570953369
    outer loop
      vertex -35.5 -82 2.634000062942505
      vertex -35.29199981689453 -63.10300064086914 2.7929999828338623
      vertex -35.5 -63.10300064086914 2.634000062942505
    endloop
  endfacet
  facet normal 0.7219421863555908 0.09757699072360992 0.6850388646125793
    outer loop
      vertex -86.04199981689453 -56.06100082397461 4.500999927520752
      vertex -85.12100219726562 -56.98500061035156 3.6619999408721924
      vertex -85.27400207519531 -55.85300064086914 3.6619999408721924
    endloop
  endfacet
  facet normal 0.7218341827392578 0.09733470529317856 0.6851871013641357
    outer loop
      vertex -86.04199981689453 -56.06100082397461 4.500999927520752
      vertex -85.91699981689453 -56.987998962402344 4.500999927520752
      vertex -85.12100219726562 -56.98500061035156 3.6619999408721924
    endloop
  endfacet
  facet normal -0.3832542896270752 0 0.9236428737640381
    outer loop
      vertex -35.74100112915039 -82 2.5339999198913574
      vertex -35.5 -82 2.634000062942505
      vertex -35.5 -63.10300064086914 2.634000062942505
    endloop
  endfacet
  facet normal -0.3832542896270752 0 0.9236428737640381
    outer loop
      vertex -35.74100112915039 -82 2.5339999198913574
      vertex -35.5 -63.10300064086914 2.634000062942505
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
    endloop
  endfacet
  facet normal -0.13015742599964142 0 0.9914933443069458
    outer loop
      vertex -36 -63.10300064086914 2.5
      vertex -36 -82 2.5
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
    endloop
  endfacet
  facet normal -0.13015742599964142 0 0.9914933443069458
    outer loop
      vertex -35.74100112915039 -82 2.5339999198913574
      vertex -35.74100112915039 -63.10300064086914 2.5339999198913574
      vertex -36 -82 2.5
    endloop
  endfacet
  facet normal 0.8586313724517822 0.11578092724084854 0.4993465542793274
    outer loop
      vertex -85.91699981689453 -56.987998962402344 4.500999927520752
      vertex -86.04199981689453 -56.06100082397461 4.500999927520752
      vertex -86.60099792480469 -56.2239990234375 5.5
    endloop
  endfacet
  facet normal 0 0 1
    outer loop
      vertex -36 -63.10300064086914 2.5
      vertex -39.619998931884766 -64.53099822998047 2.5
      vertex -36 -82 2.5
    endloop
  endfacet
  facet normal 0.33575916290283203 -0.4372769296169281 0.8342989087104797
    outer loop
      vertex -36.71900177001953 -60.779998779296875 3.0280001163482666
      vertex -38.310001373291016 -60.79199981689453 3.6619999408721924
      vertex -37.82600021362305 -61.630001068115234 3.0280001163482666
    endloop
  endfacet
  facet normal 0.22401359677314758 -0.2633378803730011 0.9383342266082764
    outer loop
      vertex -36.20899963378906 -61.32699966430664 2.7269999980926514
      vertex -37.82600021362305 -61.630001068115234 3.0280001163482666
      vertex -37.28300094604492 -62.571998596191406 2.634000062942505
    endloop
  endfacet
  facet normal -0.044944703578948975 -0.3401497006416321 0.9392966032028198
    outer loop
      vertex -42.165000915527344 -63.2140007019043 2.634000062942505
      vertex -40.5 -63.433998107910156 2.634000062942505
      vertex -40.5 -62.34600067138672 3.0280001163482666
    endloop
  endfacet
  facet normal 0.014495695941150188 -0.10977195203304291 0.9938510656356812
    outer loop
      vertex -39.619998931884766 -64.53099822998047 2.5
      vertex -38.83399963378906 -63.2140007019043 2.634000062942505
      vertex -40.5 -63.433998107910156 2.634000062942505
    endloop
  endfacet
  facet normal -0.07191598415374756 -0.5464824438095093 0.8343769907951355
    outer loop
      vertex -40.5 -61.37799835205078 3.6619999408721924
      vertex -41.882999420166016 -62.16400146484375 3.0280001163482666
      vertex -40.5 -62.34600067138672 3.0280001163482666
    endloop
  endfacet
  facet normal 0.05534426122903824 -0.1337055265903473 0.9894745349884033
    outer loop
      vertex -37.28300094604492 -62.571998596191406 2.634000062942505
      vertex -38.83399963378906 -63.2140007019043 2.634000062942505
      vertex -39.619998931884766 -64.53099822998047 2.5
    endloop
  endfacet
  facet normal 0.0718642920255661 -0.5464845299720764 0.8343801498413086
    outer loop
      vertex -39.11600112915039 -62.16400146484375 3.0280001163482666
      vertex -40.5 -61.37799835205078 3.6619999408721924
      vertex -40.5 -62.34600067138672 3.0280001163482666
    endloop
  endfacet
  facet normal -0.07187410444021225 -0.5465325713157654 0.8343477845191956
    outer loop
      vertex -41.882999420166016 -62.16400146484375 3.0280001163482666
      vertex -40.5 -61.37799835205078 3.6619999408721924
      vertex -41.632999420166016 -61.229000091552734 3.6619999408721924
    endloop
  endfacet
  facet normal 0.044764354825019836 -0.3404058516025543 0.939212441444397
    outer loop
      vertex -38.83399963378906 -63.2140007019043 2.634000062942505
      vertex -39.11600112915039 -62.16400146484375 3.0280001163482666
      vertex -40.5 -62.34600067138672 3.0280001163482666
    endloop
  endfacet
  facet normal 0.1312878131866455 -0.31717661023139954 0.9392350912094116
    outer loop
      vertex -37.28300094604492 -62.571998596191406 2.634000062942505
      vertex -39.11600112915039 -62.16400146484375 3.0280001163482666
      vertex -38.83399963378906 -63.2140007019043 2.634000062942505
    endloop
  endfacet
  facet normal 0.13129131495952606 -0.3171643912792206 0.9392387270927429
    outer loop
      vertex -37.28300094604492 -62.571998596191406 2.634000062942505
      vertex -37.82600021362305 -61.630001068115234 3.0280001163482666
      vertex -39.11600112915039 -62.16400146484375 3.0280001163482666
    endloop
  endfacet
endsolid 

```