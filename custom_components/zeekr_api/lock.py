import logging
from homeassistant.components.lock import LockEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CONTROL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeekrLock(coordinator)])

class ZeekrLock(CoordinatorEntity, LockEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        prefix = coordinator.entry.data.get("name", "Zeekr 7X")
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "door_lock"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_central_lock"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def is_locked(self):
        status = self.coordinator.data.get("main", {}).get("additionalVehicleStatus", {}).get("drivingSafetyStatus", {}).get("centralLockingStatus")
        return str(status) == "1"

    async def async_lock(self, **kwargs):
        payload = {
            "command": "stop", 
            "serviceId": "RDL", 
            "setting": {
                "serviceParameters": [
                    {"key": "door", "value": "all"}
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Deuren vergrendelen")
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs):
        payload = {
            "command": "start", 
            "serviceId": "RDU", 
            "setting": {
                "serviceParameters": [
                    {"key": "door", "value": "all"}
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Deuren ontgrendelen")
        await self.coordinator.async_request_refresh()
