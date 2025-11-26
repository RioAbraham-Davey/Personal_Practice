'''
Operates the opening and closing of pool valves:
Suction and Return valves.
Solar Valve.
Water Feature Valve.

each valve has position A (relay off) and position B (relay on)

needs:
add toggle
all off
position of each valve
master power relay

will:
operate the valves when requested
remember the position of each valve
before rotation, put all valves last position,
then change to new position and turn on the master power relay
when operation is complete, turn off master switch then turn off every valve relay
all valve relays 


only:
operate 1 set of valves at a time:
1. suction and return
2. solar
3. water feature
during which, all valves have to stay in their last position
if 1 set is running and another set change is requested,
the new set will be queued to run after the current set is done
'''
from relay_manager import RelayManager  # only for using, initialising is done in main.py
from relay_manager import Relay  # only for type hinting
from machine import Pin, ADC
import uasyncio as aio
from library.logger import Log

log = Log(__name__, Log.DEBUG).get_logger()


class Valve:
    class Position:
        A_OFF = const(0)
        B_ON = const(1)
        transition_to_A_OFF = const(2)
        transition_to_B_ON = const(3)

    def __init__(self, relay: Relay):
        self._relay = relay
        self.position = Valve.Position.A_OFF

    def _start_position_A_OFF(self):
        self.position = Valve.Position.transition_to_A_OFF
        self._relay.off()

    def _finish_position_A_OFF(self):
        self.position = Valve.Position.A_OFF
        # self._relay.off() # this happens in ValveManager

    def _start_position_B_ON(self):
        log.debug(f"Starting position B ON...")
        self.position = Valve.Position.transition_to_B_ON
        self._relay.on()

    def _finish_position_B_ON(self):
        self.position = Valve.Position.B_ON
        # self._relay.off() # this happens in ValveManager


class ValveManager:
    class State:
        RESTING = const(0)
        TRANSITION = const(1)

    class ADCThreshold:
        STOPPED = const(800)
        one_VALVE_MOVING = const(1400)
        two_VALVEs_MOVING = const(2600)
        MAX = const(3000)

    STATE = State.RESTING

    def __init__(self, relays: RelayManager):
        self._relays = relays
        self._suction_valve = Valve(relays.SuctionValve)
        self._return_valve = Valve(relays.ReturnValve)
        self._solar_valve = Valve(relays.SolarValve)
        self._water_feature_valve = Valve(relays.WaterFeatureValve)

        self._master_power_relay = relays.ValvePower
        # FIXME: This is purely for testing purposes on old PCBA, to be removed
        try:
            self.adc = ADC(Pin(Pin.board.SENSE_ValvePresent))
        except Exception as e:
            self.adc = ADC(Pin(Pin.board.SENSE_RoofAirTemp))
            log.error(
                f"ADC not available, using roof air temp pin instead: {e}")

    def _all_off(self):
        '''
        Turn off all valve relays and master power relay
        to be only used by the ValveManager in _transition_valves()
        '''
        self._master_power_relay.off()

        self._suction_valve._relay.off()
        self._return_valve._relay.off()
        self._solar_valve._relay.off()
        self._water_feature_valve._relay.off()

    def _adc_read(self, valve_count: int = 1):
        reading = self.adc.read()
        if valve_count == 1 and reading > self.ADCThreshold.one_VALVE_MOVING:
            log.error(f"ADC Reading too high for 1 valve moving: {reading}")
        elif valve_count == 2 and reading > self.ADCThreshold.two_VALVEs_MOVING:
            log.error(f"ADC Reading too high for 2 valves moving: {reading}")
        if reading > self.ADCThreshold.MAX:
            log.critical(f"ADC Reading too high for valves: {reading}")
        return reading

    async def _transition_valves(self, valve_count: int = 1):
        '''
        it is the responsibility of the calling function to set valves in the correct position.
        '''
        log.debug("Master power relay ON...")
        self.STATE = ValveManager.State.TRANSITION
        self._master_power_relay.on()
        adc = self._adc_read(valve_count)
        count = 0
        while adc < self.ADCThreshold.STOPPED:
            if count > 2:
                log.error(f"Valve(s) are not moving... [{adc}]")
                break
            log.debug(f"Waiting for valve(s) to start moving [{adc}]")
            await aio.sleep(1)
            adc = self._adc_read(valve_count)
            count += 1
        adc = self._adc_read(valve_count)
        count = 0
        while adc > self.ADCThreshold.STOPPED:
            if count > 60:
                log.error(f"Valve(s) are not stopping... [{adc}]")
                break
            log.debug(f"Waiting for valve(s) to stop moving [{adc}]")
            await aio.sleep(1)
            adc = self._adc_read(valve_count)
            count += 1
        log.debug("Master power relay OFF...")
        self.STATE = ValveManager.State.RESTING
        self._master_power_relay.off()

    def _set_all_valves_to_last_position(self):
        log.critical("Setting all valves to last position [tbd]")
        pass

    async def set_pool_mode(self):
        log.debug("Pool Mode: starting")
        while self.STATE == ValveManager.State.TRANSITION:
            log.debug("Pool Mode: waiting for previous operation to complete")
            await aio.sleep(5)
        self._set_all_valves_to_last_position()
        self._suction_valve._start_position_A_OFF()
        self._return_valve._start_position_A_OFF()
        await self._transition_valves(2)
        self._suction_valve._finish_position_A_OFF()
        self._return_valve._finish_position_A_OFF()

    async def set_spa_mode(self):
        # turn suction and return valves to position B
        log.debug("Spa Mode: starting")
        while self.STATE == ValveManager.State.TRANSITION:
            log.debug("Spa Mode: waiting for previous operation to complete")
            await aio.sleep(5)
        self._set_all_valves_to_last_position()
        self._suction_valve._start_position_B_ON()
        self._return_valve._start_position_B_ON()
        await self._transition_valves(2)
        self._suction_valve._finish_position_B_ON()
        self._return_valve._finish_position_B_ON()

    async def set_spa_refill(self):
        # turn suction valve to position B and return valve to position A
        log.debug("Spa Refill Mode: starting")
        while self.STATE == ValveManager.State.TRANSITION:
            log.debug(
                "Spa Refill Mode: waiting for previous operation to complete")
            await aio.sleep(5)
        self._set_all_valves_to_last_position()
        self._suction_valve._start_position_A_OFF()
        self._return_valve._start_position_B_ON()
        await self._transition_valves(2)
        self._suction_valve._finish_position_A_OFF()
        self._return_valve._finish_position_B_ON()
        pass

    async def set_solar_on(self, position: Valve.Position):
        # await self._solar_valve.set_position(position)
        pass

    async def set_solar_off(self):
        # await self._solar_valve.set_position(Valve.Position.A_OFF)
        pass

    async def set_water_feature_on(self):
        log.debug("WF on: starting")
        while self.STATE == ValveManager.State.TRANSITION:
            log.debug("WF on: waiting for previous operation to complete")
            await aio.sleep(5)
        self._set_all_valves_to_last_position()
        self._water_feature_valve._start_position_B_ON()
        await self._transition_valves()
        self._water_feature_valve._finish_position_B_ON()

    async def set_water_feature_off(self):
        while self.STATE == ValveManager.State.TRANSITION:
            log.debug("WF off: waiting for previous operation to complete")
            await aio.sleep(5)
        self._set_all_valves_to_last_position()
        self._water_feature_valve._start_position_A_OFF()
        await self._transition_valves()
        self._water_feature_valve._finish_position_A_OFF()
