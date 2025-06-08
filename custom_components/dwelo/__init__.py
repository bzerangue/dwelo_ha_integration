from __future__ import annotations

"""The Dwelo Integration integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_GATEWAY_ID, DOMAIN, HOST
from .dwelo_client import DweloClient
from .models import DweloData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.LOCK]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dwelo Integration from a config entry."""
    _LOGGER.debug("Setting up Dwelo config entry: %s with gateway_id: %s", entry.entry_id, entry.data[CONF_GATEWAY_ID])
    hass.data.setdefault(DOMAIN, {})

    client = DweloClient(
        HOST,
        hass,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_GATEWAY_ID],
    )

    if not await client.login():
        _LOGGER.error("Failed to login to Dwelo API")
        return False

    devices = await client.get_devices()
    if not devices:
        _LOGGER.error("No devices retrieved from Dwelo API")
        return False

    hass.data[DOMAIN][entry.entry_id] = DweloData(
        entry_id=entry.entry_id,
        client=client,
        device_metadata=devices,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Dwelo setup completed successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok