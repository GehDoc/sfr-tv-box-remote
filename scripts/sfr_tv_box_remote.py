"""Command-Line Interface for interacting with SFR boxes.

This script provides a way to send single commands to a discovered box
to test and control it from the command line.
"""

# Standard library imports
import argparse
import asyncio
import logging
from typing import Dict
from typing import Type

# Third-party imports (none in this file)
# Local application/library specific imports
from sfr_tv_box_core.base_driver import BaseSFRBoxDriver
from sfr_tv_box_core.constants import DEFAULT_WEBSOCKET_PORT
from sfr_tv_box_core.constants import CommandType
from sfr_tv_box_core.constants import KeyCode
from sfr_tv_box_core.stb8_driver import STB8Driver

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
_LOGGER = logging.getLogger(__name__)

# Map model strings to driver classes
# For now, only STB8 is implemented.
DRIVER_MAP: Dict[str, Type[BaseSFRBoxDriver]] = {
    "STB8": STB8Driver,
    # "STB7": V7Driver, # To be added in Phase 2.3
    # "LaBox": LaBoxDriver, # To be added in Phase 5
}


async def main() -> None:
    """Main function to parse arguments and run a single command."""
    parser = argparse.ArgumentParser(prog="sfr_tv_box_remote.py", description="A CLI to control SFR TV boxes.")
    parser.add_argument("--ip", required=True, help="IP address of the set-top box.")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_WEBSOCKET_PORT,
        help=f"Port for the WebSocket connection (default: {DEFAULT_WEBSOCKET_PORT}).",
    )
    parser.add_argument("--model", choices=DRIVER_MAP.keys(), default="STB8", help="The model of the box (default: STB8).")

    subparsers = parser.add_subparsers(dest="command", required=True, help="The command to execute.")

    # Sub-parser for the 'send_key' command
    parser_send_key = subparsers.add_parser(CommandType.SEND_KEY.value, help="Send a remote key press.")
    parser_send_key.add_argument("key", choices=[key.name for key in KeyCode], help="The key to press.")

    # Sub-parser for the 'get_status' command
    subparsers.add_parser(CommandType.GET_STATUS.value, help="Get the current status of the box.")

    # Sub-parser for the 'get_versions' command
    subparsers.add_parser(CommandType.GET_VERSIONS.value, help="Get version information from the box.")

    # Sub-parser for the 'listen' command
    subparsers.add_parser("listen", help="Listen for incoming WebSocket messages from the box.")

    args = parser.parse_args()

    driver_class = DRIVER_MAP.get(args.model)
    if not driver_class:
        _LOGGER.error("Model '%s' is not supported.", args.model)
        return

    driver = driver_class(host=args.ip, port=args.port)

    is_listen_mode = args.command == "listen"

    # --- Setup message handling ---
    if is_listen_mode:

        def print_message_callback(message: str) -> None:
            _LOGGER.info("Received: %s", message)

        driver.set_message_callback(print_message_callback)
    else:
        # For one-shot commands, use a Future to capture the first response
        first_message_received = asyncio.Future()

        def message_callback(message: str) -> None:
            if not first_message_received.done():
                first_message_received.set_result(message)

        driver.set_message_callback(message_callback)

    try:
        await driver.start()
        _LOGGER.info("Successfully connected to %s.", args.ip)

        if is_listen_mode:
            _LOGGER.info("Listening for messages. Press Ctrl+C to stop.")
            # Keep the connection alive indefinitely
            while True:
                await asyncio.sleep(3600)  # Sleep for a long time, or until interrupted
        else:
            command_params = {}
            if args.command == CommandType.SEND_KEY.value:
                command_params["key"] = KeyCode[args.key]

            _LOGGER.info("Sending command: %s with params: %s", args.command, command_params or "None")
            await driver.send_command(CommandType(args.command), **command_params)

            _LOGGER.info("Waiting for response...")
            response = await asyncio.wait_for(first_message_received, timeout=5.0)
            _LOGGER.info("Received response:\n%s", response)

    except asyncio.TimeoutError:
        _LOGGER.error("Did not receive a response within the timeout period.")
    except Exception as e:
        _LOGGER.error("An error occurred: %s", e, exc_info=True)
    finally:
        if driver:
            await driver.stop()
            _LOGGER.info("Connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("\nCLI cancelled by user.")
