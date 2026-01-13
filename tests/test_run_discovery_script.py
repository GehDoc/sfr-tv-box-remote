"""Tests for the run_discovery.py command-line script."""
import logging
from unittest.mock import AsyncMock

import pytest

from sfr_box_core.discovery import DiscoveredBox

# Import the script's main function to test it directly
from scripts.run_discovery import main as run_discovery_main


@pytest.mark.asyncio
async def test_script_with_discovered_box(monkeypatch, caplog):
    """Test the script's output when a box is successfully discovered."""
    caplog.set_level(logging.INFO)
    # Mock the core discovery function to return a fake box
    fake_box = DiscoveredBox(
        identifier="STB8",
        ip_address="192.168.1.99",
        port=7682,
        name="STB8 (192.168.1.99)",
    )
    # Use AsyncMock for async functions
    mock_discover = AsyncMock(return_value=[fake_box])
    monkeypatch.setattr("scripts.run_discovery.async_discover_boxes", mock_discover)

    # Mock sys.argv to simulate running with default arguments
    monkeypatch.setattr("sys.argv", ["scripts/run_discovery.py"])

    # Run the script's main function
    await run_discovery_main()

    # Check the log output for key information, ignoring excess whitespace
    log_text = caplog.text
    assert "Starting network discovery" in log_text
    assert "Discovered SFR Boxes" in log_text
    assert "Identifier: STB8" in log_text
    assert "IP Address: 192.168.1.99" in log_text
    assert "Port:" in log_text
    assert "7682" in log_text


@pytest.mark.asyncio
async def test_script_with_no_box_found(monkeypatch, caplog):
    """Test the script's output when no boxes are found."""
    caplog.set_level(logging.INFO)
    # Use AsyncMock for async functions
    mock_discover = AsyncMock(return_value=[])
    monkeypatch.setattr("scripts.run_discovery.async_discover_boxes", mock_discover)

    monkeypatch.setattr("sys.argv", ["scripts/run_discovery.py"])

    await run_discovery_main()

    assert "No SFR Boxes discovered on the network." in caplog.text


@pytest.mark.asyncio
async def test_script_with_timeout_argument(monkeypatch):
    """Test that the script correctly parses and uses the --timeout argument."""
    # Use AsyncMock for async functions
    mock_discover = AsyncMock(return_value=[])
    monkeypatch.setattr("scripts.run_discovery.async_discover_boxes", mock_discover)

    # Mock sys.argv to simulate running with '-t 5'
    monkeypatch.setattr("sys.argv", ["scripts/run_discovery.py", "-t", "5"])

    await run_discovery_main()

    # Assert that async_discover_boxes was called with the correct timeout
    mock_discover.assert_called_once_with(timeout=5)
