"""A module for Dwelo lock devices."""

from datetime import timedelta
import logging

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .dwelo_devices.dwelo_lock import DweloLockDevice
from .models import DweloLockState

_LOGGER = logging.getLogger(__name__)

DWELO_LOCK_STATE_TO_HA_STATE = {
    DweloLockState.LOCKED: "locked",
    DweloLockState.UNLOCKED: "unlocked",
}
HA_STATE_TO_DWELO_LOCK_STATE = {v: k for k, v in DWELO_LOCK_STATE_TO_HA_STATE.items()}

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Dwelo lock platform."""

    data: DweloData = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for metadata in data.device_metadata.values():
        if metadata.device_type == "lock":
            device = await DweloLockDevice.from_metadata(data.client, metadata)
            if device and device.data:  # Ensure device is valid
                entities.append(DweloLockEntity(device))
            else:
                _LOGGER.error(f"Failed to initialize lock device: {metadata}")

    async_add_entities(entities)


class DweloLockEntity(LockEntity):
    """Representation of a Dwelo lock entity within Home Assistant."""

    def __init__(
        self,
        device: DweloLockDevice,
    ) -> None:
        """Initialize the lock."""
        super().__init__()
        self._device = device

        self._attr_unique_id = f"lock_{self._device.metadata.uid}"
        self._attr_name = self._device.metadata.given_name
        self._attr_supported_features = LockEntityFeature(0)  # No additional features like open
        self._attr_is_locked = self._device.data.state == DweloLockState.LOCKED
        self._attr_extra_state_attributes = {
            "battery_level": self._device.data.battery_level,
            "is_online": self._device.data.is_online,
        }
        _LOGGER.debug(f"Initialized lock entity: {self._device.metadata}")

    async def async_update(self) -> None:
        """Update the lock data from the Dwelo API."""
        await self._device.async_update()
        if self._device.data:
            self._attr_is_locked = self._device.data.state == DweloLockState.LOCKED
            self._attr_extra_state_attributes = {
                "battery_level": self._device.data.battery_level,
                "is_online": self._device.data.is_online,
            }
            _LOGGER.debug(f"Updated lock data: {self._device.data}")
        else:
            _LOGGER.error(f"Failed to update lock data for {self._device.metadata.uid}")

    @property
    def is_locked(self) -> bool:
        """Return true if the lock is locked."""
        return self._attr_is_locked

    async def async_lock(self, **kwargs) -> None:
        """Lock the device."""
        _LOGGER.info(f"Locking device {self._device.metadata.given_name}")
        await self._device.set_lock_state(self._device.metadata, DweloLockState.LOCKED)
        self._attr_is_locked = True
        self.async_write_ha_state()
        await self.async_update()

    async def async_unlock(self, **kwargs) -> None:
        """Unlock the device."""
        _LOGGER.info(f"Unlocking device {self._device.metadata.given_name}")
        await self._device.set_lock_state(self._device.metadata, DweloLockState.UNLOCKED)
        self._attr_is_locked = False
        self.async_write_ha_state()
        await self.async_update()