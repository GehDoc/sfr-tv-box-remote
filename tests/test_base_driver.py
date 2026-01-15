"""Tests for the `BaseSFRBoxDriver` abstract base class."""

import asyncio
import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import call

import pytest
import websockets

from sfr_tv_box_core.base_driver import BaseSFRBoxDriver
from sfr_tv_box_core.constants import DEFAULT_WEBSOCKET_PORT


# Since we are testing the abstract base class, we need a concrete implementation.
class ConcreteDriver(BaseSFRBoxDriver):
    """A concrete implementation of `BaseSFRBoxDriver` for testing purposes."""

    def __init__(self, *args, **kwargs):
        """Initializes the `ConcreteDriver` and a list to store handled messages."""
        super().__init__(*args, **kwargs)
        self.handled_messages = []

    async def _handle_message(self, message: str):
        """Handles a message by appending it to the `handled_messages` list."""
        self.handled_messages.append(message)


@pytest.fixture
def driver():
    """Provides a fresh instance of the ConcreteDriver for each test."""
    return ConcreteDriver(host="localhost", port=1234)


@pytest.mark.asyncio
async def test_driver_initialization(driver):
    """Test that the driver initializes correctly."""
    assert driver._host == "localhost"
    assert driver._port == 1234
    assert driver._websocket is None


@pytest.mark.asyncio
async def test_connect_success(driver, monkeypatch):
    """Test a successful connection using monkeypatch."""
    mock_ws = AsyncMock()
    # Create an async mock for the connect function
    mock_connect = AsyncMock(return_value=mock_ws)
    # Use monkeypatch to replace websockets.connect with our mock
    monkeypatch.setattr(websockets, "connect", mock_connect)

    await driver._connect()

    mock_connect.assert_called_once_with("ws://localhost:1234/ws")
    assert driver._websocket is mock_ws


@pytest.mark.asyncio
async def test_connect_with_retries(driver, monkeypatch):
    """Test connection with retries on failure using monkeypatch."""
    # Create an async mock that will simulate failures then success
    mock_connect = AsyncMock(
        side_effect=[
            websockets.exceptions.ConnectionClosedError(None, None),
            Exception("Some other connection error"),
            AsyncMock(),  # Successful connection on the third try
        ]
    )
    monkeypatch.setattr(websockets, "connect", mock_connect)
    # Patch asyncio.sleep to capture calls and prevent actual delays
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)

    await driver._connect()

    assert mock_connect.call_count == 3
    assert sleep_mock.call_count == 2
    assert driver._websocket is not None

    # Assert that the sleep delays were exponential (1s, then 2s)
    sleep_mock.assert_has_calls([
        call(1), # First retry after 1 second
        call(2)  # Second retry after 2 seconds
    ])


@pytest.mark.asyncio
async def test_send_message_when_connected(driver):
    """Test sending a message when the WebSocket is connected."""
    driver._websocket = AsyncMock()
    await driver.send_message("test message")
    driver._websocket.send.assert_called_once_with("test message")


@pytest.mark.asyncio
async def test_listen_for_messages_and_handle(driver):
    """Test that the message listener loop correctly handles incoming messages."""
    mock_ws = AsyncMock()
    # To mock the async iterator `async for message in self._websocket:`
    mock_ws.__aiter__.return_value = ["msg1", "msg2"]
    driver._websocket = mock_ws

    listener_mock = MagicMock()
    driver.register_listener(listener_mock)

    await driver._listen_for_messages()

    # Check that the internal handler was called
    assert driver.handled_messages == ["msg1", "msg2"]
    # Check that the external listener was called
    listener_mock.assert_any_call("msg1")
    listener_mock.assert_any_call("msg2")
    assert listener_mock.call_count == 2


@pytest.mark.asyncio
async def test_listener_registration(driver):
    """Test registering and unregistering message listeners."""
    listener1 = MagicMock()
    listener2 = MagicMock()

    driver.register_listener(listener1)
    assert listener1 in driver._listeners

    driver.register_listener(listener2)
    assert listener2 in driver._listeners

    driver.unregister_listener(listener1)
    assert listener1 not in driver._listeners
    assert listener2 in driver._listeners


@pytest.mark.asyncio
async def test_set_message_callback(driver):
    """Test that `set_message_callback` clears old listeners and sets one."""
    listener1 = MagicMock()
    listener2 = MagicMock()
    new_callback = MagicMock()

    driver.register_listener(listener1)
    driver.register_listener(listener2)
    assert len(driver._listeners) == 2

    driver.set_message_callback(new_callback)
    assert len(driver._listeners) == 1
    assert new_callback in driver._listeners
    assert listener1 not in driver._listeners
    assert listener2 not in driver._listeners


@pytest.mark.asyncio
async def test_send_message_when_not_connected(driver, caplog):
    """Test that `send_message` logs a warning when not connected."""
    assert driver._websocket is None  # Ensure we start disconnected
    await driver.send_message("this should not be sent")
    assert "Cannot send message: WebSocket not connected." in caplog.text


@pytest.mark.asyncio
async def test_stop_on_stopped_driver(driver):
    """Test that `stop` can be called on an already stopped driver without error."""
    # Ensure driver is in a "stopped" state
    assert driver._websocket is None
    assert driver._reconnect_task is None

    # Calling stop should do nothing and not raise an exception
    await driver.stop()
    await driver.stop()  # Call it again to be sure


