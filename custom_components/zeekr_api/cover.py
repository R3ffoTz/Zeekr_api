from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CONTROL
import asyncio

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = coordinator.entry.data.get("name", "Zeekr 7X")
    async_add_entities([ZeekrSunshade(coordinator, prefix)])

class ZeekrSunshade(CoordinatorEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHADE
    _attr_supported_features = (
        CoverEntityFeature.OPEN | 
        CoverEntityFeature.CLOSE
    )

    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "sunshade"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sunshade_cover"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def is_closed(self):
        val = self.coordinator.data.get("main", {}).get("additionalVehicleStatus", {}).get("climateStatus", {}).get("curtainOpenStatus")
        return val == 1

    async def async_open_cover(self, **kwargs):
        payload = {
            "command": "start", 
            "serviceId": "RWS", 
            "setting": {
                "serviceParameters": [
                    {"key": "target", "value": "sunshade"}
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Open sunshade")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        payload = {
            "command": "stop", 
            "serviceId": "RWS", 
            "setting": {
                "serviceParameters": [
                    {"key": "target", "value": "sunshade"}
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Close sunshade")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
