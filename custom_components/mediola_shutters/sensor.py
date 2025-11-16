"""Sensor platform for Mediola Shutters integration."""
import logging
from typing import Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
    """Set up Mediola sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensor entities for each shutter
    entities = []
    for shutter in coordinator.data:
        entities.append(MediolaPositionSensor(coordinator, shutter, entry))

    async_add_entities(entities)


class MediolaPositionSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the current position percentage of a Mediola shutter."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:window-shutter"

    def __init__(self, coordinator, shutter_data, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._shutter_data = shutter_data
        self._entry = entry
        
        # Extract shutter information
        self._sid = shutter_data.get("sid")
        self._adr = shutter_data.get("adr")
        self._device_type = shutter_data.get("type")
        
        # Unique ID for this entity
        self._attr_unique_id = f"{entry.entry_id}_position_{self._sid}"
        
        # Entity name
        self._attr_name = "Position"

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
    def native_value(self) -> Optional[int]:
        """Return the current position percentage.
        
        Returns percentage where 0% = fully open, 100% = fully closed.
        """
        # Find current shutter data in coordinator
        for shutter in self.coordinator.data:
            if shutter.get("sid") == self._sid:
                state = shutter.get("state", "")
                device_type = shutter.get("type")
                position = self.coordinator.api.parse_position(device_type, state)
                return position
        return None