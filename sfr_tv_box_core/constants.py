"""Shared constants for the sfr-box-remote library."""

from enum import StrEnum


class CommandType(StrEnum):
    """Abstract CommandType names.

    These define the high-level commands supported by the SFR boxes.
    Each driver is responsible for translating these into specific
    protocol messages.
    """

    SEND_KEY = "SEND_KEY"
    GET_STATUS = "GET_STATUS"
    GET_VERSIONS = "GET_VERSIONS"


class KeyCode(StrEnum):
    """Abstract KeyCode names.

    These are shared across all box models. The specific driver for each
    model is responsible for mapping these abstract names to the correct
    value (string or integer) required by the box's protocol.
    """

    # Volume
    VOL_UP = "VOL_UP"
    VOL_DOWN = "VOL_DOWN"
    MUTE = "MUTE"

    # Channel
    CHAN_UP = "CHAN_UP"
    CHAN_DOWN = "CHAN_DOWN"

    # Navigation
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    OK = "OK"
    BACK = "BACK"

    # Power & Home
    POWER = "POWER"
    HOME = "HOME"

    # Media
    FFWD = "FFWD"
    REWIND = "REWIND"
    PLAY_PAUSE = "PLAY_PAUSE"
    STOP = "STOP"
    RECORD = "RECORD"

    # Numbers
    NUM_0 = "NUM_0"
    NUM_1 = "NUM_1"
    NUM_2 = "NUM_2"
    NUM_3 = "NUM_3"
    NUM_4 = "NUM_4"
    NUM_5 = "NUM_5"
    NUM_6 = "NUM_6"
    NUM_7 = "NUM_7"
    NUM_8 = "NUM_8"
    NUM_9 = "NUM_9"

    # Other
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
