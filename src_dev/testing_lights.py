from machine import Pin
import neopixel
import time

# 32 LED strip connected to X8.
p = Pin.board.NEOPIXEL
n = neopixel.NeoPixel(p, 12)

# Draw a red gradient.

for i in range(12):
    n[i] = (100, 0, 0)
    n.write()