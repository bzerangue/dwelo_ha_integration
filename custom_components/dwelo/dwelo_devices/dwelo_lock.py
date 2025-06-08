"""A module for Dwelo lock related objects."""

import logging

from ..device_converter import convert_to_lock
from ..dwelo_client import DweloClient
from ..models import DweloDeviceMetadata, DweloLockData, DweloLockState

_LOGGER = logging.getLogger(__name__)


class DweloLockDevice:
    """A class representing a Dwelo lock."""

    def __init__(
        self,
        client: DweloClient,
        device_metadata: DweloDeviceMetadata,
        device_data: DweloLockData,
    ) -> None:
        """Initialize the lock."""
        if device_metadata.device_type != "lock":
            _LOGGER.error(f"Device is not a lock: {device_metadata}")
            return

        self._client = client
        self._device_metadata = device_metadata
        self._device_data = device_data

    @classmethod
    async def from_metadata(
        cls, client: DweloClient, device_metadata: DweloDeviceMetadata
    ):
        """Create a lock from a device."""
        device_data = await cls._async_get_data(client, device_metadata)
        if device_data:
            return cls(client, device_metadata, device_data)
        return None

    @property
    def data(self):
        """Get the device data."""
        return self._device_data

    @property
    def metadata(self):
        """Get the device metadata."""
        return self._device_metadata

    @staticmethod
    async def _async_get_data(
        client: DweloClient, metadata: DweloDeviceMetadata
    ) -> DweloLockData:
        """Get the lock data for a given device."""
        if metadata.device_type != "lock":
            _LOGGER.error(f"Device is not a lock: {metadata}")
            return None

        gateway_data = await client.get(
            f"{client.GATEWAY_ENDPOINT}{metadata.gateway_id}"
        )
        if not gateway_data:
            _LOGGER.error(f"No gateway data for gateway ID {metadata.gateway_id}")
            return None

        device_data = {}
        for sensor in gateway_data["results"]:
            if sensor["deviceId"] == metadata.uid:
                device_data[sensor["sensorType"]] = sensor

        return convert_to_lock(device_data, metadata)

    async def async_update(self) -> DweloLockData:
        """Get the lock data for a given device."""
        self._device_data = await self._async_get_data(
            self._client, self._device_metadata
        )
        return self._device_data

    async def set_lock_state(
        self, device_metadata: DweloDeviceMetadata, state: DweloLockState
    ) -> bool:
        """Set the state of a lock (lock or unlock)."""
        if device_metadata.device_type != "lock":
            _LOGGER.error(f"Device is not a lock: {device_metadata}")
            return False

        if state not in [DweloLockState.LOCKED, DweloLockState.UNLOCKED]:
            _LOGGER.error(f"Invalid lock state: {state}")
            return False

        # Map DweloLockState to API command
        command_map = {
            DweloLockState.LOCKED: "lock",
            DweloLockState.UNLOCKED: "unlock",
        }
        command = command_map[state]

        response = await self._client.post(
            f"{self._client.DEVICE_ENDPOINT}{device_metadata.uid}/command/",
            {"command": command},
        )
        _LOGGER.debug(f"Lock command response: {response}")
        if response is None:
            _LOGGER.error(f"Failed to send {command} command for {device_metadata.uid}")
            return False
        return True