"""The Dwelo Integration integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, HOST
from .dwelo_client import DweloClient
from .models import DweloData

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dwelo Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    client = DweloClient(
        HOST, hass, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )

    if not await client.login():
        return False

    hass.data[DOMAIN][entry.entry_id] = DweloData(
        entry_id=entry.entry_id, client=client, devices=await client.get_devices()
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
