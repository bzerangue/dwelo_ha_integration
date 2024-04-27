"""Exceptions for Dwelo devices."""


class InvalidDeviceException(Exception):
    """Exception raised when a device is not of the expected type."""

    def __init__(self, message) -> None:
        """Create an InvalidDeviceException."""
        self.message = message
        super().__init__(self.message)
