"""Tests for the sfr_tv_box_remote.py command-line script using a dedicated TestDriver."""

import asyncio
import logging
from typing import Any  # Import Any
from unittest.mock import AsyncMock

import pytest

from sfr_tv_box_core.base_driver import BaseSFRBoxDriver  # Import BaseSFRBoxDriver
from sfr_tv_box_core.constants import DEFAULT_WEBSOCKET_PORT
from sfr_tv_box_core.constants import CommandType
from sfr_tv_box_core.constants import KeyCode

from scripts.sfr_tv_box_remote import main as sfr_tv_box_remote_main


class _TestDriver(BaseSFRBoxDriver):  # Renamed to _TestDriver
    """A dedicated test driver for the CLI that simulates network interaction."""

    def __init__(
        self, host: str, port: int = DEFAULT_WEBSOCKET_PORT, device_id: str = "test-stb8"
    ):
        super().__init__(host, port)
        self.sent_commands = []
        self.started = False
        self.stopped = False
        self._callback = None
        self._mock_responses = asyncio.Queue()  # To queue up specific responses if needed

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


@pytest.fixture
def mock_driver_map_with_test_driver(monkeypatch):
    """Patches DRIVER_MAP to return our mock TestDriver class.

    and returns the mock instance that would be created.
    """
    mock_instance = AsyncMock(spec=_TestDriver)  # Use _TestDriver spec

    # Configure the mock_instance to behave like a _TestDriver
    captured_callback = None

    def set_callback_side_effect(cb):
        nonlocal captured_callback
        captured_callback = cb

    mock_instance.set_message_callback.side_effect = set_callback_side_effect

    async def send_command_side_effect(*args, **kwargs):
        if captured_callback:
            asyncio.get_running_loop().call_soon(captured_callback, '{"result": "OK", "data": "dummy_response"}')
        await asyncio.sleep(0)

    mock_instance.send_command.side_effect = send_command_side_effect
    mock_instance.start.side_effect = AsyncMock()
    mock_instance.stop.side_effect = AsyncMock()

    # The factory that cli.py will call when it wants to create a driver
    def mock_driver_factory(host, port, device_id="default-test-stb8"):
        # Configure the mock_instance properties as they would be set by __init__
        mock_instance.host = host
        mock_instance.port = port
        mock_instance.device_id = device_id
        return mock_instance

    monkeypatch.setattr("scripts.sfr_tv_box_remote.DRIVER_MAP", {"STB8": mock_driver_factory})
    return mock_instance  # Fixture returns the configured mock instance


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_send_key(mock_driver_map_with_test_driver, monkeypatch, caplog):
    """Test the CLI for a 'send_key' command using TestDriver."""
    caplog.set_level(logging.INFO)
    test_driver_instance = mock_driver_map_with_test_driver

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "SEND_KEY", "POWER"]
    monkeypatch.setattr("sys.argv", test_argv)

    await sfr_tv_box_remote_main()

    test_driver_instance.start.assert_awaited_once()  # Verify start was called
    test_driver_instance.send_command.assert_awaited_once_with(CommandType.SEND_KEY, key=KeyCode.POWER)
    test_driver_instance.stop.assert_awaited_once()  # Verify stop was called
    assert "Received response" in caplog.text
    assert "dummy_response" in caplog.text


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_get_status(mock_driver_map_with_test_driver, monkeypatch, caplog):
    """Test the CLI for a 'get_status' command using TestDriver."""
    caplog.set_level(logging.INFO)
    test_driver_instance = mock_driver_map_with_test_driver

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "GET_STATUS"]
    monkeypatch.setattr("sys.argv", test_argv)

    await sfr_tv_box_remote_main()

    test_driver_instance.start.assert_awaited_once()
    test_driver_instance.send_command.assert_awaited_once_with(CommandType.GET_STATUS)
    test_driver_instance.stop.assert_awaited_once()
    assert "Received response" in caplog.text


@pytest.mark.asyncio
async def test_sfr_tv_box_remote_unsupported_model(monkeypatch, capsys):
    """Test the CLI argument parsing with an unsupported model."""
    # We patch the DRIVER_MAP itself to return an empty dict of supported models
    monkeypatch.setattr(
        "scripts.sfr_tv_box_remote.DRIVER_MAP",
        {"STB8_UNSUPPORTED": lambda host, port, device_id="default-test-stb8": None},
    )

    test_argv = ["sfr_tv_box_remote.py", "--ip", "1.2.3.4", "--model", "STB7", "GET_STATUS"]
    monkeypatch.setattr("sys.argv", test_argv)

    with pytest.raises(SystemExit):
        await sfr_tv_box_remote_main()

    # Check stderr which is where argparse prints errors
    outerr = capsys.readouterr()
    assert "invalid choice: 'STB7'" in outerr.err
