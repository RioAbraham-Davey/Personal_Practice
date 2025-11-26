from relay_manager import RelayManager
from valves_manager import ValveManager

from machine import Pin, ADC, I2C
from library.heater import Heater
from math import log as LOG
import ble_manager
import uasyncio as aio
import ui_manager
import time
import enums
from library.logger import Log


log = Log(__name__, Log.DEBUG).get_logger()

# demo

# demo
board = Pin.board


def foo():
    return False


light_transition = foo


class Pixels:
    from library.lights import DaveyColourIndex

    class _pixel:
        def __init__(self, name, location, parent):
            self.name = name
            self.location = location
            self.parent = parent  # Reference to the parent pixels instance

        # add a way to set colour

        def set_colour(self, colour, brightness=1.0):
            # Call the set_colour method in the pixels class
            self.parent.set_colour(self, colour, brightness)

    class nameIndex:
        WaterFeature = const(0)
        Light = const(1)
        Spa = const(2)
        Filtration = const(3)
        Pool = const(4)
        Heat = const(5)
        Heat1 = const(6)
        Heat2 = const(7)
        Heat3 = const(8)
        Heat4 = const(9)
        Status = const(10)
        Power = const(11)

    class Colours(tuple):
        _BLUE = (0, 25, 255)
        _RED = (255, 5, 1)
        _PURPLE = (50, 0, 255)
        ORANGE = (255, 75, 0)
        RED = (255, 0, 0)
        YELLOW = (255, 150, 0)
        GREEN = (0, 255, 0)
        CYAN = (0, 255, 255)
        BLUE = (0, 0, 255)
        PURPLE = (180, 0, 255)
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        SLOW = _BLUE
        FAST = _RED

    # NOTE: This list order must match library.lights.Colour list
    colours_list = (Colours.BLACK, Colours.BLUE, Colours.PURPLE, Colours.RED,
                    Colours.YELLOW, Colours.GREEN, Colours.CYAN, Colours.WHITE,
                    Colours.SLOW, Colours.FAST)

    def __init__(self, pin, num_pixels=12):
        import neopixel
        self.pin = pin
        self.num_pixels = num_pixels
        self._pixels = neopixel.NeoPixel(pin, num_pixels)
        self.breath_list = [False for _ in range(num_pixels)]
        self.breath_list[Pixels.nameIndex.Power] = True

    def set_colour(self, pixel: int, colour: tuple[int, int, int], brightness=0.2):
        '''
        Set the colour as tuple of (r, g, b) for the pixel.
        '''
        # check that brightness is between 0 and 1, throw exception with correct range
        if brightness < 0 or brightness > 1:
            raise ValueError("Brightness must be between 0.0 and 1.0")
        new_colour = []
        for c in colour:
            if c == 0:
                new_colour.append(0)
            else:
                temp_colour = int(c * brightness)
                if temp_colour == 0:
                    new_colour.append(1)
                else:
                    new_colour.append(temp_colour)
        self._pixels[pixel] = new_colour

    def set_davey_colour(self, pixel: int, colourIndex: int, brightness=0.2):
        '''
        Set the colour based on DaveyColourIndex.
        '''
        self.set_colour(pixel, Pixels.colours_list[colourIndex], brightness)

    def apply_colour(self, pixel: int, colour: tuple[int, int, int], brightness=0.2):
        '''
        Apply the colour to the pixel.
        '''
        self.set_colour(pixel, colour, brightness)
        self._pixels.write()

    async def tasks(self):
        while True:
            self._pixels.write()
            await aio.sleep_ms(10)

    def clear(self, pixel: int):
        self._pixels[pixel] = Pixels.Colours.BLACK
        self.breath_list[pixel] = False

    def clear_now(self, pixel: int):
        self.clear(pixel)
        self._pixels.write()

    def clear_all(self):
        self._pixels.fill(Pixels.Colours.BLACK)
        self._pixels.write()


