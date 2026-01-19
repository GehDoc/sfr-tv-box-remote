"""Tests for the sfr_tv_box_remote.py command-line script using a dedicated TestDriver."""

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest

from sfr_tv_box_core.base_driver import BaseSFRBoxDriver
from sfr_tv_box_core.constants import DEFAULT_WEBSOCKET_PORT
from sfr_tv_box_core.constants import CommandType
from sfr_tv_box_core.constants import KeyCode

from scripts.sfr_tv_box_remote import main as sfr_tv_box_remote_main


class _TestDriver(BaseSFRBoxDriver):
    """A dedicated test driver for the CLI that simulates network interaction."""

    def __init__(self, host: str, port: int = DEFAULT_WEBSOCKET_PORT, device_id: str = "test-stb8"):
        super().__init__(host, port)
        self.sent_commands = []
        self.started = False
        self.stopped = False
        self._callback = None
        self._mock_responses = asyncio.Queue()

    async def _handle_message(self, message: str) -> None:
        """Implementation for the abstract method."""
        pass

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    def set_message_callback(self, callback) -> None:
        self._callback = callback

    async def send_command(self, command_type: CommandType, **kwargs: Any) -> None:
        """Simulate sending a command and immediately triggering a response."""
        self.sent_commands.append((command_type, kwargs))
        if self._callback:
            # Schedule the callback to be run by the event loop,
            # don't call it directly.
            asyncio.get_running_loop().call_soon(self._callback, '{"result": "OK", "data": "dummy_response"}')
        # Yield control to allow the scheduled callback to run.
        await asyncio.sleep(0)


@pytest.fixture(scope="function")
def mock_driver(monkeypatch):
    """Patches DRIVER_MAP to return a mock driver instance.

    Each test gets a fresh mock instance to prevent state contamination.
    """
    mock_instance = AsyncMock(spec=_TestDriver)
    mock_instance._callback = None

    def set_callback_side_effect(cb):
        mock_instance._callback = cb

    mock_instance.set_message_callback.side_effect = set_callback_side_effect

    async def send_command_side_effect(*args, **kwargs):
        if mock_instance._callback:
            asyncio.get_running_loop().call_soon(mock_instance._callback, '{"result": "OK", "data": "dummy_response"}')
        await asyncio.sleep(0)

    mock_instance.send_command.side_effect = send_command_side_effect
    mock_instance.start = AsyncMock()
    mock_instance.stop = AsyncMock()

    def mock_driver_factory(host, port, device_id="default-test-stb8"):
        mock_instance.host = host
        mock_instance.port = port
        mock_instance.device_id = device_id
        return mock_instance

    monkeypatch.setattr("scripts.sfr_tv_box_remote.DRIVER_MAP", {"STB8": mock_driver_factory})
    return mock_instance


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_send_key(mock_driver, monkeypatch, caplog):
    """Test the CLI for a 'send_key' command."""
    caplog.set_level(logging.INFO)

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "SEND_KEY", "POWER"]
    monkeypatch.setattr("sys.argv", test_argv)

    await sfr_tv_box_remote_main()

    mock_driver.start.assert_awaited_once()
    mock_driver.send_command.assert_awaited_once_with(CommandType.SEND_KEY, key=KeyCode.POWER)
    mock_driver.stop.assert_awaited_once()
    assert "Received response" in caplog.text
    assert "dummy_response" in caplog.text


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_get_status(mock_driver, monkeypatch, caplog):
    """Test the CLI for a 'get_status' command."""
    caplog.set_level(logging.INFO)

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "GET_STATUS"]
    monkeypatch.setattr("sys.argv", test_argv)

    await sfr_tv_box_remote_main()

    mock_driver.start.assert_awaited_once()
    mock_driver.send_command.assert_awaited_once_with(CommandType.GET_STATUS)
    mock_driver.stop.assert_awaited_once()
    assert "Received response" in caplog.text


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_unsupported_model(monkeypatch, capsys):
    """Test the CLI argument parsing with an unsupported model."""
    monkeypatch.setattr(
        "scripts.sfr_tv_box_remote.DRIVER_MAP",
        {"STB8_UNSUPPORTED": lambda host, port, device_id="default-test-stb8": None},
    )

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "--model", "STB7", "GET_STATUS"]
    monkeypatch.setattr("sys.argv", test_argv)

    with pytest.raises(SystemExit):
        await sfr_tv_box_remote_main()

    outerr = capsys.readouterr()
    assert "invalid choice: 'STB7'" in outerr.err


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_listen_mode(mock_driver, monkeypatch, caplog):
    """Test the CLI for 'listen' command."""
    caplog.set_level(logging.INFO)

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "listen"]
    monkeypatch.setattr("sys.argv", test_argv)

    original_sleep = asyncio.sleep

    async def mock_sleep(delay):
        if delay == 3600 and mock_driver._callback:
            mock_driver._callback("SIMULATED_INCOMING_MESSAGE")
            raise asyncio.CancelledError
        return await original_sleep(delay)

    monkeypatch.setattr(asyncio, "sleep", AsyncMock(side_effect=mock_sleep))

    with pytest.raises(asyncio.CancelledError):
        await sfr_tv_box_remote_main()

    mock_driver.start.assert_awaited_once()
    mock_driver.set_message_callback.assert_called_once()
    mock_driver.stop.assert_awaited_once()

    assert "Successfully connected to 1.2.3.4" in caplog.text
    assert "Listening for messages. Press Ctrl+C to stop." in caplog.text
    assert "Received: SIMULATED_INCOMING_MESSAGE" in caplog.text
