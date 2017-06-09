from .driver_base import DriverBase
import typing


class Virtual(DriverBase):
    def __init__(self, drivers: typing.List[DriverBase], pos_leds: typing.List[int], **kwargs):
        super().__init__(num=len(pos_leds), **kwargs)

        self._drivers = drivers
        self._pos_leds = pos_leds

    def _send_packet(self):
        i = 0
        for pos_led in self._pos_leds:
            j = 0
            while self._drivers[j].numLEDs < pos_led:
                pos_led -= self._drivers[j].numLEDs
                j += 1
            start_index = pos_led * 3
            self._drivers[i].set_colors(self._colors[start_index * 3:(start_index + 1) * 3], pos_led)
            i += 1