async def demo_ble():
    log.warning("Starting Demo...")
    # add default value for all characteristics
    # light:
    # 18000/60/60, 25200 -> 5am, 7am
    ble.update_char(ble.lights_schedule1_char, "18000,25200,127,0,5")
    ble.update_char(ble.lights_schedule2_char, "64800,72000,127,0,7")
    ble.update_char(ble.lights_manual_config_char, bytes(
        [enums.Light.ColourCode.Yellow]))  # Yellow
    ble.update_char(ble.lights_mode_char, enums.Modes.ManualOff)
    ble.update_char(ble.lights_status_char, enums.Status.manualOff)
    # water feature:
    ble.update_char(ble.wf_schedule1_char, "18000,25200,127,0,5")
    ble.update_char(ble.wf_schedule2_char, "64800,72000,127,0,7")
    ble.update_char(ble.wf_mode_char, enums.Modes.ManualOff)
    ble.update_char(ble.wf_status_char, enums.Status.manualOff)
    # heat:
    ble.update_char(ble.heat_schedule1_char, "46800,64800,127,0,30,1")
    ble.update_char(ble.heat_schedule2_char, "64800,68400,127,0,38,2")
    ble.update_char(ble.heat_manual_config_char, bytes(
        [0x1C, 0x28]))  # 28C pool, 40C spa
    ble.update_char(ble.heat_mode_char, enums.Modes.ManualOff)
    ble.update_char(ble.heat_status_char, enums.Status.manualOff)
    # garden light:
    ble.update_char(ble.gl_schedule1_char, "18000,25200,127,0,5")
    ble.update_char(ble.gl_schedule2_char, "64800,72000,127,0,7")
    ble.update_char(ble.gl_mode_char, enums.Modes.ManualOff)
    ble.update_char(ble.gl_status_char, enums.Status.manualOff)
    # spa refill
    ble.update_char(ble.spa_refill_manual_config_char, bytes([1]))  # minutes
    ble.update_char(ble.spa_refill_mode_char, enums.Modes.ManualOff)
    ble.update_char(ble.spa_refill_status_char, enums.Status.manualOff)
    # config:
    ble.update_char(ble.lights_brand_char, enums.Light.Brands.SpaElectric)
    # status:
    ble.update_char(ble.water_temperature_char, "...")

    while True:
        if ble.is_connected():
            np.set_colour(np.nameIndex.Status, np.Colours.BLUE)
        else:
            np.clear(np.nameIndex.Status)

        await aio.sleep_ms(500)


async def demo_neopixel_lights(np: Pixels):
    def get_next_led_colour_index(neo_index):
        neo_index = (neo_index + 1) % colours_length
        if neo_index == 0:  # skip black
            neo_index = 1
        return neo_index

    def get_ble_colour():
        return ble.lights_manual_config_char.read()[0]

    colours_length = len(Pixels.colours_list)-2  # -2 for slow and fast
    last_colour = enums.Light.ColourCode.Black
    transition_delay = const(500)
    while True:
        set_colour = get_ble_colour()
        current_status = ble.lights_status_char.read()
        if last_colour != set_colour:
            log.info(f"Colour Updated:{set_colour}")
            last_colour = set_colour
            neo_index = set_colour

        if current_status == enums.Status.transition:
            np.breath_list[np.nameIndex.Light] = True
            await aio.sleep_ms(transition_delay)
        elif (current_status == enums.Status.manualOff or
              current_status == enums.Status.scheduleOff):
            np.clear(np.nameIndex.Light)
            await aio.sleep_ms(transition_delay)
        else:
            if set_colour == enums.Light.ColourCode.Fast:
                np.set_davey_colour(np.nameIndex.Light, neo_index)
                neo_index = get_next_led_colour_index(neo_index)
                await aio.sleep_ms(1000)
            elif set_colour == enums.Light.ColourCode.Slow:
                next_neo_index = get_next_led_colour_index(neo_index+1)
                neo_index = get_next_led_colour_index(neo_index)
                c = Pixels.colours_list[neo_index]
                cn = Pixels.colours_list[next_neo_index]

                steps = const(30)
                delay = const(166)  # delay is 5000/steps
                for step in range(steps + 1):
                    if (ble.lights_mode_char.read() == enums.Modes.ManualOff or
                            get_ble_colour() != enums.Light.ColourCode.Slow):
                        break
                    blend_factor = step / steps
                    r = int((c[0] * (1 - blend_factor)) +
                            (cn[0] * blend_factor))
                    g = int((c[1] * (1 - blend_factor)) +
                            (cn[1] * blend_factor))
                    b = int((c[2] * (1 - blend_factor)) +
                            (cn[2] * blend_factor))
                    np.set_colour(np.nameIndex.Light, (r, g, b))
                    await aio.sleep_ms(delay)
                neo_index = next_neo_index
            else:  # Normal Colour
                np.set_davey_colour(np.nameIndex.Light, set_colour)
                await aio.sleep_ms(400)
        await aio.sleep_ms(100)


