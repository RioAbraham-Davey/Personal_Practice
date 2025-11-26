'''
MicroPython driver for NXP PCF85063A RTC
'''
from machine import I2C
from micropython import const


def _bcd_to_dec(bcd):
    return ((bcd // 16) * 10) + (bcd % 16)


def _dec_to_bcd(dec):
    return ((dec // 10) * 16) + (dec % 10)


class PCF85063A:
    class CAP_SEL:
        Cap_7_pF = const(0)
        Cap_12_5_pF = const(1)

    class CLOCKOUT_FREQUENCY:
        # Constants for clock frequency settings
        Freq_32KHZ = const(0b000)
        Freq_16KHZ = const(0b001)
        Freq_8KHZ = const(0b010)
        Freq_4KHZ = const(0b011)
        Freq_2KHZ = const(0b100)
        Freq_1KHZ = const(0b101)
        Freq_1HZ = const(0b110)
        Disabled = const(0b111)

    def __init__(self, i2c: I2C, address: int = 0x51):
        self.i2c = i2c
        self.address = address
        self._datetime_register = 0x04
        self.set_clockout_frequency(self.CLOCKOUT_FREQUENCY.Disabled)
        self.set_cap_sel(self.CAP_SEL.Cap_7_pF)

    def _write_byte(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytearray([value]))

    def _read_byte(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _read_bytes(self, register, length):
        return self.i2c.readfrom_mem(self.address, register, length)

    @property
    def datetime(self):
        '''
        Returns the date and time of the RTC
        as a tuple of 8 integers representing
        (compatible with mpy machine.RTC.datetime())
        year, month, day, 0, hour, minute, second, 0
        first 0 is day of week and second 0 is milliseconds
        '''
        data = self._read_bytes(self._datetime_register, 7)
        second = _bcd_to_dec(data[0] & 0x7F)
        minute = _bcd_to_dec(data[1] & 0x7F)
        hour = _bcd_to_dec(data[2] & 0x3F)
        day = _bcd_to_dec(data[3] & 0x3F)
        month = _bcd_to_dec(data[5] & 0x1F)
        year = 2000 + _bcd_to_dec(data[6] & 0xFF)
        dt = (year, month, day, 0, hour, minute, second, 0)
        return dt

    @datetime.setter
    def datetime(self, dt: tuple[int, int, int, int, int, int, int, int]):
        '''
        Sets the date and time of the RTC
        The input is a tuple of 8 integers representing
        (compatible with mpy machine.RTC.datetime())
        year, month, day, 0, hour, minute, second, 0
        first 0 is day of week and second 0 is milliseconds
        '''
        year = _dec_to_bcd(dt[0] - 2000)
        month = _dec_to_bcd(dt[1] & 0x1F)
        day = _dec_to_bcd(dt[2] & 0x3F)
        # day of week not used 3
        hour = _dec_to_bcd(dt[4] & 0x3F)
        minute = _dec_to_bcd(dt[5] & 0x7F)
        second = _dec_to_bcd(dt[6] & 0x7F)
        # milliseconds not used 7
        self._write_byte(self._datetime_register, second)
        self._write_byte(self._datetime_register + 1, minute)
        self._write_byte(self._datetime_register + 2, hour)
        self._write_byte(self._datetime_register + 3, day)
        self._write_byte(self._datetime_register + 5, month)
        self._write_byte(self._datetime_register + 6, year)

    def set_clockout_frequency(self, frequency):
        reg = self._read_byte(0x01)
        reg = (reg & 0xF8) | (frequency & 0x07)
        self._write_byte(0x01, reg)

    def set_cap_sel(self, cap):
        reg = self._read_byte(0x00)
        reg = (reg & 0xFE) | (cap & 0x01)
        self._write_byte(0x00, reg)

    def set_timer(self, timer_value, frequency):
        self._write_byte(0x10, timer_value)
        reg = self._read_byte(0x11)
        reg = (reg & 0xF3) | ((frequency & 0x03) << 2)
        self._write_byte(0x11, reg)


def get_pcf(i2c=None):
    from machine import I2C, Pin
    from drivers.pcf85063a import PCF85063A
    if i2c is None:
        i2c = I2C(0, scl=Pin.board.I2C_SCL, sda=Pin.board.I2C_SDA)
    pcf_rtc = PCF85063A(i2c)
    return pcf_rtc


def set_mpy_rtc(log):
    '''
    Use external RTC to set internal RTC
    '''
    from machine import RTC
    pcf_rtc = get_pcf()
    log.debug(f"External RTC Time: {pcf_rtc.datetime}")
    log.debug(f"Internal RTC Time: {RTC().datetime()}")
    log.debug("Setting internal RTC from External RTC Time...")
    RTC().datetime(pcf_rtc.datetime)
    log.debug(f"New Internal RTC Time: {RTC().datetime()}")


def set_external_rtc(log=None, datetimeTuple=None, i2c=None):
    '''
    Use internal RTC to set external RTC
    '''
    from machine import RTC
    if log is None:
        log = print
    pcf_rc = get_pcf(i2c)
    log(f"External RTC Time: {pcf_rc.datetime}")
    log(f"Internal RTC Time: {RTC().datetime()}")
    if datetimeTuple is not None:
        log("Setting Internal RTC Time from input...")
        RTC().datetime(datetimeTuple)
        log(f"New Internal RTC Time: {RTC().datetime()}")
    log("Setting External RTC from Internal RTC Time...")
    pcf_rc.datetime = RTC().datetime()
    log(f"New External RTC Time: {pcf_rc.datetime}")
