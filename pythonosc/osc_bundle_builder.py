"""Build OSC bundles for client applications."""

from typing import List

from . import osc_bundle
from . import osc_message
from .parsing import osc_types

# Shortcut to specify an immediate execution of messages in the bundle.
IMMEDIATELY = osc_types.IMMEDIATELY


class BuildError(Exception):
    """Error raised when an error occurs building the bundle."""


class OscBundleBuilder(object):
    """Builds arbitrary OscBundle instances."""

    def __init__(self, timestamp: int) -> None:
        """Build a new bundle with the associated timestamp.

        Args:
          - timestamp: system time represented as a floating point number of
                       seconds since the epoch in UTC or IMMEDIATELY.
        """
        self._timestamp = timestamp
        self._contents = []  # type: List[osc_bundle.OscBundle]

    def add_content(self, content: osc_bundle.OscBundle) -> None:
        """Add a new content to this bundle.

        Args:
          - content: Either an OscBundle or an OscMessage
        """
        self._contents.append(content)

    def build(self) -> osc_bundle.OscBundle:
        """Build an OscBundle with the current state of this builder.

        Raises:
          - BuildError: if we could not build the bundle.
        """
        dgram = b'#bundle\x00'
        try:
            dgram += osc_types.write_date(self._timestamp)
            for content in self._contents:
                if (type(content) == osc_message.OscMessage
                        or type(content) == osc_bundle.OscBundle):
                    size = content.size
                    dgram += osc_types.write_int(size)
                    dgram += content.dgram
                else:
                    raise BuildError(
                        "Content must be either OscBundle or OscMessage"
                        "found {}".format(type(content)))
            return osc_bundle.OscBundle(dgram)
        except osc_types.BuildError as be:
            raise BuildError('Could not build the bundle {}'.format(be))
