"""Config flow for Dwelo Integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback, HomeAssistant

from .const import CONF_GATEWAY_ID, DOMAIN, HOST
from .dwelo_client import DweloClient

_LOGGER = logging.getLogger(__name__)

class DweloConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dwelo Integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        _LOGGER.debug("Starting Dwelo config flow user step")

        if user_input is not None:
            try:
                _LOGGER.debug("Validating input: %s", user_input)
                client = DweloClient(
                    HOST,
                    self.hass,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_GATEWAY_ID],
                )
                if not await client.login():
                    errors["base"] = "invalid_auth"
                else:
                    devices = await client.get_devices()
                    if not devices:
                        errors["base"] = "no_devices"
                    else:
                        await self.async_set_unique_id(
                            f"{user_input[CONF_EMAIL]}_{user_input[CONF_GATEWAY_ID]}"
                        )
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=f"Dwelo ({user_input[CONF_EMAIL]})",
                            data=user_input,
                        )
            except Exception as e:
                _LOGGER.error("Error setting up Dwelo config: %s", e)
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
        """Initialize options flow."""
        self._config_entry = config_entry  # Changed from self.config_entry
        _LOGGER.debug("Initializing Dwelo options flow for entry: %s", config_entry.entry_id)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        _LOGGER.debug("Starting Dwelo options flow init step with config: %s", self._config_entry.data)

        if user_input is not None:
            try:
                client = DweloClient(
                    HOST,
                    self.hass,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_GATEWAY_ID],
                )
                if not await client.login():
                    errors["base"] = "invalid_auth"
                else:
                    devices = await client.get_devices()
                    if not devices:
                        errors["base"] = "no_devices"
                    else:
                        return self.async_create_entry(title="", data=user_input)
            except Exception as e:
                _LOGGER.error("Error updating Dwelo options: %s", e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        default=self._config_entry.data.get(CONF_EMAIL),
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=self._config_entry.data.get(CONF_PASSWORD),
                    ): str,
                    vol.Required(
                        CONF_GATEWAY_ID,
                        default=self._config_entry.data.get(CONF_GATEWAY_ID),
                    ): str,
                }
            ),
            errors=errors,
        )