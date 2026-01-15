"""Tests for the discovery module."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from zeroconf import ServiceInfo

from sfr_tv_box_core.discovery import _DiscoveryListener
from sfr_tv_box_core.discovery import async_discover_boxes


@pytest.fixture
def mock_async_zeroconf():
    """Fixture to mock AsyncZeroconf and its interactions."""
    mock_service_info = MagicMock(spec=ServiceInfo)
    mock_service_info.server = "STB8-device.local."
    mock_service_info.parsed_addresses.return_value = ["192.168.1.10"]

    mock_zc_instance = MagicMock()
    mock_zc_instance.async_get_service_info = AsyncMock(return_value=mock_service_info)

    mock_aiozc = MagicMock()
    mock_aiozc.zeroconf = mock_zc_instance
    mock_aiozc.async_close = AsyncMock()

    with patch("sfr_tv_box_core.discovery.AsyncZeroconf", return_value=mock_aiozc) as _:
        yield mock_aiozc, mock_service_info


@pytest.mark.asyncio
async def test_discover_single_box_async(mock_async_zeroconf, monkeypatch):
    """Test discovering a single STB8 box with the async implementation."""
    mock_aiozc, mock_service_info = mock_async_zeroconf

    mock_browser = MagicMock(async_cancel=AsyncMock())
    monkeypatch.setattr(
        "sfr_tv_box_core.discovery.AsyncServiceBrowser",
        lambda *args, **kwargs: mock_browser,
    )

    listener = _DiscoveryListener()

    # In tests, we call the internal async handler directly
    await listener._async_add_handler(mock_aiozc.zeroconf, "_ws._tcp.local.", "STB8-aabbcc.local.")

    monkeypatch.setattr("sfr_tv_box_core.discovery._DiscoveryListener", lambda: listener)

    result = await async_discover_boxes(timeout=0.1)

    assert len(result) == 1
    box = result[0]
    assert box.identifier == "STB8"
    assert box.ip_address == "192.168.1.10"
    assert box.port == 7682


@pytest.mark.asyncio
async def test_discover_multiple_boxes_async(mock_async_zeroconf, monkeypatch):
    """Test discovering multiple different boxes with the async implementation."""
    mock_aiozc, mock_service_info = mock_async_zeroconf

    monkeypatch.setattr(
        "sfr_tv_box_core.discovery.AsyncServiceBrowser",
        lambda *args, **kwargs: MagicMock(async_cancel=AsyncMock()),
    )

    listener = _DiscoveryListener()

    # Simulate finding STB7
    mock_service_info.server = "STB7-device.local."
    mock_service_info.parsed_addresses.return_value = ["192.168.1.20"]
    await listener._async_add_handler(mock_aiozc.zeroconf, "_ws._tcp.local.", "STB7-xxyyzz.local.")

    # Simulate finding LaBox
    mock_service_info.server = "ws_server-device.local."
    mock_service_info.parsed_addresses.return_value = ["192.168.1.30"]
    await listener._async_add_handler(mock_aiozc.zeroconf, "_ws._tcp.local.", "ws_server-123456.local.")

    # Simulate finding an unrelated service that should be ignored
    await listener._async_add_handler(mock_aiozc.zeroconf, "_ws._tcp.local.", "OtherDevice.local.")

    monkeypatch.setattr("sfr_tv_box_core.discovery._DiscoveryListener", lambda: listener)

    result = await async_discover_boxes(timeout=0.1)

    assert len(result) == 2

    identifiers = {box.identifier for box in result}
    assert "STB7" in identifiers
    assert "LABOX" in identifiers
