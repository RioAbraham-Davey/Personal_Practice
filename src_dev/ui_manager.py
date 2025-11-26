'''
Handle the UI of the pool controller
Read buttons and update the LEDs
Take care of any flashing/pulsing for LEDs
'''

from ble_manager import BLEManager
from library import aiobutton
from library import heater
from drivers import fxl6408
from machine import I2C, Pin
import uasyncio as aio
from library.logger import Log
import enums

log = Log(__name__, Log.DEBUG).get_logger()

# demo


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


class UIManager:
    ble: BLEManager
    heat: heater.Heater

    def __init__(self, ble: BLEManager, heater: heater.Heater, i2c: I2C | None = None):
        board = Pin.board
        UIManager.ble = ble
        UIManager.heat = heater

        if i2c is None:
            i2c = I2C(1, scl=board.I2C_SCL, sda=board.I2C_SDA)
        self._buttons = _FXLButtons(i2c)

        self._btn_light = aiobutton.AIOButton(
            lambda x: self._buttons.light.pressed,
            h_release=btn_light_released_handler,
            h_hold=btn_light_hold_handler,
            hold_ms=1000,
            hold_repeat=False)

        self._btn_light_colour = aiobutton.AIOButton(
            lambda x: self._buttons.light_colour.pressed,
            h_release=btn_light_colour_released_handler,
            h_hold=btn_light_colour_hold_handler,
            hold_ms=3000,
            hold_repeat=False)

        self._btn_water_feature = aiobutton.AIOButton(
            lambda x: self._buttons.water_feature.pressed,
            h_release=btn_water_feature_released_handler,
            h_hold=btn_water_feature_hold_handler,
            hold_ms=1000,
            hold_repeat=False)

        self._btn_heat_mode = aiobutton.AIOButton(
            lambda x: self._buttons.heat_toggle.pressed,
            h_release=btn_heat_mode_released_handler,
            h_hold=btn_heat_mode_hold_handler,
            hold_ms=1000,
            hold_repeat=False)

        self._btn_heat_increment = aiobutton.AIOButton(
            lambda x: self._buttons.heat_increment.pressed,
            h_release=btn_heat_increment_released_handler,
            h_hold=btn_heat_increment_released_handler,
            hold_ms=1000,
            hold_repeat=True)

        self._btn_heat_decrement = aiobutton.AIOButton(
            lambda x: self._buttons.heat_decrement.pressed,
            h_release=btn_heat_decrement_released_handler,
            h_hold=btn_heat_decrement_released_handler,
            hold_ms=1000,
            hold_repeat=True)

        self._btn_power = aiobutton.AIOButton(
            lambda x: self._buttons.power.pressed,
            h_release=btn_power_released_handler,
            h_hold=btn_power_hold_handler,
            hold_ms=1000,
            hold_repeat=False)

    async def tasks(self):
        await aio.gather(
            self._btn_light.coro_check(),
            self._btn_light_colour.coro_check(),
            self._btn_water_feature.coro_check(),
            self._btn_heat_mode.coro_check(),
            self._btn_heat_increment.coro_check(),
            self._btn_heat_decrement.coro_check(),
            self._btn_power.coro_check()
        )


def btn_light_released_handler(btn):
    log.debug("Light button released")
    current_mode = UIManager.ble.lights_mode_char.read()
    if current_mode == enums.Modes.ManualOff:
        current_mode = enums.Modes.ManualOn
    else:
        current_mode = enums.Modes.ManualOff

    UIManager.ble.update_char(UIManager.ble.lights_mode_char, current_mode)


def btn_light_hold_handler(btn):
    log.debug("Light button hold")
    current_mode = UIManager.ble.lights_mode_char.read()
    UIManager.ble.update_char(UIManager.ble.lights_mode_char, enums.Modes.Auto)


def btn_light_colour_released_handler(btn):
    log.debug("Light colour button released")
    current_colour = UIManager.ble.lights_manual_config_char.read()[0]
    new_colour = (current_colour + 1) % 10
    if new_colour == enums.Light.ColourCode.Black:
        new_colour = enums.Light.ColourCode.Blue

    UIManager.ble.update_char(
        UIManager.ble.lights_manual_config_char, bytes([new_colour]))


def btn_light_colour_hold_handler(btn):
    log.debug("Light colour button hold")
    current_brand = UIManager.ble.lights_brand_char.read()
    if current_brand == enums.Light.Brands.SpaElectric:
        current_brand = enums.Light.Brands.AquaQuip
    else:
        current_brand = enums.Light.Brands.SpaElectric

    UIManager.ble.update_char(UIManager.ble.lights_brand_char, current_brand)


