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

from .const import DEVICE_TYPE_ER, DEVICE_TYPE_WR, DOMAIN

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
        self._device_type = shutter_data.get("type")
        
        # Unique ID for this entity
        self._attr_unique_id = f"{entry.entry_id}_cover_{self._sid}"
        
        # Set supported features based on device type
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )
        
        # Only WIR shutters support position setting
        if self._device_type == DEVICE_TYPE_WR:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

    @property
    def device_info(self):
        """Return device information about this shutter."""
        manufacturer = self.coordinator.api.get_manufacturer(self._device_type)
        model = f"{self._device_type} Shutter"
        
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._sid}")},
            "name": f"Shutter {self._sid}",
            "manufacturer": manufacturer,
            "model": model,
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover.
        
        0 is closed, 100 is fully open.
        For WIR: Mediola uses inverted logic: 0 = open, 100 = closed
        For Elero: Returns estimated position based on state
        """
        # Find current shutter data in coordinator
        for shutter in self.coordinator.data:
            if shutter.get("sid") == self._sid:
                state = shutter.get("state", "")
                device_type = shutter.get("type")
                
                position = self.coordinator.api.parse_position(device_type, state)
                
                if position is None:
                    return None
                
                # Invert position for Home Assistant
                # Mediola: 0 = open (HA 100), Mediola: 100 = closed (HA 0)
                ha_position = 100 - position
                return ha_position
        return None

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed."""
        position = self.current_cover_position
        if position is None:
            return None
        return position == 0

    @property
    def is_opening(self) -> Optional[bool]:
        """Return if the cover is opening."""
        # Only Elero reports moving states
        if self._device_type == DEVICE_TYPE_ER:
            for shutter in self.coordinator.data:
                if shutter.get("sid") == self._sid:
                    state = shutter.get("state", "")
                    return state == "100A"  # ELERO_STATE_MOVING_UP
        return None

    @property
    def is_closing(self) -> Optional[bool]:
        """Return if the cover is closing."""
        # Only Elero reports moving states
        if self._device_type == DEVICE_TYPE_ER:
            for shutter in self.coordinator.data:
                if shutter.get("sid") == self._sid:
                    state = shutter.get("state", "")
                    return state == "100B"  # ELERO_STATE_MOVING_DOWN
        return None

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.open_shutter, self._device_type, self._sid, self._adr
        )
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.close_shutter, self._device_type, self._sid, self._adr
        )
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.stop_shutter, self._device_type, self._sid, self._adr
        )
        # Request data update
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position.
        
        Note: Only supported for WIR shutters.
        """
        if self._device_type != DEVICE_TYPE_WR:
            _LOGGER.warning(
                "Shutter %s (type %s) does not support position setting",
                self._sid,
                self._device_type,
            )
            return
        
        ha_position = kwargs[ATTR_POSITION]
        # Invert position: HA 100 = open (Mediola 0), HA 0 = closed (Mediola 100)
        mediola_position = 100 - ha_position
        
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_shutter_position,
            self._device_type,
            self._sid,
            self._adr,
            mediola_position,
        )
        # Request data update
        await self.coordinator.async_request_refresh()