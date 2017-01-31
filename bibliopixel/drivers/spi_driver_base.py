from .driver_base import DriverBase, ChannelOrder
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
            error = "When using spi, the given device must be in the format /dev/spidev*.*"
            log.error(error)
            raise ValueError(error)

        self._device_id = a
        self._device_cs = b

    def send_packet(self, data):
        pass

    def compute_packet(self, data):
        return data


class SpiFileInterface(SpiBaseInterface):
    def __init__(self, **kwargs):
        super(SpiFileInterface, self).__init__(**kwargs)
        # File based SPI requires a bytearray so we have to overwrite _buf
        self._buf = bytearray(self._buf)
        self.spi = open(self._dev, "wb")

    def send_packet(self, data):
        self.spi.write(data)
        self.spi.flush()


class SpiPyDevInterface(SpiBaseInterface):
    def __init__(self, **kwargs):
        super(SpiPyDevInterface, self).__init__(**kwargs)

        import os.path
        try:
            import spidev
        except:
            error = "Unable to import spidev. Please install. pip install spidev"
            log.error(error)
            raise ImportError(error)
        if not os.path.exists(self._dev):
            error = "Cannot find SPI device. Please see https://github.com/maniacallabs/bibliopixel/wiki/SPI-Setup for details."
            log.error(error)
            raise IOError(error)
        # permissions check
        try:
            open(self._dev)
        except IOError as e:
            if e.errno == 13:
                error = "Cannot find SPI device. Please see https://github.com/maniacallabs/bibliopixel/wiki/SPI-Setup for details."
                log.error(error)
                raise IOError(error)
            else:
                raise e
        import spidev
        self.spi = spidev.SpiDev()
        self.spi.open(self._device_id, self._device_cs)
        self.spi.max_speed_hz = int(self._spi_speed * 1000000.0)
        log.info('py-spidev speed @ %.1f MHz', (float(self.spi.max_speed_hz) / 1000000.0))

    def send_packet(self, data):
        self.spi.xfer2(data)


class SpiPiGpioInterface(SpiBaseInterface):
    def __init__(self, **kwargs):
        super(SpiPiGpioInterface, self).__init__(**kwargs)

        AUX_SPI = (1 << 8)
        try:
            import pigpio
        except:
            error = "Unable to import pigpio. Please install. http://abyz.co.uk/rpi/pigpio/"
            log.error(error)
            raise ImportError(error)
        self.pi = pigpio.pi()
        self.spi = self.pi.spi_open(self._device_id, 50000, AUX_SPI)

    def send_packet(self, data):
        self.pi.spi_write(self.spi, data)


class SpiDummyInterface(SpiBaseInterface):
    """ interface for testing proposal"""
    def __init__(self, **kwargs):
        super(SpiDummyInterface, self).__init__(**kwargs)
        pass


class DriverSPIBase(DriverBase):
    """Base driver for controling SPI devices on systems like the Raspberry Pi and BeagleBone"""

    def __init__(self, num, c_order=ChannelOrder.GRB, interface=SpiPyDevInterface,
                 dev="/dev/spidev0.0", SPISpeed=2, gamma=None):
        super(DriverSPIBase, self).__init__(num, c_order=c_order, gamma=gamma)

        self.interface = interface(dev=dev, SPISpeed=SPISpeed)

    def _send_packet(self):
        self.interface.send_packet(self._packet)

    def _compute_packet(self):
        self._render()
        self._packet = self.interface.compute_packet(self._buf)
