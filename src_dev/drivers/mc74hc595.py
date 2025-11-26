"""
MicroPython basic 74HC595 shift register using SPI
"""
__version__ = "0.2.0"

from machine import SPI, Pin, Signal
# spi = SPI(1, mosi=board.ShftR_Data_MOSI, miso=3, sck=board.ShftR_Clock_SCK)
# latch = Pin(board.ShftR_LatchPulse, Pin.OUT)
# out_enable = Signal(Pin(board.ShftR_nOutEnable_Control, Pin.OUT), invert=True)
# shift_register = MC74HC595(spi, latch, out_enable)


class MC74HC595:
    '''
    74HC595 shift register using SPI
    Parameters:
    spi : SPI object (feed MOSI and SCK pins, use an unused spare pin (i.e. GPIO3) for MISO as it is not used and MPY on ESP32 will auto assign MISO if not provided)
    latchPulse : Pin object
    size_bytes : int (number of 74HC595 chips in series)
    '''

    def __init__(self, spi: SPI, latchPulse: Pin | Signal, OutEnable: Pin | Signal, size_bytes: int = 1):
        self.spi = spi
        self.latchPulse = latchPulse
        self._port = bytearray(size_bytes)
        self.OutEnable = OutEnable
        self._size_bytes = size_bytes
        self.OutEnable.off()
        self.clear()
        self.OutEnable.on()

    def _write(self, latch=False):
        self.spi.write(self._port)
        if latch:
            self.latch()

    def latch(self):
        self.latchPulse(1)
        self.latchPulse(0)

    def pin(self, pin, value=None, latch=True):
        if value is None:
            return (self._port[pin // 8] >> (pin % 8)) & 1
        elif value:
            self._port[pin // 8] |= 1 << (pin % 8)
        else:
            self._port[pin // 8] &= ~(1 << (pin % 8))
        self._write(latch)

    def toggle(self, pin, latch=True):
        self._port[pin // 8] ^= 1 << (pin % 8)
        self._write(latch)

    def clear(self):
        self[0] = 0

    def __getitem__(self, index):
        '''
        Get the value of the byte at the given index (entire port 0/1)
        '''
        return self._port[index]

    def __setitem__(self, index, value):
        '''
        Set the value of the byte at the given index (entire port 0/1)
        '''
        self._port[index] = value
        self._write(True)
