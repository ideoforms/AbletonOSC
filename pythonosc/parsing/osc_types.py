"""Functions to get OSC types from datagrams and vice versa"""

import struct

from . import ntp
from datetime import datetime, timedelta, date

from typing import Union, Tuple, cast

MidiPacket = Tuple[int, int, int, int]


class ParseError(Exception):
    """Base exception for when a datagram parsing error occurs."""


class BuildError(Exception):
    """Base exception for when a datagram building error occurs."""


# Constant for special ntp datagram sequences that represent an immediate time.
IMMEDIATELY = 0

# Datagram length in bytes for types that have a fixed size.
_INT_DGRAM_LEN = 4
_INT64_DGRAM_LEN = 8
_UINT64_DGRAM_LEN = 8
_FLOAT_DGRAM_LEN = 4
_DOUBLE_DGRAM_LEN = 8
_TIMETAG_DGRAM_LEN = 8
# Strings and blob dgram length is always a multiple of 4 bytes.
_STRING_DGRAM_PAD = 4
_BLOB_DGRAM_PAD = 4
_EMPTY_STR_DGRAM = b'\x00\x00\x00\x00'


def write_string(val: str) -> bytes:
    """Returns the OSC string equivalent of the given python string.

    Raises:
      - BuildError if the string could not be encoded.
    """
    try:
        dgram = val.encode('utf-8')  # Default, but better be explicit.
    except (UnicodeEncodeError, AttributeError) as e:
        raise BuildError('Incorrect string, could not encode {}'.format(e))
    diff = _STRING_DGRAM_PAD - (len(dgram) % _STRING_DGRAM_PAD)
    dgram += (b'\x00' * diff)
    return dgram


def get_string(dgram: bytes, start_index: int) -> Tuple[str, int]:
    """Get a python string from the datagram, starting at pos start_index.

    According to the specifications, a string is:
    "A sequence of non-null ASCII characters followed by a null,
    followed by 0-3 additional null characters to make the total number
    of bits a multiple of 32".

    Args:
      dgram: A datagram packet.
      start_index: An index where the string starts in the datagram.

    Returns:
      A tuple containing the string and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    if start_index < 0:
        raise ParseError('start_index < 0')
    offset = 0
    try:
        if (len(dgram) > start_index + _STRING_DGRAM_PAD
                and dgram[start_index + _STRING_DGRAM_PAD] == _EMPTY_STR_DGRAM):
            return '', start_index + _STRING_DGRAM_PAD
        while dgram[start_index + offset] != 0:
            offset += 1
        # Align to a byte word.
        if (offset) % _STRING_DGRAM_PAD == 0:
            offset += _STRING_DGRAM_PAD
        else:
            offset += (-offset % _STRING_DGRAM_PAD)
        # Python slices do not raise an IndexError past the last index,
        # do it ourselves.
        if offset > len(dgram[start_index:]):
            raise ParseError('Datagram is too short')
        data_str = dgram[start_index:start_index + offset]
        return data_str.replace(b'\x00', b'').decode('utf-8'), start_index + offset
    except IndexError as ie:
        raise ParseError('Could not parse datagram %s' % ie)
    except TypeError as te:
        raise ParseError('Could not parse datagram %s' % te)


def write_int(val: int) -> bytes:
    """Returns the datagram for the given integer parameter value

    Raises:
      - BuildError if the int could not be converted.
    """
    try:
        return struct.pack('>i', val)
    except struct.error as e:
        raise BuildError('Wrong argument value passed: {}'.format(e))


def get_int(dgram: bytes, start_index: int) -> Tuple[int, int]:
    """Get a 32-bit big-endian two's complement integer from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the integer starts in the datagram.

    Returns:
      A tuple containing the integer and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>i',
                          dgram[start_index:start_index + _INT_DGRAM_LEN])[0],
            start_index + _INT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def write_int64(val: int) -> bytes:
    """Returns the datagram for the given 64-bit big-endian signed parameter value

    Raises:
      - BuildError if the int64 could not be converted.
    """
    try:
        return struct.pack('>q', val)
    except struct.error as e:
        raise BuildError('Wrong argument value passed: {}'.format(e))


