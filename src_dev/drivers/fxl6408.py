"""
MicroPython basic FXL6408 I2C I/O Expander

TBD: Add interrupt, add 16 bit support
"""

__version__ = "0.1.0"


class FXL6408:
    # _OUTPUT_STATE_OFFSET = 0x05
    _INPUT_STATUS_OFFSET = 0x0F

    def __init__(self, i2c, address=0x43, size_bytes=1):
        self._i2c = i2c
        self._address = address
        self._port = bytearray(size_bytes)
        self._size_bytes = size_bytes

    def check(self):
        if self._i2c.scan().count(self._address) == 0:
            raise OSError(
                f"FXL6408 not found at I2C address {self._address:#x}")
        return True

    @property
    def port(self):
        self._read()
        port = self._port[0]
        # if self._size_bytes > 1:
        #     for i in range(self._size_bytes):
        #         port |= self._port[i] << (8 * i)
        return port

    # @port.setter
    # def port(self, value):
    #     self._port[0] = value & 0xFF
    #     # if self._size_bytes > 1:
    #     #     for i in range(self._size_bytes):
    #     #         self._port[i] = (value >> (8 * i)) & 0xFF
    #     self._write()

    def pin(self, pin, value: bool | None = None):
        pin = self._validate_pin(pin)
        if value is None:
            self._read()
            return (self._port[pin // 8] >> (pin % 8)) & 1
        # if value:
        #     self._port[pin // 8] |= 1 << (pin % 8)
        # else:
        #     self._port[pin // 8] &= ~(1 << (pin % 8))
        # self._write()

    # def toggle(self, pin):
    #     pin = self._validate_pin(pin)
    #     self._port[pin // 8] ^= 1 << (pin % 8)
    #     self._write()

    def _validate_pin(self, pin):
        # pin valid range 0..7
        # first digit: port (0-1)
        # second digit: io (0-7)
        # NOTE: only 1 port is supported
        if not 0 <= pin <= 7:
            # and ((self._size_bytes > 1) and (not 10 <= pin <= 17)): ???
            raise ValueError(f"Invalid pin {pin}. Use 0-7")
        # if pin >= 10:
        #     pin -= 2
        return pin

    def _read(self):
        self._readRegister(self._INPUT_STATUS_OFFSET, self._port)

    def _readRegister(self, offset, outputPointer):
        self._i2c.writeto(self._address, bytes([offset]))
        self._i2c.readfrom_into(self._address, outputPointer)

    # def _write(self):
    #     self._writeRegister(self._OUTPUT_STATE_OFFSET, self._port)

    # def _writeRegister(self, offset, dataToWrite):
    #     self._i2c.writeto(self._address, bytes([offset, dataToWrite]))
