"""OSC Servers that receive UDP packets and invoke handlers accordingly.
"""

import os
import socketserver

from . import osc_bundle
from . import osc_message
from .dispatcher import Dispatcher

from typing import List, Tuple
from types import coroutine


class _UDPHandler(socketserver.BaseRequestHandler):
    """Handles correct UDP messages for all types of server."""

    def handle(self) -> None:
        """Calls the handlers via dispatcher

        This method is called after a basic sanity check was done on the datagram,
        whether this datagram looks like an osc message or bundle.
        If not the server won't call it and so no new
        threads/processes will be spawned.
        """
        self.server.dispatcher.call_handlers_for_packet(self.request[0], self.client_address)


def _is_valid_request(request: List[bytes]) -> bool:
    """Returns true if the request's data looks like an osc bundle or message.

    Returns:
        True if request is OSC bundle or OSC message
    """
    data = request[0]
    return (
            osc_bundle.OscBundle.dgram_is_bundle(data)
            or osc_message.OscMessage.dgram_is_message(data))


class OSCUDPServer(socketserver.UDPServer):
    """Superclass for different flavors of OSC UDP servers"""

    def __init__(self, server_address: Tuple[str, int], dispatcher: Dispatcher) -> None:
        """Initialize

        Args:
            server_address: IP and port of server
            dispatcher: Dispatcher this server will use
        """
        super().__init__(server_address, _UDPHandler)
        self._dispatcher = dispatcher

    def verify_request(self, request: List[bytes], client_address: Tuple[str, int]) -> bool:
        """Returns true if the data looks like a valid OSC UDP datagram

        Args:
            request: Incoming data
            client_address: IP and port of client this message came from

        Returns:
            True if request is OSC bundle or OSC message
        """
        return _is_valid_request(request)

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher


class BlockingOSCUDPServer(OSCUDPServer):
    """Blocking version of the UDP server.

    Each message will be handled sequentially on the same thread.
    Use this is you don't care about latency in your message handling or don't
    have a multiprocess/multithread environment.
    """


class ThreadingOSCUDPServer(socketserver.ThreadingMixIn, OSCUDPServer):
    """Threading version of the OSC UDP server.

    Each message will be handled in its own new thread.
    Use this when lightweight operations are done by each message handlers.
    """


if hasattr(os, "fork"):
    class ForkingOSCUDPServer(socketserver.ForkingMixIn, OSCUDPServer):
        """Forking version of the OSC UDP server.

        Each message will be handled in its own new process.
        Use this when heavyweight operations are done by each message handlers
        and forking a whole new process for each of them is worth it.
        """



