"""Use OSC packets to parse incoming UDP packets into messages or bundles.

It lets you access easily to OscMessage and OscBundle instances in the packet.
"""

import time

from .parsing import osc_types
from . import osc_bundle
from . import osc_message

from typing import Union, List, NamedTuple

# A namedtuple as returned my the _timed_msg_of_bundle function.
# 1) the system time at which the message should be executed
#    in seconds since the epoch.
# 2) the actual message.
TimedMessage = NamedTuple('TimedMessage', [
    ('time', float),
    ('message', osc_message.OscMessage),
])


def _timed_msg_of_bundle(bundle: osc_bundle.OscBundle, now: float) -> List[TimedMessage]:
    """Returns messages contained in nested bundles as a list of TimedMessage."""
    msgs = []
    for content in bundle:
        if type(content) is osc_message.OscMessage:
            if (bundle.timestamp == osc_types.IMMEDIATELY or bundle.timestamp < now):
                msgs.append(TimedMessage(now, content))
            else:
                msgs.append(TimedMessage(bundle.timestamp, content))
        else:
            msgs.extend(_timed_msg_of_bundle(content, now))
    return msgs


class ParseError(Exception):
    """Base error thrown when a packet could not be parsed."""


class OscPacket(object):
    """Unit of transmission of the OSC protocol.

    Any application that sends OSC Packets is an OSC Client.
    Any application that receives OSC Packets is an OSC Server.
    """

    def __init__(self, dgram: bytes) -> None:
        """Initialize an OdpPacket with the given UDP datagram.

        Args:
          - dgram: the raw UDP datagram holding the OSC packet.

        Raises:
          - ParseError if the datagram could not be parsed.
        """
        now = time.time()
        try:
            if osc_bundle.OscBundle.dgram_is_bundle(dgram):
                self._messages = sorted(
                    _timed_msg_of_bundle(osc_bundle.OscBundle(dgram), now),
                    key=lambda x: x.time)
            elif osc_message.OscMessage.dgram_is_message(dgram):
                self._messages = [TimedMessage(now, osc_message.OscMessage(dgram))]
            else:
                # Empty packet, should not happen as per the spec but heh, UDP...
                raise ParseError(
                    'OSC Packet should at least contain an OscMessage or an '
                    'OscBundle.')
        except (osc_bundle.ParseError, osc_message.ParseError) as pe:
            raise ParseError('Could not parse packet %s' % pe)

    @property
    def messages(self) -> List[TimedMessage]:
        """Returns asc-time-sorted TimedMessages of the messages in this packet."""
        return self._messages
