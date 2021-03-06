import socket, sys, time, os

from . driver_base import DriverBase
from .. import log, util
from .. return_codes import RETURN_CODES


class CMDTYPE:
    SETUP_DATA = 1  # reserved for future use
    PIXEL_DATA = 2
    BRIGHTNESS = 3


class NetworkUDP(DriverBase):
    """Driver for communicating with another device on the network."""

    def __init__(self, num=0, width=0, height=0, host="localhost",
                 broadcast=False, port=3142, broadcast_interface='', **kwds):
        super().__init__(num, width, height, **kwds)

        self._host = host
        self._port = port
        self._sock = None
        self._broadcast = broadcast
        self._broadcast_interface = broadcast_interface

    def _generateHeader(self, cmd, size):
        packet = bytearray()
        packet.append(cmd)
        packet.append(size & 0xFF)
        packet.append(size >> 8)
        return packet

    def _connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            if self._broadcast:
                self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            return self._sock
        except socket.gaierror:
            error = "Unable to connect to or resolve host: {}".format(
                self._host)
            log.error(error)
            raise IOError(error)

    def _compute_packet(self):
        count = self.bufByteCount()
        self._packet = util.generate_header(CMDTYPE.PIXEL_DATA, count)
        indexes = range(self._pos, self._pos + self.numLEDs)
        self._packet.extend(int(c) for i in indexes for c in self._colors[i])

    # Push new data to strand
    def _send_packet(self):
        try:
            s = self._connect()
            s.sendto(self._packet, (self._host, self._port))

            s.close()

        except Exception as e:
            log.exception(e)
            error = "Problem communicating with network receiver!"
            log.error(error)
            raise IOError(error)
