"""Build OSC messages for client applications."""

from . import osc_message
from .parsing import osc_types

from typing import List, Tuple, Union, Any, Optional


ArgValue = Union[str, bytes, bool, int, float, osc_types.MidiPacket, list]


class BuildError(Exception):
    """Error raised when an incomplete message is trying to be built."""


class OscMessageBuilder(object):
    """Builds arbitrary OscMessage instances."""

    ARG_TYPE_FLOAT = "f"
    ARG_TYPE_DOUBLE = "d"
    ARG_TYPE_INT = "i"
    ARG_TYPE_INT64 = "h"
    ARG_TYPE_STRING = "s"
    ARG_TYPE_BLOB = "b"
    ARG_TYPE_RGBA = "r"
    ARG_TYPE_MIDI = "m"
    ARG_TYPE_TRUE = "T"
    ARG_TYPE_FALSE = "F"
    ARG_TYPE_NIL = "N"

    ARG_TYPE_ARRAY_START = "["
    ARG_TYPE_ARRAY_STOP = "]"

    _SUPPORTED_ARG_TYPES = (
        ARG_TYPE_FLOAT, ARG_TYPE_DOUBLE, ARG_TYPE_INT, ARG_TYPE_INT64, ARG_TYPE_BLOB, ARG_TYPE_STRING,
        ARG_TYPE_RGBA, ARG_TYPE_MIDI, ARG_TYPE_TRUE, ARG_TYPE_FALSE, ARG_TYPE_NIL)

    def __init__(self, address: str=None) -> None:
        """Initialize a new builder for a message.

        Args:
          - address: The osc address to send this message to.
        """
        self._address = address
        self._args = []  # type: List[Tuple[str, Union[ArgValue, None]]]

    @property
    def address(self) -> Optional[str]:
        """Returns the OSC address this message will be sent to."""
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        """Sets the OSC address this message will be sent to."""
        self._address = value

    @property
    def args(self) -> List[Tuple[str, Union[ArgValue, None]]]:
        """Returns the (type, value) arguments list of this message."""
        return self._args

    def _valid_type(self, arg_type: str) -> bool:
        if arg_type in self._SUPPORTED_ARG_TYPES:
            return True
        elif isinstance(arg_type, list):
            for sub_type in arg_type:
                if not self._valid_type(sub_type):
                    return False
            return True
        return False

    def add_arg(self, arg_value: ArgValue, arg_type: str=None) -> None:
        """Add a typed argument to this message.

        Args:
          - arg_value: The corresponding value for the argument.
          - arg_type: A value in ARG_TYPE_* defined in this class,
                      if none then the type will be guessed.
        Raises:
          - ValueError: if the type is not supported.
        """
        if arg_type and not self._valid_type(arg_type):
            raise ValueError(
                'arg_type must be one of {}, or an array of valid types'
                    .format(self._SUPPORTED_ARG_TYPES))
        if not arg_type:
            arg_type = self._get_arg_type(arg_value)
        if isinstance(arg_type, list):
            self._args.append((self.ARG_TYPE_ARRAY_START, None))
            for v, t in zip(arg_value, arg_type):  # type: ignore[var-annotated, arg-type]
                self.add_arg(v, t)
            self._args.append((self.ARG_TYPE_ARRAY_STOP, None))
        else:
            self._args.append((arg_type, arg_value))

    # The return type here is actually Union[str, List[<self>]], however there
    # is no annotation for a recursive type like this.
    def _get_arg_type(self, arg_value: ArgValue) -> Union[str, Any]:
        """Guess the type of a value.

        Args:
          - arg_value: The value to guess the type of.
        Raises:
          - ValueError: if the type is not supported.
        """
        if isinstance(arg_value, str):
            arg_type = self.ARG_TYPE_STRING  # type: Union[str, Any]
        elif isinstance(arg_value, bytes):
            arg_type = self.ARG_TYPE_BLOB
        elif arg_value is True:
            arg_type = self.ARG_TYPE_TRUE
        elif arg_value is False:
            arg_type = self.ARG_TYPE_FALSE
        elif isinstance(arg_value, int):
            if arg_value.bit_length() > 32:
                arg_type = self.ARG_TYPE_INT64
            else:
                arg_type = self.ARG_TYPE_INT
        elif isinstance(arg_value, float):
            arg_type = self.ARG_TYPE_FLOAT
        elif isinstance(arg_value, tuple) and len(arg_value) == 4:
            arg_type = self.ARG_TYPE_MIDI
        elif isinstance(arg_value, list):
            arg_type = [self._get_arg_type(v) for v in arg_value]
        elif arg_value is None:
            arg_type = self.ARG_TYPE_NIL
        else:
            raise ValueError('Infered arg_value type is not supported')
        return arg_type

    def build(self) -> osc_message.OscMessage:
        """Builds an OscMessage from the current state of this builder.

        Raises:
          - BuildError: if the message could not be build or if the address
                        was empty.

        Returns:
          - an osc_message.OscMessage instance.
        """
        if not self._address:
            raise BuildError('OSC addresses cannot be empty')
        dgram = b''
        try:
            # Write the address.
            dgram += osc_types.write_string(self._address)
            if not self._args:
                dgram += osc_types.write_string(',')
                return osc_message.OscMessage(dgram)

            # Write the parameters.
            arg_types = "".join([arg[0] for arg in self._args])
            dgram += osc_types.write_string(',' + arg_types)
            for arg_type, value in self._args:
                if arg_type == self.ARG_TYPE_STRING:
                    dgram += osc_types.write_string(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_INT:
                    dgram += osc_types.write_int(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_INT64:
                    dgram += osc_types.write_int64(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_FLOAT:
                    dgram += osc_types.write_float(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_DOUBLE:
                    dgram += osc_types.write_double(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_BLOB:
                    dgram += osc_types.write_blob(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_RGBA:
                    dgram += osc_types.write_rgba(value)  # type: ignore[arg-type]
                elif arg_type == self.ARG_TYPE_MIDI:
                    dgram += osc_types.write_midi(value)  # type: ignore[arg-type]
                elif arg_type in (self.ARG_TYPE_TRUE,
                                  self.ARG_TYPE_FALSE,
                                  self.ARG_TYPE_ARRAY_START,
                                  self.ARG_TYPE_ARRAY_STOP,
                                  self.ARG_TYPE_NIL):
                    continue
                else:
                    raise BuildError('Incorrect parameter type found {}'.format(
                        arg_type))

            return osc_message.OscMessage(dgram)
        except osc_types.BuildError as be:
            raise BuildError('Could not build the message: {}'.format(be))