async def demo_lights(relays: RelayManager):
    from library import lights
    global light_transition
    aq = relays.Lights
    se = relays.Lights
    lightSE = lights.SpaElectricColours(
        se.off, se.on, se.value)
    lightAQ = lights.AquaQuipColours(
        aq.off, aq.on, aq.value)

    await lightSE.light.off()
    await lightAQ.light.off()

    light = lightSE
    light_transition = light.light.is_transitioning

    last_colour = enums.Light.ColourCode.Black
    last_mode = enums.Modes.ManualOff
    last_brand = enums.Light.Brands.SpaElectric
    last_sch1 = (0, 0, 0, 0, 0)
    last_sch2 = (0, 0, 0, 0, 0)
    while True:
        ble_colour = ble.lights_manual_config_char.read()[0]
        current_mode = ble.lights_mode_char.read()
        brand = ble.lights_brand_char.read()
        if brand != last_brand:
            if brand == enums.Light.Brands.SpaElectric:
                last_brand = brand
                log.warning("Brand: Spa Electric")
                light = lightSE
            elif brand == enums.Light.Brands.AquaQuip:
                last_brand = brand
                log.warning("Brand: AquaQuip")
                light = lightAQ
            elif brand == enums.Light.Brands.SETUP:
                log.warning("Light Setup/Config")
                await light.light.setup()
                ble.lights_brand_char.write(last_brand)
                brand = last_brand
            light_transition = light.light.is_transitioning
        if light_transition():
            np.breath_list[np.nameIndex.Light] = True
        else:
            np.breath_list[np.nameIndex.Light] = False
            if current_mode == enums.Modes.ManualOff:
                if last_mode != current_mode:
                    log.debug("Lights Manual Off")
                    last_mode = current_mode
                    ble.update_char(ble.lights_status_char,
                                    enums.Status.transition)
                    await light.light.off()
                    ble.update_char(ble.lights_status_char,
                                    enums.Status.manualOff)
            elif current_mode == enums.Modes.ManualOn:
                if last_mode != current_mode or last_colour != ble_colour:
                    log.debug("Lights Manual On")
                    last_mode = current_mode
                    colour = light.light.get_colour_object(ble_colour)
                    if last_colour != ble_colour:
                        log.info(f"Lights Colour Updated: {colour.name}")
                        last_colour = ble_colour
                    np.breath_list[np.nameIndex.Light] = True
                    # NOTE: set_colour is has a check to turn on lights if they are off
                    ble.update_char(ble.lights_status_char,
                                    enums.Status.transition)
                    await light.light.set_colour(colour)
                    ble.update_char(ble.lights_status_char,
                                    enums.Status.manualOn)
                    np.breath_list[np.nameIndex.Light] = False
            elif current_mode == enums.Modes.Auto:
                sch1 = schedule_from_string(
                    ble.lights_schedule1_char.read().decode())
                sch2 = schedule_from_string(
                    ble.lights_schedule2_char.read().decode())
                if sch1 != last_sch1 or sch2 != last_sch2:
                    last_sch1 = sch1
                    last_sch2 = sch2
                    last_mode = enums.Modes.ManualOff  # force update
                    log.info("Lights Schedule Updated")
                if last_mode != current_mode:
                    last_mode = current_mode
                    log.debug("Lights Auto")
                    if not (sch1[enums.ScheduleIndex.enabled] and
                            sch2[enums.ScheduleIndex.enabled]):
                        log.warning(
                            "Auto light mode but both schedules are disabled")
                    if schedule_is_running(sch1) and schedule_is_running(sch2):
                        log.warning("Schedules are overlapping")
                    if schedule_is_running(sch1):
                        log.info("Lights Auto 1 ON")
                        colour = light.light.get_colour_object(
                            sch1[enums.ScheduleIndex.config])
                        ble.update_char(ble.lights_status_char,
                                        enums.Status.transition)
                        await light.light.set_colour(colour)
                        ble.update_char(ble.lights_status_char,
                                        enums.Status.schedule1On)
                    elif schedule_is_running(sch2):
                        log.info("Lights Auto 2 ON")
                        colour = light.light.get_colour_object(
                            sch2[enums.ScheduleIndex.config])
                        ble.update_char(ble.lights_status_char,
                                        enums.Status.transition)
                        await light.light.set_colour(colour)
                        ble.update_char(ble.lights_status_char,
                                        enums.Status.schedule2On)
                    else:
                        log.info("Lights Auto Off")
                        ble.update_char(ble.lights_status_char,
                                        enums.Status.transition)
                        await light.light.off()
                        ble.update_char(ble.lights_status_char,
                                        enums.Status.scheduleOff)
        await aio.sleep_ms(100)


