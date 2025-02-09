import sys
from typing import Tuple, Any, Callable
from .constants import OSC_LISTEN_PORT, OSC_RESPONSE_PORT
from ..pythonosc.osc_message import OscMessage, ParseError
from ..pythonosc.osc_bundle import OscBundle
from ..pythonosc.osc_message_builder import OscMessageBuilder, BuildError

import re
import errno
import socket
import logging
import traceback
import random

class OSCServer:
    def __init__(self,
                 local_addr: Tuple[str, int] = ('0.0.0.0', OSC_LISTEN_PORT),
                 remote_addr: Tuple[str, int] = ('127.0.0.1', OSC_RESPONSE_PORT)):
        """
        Class that handles OSC server responsibilities, including support for sending
        reply messages.

        Implemented because pythonosc's OSC server causes a beachball when handling
        incoming messages. To investigate, as it would be ultimately better not to have
        to roll our own.

        Args:
            local_addr: Local address and port to listen on.
                        By default, binds to the wildcard address 0.0.0.0, which means listening on
                        every available local IPv4 interface (including 127.0.0.1).
            remote_addr: Remote address to send replies to, by default. Can be overridden in send().
        """

        self._local_addr = local_addr
        self._remote_addr = remote_addr
        self._response_port = remote_addr[1]

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        self._socket.bind(self._local_addr)
        self._callbacks = {}

        self.logger = logging.getLogger("abletonosc")
        self.logger.info("Starting OSC server (local %s, response port %d)",
                         str(self._local_addr), self._response_port)
        max_chunk_size = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        self.logger.info(f"Socket message size limit: {max_chunk_size} bytes")

    def add_handler(self, address: str, handler: Callable) -> None:
        """
        Add an OSC handler.

        Args:
            address: The OSC address string
            handler: A handler function, with signature:
                     params: Tuple[Any, ...]
        """
        self._callbacks[address] = handler

    def clear_handlers(self) -> None:
        """
        Remove all existing OSC handlers.
        """
        self._callbacks = {}

    def send(self,
             address: str,
             params: Tuple = (),
             remote_addr: Tuple[str, int] = None) -> None:
        """
        Send an OSC message.

        Args:
            address: The OSC address (e.g. /frequency)
            params: A tuple of zero or more OSC params
            remote_addr: The remote address to send to, as a 2-tuple (hostname, port).
                         If None, uses the default remote address.
        """
        chunks = []
        max_chunk_size = min(self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF), 47000)
        self.logger.debug(f"Max chunk size {max_chunk_size}")
        #  calculate total size of params in bytes
        total_size = sys.getsizeof(params)
        for item in params:
            total_size += sys.getsizeof(item)

        if total_size <= max_chunk_size:
            # the whole params fit in 1 chunk
            chunks = [params]
        else:
            # Split the data into smaller chunks to avoid the "Message Too Long" error
            # If the data is split into chunks, the last 4 pieces of information of a chunk are
            # chunk index, total chunks, message id, '#$#'
            current_chunk = []
            current_size = 0

            for item in params:
                item_size = sys.getsizeof(item)
                
                if current_size + item_size <= max_chunk_size:
                    current_chunk.append(item)
                    current_size += item_size
                else:
                    chunks.append(tuple(current_chunk))
                    current_chunk = [item]
                    current_size = item_size

            # Add the last chunk if it is not empty
            if current_chunk:
                chunks.append(tuple(current_chunk))

        total_chunks = len(chunks)
        updated_chunks = []
        self.logger.debug(f"total chunks {total_chunks}")

        if total_chunks > 1:
            msg_id = random.randint(1, 127)
            self.logger.info(f"Long message, split into {total_chunks} chunks before sending. msg id {msg_id}")

            for index, chunk in enumerate(chunks):
                updated_chunk = chunk + (index, total_chunks, msg_id, '#$#')
                self.logger.debug(f"updated chunk {updated_chunk}")

                updated_chunks.append(updated_chunk)

        self.logger.debug(f"updated chunks {updated_chunks}")
        # Select chunks to iterate based on the total number of chunks
        chunks_to_iterate = updated_chunks if total_chunks > 1 else chunks
        self.logger.debug(f"chunks to iterate {chunks_to_iterate}")

        for chunk in chunks_to_iterate:
            msg_builder = OscMessageBuilder(address)
            for param in chunk:
                msg_builder.add_arg(param)

            try:
                msg = msg_builder.build()
                if remote_addr is None:
                    remote_addr = self._remote_addr
                self._socket.sendto(msg.dgram, remote_addr)
            except BuildError:
                self.logger.error("AbletonOSC: OSC build error: %s" % (traceback.format_exc()))

    def process_message(self, message, remote_addr):
        if message.address in self._callbacks:
            callback = self._callbacks[message.address]
            rv = callback(message.params)

            if rv is not None:
                assert isinstance(rv, tuple)
                remote_hostname, _ = remote_addr
                response_addr = (remote_hostname, self._response_port)
                self.send(address=message.address,
                          params=rv,
                          remote_addr=response_addr)
        elif "*" in message.address:
            regex = message.address.replace("*", "[^/]+")
            for callback_address, callback in self._callbacks.items():
                if re.match(regex, callback_address):
                    try:
                        rv = callback(message.params)
                    except ValueError:
                        #--------------------------------------------------------------------------------
                        # Don't throw errors for queries that require more arguments
                        # (e.g. /live/track/get/send with no args)
                        #--------------------------------------------------------------------------------
                        continue
                    except AttributeError:
                        #--------------------------------------------------------------------------------
                        # Don't throw errors when trying to create listeners for properties that can't
                        # be listened for (e.g. can_be_armed, is_foldable)
                        #--------------------------------------------------------------------------------
                        continue
                    if rv is not None:
                        assert isinstance(rv, tuple)
                        remote_hostname, _ = remote_addr
                        response_addr = (remote_hostname, self._response_port)
                        self.send(address=callback_address,
                                  params=rv,
                                  remote_addr=response_addr)
        else:
            self.logger.error("AbletonOSC: Unknown OSC address: %s" % message.address)

    def process_bundle(self, bundle, remote_addr):
        for i in bundle:
            if OscBundle.dgram_is_bundle(i.dgram):
                self.process_bundle(i, remote_addr)
            else:
                self.process_message(i, remote_addr)

    def parse_bundle(self, data, remote_addr):
        if OscBundle.dgram_is_bundle(data):
            try:
                bundle = OscBundle(data)
                self.process_bundle(bundle, remote_addr)
            except ParseError:
                self.logger.error("AbletonOSC: Error parsing OSC bundle: %s" % (traceback.format_exc()))
        else:
            try:
                message = OscMessage(data)
                self.process_message(message, remote_addr)
            except ParseError:
                self.logger.error("AbletonOSC: Error parsing OSC message: %s" % (traceback.format_exc()))

    def process(self) -> None:
        """
        Synchronously process all data queued on the OSC socket.
        """
        try:
            repeats = 0
            while True:
                #--------------------------------------------------------------------------------
                # Loop until no more data is available.
                #--------------------------------------------------------------------------------
                data, remote_addr = self._socket.recvfrom(65536)
                #--------------------------------------------------------------------------------
                # Update the default reply address to the most recent client. Used when
                # sending (e.g) /live/song/beat messages and listen updates.
                #
                # This is slightly ugly and prevents registering listeners from different IPs.
                #--------------------------------------------------------------------------------
                self._remote_addr = (remote_addr[0], OSC_RESPONSE_PORT)
                self.parse_bundle(data, remote_addr)

        except socket.error as e:
            if e.errno == errno.ECONNRESET:
                #--------------------------------------------------------------------------------
                # This benign error seems to occur on startup on Windows
                #--------------------------------------------------------------------------------
                self.logger.warning("AbletonOSC: Non-fatal socket error: %s" % (traceback.format_exc()))
            elif e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                #--------------------------------------------------------------------------------
                # Another benign networking error, throw when no data is received
                # on a call to recvfrom() on a non-blocking socket
                #--------------------------------------------------------------------------------
                pass
            else:
                #--------------------------------------------------------------------------------
                # Something more serious has happened
                #--------------------------------------------------------------------------------
                self.logger.error("AbletonOSC: Socket error: %s" % (traceback.format_exc()))

        except Exception as e:
            self.logger.error("AbletonOSC: Error handling OSC message: %s" % e)
            self.logger.warning("AbletonOSC: %s" % traceback.format_exc())

    def shutdown(self) -> None:
        """
        Shutdown the server network sockets.
        """
        self._socket.close()
