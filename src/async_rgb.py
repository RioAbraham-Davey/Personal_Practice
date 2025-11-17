import asyncio
from machine import Pin
from neopixel import NeoPixel
import random
import aiorepl

pin = Pin(48, Pin.OUT)
np = NeoPixel(pin, 1)

async def blink_rgb():
    while True:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        np[0] = (r, g, b)
        np.write()
        await asyncio.sleep(0.5)
        np[0] = (0, 0, 0)
        np.write()
        await asyncio.sleep(0.5)

async def simple_addition():
    while True:
        try:
            num1 = random.randint(1, 100)
            num2 = random.randint(1, 100)
            print(f"Calculating: {num1} + {num2}")
            result = num1 + num2
            print(f"Result: {result}")
        except ValueError:
            print("Invalid input. Please enter numeric values.")
        await asyncio.sleep(3)

loop = asyncio.new_event_loop()
blinking = asyncio.create_task(blink_rgb())
repl = asyncio.create_task(simple_addition())
loop.run_forever()