async def demo_garden_lights(relays: RelayManager):
    last_mode = enums.Modes.ManualOff
    last_sch1 = (0, 0, 0, 0, 0)
    last_sch2 = (0, 0, 0, 0, 0)
    while True:
        ble_mode = ble.gl_mode_char.read()
        if ble_mode == enums.Modes.ManualOff:
            if last_mode != ble_mode:
                last_mode = ble_mode
                log.info("Garden Lights Manual Off")
                ble.update_char(ble.gl_status_char, enums.Status.transition)
                relays.GPO1.off()
                ble.update_char(ble.gl_status_char, enums.Status.manualOff)
        elif ble_mode == enums.Modes.Auto:
            sch1 = schedule_from_string(
                ble.gl_schedule1_char.read().decode())
            sch2 = schedule_from_string(
                ble.gl_schedule2_char.read().decode())
            if sch1 != last_sch1 or sch2 != last_sch2:
                last_sch1 = sch1
                last_sch2 = sch2
                last_mode = enums.Modes.ManualOff  # force update
                log.info("Garden Lights Schedule Updated")
            if last_mode != ble_mode:
                last_mode = ble_mode
                log.info("Garden Lights Auto")
                if not (sch1[enums.ScheduleIndex.enabled] and
                        sch2[enums.ScheduleIndex.enabled]):
                    log.warning("Auto gl mode but both schedules are disabled")
                if schedule_is_running(sch1) and schedule_is_running(sch2):
                    log.warning("Schedules are overlapping")
                if schedule_is_running(sch1):
                    log.info("Garden Lights Auto 1 ON")
                    ble.update_char(ble.gl_status_char,
                                    enums.Status.transition)
                    relays.GPO1.on()
                    ble.update_char(ble.gl_status_char,
                                    enums.Status.schedule1On)
                elif schedule_is_running(sch2):
                    log.info("Garden Lights Auto 2 ON")
                    ble.update_char(ble.gl_status_char,
                                    enums.Status.transition)
                    relays.GPO1.on()
                    ble.update_char(ble.gl_status_char,
                                    enums.Status.schedule2On)
                else:
                    log.info("Garden Lights Auto Off")
                    ble.update_char(ble.gl_status_char,
                                    enums.Status.transition)
                    relays.GPO1.off()
                    ble.update_char(ble.gl_status_char,
                                    enums.Status.scheduleOff)
        else:
            if last_mode != ble_mode:
                last_mode = ble_mode
                ble.update_char(ble.gl_status_char, enums.Status.transition)
                log.info("Garden Lights Manual On")
                ble.update_char(ble.gl_status_char, enums.Status.manualOn)
                relays.GPO1.on()
        await aio.sleep_ms(100)


async def change_valve(transition_func, ble_status_char, final_status, np_index, np_colour):
    log.debug(f"valve transitioning...")
    np.breath_list[np_index] = True
    if ble_status_char is not None:
        ble.update_char(ble_status_char, enums.Status.transition)
    await transition_func()
    if ble_status_char is not None:
        ble.update_char(ble_status_char, final_status)
    np.breath_list[np_index] = False
    np.set_colour(np_index, np_colour)


async def demo_water_feature():
    last_mode = None
    last_sch1 = (0, 0, 0, 0, 0)
    last_sch2 = (0, 0, 0, 0, 0)
    while True:
        ble_mode = ble.wf_mode_char.read()
        if ble_mode == enums.Modes.ManualOff:
            if last_mode != ble_mode:
                last_mode = ble_mode
                log.info("Water Feature Manual Off")
                await change_valve(valves.set_water_feature_off,
                                   ble.wf_status_char, enums.Status.manualOff,
                                   np.nameIndex.WaterFeature, Pixels.Colours.BLACK)
        elif ble_mode == enums.Modes.Auto:
            sch1 = schedule_from_string(
                ble.wf_schedule1_char.read().decode())
            sch2 = schedule_from_string(
                ble.wf_schedule2_char.read().decode())
            if sch1 != last_sch1 or sch2 != last_sch2:
                last_sch1 = sch1
                last_sch2 = sch2
                last_mode = enums.Modes.ManualOff  # force update
                log.info("Water Feature Schedule Updated")
            if last_mode != ble_mode:
                last_mode = ble_mode
                log.info("Water Feature Auto")
                if not (sch1[enums.ScheduleIndex.enabled] and
                        sch2[enums.ScheduleIndex.enabled]):
                    log.warning("Auto wf mode but both schedules are disabled")
                if schedule_is_running(sch1) and schedule_is_running(sch2):
                    log.warning("Schedules are overlapping")
                if schedule_is_running(sch1):
                    log.info("Water Feature Auto 1 ON")
                    await change_valve(valves.set_water_feature_on,
                                       ble.wf_status_char, enums.Status.schedule1On,
                                       np.nameIndex.WaterFeature, np.Colours.ORANGE)
                elif schedule_is_running(sch2):
                    log.info("Water Feature Auto 2 ON")
                    await change_valve(valves.set_water_feature_on,
                                       ble.wf_status_char, enums.Status.schedule2On,
                                       np.nameIndex.WaterFeature, np.Colours.ORANGE)
                else:
                    log.info("Water Feature Auto Off")
                    await change_valve(valves.set_water_feature_off,
                                       ble.wf_status_char, enums.Status.scheduleOff,
                                       np.nameIndex.WaterFeature, Pixels.Colours.BLACK)
        else:
            if last_mode != ble_mode:
                last_mode = ble_mode
                log.info("Water Feature Manual On")
                await change_valve(valves.set_water_feature_on,
                                   ble.wf_status_char, enums.Status.manualOn,
                                   np.nameIndex.WaterFeature, np.Colours.ORANGE)
        await aio.sleep_ms(100)


