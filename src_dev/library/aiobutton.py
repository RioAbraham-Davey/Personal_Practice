from micropython import const
import uasyncio as aio

# Module version
__version__ = "0.1.0"
__all__ = ["AIOButton"]

H_INPUT = const(0)
H_PRESS = const(1)
H_RELEASE = const(2)
H_HOLD = const(3)
S_INSTANT = const(4)
S_DEBOUNCED = const(5)
T_DEBOUNCE = const(6)
T_HOLD = const(7)
T_PRESS = const(8)
NUM_OF_PARAS = const(9)


class AIOButton(object):
    """A class for uasyncio button."""

    def __init__(
        self,
        h_input=None,
        h_press=None,
        h_release=None,
        h_hold=None,
        debounce_ms=50,
        press_ms=100,
        hold_ms=1000,
        check_ms=50,
        hold_repeat=True,
        hold_repeat_ms=333,  # roughly 3 times per second
    ):
        self.para_list = [h_input, h_press,
                          h_release, h_hold,
                          False, False,
                          0, 0, 0]
        self.debounce_ms = debounce_ms
        self.press_ms = press_ms
        self.hold_ms = hold_ms
        self.check_ms = check_ms
        self.hold_repeat = hold_repeat
        self.hold_repeat_ms = hold_repeat_ms

    def set_input_handler(self, input_handler):
        self.para_list[H_INPUT] = input_handler

    def set_press_handler(self, press_handler):
        self.para_list[H_PRESS] = press_handler

    def set_release_handler(self, release_handler):
        self.para_list[H_RELEASE] = release_handler

    def set_hold_handler(self, hold_handler):
        self.para_list[H_HOLD] = hold_handler

    def get_instant(self):
        return self.para_list[S_INSTANT]

    def get_debounced(self):
        return self.para_list[S_DEBOUNCED]

    async def coro_check(self):
        while True:
            await aio.sleep_ms(self.check_ms)
            if self.para_list[H_INPUT]:
                self.para_list[S_INSTANT] = self.para_list[H_INPUT](self)
            if self.para_list[S_DEBOUNCED] != bool(self.para_list[S_INSTANT]):
                self.para_list[T_DEBOUNCE] += self.check_ms
                if self.para_list[T_DEBOUNCE] >= self.debounce_ms:
                    self.para_list[T_DEBOUNCE] = 0
                    self.para_list[S_DEBOUNCED] = bool(
                        self.para_list[S_INSTANT])
                    if self.para_list[S_DEBOUNCED]:
                        # self.para_list[T_DEBOUNCE] += self.check_ms
                        if self.para_list[H_PRESS]:
                            self.para_list[H_PRESS](self)
                        self.para_list[T_HOLD] = self.hold_ms
                    else:
                        # this is to not perform release after hold
                        if self.para_list[T_HOLD] > 0:
                            if self.para_list[H_RELEASE]:
                                self.para_list[H_RELEASE](self)
                            self.para_list[T_HOLD] = 0
                        else:
                            # do nothing as the button is released after hold
                            pass
            else:
                if self.para_list[T_DEBOUNCE] > 0:
                    self.para_list[T_DEBOUNCE] -= self.check_ms
            if self.para_list[T_HOLD] > 0:
                self.para_list[T_HOLD] -= self.check_ms
                if self.para_list[T_HOLD] <= 0:
                    if self.hold_repeat:
                        self.para_list[T_HOLD] = self.hold_repeat_ms
                    else:
                        self.para_list[T_HOLD] = 0
                    if self.para_list[H_HOLD]:
                        self.para_list[H_HOLD](self)
