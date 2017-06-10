import fcntl
import math
import os
import struct
from . channel_order import ChannelOrder
from . driver_base import DriverBase
from .. import log


class SpiBaseInterface(object):
    """ abstract class for different spi backends"""

    def __init__(self, dev, SPISpeed):
        self._dev = dev
        self._spi_speed = SPISpeed

    def send_packet(self, data):
        raise NotImplementedError

    def compute_packet(self, data):
        return data


# partial source @see https://armbedded.taskit.de/node/318
# @see <linux/spi/spidev.h>
# hex numbers from good old strace(1)
SPI_IOC_WR_MODE = 0x40016b01
SPI_IOC_RD_MODE = 0x80016b01
SPI_IOC_WR_BITS_PER_WORD = 0x40016b03
SPI_IOC_RD_BITS_PER_WORD = 0x80016b03
SPI_IOC_WR_MAX_SPEED_HZ = 0x40046b04
SPI_IOC_RD_MAX_SPEED_HZ = 0x80046b04


class SpiFileInterface(SpiBaseInterface):
    """ using os open/write to send data"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.exists(self._dev):
            error(CANT_FIND_ERROR)

        self._fnctl = fcntl
        self._spi = open(self._dev, 'wb')

        speed = self._set_speed(self._spi_speed)

        bits = self._set_bits_per_word(8)
        log.info('file io spi speed @ %.1f MHz, %d bits per word', speed / 1e6, bits)

    def _set_speed(self, speed):
        speed_b = struct.pack('>I', int(speed * 1e9))  # unint32
        self._fnctl.ioctl(self._spi, SPI_IOC_WR_MAX_SPEED_HZ, speed_b)

        self._fnctl.ioctl(self._spi, SPI_IOC_RD_MAX_SPEED_HZ, speed_b)
        speed = struct.unpack(">I", speed_b)[0] / 1000
        return speed

    def _set_bits_per_word(self, bits):
        bits_b = struct.pack('B', bits)  # uint8
        self._fnctl.ioctl(self._spi, SPI_IOC_WR_BITS_PER_WORD, bits_b)

        self._fnctl.ioctl(self._spi, SPI_IOC_RD_MAX_SPEED_HZ, bits_b)
        bits = int.from_bytes(bits_b, byteorder='big')
        return bits

    def send_packet(self, data):
        self._set_speed(self._spi_speed)
        package_size = 4032  # bit smaller than 4096 because of headers
        for i in range(int(math.ceil(len(data) / package_size))):
            start = i * package_size
            end = (i + 1) * package_size
            self._spi.write(data[start:end])
            self._spi.flush()


class SpiPyDevInterface(SpiBaseInterface):
    """ using py-spidev to send data"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        a, b = -1, -1
        d = self._dev.replace('/dev/spidev', '')
        s = d.split('.')
        if len(s) == 2:
            a = int(s[0])
            b = int(s[1])
        if a < 0 or b < 0:
            error(BAD_FORMAT_ERROR)

        self._device_id = a
        self._device_cs = b

        if not os.path.exists(self._dev):
            error(CANT_FIND_ERROR)
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
        self._spi.max_speed_hz = int(self._spi_speed * 1e6)
        log.info('py-spidev speed @ %.1f MHz', self._spi.max_speed_hz / 1e6)

    def send_packet(self, data):
        self._spi.xfer2(list(data))


class SpiDummyInterface(SpiBaseInterface):
    """ interface for testing proposal"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

    def send_packet(self, data):
        """ do nothing """
        pass


class DriverSPIBase(DriverBase):
    """Base driver for controling SPI devices on systems like the Raspberry Pi and BeagleBone"""

    def __init__(self, num, c_order=ChannelOrder.GRB, interface=SpiFileInterface,
                 dev='/dev/spidev0.0', SPISpeed=2, gamma=None):
        super().__init__(num, c_order=c_order, gamma=gamma)

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
    raise Exception(text)
