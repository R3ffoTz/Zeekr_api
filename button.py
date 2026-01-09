from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CONTROL
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = entry.data.get("name", "Zeekr")
    
    async_add_entities([
        ZeekrRefreshButton(coordinator, prefix),
        ZeekrTrunkButton(coordinator, prefix),
        ZeekrTravelUpdateButton(coordinator, prefix, entry.entry_id)
    ])

class ZeekrTravelUpdateButton(ButtonEntity):
    def __init__(self, coordinator, prefix, entry_id):
        self.coordinator = coordinator
        vin = coordinator.entry.data.get('vin')
        self._entry_id = entry_id
        self._attr_name = f"{prefix} Update Reisplan"
        self._attr_unique_id = f"{entry_id}_travel_update"
        self._attr_icon = "mdi:cloud-upload"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        travel_switch = self.hass.data[DOMAIN].get(f"{self._entry_id}_travel_switch")
        if travel_switch:
            await travel_switch._send_plan("start")
        else:
            _LOGGER.error("Travel Switch niet gevonden")

class ZeekrRefreshButton(ButtonEntity):
    def __init__(self, coordinator, prefix):
        self.coordinator = coordinator
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} Data Verversen"
        self._attr_unique_id = f"{self.coordinator.entry.entry_id}_refresh_button"
        self._attr_icon = "mdi:database-refresh"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        await self.coordinator.async_refresh()

class ZeekrTrunkButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} Kofferbak"
        self._attr_unique_id = f"{self.coordinator.entry.entry_id}_trunk_button"
        self._attr_icon = "mdi:car-back"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        # We controleren eerst de status om te bepalen of we openen of sluiten
        status_open = self.coordinator.data.get("main", {}).get("additionalVehicleStatus", {}).get("drivingSafetyStatus", {}).get("trunkOpenStatus")
        is_open = str(status_open) == "1"
        
        # Toggle logica
        if is_open:
             payload = {"command": "stop", "serviceId": "RTC", "setting": {"serviceParameters": [{"key": "trunk", "value": "0"}]}}
             desc = "Kofferbak sluiten"
        else:
             payload = {"command": "start", "serviceId": "RTC", "setting": {"serviceParameters": [{"key": "trunk", "value": "100"}]}}
             desc = "Kofferbak openen"

        await self.coordinator.send_command(URL_CONTROL, payload, desc)
