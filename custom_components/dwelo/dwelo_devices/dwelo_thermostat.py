"""A module for Dwelo thermostat related objects."""

import logging

from ..device_converter import convert_to_thermostat
from ..dwelo_client import DweloClient
from ..models import DweloDeviceMetadata, DweloThermostatData, DweloThermostatMode

_LOGGER = logging.getLogger(__name__)


class DweloThermostatDevice:
    """A class representing a Dwelo thermostat."""

    def __init__(
        self,
        client: DweloClient,
        device_metadata: DweloDeviceMetadata,
        device_data: DweloThermostatData,
    ) -> None:
        """Initialize the thermostat."""

        if device_metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {device_metadata}")  # noqa: G004
            return

        self._client = client
        self._device_metadata = device_metadata
        self._device_data = device_data

    @classmethod
    async def from_metadata(
        cls, client: DweloClient, device_metadata: DweloDeviceMetadata
    ):
        """Create a thermostat from a device."""
        device_data = await cls._async_get_data(client, device_metadata)
        return cls(client, device_metadata, device_data)

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
    ) -> DweloThermostatData:
        """Get the thermostat data for a given device."""
        if metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {metadata}")  # noqa: G004
            return

        gateway_data = await client.get(
            f"{client.GATEWAY_ENDPOINT}{metadata.gateway_id}"
        )
        if not gateway_data:
            return None

        device_data = {}
        for sensor in gateway_data["results"]:
            if sensor["deviceId"] == metadata.uid:
                device_data[sensor["sensorType"]] = sensor

        return convert_to_thermostat(device_data)

    async def async_update(self) -> DweloThermostatData:
        """Get the thermostat data for a given device."""
        self._device_data = await self._async_get_data(
            self._client, self._device_metadata
        )
        return self.data

    async def set_thermostat_temperature(
        self,
        device_metadata: DweloDeviceMetadata,
        temperature: float,
        mode: DweloThermostatMode,
    ) -> bool:
        """Set the temperature of a thermostat.

        Note that this sets the temperature for a specific mode, but does not
        set the active mode of the thermostat itself. If you would like to set
        the thermostat mode, use set_thermostat_mode. This means that this API
        can set the target temperature for a mode that is not active (so you
        can set the temperature for the heat mode while the thermostat is set
        to cool).
        """
        if device_metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {device_metadata}")  # noqa: G004
            return False

        await self._client.post(
            f"{self._client.DEVICE_ENDPOINT}{device_metadata.uid}/command/",
            {"command": mode, "commandValue": temperature},
        )

    async def set_thermostat_mode(
        self, device_metadata: DweloDeviceMetadata, mode: DweloThermostatMode
    ) -> bool:
        """Set the mode of a thermostat."""
        if device_metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {device_metadata}")  # noqa: G004
            return False

        await self._client.post(
            f"{self._client.DEVICE_ENDPOINT}{device_metadata.uid}/command/",
            {"command": mode},
        )
