from .driver_base import DriverBase
from ..threads.update_threading import UpdateThreading


class Virtual(DriverBase):
    def __init__(self, drivers, pos_leds, threadedUpdate=False, **kwargs):
        super().__init__(num=len(pos_leds), **kwargs)

        self.drivers = drivers if isinstance(drivers, list) else [drivers]
        self._pos_leds = pos_leds

        # if not hasattr(self, 'numLEDs'):
        #     numLEDsdrivers = sum(d.numLEDs for d in self.drivers)

        # This buffer will always be the same list - i.e. is guaranteed to only
        # be changed by list surgery, never assignment.
        #self._colors = maker.color_list(self.numLEDsdrivers)

        pos = 0
        for d in self.drivers:
            d.set_colors(self._colors, pos)
            pos += d.numLEDs

        self.threading = UpdateThreading(threadedUpdate, self)

        for driver in self.drivers:
            driver.set_brightness(255)

    def _compute_packet(self):
        i = 0

        for pos_led in self._pos_leds:
            j = 0
            while self.drivers[j].numLEDs < pos_led:
                pos_led -= self.drivers[j].numLEDs
                j += 1
            # start_index = pos_led * 3
            # self._drivers[i].set_colors(self._colors[start_index * 3:(start_index + 1) * 3], pos_led)
            print('i={:D},j={:d}, color={},pos_led={:d}'.format(i, j, self._colors[i], pos_led))
            self.drivers[j]._colors[pos_led] =self._colors[i]
            i += 1

    def _send_packet(self):
        self.threading.push_to_driver()
