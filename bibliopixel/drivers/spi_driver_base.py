from . driver_base import DriverBase, ChannelOrder
import time

import os
from .. import log


class SpiInterface(object):
    FILE = 0
    PY_SPI = 1
    PI_GPIO = 2


class DriverSPIBase(DriverBase):
    """Base driver for controling SPI devices on systems like the Raspberry Pi and BeagleBone"""

    def __init__(self, num, c_order=ChannelOrder.GRB, interface=SpiInterface.PY_SPI,
                 dev="/dev/spidev0.0", SPISpeed=2, open=open, gamma=None):
        super(DriverSPIBase,self).__init__(num, c_order=c_order, gamma=gamma)

        self.dev = dev
        self.interface = interface
        self._spiSpeed = SPISpeed

        if self.interface == SpiInterface.PI_GPIO:
            a, b = -1, -1
            d = self.dev.replace("/dev/spidev", "")
            s = d.split('.')
            if len(s) == 2:
                a = int(s[0])
                b = int(s[1])
            if a < 0 or b < 0:
                error = "When using py-spidev, the given device must be in the format /dev/spidev*.*"
                log.error(error)
                raise ValueError(error)
            AUX_SPI = (1 << 8)
            import pigpio
            self.pi = pigpio.pi()
            self.spi = self.pi.spi_open(a, 50000, AUX_SPI)
        elif self.interface == SpiInterface.PY_SPI:
            a, b = -1, -1
            d = self.dev.replace("/dev/spidev", "")
            s = d.split('.')
            if len(s) == 2:
                a = int(s[0])
                b = int(s[1])
            if a < 0 or b < 0:
                error = "When using py-spidev, the given device must be in the format /dev/spidev*.*"
                log.error(error)
                raise ValueError(error)
            self._bootstrapPYSPIDev()
            import spidev
            self.spi = spidev.SpiDev()
            self.spi.open(a, b)
            self.spi.max_speed_hz = int(self._spiSpeed * 1000000.0)
            log.info('py-spidev speed @ %.1f MHz',
                     (float(self.spi.max_speed_hz) / 1000000.0))
        elif self.interface == SpiInterface.FILE:
            # File based SPI requires a bytearray so we have to overwrite _buf
            self._buf = bytearray(self._buf)
            self.spi = open(self.dev, "wb")
        else:
            raise ValueError('invalid interface')

    def _bootstrapPYSPIDev(self):
        import os.path
        if self.interface == SpiInterface.PY_SPI:
            try:
                import spidev
            except:
                error = "Unable to import spidev. Please install. pip install spidev"
                log.error(error)
                raise ImportError(error)
            if not os.path.exists(self.dev):
                error = "Cannot find SPI device. Please see https://github.com/maniacallabs/bibliopixel/wiki/SPI-Setup for details."
                log.error(error)
                raise IOError(error)
            # permissions check
            try:
                open(self.dev)
            except IOError as e:
                if e.errno == 13:
                    error = "Cannot find SPI device. Please see https://github.com/maniacallabs/bibliopixel/wiki/SPI-Setup for details."
                    log.error(error)
                    raise IOError(error)
                else:
                    raise e

    def _send_packet(self):
        if self.interface == SpiInterface.PI_GPIO:
            self.pi.spi_write(self.spi, self._packet)
        elif self.interface == SpiInterface.PY_SPI:
            self.spi.xfer2(self._packet)
        elif self.interface == SpiInterface.FILE:
            self.spi.write(self._packet)
            self.spi.flush()

    def _compute_packet(self):
        self._render()
        if self.interface is not SpiInterface.FILE:
            self._packet = self._buf