@pytest.mark.asyncio
async def test_listen_for_messages_reconnects_on_connection_closed(driver, monkeypatch, caplog):
    """Test that the driver tries to reconnect after a ConnectionClosed exception."""
    caplog.set_level(logging.INFO)
    # Mock the driver's own start/stop methods to track if they are called
    driver.start = AsyncMock()
    driver.stop = AsyncMock()

    # Mock the websocket to raise an exception when iterated over
    mock_ws = AsyncMock()
    mock_ws.__aiter__.side_effect = websockets.exceptions.ConnectionClosed(None, None)
    driver._websocket = mock_ws

    await driver._listen_for_messages()

    # Verify that the reconnection logic was triggered
    driver.stop.assert_awaited_once()
    driver.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_listen_for_messages_reconnects_on_exception(driver, monkeypatch, caplog):
    """Test that the driver tries to reconnect after a generic Exception during listening."""
    caplog.set_level(logging.ERROR)
    # Mock the driver's own start/stop methods
    driver.start = AsyncMock()
    driver.stop = AsyncMock()

    # Mock the websocket to raise a generic Exception
    mock_ws = AsyncMock()
    mock_ws.__aiter__.side_effect = Exception("Simulated listening error")
    driver._websocket = mock_ws

    await driver._listen_for_messages()

    # Verify that the reconnection logic was triggered
    driver.stop.assert_awaited_once()
    driver.start.assert_awaited_once()
    assert "Error during message listening: Simulated listening error" in caplog.text


@pytest.mark.asyncio
async def test_driver_initialization_default_port():
    """Test that the driver uses the default port if none is provided."""
    driver = ConcreteDriver(host="localhost")
    assert driver._port == DEFAULT_WEBSOCKET_PORT


@pytest.mark.asyncio
async def test_start_creates_task_and_connects(monkeypatch):
    """Test that start() connects and creates the listening task."""
    driver = ConcreteDriver(host="localhost", port=1234)
    # Mock the underlying websocket connection to avoid real network calls.
    # This allows the original _connect() method to run and set _websocket.
    mock_ws_connect = AsyncMock(return_value=MagicMock())
    monkeypatch.setattr(websockets, "connect", mock_ws_connect)

    # Mock the listening method itself to prevent the test from hanging
    listen_mock = AsyncMock()
    monkeypatch.setattr(driver, "_listen_for_messages", listen_mock)

    # A task object is not directly awaitable, so a MagicMock is more accurate.
    mock_task = MagicMock(spec=asyncio.Task)
    # The mock for create_task needs to "consume" the coroutine passed to it
    # to prevent a "coroutine never awaited" warning.
    def consume_coro_and_return_mock(coro):
        coro.close()  # Mark the coroutine as handled
        return mock_task
    mock_create_task = MagicMock(side_effect=consume_coro_and_return_mock)
    monkeypatch.setattr(asyncio, "create_task", mock_create_task)

    await driver.start()

    # Verify that the connection was attempted
    mock_ws_connect.assert_awaited_once()
    # Verify that the listening coroutine was passed to create_task
    listen_mock.assert_called_once()
    mock_create_task.assert_called_once()
    # Verify that the task was stored
    assert driver._reconnect_task is mock_task


@pytest.mark.asyncio
async def test_stop_cancels_task_and_closes_websocket():
    """Test that stop() cancels the task and closes the connection."""
    driver = ConcreteDriver(host="localhost", port=1234)
    # Simulate a running driver by assigning mocks to instance attributes
    mock_ws = AsyncMock()
    # A task object itself is not awaitable in the same way an AsyncMock is.
    # Using a MagicMock is more accurate and avoids RuntimeWarnings.
    mock_task = MagicMock(spec=asyncio.Task)

    driver._websocket = mock_ws
    driver._reconnect_task = mock_task

    await driver.stop()

    # Assert on the local mock variables, not on the driver attributes which are now None
    mock_ws.close.assert_awaited_once()
    mock_task.cancel.assert_called_once()
    assert driver._websocket is None
    assert driver._reconnect_task is None


@pytest.mark.asyncio
async def test_listen_loop_restarts_on_handler_exception(monkeypatch, caplog):
    """Test that the listen loop restarts if _handle_message raises an exception."""
    # Use a fresh driver to monkeypatch its methods for this specific test
    driver = ConcreteDriver(host="localhost", port=1234)
    caplog.set_level(logging.ERROR)

    # Monkeypatch the driver's own start/stop methods to track if they are called
    start_mock = AsyncMock()
    stop_mock = AsyncMock()
    monkeypatch.setattr(driver, "start", start_mock)
    monkeypatch.setattr(driver, "stop", stop_mock)

    # Mock the websocket to provide one message
    mock_ws = AsyncMock()
    mock_ws.__aiter__.return_value = ["a message"]
    driver._websocket = mock_ws

    # Mock the internal handler to raise an exception.
    # Defining the side effect as an async function is sometimes more stable
    # for the mock runner than a direct exception object.
    error_message = "Handler failed!"
    async def raise_exception_side_effect(*args, **kwargs):
        raise Exception(error_message)
    handle_mock = AsyncMock(side_effect=raise_exception_side_effect)
    monkeypatch.setattr(driver, "_handle_message", handle_mock)

    await driver._listen_for_messages()

    # Verify the message was passed to the handler
    handle_mock.assert_awaited_once_with("a message")
    # Verify the exception was logged
    assert error_message in caplog.text
    # Verify the reconnection logic was triggered
    stop_mock.assert_awaited_once()
    start_mock.assert_awaited_once()

