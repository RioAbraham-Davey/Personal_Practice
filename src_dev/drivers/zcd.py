'''
Zero Crossing Detection (ZCD) driver
'''
from machine import Pin
import time
import uasyncio as aio
from library.logger import Log

log = Log(__name__, Log.WARNING).get_logger()

board = Pin.board
zcd = Pin(board.DETECT_ZeroCrossingDetection, Pin.IN)


def measure_zcd_us():
    one = time.ticks_us()
    wait_for_zcd()
    two = time.ticks_us()
    return two - one


def wait_for_zcd():
    # NOTE: This is a blocking function
    # TODO: Implement a check for old board to skip this function
    edge = zcd.value()
    start = time.ticks_ms()
    while edge == zcd.value():
        # allow upto 3 edge detections to be missed (3x(1/50Hz/2) = 30ms)
        if time.ticks_diff(time.ticks_ms(), start) > 50:
            log.error('ZCD not detected')
            break


async def wait_for_zcd_async():
    edge = zcd.value()
    while edge == zcd.value():
        await aio.sleep_ms(1)
