import uasyncio as aio
from micropython import const
import enums

from library.logger import Log
log = Log(__name__, Log.WARNING).get_logger()


DaveyColourIndex = enums.Light.ColourCode
# '''
# Enum class to define the Davey standardised colours
# Blue, Purple, Red, Yellow, Green, Aqua, White, Slow, Fast
# '''

# Colour Order:
'''' Astral
    1, blue
    2, magenta
    3, red
    4, orange
    5, green
    6, aqua
    7, white
    8, customised colour
    9, customised pattern
    10, rainbow pattern
    11, ocean pattern
    12, disco pattern
'''
''' Spa Electric
    1, blue
    2, magenta
    3, red
    4, lime
    5, green
    6, aqua
    7, white 1
    8, white 2
    9, slow colour blend
    10, fast colour change
'''
''' Waterco
    1, WHITE
    2, SLOW CHANGING COLOURS - 20 SEC RAMPING
    3, FAST CHANGING COLOURS - 5 SEC RAMPING
    4, BLUE
    5, MAGENTA
    6, RED
    7, YELLOW-GREEN (GOLD)
    8, GREEN
    9, AQUA
'''
''' AquaQuip
    1 MAURITIAN WHITE
    2 TURQUOISE
    3 TAHITIAN BLUE
    4 AQUA DELIGHT
    5 APPLE GREEN
    6 GOLFERS GREEN
    7 SUNSET ORANGE
    8 FUCHSIA
    9 PLANET PURPLE
    10 SLOW SCROLL
    11 FAST SCROLL
    12 ADVANCE AUSTRALIA
    13 VIVID SCROLL
    14 DISCO INFERNO
'''


class PoolLightColour:
    '''
    Pool Light Colour class
    DaveyCode: Davey code for the colour
    ManufacturerName: Name of the colour specific to the manufacturer
    ManufacturerCode: Step or Time code for the colour specific to the manufacturer
    '''

    def __init__(self, DaveyCode, ManufacturerName, ManufacturerCode):
        self.davey_code = DaveyCode
        self.name = ManufacturerName
        self.config_code = ManufacturerCode


class LightControl:
    # TODO: Implement the State class and use it to manage the state of the light and lock the state to prevent multiple changes while the light is changing
    def __init__(self, hw_function_off, hw_function_on, hw_function_check, off_ms, on_ms,  colours: tuple[PoolLightColour, ...], synchronise, hold_ms=3000, setup=None, set_colour=None):
        '''
        hw_function_off: Function to turn the light off with a single call
        hw_function_on: Function to turn the light on with a single call
        hw_function_check: Function to check the state of the hardware pin, expecting a 0/1 or True/False and wrapping that internally to force True/False
        adjust_steps: Function that returns a +/- int to adjust the number of steps required to reach the desired colour, if not needed it should just return 0
        synchronise: Function to synchronise the lights, as it is light dependent it needs to be defined in the calling code
        '''
        self._colours = colours
        self._current_colour = None
        self.hw_on = hw_function_on
        self.hw_off = hw_function_off
        self.hw_check = hw_function_check
        self._OFF_ms = off_ms
        self._ON_ms = on_ms
        self._HOLD_ms = hold_ms
        self.synchronise = synchronise
        self._setup = setup
        self._set_colour = set_colour
        self.state = enums.Status.manualOff

    def value(self):
        return self.state

    async def on(self, hold_ms=None):
        await self._on(hold_ms)
        self.state = enums.Status.manualOn

    async def _on(self, hold_ms=None):
        if hold_ms is None:
            hold_ms = self._HOLD_ms
        log.debug("hw_on")
        self.hw_on()
        log.debug(f"wait for {hold_ms}ms")
        await aio.sleep_ms(hold_ms)

    async def off(self, hold_ms=None):
        await self._off(hold_ms)
        self.state = enums.Status.manualOff

    async def _off(self, hold_ms=None):
        if hold_ms is None:
            hold_ms = self._HOLD_ms
        log.debug("hw_off")
        self.hw_off()
        log.debug(f"wait for {hold_ms}ms")
        await aio.sleep_ms(hold_ms)

    async def toggle(self, hold_ms=None):
        if hold_ms is None:
            hold_ms = self._HOLD_ms
        if self._check():
            await self.off()
        else:
            await self.on()
        await aio.sleep_ms(hold_ms)
        return self._check()

    def _check(self):
        log.debug("hw_check")
        return True if self.hw_check() else False

    async def single_switch(self, off_ms=None, on_ms=None):
        if off_ms is None:
            off_ms = self._OFF_ms
        elif off_ms > 20:
            off_ms -= 10  # relay on has a 10ms delay, so we need to adjust the off_ms to compensate
        if on_ms is None:
            on_ms = self._ON_ms
        if self._check() == False:
            log.info("Light is off, turning on")
            # NOTE: this may need to switch hold_ms for the lights that use NEXT
            await self._on(self._ON_ms)
        await self._off(off_ms)
        await self._on(on_ms)

    # def _calculate_steps(self, Colour: PoolLightColour):
    #     steps_required = Colour.code - self._current_colour.code
    #     log.debug(steps_required)
    #     if steps_required < 0:
    #         steps_required = len(self._colours) + steps_required
    #         log.debug(f"adjusted, -: {steps_required}")
    #     return steps_required

    def colour(self):
        return self._current_colour

    async def set_colour(self, Colour: PoolLightColour):
        if self._set_colour is None:
            log.debug(f"LIGHT colour to {Colour.name}")
            self.state = enums.Status.transition
            log.debug(f"state: {self.state}")
            await self.single_switch(Colour.config_code)
            self._current_colour = Colour
            self.state = enums.Status.manualOn
        else:
            log.debug("Custom set_colour function defined")
            await self._set_colour(Colour)
        # if self._current_colour is None:
        #     log.debug("First time setting colour")
        #     self.synchronise()
        # log.debug(
        #     f"Current colour is {self._current_colour.name}, {self._current_colour.code} --> Setting colour to {Colour.name}, {Colour.code}")
        # steps_required = self._calculate_steps(Colour)
        # log.debug(steps_required)
        # if steps_required == 0:
        #     log.debug("No change required")
        #     return

        # steps_required += self.adjust_steps()
        # log.debug(steps_required)

        # for _ in range(steps_required):
        #     self.single_switch()
        # self._current_colour = Colour

    def get_colour_object(self, davey_code: int):
        for colour in self._colours:
            if colour.davey_code == davey_code:
                return colour
        return PoolLightColour(None, None, None)

    async def setup(self):
        if self._setup is not None:
            log.debug("Running setup function")
            self.state = enums.Status.transition
            await self._setup()
            self.state = enums.Status.manualOff
        else:
            log.debug("No setup function defined")

    def is_transitioning(self):
        return (self.state == enums.Status.transition)