def get_int64(dgram: bytes, start_index: int) -> Tuple[int, int]:
    """Get a 64-bit big-endian signed integer from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the 64-bit integer starts in the datagram.

    Returns:
      A tuple containing the 64-bit integer and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT64_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>q',
                          dgram[start_index:start_index + _INT64_DGRAM_LEN])[0],
            start_index + _INT64_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_uint64(dgram: bytes, start_index: int) -> Tuple[int, int]:
    """Get a 64-bit big-endian unsigned integer from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the integer starts in the datagram.

    Returns:
      A tuple containing the integer and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _UINT64_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>Q',
                          dgram[start_index:start_index + _UINT64_DGRAM_LEN])[0],
            start_index + _UINT64_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def get_timetag(dgram: bytes, start_index: int) -> Tuple[Tuple[datetime, int], int]:
    """Get a 64-bit OSC time tag from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the osc time tag starts in the datagram.

    Returns:
      A tuple containing the tuple of time of sending in utc as datetime and the
      fraction of the current second and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _TIMETAG_DGRAM_LEN:
            raise ParseError('Datagram is too short')

        timetag, _ = get_uint64(dgram, start_index)
        seconds, fraction = ntp.parse_timestamp(timetag)

        hours, seconds = seconds // 3600, seconds % 3600
        minutes, seconds = seconds // 60, seconds % 60

        utc = (datetime.combine(ntp._NTP_EPOCH, datetime.min.time()) +
               timedelta(hours=hours, minutes=minutes, seconds=seconds))

        return (utc, fraction), start_index + _TIMETAG_DGRAM_LEN
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def write_float(val: float) -> bytes:
    """Returns the datagram for the given float parameter value

    Raises:
      - BuildError if the float could not be converted.
    """
    try:
        return struct.pack('>f', val)
    except struct.error as e:
        raise BuildError('Wrong argument value passed: {}'.format(e))


def get_float(dgram: bytes, start_index: int) -> Tuple[float, int]:
    """Get a 32-bit big-endian IEEE 754 floating point number from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the float starts in the datagram.

    Returns:
      A tuple containing the float and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _FLOAT_DGRAM_LEN:
            # Noticed that Reaktor doesn't send the last bunch of \x00 needed to make
            # the float representation complete in some cases, thus we pad here to
            # account for that.
            dgram = dgram + b'\x00' * (_FLOAT_DGRAM_LEN - len(dgram[start_index:]))
        return (
            struct.unpack('>f',
                          dgram[start_index:start_index + _FLOAT_DGRAM_LEN])[0],
            start_index + _FLOAT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def write_double(val: float) -> bytes:
    """Returns the datagram for the given double parameter value

    Raises:
      - BuildError if the double could not be converted.
    """
    try:
        return struct.pack('>d', val)
    except struct.error as e:
        raise BuildError('Wrong argument value passed: {}'.format(e))


def get_double(dgram: bytes, start_index: int) -> Tuple[float, int]:
    """Get a 64-bit big-endian IEEE 754 floating point number from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the double starts in the datagram.

    Returns:
      A tuple containing the double and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _DOUBLE_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>d',
                          dgram[start_index:start_index + _DOUBLE_DGRAM_LEN])[0],
            start_index + _DOUBLE_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram {}'.format(e))


def get_blob(dgram: bytes, start_index: int) -> Tuple[bytes, int]:
    """ Get a blob from the datagram.

    According to the specifications, a blob is made of
    "an int32 size count, followed by that many 8-bit bytes of arbitrary
    binary data, followed by 0-3 additional zero bytes to make the total
    number of bits a multiple of 32".

    Args:
      dgram: A datagram packet.
      start_index: An index where the float starts in the datagram.

    Returns:
      A tuple containing the blob and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    size, int_offset = get_int(dgram, start_index)
    # Make the size a multiple of 32 bits.
    total_size = size + (-size % _BLOB_DGRAM_PAD)
    end_index = int_offset + size
    if end_index - start_index > len(dgram[start_index:]):
        raise ParseError('Datagram is too short.')
    return dgram[int_offset:int_offset + size], int_offset + total_size


def write_blob(val: bytes) -> bytes:
    """Returns the datagram for the given blob parameter value.

    Raises:
      - BuildError if the value was empty or if its size didn't fit an OSC int.
    """
    if not val:
        raise BuildError('Blob value cannot be empty')
    dgram = write_int(len(val))
    dgram += val
    while len(dgram) % _BLOB_DGRAM_PAD != 0:
        dgram += b'\x00'
    return dgram


def get_date(dgram: bytes, start_index: int) -> Tuple[float, int]:
    """Get a 64-bit big-endian fixed-point time tag as a date from the datagram.

    According to the specifications, a date is represented as is:
    "the first 32 bits specify the number of seconds since midnight on
    January 1, 1900, and the last 32 bits specify fractional parts of a second
    to a precision of about 200 picoseconds".

    Args:
      dgram: A datagram packet.
      start_index: An index where the date starts in the datagram.

    Returns:
      A tuple containing the system date and the new end index.
      returns osc_immediately (0) if the corresponding OSC sequence was found.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    # Check for the special case first.
    if dgram[start_index:start_index + _TIMETAG_DGRAM_LEN] == ntp.IMMEDIATELY:
        return IMMEDIATELY, start_index + _TIMETAG_DGRAM_LEN
    if len(dgram[start_index:]) < _TIMETAG_DGRAM_LEN:
        raise ParseError('Datagram is too short')
    timetag, start_index = get_uint64(dgram, start_index)
    seconds = timetag * ntp._NTP_TIMESTAMP_TO_SECONDS
    return ntp.ntp_time_to_system_epoch(seconds), start_index


def write_date(system_time: Union[int, float]) -> bytes:
    if system_time == IMMEDIATELY:
        return ntp.IMMEDIATELY

    try:
        return ntp.system_time_to_ntp(system_time)
    except ntp.NtpError as ntpe:
        raise BuildError(ntpe)


def write_rgba(val: bytes) -> bytes:
    """Returns the datagram for the given rgba32 parameter value

    Raises:
      - BuildError if the int could not be converted.
    """
    try:
        return struct.pack('>I', val)
    except struct.error as e:
        raise BuildError('Wrong argument value passed: {}'.format(e))


def get_rgba(dgram: bytes, start_index: int) -> Tuple[bytes, int]:
    """Get an rgba32 integer from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the integer starts in the datagram.

    Returns:
      A tuple containing the integer and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        return (
            struct.unpack('>I',
                          dgram[start_index:start_index + _INT_DGRAM_LEN])[0],
            start_index + _INT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)


def write_midi(val: MidiPacket) -> bytes:
    """Returns the datagram for the given MIDI message parameter value

       A valid MIDI message: (port id, status byte, data1, data2).

    Raises:
      - BuildError if the MIDI message could not be converted.

    """
    if len(val) != 4:
        raise BuildError('MIDI message length is invalid')
    try:
        value = sum((value & 0xFF) << 8 * (3 - pos) for pos, value in enumerate(val))
        return struct.pack('>I', value)
    except struct.error as e:
        raise BuildError('Wrong argument value passed: {}'.format(e))


def get_midi(dgram: bytes, start_index: int) -> Tuple[MidiPacket, int]:
    """Get a MIDI message (port id, status byte, data1, data2) from the datagram.

    Args:
      dgram: A datagram packet.
      start_index: An index where the MIDI message starts in the datagram.

    Returns:
      A tuple containing the MIDI message and the new end index.

    Raises:
      ParseError if the datagram could not be parsed.
    """
    try:
        if len(dgram[start_index:]) < _INT_DGRAM_LEN:
            raise ParseError('Datagram is too short')
        val = struct.unpack('>I',
                            dgram[start_index:start_index + _INT_DGRAM_LEN])[0]
        midi_msg = cast(
            MidiPacket,
            tuple((val & 0xFF << 8 * i) >> 8 * i for i in range(3, -1, -1)))
        return (midi_msg, start_index + _INT_DGRAM_LEN)
    except (struct.error, TypeError) as e:
        raise ParseError('Could not parse datagram %s' % e)
