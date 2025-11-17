import uasyncio as aio
from machine import Pin, Signal
from button_function import AIOButton, decorator_ignore_if_held


# Input pin (example: active-low button)
pin = Signal(Pin(0, Pin.IN), invert=True)

colourSequence = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)]
currentColourIndex = 0


# Handlers receive the AIOButton instance (coro_check calls handlers with self)
def on_press(btn):
    print("pressed")

@decorator_ignore_if_held
def on_release(btn):
    print("released")

def on_hold(btn):
    print("held")

btn = AIOButton(hold_repeat=True, h_input=lambda x: pin.value(), h_press=on_press, h_release=on_release, h_hold=on_hold)

loop = aio.new_event_loop()
task = aio.create_task(btn.coro_check())
loop.run_forever()