class SpaElectricColours:
    '''
    Spa Electric light control
    The available colours and pattern (in order of selection) are:
    1, Blue -> BLUE
    2, Magenta -> PURPLE
    3, Red -> RED
    4, Lime -> YELLOW
    5, Green -> GREEN
    6, Aqua -> CYAN
    7, White 1 -> WHITE
    8, White 2 -> _skip
    9, Slow colour blend -> SLOW
    10, Fast colour change -> FAST
    '''
    blue = PoolLightColour(DaveyColourIndex.Blue, 'blue', 250)
    purple = PoolLightColour(DaveyColourIndex.Purple, 'magenta', 300)
    red = PoolLightColour(DaveyColourIndex.Red, 'red', 350)
    yellow = PoolLightColour(DaveyColourIndex.Yellow, 'lime', 400)
    green = PoolLightColour(DaveyColourIndex.Green, 'green', 450)
    cyan = PoolLightColour(DaveyColourIndex.Cyan, 'aqua', 500)
    white = PoolLightColour(DaveyColourIndex.White, 'white 1', 550)
    slow = PoolLightColour(DaveyColourIndex.Slow, 'slow colour blend', 600)
    fast = PoolLightColour(DaveyColourIndex.Fast, 'fast colour change', 650)

    colours = (blue, purple, red, yellow, green, cyan, white, slow, fast)

    def __init__(self, hw_function_off, hw_function_on, hw_function_check, off_ms=400, on_ms=120):
        '''
        hw_function_off: Function to turn the light off with a single call
        hw_function_on: Function to turn the light on with a single call
        hw_function_check: Function to check the state of the hardware pin, expecting a 0/1 or True/False and wrapping that internally to force True/False
        '''
        self.light = LightControl(hw_function_off, hw_function_on, hw_function_check,
                                  off_ms, on_ms, self.colours, self.synchronise, hold_ms=const(3_000), setup=self._setup)

    async def synchronise(self):
        await self.light.on()
        await self.light.single_switch(220, 120)  # rapid on/off
        # self.light.single_switch()  # off for 2s and then turn on
        current_colour = self.light._current_colour
        self.light._current_colour = self.colours[0]
        if current_colour == None:
            await self.light.set_colour(self.light._current_colour)
        else:
            await self.light.set_colour(current_colour)
        return self.light._current_colour

    async def _setup(self):
        async def _enter_setting_mode(self):
            log.debug("Entering setting mode")
            log.debug("wait 30s...")
            await self.light.off(30_000)
            for _ in range(3):
                log.debug("wait 12s...")
                await self.light.single_switch(12_000, 1000)

        async def _save_settings(self):
            log.debug("Save settings")
            log.debug("wait 31s...")
            await self.light.single_switch(31_000, self.light._HOLD_ms)

        async def _next_setting(self, count=1):
            for _ in range(count):
                log.debug("Next setting")
                await self.light.single_switch(1000, self.light._HOLD_ms)
        '''
        Setup the light to the correct mode
        This has to be called upon initial setup if SpaElectric is selected to ensure the light is in the correct mode.
        '''
        await _enter_setting_mode(self)
        # go to "green" which is multi mode mode
        await _next_setting(self)
        await _save_settings(self)


