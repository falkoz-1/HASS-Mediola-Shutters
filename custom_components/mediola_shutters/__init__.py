"""The Mediola Shutters integration."""
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .mediola_api import MediolaAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.COVER, Platform.SENSOR, Platform.BINARY_SENSOR]

# Service names
SERVICE_OPEN_SHUTTER = "open_shutter"
SERVICE_CLOSE_SHUTTER = "close_shutter"
SERVICE_STOP_SHUTTER = "stop_shutter"
SERVICE_SET_POSITION = "set_shutter_position"
SERVICE_OPEN_ALL = "open_all_shutters"
SERVICE_CLOSE_ALL = "close_all_shutters"
SERVICE_STOP_ALL = "stop_all_shutters"

# Service schemas
SERVICE_SHUTTER_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
    }
)

SERVICE_SET_POSITION_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("position"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mediola Shutters from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    # Get scan interval from options, fallback to data, fallback to default
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    # Initialize the API client
    api = MediolaAPI(host, username, password)

    # Create coordinator for data updates
    coordinator = MediolaDataUpdateCoordinator(hass, api, scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await async_setup_services(hass, entry.entry_id)
    
    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_services(hass: HomeAssistant, entry_id: str) -> None:
    """Set up services for Mediola Shutters."""
    
    async def handle_open_shutter(call: ServiceCall) -> None:
        """Handle open shutter service call."""
        entity_id = call.data["entity_id"]
        # Call the cover.open_cover service
        await hass.services.async_call(
            "cover", "open_cover", {"entity_id": entity_id}, blocking=True
        )

    async def handle_close_shutter(call: ServiceCall) -> None:
        """Handle close shutter service call."""
        entity_id = call.data["entity_id"]
        # Call the cover.close_cover service
        await hass.services.async_call(
            "cover", "close_cover", {"entity_id": entity_id}, blocking=True
        )

    async def handle_stop_shutter(call: ServiceCall) -> None:
        """Handle stop shutter service call."""
        entity_id = call.data["entity_id"]
        # Call the cover.stop_cover service
        await hass.services.async_call(
            "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
        )

    async def handle_set_position(call: ServiceCall) -> None:
        """Handle set position service call."""
        entity_id = call.data["entity_id"]
        position = call.data["position"]
        # Call the cover.set_cover_position service
        await hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=True,
        )

    async def handle_open_all(call: ServiceCall) -> None:
        """Handle open all shutters service call."""
        coordinator = hass.data[DOMAIN][entry_id]
        for shutter in coordinator.data:
            sid = shutter.get("sid")
            adr = shutter.get("adr")
            await hass.async_add_executor_job(
                coordinator.api.open_shutter, sid, adr
            )
        await coordinator.async_request_refresh()

    async def handle_close_all(call: ServiceCall) -> None:
        """Handle close all shutters service call."""
        coordinator = hass.data[DOMAIN][entry_id]
        for shutter in coordinator.data:
            sid = shutter.get("sid")
            adr = shutter.get("adr")
            await hass.async_add_executor_job(
                coordinator.api.close_shutter, sid, adr
            )
        await coordinator.async_request_refresh()

    async def handle_stop_all(call: ServiceCall) -> None:
        """Handle stop all shutters service call."""
        coordinator = hass.data[DOMAIN][entry_id]
        for shutter in coordinator.data:
            sid = shutter.get("sid")
            adr = shutter.get("adr")
            await hass.async_add_executor_job(
                coordinator.api.stop_shutter, sid, adr
            )
        await coordinator.async_request_refresh()

    # Register services only if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_OPEN_SHUTTER):
        hass.services.async_register(
            DOMAIN, SERVICE_OPEN_SHUTTER, handle_open_shutter, schema=SERVICE_SHUTTER_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLOSE_SHUTTER):
        hass.services.async_register(
            DOMAIN, SERVICE_CLOSE_SHUTTER, handle_close_shutter, schema=SERVICE_SHUTTER_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_STOP_SHUTTER):
        hass.services.async_register(
            DOMAIN, SERVICE_STOP_SHUTTER, handle_stop_shutter, schema=SERVICE_SHUTTER_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_POSITION):
        hass.services.async_register(
            DOMAIN, SERVICE_SET_POSITION, handle_set_position, schema=SERVICE_SET_POSITION_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_OPEN_ALL):
        hass.services.async_register(DOMAIN, SERVICE_OPEN_ALL, handle_open_all)

    if not hass.services.has_service(DOMAIN, SERVICE_CLOSE_ALL):
        hass.services.async_register(DOMAIN, SERVICE_CLOSE_ALL, handle_close_all)

    if not hass.services.has_service(DOMAIN, SERVICE_STOP_ALL):
        hass.services.async_register(DOMAIN, SERVICE_STOP_ALL, handle_stop_all)


class MediolaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Mediola data from the gateway."""

    def __init__(self, hass: HomeAssistant, api: MediolaAPI, scan_interval: int) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from Mediola gateway."""
        try:
            return await self.hass.async_add_executor_job(self.api.get_states)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Mediola gateway: {err}")