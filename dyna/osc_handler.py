from . import OSC
import errno
import socket
import traceback

import logging

class OSCHandler:
    def __init__(self, local_addr=('127.0.0.1', 9000), remote_addr=('127.0.0.1', 9001)):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)

        self._local_addr = local_addr
        self._remote_addr = remote_addr

        self._socket.bind(self._local_addr)
        self.logger = logging.getLogger("liveosc")

        self.logger.info('Starting on: ' + str(self._local_addr) + ', remote addr: ' + str(self._remote_addr))

        self._callback_manager = OSC.CallbackManager()
        self._callback_manager.add("/test", lambda msg, source: self.logger.info("Received test!"))

    def send(self, address, msg):
        oscmsg = OSC.OSCMessage(address, msg)
        if len(oscmsg.error) > 0:
            self.logger.info('OSCMessage Error: ' + ''.join(oscmsg.error))

        self._socket.sendto(oscmsg.getBinary(), self._remote_addr)

    def send_message(self, message):
        self._socket.sendto(message.getBinary(), self._remote_addr)

    def process(self):
        try:
            while 1:
                self._data, self._addr = self._socket.recvfrom(65536)
                self.logger.info("Received %d" % len(self._data))
                try:
                    self._callback_manager.handle(self._data, self._addr)

                except OSC.NoSuchCallback as e:
                    errmsg = 'Unknown callback: ' + str(e.args[0])
                    self.logger.info('LiveOSC: ' + errmsg)

                except Exception as e:
                    errmsg = type(e).__name__ + ': ' + str(e.args[0])

                    self.logger.info('LiveOSC: error handling message ' + errmsg)
                    self.logger.info("".join(traceback.format_exc()))

        except socket.error as e:
            if e.errno == errno.EAGAIN:
                return
            else:
                pass

        except Exception as e:
            self.logger.warning('LiveOSC: error handling message ' + type(e).__name__ + ':' + str(e.args[0]))

    def shutdown(self):
        self._socket.close()
