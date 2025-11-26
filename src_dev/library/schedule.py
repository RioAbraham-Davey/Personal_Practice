'''
Simple schedule class to be used by each module.
Interface is the same for all modules.
Start: start time in 24 hour format as seconds from midnight
End: end time in 24 hour format as seconds from midnight
Enabled: True or False
Config: particular config for the schedule which is module specific
'''
# write a schedule class that can be used by all modules
# schedule class will have the following attributes
# start, end, enabled, config
# start and end will be in 24 hour format
# enabled will be True or False
# config will be module specific
# schedule class will have the following methods
# __init__, __str__, __repr__, __eq__, __ne__, __lt__, __le__, __gt__, __ge__
# __init__ will initialize the schedule object
# __str__ will return the schedule object as a string
# __repr__ will return the status of the schedule object as True or False representing Schedule running or not
# __eq__ will compare two schedule objects for equality
# __ne__ will compare two schedule objects for inequality
# __lt__ will compare two schedule objects for less than
# __le__ will compare two schedule objects for less than or equal to
# __gt__ will compare two schedule objects for greater than
# __ge__ will compare two schedule objects for greater than or equal to
# schedule class will have the following properties
# start, end, enabled, config
# start will return the start time in 24 hour format
# end will return the end time in 24 hour format
# enabled will return True or False
# config will return the config for the schedule
# schedule class will have the following class methods
# from_string, from_dict
# from_string will return a schedule object from a string
# from_dict will return a schedule object from a dictionary
# schedule class will have the following static methods
# to_string, to_dict
# to_string will return a string from a schedule object
# to_dict will return a dictionary from a schedule object
# schedule class will have the following class attributes
# _time_format
# _time_format will be the time format for the schedule
import time
from library.logger import Log

log = Log(__name__, Log.DEBUG).get_logger()


class Schedule:
    _time_format = '%H:%M:%S'

    def __init__(self, start: int, end: int, day_of_week: int, enabled: bool | int, config: bytearray):
        self._start = start
        self._end = end
        self._day_of_week = day_of_week
        self._enabled = enabled
        self._config = config
        self._is_running = False

    def __str__(self):
        return f'Start: {self._start}, End: {self._end}, Day of Week: {self._day_of_week} Enabled: {self._enabled}, Config: {self._config}'

    # def __eq__(self, other):
    #     return self._start == other._start and self._end == other._end and self._enabled == other._enabled and self._config == other._config

    # def __ne__(self, other):
    #     return self._start != other._start or self._end != other._end or self._enabled != other._enabled or self._config != other._config

    # def __lt__(self, other):
    #     return self._start < other._start

    # def __le__(self, other):
    #     return self._start <= other._start

    # def __gt__(self, other):
    #     return self._start > other._start

    # def __ge__(self, other):
    #     return self._start >= other._start

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def enabled(self):
        return self._enabled

    @property
    def config(self):
        return self._config

    @classmethod
    def from_string(cls, string):
        log.debug(f'From String: {string}')
        start, end, dow, enabled, config = string.split(',')
        log.debug(
            f'Start: {start}, End: {end}, Day of Week: {dow}, Enabled: {enabled}, Config: {config}')
        return cls(int(start), int(end), int(dow), int(enabled), bytearray([int(config)]))

    @ classmethod
    def from_dict(cls, dictionary):
        return cls(dictionary['start'], dictionary['end'], dictionary['dow'], dictionary['enabled'], dictionary['config'])

    @ staticmethod
    def to_string(schedule):
        return f'{schedule._start},{schedule._end},{schedule._day_of_week},{schedule._enabled},{schedule._config}'

    @ staticmethod
    def to_dict(schedule):
        return {'start': schedule._start, 'end': schedule._end, 'dow': schedule._day_of_week, 'enabled': schedule._enabled, 'config': schedule._config}

    def is_enabled(self):
        return self._enabled

    def is_running(self):
        '''
            Check if the schedule is running

        '''
        if self.is_enabled():
            if self._is_today_a_schedule_day(self._day_of_week):
                current_time = self._datetime_to_seconds(time.localtime())
                if self._start <= current_time <= self._end:
                    self._is_running = True
        else:
            self._is_running = False
        return self._is_running

    @ staticmethod
    def _datetime_to_seconds(dt):
        '''
        dt: tuple of 8 integers representing
        (compatible with mpy time.localtime())
        year, month, day, hour, minute, second, week of year, day of year
        '''
        return dt[3] * 3600 + dt[4] * 60 + dt[5]

    @ staticmethod
    def _is_today_a_schedule_day(dow):
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
        log.debug(f'Today: {today}, DOW: {dow}, Bitwise: {1 << today}')
        return (1 << today) & dow
