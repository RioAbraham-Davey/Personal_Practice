from library import aiobutton
from drivers import fxl6408
from machine import I2C, Pin
import asyncio as aio

class _FXLButtons:
    _port: fxl6408.FXL6408

    class _Button:
        def __init__(self, pin):
            self._pin = pin

        '''
        Return the state of the button
        Property is needed for the AIOButton class to work
        As it needs to make a function call to this class without knowing the instance
        So a lambda is created using the instance and the function is called
        '''
        @property
        def pressed(self):
            return not _FXLButtons._Button_port.pin(self._pin)

    def __init__(self, i2c):
        _FXLButtons._Button_port = fxl6408.FXL6408(i2c)
        self.water_feature = _FXLButtons._Button(0)
        self.light = _FXLButtons._Button(1)
        self.heat_decrement = _FXLButtons._Button(4)
        self.light_colour = _FXLButtons._Button(2)
        self.heat_increment = _FXLButtons._Button(3)
        self.heat_toggle = _FXLButtons._Button(5)
        self.power = _FXLButtons._Button(6)

def btn_light_released_handler(btn):
    print(1)
    return None

def btn_light_hold_handler(btn):
    print(2)
    return None

def btn_light_colour_released_handler(btn):
    print(3)
    return None

def btn_light_colour_hold_handler(btn):
    print(4)
    return None

def btn_water_feature_released_handler(btn):
    print(5)
    return None

def btn_water_feature_hold_handler(btn):
    print(6)
    return None

def btn_heat_mode_released_handler(btn):
    print(7)
    return None

def btn_heat_mode_hold_handler(btn):
    print(8)
    return None

def btn_heat_increment_released_handler(btn):
    print(9)
    return None

def btn_heat_decrement_released_handler(btn):
    print(10)
    return None

def btn_power_released_handler(btn):
    print(11)
    return None

def btn_power_hold_handler(btn):
    print(12)
    return None

i2c = I2C(1, scl=Pin.board.I2C_SCL, sda=Pin.board.I2C_SDA)
buttons = _FXLButtons(i2c)

btn_light = aiobutton.AIOButton(
    lambda x: buttons.light.pressed,
    h_release= btn_light_released_handler,
    h_hold= btn_light_hold_handler,
    hold_ms=1000,
    hold_repeat=False)

btn_light_colour = aiobutton.AIOButton(
    lambda x: buttons.light_colour.pressed,
    h_release= btn_light_colour_released_handler,
    h_hold= btn_light_colour_hold_handler,
    hold_ms=3000,
    hold_repeat=False)

btn_water_feature = aiobutton.AIOButton(
    lambda x: buttons.water_feature.pressed,
    h_release= btn_water_feature_released_handler,
    h_hold=btn_water_feature_hold_handler,
    hold_ms=1000,
    hold_repeat=False)

btn_heat_toggle = aiobutton.AIOButton(
    lambda x: buttons.heat_toggle.pressed,
    h_release=btn_heat_mode_released_handler,
    h_hold=btn_heat_mode_hold_handler,
    hold_ms=1000,
    hold_repeat=False)

btn_heat_increment = aiobutton.AIOButton(
    lambda x: buttons.heat_increment.pressed,
    h_release=btn_heat_increment_released_handler,
    h_hold=btn_heat_increment_released_handler,
    hold_ms=1000,
    hold_repeat=True)

btn_heat_decrement = aiobutton.AIOButton(
    lambda x: buttons.heat_decrement.pressed,
    h_release= btn_heat_decrement_released_handler,
    h_hold= btn_heat_decrement_released_handler,
    hold_ms= 1000,
    hold_repeat= True)

btn_power = aiobutton.AIOButton(
    lambda x: buttons.power.pressed,
    h_release= btn_power_released_handler,
    h_hold= btn_power_hold_handler,
    hold_ms= 1000,
    hold_repeat= False)

async def tasks():
    await aio.gather(
        btn_light.coro_check(),
        btn_light_colour.coro_check(),
        btn_water_feature.coro_check(),
        btn_heat_toggle.coro_check(),
        btn_heat_increment.coro_check(),
        btn_heat_decrement.coro_check(),
        btn_power.coro_check()
    )

main_loop = aio.new_event_loop()
task = aio.create_task(tasks())
main_loop.run_forever()