class AquaQuipColours:
    '''
    AquaQuip light control
    The available colours and pattern (in order of selection) are:
    1, Blue -> BLUE
    2, Aqua -> CYAN
    3, Green -> GREEN
    4, Gold -> YELLOW
    5, Magenta -> PURPLE
    6, Red -> RED
    7, White -> WHITE
    8, Seaside Scroll -> _skip
    9, Slow Scroll -> SLOW
    10, Rapid Scroll -> FAST
    11, Fireworks -> _skip
    12, Disco Tech -> _skip
    13, Flash -> _skip
    '''

    blue = PoolLightColour(DaveyColourIndex.Blue, 'Blue', 160)
    cyan = PoolLightColour(DaveyColourIndex.Cyan, 'Aqua', 200)
    green = PoolLightColour(DaveyColourIndex.Green, 'Green', 240)
    yellow = PoolLightColour(DaveyColourIndex.Yellow, 'Gold', 290)
    purple = PoolLightColour(DaveyColourIndex.Purple, 'Magenta', 350)
    red = PoolLightColour(DaveyColourIndex.Red, 'Red', 420)
    white = PoolLightColour(DaveyColourIndex.White, 'White', 510)
    # SeasideScroll = PoolLightColour('_Skip', 610)
    slow = PoolLightColour(DaveyColourIndex.Slow, 'Slow Scroll', 730)
    fast = PoolLightColour(DaveyColourIndex.Fast, 'Rapid Scroll', 870)
    # Fireworks = PoolLightColour('_Skip', 1040)
    # DiscoTech = PoolLightColour('_Skip', 1240)
    # Flash = PoolLightColour('_Skip', 1440)

    colours = (blue, purple, red, yellow, green, cyan, white, slow, fast)

    def __init__(self, hw_function_off, hw_function_on, hw_function_check, off_ms=400, on_ms=120):
        '''
        hw_function_off: Function to turn the light off with a single call
        hw_function_on: Function to turn the light on with a single call
        hw_function_check: Function to check the state of the hardware pin, expecting a 0/1 or True/False and wrapping that internally to force True/False
        '''
        self.light = LightControl(hw_function_off, hw_function_on, hw_function_check,
                                  off_ms, on_ms, self.colours, self.synchronise, hold_ms=const(1_500))

    async def synchronise(self):
        await self.light.on()
        await self.light.single_switch(6_500)  # rapid on/off
        current_colour = self.light._current_colour
        self.light._current_colour = self.colours[0]
        if current_colour == None:
            await self.light.set_colour(self.light._current_colour)
        else:
            await self.light.set_colour(current_colour)
        return self.light._current_colour


async def test_colour(light, colour: PoolLightColour, wait_ms=1000):
    await light.set_colour(colour)
    log.debug(
        f"CHECK --------------------- {colour.name} ---------------------")
    await aio.sleep_ms(wait_ms)


async def test():
    from tests import davey as dwp

    rel = dwp.pin_RELAY_Light

    log.debug("Testing Spa Electric Colours")
    check = SpaElectricColours(rel.off, rel.on, rel.value)
    await test_colour(check, check.white, 1000)
    await test_colour(check, check.blue, 1000)
    await test_colour(check, check.green, 1000)
    await test_colour(check, check.cyan, 1000)
    await test_colour(check, check.purple, 1000)
    await test_colour(check, check.red, 500)
    await test_colour(check, check.yellow, 5000)

    log.debug("Testing AquaQuip Colours")
    check = AquaQuipColours(rel.off, rel.on, rel.value)
    await test_colour(check, check.white, 1000)
    await test_colour(check, check.blue, 1000)
    await test_colour(check, check.green, 1000)
    await test_colour(check, check.cyan, 1000)
    await test_colour(check, check.purple, 1000)
    await test_colour(check, check.red, 500)
    await test_colour(check, check.yellow, 500)


if __name__ == "__main__":
    aio.run(test())