async def turn_on_pump(heating=True):
    log.debug("turning on the pump")
    if heating:
        np.breath_list[np.nameIndex.Heat] = True
    relays.GPO2.on()
    await aio.sleep(10)
    log.debug("pump on")


async def turn_off_pump():
    log.debug("turning off the pump")
    relays.GPO2.off()
    await aio.sleep(3)
    log.debug("pump off")


def heater_off(reason=None):
    if reason != None:
        log.info(f"Heater Off: {reason}")
    heater.disable()


async def heater_on(reason):
    log.info(f"Heater On: {reason}")
    np.clear(np.nameIndex.Heat)
    await heater.enable()


def neopixel_heater_breath(pool, spa, filter):
    if pool:
        np.breath_list[np.nameIndex.Pool] = True
    else:
        np.clear(np.nameIndex.Pool)
    if spa:
        np.breath_list[np.nameIndex.Spa] = True
    else:
        np.clear(np.nameIndex.Spa)
    if filter:
        np.breath_list[np.nameIndex.Filtration] = True
    else:
        np.clear(np.nameIndex.Filtration)


async def demo_heater(relays: RelayManager):
    last_heat_mode = None  # to force update on first loop
    last_sch1 = (0, 0, 0, 0, 0)
    last_sch2 = (0, 0, 0, 0, 0)
    # ble_heat_target_temp = 0
    while True:
        spa_refill_mode = ble.spa_refill_mode_char.read()
        if spa_refill_mode == enums.Modes.ManualOn:
            spa_refill_minutes = ble.spa_refill_manual_config_char.read()[0]
            log.debug("Setting valves to spa refill position...")
            neopixel_heater_breath(True, True, True)
            ble.update_char(ble.spa_refill_status_char,
                            enums.Status.transition)
            heater_off("Spa Refill")
            await turn_off_pump()
            await valves.set_spa_refill()
            ble.update_char(ble.spa_refill_status_char, enums.Status.manualOn)
            log.info(f"Spa Refill On: {spa_refill_minutes} minutes")
            await turn_on_pump(heating=False)
            for _ in range(spa_refill_minutes * 60 * 100):
                await aio.sleep_ms(10)
                if ble.spa_refill_mode_char.read() == enums.Modes.ManualOff:
                    log.info("Spa Refill cancelled")
                    break
            log.info("Spa Refill Off")
            ble.update_char(ble.spa_refill_status_char,
                            enums.Status.transition)
            await turn_off_pump()
            ble.update_char(ble.spa_refill_status_char,
                            enums.Status.manualOff)
            ble.update_char(ble.spa_refill_mode_char, enums.Modes.ManualOff)
            # NOTE: let the heat mode take over the valves
            last_heat_mode = None

        ble_mode = ble.heat_mode_char.read()
        if ble_mode == enums.HeaterModes.Off_Filter:
            if last_heat_mode != ble_mode:
                last_heat_mode = ble_mode
                heater_off("Manual Off/Filtration")
                neopixel_heater_breath(False, False, True)
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.transition_)
                await turn_off_pump()
                await change_valve(valves.set_pool_mode,
                                   None, None,
                                   np.nameIndex.Filtration, Pixels.Colours.ORANGE)
                await turn_on_pump(heating=False)
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.manualOff_Filter)
        elif ble_mode == enums.HeaterModes.Pool:
            if last_heat_mode != ble_mode:
                last_heat_mode = ble_mode
                neopixel_heater_breath(True, False, False)
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.transition_)
                heater_off()
                await turn_off_pump()
                await change_valve(valves.set_pool_mode,
                                   None, None,
                                   np.nameIndex.Pool, Pixels.Colours.ORANGE)
                await turn_on_pump()
                await heater_on("Manual Pool")
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.manualPool)
                # ble_heat_target_temp = ble.heat_manual_config_char.read()[0]
        elif ble_mode == enums.HeaterModes.Spa:
            if last_heat_mode != ble_mode:
                last_heat_mode = ble_mode
                neopixel_heater_breath(False, True, False)
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.transition_)
                heater_off()
                await turn_off_pump()
                await change_valve(valves.set_spa_mode,
                                   None, None,
                                   np.nameIndex.Spa, Pixels.Colours.ORANGE)
                await turn_on_pump()
                await heater_on("Manual Spa")
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.manualSpa)
                # ble_heat_target_temp = ble.heat_manual_config_char.read()[1]
        elif ble_mode == enums.HeaterModes.Automatic:
            sch1 = schedule_from_string(
                ble.heat_schedule1_char.read().decode())
            sch2 = schedule_from_string(
                ble.heat_schedule2_char.read().decode())
            if sch1 != last_sch1 or sch2 != last_sch2:
                last_sch1 = sch1
                last_sch2 = sch2
                last_heat_mode = enums.HeaterModes.Off_Filter  # force update
                log.info("Heater Schedule Updated")
            if last_heat_mode != ble_mode:
                last_heat_mode = ble_mode
                log.debug("Auto Heat On")
                if not (sch1[enums.ScheduleIndex.enabled] and
                        sch2[enums.ScheduleIndex.enabled]):
                    log.warning(
                        "Auto heater mode but both schedules are disabled")
                    if schedule_is_running(sch1) and schedule_is_running(sch2):
                        log.warning("Schedules are overlapping")
                    if schedule_is_running(sch1):
                        log.info("Heater Auto 1 ON")
                        neopixel_heater_breath(True, True, False)
                        ble.update_char(ble.heat_status_char,
                                        enums.HeaterStatus.transition_)
                        heater_off()
                        await turn_off_pump()
                        if sch1[enums.ScheduleIndex.heat_mode] == enums.HeaterModes.Pool[0]:
                            neopixel_heater_breath(True, False, False)
                            await change_valve(valves.set_pool_mode,
                                               None, None,
                                               np.nameIndex.Pool, Pixels.Colours.ORANGE)
                            await turn_on_pump()
                            await heater_on("Schedule 1 Pool")
                            ble.update_char(ble.heat_status_char,
                                            enums.HeaterStatus.schedule1On_)
                        elif sch1[enums.ScheduleIndex.heat_mode] == enums.HeaterModes.Spa[0]:
                            neopixel_heater_breath(False, True, False)
                            await change_valve(valves.set_spa_mode,
                                               None, None,
                                               np.nameIndex.Spa, Pixels.Colours.ORANGE)
                            await turn_on_pump()
                            await heater_on("Schedule 1 Spa")
                            ble.update_char(ble.heat_status_char,
                                            enums.HeaterStatus.schedule1On_)
                        else:
                            log.error("Schedule 1 Invalid Heat Mode")
                        # ble_heat_target_temp = sch1[enums.ScheduleIndex.config]
                    elif schedule_is_running(sch2):
                        log.info("Heater Auto 2 ON")
                        neopixel_heater_breath(True, True, False)
                        ble.update_char(ble.heat_status_char,
                                        enums.HeaterStatus.transition_)
                        heater_off()
                        await turn_off_pump()
                        if sch2[enums.ScheduleIndex.heat_mode] == enums.HeaterModes.Pool[0]:
                            neopixel_heater_breath(True, False, False)
                            await change_valve(valves.set_pool_mode,
                                               None, None,
                                               np.nameIndex.Pool, Pixels.Colours.ORANGE)
                            await turn_on_pump()
                            await heater_on("Schedule 2 Pool")
                            ble.update_char(ble.heat_status_char,
                                            enums.HeaterStatus.schedule2On_)
                        elif sch2[enums.ScheduleIndex.heat_mode] == enums.HeaterModes.Spa[0]:
                            neopixel_heater_breath(False, True, False)
                            await change_valve(valves.set_spa_mode,
                                               None, None,
                                               np.nameIndex.Spa, Pixels.Colours.ORANGE)
                            await turn_on_pump()
                            await heater_on("Schedule 2 Spa")
                            ble.update_char(ble.heat_status_char,
                                            enums.HeaterStatus.schedule2On_)
                        else:
                            log.error("Schedule 2 Invalid Heat Mode")
                        # ble_heat_target_temp = sch2[enums.ScheduleIndex.config]
                    else:
                        heater_off("Auto Off/Filtration")
                        neopixel_heater_breath(False, False, True)
                        ble.update_char(ble.heat_status_char,
                                        enums.HeaterStatus.transition_)
                        await turn_off_pump()
                        await change_valve(valves.set_pool_mode,
                                           None, None,
                                           np.nameIndex.Filtration, Pixels.Colours.BLACK)
                        await turn_on_pump(heating=False)
                        ble.update_char(ble.heat_status_char,
                                        enums.HeaterStatus.scheduleOff_)

        # TODO: Is this the correct location?
        ble_heat_status = ble.heat_status_char.read()
        if ble_heat_status == enums.HeaterStatus.transition_:
            ble_heat_mode = ble.heat_mode_char.read()
            if ble_heat_mode == enums.HeaterModes.Off_Filter:
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.manualOff_Filter)
            elif ble_heat_mode == enums.HeaterModes.Pool:
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.manualPool)
            elif ble_heat_mode == enums.HeaterModes.Spa:
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.manualSpa)
            elif ble_heat_mode == enums.HeaterModes.Automatic:
                ble.update_char(ble.heat_status_char,
                                enums.HeaterStatus.scheduleOff_)
            else:
                log.error("Invalid Heat Mode")

        if ble_heat_status in (enums.HeaterStatus.manualPool,
                               enums.HeaterStatus.manualSpa,
                               enums.HeaterStatus.schedule1On_,
                               enums.HeaterStatus.schedule2On_):
            ble_heat_target_temp = 0
            if ble_heat_status == enums.HeaterStatus.manualPool:
                ble_heat_target_temp = ble.heat_manual_config_char.read()[0]
            elif ble_heat_status == enums.HeaterStatus.manualSpa:
                ble_heat_target_temp = ble.heat_manual_config_char.read()[1]
            elif ble_heat_status == enums.HeaterStatus.schedule1On_:
                sch1 = schedule_from_string(
                    ble.heat_schedule1_char.read().decode())
                ble_heat_target_temp = sch1[enums.ScheduleIndex.config]
            elif ble_heat_status == enums.HeaterStatus.schedule2On_:
                sch2 = schedule_from_string(
                    ble.heat_schedule2_char.read().decode())
                ble_heat_target_temp = sch2[enums.ScheduleIndex.config]
            ble_heat_target_temp *= 100  # convert to centiCelsius
            if heater.get_target_temperature() != (ble_heat_target_temp):
                log.info(f"Heater Target Updated: {ble_heat_target_temp}")
                await heater.set_target_temperature(ble_heat_target_temp)

        await aio.sleep_ms(100)


