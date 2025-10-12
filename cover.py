"""Cover platform for Mediola Shutters integration."""
import logging
from typing import Any, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mediola cover entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create cover entities for each shutter
    entities = []
    for shutter in coordinator.data:
        entities.append(MediolaCover(coordinator, shutter, entry))

    async_add_entities(entities)


class MediolaCover(CoordinatorEntity, CoverEntity):
    """Representation of a Mediola shutter cover."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_has_entity_name = True
    _attr_name = None  # Use device name

    def __init__(self, coordinator, shutter_data, entry):
        """Initialize the cover."""
        super().__init__(coordinator)
        self._shutter_data = shutter_data
        self._entry = entry
        
        # Extract shutter information
        self._sid = shutter_data.get("sid")
        self._adr = shutter_data.get("adr")
        
        # Unique ID for this entity
        self._attr_unique_id = f"{entry.entry_id}_cover_{self._sid}"
        
        # Supported features
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def device_info(self):
        """Return device information about this shutter."""
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._sid}")},
            "name": f"Shutter {self._sid}",
            "manufacturer": "Mediola",
            "model": "Window Roller",
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover.
        
        0 is closed, 100 is fully open.
        Mediola uses inverted logic: 0 = open, 100 = closed
        """
        # Find current shutter data in coordinator
        for shutter in self.coordinator.data:
            if shutter.get("sid") == self._sid:
                state = shutter.get("state", "010000")
                mediola_position = self.coordinator.api.parse_position_from_state(state)
                # Invert: Mediola 0 = open (HA 100), Mediola 100 = closed (HA 0)
                ha_position = 100 - mediola_position
                return ha_position
        return None

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed."""
        position = self.current_cover_position
        if position is None:
            return None
        return position == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.open_shutter, self._sid, self._adr
        )
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.close_shutter, self._sid, self._adr
        )
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.stop_shutter, self._sid, self._adr
        )
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        ha_position = kwargs[ATTR_POSITION]
        # Invert position: HA 100 = open (Mediola 0), HA 0 = closed (Mediola 100)
        mediola_position = 100 - ha_position
        
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_shutter_position,
            self._sid,
            self._adr,
            mediola_position,
        )
        # Request data update
        await self.coordinator.async_request_refresh()