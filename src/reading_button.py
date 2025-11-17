from machine import Pin, Signal
import time
from neopixel import NeoPixel


led =Pin(48, Pin.OUT)
np = NeoPixel(led, 1)

colourSequence = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)]
currentColourIndex = 0

try:
    button = Signal(Pin(0, Pin.IN), invert=False)
    while True:
        if button.value() == 0:
            if currentColourIndex < len(colourSequence) - 1:
                currentColourIndex += 1
            else:
                currentColourIndex = 0

            np[0] = colourSequence[currentColourIndex]
            np.write()

            while button.value() == 0:
                pass
        time.sleep(0.05)

except KeyboardInterrupt:
    pass    