async def demo_heater_neopixel():
    while True:
        ble_heat_config = ble.heat_manual_config_char.read()
        ble_heat_status = ble.heat_status_char.read()
        # heat LEDs
        # if ble_heat_status in (enums.HeaterStatus.manualPool,
        #                        enums.HeaterStatus.manualSpa,
        #                        enums.HeaterStatus.schedule1On_,
        #                        enums.HeaterStatus.schedule2On_):
        if heater.is_enabled():
            if ble_heat_status == enums.HeaterStatus.manualPool:  # pool
                temp = ble_heat_config[0]
            elif ble_heat_status == enums.HeaterStatus.manualSpa:  # spa
                temp = ble_heat_config[1]
            elif ble_heat_status == enums.HeaterStatus.schedule1On_:
                sch1 = schedule_from_string(
                    ble.heat_schedule1_char.read().decode())
                temp = sch1[enums.ScheduleIndex.config]
            elif ble_heat_status == enums.HeaterStatus.schedule2On_:
                sch2 = schedule_from_string(
                    ble.heat_schedule2_char.read().decode())
                temp = sch2[enums.ScheduleIndex.config]
            else:
                temp = 15  # default to zero for transition

            if temp > 40:  # max temp
                temp = 40
            elif temp < 15:  # min temp
                temp = 15
            temp0 = ((temp - 15) / 25 * 4)

            if temp0 > 4:
                temp0 = 4
            elif temp0 < 0:
                temp0 = 0

            if temp0 <= 1:
                brightness1 = temp0-0
                brightness2 = 0
                brightness3 = 0
                brightness4 = 0
            elif temp0 <= 2:
                brightness1 = 1
                brightness2 = temp0-1
                brightness3 = 0
                brightness4 = 0
            elif temp0 <= 3:
                brightness1 = 1
                brightness2 = 1
                brightness3 = temp0-2
                brightness4 = 0
            else:
                brightness1 = 1
                brightness2 = 1
                brightness3 = 1
                brightness4 = temp0-3

            np.set_colour(np.nameIndex.Heat1, np.Colours.ORANGE, brightness1)
            np.set_colour(np.nameIndex.Heat2, np.Colours.ORANGE, brightness2)
            np.set_colour(np.nameIndex.Heat3, np.Colours.ORANGE, brightness3)
            np.set_colour(np.nameIndex.Heat4, np.Colours.ORANGE, brightness4)
        else:
            # all off
            np.clear(np.nameIndex.Heat1)
            np.clear(np.nameIndex.Heat2)
            np.clear(np.nameIndex.Heat3)
            np.clear(np.nameIndex.Heat4)

        if heater.is_running():
            np.clear(np.nameIndex.Heat)
            np.set_colour(np.nameIndex.Heat, np.Colours.RED, 0.5)
        elif not np.breath_list[np.nameIndex.Heat]:
            np.clear(np.nameIndex.Heat)

        await aio.sleep_ms(50)


