from typing import Tuple, Any, Callable
from ..pythonosc.osc_message import OscMessage, ParseError
from ..pythonosc.osc_message_builder import OscMessageBuilder, BuildError

import errno
import socket
import logging
import traceback

class OSCServer:
    def __init__(self, local_addr=('127.0.0.1', 9000), remote_addr=('127.0.0.1', 9001)):
        """
        Implemented because pythonosc's OSC server causes a beachball when handling
        incoming messages. To investigate, as it would be ultimately better not to have
        to roll our own.
        """
        self._local_addr = local_addr
        self._remote_addr = remote_addr

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        self._socket.bind(self._local_addr)
        self._callbacks = {}

        self.logger = logging.getLogger("liveosc")
        self.logger.info("Starting OSC server (local %s, remote %s)",
                         str(self._local_addr), str(self._remote_addr))

    def add_handler(self, address: str, handler: Callable):
        self._callbacks[address] = handler

    def send(self, address: str, params: Tuple[Any] = ()) -> None:
        """
        Args:
            address: The OSC address (e.g. /frequency)
            params: A tuple of zero or more OSC params
        """
        msg_builder = OscMessageBuilder(address)
        for param in params:
            msg_builder.add_arg(param)

        try:
            msg = msg_builder.build()
            self._socket.sendto(msg.dgram, self._remote_addr)
        except BuildError:
            self.logger.info("LiveOSC: OSC build error: %s" % (traceback.format_exc()))


    def process(self) -> None:
        """
        Synchronously process all data queued on the OSC socket.
        """
        try:
            while True:
                data, addr = self._socket.recvfrom(65536)
                try:
                    message = OscMessage(data)

                    if message.address in self._callbacks:
                        callback = self._callbacks[message.address]
                        callback(message.address, message.params)
                    else:
                        self.logger.info("LiveOSC: Unknown OSC address: %s" % message.address)
                except ParseError:
                    self.logger.info("LiveOSC: OSC parse error: %s" % (traceback.format_exc()))

        except socket.error as e:
            if e.errno == errno.EAGAIN:
                return
            else:
                self.logger.info("LiveOSC: Socket error: %s" % (traceback.format_exc()))

        except Exception as e:
            self.logger.info("LiveOSC: Error handling message: %s" % (traceback.format_exc()))

    def shutdown(self) -> None:
        """
        Shutdown the server network sockets.
        """
        self._socket.close()
