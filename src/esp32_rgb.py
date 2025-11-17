from machine import Pin
from neopixel import NeoPixel
import time

print("testing the rgb")

pin =Pin(48, Pin.OUT)
np = NeoPixel(pin, 1)

r = 0
g = 0
b = 0
while True:
    if r < 255:
        if  g < 255:
            if b < 255:
                b += 1
            g += 1
        r += 1
        
    np[0] = (255, 255, 255)
    np.write()
    time.sleep(0.1)


