import logging

from . import osc_message
from .parsing import osc_types

from typing import Any, Iterator, List, Union

_BUNDLE_PREFIX = b"#bundle\x00"


class ParseError(Exception):
    """Base exception raised when a datagram parsing error occurs."""


class OscBundle(object):
    """Bundles elements that should be triggered at the same time.

    An element can be another OscBundle or an OscMessage.
    """

    def __init__(self, dgram: bytes) -> None:
        """Initializes the OscBundle with the given datagram.

        Args:
          dgram: a UDP datagram representing an OscBundle.

        Raises:
          ParseError: if the datagram could not be parsed into an OscBundle.
        """
        # Interesting stuff starts after the initial b"#bundle\x00".
        self._dgram = dgram
        index = len(_BUNDLE_PREFIX)
        try:
            self._timestamp, index = osc_types.get_date(self._dgram, index)
        except osc_types.ParseError as pe:
            raise ParseError("Could not get the date from the datagram: %s" % pe)
        # Get the contents as a list of OscBundle and OscMessage.
        self._contents = self._parse_contents(index)

    def _parse_contents(self, index: int) -> List[Union['OscBundle', osc_message.OscMessage]]:
        contents = []  # type: List[Union[OscBundle, osc_message.OscMessage]]

        try:
            # An OSC Bundle Element consists of its size and its contents.
            # The size is an int32 representing the number of 8-bit bytes in the
            # contents, and will always be a multiple of 4. The contents are either
            # an OSC Message or an OSC Bundle.
            while self._dgram[index:]:
                # Get the sub content size.
                content_size, index = osc_types.get_int(self._dgram, index)
                # Get the datagram for the sub content.
                content_dgram = self._dgram[index:index + content_size]
                # Increment our position index up to the next possible content.
                index += content_size
                # Parse the content into an OSC message or bundle.
                if OscBundle.dgram_is_bundle(content_dgram):
                    contents.append(OscBundle(content_dgram))
                elif osc_message.OscMessage.dgram_is_message(content_dgram):
                    contents.append(osc_message.OscMessage(content_dgram))
                else:
                    logging.warning(
                        "Could not identify content type of dgram %r" % content_dgram)
        except (osc_types.ParseError, osc_message.ParseError, IndexError) as e:
            raise ParseError("Could not parse a content datagram: %s" % e)

        return contents

    @staticmethod
    def dgram_is_bundle(dgram: bytes) -> bool:
        """Returns whether this datagram starts like an OSC bundle."""
        return dgram.startswith(_BUNDLE_PREFIX)

    @property
    def timestamp(self) -> float:
        """Returns the timestamp associated with this bundle."""
        return self._timestamp

    @property
    def num_contents(self) -> int:
        """Shortcut for len(*bundle) returning the number of elements."""
        return len(self._contents)

    @property
    def size(self) -> int:
        """Returns the length of the datagram for this bundle."""
        return len(self._dgram)

    @property
    def dgram(self) -> bytes:
        """Returns the datagram from which this bundle was built."""
        return self._dgram

    def content(self, index: int) -> Any:
        """Returns the bundle's content 0-indexed."""
        return self._contents[index]

    def __iter__(self) -> Iterator[Any]:
        """Returns an iterator over the bundle's content."""
        return iter(self._contents)