async def demo_neopixel_breath(np: Pixels):
    brightness = 0.0
    direction = +0.05
    while True:
        for i in range(np.num_pixels):
            if np.breath_list[i]:
                np.set_colour(i, np.Colours.ORANGE, brightness)

        brightness += direction

        if brightness >= 1.0 or brightness <= 0.0:
            direction *= -1

        if brightness > 1.0:
            brightness = 1.0
        elif brightness < 0.0:
            brightness = 0.0

        await aio.sleep_ms(50)


async def demo_water_temp():
    last_temp = None
    while True:
        if ble.is_connected():
            temp = await heater.get_rounded_temperature()
            if temp != last_temp:
                last_temp = temp
                msg = "{:.1f}".format(temp/100)
                log.debug(f"Water Temp Changed: {msg}")
                ble.update_char(ble.water_temperature_char, msg)
                await aio.sleep(5)
        else:
            await aio.sleep(1)
            last_temp = None


async def demo_time():
    def convert_int_to_hex(i):
        a = i // 10
        b = i % 10
        return a*16 + b
    while True:
        await aio.sleep(1)
        # wd and yd not used.
        yyyy, mm, dd, HH, MM, SS, wd, yd = time.localtime()

        t = bytes([convert_int_to_hex(yyyy//100), convert_int_to_hex(yyyy % 100),
                   convert_int_to_hex(mm), convert_int_to_hex(dd),
                   convert_int_to_hex(HH), convert_int_to_hex(MM), convert_int_to_hex(SS)])
        # log.debug(f"Time: {t}")
        ble.update_char(ble.time_sync_char, t)


def adc_to_celsius(adc_val):
    BETA = const(4190)
    RNTC = const(68_000)
    VIN = const(3_300)
    RDIV = const(3_300)
    VREF = const(950)
    KELVIN_CONSTANT = 273.15
    try:
        Vout = adc_val * VREF / 4095
        Rt = ((VIN*RDIV) - (Vout*RDIV))/Vout
        temperature_c = (1 / (1/298.16 + (1/BETA) *
                              LOG(Rt/RNTC))) - KELVIN_CONSTANT
    except ZeroDivisionError as e:
        # log.error(f"Error converting adc to celsius: {e}")
        temperature_c = 25.5
    return temperature_c


def schedule_from_string(string):
    '''
    expected schedule string format:
    start, end, dow, enabled, [config], [mode]
    '''
    temp = string.split(',')
    schedule = tuple(int(i) for i in temp)
    if len(schedule) not in (4, 5, 6):
        log.error("Invalid Schedule String, using default values!!!")
    return schedule


def schedule_is_running(sch):
    '''
        Check if the schedule is running
    '''
    def datetime_to_seconds(dt):
        '''
        dt: tuple of 8 integers representing
        (compatible with mpy time.localtime())
        year, month, day, hour, minute, second, week of year, day of year
        '''
        return dt[3] * 3600 + dt[4] * 60 + dt[5]

    def is_today_enabled(dow):
        '''
        dow: is binary bit field of the day of the week
        0: Monday
        1: Tuesday
        2: Wednesday
        3: Thursday
        4: Friday
        5: Saturday
        6: Sunday
        '''
        today = time.localtime()[6]
        return dow & (1 << today)

    is_running: bool = False
    today = time.localtime()[6]
    if sch[enums.ScheduleIndex.enabled] and is_today_enabled(sch[enums.ScheduleIndex.dow]):
        current_time = datetime_to_seconds(time.localtime())
        if sch[enums.ScheduleIndex.start] <= current_time <= sch[enums.ScheduleIndex.end]:
            is_running = True
    else:
        is_running = False
    return is_running


def fake_heater_on():
    relays.Heater.on()
    # relays.Lights.on()


def fake_heater_off():
    relays.Heater.off()
    # relays.Lights.off()


# if __name__ == "__main__":
# np = Pixels(Pin(48, Pin.OUT), 1)
np = Pixels(Pin(board.NEOPIXEL, Pin.OUT))
relays = RelayManager()
valves = ValveManager(relays)
i2c = I2C(1, scl=board.I2C_SCL, sda=board.I2C_SDA)

ble = ble_manager.BLEManager(i2c)
WaterTemp = ADC(Pin(board.SENSE_WaterTemp))
heater = Heater(fake_heater_on, fake_heater_off, relays.Heater.value,
                lambda: adc_to_celsius(WaterTemp.read())*100,
                off_check_period_s=20, minimum_on_time_s=10)
ui = ui_manager.UIManager(ble, heater, i2c)
ble.update_char(ble.heat_mode_char, bytes([2]))


loop = aio.new_event_loop()

loop.create_task(np.tasks())
loop.create_task(demo_neopixel_breath(np))
loop.create_task(ble.tasks())
loop.create_task(demo_ble())
loop.create_task(demo_time())
loop.create_task(ui.tasks())
loop.create_task(relays.tasks())
loop.create_task(heater.tasks())
loop.create_task(demo_lights(relays))
loop.create_task(demo_neopixel_lights(np))
loop.create_task(demo_heater_neopixel())
loop.create_task(demo_garden_lights(relays))
loop.create_task(demo_water_feature())
loop.create_task(demo_heater(relays))
loop.create_task(demo_water_temp())

loop.run_forever()
