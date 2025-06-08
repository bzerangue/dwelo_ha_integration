"""Config flow for Dwelo Integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback

from .const import CONF_GATEWAY_ID, DOMAIN
from .dwelo_client import DweloClient

_LOGGER = logging.getLogger(__name__)

class DweloConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dwelo Integration."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate input by testing login and device retrieval
                client = DweloClient(
                    self.hass,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_GATEWAY_ID],
                )
                if not await client.login():
                    errors["base"] = "invalid_auth"
                else:
                    # Test device retrieval
                    devices = await client.get_devices()
                    if not devices:
                        errors["base"] = "no_devices"
                    else:
                        # Ensure unique ID based on email and gateway ID
                        await self.async_set_unique_id(f"{user_input[CONF_EMAIL]}_{user_input[CONF_GATEWAY_ID]}")
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"Dwelo ({user_input[CONF_EMAIL]})",
                            data=user_input,
                        )
            except Exception as e:
                _LOGGER.error(f"Error setting up Dwelo config: {e}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_GATEWAY_ID): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Dwelo Integration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=self.config_entry.data.get(CONF_EMAIL),
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=self.config_entry.data.get(CONF_PASSWORD),
                    ): str,
                    vol.Required(
                        CONF_GATEWAY_ID,
                        default=self.config_entry.data.get(CONF_GATEWAY_ID),
                    ): str,
                }
            ),
        )