from .spi_driver_base import DriverSPIBase, ChannelOrder
import os
from .. import gamma


class DriverWS2812(DriverSPIBase):
    """SPI driver for WS2812 based LED strips on devices like the Raspberry Pi, OrangePi, BeagleBone,.."""

    def __init__(self, num, use_py_spi=True, dev="/dev/spidev0.0"):
       super(DriverWS2812, self).__init__(num, c_order=ChannelOrder.GRB, dev=dev, SPISpeed=3)

        self.gamma = gamma.WS2812

    # WS2812 requires gamma correction so we run it through gamma as the
    # channels are orderedi
    # As an hack to emulate PWM we use 3 bit on an SPI interface.
    # data -> spi
    # 0b0 -> 0b100
    # 0b1 -> 0b110
    def _fixData(self, data):
        #allocate buffer for gamma correction
        buf = [0] * self.bufByteCount
        for a, b in enumerate(self.c_order):
            buf[a:self.numLEDs * 3:3] = [self.gamma[v] for v in data[b::3]]

        #buffer for result
        buf2 = []
        for byte in buf:
            # save each byte in an 32(24 bit uses) int var
            tmp = 0
            for i in range(8):
                tmp |= (0b100 | (0b10 if (byte & 1 << i) > 0 else 0)) << (i * 3)
            #save each byte in little endian
            buf2.append(tmp >> 16 & 0xff)
            buf2.append(tmp >> 8 & 0xff)
            buf2.append(tmp & 0xff)
        self._buf = buf2

MANIFEST = [
    {
        "id": "WS2812SPI",
        "class": DriverWS2812SPI,
        "type": "driver",
        "display": "WS2812 (SPI)",
        "desc": "Interface with WS2812 / WS2812B strips over a native SPI port (Pi, BeagleBone, etc.)",
        "params": [{
                "id": "num",
                "label": "# Pixels",
                "type": "int",
                "default": 1,
                "min": 1,
                "help": "Total pixels in display."
        }, {
            "id": "dev",
            "label": "SPI Device Path",
            "type": "str",
            "default": "/dev/spidev0.0",
        }, {
            "id": "use_py_spi",
            "label": "Use PySPI",
            "type": "bool",
            "default": True,
            "group": "Advanced"
        }]
    }
]
