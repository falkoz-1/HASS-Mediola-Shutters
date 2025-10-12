"""Config flow for Mediola Shutters integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .mediola_api import MediolaAPI

_LOGGER = logging.getLogger(__name__)

# Schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            cv.positive_int, vol.Range(min=5, max=300)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.
    
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = MediolaAPI(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])

    # Try to connect and get states
    try:
        shutters = await hass.async_add_executor_job(api.get_states)
    except Exception as err:
        _LOGGER.error("Could not connect to Mediola gateway: %s", err)
        raise CannotConnect

    # Return info that we want to store in the config entry
    return {
        "title": f"Mediola Gateway ({data[CONF_HOST]})",
        "num_shutters": len(shutters),
    }


class MediolaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mediola Shutters."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on the host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "MediolaOptionsFlowHandler":
        """Get the options flow for this handler."""
        return MediolaOptionsFlowHandler(config_entry)


class MediolaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Mediola Shutters integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current scan interval
        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_scan_interval
                ): vol.All(cv.positive_int, vol.Range(min=5, max=300)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""