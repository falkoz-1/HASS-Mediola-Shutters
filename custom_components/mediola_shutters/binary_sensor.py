"""Binary sensor platform for Mediola Shutters integration."""
import logging
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
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
    """Set up Mediola binary sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create binary sensor entities for each shutter
    entities = []
    for shutter in coordinator.data:
        entities.append(MediolaOpeningSensor(coordinator, shutter, entry))

    async_add_entities(entities)


class MediolaOpeningSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor showing if a Mediola shutter is open or closed."""

    _attr_device_class = BinarySensorDeviceClass.OPENING
    _attr_has_entity_name = True

    def __init__(self, coordinator, shutter_data, entry):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._shutter_data = shutter_data
        self._entry = entry
        
        # Extract shutter information
        self._sid = shutter_data.get("sid")
        self._adr = shutter_data.get("adr")
        self._device_type = shutter_data.get("type")
        
        # Unique ID for this entity
        self._attr_unique_id = f"{entry.entry_id}_opening_{self._sid}"
        
        # Entity name
        self._attr_name = "Opening"

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
    def is_on(self) -> Optional[bool]:
        """Return true if the shutter is open.
        
        For opening sensor: True = open, False = closed.
        """
        # Find current shutter data in coordinator
        for shutter in self.coordinator.data:
            if shutter.get("sid") == self._sid:
                state = shutter.get("state", "")
                device_type = shutter.get("type")
                position = self.coordinator.api.parse_position(device_type, state)
                
                if position is None:
                    # If position is unknown (e.g., moving), return None
                    return None
                
                # If position is 0, shutter is fully open (True)
                # If position is greater than 0, shutter is at least partially closed (False)
                return position == 0
        return None