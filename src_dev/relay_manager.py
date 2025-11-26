'''
Centralised relay manager to align ZCD and relay control for
GPOs Relay
Valves Relay
Light Relay
Heater Relay

A task to run every 1ms and check for changes in the relay states
align relay state changes with ZCD

all relay on and off is handled through this class
'''
from time import sleep_ms
from machine import Pin, Signal, SPI
from drivers import mc74hc595
from drivers.zcd import wait_for_zcd
from library.logger import Log
import uasyncio as aio
# from typing import Callable #NOTE: typing not available in micropython yet
log = Log(__name__, Log.DEBUG).get_logger()


class Relay:
    '''
    Template class for relay
    '''

    def __init__(self, on, off, value): ...
    def on(self): ...
    def off(self): ...
    def value(self) -> int: ...


class _ZCDRelay(Relay):

    '''
    ZCD Relay class to align relay control with ZCD
    '''

    def __init__(self, on, off, value):
        self._on = on
        self._off = off
        self._value = value
        # self._state = False
        # self._schedule = False

    def on(self):
        # self._schedule = True
        wait_for_zcd()
        # NOTE: There seems to be a 5ms delay between GPIO on and Relay on (instant), so a delay is needed to ensure ZCD compliance
        sleep_ms(5)
        self._on()
        # self._state = True

    def off(self):
        # self._schedule = False
        wait_for_zcd()
        # NOTE: There seems to be a 5ms delay between GPIO off and Relay off (about 5ms delay), as the relay off has a slower response, the delay is not needed.
        self._off()
        # self._state = False

    def value(self):
        return self._value()
        # self._state = self._value()
        # return self._state


class _NormalRelay(Relay):
    '''
    Simple Relay class to control relay without ZCD
    '''

    def __init__(self, on, off, value):
        self._on = on
        self._off = off
        self._value = value

    def on(self):
        self._on()

    def off(self):
        self._off()

    def value(self):
        return self._value()


class _PulseRelay(Relay):
    '''
    Pulse Relay class to control relay without ZCD but needs a pulse to stay on
    '''

    def __init__(self, pin: Pin):
        self._pin = pin
        self._value = False

    def on(self):
        self._value = True

    def off(self):
        self._value = False

    def value(self):
        return self._value

    def action(self):
        if self._value:
            self._pin.value(not self._pin.value())


class RelayManager:
    '''
    Centralised relay manager to align ZCD and relay control for all relays
    This is so we can have a unified relay control across the system with simple on/off/value methods
    Per relay mapping to be done in the constructor
    Initiate once in the main.py and the "relay" object to be used across the system
    Usage example:
    main:
    rm = RelayManager()
    LightsManager(rm.lights)
    lights = rm.Lights

    lights.on()
    '''

    def __init__(self):
        board = Pin.board

        # ZCD setup
        _lights = Signal(Pin(board.RELAY_Light, Pin.OUT), invert=False)
        _gpo1 = Signal(Pin(board.RELAY_GPO1, Pin.OUT), invert=False)
        _gpo2 = Signal(Pin(board.RELAY_GPO2, Pin.OUT), invert=False)
        _valve_power = Signal(
            Pin(board.RELAY_ValvePower, Pin.OUT), invert=False)

        self.Lights = _ZCDRelay(_lights.on, _lights.off, _lights.value)
        self.GPO1 = _ZCDRelay(_gpo1.on, _gpo1.off, _gpo1.value)
        self.GPO2 = _ZCDRelay(_gpo2.on, _gpo2.off, _gpo2.value)
        self.ValvePower = _ZCDRelay(
            _valve_power.on, _valve_power.off, _valve_power.value)

        # Non-ZCD setup
        # Valves Via Shift Register
        spi = SPI(1, mosi=board.ShftR_Data_MOSI,
                  miso=3, sck=board.ShftR_Clock_SCK)
        latch = Pin(board.ShftR_LatchPulse, Pin.OUT)
        out_enable = Signal(
            Pin(board.ShftR_nOutEnable_Control, Pin.OUT), invert=True)
        sr = mc74hc595.MC74HC595(spi, latch, out_enable)

        # Shift Register Pin Mapping
        _suction = const(0)
        _return = const(1)
        _solar = const(2)
        _water_feature = const(3)

        _off = const(0)
        _on = const(1)

        self.SuctionValve = _NormalRelay(lambda: sr.pin(_suction, _on), lambda: sr.pin(_suction, _off),
                                         lambda: sr.pin(_suction))
        self.ReturnValve = _NormalRelay(lambda: sr.pin(_return, _on), lambda: sr.pin(_return, _off),
                                        lambda: sr.pin(_return))
        self.SolarValve = _NormalRelay(lambda: sr.pin(_solar, _on), lambda: sr.pin(_solar, _off),
                                       lambda: sr.pin(_solar))
        self.WaterFeatureValve = _NormalRelay(lambda: sr.pin(_water_feature, _on), lambda: sr.pin(_water_feature, _off),
                                              lambda: sr.pin(_water_feature))

        # Pulse / Heater Relay
        try:
            _heater = Pin(board.Heater_Pulse, Pin.OUT)
        except AttributeError as e:
            log.error(
                f'Heater Pulse Pin not available, using Boot Pin instead: {e}')
            _heater = Pin(board.BOOT, Pin.OUT)
        self.Heater = _PulseRelay(_heater)

        self.all_off()

    async def tasks(self):
        while True:
            self.Heater.action()
            await aio.sleep_ms(10)

    def all_off(self):
        self.Lights.off()
        self.GPO1.off()
        self.GPO2.off()
        self.ValvePower.off()
        self.SuctionValve.off()
        self.ReturnValve.off()
        self.SolarValve.off()
        self.WaterFeatureValve.off()
        self.Heater.off()
        log.debug('All Relays Off')
