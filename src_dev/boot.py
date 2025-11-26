from library.logger import Log
from drivers.pcf85063a import set_mpy_rtc


log = Log(__name__, Log.DEBUG).get_logger()

log.debug("Starting boot.py...")


set_mpy_rtc(log)
