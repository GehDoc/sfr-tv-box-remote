import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sfr_box_core.base_driver import BaseSFRBoxDriver
import websockets

# Since we are testing the abstract base class, we need a concrete implementation.
class ConcreteDriver(BaseSFRBoxDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handled_messages = []

    async def _handle_message(self, message: str):
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
    # Also patch asyncio.sleep to make the test run instantly
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    await driver._connect()
    
    assert mock_connect.call_count == 3
    # The assertion on sleep needs the mock object, which is now on asyncio itself
    assert asyncio.sleep.call_count == 2
    assert driver._websocket is not None

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

