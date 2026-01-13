"""Abstract Base Class for SFR Box drivers."""

import asyncio
import logging
from abc import ABC
from abc import abstractmethod
from typing import Callable
from typing import Optional

import websockets

_LOGGER = logging.getLogger(__name__)


class BaseSFRBoxDriver(ABC):
    """Abstract Base Class for SFR Box drivers.

    This class provides the common WebSocket handling logic, including connection,
    reconnection with exponential backoff, and message sending/receiving.
    Specific box implementations (V8, V7, LaBox) will inherit from this class
    and implement the abstract methods for their specific protocols.
    """

    def __init__(self, host: str, port: int = 8080):
        """Initializes the BaseSFRBoxDriver.

        Args:
            host (str): The hostname or IP address of the SFR Box.
            port (int): The port for the WebSocket connection. Defaults to 8080.
        """
        self._host = host
        self._port = port
        self._websocket: Optional[websockets.client.WebSocketClientProtocol] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._message_callback: Optional[Callable[[str], None]] = None
        self._listeners = []  # Placeholder for message listeners

    @abstractmethod
    async def _handle_message(self, message: str) -> None:
        """Abstract method to handle incoming messages from the WebSocket.

        Implement this in subclasses for specific box logic.

        Args:
            message (str): The received message string.
        """
        pass

    async def _connect(self) -> None:
        """Establishes a WebSocket connection to the SFR Box with exponential backoff."""
        uri = f"ws://{self._host}:{self._port}/ws"
        retry_delay = 1
        while True:
            try:
                _LOGGER.info("Attempting to connect to %s", uri)
                self._websocket = await websockets.connect(uri)
                _LOGGER.info("Successfully connected to %s", uri)
                break
            except Exception as e:
                _LOGGER.error(
                    "Connection failed: %s. Retrying in %d s...",
                    e,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s

    async def start(self) -> None:
        """Starts the WebSocket connection and message listening."""
        await self._connect()
        if self._websocket:
            self._reconnect_task = asyncio.create_task(self._listen_for_messages())

    async def stop(self) -> None:
        """Closes the WebSocket connection and stops reconnection attempts."""
        if self._websocket:
            _LOGGER.info("Closing WebSocket connection.")
            await self._websocket.close()
            self._websocket = None
        if self._reconnect_task:
            _LOGGER.info("Cancelling reconnection task.")
            self._reconnect_task.cancel()
            self._reconnect_task = None

    async def send_message(self, message: str) -> None:
        """Sends a message over the WebSocket connection.

        Args:
            message (str): The message string to send.
        """
        if self._websocket:
            _LOGGER.debug("Sending message: %s", message)
            await self._websocket.send(message)
        else:
            _LOGGER.warning("Cannot send message: WebSocket not connected.")

    def register_listener(self, listener: Callable[[str], None]) -> None:
        """Registers a listener for incoming messages."""
        self._listeners.append(listener)

    def unregister_listener(self, listener: Callable[[str], None]) -> None:
        """Unregisters a listener for incoming messages."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def _listen_for_messages(self) -> None:
        """Listens for incoming messages from the WebSocket."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                _LOGGER.debug("Received message: %s", message)
                # Assuming message is a string, which is common.
                # If it can be bytes, add handling for that.
                if isinstance(message, str):
                    for listener in self._listeners:
                        listener(message)
                    await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            _LOGGER.info("WebSocket connection closed. Attempting to reconnect...")
            await self.stop()
            await self.start()  # Trigger reconnection logic
        except Exception as e:
            _LOGGER.error("Error during message listening: %s", e)
            await self.stop()
            # Depending on the desired behavior, you might want to trigger
            # reconnection here too.
            await self.start()
