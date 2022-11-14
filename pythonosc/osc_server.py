"""OSC Servers that receive UDP packets and invoke handlers accordingly.
"""

import asyncio
import os
import socketserver

from . import osc_bundle
from . import osc_message
from .dispatcher import Dispatcher

from asyncio import BaseEventLoop

from socket import socket as _socket
from typing import Any, Tuple, Union, cast, Coroutine

_RequestType = Union[_socket, Tuple[bytes, _socket]]
_AddressType = Union[Tuple[str, int], str]


class _UDPHandler(socketserver.BaseRequestHandler):
    """Handles correct UDP messages for all types of server."""

    def handle(self) -> None:
        """Calls the handlers via dispatcher

        This method is called after a basic sanity check was done on the datagram,
        whether this datagram looks like an osc message or bundle.
        If not the server won't call it and so no new
        threads/processes will be spawned.
        """
        server = cast(OSCUDPServer, self.server)
        server.dispatcher.call_handlers_for_packet(self.request[0], self.client_address)


def _is_valid_request(request: _RequestType) -> bool:
    """Returns true if the request's data looks like an osc bundle or message.

    Returns:
        True if request is OSC bundle or OSC message
    """
    assert isinstance(request, tuple)  # TODO: handle requests which are passed just as a socket?
    data = request[0]
    return (
            osc_bundle.OscBundle.dgram_is_bundle(data)
            or osc_message.OscMessage.dgram_is_message(data))


class OSCUDPServer(socketserver.UDPServer):
    """Superclass for different flavors of OSC UDP servers"""

    def __init__(self, server_address: Tuple[str, int], dispatcher: Dispatcher, bind_and_activate: bool = True) -> None:
        """Initialize

        Args:
            server_address: IP and port of server
            dispatcher: Dispatcher this server will use
            (optional) bind_and_activate: default=True defines if the server has to start on call of constructor  
        """
        super().__init__(server_address, _UDPHandler, bind_and_activate)  # type: ignore[call-arg]  # https://github.com/python/typeshed/pull/8542
        self._dispatcher = dispatcher

    def verify_request(self, request: _RequestType, client_address: _AddressType) -> bool:
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


class AsyncIOOSCUDPServer():
    """Asynchronous OSC Server

    An asynchronous OSC Server using UDP. It creates a datagram endpoint that runs in an event loop.
    """

    def __init__(self, server_address: Tuple[str, int], dispatcher: Dispatcher, loop: BaseEventLoop) -> None:
        """Initialize

        Args:
            server_address: IP and port of server
            dispatcher: Dispatcher this server shall use
            loop: Event loop to add the server task to. Use ``asyncio.get_event_loop()`` unless you know what you're
                doing.
        """

        self._server_address = server_address
        self._dispatcher = dispatcher
        self._loop = loop

    class _OSCProtocolFactory(asyncio.DatagramProtocol):
        """OSC protocol factory which passes datagrams to dispatcher"""

        def __init__(self, dispatcher: Dispatcher) -> None:
            self.dispatcher = dispatcher

        def datagram_received(self, data: bytes, client_address: Tuple[str, int]) -> None:
            self.dispatcher.call_handlers_for_packet(data, client_address)

    def serve(self) -> None:
        """Creates a datagram endpoint and registers it with event loop.

        Use this only in synchronous code (i.e. not from within a coroutine). This will start the server and run it
        forever or until a ``stop()`` is called on the event loop.
        """
        self._loop.run_until_complete(self.create_serve_endpoint())

    def create_serve_endpoint(self) -> Coroutine[Any, Any, Tuple[asyncio.transports.BaseTransport, asyncio.DatagramProtocol]]:
        """Creates a datagram endpoint and registers it with event loop as coroutine.

        Returns:
            Awaitable coroutine that returns transport and protocol objects
        """
        return self._loop.create_datagram_endpoint(
            lambda: self._OSCProtocolFactory(self.dispatcher),
            local_addr=self._server_address)

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher
