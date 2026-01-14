from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeekrDeviceTracker(coordinator)])

class ZeekrDeviceTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        prefix = coordinator.entry.data.get("name", "Zeekr 7X")
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "location"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_location"
        self._attr_icon = "mdi:car-connected"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def source_type(self):
        return SourceType.GPS

    @property
    def latitude(self):
        """HÃ¤mta latitud (nu via 'main' nyckeln)."""
        pos = self.coordinator.data.get("main", {}).get("basicVehicleStatus", {}).get("position", {})
        try:
            return float(pos.get("latitude"))
        except (TypeError, ValueError):
            return None

    @property
    def longitude(self):
        """HÃ¤mta longitud (nu via 'main' nyckeln)."""
        pos = self.coordinator.data.get("main", {}).get("basicVehicleStatus", {}).get("position", {})
        try:
            return float(pos.get("longitude"))
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self):
        """Extra information som hÃ¶jd och riktning."""
        pos = self.coordinator.data.get("main", {}).get("basicVehicleStatus", {}).get("position", {})
        return {
            "altitude": pos.get("altitude"),
            "direction": pos.get("direction"),
            "gps_trusted": pos.get("posCanBeTrusted") == "1",
            "update_time": self.coordinator.data.get("main", {}).get("updateTime")
        }
