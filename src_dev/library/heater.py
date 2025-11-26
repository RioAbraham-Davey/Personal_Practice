"""
Heating Module

A simple heating algorithm that uses a relay (on/off) to control a heater.
This can be used for both gas and heat pump.
It should also be able to control solar heating with a bit of modification.
"""
import uasyncio as aio

from library.logger import Log

log = Log(__name__, Log.DEBUG).get_logger()


# a simple heating algorithm class
# the class should be hardware agnostic
# as part of initialisation, the class should be passed a function that can be used to turn the heater on and off
# the class should also be passed a function that can be used to read the temperature
# the class should be able to run the heating algorithm in a loop
# the class should be able to stop the heating algorithm
# the class should be able to set the target temperature
# the class should be able to set the upper temperature tolerance
# the class should be able to set the temperature rounding steps
# the class should be able to set the minimum on time
# the class should be able to set the minimum off time


class Heater:
    def __init__(self,
                 turn_on, turn_off, value,
                 read_temperature,
                 off_check_period_s: int = (30*60),
                 minimum_on_time_s: int = (5*60),
                 upper_temperature_tolerance_centiC: int = 100,
                 round_steps: int = 50
                 ):
        """
        turn_on: function to turn on the heater
        turn_off: function to turn off the heater
        read_temperature: function to read the temperature in centi Celsius
        off_check_period_s: the period to check the temperature in seconds
        minimum_on_time_s: the minimum time the heater should be on in seconds
        upper_temperature_tolerance_centiC: the upper temperature tolerance in centi Celsius (1.5 Celsius is 150 centi Celsius)
        round_steps: the temperature rounding steps in centi Celsius
        """
        self._turn_on = turn_on
        self._turn_off = turn_off
        self._value = value
        self._read_temperature = read_temperature

        self._off_period_s = off_check_period_s
        self._minimum_on_s = minimum_on_time_s
        self._upper_tolerance_centiC = upper_temperature_tolerance_centiC

        self._round_steps = round_steps

        self._target_centiC = 0
        self._enabled = False

    async def tasks(self):
        last_state = True
        while True:
            if self.is_enabled():
                if not last_state:
                    last_state = True
                    log.debug('Heater is enabled.')
                log.debug('...............Heater LOOP...............')
                await aio.sleep(1)
                temperature = await self.get_rounded_temperature()
                log.debug(f"Heater Temperature: {temperature/100}C")
                if temperature < self._target_centiC:
                    # await put system in particular heat mode?
                    log.debug('attempt to turn on')
                    if self._turn_on_if_possible():
                        log.debug(
                            f'turned on for {self._minimum_on_s} seconds')
                        await aio.sleep(self._minimum_on_s)
                elif temperature > self._target_centiC + self._upper_tolerance_centiC:
                    # await put system in particular heat mode?
                    log.debug('attempt to turn off')
                    if self._turn_off_if_possible():
                        log.debug(
                            f'turned off for {self._off_period_s} seconds')
                        await aio.sleep(self._off_period_s)
            elif last_state:
                last_state = False
                log.debug('Heater is disabled.')
                if self._turn_off_if_possible():
                    log.warning(f'heater turned off')
            await aio.sleep(1)

    async def enable(self):
        log.debug(f'Heater is enabled.')
        self._enabled = True
        temperature = await self.get_rounded_temperature()
        if temperature < self._target_centiC:
            log.debug('attempt to turn on')
            if self._turn_on_if_possible():
                log.warning(f'turned on for partial cycle')

    def disable(self):
        self._enabled = False
        # disable the heater should be immediate, in case an on session is running
        log.debug('Heater is disabled.')
        if self._turn_off_if_possible():
            log.warning(f'heater turned off')

    def is_running(self):
        return (self._value() == 1)

    def is_enabled(self):
        return self._enabled

    async def set_target_temperature(self, temperature_centiC: int):
        valid = False
        if temperature_centiC % self._round_steps == 0:
            valid = True
            self._target_centiC = temperature_centiC
            log.debug(f"Target Temperature set to {temperature_centiC/100}C")
        if valid and self.is_enabled():
            # NOTE: We do this to enforce the new temperature half way through the cycle
            temperature = await self.get_rounded_temperature()
            if temperature < self._target_centiC:
                log.debug('Change of target temperature, attempt to turn on')
                if self._turn_on_if_possible():
                    log.warning(f'turned on for temp change')
            elif temperature > self._target_centiC + self._upper_tolerance_centiC:
                log.debug('Change of target temperature, attempt to turn off')
                if self._turn_off_if_possible():
                    log.warning(f'turned off for temp change')
        return valid

    def get_target_temperature(self):
        return self._target_centiC

    def _turn_on_if_possible(self):
        # check valve position before turning on
        possible = True
        if possible:
            self._turn_on()
        else:
            possible = False
        return possible

    def _turn_off_if_possible(self):
        # check valve position before turning off
        possible = True
        if possible:
            self._turn_off()
        else:
            possible = False
        return possible

    async def get_rounded_temperature(self):
        """
        round temp to the nearest step with _round_steps
        For example, if _round_steps is 100:
        *    ~  1100 <-  1050,  1051,  1099
        *    ~  1000 <-  1049,  1048,  1001
        *    ~ -1100 <- -1050, -1051, -1099
        *    ~ -1000 <- -1049, -1048, -1001
        """
        # read 10 times and average
        value = 0
        total_samples = const(100)
        for _ in range(total_samples):
            value += self._read_temperature()
            await aio.sleep_ms(10)
        value = value // total_samples

        step = self._round_steps
        if value >= 0:
            result = ((value + (step//2)) // step) * step
        else:
            result = ((value - (step//2)) // step) * step
        return result
