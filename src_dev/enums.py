'''
NOTE: with const you cannot have a variable name that is the same as another variable name even if it is in a class
'''


class Modes:
    ManualOff = const(b'\x00')
    ManualOn = const(b'\x01')
    Auto = const(b'\x02')


class Status:
    # needs to be different from Modes, refer to NOTE
    manualOff = const(b'\x00')
    manualOn = const(b'\x01')
    scheduleOff = const(b'\x02')
    schedule1On = const(b'\x03')
    schedule2On = const(b'\x04')
    transition = const(b'\xFF')


class HeaterModes:
    Off_Filter = const(b'\x00')
    Pool = const(b'\x01')
    Spa = const(b'\x02')
    Automatic = const(b'\x03')


class HeaterStatus:
    manualOff_Filter = const(b'\x00')
    manualPool = const(b'\x01')
    manualSpa = const(b'\x02')
    scheduleOff_ = const(b'\x03')
    schedule1On_ = const(b'\x04')
    schedule2On_ = const(b'\x05')
    transition_ = const(b'\xFF')


class ScheduleIndex:
    start = const(0)
    end = const(1)
    dow = const(2)
    enabled = const(3)
    config = const(4)
    heat_mode = const(5)


class Light:
    class Brands:
        SpaElectric = const(b'\x00')
        AquaQuip = const(b'\x01')
        Waterco = const(b'\x02')
        SETUP = const(b'\xFF')

    class ColourCode:
        Black = const(0)  # this is equivalent to off
        Blue = const(1)
        Purple = const(2)
        Red = const(3)
        Yellow = const(4)
        Green = const(5)
        Cyan = const(6)
        White = const(7)
        Slow = const(8)
        Fast = const(9)
