import os
from . channel_order import ChannelOrder
from . driver_base import DriverBase
from .. import log


class SpiBaseInterface(object):
    """ abstract class for different spi backends"""

    def __init__(self, dev, SPISpeed):
        self._dev = dev
        self._spi_speed = SPISpeed
        a, b = -1, -1
        d = self._dev.replace("/dev/spidev", "")
        s = d.split('.')
        if len(s) == 2:
            a = int(s[0])
            b = int(s[1])
        if a < 0 or b < 0:
            error(BAD_FORMAT_ERROR)

        self._device_id = a
        self._device_cs = b

    def send_packet(self, data):
        raise NotImplementedError

    def compute_packet(self, data):
        return data


class SpiFileInterface(SpiBaseInterface):
    """ using os open/write to send data"""

    def __init__(self, **kwargs):
        super(SpiFileInterface, self).__init__(**kwargs)
        self._spi = open(self._dev, "wb")

    def send_packet(self, data):
        self._spi.write(bytearray(data))
        self._spi.flush()


class SpiPyDevInterface(SpiBaseInterface):
    """ using py-spidev to send data"""

    def __init__(self, **kwargs):
        super(SpiPyDevInterface, self).__init__(**kwargs)

        if not os.path.exists(self._dev):
            error(BAD_FORMAT_ERROR)
        # permissions check
        try:
            fd = open(self._dev, 'r')
            fd.close()
        except IOError as e:
            if e.errno == 13:
                error(PERMISSION_ERROR)
            else:
                raise e
        # import spidev and cache error
        try:
            import spidev
            self._spi = spidev.SpiDev()
        except ImportError:
            error(CANT_IMPORT_SPIDEV_ERROR)
        self._spi.open(self._device_id, self._device_cs)
        self._spi.max_speed_hz = int(self._spi_speed * 1000000.0)
        log.info('py-spidev speed @ %.1f MHz', (float(self._spi.max_speed_hz) / 1000000.0))

    def send_packet(self, data):
        self._spi.xfer2(data)


class SpiDummyInterface(SpiBaseInterface):
    """ interface for testing proposal"""

    def __init__(self, **kwargs):
        super(SpiDummyInterface, self).__init__(**kwargs)
        pass

    def send_packet(self, data):
        """ do nothing """
        pass


class DriverSPIBase(DriverBase):
    """Base driver for controling SPI devices on systems like the Raspberry Pi and BeagleBone"""

    def __init__(self, num, c_order=ChannelOrder.GRB, interface=SpiPyDevInterface,
                 dev="/dev/spidev0.0", SPISpeed=2, gamma=None):
        super(DriverSPIBase, self).__init__(num, c_order=c_order, gamma=gamma)

        self._interface = interface(dev=dev, SPISpeed=SPISpeed)

    def _send_packet(self):
        self._interface.send_packet(self._packet)

    def _compute_packet(self):
        self._render()
        self._packet = self._interface.compute_packet(self._buf)


PERMISSION_ERROR = """Cannot access SPI device.
Please see

    https://github.com/maniacallabs/bibliopixel/wiki/SPI-Setup

for details.
"""

CANT_FIND_ERROR = """Cannot find SPI device.
Please see

    https://github.com/maniacallabs/bibliopixel/wiki/SPI-Setup

for details.
"""

BAD_FORMAT_ERROR = (
    'When using py-spidev, `dev` must be in the format /dev/spidev*.*')

CANT_IMPORT_SPIDEV_ERROR = """
Unable to import spidev. Please install:

    pip install spidev
"""


def error(text):
    log.error(text)
    raise IOError(text)
