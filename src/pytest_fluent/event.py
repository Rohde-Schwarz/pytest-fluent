"""Custom Event class."""

import logging
import time
import typing

from fluent.sender import FluentSender

LOGGER = logging.getLogger(__package__)


class Event:
    """Customized Event class for sending different tags.

    Args:
            host (str): Host name of the Fluent instance. Defaults to "localhost".
            port (int): Port of the Fluent instance. Defaults to 24224.
    """

    def __init__(
        self,
        tags: typing.List[str],
        host: str = "localhost",
        port: int = 24224,
        **kwargs,
    ) -> None:
        """Initialize custom event class."""
        self.senders = {
            tag: FluentSender(tag=tag, host=host, port=port, **kwargs)
            for tag in tags
            if tag
        }

    def __call__(self, tag: str, label: str, data: dict, **kwargs):
        """Send a new event.

        Args:
            tag (str): Fluent tag.
            label (str): Fluent label.
            data (dict): Data to transmit as dictionary.
        """
        assert isinstance(data, dict), "data must be a dict"
        # Return if tag is empty string
        if not tag:
            return
        sender_ = self.senders.get(tag)
        if sender_ is None or not isinstance(sender_, FluentSender):
            LOGGER.warning("Could not retrieve fluent instance for tag %s", tag)
            return
        timestamp = kwargs.get("time", int(time.time()))
        if not sender_.emit_with_time(label, timestamp, data):
            LOGGER.warning("Could not send data via fluent for tag %s: %s", tag, data)
