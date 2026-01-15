"""Module for discovering SFR boxes on the local network using mDNS (Zeroconf)."""

import asyncio
import logging
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional

from zeroconf import Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser
from zeroconf.asyncio import AsyncZeroconf

from sfr_tv_box_core.constants import DEFAULT_WEBSOCKET_PORT

_LOGGER = logging.getLogger(__name__)

SERVICE_TYPE = "_ws._tcp.local."

# Service name prefixes used to identify box models
MODEL_PREFIXES = {
    "STB8": "STB8",
    "STB7": "STB7",
    "LABOX": "ws_server",
}




class DiscoveredBox(NamedTuple):
    """Represents a discovered SFR Box."""

    identifier: str
    ip_address: str
    port: int
    name: str


class _DiscoveryListener:
    """Zeroconf Service Listener to discover SFR boxes."""

    def __init__(self):
        self.discovered_boxes: Dict[str, DiscoveredBox] = {}

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """A service has been removed."""
        _LOGGER.debug("Service %s removed", name)
        if name in self.discovered_boxes:
            del self.discovered_boxes[name]

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """A service has been updated."""
        # For now, we don't need to handle updates, but the method is required.
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """A service has been added.

        This is a synchronous callback from zeroconf, so we schedule the
        async work to be done on the event loop.
        """
        asyncio.create_task(self._async_add_handler(zc, type_, name))

    async def _async_add_handler(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Asynchronously handle the service addition to get service info."""
        _LOGGER.debug("Service %s added", name)
        info = await zc.async_get_service_info(type_, name)
        if not info or not info.server:
            return

        model = self._get_model_from_name(name)
        if not model:
            _LOGGER.debug("Ignoring service '%s' with unknown model", name)
            return

        # Per user spec for POC, port is hardcoded.
        # In the future, this might come from the service info or a secondary lookup.
        port = DEFAULT_WEBSOCKET_PORT

        ip_addresses = info.parsed_addresses()
        if not ip_addresses:
            _LOGGER.warning("No IP address found for service '%s'", name)
            return

        ip_address = ip_addresses[0]

        # For POC, name is a placeholder
        friendly_name = f"{model} ({ip_address})"

        self.discovered_boxes[name] = DiscoveredBox(
            identifier=model,
            ip_address=ip_address,
            port=port,
            name=friendly_name,
        )

    def _get_model_from_name(self, name: str) -> Optional[str]:
        """Determine box model from the mDNS service instance name."""
        for model, prefix in MODEL_PREFIXES.items():
            if name.startswith(prefix):
                return model
        return None


async def async_discover_boxes(timeout: int = 5) -> List[DiscoveredBox]:
    """Scan the network for SFR boxes using mDNS.

    Args:
        timeout: The number of seconds to scan for.

    Returns:
        A list of DiscoveredBox objects.
    """
    aiozc = AsyncZeroconf()
    listener = _DiscoveryListener()
    browser = AsyncServiceBrowser(aiozc.zeroconf, SERVICE_TYPE, listener=listener)

    _LOGGER.info("Starting mDNS scan for %d seconds...", timeout)
    await asyncio.sleep(timeout)

    await browser.async_cancel()
    await aiozc.async_close()

    _LOGGER.info("mDNS scan finished. Found %d boxes.", len(listener.discovered_boxes))
    return list(listener.discovered_boxes.values())
