#!/usr/bin/env python3
"""
A command-line utility to discover SFR boxes on the local network.
"""
import asyncio
import logging
import argparse
import sys
import os

# Ensure the script can find the sfr_box_core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sfr_box_core.discovery import async_discover_boxes

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)


async def main():
    """Main function to run the discovery."""
    parser = argparse.ArgumentParser(description="Discover SFR STBs on the local network.")
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="The duration (in seconds) to scan for devices. Default is 10 seconds."
    )
    args = parser.parse_args()

    _LOGGER.info("Starting network discovery for SFR Boxes (scan duration: %d seconds)...", args.timeout)
    
    try:
        discovered_boxes = await async_discover_boxes(timeout=args.timeout)

        if discovered_boxes:
            _LOGGER.info("\n--- Discovered SFR Boxes ---")
            for i, box in enumerate(discovered_boxes, 1):
                _LOGGER.info("  Box #%d:", i)
                _LOGGER.info("    Identifier: %s", box.identifier)
                _LOGGER.info("    Name:       %s", box.name)
                _LOGGER.info("    IP Address: %s", box.ip_address)
                _LOGGER.info("    Port:       %s", box.port)
            _LOGGER.info("--------------------------")
        else:
            _LOGGER.info("No SFR Boxes discovered on the network.")
    
    except Exception as e:
        _LOGGER.error("An error occurred during discovery: %s", e, exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Discovery cancelled by user.")
