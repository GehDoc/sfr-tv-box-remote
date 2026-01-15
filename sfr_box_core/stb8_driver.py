"""Driver implementation for the SFR STB8 set-top box."""

import json
import logging
import time
from typing import Any
from typing import Dict
from typing import Optional

from .base_driver import BaseSFRBoxDriver
from .constants import CommandType
from .constants import KeyCode

_LOGGER = logging.getLogger(__name__)


class _STB8CommandBuilder:
    """Builds the JSON payloads for STB8 commands."""

    def __init__(self, device_id: str):
        self._device_id = device_id
        self._keycode_map = self._create_keycode_map()

    def _create_base_payload(self, action: str) -> Dict[str, Any]:
        """Creates the base dictionary for all commands."""
        return {
            "action": action,
            "deviceId": self._device_id,
            "requestId": int(time.time() * 1000),
        }

    def build_send_key(self, key: KeyCode) -> Optional[str]:
        """Build the payload for the SEND_KEY command."""
        key_str = self._keycode_map.get(key)
        if key_str is None:
            return None

        payload = self._create_base_payload("buttonEvent")
        payload["params"] = {"key": key_str}
        return json.dumps(payload)

    def build_get_status(self) -> str:
        """Build the payload for the GET_STATUS command."""
        payload = self._create_base_payload("getStatus")
        return json.dumps(payload)

    def build_get_versions(self, device_name: str) -> str:
        """Build the payload for the GET_VERSIONS command."""
        payload = self._create_base_payload("getVersions")
        payload["params"] = {"deviceName": device_name}
        return json.dumps(payload)

    @staticmethod
    def _create_keycode_map() -> Dict[KeyCode, str]:
        """Creates the mapping from abstract KeyCode to STB8 string value."""
        return {
            KeyCode.VOL_UP: "volUp",
            KeyCode.VOL_DOWN: "volDown",
            KeyCode.CHAN_UP: "channelUp",
            KeyCode.CHAN_DOWN: "channelDown",
            KeyCode.HOME: "home",
            KeyCode.BACK: "back",
            KeyCode.POWER: "power",
            KeyCode.FFWD: "fastForward",
            KeyCode.REWIND: "fastBackward",
            KeyCode.PLAY_PAUSE: "playPause",
            KeyCode.STOP: "stop",
            KeyCode.RECORD: "record",
            KeyCode.MUTE: "mute",
            KeyCode.UP: "up",
            KeyCode.LEFT: "left",
            KeyCode.RIGHT: "right",
            KeyCode.DOWN: "down",
            KeyCode.OK: "ok",
            KeyCode.NUM_0: "0",
            KeyCode.NUM_1: "1",
            KeyCode.NUM_2: "2",
            KeyCode.NUM_3: "3",
            KeyCode.NUM_4: "4",
            KeyCode.NUM_5: "5",
            KeyCode.NUM_6: "6",
            KeyCode.NUM_7: "7",
            KeyCode.NUM_8: "8",
            KeyCode.NUM_9: "9",
        }


class STB8Driver(BaseSFRBoxDriver):
    """Driver for the STB8.

    Implements the command building and response parsing specific to this model.
    """

    def __init__(self, host: str, port: int = 8080, device_id: str = "default-stb8"):
        """Initialize the STB8Driver.

        Args:
            host: The hostname or IP address of the SFR Box.
            port: The port for the WebSocket connection.
            device_id: The unique ID of the STB8 device.
        """
        super().__init__(host, port)
        self._builder = _STB8CommandBuilder(device_id)
        self._device_id = device_id  # Store device_id for use in get_versions

    async def _handle_message(self, message: str) -> None:
        """Handle incoming messages from the WebSocket."""
        # For now, we just log the message.
        # In the future, this will parse the message and update state.
        _LOGGER.info("STB8 received message: %s", message)

    async def send_command(self, command_type: CommandType, **kwargs: Any) -> None:
        """Send a command to the box.

        Args:
            command_type: The abstract CommandType to send.
            **kwargs: Parameters for the command.
        """
        payload: Optional[str] = None
        if command_type == CommandType.SEND_KEY:
            key = kwargs.get("key")
            if not isinstance(key, KeyCode):
                _LOGGER.error("send_command for SEND_KEY requires a 'key' of type KeyCode.")
                return
            payload = self._builder.build_send_key(key)
        elif command_type == CommandType.GET_STATUS:
            payload = self._builder.build_get_status()
        elif command_type == CommandType.GET_VERSIONS:
            # For GET_VERSIONS, the deviceName parameter for the payload is the same as device_id
            payload = self._builder.build_get_versions(self._device_id)
        else:
            _LOGGER.warning("Unsupported command type: %s", command_type)
            return

        if payload:
            await self.send_message(payload)