def btn_water_feature_released_handler(btn):
    log.debug("Water feature button released")
    current_mode = UIManager.ble.wf_mode_char.read()
    if current_mode == enums.Modes.ManualOff:
        current_mode = enums.Modes.ManualOn
    else:
        current_mode = enums.Modes.ManualOff

    UIManager.ble.update_char(UIManager.ble.wf_mode_char, current_mode)


def btn_water_feature_hold_handler(btn):
    log.debug("Water feature button hold")
    UIManager.ble.update_char(UIManager.ble.wf_mode_char, enums.Modes.Auto)


def btn_heat_mode_released_handler(btn):
    log.debug("Heat mode button released")
    current_mode = UIManager.ble.heat_mode_char.read()[0]
    new_mode = (current_mode + 1) % 3
    if current_mode == enums.HeaterModes.Automatic[0]:  # go from auto to off
        new_mode = enums.HeaterModes.Off_Filter[0]

    UIManager.ble.update_char(UIManager.ble.heat_mode_char, bytes([new_mode]))


def btn_heat_mode_hold_handler(btn):
    log.debug("Heat mode button hold")
    UIManager.ble.update_char(
        UIManager.ble.heat_mode_char, enums.HeaterModes.Automatic)


def btn_heat_increment_released_handler(btn):
    log.debug("Heat increment button released")
    if UIManager.heat.is_enabled():
        current_mode = UIManager.ble.heat_mode_char.read()
        current_temp = UIManager.ble.heat_manual_config_char.read()
        pool = current_temp[0]
        spa = current_temp[1]
        log.debug(f"current_temp: {current_temp[0], current_temp[1]}")
        if current_mode == enums.HeaterModes.Pool:  # pool
            pool += 1
            if pool > 40:
                pool = 40
            log.debug(f"pool: {pool}")
        elif current_mode == enums.HeaterModes.Spa:  # spa
            spa += 1
            if spa > 40:
                spa = 40
            log.debug(f"spa: {spa}")
        else:
            log.debug(
                "Heat increment button released, but not in pool or spa mode")
            return
        log.debug(f"new_temp: {pool, spa}")

        UIManager.ble.update_char(
            UIManager.ble.heat_manual_config_char, bytes([pool, spa]))
    else:
        log.debug("Heat increment button released, but heater is disabled")


def btn_heat_decrement_released_handler(btn):
    log.debug("Heat decrement button released")
    if UIManager.heat.is_enabled():
        current_mode = UIManager.ble.heat_mode_char.read()
        current_temp = UIManager.ble.heat_manual_config_char.read()
        pool = current_temp[0]
        spa = current_temp[1]
        log.debug(f"current_temp: {current_temp[0], current_temp[1]}")
        if current_mode == enums.HeaterModes.Pool:  # pool
            pool -= 1
            if pool < 15:
                pool = 15
            log.debug(f"pool: {pool}")
        elif current_mode == enums.HeaterModes.Spa:  # spa
            spa -= 1
            if spa < 15:
                spa = 15
            log.debug(f"spa: {spa}")
        else:
            log.debug(
                "Heat decrement button released, but not in pool or spa mode")
            return
        log.debug(f"new_temp: {pool, spa}")

        UIManager.ble.update_char(
            UIManager.ble.heat_manual_config_char, bytes([pool, spa]))
    else:
        log.debug("Heat decrement button released, but heater is disabled")


count = 0


def btn_power_released_handler(btn):
    global count
    count = 0
    log.critical("GL toggle")
    current_mode = UIManager.ble.gl_mode_char.read()
    if current_mode == enums.Modes.ManualOff:
        current_mode = enums.Modes.ManualOn
    else:
        current_mode = enums.Modes.ManualOff
    UIManager.ble.update_char(UIManager.ble.gl_mode_char, current_mode)


def btn_power_hold_handler(btn):
    global count
    if count == 0:
        log.critical("GL Auto")
        UIManager.ble.update_char(
            UIManager.ble.gl_mode_char, enums.Modes.Auto)
    if count >= 3*5:  # 3 repeats per second, 5 seconds
        log.critical("spa refill")
        UIManager.ble.update_char(
            UIManager.ble.spa_refill_mode_char, enums.Modes.ManualOn)
        count = 0
    else:
        count += 1
