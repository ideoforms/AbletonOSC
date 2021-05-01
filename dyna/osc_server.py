from . import OSC
from typing import Tuple, Any

import errno
import socket
import traceback

import logging

class OSCServer:
    def __init__(self, local_addr=('127.0.0.1', 9000), remote_addr=('127.0.0.1', 9001)):
        self._local_addr = local_addr
        self._remote_addr = remote_addr

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        self._socket.bind(self._local_addr)

        self.logger = logging.getLogger("liveosc")
        self.logger.info("Starting OSC server (local %s, remote %s)",
                         str(self._local_addr), str(self._remote_addr))

        self._callback_manager = OSC.CallbackManager()
        self._callback_manager.add("/test", lambda msg, source: self.logger.info("Received test!"))

    def send(self, address: str, params: Tuple[Any] = ()) -> None:
        """
        Args:
            address: The OSC address (e.g. /frequency)
            params: A tuple of zero or more OSC params
        """
        oscmsg = OSC.OSCMessage(address, params)
        if len(oscmsg.error) > 0:
            self.logger.info("Error sending OSC message: %s" % oscmsg.error)

        self._socket.sendto(oscmsg.getBinary(), self._remote_addr)

    def process(self) -> None:
        """
        Synchronously process all data queued on the OSC socket.
        """
        try:
            while 1:
                data, addr = self._socket.recvfrom(65536)
                try:
                    self._callback_manager.handle(data, addr)

                except OSC.NoSuchCallback as e:
                    errmsg = 'Unknown callback: ' + str(e.args[0])
                    self.logger.info('LiveOSC: ' + errmsg)

                except Exception as e:
                    errmsg = type(e).__name__ + ': ' + str(e.args[0])

                    self.logger.info('LiveOSC: Error handling message: ' + errmsg)
                    self.logger.info("".join(traceback.format_exc()))

        except socket.error as e:
            if e.errno == errno.EAGAIN:
                return
            else:
                pass

        except Exception as e:
            self.logger.warning('LiveOSC: error handling message ' + type(e).__name__ + ':' + str(e.args[0]))

    def shutdown(self) -> None:
        """
        Shutdown the server network sockets.
        """
        self._socket.close()
